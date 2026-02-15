set(src_dirs         
            SPI
            LCD
            keypad
            wifi
            word_storage
            buzzer
            bat_percent
            ds3231
            RGB
            encoder
 
)
 
set(include_dirs            
            SPI
            LCD
            keypad
            wifi
            word_storage
            buzzer
            bat_percent
            ds3231
            RGB
            encoder
)
 
set(requires
            driver
            esp_timer
            esp_driver_ledc
            esp_wifi 
            esp_event 
            esp_netif
            nvs_flash
            esp_system
            spiffs
            esp_adc
            led_strip

)
 
idf_component_register(
                        SRC_DIRS ${src_dirs}
                        INCLUDE_DIRS ${include_dirs} 
                        REQUIRES ${requires}
)
 
component_compile_options(
                            -ffast-math 
                            -O3
                            -Wno-error=format=-Wno-format
                            -Werror=implicit-function-declaration
)