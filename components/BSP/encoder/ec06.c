#include "ec06.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "driver/gpio.h"
#include <stdlib.h>

static const char *TAG = "ENCODER";

// =================【用户配置区】=================

// 1. 引脚定义
#define ENCODER_A_GPIO 1
#define ENCODER_B_GPIO 2

// 2. 硬件判定阈值：机械编码器转动一格(Detent)通常会产生 4 个硬件脉冲
#define EC_STEP_PER_DETENT 4   

// 3. 防抖冷却时间 (微秒)：120ms
#define EC_DEBOUNCE_US 120000

// 4. 反向迟滞量：当试图改变旋转方向时，需要额外增加的脉冲门槛
//    这能有效防止停止时的机械回弹导致的误触
#define EC_HYSTERESIS   2

// ===============================================

static pcnt_unit_handle_t pcnt_unit = NULL;
static int accumulated_count = 0;     // 软件累加器
static int last_direction = 0;        // 上次生效的方向: 1为正(顺), -1为负(逆), 0初始
static int64_t last_trigger_time = 0; // 上次触发时间

/**
 * @brief 初始化编码器驱动
 * 使用双通道 4X 正交解码模式，抗干扰能力最强
 */
void init_encoder_direction() {
    ESP_LOGI(TAG, "Initializing EC06 Encoder...");

    // 1. 强制开启 GPIO 内部上拉 (机械触点必须要有上拉，否则悬空会乱跳)
    gpio_set_pull_mode(ENCODER_A_GPIO, GPIO_PULLUP_ONLY);
    gpio_set_pull_mode(ENCODER_B_GPIO, GPIO_PULLUP_ONLY);

    // 2. 创建 PCNT 单元
    //    设置较大的限值，防止溢出，虽然我们会定期清零
    pcnt_unit_config_t unit_config = {
        .high_limit = 1000,
        .low_limit = -1000,
    };
    ESP_ERROR_CHECK(pcnt_new_unit(&unit_config, &pcnt_unit));

    // 3. 设置硬件毛刺滤波 (10000ns = 10us)
    //    过滤掉所有短于 10us 的电气毛刺
    pcnt_glitch_filter_config_t filter_config = {
        .max_glitch_ns = 10000,
    };
    ESP_ERROR_CHECK(pcnt_unit_set_glitch_filter(pcnt_unit, &filter_config));

    // 4. 配置通道 A
    pcnt_chan_config_t chan_a_config = {
        .edge_gpio_num = ENCODER_A_GPIO,
        .level_gpio_num = ENCODER_B_GPIO,
    };
    pcnt_channel_handle_t pcnt_chan_a = NULL;
    ESP_ERROR_CHECK(pcnt_new_channel(pcnt_unit, &chan_a_config, &pcnt_chan_a));

    // 5. 配置通道 B
    pcnt_chan_config_t chan_b_config = {
        .edge_gpio_num = ENCODER_B_GPIO,
        .level_gpio_num = ENCODER_A_GPIO,
    };
    pcnt_channel_handle_t pcnt_chan_b = NULL;
    ESP_ERROR_CHECK(pcnt_new_channel(pcnt_unit, &chan_b_config, &pcnt_chan_b));

    // =========================================================
    // 6. 配置 4X 正交解码逻辑 (核心)
    //    逻辑：利用 A/B 相位差，实现正转 +1，反转 -1
    // =========================================================
    
    // 通道 A 动作：
    // 上升沿：若 B 高电平->减，若 B 低电平->加
    // 下降沿：若 B 高电平->加，若 B 低电平->减
    ESP_ERROR_CHECK(pcnt_channel_set_edge_action(pcnt_chan_a, PCNT_CHANNEL_EDGE_ACTION_DECREASE, PCNT_CHANNEL_EDGE_ACTION_INCREASE));
    ESP_ERROR_CHECK(pcnt_channel_set_level_action(pcnt_chan_a, PCNT_CHANNEL_LEVEL_ACTION_KEEP, PCNT_CHANNEL_LEVEL_ACTION_INVERSE));

    // 通道 B 动作 (与 A 形成互补)：
    ESP_ERROR_CHECK(pcnt_channel_set_edge_action(pcnt_chan_b, PCNT_CHANNEL_EDGE_ACTION_INCREASE, PCNT_CHANNEL_EDGE_ACTION_DECREASE));
    ESP_ERROR_CHECK(pcnt_channel_set_level_action(pcnt_chan_b, PCNT_CHANNEL_LEVEL_ACTION_KEEP, PCNT_CHANNEL_LEVEL_ACTION_INVERSE));

    // 7. 启动计数器
    ESP_ERROR_CHECK(pcnt_unit_enable(pcnt_unit));
    ESP_ERROR_CHECK(pcnt_unit_clear_count(pcnt_unit));
    ESP_ERROR_CHECK(pcnt_unit_start(pcnt_unit));
    
    ESP_LOGI(TAG, "Encoder initialized successfully (4X Mode)");
}

/**
 * @brief 检测编码器旋转事件
 * @return 0: 无动作, 1: 逆时针(PREV), 2: 顺时针(NEXT)
 */
uint8_t check_encoder_direction() {
    int curr_hw_count = 0;
    
    // 1. 读取硬件计数器当前的增量
    ESP_ERROR_CHECK(pcnt_unit_get_count(pcnt_unit, &curr_hw_count));
    
    if (curr_hw_count == 0) {
        return 0; // 硬件没动，直接返回
    }

    // 2. 将硬件增量累加到软件变量中，清空硬件计数器
    //    这样不仅防止硬件溢出，还能让我们的逻辑始终处理相对增量
    accumulated_count += curr_hw_count;
    ESP_ERROR_CHECK(pcnt_unit_clear_count(pcnt_unit));

    // 3. 逻辑检查：阈值 + 迟滞
    int direction_now = (accumulated_count > 0) ? 1 : -1;
    int threshold = EC_STEP_PER_DETENT;

    // 核心改进：迟滞 (Hysteresis)
    // 如果当前旋转意图和上次生效方向相反（例如上次顺时针，这次想逆时针），
    // 增加阈值门槛。这能有效屏蔽掉停止时的机械回弹（backlash）。
    // last_direction: 1 (CW), -1 (CCW), 0 (Init)
    if (last_direction != 0 && direction_now != last_direction) {
        threshold += EC_HYSTERESIS;
    }

    // 检查累加值是否达到计算后的动态阈值
    if (abs(accumulated_count) >= threshold) {
        
        int64_t now = esp_timer_get_time();
        
        // 更新记录“最后一次有效方向”
        last_direction = direction_now; 
        
        // 归零软件累加器
        accumulated_count = 0;

        // --- 防抖时间冷却逻辑 ---
        if ((now - last_trigger_time) > EC_DEBOUNCE_US) {
            last_trigger_time = now;
            
            if (direction_now == 1) {
                // 正数 -> 顺时针
                ESP_LOGI(TAG, "Action: NEXT >>");
                return 1; 
            } else {
                // 负数 -> 逆时针
                ESP_LOGI(TAG, "Action: << PREV");
                return 2; 
            }
        } 
        // 冷却期内的操作会被吞掉，但 accumulated_count 已清零，
        // 保证了快速旋转时不会积压错误的脉冲。
    }

    return 0;
}
