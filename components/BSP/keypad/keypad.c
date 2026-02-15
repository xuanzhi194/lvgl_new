#include "keypad.h"
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "buzzer.h"
//if button connect to gnd if cliked: gpio_level_get = 0; otherwise = 1;
static bool gpio_level_get = 0;
void keypad_io_cfg(gpio_num_t gpio_num){

    //if pullmode = 0 -> pulldown  if pullmode = 1 -> pullup
    /* 1. 配置结构体 */
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << gpio_num),
        .mode         = GPIO_MODE_INPUT,      // 输入模式
        .pull_down_en = GPIO_PULLDOWN_DISABLE, // 下拉
        .pull_up_en   = GPIO_PULLUP_ENABLE,
        .intr_type    = GPIO_INTR_DISABLE,    // 不用中断
    };
    gpio_config(&io_conf);
}

bool keypad_get_key_value(gpio_num_t gpio_num){
    bool pressed = 0;
    if(gpio_get_level(gpio_num) == gpio_level_get){
        vTaskDelay(10);
        pressed = 1;
    }else{
        pressed = 0;
    }
    return pressed;
}