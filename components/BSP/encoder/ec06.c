#include "ec06.h"
#include "esp_log.h"
#include <stdlib.h>
#include "esp_timer.h" // For debounce

static const char *TAG = "ENCODER";

#define ENCODER_A_GPIO 1
#define ENCODER_B_GPIO 2

// Back to 4X mode for better resolution
// One physical detent = 4 pulses. 
#define ENCODER_STEP_THRESHOLD_CW  4  // CW (right): normal threshold
#define ENCODER_STEP_THRESHOLD_CCW  6  // CCW (left): higher threshold, B phase is noisier

// Debounce time window in microseconds (150ms)
#define ENCODER_DEBOUNCE_US 150000 
// Time to clear accumulated "half-steps" to prevent phantom triggers (200ms)
#define ENCODER_AGING_US 200000

pcnt_unit_handle_t pcnt_unit = NULL;
int last_count = 0;

void init_encoder_direction() {
    // 1. Create PCNT unit
    pcnt_unit_config_t unit_config = {
        .high_limit = 100,
        .low_limit = -100,
    };
    ESP_ERROR_CHECK(pcnt_new_unit(&unit_config, &pcnt_unit));

    // 2. Set glitch filter 
    // Set to 10000ns (10us) which is a safe value for hardware limits
    // Hardware filter prevents high-frequency spikes, software handles mechanical bounce
    pcnt_glitch_filter_config_t filter_config = {
        .max_glitch_ns = 10000, 
    };
    ESP_ERROR_CHECK(pcnt_unit_set_glitch_filter(pcnt_unit, &filter_config));

    // ==========================================
    // Configure two channels for 4X decoding
    // ==========================================

    // --- Configure Channel 0 (Listen for A edges) ---
    pcnt_chan_config_t chan_a_config = {
        .edge_gpio_num = ENCODER_A_GPIO, // A is the edge source
        .level_gpio_num = ENCODER_B_GPIO, // B is the level source
    };
    pcnt_channel_handle_t pcnt_chan_a = NULL;
    ESP_ERROR_CHECK(pcnt_new_channel(pcnt_unit, &chan_a_config, &pcnt_chan_a));

    // --- Configure Channel 1 (Listen for B edges) ---
    pcnt_chan_config_t chan_b_config = {
        .edge_gpio_num = ENCODER_B_GPIO, // B is the edge source
        .level_gpio_num = ENCODER_A_GPIO, // A is the level source
    };
    pcnt_channel_handle_t pcnt_chan_b = NULL;
    ESP_ERROR_CHECK(pcnt_new_channel(pcnt_unit, &chan_b_config, &pcnt_chan_b));

    // ==========================================
    // Set Full Quadrature Logic (4X)
    // ==========================================
    
    // Logic goal: Clockwise (CW) increases count, Counter-Clockwise (CCW) decreases count

    // Channel A action definition:
    ESP_ERROR_CHECK(pcnt_channel_set_edge_action(pcnt_chan_a, PCNT_CHANNEL_EDGE_ACTION_INCREASE, PCNT_CHANNEL_EDGE_ACTION_DECREASE));
    ESP_ERROR_CHECK(pcnt_channel_set_level_action(pcnt_chan_a, PCNT_CHANNEL_LEVEL_ACTION_KEEP, PCNT_CHANNEL_LEVEL_ACTION_INVERSE));

    // Channel B action definition:
    ESP_ERROR_CHECK(pcnt_channel_set_edge_action(pcnt_chan_b, PCNT_CHANNEL_EDGE_ACTION_INCREASE, PCNT_CHANNEL_EDGE_ACTION_DECREASE));
    ESP_ERROR_CHECK(pcnt_channel_set_level_action(pcnt_chan_b, PCNT_CHANNEL_LEVEL_ACTION_INVERSE, PCNT_CHANNEL_LEVEL_ACTION_KEEP));

    // Enable and start
    ESP_ERROR_CHECK(pcnt_unit_enable(pcnt_unit));
    ESP_ERROR_CHECK(pcnt_unit_clear_count(pcnt_unit));
    ESP_ERROR_CHECK(pcnt_unit_start(pcnt_unit));
}

uint8_t check_encoder_direction() {
    static int64_t last_time = 0;
    int count = 0;
    int64_t current_time = esp_timer_get_time();

    //获取脉冲计数
    pcnt_unit_get_count(pcnt_unit, &count);

    // 简单去噪：判断时间间隔是否满足要求（例如100ms）
    if ((current_time - last_time) > ENCODER_DEBOUNCE_US) { 
        // 增加阈值判断：只有积累到一定步数（例如4步及以上）才认为是有效旋转
        // 这能有效过滤掉停止时的微小回弹（通常是1-2个脉冲）
        if (count >= ENCODER_STEP_THRESHOLD_CW) {
            // 顺时针旋转
            pcnt_unit_clear_count(pcnt_unit);
            last_time = current_time;
            return 2; // 下一个/顺时针
        } else if (count <= -ENCODER_STEP_THRESHOLD_CCW) {
            // 逆时针旋转
            pcnt_unit_clear_count(pcnt_unit);
            last_time = current_time;
            return 1; // 上一个/逆时针
        }
        // 如果 count 在 -3 到 3 之间，视为抖动/无效动作，不做处理也不清零，让其继续累积
    }

    return 0; // 无有效动作
}
