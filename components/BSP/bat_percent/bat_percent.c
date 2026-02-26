#include "bat_percent.h"

static const char *TAG = "BAT_MONITOR";

static adc_oneshot_unit_handle_t adc1_handle;
static adc_cali_handle_t adc1_cali_handle = NULL;

void battery_adc_init(void) {
    // 1. 初始化 ADC 单元
    adc_oneshot_unit_init_cfg_t init_config1 = {
        .unit_id = ADC_UNIT_1,
    };
    adc_oneshot_new_unit(&init_config1, &adc1_handle);

    // 2. 配置通道
    adc_oneshot_chan_cfg_t config = {
        .bitwidth = ADC_BITWIDTH_DEFAULT,
        .atten = BAT_ADC_ATTEN,
    };
    adc_oneshot_config_channel(adc1_handle, BAT_ADC_CHAN, &config);

    // 3. 校准方案：改为 curve_fitting (曲线拟合) 以解决兼容性错误
    adc_cali_curve_fitting_config_t cali_config = {
        .unit_id = ADC_UNIT_1,
        .chan = BAT_ADC_CHAN,
        .atten = BAT_ADC_ATTEN,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };
    
    // 尝试创建校准句柄
    esp_err_t ret = adc_cali_create_scheme_curve_fitting(&cali_config, &adc1_cali_handle);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ADC create handle fail\r\n");
    }
}

int get_battery_percentage(void) {
    // Multi-sample averaging: read 16 times to reduce ADC noise
    #define BAT_SAMPLE_COUNT 16
    int32_t adc_sum = 0;
    int adc_raw;
    for (int i = 0; i < BAT_SAMPLE_COUNT; i++) {
        adc_oneshot_read(adc1_handle, BAT_ADC_CHAN, &adc_raw);
        adc_sum += adc_raw;
    }
    int adc_avg = (int)(adc_sum / BAT_SAMPLE_COUNT);

    int voltage_mv;
    if (adc1_cali_handle) {
        adc_cali_raw_to_voltage(adc1_cali_handle, adc_avg, &voltage_mv);
    } else {
        // Approximate when no calibration (12bit, 12dB ~3100mV full scale)
        voltage_mv = adc_avg * 3100 / 4095;
    }

    int battery_voltage = voltage_mv * VOLTAGE_DIVIDER_RATIO;
    int percentage = (battery_voltage - BAT_MIN_VOLT) * 100 / (BAT_MAX_VOLT - BAT_MIN_VOLT);

    if (percentage > 100) percentage = 100;
    if (percentage < 0)   percentage = 0;

    return percentage;
}