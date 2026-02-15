#include "ec06.h"
#include "esp_log.h"
#include <stdlib.h>

static const char *TAG = "ENCODER";

#define ENCODER_A_GPIO 1
#define ENCODER_B_GPIO 2

// 在 4X 模式下，一个物理卡位通常产生 4 个脉冲
// 所以这里的阈值必须设为 4，这会带来最佳的手感
#define ENCODER_STEP_THRESHOLD 4

pcnt_unit_handle_t pcnt_unit = NULL;
int last_count = 0;

void init_encoder_direction() {
    // 1. 创建 PCNT 单元
    pcnt_unit_config_t unit_config = {
        .high_limit = 100,
        .low_limit = -100,
    };
    ESP_ERROR_CHECK(pcnt_new_unit(&unit_config, &pcnt_unit));

    // 2. 设置毛刺滤波器 (建议设大一点，比如 1000~10000ns)
    pcnt_glitch_filter_config_t filter_config = {
        .max_glitch_ns = 10000, 
    };
    ESP_ERROR_CHECK(pcnt_unit_set_glitch_filter(pcnt_unit, &filter_config));

    // ==========================================
    // 关键修改：配置两个通道，实现 4X 解码
    // ==========================================

    // --- 配置通道 0 (监听 A 的跳变) ---
    pcnt_chan_config_t chan_a_config = {
        .edge_gpio_num = ENCODER_A_GPIO, // A 是跳变源
        .level_gpio_num = ENCODER_B_GPIO, // B 是参考电平
    };
    pcnt_channel_handle_t pcnt_chan_a = NULL;
    ESP_ERROR_CHECK(pcnt_new_channel(pcnt_unit, &chan_a_config, &pcnt_chan_a));

    // --- 配置通道 1 (监听 B 的跳变) ---
    pcnt_chan_config_t chan_b_config = {
        .edge_gpio_num = ENCODER_B_GPIO, // B 是跳变源
        .level_gpio_num = ENCODER_A_GPIO, // A 是参考电平
    };
    pcnt_channel_handle_t pcnt_chan_b = NULL;
    ESP_ERROR_CHECK(pcnt_new_channel(pcnt_unit, &chan_b_config, &pcnt_chan_b));

    // ==========================================
    // 设置正交解码逻辑 (Full Quadrature Logic)
    // ==========================================
    
    // 逻辑目标：顺时针(CW)计数增加，逆时针(CCW)计数减少

    // 通道 A 的动作定义:
    // A 上升沿 + B 低电平 = 增
    // A 下降沿 + B 高电平 = 增
    ESP_ERROR_CHECK(pcnt_channel_set_edge_action(pcnt_chan_a, PCNT_CHANNEL_EDGE_ACTION_INCREASE, PCNT_CHANNEL_EDGE_ACTION_DECREASE));
    ESP_ERROR_CHECK(pcnt_channel_set_level_action(pcnt_chan_a, PCNT_CHANNEL_LEVEL_ACTION_KEEP, PCNT_CHANNEL_LEVEL_ACTION_INVERSE));

    // 通道 B 的动作定义:
    // B 上升沿 + A 高电平 = 增
    // B 下降沿 + A 低电平 = 增
    ESP_ERROR_CHECK(pcnt_channel_set_edge_action(pcnt_chan_b, PCNT_CHANNEL_EDGE_ACTION_INCREASE, PCNT_CHANNEL_EDGE_ACTION_DECREASE));
    ESP_ERROR_CHECK(pcnt_channel_set_level_action(pcnt_chan_b, PCNT_CHANNEL_LEVEL_ACTION_INVERSE, PCNT_CHANNEL_LEVEL_ACTION_KEEP));

    // 启用并启动
    ESP_ERROR_CHECK(pcnt_unit_enable(pcnt_unit));
    ESP_ERROR_CHECK(pcnt_unit_clear_count(pcnt_unit));
    ESP_ERROR_CHECK(pcnt_unit_start(pcnt_unit));
}

uint8_t check_encoder_direction() {
    int current_count = 0;
    ESP_ERROR_CHECK(pcnt_unit_get_count(pcnt_unit, &current_count));

    int diff = current_count - last_count;
    if (abs(diff) >= ENCODER_STEP_THRESHOLD) {
        last_count = current_count; 
        
        if (diff > 0) {
            return 2; // NEXT 
        } else {
            return 1; // PREV 
        }
    }
    return 0;
}