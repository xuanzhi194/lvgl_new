#include "esp_adc/adc_oneshot.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "nvs_flash.h"
#include "esp_netif.h"    
#include "esp_err.h"
#include "esp_sntp.h"
#include "esp_log.h"

// 定义参数
#define BAT_ADC_CHAN          ADC_CHANNEL_7       // GPIO8 对应 ADC1_CH7
#define BAT_ADC_ATTEN         ADC_ATTEN_DB_12     // 12dB 衰减，可测量范围 0-3.1V
#define VOLTAGE_DIVIDER_RATIO 2                   // 100k + 100k 分压比
#define BAT_MIN_VOLT          3100                // 0% 电量对应 3100mV
#define BAT_MAX_VOLT          4200                // 100% 电量对应 4200mV

void battery_adc_init();
int get_battery_percentage();