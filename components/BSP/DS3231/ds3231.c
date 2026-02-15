#include "ds3231.h"

/**
 * @brief Convert BCD (Binary Coded Decimal) to Decimal.
 * DS3231 registers are in BCD format[cite: 558, 563].
 */
static uint8_t bcd2dec(uint8_t val) {
    return ((val >> 4) * 10) + (val & 0x0F);
}

/**
 * @brief Convert Decimal to BCD.
 */
static uint8_t dec2bcd(uint8_t val) {
    return ((val / 10) << 4) + (val % 10);
}

esp_err_t ds3231_init(i2c_port_t port, int sda_pin, int scl_pin) {
    i2c_config_t conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = sda_pin,
        .scl_io_num = scl_pin,
        // SDA/SCL are open-drain and require pullup resistors [cite: 318, 698]
        .sda_pullup_en = GPIO_PULLUP_ENABLE, 
        .scl_pullup_en = GPIO_PULLUP_ENABLE, 
        // Fast Mode I2C supports up to 400kHz [cite: 21, 699]
        .master.clk_speed = 400000,          
    };
    esp_err_t err = i2c_param_config(port, &conf);
    if (err != ESP_OK) return err;
    return i2c_driver_install(port, conf.mode, 0, 0, 0);
}

esp_err_t ds3231_set_time(i2c_port_t port, ds3231_time_t *time) {
    uint8_t data[8];
    data[0] = DS3231_TIME_REG_START; // Register pointer [cite: 851]
    data[1] = dec2bcd(time->second); // 00h [cite: 396]
    data[2] = dec2bcd(time->minute); // 01h [cite: 402]
    // Bit 6 of Hours register selects 12/24 mode (0 for 24h) [cite: 564, 566]
    data[3] = dec2bcd(time->hour);   // 02h [cite: 410]
    data[4] = dec2bcd(time->day);    // 03h [cite: 418]
    data[5] = dec2bcd(time->date);   // 04h [cite: 427]
    data[6] = dec2bcd(time->month);  // 05h [cite: 435]
    data[7] = dec2bcd(time->year % 100); // 06h [cite: 443]

    // Transmit START condition and slave address followed by 8 bytes [cite: 711, 757, 847]
    return i2c_master_write_to_device(port, DS3231_ADDR, data, 8, 1000);
}

esp_err_t ds3231_get_time(i2c_port_t port, ds3231_time_t *time) {
    uint8_t reg_addr = DS3231_TIME_REG_START;
    uint8_t data[7];

    // Write address pointer then read 7 bytes. Secondary buffers ensure data integrity [cite: 570, 837, 863]
    esp_err_t err = i2c_master_write_read_device(port, DS3231_ADDR, &reg_addr, 1, data, 7, 1000);
    if (err != ESP_OK) return err;

    time->second = bcd2dec(data[0]);
    time->minute = bcd2dec(data[1]);
    // Mask bits for 24-hour mode hours [cite: 414]
    time->hour   = bcd2dec(data[2] & 0x3F); 
    time->day    = bcd2dec(data[3]);
    time->date   = bcd2dec(data[4]);
    // Mask century bit in month register [cite: 440, 567]
    time->month  = bcd2dec(data[5] & 0x1F); 
    time->year   = bcd2dec(data[6]) + 2000;

    return ESP_OK;
}