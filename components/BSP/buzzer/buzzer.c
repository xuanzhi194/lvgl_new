#include "buzzer.h"

// 定义配置参数
#define BUZZER_IO           (7)               // 使用 IO7
#define BUZZER_LEDC_TIMER   LEDC_TIMER_0
#define BUZZER_LEDC_MODE    LEDC_LOW_SPEED_MODE
#define BUZZER_LEDC_CHANNEL LEDC_CHANNEL_0
#define BUZZER_DUTY_RES     LEDC_TIMER_13_BIT // 13位分辨率
#define BUZZER_INITIAL_FREQ (2000)            // 初始频率 2kHz

/**
 * 初始化 PWM 配置
 */
void buzzer_init() {
    // 1. 定时器配置
    ledc_timer_config_t ledc_timer = {
        .speed_mode       = BUZZER_LEDC_MODE,
        .timer_num        = BUZZER_LEDC_TIMER,
        .duty_resolution  = BUZZER_DUTY_RES,
        .freq_hz          = BUZZER_INITIAL_FREQ,
        .clk_cfg          = LEDC_AUTO_CLK
    };
    ledc_timer_config(&ledc_timer);

    // 2. 通道配置
    ledc_channel_config_t ledc_channel = {
        .speed_mode     = BUZZER_LEDC_MODE,
        .channel        = BUZZER_LEDC_CHANNEL,
        .timer_sel      = BUZZER_LEDC_TIMER,
        .intr_type      = LEDC_INTR_DISABLE,
        .gpio_num       = BUZZER_IO,
        .duty           = 0, // init close
        .hpoint         = 0
    };
    ledc_channel_config(&ledc_channel);
}

/**
 * setting booming
 * @param freq 
 * @param state
 */
void buzzer_set_sound(uint32_t freq, uint8_t volume_percent) {
        // update frequency
        ledc_set_freq(BUZZER_LEDC_MODE, BUZZER_LEDC_TIMER, freq);
        // set duty cycle (2^13 / 2 = 4096)
        uint32_t duty_param = (8192 * volume_percent) / 100;
        ledc_set_duty(BUZZER_LEDC_MODE, BUZZER_LEDC_CHANNEL, duty_param);
        ledc_update_duty(BUZZER_LEDC_MODE, BUZZER_LEDC_CHANNEL);
}

//buzzer alarm combination
void buzzer_timeout() {
    uint32_t alarm_freq = 2700; 
    uint8_t volume = 50;      

    for (int round = 0; round < 5; round++) {
        for(int i = 0; i < 3; i++) {
            buzzer_set_sound(alarm_freq, volume);   // 发声
            vTaskDelay(pdMS_TO_TICKS(100));         // 持续 100ms
            buzzer_set_sound(alarm_freq, 0);        // 静音 (占空比为0)
            vTaskDelay(pdMS_TO_TICKS(100));         // 间隔 100ms
        }
        // 两组声音之间的长停顿
        vTaskDelay(pdMS_TO_TICKS(400)); 
    }
    
    // 安全起见，确保函数退出前蜂鸣器被彻底关闭
    buzzer_set_sound(alarm_freq, 0);
}