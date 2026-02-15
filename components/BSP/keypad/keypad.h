#ifndef __KEYPAD_H_
#define __KEYPAD_H_
#include <stdint.h>
#include "driver/gpio.h"
void keypad_io_cfg(gpio_num_t gpio_num);
bool keypad_get_key_value(gpio_num_t gpio_num);
#endif