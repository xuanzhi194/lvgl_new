#ifndef DS3231_H
#define DS3231_H
#include "driver/i2c.h"

// DS3231 7-bit I2C address is 1101000b (0x68)
#define DS3231_ADDR             0x68    
// Timekeeping registers start at address 00h
#define DS3231_TIME_REG_START   0x00    

/**
 * @brief Structure to hold RTC time information.
 * The RTC manages seconds, minutes, hours, day, date, month, and year.
 */
typedef struct {
    uint8_t second;
    uint8_t minute;
    uint8_t hour;   // Supports 24-hour or 12-hour format
    uint8_t day;    // Day of the week (1-7)
    uint8_t date;   // Date of the month (1-31)
    uint8_t month;  // Month (01-12)
    uint16_t year;  // Year (00-99) with leap-year compensation
} ds3231_time_t;

/**
 * @brief Initialize I2C master for DS3231
 */
esp_err_t ds3231_init(i2c_port_t port, int sda_pin, int scl_pin);

/**
 * @brief Write time data to DS3231 registers
 */
esp_err_t ds3231_set_time(i2c_port_t port, ds3231_time_t *time);

/**
 * @brief Read current time data from DS3231
 */
esp_err_t ds3231_get_time(i2c_port_t port, ds3231_time_t *time);

#endif