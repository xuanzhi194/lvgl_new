/*
* Copyright 2026 NXP
* NXP Proprietary. This software is owned or controlled by NXP and may only be used strictly in
* accordance with the applicable license terms. By expressly accepting such terms or by downloading, installing,
* activating and/or otherwise using the software, you are agreeing that you have read, and that you agree to
* comply with and are bound by, such license terms.  If you do not agree to be bound by the applicable license
* terms, then you may not retain, install, activate or otherwise use the software.
*/

#ifndef GUI_GUIDER_H
#define GUI_GUIDER_H
#ifdef __cplusplus
extern "C" {
#endif

#include "lvgl.h"

typedef struct
{
  
	lv_obj_t *screen_reppo;
	bool screen_reppo_del;
	lv_obj_t *screen_reppo_reppo_gif;
	lv_obj_t *screen_log;
	bool screen_log_del;
	lv_obj_t *screen_log_reppo_logo;
	lv_obj_t *screen_main;
	bool screen_main_del;
	lv_obj_t *screen_main_img_wifi;
	lv_obj_t *screen_main_img_reppo;
	lv_obj_t *screen_main_label_reppo;
	lv_obj_t *screen_main_img_battery;
	lv_obj_t *screen_main_img_ble;
	lv_obj_t *screen_main_img_todolist;
	lv_obj_t *screen_main_img_word;
	lv_obj_t *screen_main_img_timer;
	lv_obj_t *screen_main_img_setting;
	lv_obj_t *screen_main_label_word;
	lv_obj_t *screen_main_label_timer;
	lv_obj_t *screen_main_label_setting;
	lv_obj_t *screen_main_btn_word;
	lv_obj_t *screen_main_btn_word_label;
	lv_obj_t *screen_main_btn_timer;
	lv_obj_t *screen_main_btn_timer_label;
	lv_obj_t *screen_main_btn_setting;
	lv_obj_t *screen_main_btn_setting_label;
	lv_obj_t *screen_main_img_uptext;
	lv_obj_t *screen_main_label_uptext;
	lv_obj_t *screen_main_img_plane;
	lv_obj_t *screen_main_btn_plane;
	lv_obj_t *screen_main_btn_plane_label;
	lv_obj_t *screen_main_img_probg1;
	lv_obj_t *screen_main_label_done;
	lv_obj_t *screen_main_label_donenum;
	lv_obj_t *screen_main_img_runpace;
	lv_obj_t *screen_main_label_nodone;
	lv_obj_t *screen_main_img_probg2;
	lv_obj_t *screen_main_label_todonum;
	lv_obj_t *screen_main_label_todolist;
	lv_obj_t *screen_main_btn_todolist;
	lv_obj_t *screen_main_btn_todolist_label;
	lv_obj_t *screen_main_label_battery;
	lv_obj_t *screen_todolist;
	bool screen_todolist_del;
	lv_obj_t *screen_todolist_btn_back;
	lv_obj_t *screen_todolist_btn_back_label;
	lv_obj_t *screen_todolist_img_addpage;
	lv_obj_t *screen_todolist_label_addpage;
	lv_obj_t *screen_todolist_btn_delpage;
	lv_obj_t *screen_todolist_btn_delpage_label;
	lv_obj_t *screen_todolist_btn_todo1;
	lv_obj_t *screen_todolist_btn_todo1_label;
	lv_obj_t *screen_todolist_btn_todo2;
	lv_obj_t *screen_todolist_btn_todo2_label;
	lv_obj_t *screen_todolist_btn_todo3;
	lv_obj_t *screen_todolist_btn_todo3_label;
	lv_obj_t *screen_todolist_btn_todo4;
	lv_obj_t *screen_todolist_btn_todo4_label;
	lv_obj_t *screen_todolist_img_delpage;
	lv_obj_t *screen_todolist_label_delpage;
	lv_obj_t *screen_todolist_btn_addpage;
	lv_obj_t *screen_todolist_btn_addpage_label;
	lv_obj_t *screen_todolist_label_indexcut;
	lv_obj_t *screen_todolist_btn_pageminus;
	lv_obj_t *screen_todolist_btn_pageminus_label;
	lv_obj_t *screen_todolist_btn_pageplus;
	lv_obj_t *screen_todolist_btn_pageplus_label;
	lv_obj_t *screen_todolist_label_indexcur;
	lv_obj_t *screen_todolist_label_indexall;
	lv_obj_t *screen_todolist_label_done;
	lv_obj_t *screen_todolist_label_todo;
	lv_obj_t *screen_todolist_label_donenum;
	lv_obj_t *screen_todolist_label_todonum;
	lv_obj_t *screen_todolist_label_todo1;
	lv_obj_t *screen_todolist_label_todo2;
	lv_obj_t *screen_todolist_label_todo3;
	lv_obj_t *screen_todolist_label_todo4;
	lv_obj_t *screen_timing;
	bool screen_timing_del;
	lv_obj_t *screen_timing_img_moon;
	lv_obj_t *screen_timing_label_realtime;
	lv_obj_t *screen_timing_label_day;
	lv_obj_t *screen_timing_line_1;
	lv_obj_t *screen_timing_line_2;
	lv_obj_t *screen_timing_label_moon;
	lv_obj_t *screen_timing_label_date;
	lv_obj_t *screen_timing_btn_pomodoro;
	lv_obj_t *screen_timing_btn_pomodoro_label;
	lv_obj_t *screen_timing_btn_back;
	lv_obj_t *screen_timing_btn_back_label;
	lv_obj_t *screen_timing_img_night;
	lv_obj_t *screen_timing_img_morning;
	lv_obj_t *screen_pomodoro;
	bool screen_pomodoro_del;
	lv_obj_t *screen_pomodoro_label_addnum;
	lv_obj_t *screen_pomodoro_img_pomorect1;
	lv_obj_t *screen_pomodoro_label_timer;
	lv_obj_t *screen_pomodoro_label_funcstate;
	lv_obj_t *screen_pomodoro_label_pomodoro;
	lv_obj_t *screen_pomodoro_btn_stopwatch;
	lv_obj_t *screen_pomodoro_btn_stopwatch_label;
	lv_obj_t *screen_pomodoro_btn_countdown;
	lv_obj_t *screen_pomodoro_btn_countdown_label;
	lv_obj_t *screen_pomodoro_btn_back;
	lv_obj_t *screen_pomodoro_btn_back_label;
	lv_obj_t *screen_pomodoro_btn_home;
	lv_obj_t *screen_pomodoro_btn_home_label;
	lv_obj_t *screen_pomodoro_btn_start;
	lv_obj_t *screen_pomodoro_btn_start_label;
	lv_obj_t *screen_pomodoro_btn_reset;
	lv_obj_t *screen_pomodoro_btn_reset_label;
	lv_obj_t *screen_pomodoro_btn_addnum;
	lv_obj_t *screen_pomodoro_btn_addnum_label;
	lv_obj_t *screen_pomodoro_btn_minus;
	lv_obj_t *screen_pomodoro_btn_minus_label;
	lv_obj_t *screen_pomodoro_btn_plus;
	lv_obj_t *screen_pomodoro_btn_plus_label;
	lv_obj_t *screen_wordmeun;
	bool screen_wordmeun_del;
	lv_obj_t *screen_wordmeun_img_learn;
	lv_obj_t *screen_wordmeun_img_wordrect;
	lv_obj_t *screen_wordmeun_btn_back;
	lv_obj_t *screen_wordmeun_btn_back_label;
	lv_obj_t *screen_wordmeun_bar_process;
	lv_obj_t *screen_wordmeun_label_booksel;
	lv_obj_t *screen_wordmeun_img_book;
	lv_obj_t *screen_wordmeun_label_bookname;
	lv_obj_t *screen_wordmeun_label_divdernum;
	lv_obj_t *screen_wordmeun_label_wordindicate;
	lv_obj_t *screen_wordmeun_btn_bookleft;
	lv_obj_t *screen_wordmeun_btn_bookleft_label;
	lv_obj_t *screen_wordmeun_btn_bookright;
	lv_obj_t *screen_wordmeun_btn_bookright_label;
	lv_obj_t *screen_wordmeun_label_learn;
	lv_obj_t *screen_wordmeun_btn_learn;
	lv_obj_t *screen_wordmeun_btn_learn_label;
	lv_obj_t *screen_wordmeun_img_review;
	lv_obj_t *screen_wordmeun_label_Review;
	lv_obj_t *screen_wordmeun_btn_review;
	lv_obj_t *screen_wordmeun_btn_review_label;
	lv_obj_t *screen_wordcard;
	bool screen_wordcard_del;
	lv_obj_t *screen_wordcard_img_wordrect;
	lv_obj_t *screen_wordcard_btn_back;
	lv_obj_t *screen_wordcard_btn_back_label;
	lv_obj_t *screen_wordcard_btn_left;
	lv_obj_t *screen_wordcard_btn_left_label;
	lv_obj_t *screen_wordcard_label_index;
	lv_obj_t *screen_wordcard_btn_right;
	lv_obj_t *screen_wordcard_btn_right_label;
	lv_obj_t *screen_wordcard_label_spelling;
	lv_obj_t *screen_wordcard_label_phonetic;
	lv_obj_t *screen_wordcard_label_meaning;
	lv_obj_t *screen_wordcard_img_cuo;
	lv_obj_t *screen_wordcard_img_dui;
	lv_obj_t *screen_wordcard_label_gotit;
	lv_obj_t *screen_wordcard_label_review;
	lv_obj_t *screen_wordcard_btn_dui;
	lv_obj_t *screen_wordcard_btn_dui_label;
	lv_obj_t *screen_wordcard_btn_cuo;
	lv_obj_t *screen_wordcard_btn_cuo_label;
	lv_obj_t *screen_wordcard_btn_home;
	lv_obj_t *screen_wordcard_btn_home_label;
	lv_obj_t *screen_reviewcard;
	bool screen_reviewcard_del;
	lv_obj_t *screen_reviewcard_img_wordrect;
	lv_obj_t *screen_reviewcard_btn_back;
	lv_obj_t *screen_reviewcard_btn_back_label;
	lv_obj_t *screen_reviewcard_btn_left;
	lv_obj_t *screen_reviewcard_btn_left_label;
	lv_obj_t *screen_reviewcard_label_index;
	lv_obj_t *screen_reviewcard_btn_right;
	lv_obj_t *screen_reviewcard_btn_right_label;
	lv_obj_t *screen_reviewcard_label_spelling;
	lv_obj_t *screen_reviewcard_label_phonetic;
	lv_obj_t *screen_reviewcard_label_meaning;
	lv_obj_t *screen_reviewcard_img_dui;
	lv_obj_t *screen_reviewcard_label_gotit;
	lv_obj_t *screen_reviewcard_btn_dui;
	lv_obj_t *screen_reviewcard_btn_dui_label;
	lv_obj_t *screen_reviewcard_btn_home;
	lv_obj_t *screen_reviewcard_btn_home_label;
	lv_obj_t *screen_reviewcard_label_review;
	lv_obj_t *screen_reviewcard_img_cuo;
	lv_obj_t *screen_reviewcard_btn_cuo;
	lv_obj_t *screen_reviewcard_btn_cuo_label;
	lv_obj_t *screen_setting;
	bool screen_setting_del;
	lv_obj_t *screen_setting_cont_menu;
	lv_obj_t *screen_setting_btn_wifi;
	lv_obj_t *screen_setting_btn_wifi_label;
	lv_obj_t *screen_setting_btn_vocab;
	lv_obj_t *screen_setting_btn_vocab_label;
	lv_obj_t *screen_setting_btn_laba;
	lv_obj_t *screen_setting_btn_laba_label;
	lv_obj_t *screen_setting_btn_timer;
	lv_obj_t *screen_setting_btn_timer_label;
	lv_obj_t *screen_setting_btn_ble;
	lv_obj_t *screen_setting_btn_ble_label;
	lv_obj_t *screen_setting_btn_general;
	lv_obj_t *screen_setting_btn_general_label;
	lv_obj_t *screen_setting_btn_data;
	lv_obj_t *screen_setting_btn_data_label;
	lv_obj_t *screen_setting_btn_todo;
	lv_obj_t *screen_setting_btn_todo_label;
	lv_obj_t *screen_setting_label_settings;
	lv_obj_t *screen_setting_btn_back;
	lv_obj_t *screen_setting_btn_back_label;
	lv_obj_t *screen_setting_circular_down;
	lv_obj_t *screen_setting_circular_up;
	lv_obj_t *screen_setting_img_point8;
	lv_obj_t *screen_setting_img_point3;
	lv_obj_t *screen_setting_img_point7;
	lv_obj_t *screen_setting_img_point1;
	lv_obj_t *screen_setting_img_point2;
	lv_obj_t *screen_setting_img_point5;
	lv_obj_t *screen_setting_img_point4;
	lv_obj_t *screen_setting_img_point6;
	lv_obj_t *screen_wificfg;
	bool screen_wificfg_del;
	lv_obj_t *screen_wificfg_img_network;
	lv_obj_t *screen_wificfg_btn_back;
	lv_obj_t *screen_wificfg_btn_back_label;
	lv_obj_t *screen_wificfg_label_wifi;
	lv_obj_t *screen_wificfg_img_statusbg;
	lv_obj_t *screen_wificfg_label_status;
	lv_obj_t *screen_wificfg_img_wifiicon;
	lv_obj_t *screen_wificfg_label_status2;
	lv_obj_t *screen_wificfg_img_wififalse;
	lv_obj_t *screen_wificfg_label_net;
	lv_obj_t *screen_wificfg_list_1;
	lv_obj_t *screen_wificfg_list_1_item0;
	lv_obj_t *screen_wificfg_list_1_item1;
	lv_obj_t *screen_wificfg_list_1_item2;
	lv_obj_t *screen_wificfg_list_1_item3;
	lv_obj_t *screen_wificfg_list_1_item4;
	lv_obj_t *screen_wificfg_btn_scan;
	lv_obj_t *screen_wificfg_btn_scan_label;
	lv_obj_t *screen_wificfg_btn_disconnect;
	lv_obj_t *screen_wificfg_btn_disconnect_label;
	lv_obj_t *screen_wificfg_btn_cancel;
	lv_obj_t *screen_wificfg_btn_cancel_label;
	lv_obj_t *screen_wificfg_btn_connect;
	lv_obj_t *screen_wificfg_btn_connect_label;
	lv_obj_t *screen_wificfg_ta_password;
	lv_obj_t *screen_wificfg_img_passicon;
	lv_obj_t *screen_wificfg_spinner_connect;
	lv_obj_t *screen_todosel;
	bool screen_todosel_del;
	lv_obj_t *screen_todosel_btn_complete;
	lv_obj_t *screen_todosel_btn_complete_label;
	lv_obj_t *screen_todosel_btn_focus;
	lv_obj_t *screen_todosel_btn_focus_label;
	lv_obj_t *screen_todosel_btn_cancel;
	lv_obj_t *screen_todosel_btn_cancel_label;
	lv_obj_t *screen_todosel_label_task;
	lv_obj_t *screen_ai;
	bool screen_ai_del;
	lv_obj_t *g_kb_top_layer;
}lv_ui;

typedef void (*ui_setup_scr_t)(lv_ui * ui);

void ui_init_style(lv_style_t * style);

void ui_load_scr_animation(lv_ui *ui, lv_obj_t ** new_scr, bool new_scr_del, bool * old_scr_del, ui_setup_scr_t setup_scr,
                           lv_scr_load_anim_t anim_type, uint32_t time, uint32_t delay, bool is_clean, bool auto_del);

void ui_animation(void * var, int32_t duration, int32_t delay, int32_t start_value, int32_t end_value, lv_anim_path_cb_t path_cb,
                       uint16_t repeat_cnt, uint32_t repeat_delay, uint32_t playback_time, uint32_t playback_delay,
                       lv_anim_exec_xcb_t exec_cb, lv_anim_start_cb_t start_cb, lv_anim_ready_cb_t ready_cb, lv_anim_deleted_cb_t deleted_cb);


void init_scr_del_flag(lv_ui *ui);

void setup_ui(lv_ui *ui);

void init_keyboard(lv_ui *ui);

extern lv_ui guider_ui;


void setup_scr_screen_reppo(lv_ui *ui);
void setup_scr_screen_log(lv_ui *ui);
void setup_scr_screen_main(lv_ui *ui);
void setup_scr_screen_todolist(lv_ui *ui);
void setup_scr_screen_timing(lv_ui *ui);
void setup_scr_screen_pomodoro(lv_ui *ui);
void setup_scr_screen_wordmeun(lv_ui *ui);
void setup_scr_screen_wordcard(lv_ui *ui);
void setup_scr_screen_reviewcard(lv_ui *ui);
void setup_scr_screen_setting(lv_ui *ui);
void setup_scr_screen_wificfg(lv_ui *ui);
void setup_scr_screen_todosel(lv_ui *ui);
void setup_scr_screen_ai(lv_ui *ui);
#include "extra/widgets/animimg/lv_animimg.h"
LV_IMG_DECLARE(screen_reppo_reppo_gifReppo_label_v3_00);
LV_IMG_DECLARE(screen_reppo_reppo_gifReppo_label_v3_01);
LV_IMG_DECLARE(screen_reppo_reppo_gifReppo_label_v3_02);
LV_IMG_DECLARE(screen_reppo_reppo_gifReppo_label_v3_05);
LV_IMG_DECLARE(screen_reppo_reppo_gifReppo_label_v3_06);
LV_IMG_DECLARE(screen_reppo_reppo_gifReppo_label_v3_09);
LV_IMG_DECLARE(screen_reppo_reppo_gifReppo_label_v3_10);
LV_IMG_DECLARE(screen_reppo_reppo_gifReppo_label_v3_13);
LV_IMG_DECLARE(screen_reppo_reppo_gifReppo_label_v3_14);
LV_IMG_DECLARE(screen_reppo_reppo_gifReppo_label_v3_17);
LV_IMG_DECLARE(screen_reppo_reppo_gifReppo_label_v3_18);

LV_IMG_DECLARE(_reppo_background_320x170);
LV_IMG_DECLARE(_Reppo_LOGO_V4_1_alpha_100x100);

LV_IMG_DECLARE(_screen_main_bg_320x170);
LV_IMG_DECLARE(_wifi_log_2_alpha_24x24);
LV_IMG_DECLARE(_Reppo_LOGO_V4_1_alpha_25x25);
LV_IMG_DECLARE(_battery_label_v3_alpha_18x18);
LV_IMG_DECLARE(_ble_label_v3_alpha_14x14);
LV_IMG_DECLARE(_todolist_label_v4_alpha_60x80);
LV_IMG_DECLARE(_word_label_v4_alpha_60x80);
LV_IMG_DECLARE(_timing_label_v4_alpha_60x80);
LV_IMG_DECLARE(_setting_label_v4_alpha_60x80);
LV_IMG_DECLARE(_probg4_alpha_165x21);
LV_IMG_DECLARE(_plane_alpha_35x28);
LV_IMG_DECLARE(_progress_bg2_alpha_76x18);
LV_IMG_DECLARE(_progress_bg3_alpha_206x20);
LV_IMG_DECLARE(_progress_bg2_alpha_76x18);

LV_IMG_DECLARE(_screen_todolist_bg_320x170);

LV_IMG_DECLARE(_home_20x20);

LV_IMG_DECLARE(_home_20x20);
LV_IMG_DECLARE(_group_add5_alpha_98x20);
LV_IMG_DECLARE(_group_add5_alpha_98x20);
LV_IMG_DECLARE(_moon_alpha_160x160);

LV_IMG_DECLARE(_home_20x20);

LV_IMG_DECLARE(_home_20x20);
LV_IMG_DECLARE(_night_alpha_25x25);
LV_IMG_DECLARE(_morning_alpha_33x31);

LV_IMG_DECLARE(_pomodoro_bg_320x170);
LV_IMG_DECLARE(_pomorect_alpha_257x52);

LV_IMG_DECLARE(_pomodoro2_20x20);

LV_IMG_DECLARE(_pomodoro2_20x20);

LV_IMG_DECLARE(_screen_wordmenu_bg_320x170);
LV_IMG_DECLARE(_word_rectangle_alpha_129x21);
LV_IMG_DECLARE(_word_rectangle_alpha_264x94);
LV_IMG_DECLARE(_book_alpha_39x46);
LV_IMG_DECLARE(_word_rectangle_alpha_129x21);

LV_IMG_DECLARE(_screen_wordcard_bg_320x170);
LV_IMG_DECLARE(_word_rectangle_alpha_264x136);

LV_IMG_DECLARE(_leftarrow_20x20);

LV_IMG_DECLARE(_leftarrow_20x20);

LV_IMG_DECLARE(_rightarrow_18x18);

LV_IMG_DECLARE(_rightarrow_18x18);
LV_IMG_DECLARE(_cuo_1_alpha_20x20);
LV_IMG_DECLARE(_dui_1_alpha_20x20);

LV_IMG_DECLARE(_home_15x15);

LV_IMG_DECLARE(_home_15x15);

LV_IMG_DECLARE(_screen_reviewcard_bg_320x170);
LV_IMG_DECLARE(_word_rectangle_alpha_264x136);

LV_IMG_DECLARE(_leftarrow_20x20);

LV_IMG_DECLARE(_leftarrow_20x20);

LV_IMG_DECLARE(_rightarrow_18x18);

LV_IMG_DECLARE(_rightarrow_18x18);
LV_IMG_DECLARE(_dui_1_alpha_20x20);

LV_IMG_DECLARE(_home_15x15);

LV_IMG_DECLARE(_home_15x15);
LV_IMG_DECLARE(_cuo_1_alpha_20x20);

LV_IMG_DECLARE(_screen_setting_bg2_320x170);

LV_IMG_DECLARE(_wifi_icon_65x65);

LV_IMG_DECLARE(_wifi_icon_65x65);

LV_IMG_DECLARE(_wifi_icon_65x65);

LV_IMG_DECLARE(_vocab_icon_65x65);

LV_IMG_DECLARE(_vocab_icon_65x65);

LV_IMG_DECLARE(_laba_icon_65x65);

LV_IMG_DECLARE(_laba_icon_65x65);

LV_IMG_DECLARE(_timer_icon_65x65);

LV_IMG_DECLARE(_timer_icon_65x65);

LV_IMG_DECLARE(_ble_icon_65x65);

LV_IMG_DECLARE(_ble_icon_65x65);

LV_IMG_DECLARE(_general_icon_65x65);

LV_IMG_DECLARE(_general_icon_65x65);

LV_IMG_DECLARE(_data_icon_65x65);

LV_IMG_DECLARE(_data_icon_65x65);

LV_IMG_DECLARE(_todo_icon_65x65);

LV_IMG_DECLARE(_todo_icon_65x65);
LV_IMG_DECLARE(_Subtract_alpha_220x25);
LV_IMG_DECLARE(_Subtract1_alpha_220x25);
LV_IMG_DECLARE(_Ellipse_alpha_25x25);
LV_IMG_DECLARE(_Ellipse_alpha_25x25);
LV_IMG_DECLARE(_Ellipse_alpha_25x25);
LV_IMG_DECLARE(_Ellipse_alpha_25x25);
LV_IMG_DECLARE(_Ellipse_alpha_25x25);
LV_IMG_DECLARE(_Ellipse_alpha_25x25);
LV_IMG_DECLARE(_Ellipse_alpha_25x25);
LV_IMG_DECLARE(_Ellipse_alpha_25x25);

LV_IMG_DECLARE(_screen_wifi_bg_320x170);
LV_IMG_DECLARE(_pomorect_alpha_160x125);
LV_IMG_DECLARE(_pomorect_alpha_145x125);
LV_IMG_DECLARE(_wifi_log_2_alpha_110x110);
LV_IMG_DECLARE(_wifi_false_alpha_20x20);
LV_IMG_DECLARE(_password_icon2_alpha_19x18);

LV_IMG_DECLARE(_reppo_todo_sel_320x170);

LV_FONT_DECLARE(lv_font_ArchitectsDaughter_10)
LV_FONT_DECLARE(lv_font_Alatsi_Regular_12)
LV_FONT_DECLARE(lv_font_montserratMedium_16)
LV_FONT_DECLARE(lv_font_Alatsi_Regular_14)
LV_FONT_DECLARE(lv_font_Acme_Regular_16)
LV_FONT_DECLARE(lv_font_Alatsi_Regular_11)
LV_FONT_DECLARE(lv_font_arial_11)
LV_FONT_DECLARE(lv_font_montserratMedium_20)
LV_FONT_DECLARE(lv_font_arial_12)
LV_FONT_DECLARE(lv_font_Acme_Regular_12)
LV_FONT_DECLARE(lv_font_Acme_Regular_14)
LV_FONT_DECLARE(lv_font_AdobeFangsongStdRegular_16)
LV_FONT_DECLARE(lv_font_Alatsi_Regular_48)
LV_FONT_DECLARE(lv_font_Alatsi_Regular_20)
LV_FONT_DECLARE(lv_font_Alatsi_Regular_18)
LV_FONT_DECLARE(lv_font_Acme_Regular_20)
LV_FONT_DECLARE(lv_font_Abel_regular_30)
LV_FONT_DECLARE(lv_font_AdobeFangsongStdRegular_14)
LV_FONT_DECLARE(lv_font_SourceHanSerifSC_Regular_13)
LV_FONT_DECLARE(lv_font_SourceHanSerifSC_Regular_16)
LV_FONT_DECLARE(lv_font_montserratMedium_25)
LV_FONT_DECLARE(lv_font_Alatsi_Regular_17)
LV_FONT_DECLARE(lv_font_Acme_Regular_22)
LV_FONT_DECLARE(lv_font_montserratMedium_12)
LV_FONT_DECLARE(lv_font_Acme_Regular_30)
LV_FONT_DECLARE(lv_font_arial_14)
LV_FONT_DECLARE(lv_font_montserratMedium_10)
LV_FONT_DECLARE(lv_font_SourceHanSerifSC_Regular_14)
LV_FONT_DECLARE(lv_font_Alatsi_Regular_13)


#ifdef __cplusplus
}
#endif
#endif
