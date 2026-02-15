/*
* Copyright 2026 NXP
* NXP Proprietary. This software is owned or controlled by NXP and may only be used strictly in
* accordance with the applicable license terms. By expressly accepting such terms or by downloading, installing,
* activating and/or otherwise using the software, you are agreeing that you have read, and that you agree to
* comply with and are bound by, such license terms.  If you do not agree to be bound by the applicable license
* terms, then you may not retain, install, activate or otherwise use the software.
*/

#include "lvgl.h"
#include <stdio.h>
#include "gui_guider.h"
#include "events_init.h"
#include "widgets_init.h"
#include "custom.h"



void setup_scr_screen_setting(lv_ui *ui)
{
    //Write codes screen_setting
    ui->screen_setting = lv_obj_create(NULL);
    lv_obj_set_size(ui->screen_setting, 320, 170);
    lv_obj_set_scrollbar_mode(ui->screen_setting, LV_SCROLLBAR_MODE_OFF);

    //Write style for screen_setting, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_bg_opa(ui->screen_setting, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_src(ui->screen_setting, &_screen_setting_bg2_320x170, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_opa(ui->screen_setting, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_recolor(ui->screen_setting, lv_color_hex(0x7987a6), LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_recolor_opa(ui->screen_setting, 21, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write codes screen_setting_cont_menu
    ui->screen_setting_cont_menu = lv_obj_create(ui->screen_setting);
    lv_obj_set_pos(ui->screen_setting_cont_menu, 0, 0);
    lv_obj_set_size(ui->screen_setting_cont_menu, 320, 170);
    lv_obj_set_scrollbar_mode(ui->screen_setting_cont_menu, LV_SCROLLBAR_MODE_OFF);

    //Write style for screen_setting_cont_menu, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_border_width(ui->screen_setting_cont_menu, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_setting_cont_menu, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_opa(ui->screen_setting_cont_menu, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_top(ui->screen_setting_cont_menu, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_bottom(ui->screen_setting_cont_menu, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_left(ui->screen_setting_cont_menu, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_right(ui->screen_setting_cont_menu, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_shadow_width(ui->screen_setting_cont_menu, 0, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write codes screen_setting_btn_wifi
    ui->screen_setting_btn_wifi = lv_btn_create(ui->screen_setting_cont_menu);
    ui->screen_setting_btn_wifi_label = lv_label_create(ui->screen_setting_btn_wifi);
    lv_label_set_text(ui->screen_setting_btn_wifi_label, "");
    lv_label_set_long_mode(ui->screen_setting_btn_wifi_label, LV_LABEL_LONG_WRAP);
    lv_obj_align(ui->screen_setting_btn_wifi_label, LV_ALIGN_CENTER, 0, 0);
    lv_obj_set_style_pad_all(ui->screen_setting_btn_wifi, 0, LV_STATE_DEFAULT);
    lv_obj_set_width(ui->screen_setting_btn_wifi_label, LV_PCT(100));
    lv_obj_set_pos(ui->screen_setting_btn_wifi, 80, 43);
    lv_obj_set_size(ui->screen_setting_btn_wifi, 65, 65);

    //Write style for screen_setting_btn_wifi, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_bg_opa(ui->screen_setting_btn_wifi, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_border_width(ui->screen_setting_btn_wifi, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_setting_btn_wifi, 5, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_shadow_width(ui->screen_setting_btn_wifi, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_src(ui->screen_setting_btn_wifi, &_wifi_icon_65x65, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_opa(ui->screen_setting_btn_wifi, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_recolor_opa(ui->screen_setting_btn_wifi, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_color(ui->screen_setting_btn_wifi, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_font(ui->screen_setting_btn_wifi, &lv_font_montserratMedium_16, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_opa(ui->screen_setting_btn_wifi, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_align(ui->screen_setting_btn_wifi, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write style for screen_setting_btn_wifi, Part: LV_PART_MAIN, State: LV_STATE_FOCUSED.
    lv_obj_set_style_bg_opa(ui->screen_setting_btn_wifi, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_border_width(ui->screen_setting_btn_wifi, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_radius(ui->screen_setting_btn_wifi, 5, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_width(ui->screen_setting_btn_wifi, 5, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_color(ui->screen_setting_btn_wifi, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_opa(ui->screen_setting_btn_wifi, 255, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_spread(ui->screen_setting_btn_wifi, 1, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_ofs_x(ui->screen_setting_btn_wifi, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_ofs_y(ui->screen_setting_btn_wifi, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_src(ui->screen_setting_btn_wifi, &_wifi_icon_65x65, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_opa(ui->screen_setting_btn_wifi, 255, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_recolor_opa(ui->screen_setting_btn_wifi, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_color(ui->screen_setting_btn_wifi, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_font(ui->screen_setting_btn_wifi, &lv_font_montserratMedium_16, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_opa(ui->screen_setting_btn_wifi, 255, LV_PART_MAIN|LV_STATE_FOCUSED);

    //Write style for screen_setting_btn_wifi, Part: LV_PART_MAIN, State: LV_STATE_PRESSED.
    lv_obj_set_style_bg_opa(ui->screen_setting_btn_wifi, 0, LV_PART_MAIN|LV_STATE_PRESSED);
    lv_obj_set_style_border_width(ui->screen_setting_btn_wifi, 0, LV_PART_MAIN|LV_STATE_PRESSED);
    lv_obj_set_style_radius(ui->screen_setting_btn_wifi, 5, LV_PART_MAIN|LV_STATE_PRESSED);
    lv_obj_set_style_shadow_width(ui->screen_setting_btn_wifi, 0, LV_PART_MAIN|LV_STATE_PRESSED);
    lv_obj_set_style_bg_img_src(ui->screen_setting_btn_wifi, &_wifi_icon_65x65, LV_PART_MAIN|LV_STATE_PRESSED);
    lv_obj_set_style_bg_img_opa(ui->screen_setting_btn_wifi, 255, LV_PART_MAIN|LV_STATE_PRESSED);
    lv_obj_set_style_bg_img_recolor_opa(ui->screen_setting_btn_wifi, 0, LV_PART_MAIN|LV_STATE_PRESSED);
    lv_obj_set_style_text_color(ui->screen_setting_btn_wifi, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_PRESSED);
    lv_obj_set_style_text_font(ui->screen_setting_btn_wifi, &lv_font_montserratMedium_16, LV_PART_MAIN|LV_STATE_PRESSED);
    lv_obj_set_style_text_opa(ui->screen_setting_btn_wifi, 255, LV_PART_MAIN|LV_STATE_PRESSED);

    //Write codes screen_setting_btn_vocab
    ui->screen_setting_btn_vocab = lv_btn_create(ui->screen_setting_cont_menu);
    ui->screen_setting_btn_vocab_label = lv_label_create(ui->screen_setting_btn_vocab);
    lv_label_set_text(ui->screen_setting_btn_vocab_label, "");
    lv_label_set_long_mode(ui->screen_setting_btn_vocab_label, LV_LABEL_LONG_WRAP);
    lv_obj_align(ui->screen_setting_btn_vocab_label, LV_ALIGN_CENTER, 0, 0);
    lv_obj_set_style_pad_all(ui->screen_setting_btn_vocab, 0, LV_STATE_DEFAULT);
    lv_obj_set_width(ui->screen_setting_btn_vocab_label, LV_PCT(100));
    lv_obj_set_pos(ui->screen_setting_btn_vocab, 172, 42);
    lv_obj_set_size(ui->screen_setting_btn_vocab, 65, 65);

    //Write style for screen_setting_btn_vocab, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_bg_opa(ui->screen_setting_btn_vocab, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_border_width(ui->screen_setting_btn_vocab, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_setting_btn_vocab, 5, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_shadow_width(ui->screen_setting_btn_vocab, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_src(ui->screen_setting_btn_vocab, &_vocab_icon_65x65, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_opa(ui->screen_setting_btn_vocab, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_recolor_opa(ui->screen_setting_btn_vocab, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_color(ui->screen_setting_btn_vocab, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_font(ui->screen_setting_btn_vocab, &lv_font_montserratMedium_16, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_opa(ui->screen_setting_btn_vocab, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_align(ui->screen_setting_btn_vocab, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write style for screen_setting_btn_vocab, Part: LV_PART_MAIN, State: LV_STATE_FOCUSED.
    lv_obj_set_style_bg_opa(ui->screen_setting_btn_vocab, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_border_width(ui->screen_setting_btn_vocab, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_radius(ui->screen_setting_btn_vocab, 5, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_width(ui->screen_setting_btn_vocab, 5, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_color(ui->screen_setting_btn_vocab, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_opa(ui->screen_setting_btn_vocab, 255, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_spread(ui->screen_setting_btn_vocab, 1, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_ofs_x(ui->screen_setting_btn_vocab, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_ofs_y(ui->screen_setting_btn_vocab, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_src(ui->screen_setting_btn_vocab, &_vocab_icon_65x65, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_opa(ui->screen_setting_btn_vocab, 255, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_recolor_opa(ui->screen_setting_btn_vocab, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_color(ui->screen_setting_btn_vocab, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_font(ui->screen_setting_btn_vocab, &lv_font_montserratMedium_16, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_opa(ui->screen_setting_btn_vocab, 255, LV_PART_MAIN|LV_STATE_FOCUSED);

    //Write codes screen_setting_btn_laba
    ui->screen_setting_btn_laba = lv_btn_create(ui->screen_setting_cont_menu);
    ui->screen_setting_btn_laba_label = lv_label_create(ui->screen_setting_btn_laba);
    lv_label_set_text(ui->screen_setting_btn_laba_label, "");
    lv_label_set_long_mode(ui->screen_setting_btn_laba_label, LV_LABEL_LONG_WRAP);
    lv_obj_align(ui->screen_setting_btn_laba_label, LV_ALIGN_CENTER, 0, 0);
    lv_obj_set_style_pad_all(ui->screen_setting_btn_laba, 0, LV_STATE_DEFAULT);
    lv_obj_set_width(ui->screen_setting_btn_laba_label, LV_PCT(100));
    lv_obj_set_pos(ui->screen_setting_btn_laba, 111, 44);
    lv_obj_set_size(ui->screen_setting_btn_laba, 65, 65);

    //Write style for screen_setting_btn_laba, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_bg_opa(ui->screen_setting_btn_laba, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_border_width(ui->screen_setting_btn_laba, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_setting_btn_laba, 5, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_shadow_width(ui->screen_setting_btn_laba, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_src(ui->screen_setting_btn_laba, &_laba_icon_65x65, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_opa(ui->screen_setting_btn_laba, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_recolor_opa(ui->screen_setting_btn_laba, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_color(ui->screen_setting_btn_laba, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_font(ui->screen_setting_btn_laba, &lv_font_montserratMedium_16, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_opa(ui->screen_setting_btn_laba, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_align(ui->screen_setting_btn_laba, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write style for screen_setting_btn_laba, Part: LV_PART_MAIN, State: LV_STATE_FOCUSED.
    lv_obj_set_style_bg_opa(ui->screen_setting_btn_laba, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_border_width(ui->screen_setting_btn_laba, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_radius(ui->screen_setting_btn_laba, 5, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_width(ui->screen_setting_btn_laba, 5, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_color(ui->screen_setting_btn_laba, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_opa(ui->screen_setting_btn_laba, 255, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_spread(ui->screen_setting_btn_laba, 1, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_ofs_x(ui->screen_setting_btn_laba, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_ofs_y(ui->screen_setting_btn_laba, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_src(ui->screen_setting_btn_laba, &_laba_icon_65x65, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_opa(ui->screen_setting_btn_laba, 255, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_recolor_opa(ui->screen_setting_btn_laba, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_color(ui->screen_setting_btn_laba, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_font(ui->screen_setting_btn_laba, &lv_font_montserratMedium_16, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_opa(ui->screen_setting_btn_laba, 255, LV_PART_MAIN|LV_STATE_FOCUSED);

    //Write codes screen_setting_btn_timer
    ui->screen_setting_btn_timer = lv_btn_create(ui->screen_setting_cont_menu);
    ui->screen_setting_btn_timer_label = lv_label_create(ui->screen_setting_btn_timer);
    lv_label_set_text(ui->screen_setting_btn_timer_label, "");
    lv_label_set_long_mode(ui->screen_setting_btn_timer_label, LV_LABEL_LONG_WRAP);
    lv_obj_align(ui->screen_setting_btn_timer_label, LV_ALIGN_CENTER, 0, 0);
    lv_obj_set_style_pad_all(ui->screen_setting_btn_timer, 0, LV_STATE_DEFAULT);
    lv_obj_set_width(ui->screen_setting_btn_timer_label, LV_PCT(100));
    lv_obj_set_pos(ui->screen_setting_btn_timer, 197, 41);
    lv_obj_set_size(ui->screen_setting_btn_timer, 65, 65);

    //Write style for screen_setting_btn_timer, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_bg_opa(ui->screen_setting_btn_timer, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_border_width(ui->screen_setting_btn_timer, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_setting_btn_timer, 5, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_shadow_width(ui->screen_setting_btn_timer, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_src(ui->screen_setting_btn_timer, &_timer_icon_65x65, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_opa(ui->screen_setting_btn_timer, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_recolor_opa(ui->screen_setting_btn_timer, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_color(ui->screen_setting_btn_timer, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_font(ui->screen_setting_btn_timer, &lv_font_montserratMedium_16, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_opa(ui->screen_setting_btn_timer, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_align(ui->screen_setting_btn_timer, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write style for screen_setting_btn_timer, Part: LV_PART_MAIN, State: LV_STATE_FOCUSED.
    lv_obj_set_style_bg_opa(ui->screen_setting_btn_timer, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_border_width(ui->screen_setting_btn_timer, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_radius(ui->screen_setting_btn_timer, 5, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_width(ui->screen_setting_btn_timer, 5, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_color(ui->screen_setting_btn_timer, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_opa(ui->screen_setting_btn_timer, 255, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_spread(ui->screen_setting_btn_timer, 1, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_ofs_x(ui->screen_setting_btn_timer, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_ofs_y(ui->screen_setting_btn_timer, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_src(ui->screen_setting_btn_timer, &_timer_icon_65x65, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_opa(ui->screen_setting_btn_timer, 255, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_recolor_opa(ui->screen_setting_btn_timer, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_color(ui->screen_setting_btn_timer, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_font(ui->screen_setting_btn_timer, &lv_font_montserratMedium_16, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_opa(ui->screen_setting_btn_timer, 255, LV_PART_MAIN|LV_STATE_FOCUSED);

    //Write codes screen_setting_btn_ble
    ui->screen_setting_btn_ble = lv_btn_create(ui->screen_setting_cont_menu);
    ui->screen_setting_btn_ble_label = lv_label_create(ui->screen_setting_btn_ble);
    lv_label_set_text(ui->screen_setting_btn_ble_label, "");
    lv_label_set_long_mode(ui->screen_setting_btn_ble_label, LV_LABEL_LONG_WRAP);
    lv_obj_align(ui->screen_setting_btn_ble_label, LV_ALIGN_CENTER, 0, 0);
    lv_obj_set_style_pad_all(ui->screen_setting_btn_ble, 0, LV_STATE_DEFAULT);
    lv_obj_set_width(ui->screen_setting_btn_ble_label, LV_PCT(100));
    lv_obj_set_pos(ui->screen_setting_btn_ble, 41, 44);
    lv_obj_set_size(ui->screen_setting_btn_ble, 65, 65);

    //Write style for screen_setting_btn_ble, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_bg_opa(ui->screen_setting_btn_ble, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_border_width(ui->screen_setting_btn_ble, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_setting_btn_ble, 5, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_shadow_width(ui->screen_setting_btn_ble, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_src(ui->screen_setting_btn_ble, &_ble_icon_65x65, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_opa(ui->screen_setting_btn_ble, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_recolor_opa(ui->screen_setting_btn_ble, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_color(ui->screen_setting_btn_ble, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_font(ui->screen_setting_btn_ble, &lv_font_montserratMedium_16, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_opa(ui->screen_setting_btn_ble, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_align(ui->screen_setting_btn_ble, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write style for screen_setting_btn_ble, Part: LV_PART_MAIN, State: LV_STATE_FOCUSED.
    lv_obj_set_style_bg_opa(ui->screen_setting_btn_ble, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_border_width(ui->screen_setting_btn_ble, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_radius(ui->screen_setting_btn_ble, 5, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_width(ui->screen_setting_btn_ble, 5, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_color(ui->screen_setting_btn_ble, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_opa(ui->screen_setting_btn_ble, 255, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_spread(ui->screen_setting_btn_ble, 1, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_ofs_x(ui->screen_setting_btn_ble, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_ofs_y(ui->screen_setting_btn_ble, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_src(ui->screen_setting_btn_ble, &_ble_icon_65x65, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_opa(ui->screen_setting_btn_ble, 255, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_recolor_opa(ui->screen_setting_btn_ble, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_color(ui->screen_setting_btn_ble, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_font(ui->screen_setting_btn_ble, &lv_font_montserratMedium_16, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_opa(ui->screen_setting_btn_ble, 255, LV_PART_MAIN|LV_STATE_FOCUSED);

    //Write codes screen_setting_btn_general
    ui->screen_setting_btn_general = lv_btn_create(ui->screen_setting_cont_menu);
    ui->screen_setting_btn_general_label = lv_label_create(ui->screen_setting_btn_general);
    lv_label_set_text(ui->screen_setting_btn_general_label, "");
    lv_label_set_long_mode(ui->screen_setting_btn_general_label, LV_LABEL_LONG_WRAP);
    lv_obj_align(ui->screen_setting_btn_general_label, LV_ALIGN_CENTER, 0, 0);
    lv_obj_set_style_pad_all(ui->screen_setting_btn_general, 0, LV_STATE_DEFAULT);
    lv_obj_set_width(ui->screen_setting_btn_general_label, LV_PCT(100));
    lv_obj_set_pos(ui->screen_setting_btn_general, 9, 43);
    lv_obj_set_size(ui->screen_setting_btn_general, 65, 65);

    //Write style for screen_setting_btn_general, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_bg_opa(ui->screen_setting_btn_general, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_border_width(ui->screen_setting_btn_general, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_setting_btn_general, 5, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_shadow_width(ui->screen_setting_btn_general, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_src(ui->screen_setting_btn_general, &_general_icon_65x65, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_opa(ui->screen_setting_btn_general, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_recolor_opa(ui->screen_setting_btn_general, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_color(ui->screen_setting_btn_general, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_font(ui->screen_setting_btn_general, &lv_font_montserratMedium_16, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_opa(ui->screen_setting_btn_general, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_align(ui->screen_setting_btn_general, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write style for screen_setting_btn_general, Part: LV_PART_MAIN, State: LV_STATE_FOCUSED.
    lv_obj_set_style_bg_opa(ui->screen_setting_btn_general, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_border_width(ui->screen_setting_btn_general, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_radius(ui->screen_setting_btn_general, 5, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_width(ui->screen_setting_btn_general, 5, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_color(ui->screen_setting_btn_general, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_opa(ui->screen_setting_btn_general, 255, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_spread(ui->screen_setting_btn_general, 1, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_ofs_x(ui->screen_setting_btn_general, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_ofs_y(ui->screen_setting_btn_general, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_src(ui->screen_setting_btn_general, &_general_icon_65x65, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_opa(ui->screen_setting_btn_general, 255, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_recolor_opa(ui->screen_setting_btn_general, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_color(ui->screen_setting_btn_general, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_font(ui->screen_setting_btn_general, &lv_font_montserratMedium_16, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_opa(ui->screen_setting_btn_general, 255, LV_PART_MAIN|LV_STATE_FOCUSED);

    //Write codes screen_setting_btn_data
    ui->screen_setting_btn_data = lv_btn_create(ui->screen_setting_cont_menu);
    ui->screen_setting_btn_data_label = lv_label_create(ui->screen_setting_btn_data);
    lv_label_set_text(ui->screen_setting_btn_data_label, "");
    lv_label_set_long_mode(ui->screen_setting_btn_data_label, LV_LABEL_LONG_WRAP);
    lv_obj_align(ui->screen_setting_btn_data_label, LV_ALIGN_CENTER, 0, 0);
    lv_obj_set_style_pad_all(ui->screen_setting_btn_data, 0, LV_STATE_DEFAULT);
    lv_obj_set_width(ui->screen_setting_btn_data_label, LV_PCT(100));
    lv_obj_set_pos(ui->screen_setting_btn_data, 148, 43);
    lv_obj_set_size(ui->screen_setting_btn_data, 65, 65);

    //Write style for screen_setting_btn_data, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_bg_opa(ui->screen_setting_btn_data, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_border_width(ui->screen_setting_btn_data, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_setting_btn_data, 5, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_shadow_width(ui->screen_setting_btn_data, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_src(ui->screen_setting_btn_data, &_data_icon_65x65, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_opa(ui->screen_setting_btn_data, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_recolor_opa(ui->screen_setting_btn_data, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_color(ui->screen_setting_btn_data, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_font(ui->screen_setting_btn_data, &lv_font_montserratMedium_16, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_opa(ui->screen_setting_btn_data, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_align(ui->screen_setting_btn_data, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write style for screen_setting_btn_data, Part: LV_PART_MAIN, State: LV_STATE_FOCUSED.
    lv_obj_set_style_bg_opa(ui->screen_setting_btn_data, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_border_width(ui->screen_setting_btn_data, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_radius(ui->screen_setting_btn_data, 5, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_width(ui->screen_setting_btn_data, 5, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_color(ui->screen_setting_btn_data, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_opa(ui->screen_setting_btn_data, 255, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_spread(ui->screen_setting_btn_data, 1, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_ofs_x(ui->screen_setting_btn_data, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_ofs_y(ui->screen_setting_btn_data, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_src(ui->screen_setting_btn_data, &_data_icon_65x65, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_opa(ui->screen_setting_btn_data, 255, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_recolor_opa(ui->screen_setting_btn_data, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_color(ui->screen_setting_btn_data, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_font(ui->screen_setting_btn_data, &lv_font_montserratMedium_16, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_opa(ui->screen_setting_btn_data, 255, LV_PART_MAIN|LV_STATE_FOCUSED);

    //Write codes screen_setting_btn_todo
    ui->screen_setting_btn_todo = lv_btn_create(ui->screen_setting_cont_menu);
    ui->screen_setting_btn_todo_label = lv_label_create(ui->screen_setting_btn_todo);
    lv_label_set_text(ui->screen_setting_btn_todo_label, "");
    lv_label_set_long_mode(ui->screen_setting_btn_todo_label, LV_LABEL_LONG_WRAP);
    lv_obj_align(ui->screen_setting_btn_todo_label, LV_ALIGN_CENTER, 0, 0);
    lv_obj_set_style_pad_all(ui->screen_setting_btn_todo, 0, LV_STATE_DEFAULT);
    lv_obj_set_width(ui->screen_setting_btn_todo_label, LV_PCT(100));
    lv_obj_set_pos(ui->screen_setting_btn_todo, 239, 40);
    lv_obj_set_size(ui->screen_setting_btn_todo, 65, 65);

    //Write style for screen_setting_btn_todo, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_bg_opa(ui->screen_setting_btn_todo, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_border_width(ui->screen_setting_btn_todo, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_setting_btn_todo, 5, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_shadow_width(ui->screen_setting_btn_todo, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_src(ui->screen_setting_btn_todo, &_todo_icon_65x65, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_opa(ui->screen_setting_btn_todo, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_recolor_opa(ui->screen_setting_btn_todo, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_color(ui->screen_setting_btn_todo, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_font(ui->screen_setting_btn_todo, &lv_font_montserratMedium_16, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_opa(ui->screen_setting_btn_todo, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_align(ui->screen_setting_btn_todo, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write style for screen_setting_btn_todo, Part: LV_PART_MAIN, State: LV_STATE_FOCUSED.
    lv_obj_set_style_bg_opa(ui->screen_setting_btn_todo, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_border_width(ui->screen_setting_btn_todo, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_radius(ui->screen_setting_btn_todo, 5, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_width(ui->screen_setting_btn_todo, 5, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_color(ui->screen_setting_btn_todo, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_opa(ui->screen_setting_btn_todo, 255, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_spread(ui->screen_setting_btn_todo, 1, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_ofs_x(ui->screen_setting_btn_todo, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_ofs_y(ui->screen_setting_btn_todo, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_src(ui->screen_setting_btn_todo, &_todo_icon_65x65, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_opa(ui->screen_setting_btn_todo, 255, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_recolor_opa(ui->screen_setting_btn_todo, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_color(ui->screen_setting_btn_todo, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_font(ui->screen_setting_btn_todo, &lv_font_montserratMedium_16, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_opa(ui->screen_setting_btn_todo, 255, LV_PART_MAIN|LV_STATE_FOCUSED);

    //Write codes screen_setting_label_settings
    ui->screen_setting_label_settings = lv_label_create(ui->screen_setting);
    lv_label_set_text(ui->screen_setting_label_settings, "Settings");
    lv_label_set_long_mode(ui->screen_setting_label_settings, LV_LABEL_LONG_WRAP);
    lv_obj_set_pos(ui->screen_setting_label_settings, 78, 8);
    lv_obj_set_size(ui->screen_setting_label_settings, 169, 19);

    //Write style for screen_setting_label_settings, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_border_width(ui->screen_setting_label_settings, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_setting_label_settings, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_color(ui->screen_setting_label_settings, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_font(ui->screen_setting_label_settings, &lv_font_montserratMedium_16, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_opa(ui->screen_setting_label_settings, 149, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_letter_space(ui->screen_setting_label_settings, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_line_space(ui->screen_setting_label_settings, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_align(ui->screen_setting_label_settings, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_opa(ui->screen_setting_label_settings, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_top(ui->screen_setting_label_settings, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_right(ui->screen_setting_label_settings, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_bottom(ui->screen_setting_label_settings, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_left(ui->screen_setting_label_settings, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_shadow_width(ui->screen_setting_label_settings, 0, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write codes screen_setting_btn_back
    ui->screen_setting_btn_back = lv_btn_create(ui->screen_setting);
    ui->screen_setting_btn_back_label = lv_label_create(ui->screen_setting_btn_back);
    lv_label_set_text(ui->screen_setting_btn_back_label, "<");
    lv_label_set_long_mode(ui->screen_setting_btn_back_label, LV_LABEL_LONG_WRAP);
    lv_obj_align(ui->screen_setting_btn_back_label, LV_ALIGN_CENTER, 0, 0);
    lv_obj_set_style_pad_all(ui->screen_setting_btn_back, 0, LV_STATE_DEFAULT);
    lv_obj_set_width(ui->screen_setting_btn_back_label, LV_PCT(100));
    lv_obj_set_pos(ui->screen_setting_btn_back, 7, 7);
    lv_obj_set_size(ui->screen_setting_btn_back, 20, 20);

    //Write style for screen_setting_btn_back, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_bg_opa(ui->screen_setting_btn_back, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_border_width(ui->screen_setting_btn_back, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_setting_btn_back, 5, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_shadow_width(ui->screen_setting_btn_back, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_color(ui->screen_setting_btn_back, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_font(ui->screen_setting_btn_back, &lv_font_montserratMedium_16, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_opa(ui->screen_setting_btn_back, 192, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_align(ui->screen_setting_btn_back, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write style for screen_setting_btn_back, Part: LV_PART_MAIN, State: LV_STATE_FOCUSED.
    lv_obj_set_style_bg_opa(ui->screen_setting_btn_back, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_border_width(ui->screen_setting_btn_back, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_radius(ui->screen_setting_btn_back, 5, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_width(ui->screen_setting_btn_back, 5, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_color(ui->screen_setting_btn_back, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_opa(ui->screen_setting_btn_back, 255, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_spread(ui->screen_setting_btn_back, 1, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_ofs_x(ui->screen_setting_btn_back, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_ofs_y(ui->screen_setting_btn_back, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_color(ui->screen_setting_btn_back, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_font(ui->screen_setting_btn_back, &lv_font_montserratMedium_16, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_opa(ui->screen_setting_btn_back, 255, LV_PART_MAIN|LV_STATE_FOCUSED);

    //Write codes screen_setting_circular_down
    ui->screen_setting_circular_down = lv_img_create(ui->screen_setting);
    lv_obj_add_flag(ui->screen_setting_circular_down, LV_OBJ_FLAG_CLICKABLE);
    lv_img_set_src(ui->screen_setting_circular_down, &_Subtract_alpha_220x25);
    lv_img_set_pivot(ui->screen_setting_circular_down, 50,50);
    lv_img_set_angle(ui->screen_setting_circular_down, 0);
    lv_obj_set_pos(ui->screen_setting_circular_down, 54, 133);
    lv_obj_set_size(ui->screen_setting_circular_down, 220, 25);

    //Write style for screen_setting_circular_down, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_img_recolor_opa(ui->screen_setting_circular_down, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_img_recolor(ui->screen_setting_circular_down, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_img_opa(ui->screen_setting_circular_down, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_setting_circular_down, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_clip_corner(ui->screen_setting_circular_down, true, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write codes screen_setting_circular_up
    ui->screen_setting_circular_up = lv_img_create(ui->screen_setting);
    lv_obj_add_flag(ui->screen_setting_circular_up, LV_OBJ_FLAG_CLICKABLE);
    lv_img_set_src(ui->screen_setting_circular_up, &_Subtract1_alpha_220x25);
    lv_img_set_pivot(ui->screen_setting_circular_up, 50,50);
    lv_img_set_angle(ui->screen_setting_circular_up, 0);
    lv_obj_set_pos(ui->screen_setting_circular_up, 54, 143);
    lv_obj_set_size(ui->screen_setting_circular_up, 220, 25);

    //Write style for screen_setting_circular_up, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_img_recolor_opa(ui->screen_setting_circular_up, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_img_recolor(ui->screen_setting_circular_up, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_img_opa(ui->screen_setting_circular_up, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_setting_circular_up, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_clip_corner(ui->screen_setting_circular_up, true, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write codes screen_setting_img_point8
    ui->screen_setting_img_point8 = lv_img_create(ui->screen_setting);
    lv_obj_add_flag(ui->screen_setting_img_point8, LV_OBJ_FLAG_CLICKABLE);
    lv_img_set_src(ui->screen_setting_img_point8, &_Ellipse_alpha_25x25);
    lv_img_set_pivot(ui->screen_setting_img_point8, 50,50);
    lv_img_set_angle(ui->screen_setting_img_point8, 0);
    lv_obj_set_pos(ui->screen_setting_img_point8, 91, 148);
    lv_obj_set_size(ui->screen_setting_img_point8, 25, 25);
    lv_obj_add_flag(ui->screen_setting_img_point8, LV_OBJ_FLAG_HIDDEN);

    //Write style for screen_setting_img_point8, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_img_recolor_opa(ui->screen_setting_img_point8, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_img_opa(ui->screen_setting_img_point8, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_setting_img_point8, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_clip_corner(ui->screen_setting_img_point8, true, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write codes screen_setting_img_point3
    ui->screen_setting_img_point3 = lv_img_create(ui->screen_setting);
    lv_obj_add_flag(ui->screen_setting_img_point3, LV_OBJ_FLAG_CLICKABLE);
    lv_img_set_src(ui->screen_setting_img_point3, &_Ellipse_alpha_25x25);
    lv_img_set_pivot(ui->screen_setting_img_point3, 50,50);
    lv_img_set_angle(ui->screen_setting_img_point3, 0);
    lv_obj_set_pos(ui->screen_setting_img_point3, 256, 140);
    lv_obj_set_size(ui->screen_setting_img_point3, 25, 25);
    lv_obj_add_flag(ui->screen_setting_img_point3, LV_OBJ_FLAG_HIDDEN);

    //Write style for screen_setting_img_point3, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_img_recolor_opa(ui->screen_setting_img_point3, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_img_opa(ui->screen_setting_img_point3, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_setting_img_point3, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_clip_corner(ui->screen_setting_img_point3, true, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write codes screen_setting_img_point7
    ui->screen_setting_img_point7 = lv_img_create(ui->screen_setting);
    lv_obj_add_flag(ui->screen_setting_img_point7, LV_OBJ_FLAG_CLICKABLE);
    lv_img_set_src(ui->screen_setting_img_point7, &_Ellipse_alpha_25x25);
    lv_img_set_pivot(ui->screen_setting_img_point7, 50,50);
    lv_img_set_angle(ui->screen_setting_img_point7, 0);
    lv_obj_set_pos(ui->screen_setting_img_point7, 47, 140);
    lv_obj_set_size(ui->screen_setting_img_point7, 25, 25);
    lv_obj_add_flag(ui->screen_setting_img_point7, LV_OBJ_FLAG_HIDDEN);

    //Write style for screen_setting_img_point7, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_img_recolor_opa(ui->screen_setting_img_point7, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_img_opa(ui->screen_setting_img_point7, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_setting_img_point7, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_clip_corner(ui->screen_setting_img_point7, true, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write codes screen_setting_img_point1
    ui->screen_setting_img_point1 = lv_img_create(ui->screen_setting);
    lv_obj_add_flag(ui->screen_setting_img_point1, LV_OBJ_FLAG_CLICKABLE);
    lv_img_set_src(ui->screen_setting_img_point1, &_Ellipse_alpha_25x25);
    lv_img_set_pivot(ui->screen_setting_img_point1, 50,50);
    lv_img_set_angle(ui->screen_setting_img_point1, 0);
    lv_obj_set_pos(ui->screen_setting_img_point1, 155, 149);
    lv_obj_set_size(ui->screen_setting_img_point1, 25, 25);
    lv_obj_add_flag(ui->screen_setting_img_point1, LV_OBJ_FLAG_HIDDEN);

    //Write style for screen_setting_img_point1, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_img_recolor_opa(ui->screen_setting_img_point1, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_img_opa(ui->screen_setting_img_point1, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_setting_img_point1, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_clip_corner(ui->screen_setting_img_point1, true, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write codes screen_setting_img_point2
    ui->screen_setting_img_point2 = lv_img_create(ui->screen_setting);
    lv_obj_add_flag(ui->screen_setting_img_point2, LV_OBJ_FLAG_CLICKABLE);
    lv_img_set_src(ui->screen_setting_img_point2, &_Ellipse_alpha_25x25);
    lv_img_set_pivot(ui->screen_setting_img_point2, 50,50);
    lv_img_set_angle(ui->screen_setting_img_point2, 0);
    lv_obj_set_pos(ui->screen_setting_img_point2, 214, 147);
    lv_obj_set_size(ui->screen_setting_img_point2, 25, 25);
    lv_obj_add_flag(ui->screen_setting_img_point2, LV_OBJ_FLAG_HIDDEN);

    //Write style for screen_setting_img_point2, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_img_recolor_opa(ui->screen_setting_img_point2, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_img_opa(ui->screen_setting_img_point2, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_setting_img_point2, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_clip_corner(ui->screen_setting_img_point2, true, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write codes screen_setting_img_point5
    ui->screen_setting_img_point5 = lv_img_create(ui->screen_setting);
    lv_obj_add_flag(ui->screen_setting_img_point5, LV_OBJ_FLAG_CLICKABLE);
    lv_img_set_src(ui->screen_setting_img_point5, &_Ellipse_alpha_25x25);
    lv_img_set_pivot(ui->screen_setting_img_point5, 50,50);
    lv_img_set_angle(ui->screen_setting_img_point5, 0);
    lv_obj_set_pos(ui->screen_setting_img_point5, 155, 130);
    lv_obj_set_size(ui->screen_setting_img_point5, 25, 25);
    lv_obj_add_flag(ui->screen_setting_img_point5, LV_OBJ_FLAG_HIDDEN);

    //Write style for screen_setting_img_point5, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_img_recolor_opa(ui->screen_setting_img_point5, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_img_opa(ui->screen_setting_img_point5, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_setting_img_point5, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_clip_corner(ui->screen_setting_img_point5, true, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write codes screen_setting_img_point4
    ui->screen_setting_img_point4 = lv_img_create(ui->screen_setting);
    lv_obj_add_flag(ui->screen_setting_img_point4, LV_OBJ_FLAG_CLICKABLE);
    lv_img_set_src(ui->screen_setting_img_point4, &_Ellipse_alpha_25x25);
    lv_img_set_pivot(ui->screen_setting_img_point4, 50,50);
    lv_img_set_angle(ui->screen_setting_img_point4, 0);
    lv_obj_set_pos(ui->screen_setting_img_point4, 214, 133);
    lv_obj_set_size(ui->screen_setting_img_point4, 25, 25);
    lv_obj_add_flag(ui->screen_setting_img_point4, LV_OBJ_FLAG_HIDDEN);

    //Write style for screen_setting_img_point4, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_img_recolor_opa(ui->screen_setting_img_point4, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_img_opa(ui->screen_setting_img_point4, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_setting_img_point4, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_clip_corner(ui->screen_setting_img_point4, true, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write codes screen_setting_img_point6
    ui->screen_setting_img_point6 = lv_img_create(ui->screen_setting);
    lv_obj_add_flag(ui->screen_setting_img_point6, LV_OBJ_FLAG_CLICKABLE);
    lv_img_set_src(ui->screen_setting_img_point6, &_Ellipse_alpha_25x25);
    lv_img_set_pivot(ui->screen_setting_img_point6, 50,50);
    lv_img_set_angle(ui->screen_setting_img_point6, 0);
    lv_obj_set_pos(ui->screen_setting_img_point6, 91, 132);
    lv_obj_set_size(ui->screen_setting_img_point6, 25, 25);
    lv_obj_add_flag(ui->screen_setting_img_point6, LV_OBJ_FLAG_HIDDEN);

    //Write style for screen_setting_img_point6, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_img_recolor_opa(ui->screen_setting_img_point6, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_img_opa(ui->screen_setting_img_point6, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_setting_img_point6, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_clip_corner(ui->screen_setting_img_point6, true, LV_PART_MAIN|LV_STATE_DEFAULT);

    //The custom code of screen_setting.


    //Update current screen layout.
    lv_obj_update_layout(ui->screen_setting);

    //Init events for screen.
    events_init_screen_setting(ui);
}
