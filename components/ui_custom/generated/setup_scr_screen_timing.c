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



void setup_scr_screen_timing(lv_ui *ui)
{
    //Write codes screen_timing
    ui->screen_timing = lv_obj_create(NULL);
    lv_obj_set_size(ui->screen_timing, 320, 170);
    lv_obj_set_scrollbar_mode(ui->screen_timing, LV_SCROLLBAR_MODE_OFF);

    //Write style for screen_timing, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_bg_opa(ui->screen_timing, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_color(ui->screen_timing, lv_color_hex(0x000000), LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_grad_dir(ui->screen_timing, LV_GRAD_DIR_NONE, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write codes screen_timing_img_moon
    ui->screen_timing_img_moon = lv_img_create(ui->screen_timing);
    lv_obj_add_flag(ui->screen_timing_img_moon, LV_OBJ_FLAG_CLICKABLE);
    lv_img_set_src(ui->screen_timing_img_moon, &_moon_alpha_160x160);
    lv_img_set_pivot(ui->screen_timing_img_moon, 50,50);
    lv_img_set_angle(ui->screen_timing_img_moon, 0);
    lv_obj_set_pos(ui->screen_timing_img_moon, 8, 3);
    lv_obj_set_size(ui->screen_timing_img_moon, 160, 160);

    //Write style for screen_timing_img_moon, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_img_recolor_opa(ui->screen_timing_img_moon, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_img_opa(ui->screen_timing_img_moon, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_timing_img_moon, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_clip_corner(ui->screen_timing_img_moon, true, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write codes screen_timing_label_realtime
    ui->screen_timing_label_realtime = lv_label_create(ui->screen_timing);
    lv_label_set_text(ui->screen_timing_label_realtime, "10 : 32");
    lv_label_set_long_mode(ui->screen_timing_label_realtime, LV_LABEL_LONG_WRAP);
    lv_obj_set_pos(ui->screen_timing_label_realtime, 165, 15);
    lv_obj_set_size(ui->screen_timing_label_realtime, 132, 43);

    //Write style for screen_timing_label_realtime, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_border_width(ui->screen_timing_label_realtime, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_timing_label_realtime, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_color(ui->screen_timing_label_realtime, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_font(ui->screen_timing_label_realtime, &lv_font_Alatsi_Regular_48, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_opa(ui->screen_timing_label_realtime, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_letter_space(ui->screen_timing_label_realtime, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_line_space(ui->screen_timing_label_realtime, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_align(ui->screen_timing_label_realtime, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_opa(ui->screen_timing_label_realtime, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_top(ui->screen_timing_label_realtime, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_right(ui->screen_timing_label_realtime, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_bottom(ui->screen_timing_label_realtime, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_left(ui->screen_timing_label_realtime, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_shadow_width(ui->screen_timing_label_realtime, 0, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write codes screen_timing_label_day
    ui->screen_timing_label_day = lv_label_create(ui->screen_timing);
    lv_label_set_text(ui->screen_timing_label_day, "Saturday");
    lv_label_set_long_mode(ui->screen_timing_label_day, LV_LABEL_LONG_WRAP);
    lv_obj_set_pos(ui->screen_timing_label_day, 177, 66);
    lv_obj_set_size(ui->screen_timing_label_day, 114, 21);

    //Write style for screen_timing_label_day, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_border_width(ui->screen_timing_label_day, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_timing_label_day, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_color(ui->screen_timing_label_day, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_font(ui->screen_timing_label_day, &lv_font_Alatsi_Regular_20, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_opa(ui->screen_timing_label_day, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_letter_space(ui->screen_timing_label_day, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_line_space(ui->screen_timing_label_day, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_align(ui->screen_timing_label_day, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_opa(ui->screen_timing_label_day, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_top(ui->screen_timing_label_day, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_right(ui->screen_timing_label_day, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_bottom(ui->screen_timing_label_day, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_left(ui->screen_timing_label_day, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_shadow_width(ui->screen_timing_label_day, 0, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write codes screen_timing_line_1
    ui->screen_timing_line_1 = lv_line_create(ui->screen_timing);
    static lv_point_t screen_timing_line_1[] = {{0, 0},{200, 0},};
    lv_line_set_points(ui->screen_timing_line_1, screen_timing_line_1, 2);
    lv_obj_set_pos(ui->screen_timing_line_1, 171, 92);
    lv_obj_set_size(ui->screen_timing_line_1, 147, 6);

    //Write style for screen_timing_line_1, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_line_width(ui->screen_timing_line_1, 2, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_line_color(ui->screen_timing_line_1, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_line_opa(ui->screen_timing_line_1, 174, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_line_rounded(ui->screen_timing_line_1, true, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write codes screen_timing_line_2
    ui->screen_timing_line_2 = lv_line_create(ui->screen_timing);
    static lv_point_t screen_timing_line_2[] = {{0, 0},{200, 0},};
    lv_line_set_points(ui->screen_timing_line_2, screen_timing_line_2, 2);
    lv_obj_set_pos(ui->screen_timing_line_2, 161, 119);
    lv_obj_set_size(ui->screen_timing_line_2, 162, 1);

    //Write style for screen_timing_line_2, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_line_width(ui->screen_timing_line_2, 2, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_line_color(ui->screen_timing_line_2, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_line_opa(ui->screen_timing_line_2, 163, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_line_rounded(ui->screen_timing_line_2, true, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write codes screen_timing_label_moon
    ui->screen_timing_label_moon = lv_label_create(ui->screen_timing);
    lv_label_set_text(ui->screen_timing_label_moon, "Humans to Moon");
    lv_label_set_long_mode(ui->screen_timing_label_moon, LV_LABEL_LONG_WRAP);
    lv_obj_set_pos(ui->screen_timing_label_moon, 168, 95);
    lv_obj_set_size(ui->screen_timing_label_moon, 146, 18);

    //Write style for screen_timing_label_moon, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_border_width(ui->screen_timing_label_moon, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_timing_label_moon, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_color(ui->screen_timing_label_moon, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_font(ui->screen_timing_label_moon, &lv_font_Alatsi_Regular_18, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_opa(ui->screen_timing_label_moon, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_letter_space(ui->screen_timing_label_moon, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_line_space(ui->screen_timing_label_moon, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_align(ui->screen_timing_label_moon, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_opa(ui->screen_timing_label_moon, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_top(ui->screen_timing_label_moon, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_right(ui->screen_timing_label_moon, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_bottom(ui->screen_timing_label_moon, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_left(ui->screen_timing_label_moon, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_shadow_width(ui->screen_timing_label_moon, 0, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write codes screen_timing_label_date
    ui->screen_timing_label_date = lv_label_create(ui->screen_timing);
    lv_label_set_text(ui->screen_timing_label_date, "2025/12/25");
    lv_label_set_long_mode(ui->screen_timing_label_date, LV_LABEL_LONG_WRAP);
    lv_obj_set_pos(ui->screen_timing_label_date, 181, 125);
    lv_obj_set_size(ui->screen_timing_label_date, 124, 20);

    //Write style for screen_timing_label_date, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_border_width(ui->screen_timing_label_date, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_timing_label_date, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_color(ui->screen_timing_label_date, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_font(ui->screen_timing_label_date, &lv_font_Acme_Regular_20, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_opa(ui->screen_timing_label_date, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_letter_space(ui->screen_timing_label_date, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_line_space(ui->screen_timing_label_date, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_align(ui->screen_timing_label_date, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_opa(ui->screen_timing_label_date, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_top(ui->screen_timing_label_date, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_right(ui->screen_timing_label_date, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_bottom(ui->screen_timing_label_date, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_pad_left(ui->screen_timing_label_date, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_shadow_width(ui->screen_timing_label_date, 0, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write codes screen_timing_btn_pomodoro
    ui->screen_timing_btn_pomodoro = lv_btn_create(ui->screen_timing);
    ui->screen_timing_btn_pomodoro_label = lv_label_create(ui->screen_timing_btn_pomodoro);
    lv_label_set_text(ui->screen_timing_btn_pomodoro_label, "");
    lv_label_set_long_mode(ui->screen_timing_btn_pomodoro_label, LV_LABEL_LONG_WRAP);
    lv_obj_align(ui->screen_timing_btn_pomodoro_label, LV_ALIGN_CENTER, 0, 0);
    lv_obj_set_style_pad_all(ui->screen_timing_btn_pomodoro, 0, LV_STATE_DEFAULT);
    lv_obj_set_width(ui->screen_timing_btn_pomodoro_label, LV_PCT(100));
    lv_obj_set_pos(ui->screen_timing_btn_pomodoro, 297, 3);
    lv_obj_set_size(ui->screen_timing_btn_pomodoro, 20, 20);

    //Write style for screen_timing_btn_pomodoro, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_bg_opa(ui->screen_timing_btn_pomodoro, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_border_width(ui->screen_timing_btn_pomodoro, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_timing_btn_pomodoro, 5, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_shadow_width(ui->screen_timing_btn_pomodoro, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_src(ui->screen_timing_btn_pomodoro, &_home_20x20, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_opa(ui->screen_timing_btn_pomodoro, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_bg_img_recolor_opa(ui->screen_timing_btn_pomodoro, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_color(ui->screen_timing_btn_pomodoro, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_font(ui->screen_timing_btn_pomodoro, &lv_font_montserratMedium_16, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_opa(ui->screen_timing_btn_pomodoro, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_align(ui->screen_timing_btn_pomodoro, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write style for screen_timing_btn_pomodoro, Part: LV_PART_MAIN, State: LV_STATE_FOCUSED.
    lv_obj_set_style_bg_opa(ui->screen_timing_btn_pomodoro, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_border_width(ui->screen_timing_btn_pomodoro, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_radius(ui->screen_timing_btn_pomodoro, 5, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_width(ui->screen_timing_btn_pomodoro, 5, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_color(ui->screen_timing_btn_pomodoro, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_opa(ui->screen_timing_btn_pomodoro, 255, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_spread(ui->screen_timing_btn_pomodoro, 1, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_ofs_x(ui->screen_timing_btn_pomodoro, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_ofs_y(ui->screen_timing_btn_pomodoro, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_src(ui->screen_timing_btn_pomodoro, &_home_20x20, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_opa(ui->screen_timing_btn_pomodoro, 255, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_bg_img_recolor_opa(ui->screen_timing_btn_pomodoro, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_color(ui->screen_timing_btn_pomodoro, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_font(ui->screen_timing_btn_pomodoro, &lv_font_montserratMedium_16, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_opa(ui->screen_timing_btn_pomodoro, 255, LV_PART_MAIN|LV_STATE_FOCUSED);

    //Write codes screen_timing_btn_back
    ui->screen_timing_btn_back = lv_btn_create(ui->screen_timing);
    ui->screen_timing_btn_back_label = lv_label_create(ui->screen_timing_btn_back);
    lv_label_set_text(ui->screen_timing_btn_back_label, "<");
    lv_label_set_long_mode(ui->screen_timing_btn_back_label, LV_LABEL_LONG_WRAP);
    lv_obj_align(ui->screen_timing_btn_back_label, LV_ALIGN_CENTER, 0, 0);
    lv_obj_set_style_pad_all(ui->screen_timing_btn_back, 0, LV_STATE_DEFAULT);
    lv_obj_set_width(ui->screen_timing_btn_back_label, LV_PCT(100));
    lv_obj_set_pos(ui->screen_timing_btn_back, 5, 3);
    lv_obj_set_size(ui->screen_timing_btn_back, 20, 20);

    //Write style for screen_timing_btn_back, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_bg_opa(ui->screen_timing_btn_back, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_border_width(ui->screen_timing_btn_back, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_timing_btn_back, 5, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_shadow_width(ui->screen_timing_btn_back, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_color(ui->screen_timing_btn_back, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_font(ui->screen_timing_btn_back, &lv_font_montserratMedium_20, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_opa(ui->screen_timing_btn_back, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_text_align(ui->screen_timing_btn_back, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write style for screen_timing_btn_back, Part: LV_PART_MAIN, State: LV_STATE_FOCUSED.
    lv_obj_set_style_bg_opa(ui->screen_timing_btn_back, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_border_width(ui->screen_timing_btn_back, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_radius(ui->screen_timing_btn_back, 5, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_width(ui->screen_timing_btn_back, 5, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_color(ui->screen_timing_btn_back, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_opa(ui->screen_timing_btn_back, 255, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_spread(ui->screen_timing_btn_back, 1, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_ofs_x(ui->screen_timing_btn_back, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_shadow_ofs_y(ui->screen_timing_btn_back, 0, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_color(ui->screen_timing_btn_back, lv_color_hex(0xffffff), LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_font(ui->screen_timing_btn_back, &lv_font_montserratMedium_20, LV_PART_MAIN|LV_STATE_FOCUSED);
    lv_obj_set_style_text_opa(ui->screen_timing_btn_back, 255, LV_PART_MAIN|LV_STATE_FOCUSED);

    //Write codes screen_timing_img_night
    ui->screen_timing_img_night = lv_img_create(ui->screen_timing);
    lv_obj_add_flag(ui->screen_timing_img_night, LV_OBJ_FLAG_CLICKABLE);
    lv_img_set_src(ui->screen_timing_img_night, &_night_alpha_25x25);
    lv_img_set_pivot(ui->screen_timing_img_night, 50,50);
    lv_img_set_angle(ui->screen_timing_img_night, 0);
    lv_obj_set_pos(ui->screen_timing_img_night, 291, 61);
    lv_obj_set_size(ui->screen_timing_img_night, 25, 25);
    lv_obj_add_flag(ui->screen_timing_img_night, LV_OBJ_FLAG_HIDDEN);

    //Write style for screen_timing_img_night, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_img_recolor_opa(ui->screen_timing_img_night, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_img_opa(ui->screen_timing_img_night, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_timing_img_night, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_clip_corner(ui->screen_timing_img_night, true, LV_PART_MAIN|LV_STATE_DEFAULT);

    //Write codes screen_timing_img_morning
    ui->screen_timing_img_morning = lv_img_create(ui->screen_timing);
    lv_obj_add_flag(ui->screen_timing_img_morning, LV_OBJ_FLAG_CLICKABLE);
    lv_img_set_src(ui->screen_timing_img_morning, &_morning_alpha_33x31);
    lv_img_set_pivot(ui->screen_timing_img_morning, 50,50);
    lv_img_set_angle(ui->screen_timing_img_morning, 0);
    lv_obj_set_pos(ui->screen_timing_img_morning, 286, 57);
    lv_obj_set_size(ui->screen_timing_img_morning, 33, 31);

    //Write style for screen_timing_img_morning, Part: LV_PART_MAIN, State: LV_STATE_DEFAULT.
    lv_obj_set_style_img_recolor_opa(ui->screen_timing_img_morning, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_img_opa(ui->screen_timing_img_morning, 255, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_radius(ui->screen_timing_img_morning, 0, LV_PART_MAIN|LV_STATE_DEFAULT);
    lv_obj_set_style_clip_corner(ui->screen_timing_img_morning, true, LV_PART_MAIN|LV_STATE_DEFAULT);

    //The custom code of screen_timing.


    //Update current screen layout.
    lv_obj_update_layout(ui->screen_timing);

    //Init events for screen.
    events_init_screen_timing(ui);
}
