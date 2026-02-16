#include "ec06.h"
#include "esp_log.h"
#include <stdlib.h>

static const char *TAG = "ENCODER";

#define ENCODER_A_GPIO 1
#define ENCODER_B_GPIO 2

// In 4X mode, one physical detent usually generates 4 pulses
// So the threshold here must be set to 4, which gives the best feel
#define ENCODER_STEP_THRESHOLD 4

pcnt_unit_handle_t pcnt_unit = NULL;
int last_count = 0;

void init_encoder_direction() {
    // 1. Create PCNT unit
    pcnt_unit_config_t unit_config = {
        .high_limit = 100,
        .low_limit = -100,
    };
    ESP_ERROR_CHECK(pcnt_new_unit(&unit_config, &pcnt_unit));

    // 2. Set glitch filter (recommended to set larger, e.g., 1000~10000ns)
    pcnt_glitch_filter_config_t filter_config = {
        .max_glitch_ns = 10000, 
    };
    ESP_ERROR_CHECK(pcnt_unit_set_glitch_filter(pcnt_unit, &filter_config));

    // ==========================================
    // Key modification: Configure two channels for 4X decoding
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
    // Set Full Quadrature Logic
    // ==========================================
    
    // Logic goal: Clockwise (CW) increases count, Counter-Clockwise (CCW) decreases count

    // Channel A action definition:
    // A rising edge + B low level = Increase
    // A falling edge + B high level = Increase
    ESP_ERROR_CHECK(pcnt_channel_set_edge_action(pcnt_chan_a, PCNT_CHANNEL_EDGE_ACTION_INCREASE, PCNT_CHANNEL_EDGE_ACTION_DECREASE));
    ESP_ERROR_CHECK(pcnt_channel_set_level_action(pcnt_chan_a, PCNT_CHANNEL_LEVEL_ACTION_KEEP, PCNT_CHANNEL_LEVEL_ACTION_INVERSE));

    // Channel B action definition:
    // B rising edge + A high level = Increase
    // B falling edge + A low level = Increase
    ESP_ERROR_CHECK(pcnt_channel_set_edge_action(pcnt_chan_b, PCNT_CHANNEL_EDGE_ACTION_INCREASE, PCNT_CHANNEL_EDGE_ACTION_DECREASE));
    ESP_ERROR_CHECK(pcnt_channel_set_level_action(pcnt_chan_b, PCNT_CHANNEL_LEVEL_ACTION_INVERSE, PCNT_CHANNEL_LEVEL_ACTION_KEEP));

    // Enable and start
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
