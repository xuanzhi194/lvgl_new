#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "lcd.h"
#include "lvgl.h"
#include "lv_port_disp.h"
#include "lv_port_indev.h"
#include "lv_tick.h"
#include "gui_guider.h"
#include "custom.h"
#include "events_init.h"
#include "keypad.h"
#include "wifi.h"
#include "nvs_flash.h"
#include "buzzer.h"
#include "word_storage.h"
#include "bat_percent.h"
#include "ds3231.h"
#include "ws2812b.h"
#include "ec06.h"
//---------- variables -----------------//
// const char *wifi_ssid = "wcy";
// const char *wifi_password = "wcy123456";
// const char *wifi_ssid = "wphone";
// const char *wifi_password = "seanhhhh";
const char *week_days[7] = {
    "Sunday",   // 0
    "Monday",   // 1
    "Tuesday",  // 2
    "Wednesday",// 3
    "Thursday", // 4
    "Friday",   // 5
    "Saturday"  // 6
};
lv_ui guider_ui;
bool screen_main_en = 0;
lv_timer_t * bat_timer = NULL;
bool init_ntp = 0;
//------------lvgl timer to battery show----------//
void my_battery_update_cb(lv_timer_t * timer) {
    // detect screen_main
    if (lv_scr_act() != guider_ui.screen_main) return;
    lv_obj_t * label = guider_ui.screen_main_label_battery;
    if(lv_obj_is_valid(label)) {
        int bat = get_battery_percentage();
        lv_label_set_text_fmt(label, "%d%%", bat);
    }
}

//------------nvs flash task thread---------------//
void nvs_thread(void *param){
    nvs_handle_t nvs_handle;
    nvs_handle_t timing_handle;
    nvs_open("List", NVS_READWRITE,&nvs_handle);
    nvs_open("Timing", NVS_READWRITE,&timing_handle);
     while (1)
     {
        if(todo_back_label){ //record info from todolist to flash
            nvs_set_i8(nvs_handle,"val",val);
            nvs_set_blob(nvs_handle, "done_array", done_array, sizeof(done_array));
            if(ESP_OK  != nvs_commit(nvs_handle)){
                ESP_LOGI("nvs","!!!!write flash fail!!!");
            }
            todo_back_label = 0;   
        }else if(main_load_label){ //load info from flash to todolist
            nvs_get_i8(nvs_handle,"val",&val);
            size_t len = sizeof(done_array);
            nvs_get_blob(nvs_handle, "done_array", done_array, &len);
            ESP_LOGI("nvs","val = %d\r\n",val);
            main_load_label = 0;
        }else if(led_green_en){
            led_green_en = 0;
            set_flow_light(34, 80, 32);
        }else if(led_red_en){
            led_red_en = 0;
            set_flow_light(80, 32, 33);
        }else if(wordcard_change){
            get_word_from_csv(book_info[wordbook_index].word_index, &current_word,book_info[wordbook_index].book_name);
            lv_label_set_text(guider_ui.screen_wordcard_label_spelling,current_word.word);
            lv_obj_set_style_text_font(guider_ui.screen_wordcard_label_phonetic, &lv_font_arial_14, 0);
            lv_label_set_text(guider_ui.screen_wordcard_label_phonetic,current_word.phonetic);
            lv_label_set_text(guider_ui.screen_wordcard_label_meaning,current_word.definition);
            wordcard_change = 0;
            vTaskDelay(50);
        }else if(reviewcard_change){
            get_word_from_csv(book_info[wordbook_index].review_absoulte_index[review_index], &current_word,book_info[wordbook_index].book_name);
            lv_label_set_text(guider_ui.screen_reviewcard_label_spelling,current_word.word);
            lv_obj_set_style_text_font(guider_ui.screen_reviewcard_label_phonetic,&lv_font_arial_14, 0);
            lv_label_set_text(guider_ui.screen_reviewcard_label_phonetic,current_word.phonetic);
            lv_label_set_text(guider_ui.screen_reviewcard_label_meaning,current_word.definition);
            reviewcard_change = 0;
            vTaskDelay(50);
        }
        vTaskDelay(10);
     }

}

//------------Get real time thread---------------//
void wifi_time_thread(void *arg)
{
    while (1)
    {
        if(task_real_time_en){
            if(is_wifi_connected()){
                time_t now;
                struct tm timeinfo;
                time(&now);
                localtime_r(&now, &timeinfo);
                // copy info to flash
                timing_year = timeinfo.tm_year + 1900;
                timing_month = timeinfo.tm_mon + 1;
                timing_day = timeinfo.tm_mday;
                timing_weekday = timeinfo.tm_wday;
                //ESP_LOGI("TIMING","%04d-%02d-%02d %s\r\n",timing_year,timing_month,timing_day,week_days[timeinfo.tm_wday]);
                ESP_LOGI("REAL_TIME", "Current time: %04d-%02d-%02d %02d:%02d:%02d",
                timeinfo.tm_year + 1900, timeinfo.tm_mon + 1, timeinfo.tm_mday,
                timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);
                char date_str[30];   // "YYYY/MM/DD" + '\0'
                char time_str[20];    // "HH:MM:SS"   + '\0'
                snprintf(date_str, sizeof(date_str), "%04d-%02d-%02d",
                        timeinfo.tm_year + 1900,
                        timeinfo.tm_mon + 1,
                        timeinfo.tm_mday);
                snprintf(time_str, sizeof(time_str), "%02d:%02d",
                        timeinfo.tm_hour,
                        timeinfo.tm_min);
                
                if((timeinfo.tm_hour >= 19 && timeinfo.tm_hour <= 24) || (timeinfo.tm_hour >= 0 && timeinfo.tm_hour <= 5)){
                    lv_obj_clear_flag(guider_ui.screen_timing_img_night, LV_OBJ_FLAG_HIDDEN);
                    lv_obj_add_flag(guider_ui.screen_timing_img_morning, LV_OBJ_FLAG_HIDDEN);
                }else{
                    lv_obj_clear_flag(guider_ui.screen_timing_img_morning, LV_OBJ_FLAG_HIDDEN);
                    lv_obj_add_flag(guider_ui.screen_timing_img_night, LV_OBJ_FLAG_HIDDEN);
                }
                //show time in lvgl and set time to ds3231
                if(timeinfo.tm_year+1900 >= 2026){
                    lv_label_set_text(guider_ui.screen_timing_label_date,date_str);
                    lv_label_set_text(guider_ui.screen_timing_label_realtime,time_str);
                    lv_label_set_text(guider_ui.screen_timing_label_day,week_days[timeinfo.tm_wday]);
                    //calibration time to ds3231
                    ds3231_time_t set_time = {
                        .second = timeinfo.tm_sec, .minute = timeinfo.tm_min, .hour = timeinfo.tm_hour,
                        .day = timeinfo.tm_wday, .date = timeinfo.tm_mday, .month = timeinfo.tm_mon+1, .year = timeinfo.tm_year
                    };
                    ds3231_set_time(I2C_NUM_0, &set_time);
                }
                vTaskDelay(990);
            }else{
                ds3231_time_t now;
                ds3231_get_time(I2C_NUM_0, &now);
                char date_str[30];
                char time_str[20];
                snprintf(date_str, sizeof(date_str), "%04d-%02d-%02d",
                        now.year,
                        now.month,
                        now.date);
                snprintf(time_str, sizeof(time_str), "%02d:%02d",
                        now.hour,
                        now.minute);
                lv_label_set_text(guider_ui.screen_timing_label_date,date_str);
                lv_label_set_text(guider_ui.screen_timing_label_realtime,time_str);
                lv_label_set_text(guider_ui.screen_timing_label_day,week_days[now.day]); 
                if((now.hour >= 19 && now.hour <= 24) || (now.hour >= 0 && now.hour <= 5)){
                    lv_obj_clear_flag(guider_ui.screen_timing_img_night, LV_OBJ_FLAG_HIDDEN);
                    lv_obj_add_flag(guider_ui.screen_timing_img_morning, LV_OBJ_FLAG_HIDDEN);
                }else{
                    lv_obj_clear_flag(guider_ui.screen_timing_img_morning, LV_OBJ_FLAG_HIDDEN);
                    lv_obj_add_flag(guider_ui.screen_timing_img_night, LV_OBJ_FLAG_HIDDEN);
                }
                vTaskDelay(990);
            }
        }else if(wifi_scan_en){
            //-----------------------scan wifi---------------------//
            wifi_scan_top_5();
            // wifi item btn label modify from wifi scan info
            for(int i = 0; i < g_scan_ap_num ; i++){
                lv_obj_t * list_btn = lv_obj_get_child(guider_ui.screen_wificfg_list_1, i);
                lv_obj_t * label = lv_obj_get_child(list_btn, -1);    
                if(label != NULL && lv_obj_is_valid(label)) {
                    lv_label_set_text(label,g_scan_results[i].ssid);
                }            
            }
            wifi_scan_en = 0;
        }else if(wifi_connect_en){
            //------------------connect to wifi------------------//
            char * wifi_password = lv_textarea_get_text(guider_ui.screen_wificfg_ta_password);
            wifi_connect_to_new_network(wifi_ssid,wifi_password);
            vTaskDelay(3000);
            wifi_success = is_wifi_connected();
            if(wifi_success){
                wifi_connect_show();
                if(init_ntp == 0){
                    initialize_sntp();
                    init_ntp = 1;
                }
            }else{
                wifi_disconnect_show();
            }
            wifi_connect_en = 0; 
        }else if(wifi_disconnect_en){
            esp_wifi_disconnect();
            wifi_disconnect_en = 0;
            wifi_success = 0;
        }
        vTaskDelay(10);
    }
}

//-------------main loop-------------------------//
void app_main(void)
{
    //-----------RGB FLOW LIGHT INIT------------//
    init_led_strip();
    set_flow_light(51,64,69); //blue
    set_flow_light(10,24,49);
    set_flow_light(20,20,20);
    //-----------encoder init-------------------//
    init_encoder_direction();
    //-----------buzzer init--------------------//
    buzzer_init();
    //-----------battery show-------------------//
    battery_adc_init();
    //-----------DS3231 INIT--------------------//
    ds3231_init(I2C_NUM_0, 15, 16); // GPIO 15 (SDA) and GPIO 16 (SCL)
    //--------------NVS init--------------------//
    //nvs flash init
    esp_err_t ret;
    //initialize nvs flash
    ret = nvs_flash_init();
    if(ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND){
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    //----------init spiffs for word card-----------//
    init_spiffs();
    //----------wifi cfg init-----------------//
    //wifi sta mode
    init_wifi("dummy","dummy");
    init_ntp = 0;
    // ------------set lvgl by gui guider-----------//
    // LVGL initialize
    lvgl_tick_timer_init(); // init lvgl timer
    lv_init();              // init lvgl
    lv_port_disp_init();    // init lvgl display cfg
    lv_port_indev_init();   // init lvgl indev
    setup_ui(&guider_ui);   // connect to gui guider 
    lv_indev_set_group(indev_keypad, g);

    //-------------multi task thread----------------//
    xTaskCreatePinnedToCore(nvs_thread,"nvs_thread",4096,NULL,10,NULL,0);
    xTaskCreatePinnedToCore(wifi_time_thread,"time_thread",4096,NULL,10,NULL,1);

    //--------------main loop task-----------------//
    while (1) 
    {
        // -----------------LVGL task managing-----------------//
        lv_task_handler();  // LVGL task managing
        // -----------------battery timer process--------------//
        if(lv_scr_act() == guider_ui.screen_main && !screen_main_en){
            screen_main_en = 1;
            lv_obj_t * label = guider_ui.screen_main_label_battery;
            if(lv_obj_is_valid(label) && label != NULL) {
                int bat = get_battery_percentage();
                lv_label_set_text_fmt(label, "%d%%", bat);
            }
            bat_timer = lv_timer_create(my_battery_update_cb,2000,NULL);
        }else if(lv_scr_act() != guider_ui.screen_main && screen_main_en){
            screen_main_en = 0;
            lv_timer_del(bat_timer);
            bat_timer = NULL;
        }
        //-----------------------------------------------------//
        vTaskDelay(10);
    }
    
}


// void app_main(void) {
//     init_encoder_direction();
//     init_led_strip();
//     buzzer_init();
//     while (1)
//     {
//         set_flow_light(55,10,0);
//         vTaskDelay(10);
//         // buzzer_set_sound(2000,50);
//         // vTaskDelay(1000);
//         // buzzer_set_sound(2000,0);
//         // vTaskDelay(1000);
//     }
    
// }

 