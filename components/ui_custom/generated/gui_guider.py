# Copyright 2026 NXP
# NXP Proprietary. This software is owned or controlled by NXP and may only be used strictly in
# accordance with the applicable license terms. By expressly accepting such terms or by downloading, installing,
# activating and/or otherwise using the software, you are agreeing that you have read, and that you agree to
# comply with and are bound by, such license terms.  If you do not agree to be bound by the applicable license
# terms, then you may not retain, install, activate or otherwise use the software.

import SDL
import utime as time
import usys as sys
import lvgl as lv
import lodepng as png
import ustruct
import fs_driver

lv.init()
SDL.init(w=320,h=170)

# Register SDL display driver.
disp_buf1 = lv.disp_draw_buf_t()
buf1_1 = bytearray(320*170*4)
disp_buf1.init(buf1_1, None, len(buf1_1)//4)
disp_drv = lv.disp_drv_t()
disp_drv.init()
disp_drv.draw_buf = disp_buf1
disp_drv.flush_cb = SDL.monitor_flush
disp_drv.hor_res = 320
disp_drv.ver_res = 170
disp_drv.register()

# Regsiter SDL mouse driver
indev_drv = lv.indev_drv_t()
indev_drv.init()
indev_drv.type = lv.INDEV_TYPE.POINTER
indev_drv.read_cb = SDL.mouse_read
indev_drv.register()

fs_drv = lv.fs_drv_t()
fs_driver.fs_register(fs_drv, 'Z')

# Below: Taken from https://github.com/lvgl/lv_binding_micropython/blob/master/driver/js/imagetools.py#L22-L94

COLOR_SIZE = lv.color_t.__SIZE__
COLOR_IS_SWAPPED = hasattr(lv.color_t().ch,'green_h')

class lodepng_error(RuntimeError):
    def __init__(self, err):
        if type(err) is int:
            super().__init__(png.error_text(err))
        else:
            super().__init__(err)

# Parse PNG file header
# Taken from https://github.com/shibukawa/imagesize_py/blob/ffef30c1a4715c5acf90e8945ceb77f4a2ed2d45/imagesize.py#L63-L85

def get_png_info(decoder, src, header):
    # Only handle variable image types

    if lv.img.src_get_type(src) != lv.img.SRC.VARIABLE:
        return lv.RES.INV

    data = lv.img_dsc_t.__cast__(src).data
    if data == None:
        return lv.RES.INV

    png_header = bytes(data.__dereference__(24))

    if png_header.startswith(b'\211PNG\r\n\032\n'):
        if png_header[12:16] == b'IHDR':
            start = 16
        # Maybe this is for an older PNG version.
        else:
            start = 8
        try:
            width, height = ustruct.unpack(">LL", png_header[start:start+8])
        except ustruct.error:
            return lv.RES.INV
    else:
        return lv.RES.INV

    header.always_zero = 0
    header.w = width
    header.h = height
    header.cf = lv.img.CF.TRUE_COLOR_ALPHA

    return lv.RES.OK

def convert_rgba8888_to_bgra8888(img_view):
    for i in range(0, len(img_view), lv.color_t.__SIZE__):
        ch = lv.color_t.__cast__(img_view[i:i]).ch
        ch.red, ch.blue = ch.blue, ch.red

# Read and parse PNG file

def open_png(decoder, dsc):
    img_dsc = lv.img_dsc_t.__cast__(dsc.src)
    png_data = img_dsc.data
    png_size = img_dsc.data_size
    png_decoded = png.C_Pointer()
    png_width = png.C_Pointer()
    png_height = png.C_Pointer()
    error = png.decode32(png_decoded, png_width, png_height, png_data, png_size)
    if error:
        raise lodepng_error(error)
    img_size = png_width.int_val * png_height.int_val * 4
    img_data = png_decoded.ptr_val
    img_view = img_data.__dereference__(img_size)

    if COLOR_SIZE == 4:
        convert_rgba8888_to_bgra8888(img_view)
    else:
        raise lodepng_error("Error: Color mode not supported yet!")

    dsc.img_data = img_data
    return lv.RES.OK

# Above: Taken from https://github.com/lvgl/lv_binding_micropython/blob/master/driver/js/imagetools.py#L22-L94

decoder = lv.img.decoder_create()
decoder.info_cb = get_png_info
decoder.open_cb = open_png

def anim_x_cb(obj, v):
    obj.set_x(v)

def anim_y_cb(obj, v):
    obj.set_y(v)

def anim_width_cb(obj, v):
    obj.set_width(v)

def anim_height_cb(obj, v):
    obj.set_height(v)

def anim_img_zoom_cb(obj, v):
    obj.set_zoom(v)

def anim_img_rotate_cb(obj, v):
    obj.set_angle(v)

global_font_cache = {}
def test_font(font_family, font_size):
    global global_font_cache
    if font_family + str(font_size) in global_font_cache:
        return global_font_cache[font_family + str(font_size)]
    if font_size % 2:
        candidates = [
            (font_family, font_size),
            (font_family, font_size-font_size%2),
            (font_family, font_size+font_size%2),
            ("montserrat", font_size-font_size%2),
            ("montserrat", font_size+font_size%2),
            ("montserrat", 16)
        ]
    else:
        candidates = [
            (font_family, font_size),
            ("montserrat", font_size),
            ("montserrat", 16)
        ]
    for (family, size) in candidates:
        try:
            if eval(f'lv.font_{family}_{size}'):
                global_font_cache[font_family + str(font_size)] = eval(f'lv.font_{family}_{size}')
                if family != font_family or size != font_size:
                    print(f'WARNING: lv.font_{family}_{size} is used!')
                return eval(f'lv.font_{family}_{size}')
        except AttributeError:
            try:
                load_font = lv.font_load(f"Z:MicroPython/lv_font_{family}_{size}.fnt")
                global_font_cache[font_family + str(font_size)] = load_font
                return load_font
            except:
                if family == font_family and size == font_size:
                    print(f'WARNING: lv.font_{family}_{size} is NOT supported!')

global_image_cache = {}
def load_image(file):
    global global_image_cache
    if file in global_image_cache:
        return global_image_cache[file]
    try:
        with open(file,'rb') as f:
            data = f.read()
    except:
        print(f'Could not open {file}')
        sys.exit()

    img = lv.img_dsc_t({
        'data_size': len(data),
        'data': data
    })
    global_image_cache[file] = img
    return img

def calendar_event_handler(e,obj):
    code = e.get_code()

    if code == lv.EVENT.VALUE_CHANGED:
        source = e.get_current_target()
        date = lv.calendar_date_t()
        if source.get_pressed_date(date) == lv.RES.OK:
            source.set_highlighted_dates([date], 1)

def spinbox_increment_event_cb(e, obj):
    code = e.get_code()
    if code == lv.EVENT.SHORT_CLICKED or code == lv.EVENT.LONG_PRESSED_REPEAT:
        obj.increment()
def spinbox_decrement_event_cb(e, obj):
    code = e.get_code()
    if code == lv.EVENT.SHORT_CLICKED or code == lv.EVENT.LONG_PRESSED_REPEAT:
        obj.decrement()

def digital_clock_cb(timer, obj, current_time, show_second, use_ampm):
    hour = int(current_time[0])
    minute = int(current_time[1])
    second = int(current_time[2])
    ampm = current_time[3]
    second = second + 1
    if second == 60:
        second = 0
        minute = minute + 1
        if minute == 60:
            minute = 0
            hour = hour + 1
            if use_ampm:
                if hour == 12:
                    if ampm == 'AM':
                        ampm = 'PM'
                    elif ampm == 'PM':
                        ampm = 'AM'
                if hour > 12:
                    hour = hour % 12
    hour = hour % 24
    if use_ampm:
        if show_second:
            obj.set_text("%d:%02d:%02d %s" %(hour, minute, second, ampm))
        else:
            obj.set_text("%d:%02d %s" %(hour, minute, ampm))
    else:
        if show_second:
            obj.set_text("%d:%02d:%02d" %(hour, minute, second))
        else:
            obj.set_text("%d:%02d" %(hour, minute))
    current_time[0] = hour
    current_time[1] = minute
    current_time[2] = second
    current_time[3] = ampm

def analog_clock_cb(timer, obj):
    datetime = time.localtime()
    hour = datetime[3]
    if hour >= 12: hour = hour - 12
    obj.set_time(hour, datetime[4], datetime[5])

def datetext_event_handler(e, obj):
    code = e.get_code()
    target = e.get_target()
    if code == lv.EVENT.FOCUSED:
        if obj is None:
            bg = lv.layer_top()
            bg.add_flag(lv.obj.FLAG.CLICKABLE)
            obj = lv.calendar(bg)
            scr = target.get_screen()
            scr_height = scr.get_height()
            scr_width = scr.get_width()
            obj.set_size(int(scr_width * 0.8), int(scr_height * 0.8))
            datestring = target.get_text()
            year = int(datestring.split('/')[0])
            month = int(datestring.split('/')[1])
            day = int(datestring.split('/')[2])
            obj.set_showed_date(year, month)
            highlighted_days=[lv.calendar_date_t({'year':year, 'month':month, 'day':day})]
            obj.set_highlighted_dates(highlighted_days, 1)
            obj.align(lv.ALIGN.CENTER, 0, 0)
            lv.calendar_header_arrow(obj)
            obj.add_event_cb(lambda e: datetext_calendar_event_handler(e, target), lv.EVENT.ALL, None)
            scr.update_layout()

def datetext_calendar_event_handler(e, obj):
    code = e.get_code()
    target = e.get_current_target()
    if code == lv.EVENT.VALUE_CHANGED:
        date = lv.calendar_date_t()
        if target.get_pressed_date(date) == lv.RES.OK:
            obj.set_text(f"{date.year}/{date.month}/{date.day}")
            bg = lv.layer_top()
            bg.clear_flag(lv.obj.FLAG.CLICKABLE)
            bg.set_style_bg_opa(lv.OPA.TRANSP, 0)
            target.delete()

def ta_event_cb(e,kb):
    code = e.get_code()
    ta = e.get_target()
    if code == lv.EVENT.FOCUSED:
        kb.set_textarea(ta)
        kb.move_foreground()
        kb.clear_flag(lv.obj.FLAG.HIDDEN)

    if code == lv.EVENT.DEFOCUSED:
        kb.set_textarea(None)
        kb.move_background()
        kb.add_flag(lv.obj.FLAG.HIDDEN)

# Create screen_reppo
screen_reppo = lv.obj()
g_kb_screen_reppo = lv.keyboard(screen_reppo)
g_kb_screen_reppo.add_event_cb(lambda e: ta_event_cb(e, g_kb_screen_reppo), lv.EVENT.ALL, None)
g_kb_screen_reppo.add_flag(lv.obj.FLAG.HIDDEN)
g_kb_screen_reppo.set_style_text_font(test_font("Acme_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reppo.set_size(320, 170)
screen_reppo.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
# Set style for screen_reppo, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_reppo.set_style_bg_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reppo.set_style_bg_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reppo.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_reppo_reppo_gif
screen_reppo_reppo_gif = lv.animimg(screen_reppo)
screen_reppo_reppo_gif_imgs = [None]*11
screen_reppo_reppo_gif_imgs[0] = "B:MicroPython/screen_reppo_reppo_gifReppo_label_v3_00_320x170.bin"
screen_reppo_reppo_gif_imgs[1] = "B:MicroPython/screen_reppo_reppo_gifReppo_label_v3_01_320x170.bin"
screen_reppo_reppo_gif_imgs[2] = "B:MicroPython/screen_reppo_reppo_gifReppo_label_v3_02_320x170.bin"
screen_reppo_reppo_gif_imgs[3] = "B:MicroPython/screen_reppo_reppo_gifReppo_label_v3_05_320x170.bin"
screen_reppo_reppo_gif_imgs[4] = "B:MicroPython/screen_reppo_reppo_gifReppo_label_v3_06_320x170.bin"
screen_reppo_reppo_gif_imgs[5] = "B:MicroPython/screen_reppo_reppo_gifReppo_label_v3_09_320x170.bin"
screen_reppo_reppo_gif_imgs[6] = "B:MicroPython/screen_reppo_reppo_gifReppo_label_v3_10_320x170.bin"
screen_reppo_reppo_gif_imgs[7] = "B:MicroPython/screen_reppo_reppo_gifReppo_label_v3_13_320x170.bin"
screen_reppo_reppo_gif_imgs[8] = "B:MicroPython/screen_reppo_reppo_gifReppo_label_v3_14_320x170.bin"
screen_reppo_reppo_gif_imgs[9] = "B:MicroPython/screen_reppo_reppo_gifReppo_label_v3_17_320x170.bin"
screen_reppo_reppo_gif_imgs[10] = "B:MicroPython/screen_reppo_reppo_gifReppo_label_v3_18_320x170.bin"
screen_reppo_reppo_gif.set_src(screen_reppo_reppo_gif_imgs, 11, False)
screen_reppo_reppo_gif.set_duration(80*11)
screen_reppo_reppo_gif.set_repeat_count(1)
screen_reppo_reppo_gif.start()
screen_reppo_reppo_gif.set_pos(0, 0)
screen_reppo_reppo_gif.set_size(320, 170)

screen_reppo.update_layout()
# Create screen_log
screen_log = lv.obj()
g_kb_screen_log = lv.keyboard(screen_log)
g_kb_screen_log.add_event_cb(lambda e: ta_event_cb(e, g_kb_screen_log), lv.EVENT.ALL, None)
g_kb_screen_log.add_flag(lv.obj.FLAG.HIDDEN)
g_kb_screen_log.set_style_text_font(test_font("Acme_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_log.set_size(320, 170)
screen_log.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
# Set style for screen_log, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_log.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_log.set_style_bg_img_src("B:MicroPython/_reppo_background_320x170.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_log.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_log.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_log_reppo_logo
screen_log_reppo_logo = lv.img(screen_log)
screen_log_reppo_logo.set_src("B:MicroPython/_Reppo_LOGO_V4_1_alpha_100x100.bin")
screen_log_reppo_logo.add_flag(lv.obj.FLAG.CLICKABLE)
screen_log_reppo_logo.set_pivot(50,50)
screen_log_reppo_logo.set_angle(0)
screen_log_reppo_logo.set_pos(111, 33)
screen_log_reppo_logo.set_size(100, 100)
# Set style for screen_log_reppo_logo, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_log_reppo_logo.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_log_reppo_logo.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_log_reppo_logo.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

screen_log.update_layout()
# Create screen_main
screen_main = lv.obj()
g_kb_screen_main = lv.keyboard(screen_main)
g_kb_screen_main.add_event_cb(lambda e: ta_event_cb(e, g_kb_screen_main), lv.EVENT.ALL, None)
g_kb_screen_main.add_flag(lv.obj.FLAG.HIDDEN)
g_kb_screen_main.set_style_text_font(test_font("Acme_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main.set_size(320, 170)
screen_main.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
# Set style for screen_main, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main.set_style_bg_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main.set_style_bg_color(lv.color_hex(0x0e1b28), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main.set_style_bg_img_src("B:MicroPython/_screen_main_bg_320x170.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_img_wifi
screen_main_img_wifi = lv.img(screen_main)
screen_main_img_wifi.set_src("B:MicroPython/_wifi_log_2_alpha_24x24.bin")
screen_main_img_wifi.add_flag(lv.obj.FLAG.CLICKABLE)
screen_main_img_wifi.set_pivot(50,50)
screen_main_img_wifi.set_angle(0)
screen_main_img_wifi.set_pos(236, 6)
screen_main_img_wifi.set_size(24, 24)
# Set style for screen_main_img_wifi, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_img_wifi.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_wifi.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_wifi.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_img_reppo
screen_main_img_reppo = lv.img(screen_main)
screen_main_img_reppo.set_src("B:MicroPython/_Reppo_LOGO_V4_1_alpha_25x25.bin")
screen_main_img_reppo.add_flag(lv.obj.FLAG.CLICKABLE)
screen_main_img_reppo.set_pivot(50,50)
screen_main_img_reppo.set_angle(0)
screen_main_img_reppo.set_pos(3, 5)
screen_main_img_reppo.set_size(25, 25)
# Set style for screen_main_img_reppo, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_img_reppo.set_style_img_recolor_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_reppo.set_style_img_recolor(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_reppo.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_reppo.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_reppo.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_label_reppo
screen_main_label_reppo = lv.label(screen_main)
screen_main_label_reppo.set_text("Reppo")
screen_main_label_reppo.set_long_mode(lv.label.LONG.WRAP)
screen_main_label_reppo.set_width(lv.pct(100))
screen_main_label_reppo.set_pos(32, 13)
screen_main_label_reppo.set_size(38, 10)
# Set style for screen_main_label_reppo, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_label_reppo.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_reppo.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_reppo.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_reppo.set_style_text_font(test_font("ArchitectsDaughter", 10), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_reppo.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_reppo.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_reppo.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_reppo.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_reppo.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_reppo.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_reppo.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_reppo.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_reppo.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_reppo.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_img_battery
screen_main_img_battery = lv.img(screen_main)
screen_main_img_battery.set_src("B:MicroPython/_battery_label_v3_alpha_18x18.bin")
screen_main_img_battery.add_flag(lv.obj.FLAG.CLICKABLE)
screen_main_img_battery.set_pivot(50,50)
screen_main_img_battery.set_angle(0)
screen_main_img_battery.set_pos(272, 10)
screen_main_img_battery.set_size(18, 18)
# Set style for screen_main_img_battery, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_img_battery.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_battery.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_battery.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_img_ble
screen_main_img_ble = lv.img(screen_main)
screen_main_img_ble.set_src("B:MicroPython/_ble_label_v3_alpha_14x14.bin")
screen_main_img_ble.add_flag(lv.obj.FLAG.CLICKABLE)
screen_main_img_ble.set_pivot(50,50)
screen_main_img_ble.set_angle(0)
screen_main_img_ble.set_pos(256, 11)
screen_main_img_ble.set_size(14, 14)
# Set style for screen_main_img_ble, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_img_ble.set_style_img_recolor_opa(215, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_ble.set_style_img_recolor(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_ble.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_ble.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_ble.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_img_todolist
screen_main_img_todolist = lv.img(screen_main)
screen_main_img_todolist.set_src("B:MicroPython/_todolist_label_v4_alpha_60x80.bin")
screen_main_img_todolist.add_flag(lv.obj.FLAG.CLICKABLE)
screen_main_img_todolist.set_pivot(50,50)
screen_main_img_todolist.set_angle(0)
screen_main_img_todolist.set_pos(20, 45)
screen_main_img_todolist.set_size(60, 80)
# Set style for screen_main_img_todolist, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_img_todolist.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_todolist.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_todolist.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_img_word
screen_main_img_word = lv.img(screen_main)
screen_main_img_word.set_src("B:MicroPython/_word_label_v4_alpha_60x80.bin")
screen_main_img_word.add_flag(lv.obj.FLAG.CLICKABLE)
screen_main_img_word.set_pivot(50,50)
screen_main_img_word.set_angle(0)
screen_main_img_word.set_pos(95, 45)
screen_main_img_word.set_size(60, 80)
# Set style for screen_main_img_word, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_img_word.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_word.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_word.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_img_timer
screen_main_img_timer = lv.img(screen_main)
screen_main_img_timer.set_src("B:MicroPython/_timing_label_v4_alpha_60x80.bin")
screen_main_img_timer.add_flag(lv.obj.FLAG.CLICKABLE)
screen_main_img_timer.set_pivot(50,50)
screen_main_img_timer.set_angle(0)
screen_main_img_timer.set_pos(172, 45)
screen_main_img_timer.set_size(60, 80)
# Set style for screen_main_img_timer, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_img_timer.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_timer.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_timer.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_img_setting
screen_main_img_setting = lv.img(screen_main)
screen_main_img_setting.set_src("B:MicroPython/_setting_label_v4_alpha_60x80.bin")
screen_main_img_setting.add_flag(lv.obj.FLAG.CLICKABLE)
screen_main_img_setting.set_pivot(50,50)
screen_main_img_setting.set_angle(0)
screen_main_img_setting.set_pos(248, 45)
screen_main_img_setting.set_size(60, 80)
# Set style for screen_main_img_setting, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_img_setting.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_setting.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_setting.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_label_word
screen_main_label_word = lv.label(screen_main)
screen_main_label_word.set_text("VOCAB")
screen_main_label_word.set_long_mode(lv.label.LONG.WRAP)
screen_main_label_word.set_width(lv.pct(100))
screen_main_label_word.set_pos(95, 88)
screen_main_label_word.set_size(57, 11)
# Set style for screen_main_label_word, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_label_word.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_word.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_word.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_word.set_style_text_font(test_font("Alatsi_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_word.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_word.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_word.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_word.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_word.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_word.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_word.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_word.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_word.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_word.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_label_timer
screen_main_label_timer = lv.label(screen_main)
screen_main_label_timer.set_text("TIMER")
screen_main_label_timer.set_long_mode(lv.label.LONG.WRAP)
screen_main_label_timer.set_width(lv.pct(100))
screen_main_label_timer.set_pos(186, 88)
screen_main_label_timer.set_size(32, 12)
# Set style for screen_main_label_timer, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_label_timer.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_timer.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_timer.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_timer.set_style_text_font(test_font("Alatsi_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_timer.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_timer.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_timer.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_timer.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_timer.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_timer.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_timer.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_timer.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_timer.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_timer.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_label_setting
screen_main_label_setting = lv.label(screen_main)
screen_main_label_setting.set_text("SETTING")
screen_main_label_setting.set_long_mode(lv.label.LONG.WRAP)
screen_main_label_setting.set_width(lv.pct(100))
screen_main_label_setting.set_pos(253, 88)
screen_main_label_setting.set_size(51, 12)
# Set style for screen_main_label_setting, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_label_setting.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_setting.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_setting.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_setting.set_style_text_font(test_font("Alatsi_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_setting.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_setting.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_setting.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_setting.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_setting.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_setting.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_setting.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_setting.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_setting.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_setting.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_btn_word
screen_main_btn_word = lv.btn(screen_main)
screen_main_btn_word_label = lv.label(screen_main_btn_word)
screen_main_btn_word_label.set_text("")
screen_main_btn_word_label.set_long_mode(lv.label.LONG.WRAP)
screen_main_btn_word_label.set_width(lv.pct(100))
screen_main_btn_word_label.align(lv.ALIGN.CENTER, 0, 0)
screen_main_btn_word.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_main_btn_word.set_pos(95, 45)
screen_main_btn_word.set_size(60, 80)
# Set style for screen_main_btn_word, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_btn_word.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_word.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_word.set_style_radius(10, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_word.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_word.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_word.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_word.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_word.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_main_btn_word, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_main_btn_word.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_word.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_word.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_word.set_style_shadow_width(10, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_word.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_word.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_word.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_word.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_word.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_word.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_word.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_word.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_main_btn_timer
screen_main_btn_timer = lv.btn(screen_main)
screen_main_btn_timer_label = lv.label(screen_main_btn_timer)
screen_main_btn_timer_label.set_text("")
screen_main_btn_timer_label.set_long_mode(lv.label.LONG.WRAP)
screen_main_btn_timer_label.set_width(lv.pct(100))
screen_main_btn_timer_label.align(lv.ALIGN.CENTER, 0, 0)
screen_main_btn_timer.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_main_btn_timer.set_pos(172, 45)
screen_main_btn_timer.set_size(60, 80)
# Set style for screen_main_btn_timer, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_btn_timer.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_timer.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_timer.set_style_radius(10, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_timer.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_timer.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_timer.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_timer.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_timer.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_main_btn_timer, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_main_btn_timer.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_timer.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_timer.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_timer.set_style_shadow_width(10, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_timer.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_timer.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_timer.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_timer.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_timer.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_timer.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_timer.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_timer.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_main_btn_setting
screen_main_btn_setting = lv.btn(screen_main)
screen_main_btn_setting_label = lv.label(screen_main_btn_setting)
screen_main_btn_setting_label.set_text("")
screen_main_btn_setting_label.set_long_mode(lv.label.LONG.WRAP)
screen_main_btn_setting_label.set_width(lv.pct(100))
screen_main_btn_setting_label.align(lv.ALIGN.CENTER, 0, 0)
screen_main_btn_setting.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_main_btn_setting.set_pos(248, 45)
screen_main_btn_setting.set_size(60, 80)
# Set style for screen_main_btn_setting, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_btn_setting.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_setting.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_setting.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_setting.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_setting.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_setting.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_setting.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_setting.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_main_btn_setting, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_main_btn_setting.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_setting.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_setting.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_setting.set_style_shadow_width(10, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_setting.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_setting.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_setting.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_setting.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_setting.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_setting.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_setting.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_setting.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_main_img_uptext
screen_main_img_uptext = lv.img(screen_main)
screen_main_img_uptext.set_src("B:MicroPython/_probg4_alpha_165x21.bin")
screen_main_img_uptext.add_flag(lv.obj.FLAG.CLICKABLE)
screen_main_img_uptext.set_pivot(50,50)
screen_main_img_uptext.set_angle(0)
screen_main_img_uptext.set_pos(74, 8)
screen_main_img_uptext.set_size(165, 21)
# Set style for screen_main_img_uptext, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_img_uptext.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_uptext.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_uptext.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_label_uptext
screen_main_label_uptext = lv.label(screen_main)
screen_main_label_uptext.set_text("No one is perfect")
screen_main_label_uptext.set_long_mode(lv.label.LONG.WRAP)
screen_main_label_uptext.set_width(lv.pct(100))
screen_main_label_uptext.set_pos(77, 10)
screen_main_label_uptext.set_size(159, 16)
# Set style for screen_main_label_uptext, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_label_uptext.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_uptext.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_uptext.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_uptext.set_style_text_font(test_font("Alatsi_Regular", 14), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_uptext.set_style_text_opa(143, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_uptext.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_uptext.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_uptext.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_uptext.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_uptext.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_uptext.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_uptext.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_uptext.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_uptext.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_img_plane
screen_main_img_plane = lv.img(screen_main)
screen_main_img_plane.set_src(load_image(r"E:\esp32idf\GUI_GUIDER_PRJ\03-320170test\generated\MicroPython\plane_35_28.png"))
screen_main_img_plane.add_flag(lv.obj.FLAG.CLICKABLE)
screen_main_img_plane.set_pivot(0,0)
screen_main_img_plane.set_angle(150)
screen_main_img_plane.set_pos(281, 131)
screen_main_img_plane.set_size(35, 28)
# Set style for screen_main_img_plane, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_img_plane.set_style_img_recolor_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_plane.set_style_img_recolor(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_plane.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_plane.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_plane.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_btn_plane
screen_main_btn_plane = lv.btn(screen_main)
screen_main_btn_plane_label = lv.label(screen_main_btn_plane)
screen_main_btn_plane_label.set_text("")
screen_main_btn_plane_label.set_long_mode(lv.label.LONG.WRAP)
screen_main_btn_plane_label.set_width(lv.pct(100))
screen_main_btn_plane_label.align(lv.ALIGN.CENTER, 0, 0)
screen_main_btn_plane.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_main_btn_plane.set_pos(273, 134)
screen_main_btn_plane.set_size(40, 29)
# Set style for screen_main_btn_plane, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_btn_plane.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_plane.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_plane.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_plane.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_plane.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_plane.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_plane.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_plane.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_main_btn_plane, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_main_btn_plane.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_plane.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_plane.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_plane.set_style_shadow_width(10, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_plane.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_plane.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_plane.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_plane.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_plane.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_plane.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_plane.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_plane.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_main_img_probg1
screen_main_img_probg1 = lv.img(screen_main)
screen_main_img_probg1.set_src("B:MicroPython/_progress_bg2_alpha_76x18.bin")
screen_main_img_probg1.add_flag(lv.obj.FLAG.CLICKABLE)
screen_main_img_probg1.set_pivot(50,50)
screen_main_img_probg1.set_angle(0)
screen_main_img_probg1.set_pos(20, 149)
screen_main_img_probg1.set_size(76, 18)
# Set style for screen_main_img_probg1, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_img_probg1.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_probg1.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_probg1.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_label_done
screen_main_label_done = lv.label(screen_main)
screen_main_label_done.set_text("Done")
screen_main_label_done.set_long_mode(lv.label.LONG.WRAP)
screen_main_label_done.set_width(lv.pct(100))
screen_main_label_done.set_pos(24, 131)
screen_main_label_done.set_size(32, 12)
# Set style for screen_main_label_done, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_label_done.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_done.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_done.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_done.set_style_text_font(test_font("Alatsi_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_done.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_done.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_done.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_done.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_done.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_done.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_done.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_done.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_done.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_done.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_label_donenum
screen_main_label_donenum = lv.label(screen_main)
screen_main_label_donenum.set_text("5")
screen_main_label_donenum.set_long_mode(lv.label.LONG.WRAP)
screen_main_label_donenum.set_width(lv.pct(100))
screen_main_label_donenum.set_pos(74, 129)
screen_main_label_donenum.set_size(17, 13)
# Set style for screen_main_label_donenum, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_label_donenum.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_donenum.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_donenum.set_style_text_color(lv.color_hex(0xb0d7ff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_donenum.set_style_text_font(test_font("Acme_Regular", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_donenum.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_donenum.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_donenum.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_donenum.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_donenum.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_donenum.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_donenum.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_donenum.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_donenum.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_donenum.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_img_runpace
screen_main_img_runpace = lv.img(screen_main)
screen_main_img_runpace.set_src("B:MicroPython/_progress_bg3_alpha_206x20.bin")
screen_main_img_runpace.add_flag(lv.obj.FLAG.CLICKABLE)
screen_main_img_runpace.set_pivot(50,50)
screen_main_img_runpace.set_angle(0)
screen_main_img_runpace.set_pos(100, 138)
screen_main_img_runpace.set_size(206, 20)
# Set style for screen_main_img_runpace, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_img_runpace.set_style_img_recolor_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_runpace.set_style_img_recolor(lv.color_hex(0x000000), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_runpace.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_runpace.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_runpace.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_label_nodone
screen_main_label_nodone = lv.label(screen_main)
screen_main_label_nodone.set_text("ToDo")
screen_main_label_nodone.set_long_mode(lv.label.LONG.WRAP)
screen_main_label_nodone.set_width(lv.pct(100))
screen_main_label_nodone.set_pos(20, 152)
screen_main_label_nodone.set_size(38, 12)
# Set style for screen_main_label_nodone, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_label_nodone.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_nodone.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_nodone.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_nodone.set_style_text_font(test_font("Alatsi_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_nodone.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_nodone.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_nodone.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_nodone.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_nodone.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_nodone.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_nodone.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_nodone.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_nodone.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_nodone.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_img_probg2
screen_main_img_probg2 = lv.img(screen_main)
screen_main_img_probg2.set_src("B:MicroPython/_progress_bg2_alpha_76x18.bin")
screen_main_img_probg2.add_flag(lv.obj.FLAG.CLICKABLE)
screen_main_img_probg2.set_pivot(50,50)
screen_main_img_probg2.set_angle(0)
screen_main_img_probg2.set_pos(20, 128)
screen_main_img_probg2.set_size(76, 18)
# Set style for screen_main_img_probg2, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_img_probg2.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_probg2.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_img_probg2.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_label_todonum
screen_main_label_todonum = lv.label(screen_main)
screen_main_label_todonum.set_text("4")
screen_main_label_todonum.set_long_mode(lv.label.LONG.WRAP)
screen_main_label_todonum.set_width(lv.pct(100))
screen_main_label_todonum.set_pos(74, 150)
screen_main_label_todonum.set_size(18, 14)
# Set style for screen_main_label_todonum, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_label_todonum.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todonum.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todonum.set_style_text_color(lv.color_hex(0xffceaa), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todonum.set_style_text_font(test_font("Acme_Regular", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todonum.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todonum.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todonum.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todonum.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todonum.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todonum.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todonum.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todonum.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todonum.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todonum.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_label_todolist
screen_main_label_todolist = lv.label(screen_main)
screen_main_label_todolist.set_text("TO DO LIST")
screen_main_label_todolist.set_long_mode(lv.label.LONG.WRAP)
screen_main_label_todolist.set_width(lv.pct(100))
screen_main_label_todolist.set_pos(24, 88)
screen_main_label_todolist.set_size(53, 11)
# Set style for screen_main_label_todolist, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_label_todolist.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todolist.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todolist.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todolist.set_style_text_font(test_font("Alatsi_Regular", 11), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todolist.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todolist.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todolist.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todolist.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todolist.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todolist.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todolist.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todolist.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todolist.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_todolist.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_main_btn_todolist
screen_main_btn_todolist = lv.btn(screen_main)
screen_main_btn_todolist_label = lv.label(screen_main_btn_todolist)
screen_main_btn_todolist_label.set_text("")
screen_main_btn_todolist_label.set_long_mode(lv.label.LONG.WRAP)
screen_main_btn_todolist_label.set_width(lv.pct(100))
screen_main_btn_todolist_label.align(lv.ALIGN.CENTER, 0, 0)
screen_main_btn_todolist.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_main_btn_todolist.set_pos(20, 45)
screen_main_btn_todolist.set_size(60, 80)
# Set style for screen_main_btn_todolist, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_btn_todolist.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_todolist.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_todolist.set_style_radius(10, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_todolist.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_todolist.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_todolist.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_todolist.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_btn_todolist.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_main_btn_todolist, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_main_btn_todolist.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_todolist.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_todolist.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_todolist.set_style_shadow_width(10, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_todolist.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_todolist.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_todolist.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_todolist.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_todolist.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_todolist.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_todolist.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_main_btn_todolist.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_main_label_battery
screen_main_label_battery = lv.label(screen_main)
screen_main_label_battery.set_text("100%")
screen_main_label_battery.set_long_mode(lv.label.LONG.WRAP)
screen_main_label_battery.set_width(lv.pct(100))
screen_main_label_battery.set_pos(289, 13)
screen_main_label_battery.set_size(31, 9)
# Set style for screen_main_label_battery, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_main_label_battery.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_battery.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_battery.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_battery.set_style_text_font(test_font("arial", 11), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_battery.set_style_text_opa(177, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_battery.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_battery.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_battery.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_battery.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_battery.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_battery.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_battery.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_battery.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_main_label_battery.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

screen_main.update_layout()
# Create screen_todolist
screen_todolist = lv.obj()
g_kb_screen_todolist = lv.keyboard(screen_todolist)
g_kb_screen_todolist.add_event_cb(lambda e: ta_event_cb(e, g_kb_screen_todolist), lv.EVENT.ALL, None)
g_kb_screen_todolist.add_flag(lv.obj.FLAG.HIDDEN)
g_kb_screen_todolist.set_style_text_font(test_font("Acme_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist.set_size(320, 170)
screen_todolist.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
# Set style for screen_todolist, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist.set_style_bg_img_src("B:MicroPython/_screen_todolist_bg_320x170.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_todolist_btn_back
screen_todolist_btn_back = lv.btn(screen_todolist)
screen_todolist_btn_back_label = lv.label(screen_todolist_btn_back)
screen_todolist_btn_back_label.set_text("")
screen_todolist_btn_back_label.set_long_mode(lv.label.LONG.WRAP)
screen_todolist_btn_back_label.set_width(lv.pct(100))
screen_todolist_btn_back_label.align(lv.ALIGN.CENTER, 0, 0)
screen_todolist_btn_back.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_todolist_btn_back.set_pos(292, 5)
screen_todolist_btn_back.set_size(20, 20)
# Set style for screen_todolist_btn_back, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_btn_back.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_back.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_back.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_back.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_back.set_style_bg_img_src("B:MicroPython/_home_20x20.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_back.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_back.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_back.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_back.set_style_text_font(test_font("montserratMedium", 20), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_back.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_back.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_todolist_btn_back, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_todolist_btn_back.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_back.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_back.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_back.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_back.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_back.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_back.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_back.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_back.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_back.set_style_bg_img_src("B:MicroPython/_home_20x20.bin", lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_back.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_back.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_back.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_back.set_style_text_font(test_font("montserratMedium", 20), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_back.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_todolist_img_addpage
screen_todolist_img_addpage = lv.img(screen_todolist)
screen_todolist_img_addpage.set_src("B:MicroPython/_group_add5_alpha_98x20.bin")
screen_todolist_img_addpage.add_flag(lv.obj.FLAG.CLICKABLE)
screen_todolist_img_addpage.set_pivot(50,50)
screen_todolist_img_addpage.set_angle(0)
screen_todolist_img_addpage.set_pos(10, 146)
screen_todolist_img_addpage.set_size(98, 20)
# Set style for screen_todolist_img_addpage, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_img_addpage.set_style_img_opa(177, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_img_addpage.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_img_addpage.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_todolist_label_addpage
screen_todolist_label_addpage = lv.label(screen_todolist)
screen_todolist_label_addpage.set_text("Del Page -")
screen_todolist_label_addpage.set_long_mode(lv.label.LONG.WRAP)
screen_todolist_label_addpage.set_width(lv.pct(100))
screen_todolist_label_addpage.set_pos(18, 150)
screen_todolist_label_addpage.set_size(86, 14)
# Set style for screen_todolist_label_addpage, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_label_addpage.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_addpage.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_addpage.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_addpage.set_style_text_font(test_font("arial", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_addpage.set_style_text_opa(172, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_addpage.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_addpage.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_addpage.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_addpage.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_addpage.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_addpage.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_addpage.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_addpage.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_addpage.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_todolist_btn_delpage
screen_todolist_btn_delpage = lv.btn(screen_todolist)
screen_todolist_btn_delpage_label = lv.label(screen_todolist_btn_delpage)
screen_todolist_btn_delpage_label.set_text("")
screen_todolist_btn_delpage_label.set_long_mode(lv.label.LONG.WRAP)
screen_todolist_btn_delpage_label.set_width(lv.pct(100))
screen_todolist_btn_delpage_label.align(lv.ALIGN.CENTER, 0, 0)
screen_todolist_btn_delpage.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_todolist_btn_delpage.set_pos(12, 149)
screen_todolist_btn_delpage.set_size(93, 15)
# Set style for screen_todolist_btn_delpage, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_btn_delpage.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_delpage.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_delpage.set_style_radius(10, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_delpage.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_delpage.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_delpage.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_delpage.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_delpage.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_todolist_btn_delpage, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_todolist_btn_delpage.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_delpage.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_delpage.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_delpage.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_delpage.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_delpage.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_delpage.set_style_shadow_spread(2, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_delpage.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_delpage.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_delpage.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_delpage.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_delpage.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_todolist_btn_todo1
screen_todolist_btn_todo1 = lv.btn(screen_todolist)
screen_todolist_btn_todo1_label = lv.label(screen_todolist_btn_todo1)
screen_todolist_btn_todo1_label.set_text("")
screen_todolist_btn_todo1_label.set_long_mode(lv.label.LONG.WRAP)
screen_todolist_btn_todo1_label.set_width(lv.pct(100))
screen_todolist_btn_todo1_label.align(lv.ALIGN.CENTER, 0, 0)
screen_todolist_btn_todo1.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_todolist_btn_todo1.set_pos(13, 38)
screen_todolist_btn_todo1.set_size(145, 45)
# Set style for screen_todolist_btn_todo1, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_btn_todo1.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo1.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo1.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo1.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo1.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo1.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo1.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo1.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_todolist_btn_todo1, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_todolist_btn_todo1.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo1.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo1.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo1.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo1.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo1.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo1.set_style_shadow_spread(2, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo1.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo1.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo1.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo1.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo1.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_todolist_btn_todo2
screen_todolist_btn_todo2 = lv.btn(screen_todolist)
screen_todolist_btn_todo2_label = lv.label(screen_todolist_btn_todo2)
screen_todolist_btn_todo2_label.set_text("")
screen_todolist_btn_todo2_label.set_long_mode(lv.label.LONG.WRAP)
screen_todolist_btn_todo2_label.set_width(lv.pct(100))
screen_todolist_btn_todo2_label.align(lv.ALIGN.CENTER, 0, 0)
screen_todolist_btn_todo2.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_todolist_btn_todo2.set_pos(168, 37)
screen_todolist_btn_todo2.set_size(144, 45)
# Set style for screen_todolist_btn_todo2, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_btn_todo2.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo2.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo2.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo2.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo2.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo2.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo2.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo2.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_todolist_btn_todo2, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_todolist_btn_todo2.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo2.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo2.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo2.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo2.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo2.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo2.set_style_shadow_spread(2, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo2.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo2.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo2.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo2.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo2.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_todolist_btn_todo3
screen_todolist_btn_todo3 = lv.btn(screen_todolist)
screen_todolist_btn_todo3_label = lv.label(screen_todolist_btn_todo3)
screen_todolist_btn_todo3_label.set_text("")
screen_todolist_btn_todo3_label.set_long_mode(lv.label.LONG.WRAP)
screen_todolist_btn_todo3_label.set_width(lv.pct(100))
screen_todolist_btn_todo3_label.align(lv.ALIGN.CENTER, 0, 0)
screen_todolist_btn_todo3.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_todolist_btn_todo3.set_pos(13, 91)
screen_todolist_btn_todo3.set_size(145, 46)
# Set style for screen_todolist_btn_todo3, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_btn_todo3.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo3.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo3.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo3.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo3.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo3.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo3.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo3.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_todolist_btn_todo3, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_todolist_btn_todo3.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo3.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo3.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo3.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo3.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo3.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo3.set_style_shadow_spread(2, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo3.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo3.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo3.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo3.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo3.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_todolist_btn_todo4
screen_todolist_btn_todo4 = lv.btn(screen_todolist)
screen_todolist_btn_todo4_label = lv.label(screen_todolist_btn_todo4)
screen_todolist_btn_todo4_label.set_text("")
screen_todolist_btn_todo4_label.set_long_mode(lv.label.LONG.WRAP)
screen_todolist_btn_todo4_label.set_width(lv.pct(100))
screen_todolist_btn_todo4_label.align(lv.ALIGN.CENTER, 0, 0)
screen_todolist_btn_todo4.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_todolist_btn_todo4.set_pos(168, 92)
screen_todolist_btn_todo4.set_size(145, 44)
# Set style for screen_todolist_btn_todo4, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_btn_todo4.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo4.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo4.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo4.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo4.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo4.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo4.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_todo4.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_todolist_btn_todo4, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_todolist_btn_todo4.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo4.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo4.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo4.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo4.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo4.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo4.set_style_shadow_spread(2, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo4.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo4.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo4.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo4.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_todo4.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_todolist_img_delpage
screen_todolist_img_delpage = lv.img(screen_todolist)
screen_todolist_img_delpage.set_src("B:MicroPython/_group_add5_alpha_98x20.bin")
screen_todolist_img_delpage.add_flag(lv.obj.FLAG.CLICKABLE)
screen_todolist_img_delpage.set_pivot(50,50)
screen_todolist_img_delpage.set_angle(0)
screen_todolist_img_delpage.set_pos(215, 146)
screen_todolist_img_delpage.set_size(98, 20)
# Set style for screen_todolist_img_delpage, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_img_delpage.set_style_img_opa(177, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_img_delpage.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_img_delpage.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_todolist_label_delpage
screen_todolist_label_delpage = lv.label(screen_todolist)
screen_todolist_label_delpage.set_text("Add Page +")
screen_todolist_label_delpage.set_long_mode(lv.label.LONG.WRAP)
screen_todolist_label_delpage.set_width(lv.pct(100))
screen_todolist_label_delpage.set_pos(231, 149)
screen_todolist_label_delpage.set_size(65, 12)
# Set style for screen_todolist_label_delpage, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_label_delpage.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_delpage.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_delpage.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_delpage.set_style_text_font(test_font("arial", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_delpage.set_style_text_opa(169, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_delpage.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_delpage.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_delpage.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_delpage.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_delpage.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_delpage.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_delpage.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_delpage.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_delpage.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_todolist_btn_addpage
screen_todolist_btn_addpage = lv.btn(screen_todolist)
screen_todolist_btn_addpage_label = lv.label(screen_todolist_btn_addpage)
screen_todolist_btn_addpage_label.set_text("")
screen_todolist_btn_addpage_label.set_long_mode(lv.label.LONG.WRAP)
screen_todolist_btn_addpage_label.set_width(lv.pct(100))
screen_todolist_btn_addpage_label.align(lv.ALIGN.CENTER, 0, 0)
screen_todolist_btn_addpage.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_todolist_btn_addpage.set_pos(218, 149)
screen_todolist_btn_addpage.set_size(91, 14)
# Set style for screen_todolist_btn_addpage, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_btn_addpage.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_addpage.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_addpage.set_style_radius(10, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_addpage.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_addpage.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_addpage.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_addpage.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_addpage.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_todolist_btn_addpage, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_todolist_btn_addpage.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_addpage.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_addpage.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_addpage.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_addpage.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_addpage.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_addpage.set_style_shadow_spread(2, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_addpage.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_addpage.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_addpage.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_addpage.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_addpage.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_todolist_label_indexcut
screen_todolist_label_indexcut = lv.label(screen_todolist)
screen_todolist_label_indexcut.set_text("/")
screen_todolist_label_indexcut.set_long_mode(lv.label.LONG.WRAP)
screen_todolist_label_indexcut.set_width(lv.pct(100))
screen_todolist_label_indexcut.set_pos(155, 150)
screen_todolist_label_indexcut.set_size(17, 14)
# Set style for screen_todolist_label_indexcut, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_label_indexcut.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcut.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcut.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcut.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcut.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcut.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcut.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcut.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcut.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcut.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcut.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcut.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcut.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcut.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_todolist_btn_pageminus
screen_todolist_btn_pageminus = lv.btn(screen_todolist)
screen_todolist_btn_pageminus_label = lv.label(screen_todolist_btn_pageminus)
screen_todolist_btn_pageminus_label.set_text("<<")
screen_todolist_btn_pageminus_label.set_long_mode(lv.label.LONG.WRAP)
screen_todolist_btn_pageminus_label.set_width(lv.pct(100))
screen_todolist_btn_pageminus_label.align(lv.ALIGN.CENTER, 0, 0)
screen_todolist_btn_pageminus.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_todolist_btn_pageminus.set_pos(113, 146)
screen_todolist_btn_pageminus.set_size(25, 20)
# Set style for screen_todolist_btn_pageminus, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_btn_pageminus.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_pageminus.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_pageminus.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_pageminus.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_pageminus.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_pageminus.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_pageminus.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_pageminus.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_todolist_btn_pageminus, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_todolist_btn_pageminus.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_pageminus.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_pageminus.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_pageminus.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_pageminus.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_pageminus.set_style_shadow_opa(128, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_pageminus.set_style_shadow_spread(2, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_pageminus.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_pageminus.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_pageminus.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_pageminus.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_pageminus.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_todolist_btn_pageplus
screen_todolist_btn_pageplus = lv.btn(screen_todolist)
screen_todolist_btn_pageplus_label = lv.label(screen_todolist_btn_pageplus)
screen_todolist_btn_pageplus_label.set_text(">>")
screen_todolist_btn_pageplus_label.set_long_mode(lv.label.LONG.WRAP)
screen_todolist_btn_pageplus_label.set_width(lv.pct(100))
screen_todolist_btn_pageplus_label.align(lv.ALIGN.CENTER, 0, 0)
screen_todolist_btn_pageplus.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_todolist_btn_pageplus.set_pos(188, 146)
screen_todolist_btn_pageplus.set_size(25, 20)
# Set style for screen_todolist_btn_pageplus, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_btn_pageplus.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_pageplus.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_pageplus.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_pageplus.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_pageplus.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_pageplus.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_pageplus.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_btn_pageplus.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_todolist_btn_pageplus, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_todolist_btn_pageplus.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_pageplus.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_pageplus.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_pageplus.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_pageplus.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_pageplus.set_style_shadow_opa(128, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_pageplus.set_style_shadow_spread(2, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_pageplus.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_pageplus.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_pageplus.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_pageplus.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_todolist_btn_pageplus.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_todolist_label_indexcur
screen_todolist_label_indexcur = lv.label(screen_todolist)
screen_todolist_label_indexcur.set_text("1")
screen_todolist_label_indexcur.set_long_mode(lv.label.LONG.WRAP)
screen_todolist_label_indexcur.set_width(lv.pct(100))
screen_todolist_label_indexcur.set_pos(138, 150)
screen_todolist_label_indexcur.set_size(20, 14)
# Set style for screen_todolist_label_indexcur, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_label_indexcur.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcur.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcur.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcur.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcur.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcur.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcur.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcur.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcur.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcur.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcur.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcur.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcur.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexcur.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_todolist_label_indexall
screen_todolist_label_indexall = lv.label(screen_todolist)
screen_todolist_label_indexall.set_text("1")
screen_todolist_label_indexall.set_long_mode(lv.label.LONG.WRAP)
screen_todolist_label_indexall.set_width(lv.pct(100))
screen_todolist_label_indexall.set_pos(168, 150)
screen_todolist_label_indexall.set_size(20, 15)
# Set style for screen_todolist_label_indexall, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_label_indexall.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexall.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexall.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexall.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexall.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexall.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexall.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexall.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexall.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexall.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexall.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexall.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexall.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_indexall.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_todolist_label_done
screen_todolist_label_done = lv.label(screen_todolist)
screen_todolist_label_done.set_text("Done")
screen_todolist_label_done.set_long_mode(lv.label.LONG.WRAP)
screen_todolist_label_done.set_width(lv.pct(100))
screen_todolist_label_done.set_pos(10, 5)
screen_todolist_label_done.set_size(40, 15)
# Set style for screen_todolist_label_done, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_label_done.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_done.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_done.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_done.set_style_text_font(test_font("Acme_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_done.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_done.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_done.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_done.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_done.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_done.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_done.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_done.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_done.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_done.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_todolist_label_todo
screen_todolist_label_todo = lv.label(screen_todolist)
screen_todolist_label_todo.set_text("ToDo")
screen_todolist_label_todo.set_long_mode(lv.label.LONG.WRAP)
screen_todolist_label_todo.set_width(lv.pct(100))
screen_todolist_label_todo.set_pos(10, 20)
screen_todolist_label_todo.set_size(40, 15)
# Set style for screen_todolist_label_todo, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_label_todo.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo.set_style_text_font(test_font("Acme_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_todolist_label_donenum
screen_todolist_label_donenum = lv.label(screen_todolist)
screen_todolist_label_donenum.set_text("0")
screen_todolist_label_donenum.set_long_mode(lv.label.LONG.WRAP)
screen_todolist_label_donenum.set_width(lv.pct(100))
screen_todolist_label_donenum.set_pos(50, 5)
screen_todolist_label_donenum.set_size(15, 15)
# Set style for screen_todolist_label_donenum, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_label_donenum.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_donenum.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_donenum.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_donenum.set_style_text_font(test_font("Acme_Regular", 14), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_donenum.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_donenum.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_donenum.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_donenum.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_donenum.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_donenum.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_donenum.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_donenum.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_donenum.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_donenum.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_todolist_label_todonum
screen_todolist_label_todonum = lv.label(screen_todolist)
screen_todolist_label_todonum.set_text("0")
screen_todolist_label_todonum.set_long_mode(lv.label.LONG.WRAP)
screen_todolist_label_todonum.set_width(lv.pct(100))
screen_todolist_label_todonum.set_pos(50, 20)
screen_todolist_label_todonum.set_size(15, 15)
# Set style for screen_todolist_label_todonum, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_label_todonum.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todonum.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todonum.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todonum.set_style_text_font(test_font("Acme_Regular", 14), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todonum.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todonum.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todonum.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todonum.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todonum.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todonum.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todonum.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todonum.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todonum.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todonum.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_todolist_label_todo1
screen_todolist_label_todo1 = lv.label(screen_todolist)
screen_todolist_label_todo1.set_text("TO DO 1: 英语学习一个小时")
screen_todolist_label_todo1.set_long_mode(lv.label.LONG.CLIP)
screen_todolist_label_todo1.set_width(lv.pct(100))
screen_todolist_label_todo1.set_pos(17, 50)
screen_todolist_label_todo1.set_size(135, 15)
# Set style for screen_todolist_label_todo1, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_label_todo1.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo1.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo1.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo1.set_style_text_font(test_font("AdobeFangsongStdRegular", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo1.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo1.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo1.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo1.set_style_text_align(lv.TEXT_ALIGN.LEFT, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo1.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo1.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo1.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo1.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo1.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo1.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_todolist_label_todo2
screen_todolist_label_todo2 = lv.label(screen_todolist)
screen_todolist_label_todo2.set_text("TO DO 2: 编程任务一个小时")
screen_todolist_label_todo2.set_long_mode(lv.label.LONG.CLIP)
screen_todolist_label_todo2.set_width(lv.pct(100))
screen_todolist_label_todo2.set_pos(173, 50)
screen_todolist_label_todo2.set_size(135, 15)
# Set style for screen_todolist_label_todo2, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_label_todo2.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo2.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo2.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo2.set_style_text_font(test_font("AdobeFangsongStdRegular", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo2.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo2.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo2.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo2.set_style_text_align(lv.TEXT_ALIGN.LEFT, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo2.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo2.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo2.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo2.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo2.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo2.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_todolist_label_todo3
screen_todolist_label_todo3 = lv.label(screen_todolist)
screen_todolist_label_todo3.set_text("TO DO 3: 语文学习一个小时")
screen_todolist_label_todo3.set_long_mode(lv.label.LONG.CLIP)
screen_todolist_label_todo3.set_width(lv.pct(100))
screen_todolist_label_todo3.set_pos(18, 107)
screen_todolist_label_todo3.set_size(135, 15)
# Set style for screen_todolist_label_todo3, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_label_todo3.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo3.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo3.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo3.set_style_text_font(test_font("AdobeFangsongStdRegular", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo3.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo3.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo3.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo3.set_style_text_align(lv.TEXT_ALIGN.LEFT, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo3.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo3.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo3.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo3.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo3.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo3.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_todolist_label_todo4
screen_todolist_label_todo4 = lv.label(screen_todolist)
screen_todolist_label_todo4.set_text("TO DO 4: 英语单词背诵20个")
screen_todolist_label_todo4.set_long_mode(lv.label.LONG.CLIP)
screen_todolist_label_todo4.set_width(lv.pct(100))
screen_todolist_label_todo4.set_pos(173, 107)
screen_todolist_label_todo4.set_size(135, 15)
# Set style for screen_todolist_label_todo4, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_todolist_label_todo4.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo4.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo4.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo4.set_style_text_font(test_font("AdobeFangsongStdRegular", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo4.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo4.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo4.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo4.set_style_text_align(lv.TEXT_ALIGN.LEFT, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo4.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo4.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo4.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo4.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo4.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_todolist_label_todo4.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

screen_todolist.update_layout()
# Create screen_timing
screen_timing = lv.obj()
g_kb_screen_timing = lv.keyboard(screen_timing)
g_kb_screen_timing.add_event_cb(lambda e: ta_event_cb(e, g_kb_screen_timing), lv.EVENT.ALL, None)
g_kb_screen_timing.add_flag(lv.obj.FLAG.HIDDEN)
g_kb_screen_timing.set_style_text_font(test_font("Acme_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing.set_size(320, 170)
screen_timing.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
# Set style for screen_timing, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_timing.set_style_bg_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing.set_style_bg_color(lv.color_hex(0x000000), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_timing_img_moon
screen_timing_img_moon = lv.img(screen_timing)
screen_timing_img_moon.set_src("B:MicroPython/_moon_alpha_160x160.bin")
screen_timing_img_moon.add_flag(lv.obj.FLAG.CLICKABLE)
screen_timing_img_moon.set_pivot(50,50)
screen_timing_img_moon.set_angle(0)
screen_timing_img_moon.set_pos(8, 3)
screen_timing_img_moon.set_size(160, 160)
# Set style for screen_timing_img_moon, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_timing_img_moon.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_img_moon.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_img_moon.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_timing_label_realtime
screen_timing_label_realtime = lv.label(screen_timing)
screen_timing_label_realtime.set_text("10 : 32")
screen_timing_label_realtime.set_long_mode(lv.label.LONG.WRAP)
screen_timing_label_realtime.set_width(lv.pct(100))
screen_timing_label_realtime.set_pos(165, 15)
screen_timing_label_realtime.set_size(132, 43)
# Set style for screen_timing_label_realtime, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_timing_label_realtime.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_realtime.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_realtime.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_realtime.set_style_text_font(test_font("Alatsi_Regular", 48), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_realtime.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_realtime.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_realtime.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_realtime.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_realtime.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_realtime.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_realtime.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_realtime.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_realtime.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_realtime.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_timing_label_day
screen_timing_label_day = lv.label(screen_timing)
screen_timing_label_day.set_text("Saturday")
screen_timing_label_day.set_long_mode(lv.label.LONG.WRAP)
screen_timing_label_day.set_width(lv.pct(100))
screen_timing_label_day.set_pos(177, 66)
screen_timing_label_day.set_size(114, 21)
# Set style for screen_timing_label_day, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_timing_label_day.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_day.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_day.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_day.set_style_text_font(test_font("Alatsi_Regular", 20), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_day.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_day.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_day.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_day.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_day.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_day.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_day.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_day.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_day.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_day.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_timing_line_1
screen_timing_line_1 = lv.line(screen_timing)
screen_timing_line_1_line_points = [{"x":0, "y":0},{"x":200, "y":0},]
screen_timing_line_1.set_points(screen_timing_line_1_line_points, 2)
screen_timing_line_1.set_pos(171, 92)
screen_timing_line_1.set_size(147, 6)
# Set style for screen_timing_line_1, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_timing_line_1.set_style_line_width(2, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_line_1.set_style_line_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_line_1.set_style_line_opa(174, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_line_1.set_style_line_rounded(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_timing_line_2
screen_timing_line_2 = lv.line(screen_timing)
screen_timing_line_2_line_points = [{"x":0, "y":0},{"x":200, "y":0},]
screen_timing_line_2.set_points(screen_timing_line_2_line_points, 2)
screen_timing_line_2.set_pos(161, 119)
screen_timing_line_2.set_size(162, 1)
# Set style for screen_timing_line_2, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_timing_line_2.set_style_line_width(2, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_line_2.set_style_line_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_line_2.set_style_line_opa(163, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_line_2.set_style_line_rounded(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_timing_label_moon
screen_timing_label_moon = lv.label(screen_timing)
screen_timing_label_moon.set_text("Humans to Moon")
screen_timing_label_moon.set_long_mode(lv.label.LONG.WRAP)
screen_timing_label_moon.set_width(lv.pct(100))
screen_timing_label_moon.set_pos(168, 95)
screen_timing_label_moon.set_size(146, 18)
# Set style for screen_timing_label_moon, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_timing_label_moon.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_moon.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_moon.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_moon.set_style_text_font(test_font("Alatsi_Regular", 18), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_moon.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_moon.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_moon.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_moon.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_moon.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_moon.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_moon.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_moon.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_moon.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_moon.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_timing_label_date
screen_timing_label_date = lv.label(screen_timing)
screen_timing_label_date.set_text("2025/12/25")
screen_timing_label_date.set_long_mode(lv.label.LONG.WRAP)
screen_timing_label_date.set_width(lv.pct(100))
screen_timing_label_date.set_pos(181, 125)
screen_timing_label_date.set_size(124, 20)
# Set style for screen_timing_label_date, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_timing_label_date.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_date.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_date.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_date.set_style_text_font(test_font("Acme_Regular", 20), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_date.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_date.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_date.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_date.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_date.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_date.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_date.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_date.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_date.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_label_date.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_timing_btn_pomodoro
screen_timing_btn_pomodoro = lv.btn(screen_timing)
screen_timing_btn_pomodoro_label = lv.label(screen_timing_btn_pomodoro)
screen_timing_btn_pomodoro_label.set_text("")
screen_timing_btn_pomodoro_label.set_long_mode(lv.label.LONG.WRAP)
screen_timing_btn_pomodoro_label.set_width(lv.pct(100))
screen_timing_btn_pomodoro_label.align(lv.ALIGN.CENTER, 0, 0)
screen_timing_btn_pomodoro.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_timing_btn_pomodoro.set_pos(297, 3)
screen_timing_btn_pomodoro.set_size(20, 20)
# Set style for screen_timing_btn_pomodoro, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_timing_btn_pomodoro.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_btn_pomodoro.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_btn_pomodoro.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_btn_pomodoro.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_btn_pomodoro.set_style_bg_img_src("B:MicroPython/_home_20x20.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_btn_pomodoro.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_btn_pomodoro.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_btn_pomodoro.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_btn_pomodoro.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_btn_pomodoro.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_btn_pomodoro.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_timing_btn_pomodoro, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_timing_btn_pomodoro.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_pomodoro.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_pomodoro.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_pomodoro.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_pomodoro.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_pomodoro.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_pomodoro.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_pomodoro.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_pomodoro.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_pomodoro.set_style_bg_img_src("B:MicroPython/_home_20x20.bin", lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_pomodoro.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_pomodoro.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_pomodoro.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_pomodoro.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_pomodoro.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_timing_btn_back
screen_timing_btn_back = lv.btn(screen_timing)
screen_timing_btn_back_label = lv.label(screen_timing_btn_back)
screen_timing_btn_back_label.set_text("<")
screen_timing_btn_back_label.set_long_mode(lv.label.LONG.WRAP)
screen_timing_btn_back_label.set_width(lv.pct(100))
screen_timing_btn_back_label.align(lv.ALIGN.CENTER, 0, 0)
screen_timing_btn_back.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_timing_btn_back.set_pos(5, 3)
screen_timing_btn_back.set_size(20, 20)
# Set style for screen_timing_btn_back, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_timing_btn_back.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_btn_back.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_btn_back.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_btn_back.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_btn_back.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_btn_back.set_style_text_font(test_font("montserratMedium", 20), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_btn_back.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_btn_back.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_timing_btn_back, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_timing_btn_back.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_back.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_back.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_back.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_back.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_back.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_back.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_back.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_back.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_back.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_back.set_style_text_font(test_font("montserratMedium", 20), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_timing_btn_back.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_timing_img_night
screen_timing_img_night = lv.img(screen_timing)
screen_timing_img_night.set_src("B:MicroPython/_night_alpha_25x25.bin")
screen_timing_img_night.add_flag(lv.obj.FLAG.CLICKABLE)
screen_timing_img_night.set_pivot(50,50)
screen_timing_img_night.set_angle(0)
screen_timing_img_night.set_pos(291, 61)
screen_timing_img_night.set_size(25, 25)
screen_timing_img_night.add_flag(lv.obj.FLAG.HIDDEN)
# Set style for screen_timing_img_night, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_timing_img_night.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_img_night.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_img_night.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_timing_img_morning
screen_timing_img_morning = lv.img(screen_timing)
screen_timing_img_morning.set_src("B:MicroPython/_morning_alpha_33x31.bin")
screen_timing_img_morning.add_flag(lv.obj.FLAG.CLICKABLE)
screen_timing_img_morning.set_pivot(50,50)
screen_timing_img_morning.set_angle(0)
screen_timing_img_morning.set_pos(286, 57)
screen_timing_img_morning.set_size(33, 31)
# Set style for screen_timing_img_morning, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_timing_img_morning.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_img_morning.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_timing_img_morning.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

screen_timing.update_layout()
# Create screen_pomodoro
screen_pomodoro = lv.obj()
g_kb_screen_pomodoro = lv.keyboard(screen_pomodoro)
g_kb_screen_pomodoro.add_event_cb(lambda e: ta_event_cb(e, g_kb_screen_pomodoro), lv.EVENT.ALL, None)
g_kb_screen_pomodoro.add_flag(lv.obj.FLAG.HIDDEN)
g_kb_screen_pomodoro.set_style_text_font(test_font("Acme_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro.set_size(320, 170)
screen_pomodoro.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
# Set style for screen_pomodoro, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_pomodoro.set_style_bg_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro.set_style_bg_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro.set_style_bg_img_src("B:MicroPython/_pomodoro_bg_320x170.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_pomodoro_label_addnum
screen_pomodoro_label_addnum = lv.label(screen_pomodoro)
screen_pomodoro_label_addnum.set_text("1")
screen_pomodoro_label_addnum.set_long_mode(lv.label.LONG.WRAP)
screen_pomodoro_label_addnum.set_width(lv.pct(100))
screen_pomodoro_label_addnum.set_pos(134, 113)
screen_pomodoro_label_addnum.set_size(56, 16)
# Set style for screen_pomodoro_label_addnum, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_pomodoro_label_addnum.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_addnum.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_addnum.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_addnum.set_style_text_font(test_font("AdobeFangsongStdRegular", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_addnum.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_addnum.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_addnum.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_addnum.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_addnum.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_addnum.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_addnum.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_addnum.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_addnum.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_addnum.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_pomodoro_img_pomorect1
screen_pomodoro_img_pomorect1 = lv.img(screen_pomodoro)
screen_pomodoro_img_pomorect1.set_src("B:MicroPython/_pomorect_alpha_257x52.bin")
screen_pomodoro_img_pomorect1.add_flag(lv.obj.FLAG.CLICKABLE)
screen_pomodoro_img_pomorect1.set_pivot(50,50)
screen_pomodoro_img_pomorect1.set_angle(0)
screen_pomodoro_img_pomorect1.set_pos(37, 29)
screen_pomodoro_img_pomorect1.set_size(257, 52)
# Set style for screen_pomodoro_img_pomorect1, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_pomodoro_img_pomorect1.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_img_pomorect1.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_img_pomorect1.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_pomodoro_label_timer
screen_pomodoro_label_timer = lv.label(screen_pomodoro)
screen_pomodoro_label_timer.set_text("00:25:00")
screen_pomodoro_label_timer.set_long_mode(lv.label.LONG.WRAP)
screen_pomodoro_label_timer.set_width(lv.pct(100))
screen_pomodoro_label_timer.set_pos(94, 36)
screen_pomodoro_label_timer.set_size(141, 27)
# Set style for screen_pomodoro_label_timer, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_pomodoro_label_timer.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_timer.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_timer.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_timer.set_style_text_font(test_font("Abel_regular", 30), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_timer.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_timer.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_timer.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_timer.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_timer.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_timer.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_timer.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_timer.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_timer.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_timer.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_pomodoro_label_funcstate
screen_pomodoro_label_funcstate = lv.label(screen_pomodoro)
screen_pomodoro_label_funcstate.set_text("CountDown")
screen_pomodoro_label_funcstate.set_long_mode(lv.label.LONG.WRAP)
screen_pomodoro_label_funcstate.set_width(lv.pct(100))
screen_pomodoro_label_funcstate.set_pos(104, 66)
screen_pomodoro_label_funcstate.set_size(119, 15)
# Set style for screen_pomodoro_label_funcstate, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_pomodoro_label_funcstate.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_funcstate.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_funcstate.set_style_text_color(lv.color_hex(0xb586c1), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_funcstate.set_style_text_font(test_font("AdobeFangsongStdRegular", 14), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_funcstate.set_style_text_opa(163, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_funcstate.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_funcstate.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_funcstate.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_funcstate.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_funcstate.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_funcstate.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_funcstate.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_funcstate.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_funcstate.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_pomodoro_label_pomodoro
screen_pomodoro_label_pomodoro = lv.label(screen_pomodoro)
screen_pomodoro_label_pomodoro.set_text("Pomodoro Focus")
screen_pomodoro_label_pomodoro.set_long_mode(lv.label.LONG.WRAP)
screen_pomodoro_label_pomodoro.set_width(lv.pct(100))
screen_pomodoro_label_pomodoro.set_pos(62, 6)
screen_pomodoro_label_pomodoro.set_size(210, 17)
# Set style for screen_pomodoro_label_pomodoro, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_pomodoro_label_pomodoro.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_pomodoro.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_pomodoro.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_pomodoro.set_style_text_font(test_font("AdobeFangsongStdRegular", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_pomodoro.set_style_text_opa(143, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_pomodoro.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_pomodoro.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_pomodoro.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_pomodoro.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_pomodoro.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_pomodoro.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_pomodoro.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_pomodoro.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_label_pomodoro.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_pomodoro_btn_stopwatch
screen_pomodoro_btn_stopwatch = lv.btn(screen_pomodoro)
screen_pomodoro_btn_stopwatch_label = lv.label(screen_pomodoro_btn_stopwatch)
screen_pomodoro_btn_stopwatch_label.set_text("StopWatch")
screen_pomodoro_btn_stopwatch_label.set_long_mode(lv.label.LONG.WRAP)
screen_pomodoro_btn_stopwatch_label.set_width(lv.pct(100))
screen_pomodoro_btn_stopwatch_label.align(lv.ALIGN.CENTER, 0, 0)
screen_pomodoro_btn_stopwatch.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_pomodoro_btn_stopwatch.set_pos(37, 87)
screen_pomodoro_btn_stopwatch.set_size(125, 15)
# Set style for screen_pomodoro_btn_stopwatch, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_pomodoro_btn_stopwatch.set_style_bg_opa(40, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_stopwatch.set_style_bg_color(lv.color_hex(0xc3b5b5), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_stopwatch.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_stopwatch.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_stopwatch.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_stopwatch.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_stopwatch.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_stopwatch.set_style_text_font(test_font("AdobeFangsongStdRegular", 14), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_stopwatch.set_style_text_opa(221, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_stopwatch.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_pomodoro_btn_stopwatch, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_pomodoro_btn_stopwatch.set_style_bg_opa(28, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_stopwatch.set_style_bg_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_stopwatch.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_stopwatch.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_stopwatch.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_stopwatch.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_stopwatch.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_stopwatch.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_stopwatch.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_stopwatch.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_stopwatch.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_stopwatch.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_stopwatch.set_style_text_font(test_font("SourceHanSerifSC_Regular", 13), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_stopwatch.set_style_text_opa(122, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_pomodoro_btn_countdown
screen_pomodoro_btn_countdown = lv.btn(screen_pomodoro)
screen_pomodoro_btn_countdown_label = lv.label(screen_pomodoro_btn_countdown)
screen_pomodoro_btn_countdown_label.set_text("CountDown")
screen_pomodoro_btn_countdown_label.set_long_mode(lv.label.LONG.WRAP)
screen_pomodoro_btn_countdown_label.set_width(lv.pct(100))
screen_pomodoro_btn_countdown_label.align(lv.ALIGN.CENTER, 0, 0)
screen_pomodoro_btn_countdown.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_pomodoro_btn_countdown.set_pos(167, 87)
screen_pomodoro_btn_countdown.set_size(125, 15)
# Set style for screen_pomodoro_btn_countdown, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_pomodoro_btn_countdown.set_style_bg_opa(38, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_countdown.set_style_bg_color(lv.color_hex(0xbebdbd), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_countdown.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_countdown.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_countdown.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_countdown.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_countdown.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_countdown.set_style_text_font(test_font("AdobeFangsongStdRegular", 14), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_countdown.set_style_text_opa(226, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_countdown.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_pomodoro_btn_countdown, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_pomodoro_btn_countdown.set_style_bg_opa(19, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_countdown.set_style_bg_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_countdown.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_countdown.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_countdown.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_countdown.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_countdown.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_countdown.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_countdown.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_countdown.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_countdown.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_countdown.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_countdown.set_style_text_font(test_font("SourceHanSerifSC_Regular", 13), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_countdown.set_style_text_opa(129, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_pomodoro_btn_back
screen_pomodoro_btn_back = lv.btn(screen_pomodoro)
screen_pomodoro_btn_back_label = lv.label(screen_pomodoro_btn_back)
screen_pomodoro_btn_back_label.set_text("<")
screen_pomodoro_btn_back_label.set_long_mode(lv.label.LONG.WRAP)
screen_pomodoro_btn_back_label.set_width(lv.pct(100))
screen_pomodoro_btn_back_label.align(lv.ALIGN.CENTER, 0, 0)
screen_pomodoro_btn_back.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_pomodoro_btn_back.set_pos(4, 3)
screen_pomodoro_btn_back.set_size(20, 20)
# Set style for screen_pomodoro_btn_back, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_pomodoro_btn_back.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_back.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_back.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_back.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_back.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_back.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_back.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_back.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_pomodoro_btn_back, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_pomodoro_btn_back.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_back.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_back.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_back.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_back.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_back.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_back.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_back.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_back.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_back.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_back.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_back.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_pomodoro_btn_home
screen_pomodoro_btn_home = lv.btn(screen_pomodoro)
screen_pomodoro_btn_home_label = lv.label(screen_pomodoro_btn_home)
screen_pomodoro_btn_home_label.set_text("")
screen_pomodoro_btn_home_label.set_long_mode(lv.label.LONG.WRAP)
screen_pomodoro_btn_home_label.set_width(lv.pct(100))
screen_pomodoro_btn_home_label.align(lv.ALIGN.CENTER, 0, 0)
screen_pomodoro_btn_home.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_pomodoro_btn_home.set_pos(294, 3)
screen_pomodoro_btn_home.set_size(20, 20)
# Set style for screen_pomodoro_btn_home, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_pomodoro_btn_home.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_home.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_home.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_home.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_home.set_style_bg_img_src("B:MicroPython/_pomodoro2_20x20.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_home.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_home.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_home.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_home.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_home.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_home.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_pomodoro_btn_home, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_pomodoro_btn_home.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_home.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_home.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_home.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_home.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_home.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_home.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_home.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_home.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_home.set_style_bg_img_src("B:MicroPython/_pomodoro2_20x20.bin", lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_home.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_home.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_home.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_home.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_home.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_pomodoro_btn_start
screen_pomodoro_btn_start = lv.btn(screen_pomodoro)
screen_pomodoro_btn_start_label = lv.label(screen_pomodoro_btn_start)
screen_pomodoro_btn_start_label.set_text("Start")
screen_pomodoro_btn_start_label.set_long_mode(lv.label.LONG.WRAP)
screen_pomodoro_btn_start_label.set_width(lv.pct(100))
screen_pomodoro_btn_start_label.align(lv.ALIGN.CENTER, 0, 0)
screen_pomodoro_btn_start.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_pomodoro_btn_start.set_pos(94, 145)
screen_pomodoro_btn_start.set_size(66, 16)
# Set style for screen_pomodoro_btn_start, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_pomodoro_btn_start.set_style_bg_opa(34, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_start.set_style_bg_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_start.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_start.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_start.set_style_radius(10, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_start.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_start.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_start.set_style_text_font(test_font("AdobeFangsongStdRegular", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_start.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_start.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_pomodoro_btn_start, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_pomodoro_btn_start.set_style_bg_opa(34, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_start.set_style_bg_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_start.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_start.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_start.set_style_radius(10, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_start.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_start.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_start.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_start.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_start.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_start.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_start.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_start.set_style_text_font(test_font("SourceHanSerifSC_Regular", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_start.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_pomodoro_btn_reset
screen_pomodoro_btn_reset = lv.btn(screen_pomodoro)
screen_pomodoro_btn_reset_label = lv.label(screen_pomodoro_btn_reset)
screen_pomodoro_btn_reset_label.set_text("Reset")
screen_pomodoro_btn_reset_label.set_long_mode(lv.label.LONG.WRAP)
screen_pomodoro_btn_reset_label.set_width(lv.pct(100))
screen_pomodoro_btn_reset_label.align(lv.ALIGN.CENTER, 0, 0)
screen_pomodoro_btn_reset.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_pomodoro_btn_reset.set_pos(170, 145)
screen_pomodoro_btn_reset.set_size(66, 16)
# Set style for screen_pomodoro_btn_reset, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_pomodoro_btn_reset.set_style_bg_opa(34, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_reset.set_style_bg_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_reset.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_reset.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_reset.set_style_radius(10, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_reset.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_reset.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_reset.set_style_text_font(test_font("AdobeFangsongStdRegular", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_reset.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_reset.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_pomodoro_btn_reset, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_pomodoro_btn_reset.set_style_bg_opa(43, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_reset.set_style_bg_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_reset.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_reset.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_reset.set_style_radius(10, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_reset.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_reset.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_reset.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_reset.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_reset.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_reset.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_reset.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_reset.set_style_text_font(test_font("SourceHanSerifSC_Regular", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_reset.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_pomodoro_btn_addnum
screen_pomodoro_btn_addnum = lv.btn(screen_pomodoro)
screen_pomodoro_btn_addnum_label = lv.label(screen_pomodoro_btn_addnum)
screen_pomodoro_btn_addnum_label.set_text("")
screen_pomodoro_btn_addnum_label.set_long_mode(lv.label.LONG.WRAP)
screen_pomodoro_btn_addnum_label.set_width(lv.pct(100))
screen_pomodoro_btn_addnum_label.align(lv.ALIGN.CENTER, 0, 0)
screen_pomodoro_btn_addnum.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_pomodoro_btn_addnum.set_pos(129, 109)
screen_pomodoro_btn_addnum.set_size(64, 25)
# Set style for screen_pomodoro_btn_addnum, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_pomodoro_btn_addnum.set_style_bg_opa(25, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_addnum.set_style_bg_color(lv.color_hex(0xe2ecf4), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_addnum.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_addnum.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_addnum.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_addnum.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_addnum.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_addnum.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_addnum.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_addnum.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_pomodoro_btn_addnum, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_pomodoro_btn_addnum.set_style_bg_opa(29, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_addnum.set_style_bg_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_addnum.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_addnum.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_addnum.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_addnum.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_addnum.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_addnum.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_addnum.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_addnum.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_addnum.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_addnum.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_addnum.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_addnum.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_pomodoro_btn_minus
screen_pomodoro_btn_minus = lv.btn(screen_pomodoro)
screen_pomodoro_btn_minus_label = lv.label(screen_pomodoro_btn_minus)
screen_pomodoro_btn_minus_label.set_text("-")
screen_pomodoro_btn_minus_label.set_long_mode(lv.label.LONG.WRAP)
screen_pomodoro_btn_minus_label.set_width(lv.pct(100))
screen_pomodoro_btn_minus_label.align(lv.ALIGN.CENTER, 0, 0)
screen_pomodoro_btn_minus.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_pomodoro_btn_minus.set_pos(94, 112)
screen_pomodoro_btn_minus.set_size(24, 18)
# Set style for screen_pomodoro_btn_minus, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_pomodoro_btn_minus.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_minus.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_minus.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_minus.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_minus.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_minus.set_style_text_font(test_font("montserratMedium", 25), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_minus.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_minus.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_pomodoro_btn_minus, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_pomodoro_btn_minus.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_minus.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_minus.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_minus.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_minus.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_minus.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_minus.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_minus.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_minus.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_minus.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_minus.set_style_text_font(test_font("montserratMedium", 25), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_minus.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_pomodoro_btn_plus
screen_pomodoro_btn_plus = lv.btn(screen_pomodoro)
screen_pomodoro_btn_plus_label = lv.label(screen_pomodoro_btn_plus)
screen_pomodoro_btn_plus_label.set_text("+")
screen_pomodoro_btn_plus_label.set_long_mode(lv.label.LONG.WRAP)
screen_pomodoro_btn_plus_label.set_width(lv.pct(100))
screen_pomodoro_btn_plus_label.align(lv.ALIGN.CENTER, 0, 0)
screen_pomodoro_btn_plus.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_pomodoro_btn_plus.set_pos(205, 112)
screen_pomodoro_btn_plus.set_size(24, 18)
# Set style for screen_pomodoro_btn_plus, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_pomodoro_btn_plus.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_plus.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_plus.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_plus.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_plus.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_plus.set_style_text_font(test_font("montserratMedium", 25), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_plus.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_pomodoro_btn_plus.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_pomodoro_btn_plus, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_pomodoro_btn_plus.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_plus.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_plus.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_plus.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_plus.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_plus.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_plus.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_plus.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_plus.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_plus.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_plus.set_style_text_font(test_font("montserratMedium", 25), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_pomodoro_btn_plus.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

screen_pomodoro.update_layout()
# Create screen_wordmeun
screen_wordmeun = lv.obj()
g_kb_screen_wordmeun = lv.keyboard(screen_wordmeun)
g_kb_screen_wordmeun.add_event_cb(lambda e: ta_event_cb(e, g_kb_screen_wordmeun), lv.EVENT.ALL, None)
g_kb_screen_wordmeun.add_flag(lv.obj.FLAG.HIDDEN)
g_kb_screen_wordmeun.set_style_text_font(test_font("Acme_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun.set_size(320, 170)
screen_wordmeun.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
# Set style for screen_wordmeun, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordmeun.set_style_bg_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun.set_style_bg_color(lv.color_hex(0x000000), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun.set_style_bg_img_src("B:MicroPython/_screen_wordmenu_bg_320x170.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun.set_style_bg_img_opa(128, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wordmeun_img_learn
screen_wordmeun_img_learn = lv.img(screen_wordmeun)
screen_wordmeun_img_learn.set_src("B:MicroPython/_word_rectangle_alpha_129x21.bin")
screen_wordmeun_img_learn.add_flag(lv.obj.FLAG.CLICKABLE)
screen_wordmeun_img_learn.set_pivot(50,50)
screen_wordmeun_img_learn.set_angle(0)
screen_wordmeun_img_learn.set_pos(29, 135)
screen_wordmeun_img_learn.set_size(129, 21)
# Set style for screen_wordmeun_img_learn, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordmeun_img_learn.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_img_learn.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_img_learn.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wordmeun_img_wordrect
screen_wordmeun_img_wordrect = lv.img(screen_wordmeun)
screen_wordmeun_img_wordrect.set_src("B:MicroPython/_word_rectangle_alpha_264x94.bin")
screen_wordmeun_img_wordrect.add_flag(lv.obj.FLAG.CLICKABLE)
screen_wordmeun_img_wordrect.set_pivot(50,50)
screen_wordmeun_img_wordrect.set_angle(0)
screen_wordmeun_img_wordrect.set_pos(28, 33)
screen_wordmeun_img_wordrect.set_size(264, 94)
# Set style for screen_wordmeun_img_wordrect, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordmeun_img_wordrect.set_style_img_recolor_opa(134, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_img_wordrect.set_style_img_recolor(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_img_wordrect.set_style_img_opa(160, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_img_wordrect.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_img_wordrect.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wordmeun_btn_back
screen_wordmeun_btn_back = lv.btn(screen_wordmeun)
screen_wordmeun_btn_back_label = lv.label(screen_wordmeun_btn_back)
screen_wordmeun_btn_back_label.set_text("<")
screen_wordmeun_btn_back_label.set_long_mode(lv.label.LONG.WRAP)
screen_wordmeun_btn_back_label.set_width(lv.pct(100))
screen_wordmeun_btn_back_label.align(lv.ALIGN.CENTER, 0, 0)
screen_wordmeun_btn_back.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_wordmeun_btn_back.set_pos(4, 5)
screen_wordmeun_btn_back.set_size(15, 15)
# Set style for screen_wordmeun_btn_back, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordmeun_btn_back.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_back.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_back.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_back.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_back.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_back.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_back.set_style_text_opa(165, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_back.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_wordmeun_btn_back, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_wordmeun_btn_back.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_back.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_back.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_back.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_back.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_back.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_back.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_back.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_back.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_back.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_back.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_back.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_wordmeun_bar_process
screen_wordmeun_bar_process = lv.bar(screen_wordmeun)
screen_wordmeun_bar_process.set_style_anim_time(1000, 0)
screen_wordmeun_bar_process.set_mode(lv.bar.MODE.NORMAL)
screen_wordmeun_bar_process.set_range(0, 100)
screen_wordmeun_bar_process.set_value(100, lv.ANIM.OFF)
screen_wordmeun_bar_process.set_pos(84, 91)
screen_wordmeun_bar_process.set_size(203, 5)
# Set style for screen_wordmeun_bar_process, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordmeun_bar_process.set_style_bg_opa(134, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_bar_process.set_style_bg_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_bar_process.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_bar_process.set_style_radius(10, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_bar_process.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_wordmeun_bar_process, Part: lv.PART.INDICATOR, State: lv.STATE.DEFAULT.
screen_wordmeun_bar_process.set_style_bg_opa(90, lv.PART.INDICATOR|lv.STATE.DEFAULT)
screen_wordmeun_bar_process.set_style_bg_color(lv.color_hex(0x2195f6), lv.PART.INDICATOR|lv.STATE.DEFAULT)
screen_wordmeun_bar_process.set_style_bg_grad_dir(lv.GRAD_DIR.HOR, lv.PART.INDICATOR|lv.STATE.DEFAULT)
screen_wordmeun_bar_process.set_style_bg_grad_color(lv.color_hex(0x00ff40), lv.PART.INDICATOR|lv.STATE.DEFAULT)
screen_wordmeun_bar_process.set_style_bg_main_stop(0, lv.PART.INDICATOR|lv.STATE.DEFAULT)
screen_wordmeun_bar_process.set_style_bg_grad_stop(255, lv.PART.INDICATOR|lv.STATE.DEFAULT)
screen_wordmeun_bar_process.set_style_radius(10, lv.PART.INDICATOR|lv.STATE.DEFAULT)

# Create screen_wordmeun_label_booksel
screen_wordmeun_label_booksel = lv.label(screen_wordmeun)
screen_wordmeun_label_booksel.set_text("Select Vocab Book")
screen_wordmeun_label_booksel.set_long_mode(lv.label.LONG.WRAP)
screen_wordmeun_label_booksel.set_width(lv.pct(100))
screen_wordmeun_label_booksel.set_pos(58, 8)
screen_wordmeun_label_booksel.set_size(204, 19)
# Set style for screen_wordmeun_label_booksel, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordmeun_label_booksel.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_booksel.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_booksel.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_booksel.set_style_text_font(test_font("SourceHanSerifSC_Regular", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_booksel.set_style_text_opa(163, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_booksel.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_booksel.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_booksel.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_booksel.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_booksel.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_booksel.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_booksel.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_booksel.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_booksel.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wordmeun_img_book
screen_wordmeun_img_book = lv.img(screen_wordmeun)
screen_wordmeun_img_book.set_src("B:MicroPython/_book_alpha_39x46.bin")
screen_wordmeun_img_book.add_flag(lv.obj.FLAG.CLICKABLE)
screen_wordmeun_img_book.set_pivot(50,50)
screen_wordmeun_img_book.set_angle(0)
screen_wordmeun_img_book.set_pos(34, 58)
screen_wordmeun_img_book.set_size(39, 46)
# Set style for screen_wordmeun_img_book, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordmeun_img_book.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_img_book.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_img_book.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wordmeun_label_bookname
screen_wordmeun_label_bookname = lv.label(screen_wordmeun)
screen_wordmeun_label_bookname.set_text("CET4")
screen_wordmeun_label_bookname.set_long_mode(lv.label.LONG.WRAP)
screen_wordmeun_label_bookname.set_width(lv.pct(100))
screen_wordmeun_label_bookname.set_pos(84, 43)
screen_wordmeun_label_bookname.set_size(202, 18)
# Set style for screen_wordmeun_label_bookname, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordmeun_label_bookname.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_bookname.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_bookname.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_bookname.set_style_text_font(test_font("Alatsi_Regular", 18), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_bookname.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_bookname.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_bookname.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_bookname.set_style_text_align(lv.TEXT_ALIGN.LEFT, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_bookname.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_bookname.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_bookname.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_bookname.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_bookname.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_bookname.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wordmeun_label_divdernum
screen_wordmeun_label_divdernum = lv.label(screen_wordmeun)
screen_wordmeun_label_divdernum.set_text("500/2000 words (25%)")
screen_wordmeun_label_divdernum.set_long_mode(lv.label.LONG.WRAP)
screen_wordmeun_label_divdernum.set_width(lv.pct(100))
screen_wordmeun_label_divdernum.set_pos(84, 71)
screen_wordmeun_label_divdernum.set_size(202, 13)
# Set style for screen_wordmeun_label_divdernum, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordmeun_label_divdernum.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_divdernum.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_divdernum.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_divdernum.set_style_text_font(test_font("Alatsi_Regular", 14), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_divdernum.set_style_text_opa(180, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_divdernum.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_divdernum.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_divdernum.set_style_text_align(lv.TEXT_ALIGN.LEFT, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_divdernum.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_divdernum.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_divdernum.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_divdernum.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_divdernum.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_divdernum.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wordmeun_label_wordindicate
screen_wordmeun_label_wordindicate = lv.label(screen_wordmeun)
screen_wordmeun_label_wordindicate.set_text("Learn: 500 Review: 100")
screen_wordmeun_label_wordindicate.set_long_mode(lv.label.LONG.WRAP)
screen_wordmeun_label_wordindicate.set_width(lv.pct(100))
screen_wordmeun_label_wordindicate.set_pos(85, 101)
screen_wordmeun_label_wordindicate.set_size(202, 16)
# Set style for screen_wordmeun_label_wordindicate, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordmeun_label_wordindicate.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_wordindicate.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_wordindicate.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_wordindicate.set_style_text_font(test_font("Alatsi_Regular", 14), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_wordindicate.set_style_text_opa(186, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_wordindicate.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_wordindicate.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_wordindicate.set_style_text_align(lv.TEXT_ALIGN.LEFT, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_wordindicate.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_wordindicate.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_wordindicate.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_wordindicate.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_wordindicate.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_wordindicate.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wordmeun_btn_bookleft
screen_wordmeun_btn_bookleft = lv.btn(screen_wordmeun)
screen_wordmeun_btn_bookleft_label = lv.label(screen_wordmeun_btn_bookleft)
screen_wordmeun_btn_bookleft_label.set_text("<<")
screen_wordmeun_btn_bookleft_label.set_long_mode(lv.label.LONG.WRAP)
screen_wordmeun_btn_bookleft_label.set_width(lv.pct(100))
screen_wordmeun_btn_bookleft_label.align(lv.ALIGN.CENTER, 0, 0)
screen_wordmeun_btn_bookleft.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_wordmeun_btn_bookleft.set_pos(4, 75)
screen_wordmeun_btn_bookleft.set_size(20, 20)
# Set style for screen_wordmeun_btn_bookleft, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordmeun_btn_bookleft.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_bookleft.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_bookleft.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_bookleft.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_bookleft.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_bookleft.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_bookleft.set_style_text_opa(170, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_bookleft.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_wordmeun_btn_bookleft, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_wordmeun_btn_bookleft.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_bookleft.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_bookleft.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_bookleft.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_bookleft.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_bookleft.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_bookleft.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_bookleft.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_bookleft.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_bookleft.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_bookleft.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_bookleft.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_wordmeun_btn_bookright
screen_wordmeun_btn_bookright = lv.btn(screen_wordmeun)
screen_wordmeun_btn_bookright_label = lv.label(screen_wordmeun_btn_bookright)
screen_wordmeun_btn_bookright_label.set_text(">>")
screen_wordmeun_btn_bookright_label.set_long_mode(lv.label.LONG.WRAP)
screen_wordmeun_btn_bookright_label.set_width(lv.pct(100))
screen_wordmeun_btn_bookright_label.align(lv.ALIGN.CENTER, 0, 0)
screen_wordmeun_btn_bookright.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_wordmeun_btn_bookright.set_pos(295, 75)
screen_wordmeun_btn_bookright.set_size(20, 20)
# Set style for screen_wordmeun_btn_bookright, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordmeun_btn_bookright.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_bookright.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_bookright.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_bookright.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_bookright.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_bookright.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_bookright.set_style_text_opa(171, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_bookright.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_wordmeun_btn_bookright, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_wordmeun_btn_bookright.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_bookright.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_bookright.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_bookright.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_bookright.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_bookright.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_bookright.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_bookright.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_bookright.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_bookright.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_bookright.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_bookright.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_wordmeun_label_learn
screen_wordmeun_label_learn = lv.label(screen_wordmeun)
screen_wordmeun_label_learn.set_text("Learn")
screen_wordmeun_label_learn.set_long_mode(lv.label.LONG.WRAP)
screen_wordmeun_label_learn.set_width(lv.pct(100))
screen_wordmeun_label_learn.set_pos(62, 135)
screen_wordmeun_label_learn.set_size(62, 15)
# Set style for screen_wordmeun_label_learn, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordmeun_label_learn.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_learn.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_learn.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_learn.set_style_text_font(test_font("Alatsi_Regular", 18), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_learn.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_learn.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_learn.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_learn.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_learn.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_learn.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_learn.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_learn.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_learn.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_learn.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wordmeun_btn_learn
screen_wordmeun_btn_learn = lv.btn(screen_wordmeun)
screen_wordmeun_btn_learn_label = lv.label(screen_wordmeun_btn_learn)
screen_wordmeun_btn_learn_label.set_text("")
screen_wordmeun_btn_learn_label.set_long_mode(lv.label.LONG.WRAP)
screen_wordmeun_btn_learn_label.set_width(lv.pct(100))
screen_wordmeun_btn_learn_label.align(lv.ALIGN.CENTER, 0, 0)
screen_wordmeun_btn_learn.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_wordmeun_btn_learn.set_pos(29, 136)
screen_wordmeun_btn_learn.set_size(127, 19)
# Set style for screen_wordmeun_btn_learn, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordmeun_btn_learn.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_learn.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_learn.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_learn.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_learn.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_learn.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_learn.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_learn.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_wordmeun_btn_learn, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_wordmeun_btn_learn.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_learn.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_learn.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_learn.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_learn.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_learn.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_learn.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_learn.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_learn.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_learn.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_learn.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_learn.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_wordmeun_img_review
screen_wordmeun_img_review = lv.img(screen_wordmeun)
screen_wordmeun_img_review.set_src("B:MicroPython/_word_rectangle_alpha_129x21.bin")
screen_wordmeun_img_review.add_flag(lv.obj.FLAG.CLICKABLE)
screen_wordmeun_img_review.set_pivot(50,50)
screen_wordmeun_img_review.set_angle(0)
screen_wordmeun_img_review.set_pos(164, 135)
screen_wordmeun_img_review.set_size(129, 21)
# Set style for screen_wordmeun_img_review, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordmeun_img_review.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_img_review.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_img_review.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wordmeun_label_Review
screen_wordmeun_label_Review = lv.label(screen_wordmeun)
screen_wordmeun_label_Review.set_text("Review")
screen_wordmeun_label_Review.set_long_mode(lv.label.LONG.WRAP)
screen_wordmeun_label_Review.set_width(lv.pct(100))
screen_wordmeun_label_Review.set_pos(194, 136)
screen_wordmeun_label_Review.set_size(69, 16)
# Set style for screen_wordmeun_label_Review, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordmeun_label_Review.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_Review.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_Review.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_Review.set_style_text_font(test_font("Alatsi_Regular", 17), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_Review.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_Review.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_Review.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_Review.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_Review.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_Review.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_Review.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_Review.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_Review.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_label_Review.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wordmeun_btn_review
screen_wordmeun_btn_review = lv.btn(screen_wordmeun)
screen_wordmeun_btn_review_label = lv.label(screen_wordmeun_btn_review)
screen_wordmeun_btn_review_label.set_text("")
screen_wordmeun_btn_review_label.set_long_mode(lv.label.LONG.WRAP)
screen_wordmeun_btn_review_label.set_width(lv.pct(100))
screen_wordmeun_btn_review_label.align(lv.ALIGN.CENTER, 0, 0)
screen_wordmeun_btn_review.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_wordmeun_btn_review.set_pos(164, 136)
screen_wordmeun_btn_review.set_size(127, 19)
# Set style for screen_wordmeun_btn_review, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordmeun_btn_review.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_review.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_review.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_review.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_review.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_review.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_review.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordmeun_btn_review.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_wordmeun_btn_review, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_wordmeun_btn_review.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_review.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_review.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_review.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_review.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_review.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_review.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_review.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_review.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_review.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_review.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordmeun_btn_review.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

screen_wordmeun.update_layout()
# Create screen_wordcard
screen_wordcard = lv.obj()
g_kb_screen_wordcard = lv.keyboard(screen_wordcard)
g_kb_screen_wordcard.add_event_cb(lambda e: ta_event_cb(e, g_kb_screen_wordcard), lv.EVENT.ALL, None)
g_kb_screen_wordcard.add_flag(lv.obj.FLAG.HIDDEN)
g_kb_screen_wordcard.set_style_text_font(test_font("Acme_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard.set_size(320, 170)
screen_wordcard.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
# Set style for screen_wordcard, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordcard.set_style_bg_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard.set_style_bg_color(lv.color_hex(0x000000), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard.set_style_bg_img_src("B:MicroPython/_screen_wordcard_bg_320x170.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard.set_style_bg_img_opa(143, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wordcard_img_wordrect
screen_wordcard_img_wordrect = lv.img(screen_wordcard)
screen_wordcard_img_wordrect.set_src("B:MicroPython/_word_rectangle_alpha_264x136.bin")
screen_wordcard_img_wordrect.add_flag(lv.obj.FLAG.CLICKABLE)
screen_wordcard_img_wordrect.set_pivot(50,50)
screen_wordcard_img_wordrect.set_angle(0)
screen_wordcard_img_wordrect.set_pos(28, 25)
screen_wordcard_img_wordrect.set_size(264, 136)
# Set style for screen_wordcard_img_wordrect, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordcard_img_wordrect.set_style_img_opa(152, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_img_wordrect.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_img_wordrect.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wordcard_btn_back
screen_wordcard_btn_back = lv.btn(screen_wordcard)
screen_wordcard_btn_back_label = lv.label(screen_wordcard_btn_back)
screen_wordcard_btn_back_label.set_text("<")
screen_wordcard_btn_back_label.set_long_mode(lv.label.LONG.WRAP)
screen_wordcard_btn_back_label.set_width(lv.pct(100))
screen_wordcard_btn_back_label.align(lv.ALIGN.CENTER, 0, 0)
screen_wordcard_btn_back.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_wordcard_btn_back.set_pos(5, 5)
screen_wordcard_btn_back.set_size(15, 15)
# Set style for screen_wordcard_btn_back, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordcard_btn_back.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_back.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_back.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_back.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_back.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_back.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_back.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_back.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_wordcard_btn_back, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_wordcard_btn_back.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_back.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_back.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_back.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_back.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_back.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_back.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_back.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_back.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_back.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_back.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_back.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_wordcard_btn_left
screen_wordcard_btn_left = lv.btn(screen_wordcard)
screen_wordcard_btn_left_label = lv.label(screen_wordcard_btn_left)
screen_wordcard_btn_left_label.set_text("")
screen_wordcard_btn_left_label.set_long_mode(lv.label.LONG.WRAP)
screen_wordcard_btn_left_label.set_width(lv.pct(100))
screen_wordcard_btn_left_label.align(lv.ALIGN.CENTER, 0, 0)
screen_wordcard_btn_left.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_wordcard_btn_left.set_pos(5, 79)
screen_wordcard_btn_left.set_size(20, 20)
# Set style for screen_wordcard_btn_left, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordcard_btn_left.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_left.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_left.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_left.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_left.set_style_bg_img_src("B:MicroPython/_leftarrow_20x20.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_left.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_left.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_left.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_left.set_style_text_font(test_font("Acme_Regular", 22), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_left.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_left.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_wordcard_btn_left, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_wordcard_btn_left.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_left.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_left.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_left.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_left.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_left.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_left.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_left.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_left.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_left.set_style_bg_img_src("B:MicroPython/_leftarrow_20x20.bin", lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_left.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_left.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_left.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_left.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_left.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_wordcard_label_index
screen_wordcard_label_index = lv.label(screen_wordcard)
screen_wordcard_label_index.set_text("501/2000")
screen_wordcard_label_index.set_long_mode(lv.label.LONG.WRAP)
screen_wordcard_label_index.set_width(lv.pct(100))
screen_wordcard_label_index.set_pos(219, 10)
screen_wordcard_label_index.set_size(68, 11)
# Set style for screen_wordcard_label_index, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordcard_label_index.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_index.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_index.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_index.set_style_text_font(test_font("montserratMedium", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_index.set_style_text_opa(207, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_index.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_index.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_index.set_style_text_align(lv.TEXT_ALIGN.RIGHT, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_index.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_index.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_index.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_index.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_index.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_index.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wordcard_btn_right
screen_wordcard_btn_right = lv.btn(screen_wordcard)
screen_wordcard_btn_right_label = lv.label(screen_wordcard_btn_right)
screen_wordcard_btn_right_label.set_text("")
screen_wordcard_btn_right_label.set_long_mode(lv.label.LONG.WRAP)
screen_wordcard_btn_right_label.set_width(lv.pct(100))
screen_wordcard_btn_right_label.align(lv.ALIGN.CENTER, 0, 0)
screen_wordcard_btn_right.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_wordcard_btn_right.set_pos(296, 78)
screen_wordcard_btn_right.set_size(18, 18)
# Set style for screen_wordcard_btn_right, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordcard_btn_right.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_right.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_right.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_right.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_right.set_style_bg_img_src("B:MicroPython/_rightarrow_18x18.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_right.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_right.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_right.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_right.set_style_text_font(test_font("Acme_Regular", 22), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_right.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_right.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_wordcard_btn_right, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_wordcard_btn_right.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_right.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_right.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_right.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_right.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_right.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_right.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_right.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_right.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_right.set_style_bg_img_src("B:MicroPython/_rightarrow_18x18.bin", lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_right.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_right.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_right.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_right.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_right.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_wordcard_label_spelling
screen_wordcard_label_spelling = lv.label(screen_wordcard)
screen_wordcard_label_spelling.set_text("Abondon")
screen_wordcard_label_spelling.set_long_mode(lv.label.LONG.SCROLL)
screen_wordcard_label_spelling.set_width(lv.pct(100))
screen_wordcard_label_spelling.set_pos(32, 20)
screen_wordcard_label_spelling.set_size(257, 43)
# Set style for screen_wordcard_label_spelling, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordcard_label_spelling.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_spelling.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_spelling.set_style_text_color(lv.color_hex(0xefcbd1), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_spelling.set_style_text_font(test_font("Acme_Regular", 30), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_spelling.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_spelling.set_style_text_letter_space(2, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_spelling.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_spelling.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_spelling.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_spelling.set_style_pad_top(8, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_spelling.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_spelling.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_spelling.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_spelling.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wordcard_label_phonetic
screen_wordcard_label_phonetic = lv.label(screen_wordcard)
screen_wordcard_label_phonetic.set_text("[ə'bændən]")
screen_wordcard_label_phonetic.set_long_mode(lv.label.LONG.WRAP)
screen_wordcard_label_phonetic.set_width(lv.pct(100))
screen_wordcard_label_phonetic.set_pos(32, 66)
screen_wordcard_label_phonetic.set_size(255, 16)
# Set style for screen_wordcard_label_phonetic, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordcard_label_phonetic.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_phonetic.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_phonetic.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_phonetic.set_style_text_font(test_font("arial", 14), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_phonetic.set_style_text_opa(143, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_phonetic.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_phonetic.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_phonetic.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_phonetic.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_phonetic.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_phonetic.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_phonetic.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_phonetic.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_phonetic.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wordcard_label_meaning
screen_wordcard_label_meaning = lv.label(screen_wordcard)
screen_wordcard_label_meaning.set_text("v.放弃;抛弃;放纵")
screen_wordcard_label_meaning.set_long_mode(lv.label.LONG.WRAP)
screen_wordcard_label_meaning.set_width(lv.pct(100))
screen_wordcard_label_meaning.set_pos(31, 92)
screen_wordcard_label_meaning.set_size(257, 15)
# Set style for screen_wordcard_label_meaning, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordcard_label_meaning.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_meaning.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_meaning.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_meaning.set_style_text_font(test_font("AdobeFangsongStdRegular", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_meaning.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_meaning.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_meaning.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_meaning.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_meaning.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_meaning.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_meaning.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_meaning.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_meaning.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_meaning.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wordcard_img_cuo
screen_wordcard_img_cuo = lv.img(screen_wordcard)
screen_wordcard_img_cuo.set_src("B:MicroPython/_cuo_1_alpha_20x20.bin")
screen_wordcard_img_cuo.add_flag(lv.obj.FLAG.CLICKABLE)
screen_wordcard_img_cuo.set_pivot(50,50)
screen_wordcard_img_cuo.set_angle(0)
screen_wordcard_img_cuo.set_pos(188, 119)
screen_wordcard_img_cuo.set_size(20, 20)
# Set style for screen_wordcard_img_cuo, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordcard_img_cuo.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_img_cuo.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_img_cuo.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wordcard_img_dui
screen_wordcard_img_dui = lv.img(screen_wordcard)
screen_wordcard_img_dui.set_src("B:MicroPython/_dui_1_alpha_20x20.bin")
screen_wordcard_img_dui.add_flag(lv.obj.FLAG.CLICKABLE)
screen_wordcard_img_dui.set_pivot(50,50)
screen_wordcard_img_dui.set_angle(0)
screen_wordcard_img_dui.set_pos(103, 119)
screen_wordcard_img_dui.set_size(20, 20)
# Set style for screen_wordcard_img_dui, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordcard_img_dui.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_img_dui.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_img_dui.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wordcard_label_gotit
screen_wordcard_label_gotit = lv.label(screen_wordcard)
screen_wordcard_label_gotit.set_text("Got it")
screen_wordcard_label_gotit.set_long_mode(lv.label.LONG.WRAP)
screen_wordcard_label_gotit.set_width(lv.pct(100))
screen_wordcard_label_gotit.set_pos(93, 145)
screen_wordcard_label_gotit.set_size(40, 12)
# Set style for screen_wordcard_label_gotit, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordcard_label_gotit.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_gotit.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_gotit.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_gotit.set_style_text_font(test_font("montserratMedium", 10), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_gotit.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_gotit.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_gotit.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_gotit.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_gotit.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_gotit.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_gotit.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_gotit.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_gotit.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_gotit.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wordcard_label_review
screen_wordcard_label_review = lv.label(screen_wordcard)
screen_wordcard_label_review.set_text("Reivew")
screen_wordcard_label_review.set_long_mode(lv.label.LONG.WRAP)
screen_wordcard_label_review.set_width(lv.pct(100))
screen_wordcard_label_review.set_pos(171, 145)
screen_wordcard_label_review.set_size(53, 11)
# Set style for screen_wordcard_label_review, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordcard_label_review.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_review.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_review.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_review.set_style_text_font(test_font("montserratMedium", 10), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_review.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_review.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_review.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_review.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_review.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_review.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_review.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_review.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_review.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_label_review.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wordcard_btn_dui
screen_wordcard_btn_dui = lv.btn(screen_wordcard)
screen_wordcard_btn_dui_label = lv.label(screen_wordcard_btn_dui)
screen_wordcard_btn_dui_label.set_text("")
screen_wordcard_btn_dui_label.set_long_mode(lv.label.LONG.WRAP)
screen_wordcard_btn_dui_label.set_width(lv.pct(100))
screen_wordcard_btn_dui_label.align(lv.ALIGN.CENTER, 0, 0)
screen_wordcard_btn_dui.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_wordcard_btn_dui.set_pos(103, 119)
screen_wordcard_btn_dui.set_size(20, 20)
# Set style for screen_wordcard_btn_dui, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordcard_btn_dui.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_dui.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_dui.set_style_radius(20, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_dui.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_dui.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_dui.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_dui.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_dui.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_wordcard_btn_dui, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_wordcard_btn_dui.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_dui.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_dui.set_style_radius(20, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_dui.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_dui.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_dui.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_dui.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_dui.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_dui.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_dui.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_dui.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_dui.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Set style for screen_wordcard_btn_dui, Part: lv.PART.MAIN, State: lv.STATE.DISABLED.
screen_wordcard_btn_dui.set_style_bg_opa(131, lv.PART.MAIN|lv.STATE.DISABLED)
screen_wordcard_btn_dui.set_style_bg_color(lv.color_hex(0x555555), lv.PART.MAIN|lv.STATE.DISABLED)
screen_wordcard_btn_dui.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.DISABLED)
screen_wordcard_btn_dui.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DISABLED)
screen_wordcard_btn_dui.set_style_radius(20, lv.PART.MAIN|lv.STATE.DISABLED)
screen_wordcard_btn_dui.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DISABLED)
screen_wordcard_btn_dui.set_style_text_color(lv.color_hex(0x000000), lv.PART.MAIN|lv.STATE.DISABLED)
screen_wordcard_btn_dui.set_style_text_font(test_font("montserratMedium", 12), lv.PART.MAIN|lv.STATE.DISABLED)
screen_wordcard_btn_dui.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DISABLED)

# Create screen_wordcard_btn_cuo
screen_wordcard_btn_cuo = lv.btn(screen_wordcard)
screen_wordcard_btn_cuo_label = lv.label(screen_wordcard_btn_cuo)
screen_wordcard_btn_cuo_label.set_text("")
screen_wordcard_btn_cuo_label.set_long_mode(lv.label.LONG.WRAP)
screen_wordcard_btn_cuo_label.set_width(lv.pct(100))
screen_wordcard_btn_cuo_label.align(lv.ALIGN.CENTER, 0, 0)
screen_wordcard_btn_cuo.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_wordcard_btn_cuo.set_pos(188, 119)
screen_wordcard_btn_cuo.set_size(20, 20)
# Set style for screen_wordcard_btn_cuo, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordcard_btn_cuo.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_cuo.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_cuo.set_style_radius(20, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_cuo.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_cuo.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_cuo.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_cuo.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_cuo.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_wordcard_btn_cuo, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_wordcard_btn_cuo.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_cuo.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_cuo.set_style_radius(20, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_cuo.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_cuo.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_cuo.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_cuo.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_cuo.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_cuo.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_cuo.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_cuo.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_cuo.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Set style for screen_wordcard_btn_cuo, Part: lv.PART.MAIN, State: lv.STATE.DISABLED.
screen_wordcard_btn_cuo.set_style_bg_opa(128, lv.PART.MAIN|lv.STATE.DISABLED)
screen_wordcard_btn_cuo.set_style_bg_color(lv.color_hex(0x555555), lv.PART.MAIN|lv.STATE.DISABLED)
screen_wordcard_btn_cuo.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.DISABLED)
screen_wordcard_btn_cuo.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DISABLED)
screen_wordcard_btn_cuo.set_style_radius(20, lv.PART.MAIN|lv.STATE.DISABLED)
screen_wordcard_btn_cuo.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DISABLED)
screen_wordcard_btn_cuo.set_style_text_color(lv.color_hex(0x000000), lv.PART.MAIN|lv.STATE.DISABLED)
screen_wordcard_btn_cuo.set_style_text_font(test_font("montserratMedium", 12), lv.PART.MAIN|lv.STATE.DISABLED)
screen_wordcard_btn_cuo.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DISABLED)

# Create screen_wordcard_btn_home
screen_wordcard_btn_home = lv.btn(screen_wordcard)
screen_wordcard_btn_home_label = lv.label(screen_wordcard_btn_home)
screen_wordcard_btn_home_label.set_text("")
screen_wordcard_btn_home_label.set_long_mode(lv.label.LONG.WRAP)
screen_wordcard_btn_home_label.set_width(lv.pct(100))
screen_wordcard_btn_home_label.align(lv.ALIGN.CENTER, 0, 0)
screen_wordcard_btn_home.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_wordcard_btn_home.set_pos(300, 5)
screen_wordcard_btn_home.set_size(15, 15)
# Set style for screen_wordcard_btn_home, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wordcard_btn_home.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_home.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_home.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_home.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_home.set_style_bg_img_src("B:MicroPython/_home_15x15.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_home.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_home.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_home.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_home.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_home.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wordcard_btn_home.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_wordcard_btn_home, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_wordcard_btn_home.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_home.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_home.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_home.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_home.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_home.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_home.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_home.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_home.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_home.set_style_bg_img_src("B:MicroPython/_home_15x15.bin", lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_home.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_home.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_home.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_home.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wordcard_btn_home.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

screen_wordcard.update_layout()
# Create screen_reviewcard
screen_reviewcard = lv.obj()
g_kb_screen_reviewcard = lv.keyboard(screen_reviewcard)
g_kb_screen_reviewcard.add_event_cb(lambda e: ta_event_cb(e, g_kb_screen_reviewcard), lv.EVENT.ALL, None)
g_kb_screen_reviewcard.add_flag(lv.obj.FLAG.HIDDEN)
g_kb_screen_reviewcard.set_style_text_font(test_font("Acme_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard.set_size(320, 170)
screen_reviewcard.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
# Set style for screen_reviewcard, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_reviewcard.set_style_bg_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard.set_style_bg_color(lv.color_hex(0x000000), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard.set_style_bg_img_src("B:MicroPython/_screen_reviewcard_bg_320x170.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard.set_style_bg_img_opa(137, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_reviewcard_img_wordrect
screen_reviewcard_img_wordrect = lv.img(screen_reviewcard)
screen_reviewcard_img_wordrect.set_src("B:MicroPython/_word_rectangle_alpha_264x136.bin")
screen_reviewcard_img_wordrect.add_flag(lv.obj.FLAG.CLICKABLE)
screen_reviewcard_img_wordrect.set_pivot(50,50)
screen_reviewcard_img_wordrect.set_angle(0)
screen_reviewcard_img_wordrect.set_pos(28, 25)
screen_reviewcard_img_wordrect.set_size(264, 136)
# Set style for screen_reviewcard_img_wordrect, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_reviewcard_img_wordrect.set_style_img_opa(152, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_img_wordrect.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_img_wordrect.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_reviewcard_btn_back
screen_reviewcard_btn_back = lv.btn(screen_reviewcard)
screen_reviewcard_btn_back_label = lv.label(screen_reviewcard_btn_back)
screen_reviewcard_btn_back_label.set_text("<")
screen_reviewcard_btn_back_label.set_long_mode(lv.label.LONG.WRAP)
screen_reviewcard_btn_back_label.set_width(lv.pct(100))
screen_reviewcard_btn_back_label.align(lv.ALIGN.CENTER, 0, 0)
screen_reviewcard_btn_back.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_reviewcard_btn_back.set_pos(5, 5)
screen_reviewcard_btn_back.set_size(15, 15)
# Set style for screen_reviewcard_btn_back, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_reviewcard_btn_back.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_back.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_back.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_back.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_back.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_back.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_back.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_back.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_reviewcard_btn_back, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_reviewcard_btn_back.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_back.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_back.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_back.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_back.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_back.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_back.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_back.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_back.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_back.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_back.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_back.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_reviewcard_btn_left
screen_reviewcard_btn_left = lv.btn(screen_reviewcard)
screen_reviewcard_btn_left_label = lv.label(screen_reviewcard_btn_left)
screen_reviewcard_btn_left_label.set_text("")
screen_reviewcard_btn_left_label.set_long_mode(lv.label.LONG.WRAP)
screen_reviewcard_btn_left_label.set_width(lv.pct(100))
screen_reviewcard_btn_left_label.align(lv.ALIGN.CENTER, 0, 0)
screen_reviewcard_btn_left.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_reviewcard_btn_left.set_pos(5, 79)
screen_reviewcard_btn_left.set_size(20, 20)
# Set style for screen_reviewcard_btn_left, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_reviewcard_btn_left.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_left.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_left.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_left.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_left.set_style_bg_img_src("B:MicroPython/_leftarrow_20x20.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_left.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_left.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_left.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_left.set_style_text_font(test_font("Acme_Regular", 22), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_left.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_left.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_reviewcard_btn_left, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_reviewcard_btn_left.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_left.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_left.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_left.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_left.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_left.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_left.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_left.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_left.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_left.set_style_bg_img_src("B:MicroPython/_leftarrow_20x20.bin", lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_left.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_left.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_left.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_left.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_left.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_reviewcard_label_index
screen_reviewcard_label_index = lv.label(screen_reviewcard)
screen_reviewcard_label_index.set_text("0/200")
screen_reviewcard_label_index.set_long_mode(lv.label.LONG.WRAP)
screen_reviewcard_label_index.set_width(lv.pct(100))
screen_reviewcard_label_index.set_pos(219, 10)
screen_reviewcard_label_index.set_size(68, 11)
# Set style for screen_reviewcard_label_index, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_reviewcard_label_index.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_index.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_index.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_index.set_style_text_font(test_font("montserratMedium", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_index.set_style_text_opa(207, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_index.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_index.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_index.set_style_text_align(lv.TEXT_ALIGN.RIGHT, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_index.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_index.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_index.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_index.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_index.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_index.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_reviewcard_btn_right
screen_reviewcard_btn_right = lv.btn(screen_reviewcard)
screen_reviewcard_btn_right_label = lv.label(screen_reviewcard_btn_right)
screen_reviewcard_btn_right_label.set_text("")
screen_reviewcard_btn_right_label.set_long_mode(lv.label.LONG.WRAP)
screen_reviewcard_btn_right_label.set_width(lv.pct(100))
screen_reviewcard_btn_right_label.align(lv.ALIGN.CENTER, 0, 0)
screen_reviewcard_btn_right.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_reviewcard_btn_right.set_pos(296, 78)
screen_reviewcard_btn_right.set_size(18, 18)
# Set style for screen_reviewcard_btn_right, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_reviewcard_btn_right.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_right.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_right.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_right.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_right.set_style_bg_img_src("B:MicroPython/_rightarrow_18x18.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_right.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_right.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_right.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_right.set_style_text_font(test_font("Acme_Regular", 22), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_right.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_right.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_reviewcard_btn_right, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_reviewcard_btn_right.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_right.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_right.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_right.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_right.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_right.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_right.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_right.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_right.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_right.set_style_bg_img_src("B:MicroPython/_rightarrow_18x18.bin", lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_right.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_right.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_right.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_right.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_right.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_reviewcard_label_spelling
screen_reviewcard_label_spelling = lv.label(screen_reviewcard)
screen_reviewcard_label_spelling.set_text("Acquire")
screen_reviewcard_label_spelling.set_long_mode(lv.label.LONG.SCROLL_CIRCULAR)
screen_reviewcard_label_spelling.set_width(lv.pct(100))
screen_reviewcard_label_spelling.set_pos(32, 28)
screen_reviewcard_label_spelling.set_size(256, 41)
# Set style for screen_reviewcard_label_spelling, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_reviewcard_label_spelling.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_spelling.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_spelling.set_style_text_color(lv.color_hex(0xefcbd1), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_spelling.set_style_text_font(test_font("Acme_Regular", 30), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_spelling.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_spelling.set_style_text_letter_space(2, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_spelling.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_spelling.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_spelling.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_spelling.set_style_pad_top(8, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_spelling.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_spelling.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_spelling.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_spelling.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_reviewcard_label_phonetic
screen_reviewcard_label_phonetic = lv.label(screen_reviewcard)
screen_reviewcard_label_phonetic.set_text("[ə'kwfaɪr]")
screen_reviewcard_label_phonetic.set_long_mode(lv.label.LONG.CLIP)
screen_reviewcard_label_phonetic.set_width(lv.pct(100))
screen_reviewcard_label_phonetic.set_pos(32, 69)
screen_reviewcard_label_phonetic.set_size(255, 16)
# Set style for screen_reviewcard_label_phonetic, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_reviewcard_label_phonetic.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_phonetic.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_phonetic.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_phonetic.set_style_text_font(test_font("arial", 14), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_phonetic.set_style_text_opa(143, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_phonetic.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_phonetic.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_phonetic.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_phonetic.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_phonetic.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_phonetic.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_phonetic.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_phonetic.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_phonetic.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_reviewcard_label_meaning
screen_reviewcard_label_meaning = lv.label(screen_reviewcard)
screen_reviewcard_label_meaning.set_text("v.获得;学到")
screen_reviewcard_label_meaning.set_long_mode(lv.label.LONG.CLIP)
screen_reviewcard_label_meaning.set_width(lv.pct(100))
screen_reviewcard_label_meaning.set_pos(32, 91)
screen_reviewcard_label_meaning.set_size(255, 18)
# Set style for screen_reviewcard_label_meaning, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_reviewcard_label_meaning.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_meaning.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_meaning.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_meaning.set_style_text_font(test_font("AdobeFangsongStdRegular", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_meaning.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_meaning.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_meaning.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_meaning.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_meaning.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_meaning.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_meaning.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_meaning.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_meaning.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_meaning.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_reviewcard_img_dui
screen_reviewcard_img_dui = lv.img(screen_reviewcard)
screen_reviewcard_img_dui.set_src("B:MicroPython/_dui_1_alpha_20x20.bin")
screen_reviewcard_img_dui.add_flag(lv.obj.FLAG.CLICKABLE)
screen_reviewcard_img_dui.set_pivot(50,50)
screen_reviewcard_img_dui.set_angle(0)
screen_reviewcard_img_dui.set_pos(103, 119)
screen_reviewcard_img_dui.set_size(20, 20)
# Set style for screen_reviewcard_img_dui, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_reviewcard_img_dui.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_img_dui.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_img_dui.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_reviewcard_label_gotit
screen_reviewcard_label_gotit = lv.label(screen_reviewcard)
screen_reviewcard_label_gotit.set_text("Got it")
screen_reviewcard_label_gotit.set_long_mode(lv.label.LONG.WRAP)
screen_reviewcard_label_gotit.set_width(lv.pct(100))
screen_reviewcard_label_gotit.set_pos(92, 145)
screen_reviewcard_label_gotit.set_size(40, 12)
# Set style for screen_reviewcard_label_gotit, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_reviewcard_label_gotit.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_gotit.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_gotit.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_gotit.set_style_text_font(test_font("montserratMedium", 10), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_gotit.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_gotit.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_gotit.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_gotit.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_gotit.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_gotit.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_gotit.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_gotit.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_gotit.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_gotit.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_reviewcard_btn_dui
screen_reviewcard_btn_dui = lv.btn(screen_reviewcard)
screen_reviewcard_btn_dui_label = lv.label(screen_reviewcard_btn_dui)
screen_reviewcard_btn_dui_label.set_text("")
screen_reviewcard_btn_dui_label.set_long_mode(lv.label.LONG.WRAP)
screen_reviewcard_btn_dui_label.set_width(lv.pct(100))
screen_reviewcard_btn_dui_label.align(lv.ALIGN.CENTER, 0, 0)
screen_reviewcard_btn_dui.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_reviewcard_btn_dui.set_pos(103, 119)
screen_reviewcard_btn_dui.set_size(20, 20)
# Set style for screen_reviewcard_btn_dui, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_reviewcard_btn_dui.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_dui.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_dui.set_style_radius(20, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_dui.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_dui.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_dui.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_dui.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_dui.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_reviewcard_btn_dui, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_reviewcard_btn_dui.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_dui.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_dui.set_style_radius(20, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_dui.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_dui.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_dui.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_dui.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_dui.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_dui.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_dui.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_dui.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_dui.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Set style for screen_reviewcard_btn_dui, Part: lv.PART.MAIN, State: lv.STATE.DISABLED.
screen_reviewcard_btn_dui.set_style_bg_opa(169, lv.PART.MAIN|lv.STATE.DISABLED)
screen_reviewcard_btn_dui.set_style_bg_color(lv.color_hex(0x7b7b7b), lv.PART.MAIN|lv.STATE.DISABLED)
screen_reviewcard_btn_dui.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.DISABLED)
screen_reviewcard_btn_dui.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DISABLED)
screen_reviewcard_btn_dui.set_style_radius(20, lv.PART.MAIN|lv.STATE.DISABLED)
screen_reviewcard_btn_dui.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DISABLED)
screen_reviewcard_btn_dui.set_style_text_color(lv.color_hex(0x000000), lv.PART.MAIN|lv.STATE.DISABLED)
screen_reviewcard_btn_dui.set_style_text_font(test_font("montserratMedium", 12), lv.PART.MAIN|lv.STATE.DISABLED)
screen_reviewcard_btn_dui.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DISABLED)

# Create screen_reviewcard_btn_home
screen_reviewcard_btn_home = lv.btn(screen_reviewcard)
screen_reviewcard_btn_home_label = lv.label(screen_reviewcard_btn_home)
screen_reviewcard_btn_home_label.set_text("")
screen_reviewcard_btn_home_label.set_long_mode(lv.label.LONG.WRAP)
screen_reviewcard_btn_home_label.set_width(lv.pct(100))
screen_reviewcard_btn_home_label.align(lv.ALIGN.CENTER, 0, 0)
screen_reviewcard_btn_home.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_reviewcard_btn_home.set_pos(300, 5)
screen_reviewcard_btn_home.set_size(15, 15)
# Set style for screen_reviewcard_btn_home, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_reviewcard_btn_home.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_home.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_home.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_home.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_home.set_style_bg_img_src("B:MicroPython/_home_15x15.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_home.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_home.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_home.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_home.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_home.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_home.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_reviewcard_btn_home, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_reviewcard_btn_home.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_home.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_home.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_home.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_home.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_home.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_home.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_home.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_home.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_home.set_style_bg_img_src("B:MicroPython/_home_15x15.bin", lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_home.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_home.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_home.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_home.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_home.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_reviewcard_label_review
screen_reviewcard_label_review = lv.label(screen_reviewcard)
screen_reviewcard_label_review.set_text("Reivew")
screen_reviewcard_label_review.set_long_mode(lv.label.LONG.WRAP)
screen_reviewcard_label_review.set_width(lv.pct(100))
screen_reviewcard_label_review.set_pos(171, 145)
screen_reviewcard_label_review.set_size(53, 11)
# Set style for screen_reviewcard_label_review, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_reviewcard_label_review.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_review.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_review.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_review.set_style_text_font(test_font("montserratMedium", 10), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_review.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_review.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_review.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_review.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_review.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_review.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_review.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_review.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_review.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_label_review.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_reviewcard_img_cuo
screen_reviewcard_img_cuo = lv.img(screen_reviewcard)
screen_reviewcard_img_cuo.set_src("B:MicroPython/_cuo_1_alpha_20x20.bin")
screen_reviewcard_img_cuo.add_flag(lv.obj.FLAG.CLICKABLE)
screen_reviewcard_img_cuo.set_pivot(50,50)
screen_reviewcard_img_cuo.set_angle(0)
screen_reviewcard_img_cuo.set_pos(188, 119)
screen_reviewcard_img_cuo.set_size(20, 20)
# Set style for screen_reviewcard_img_cuo, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_reviewcard_img_cuo.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_img_cuo.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_img_cuo.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_reviewcard_btn_cuo
screen_reviewcard_btn_cuo = lv.btn(screen_reviewcard)
screen_reviewcard_btn_cuo_label = lv.label(screen_reviewcard_btn_cuo)
screen_reviewcard_btn_cuo_label.set_text("")
screen_reviewcard_btn_cuo_label.set_long_mode(lv.label.LONG.WRAP)
screen_reviewcard_btn_cuo_label.set_width(lv.pct(100))
screen_reviewcard_btn_cuo_label.align(lv.ALIGN.CENTER, 0, 0)
screen_reviewcard_btn_cuo.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_reviewcard_btn_cuo.set_pos(188, 119)
screen_reviewcard_btn_cuo.set_size(20, 20)
# Set style for screen_reviewcard_btn_cuo, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_reviewcard_btn_cuo.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_cuo.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_cuo.set_style_radius(20, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_cuo.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_cuo.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_cuo.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_cuo.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_reviewcard_btn_cuo.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_reviewcard_btn_cuo, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_reviewcard_btn_cuo.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_cuo.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_cuo.set_style_radius(20, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_cuo.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_cuo.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_cuo.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_cuo.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_cuo.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_cuo.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_cuo.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_cuo.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_reviewcard_btn_cuo.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Set style for screen_reviewcard_btn_cuo, Part: lv.PART.MAIN, State: lv.STATE.DISABLED.
screen_reviewcard_btn_cuo.set_style_bg_opa(172, lv.PART.MAIN|lv.STATE.DISABLED)
screen_reviewcard_btn_cuo.set_style_bg_color(lv.color_hex(0x555555), lv.PART.MAIN|lv.STATE.DISABLED)
screen_reviewcard_btn_cuo.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.DISABLED)
screen_reviewcard_btn_cuo.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DISABLED)
screen_reviewcard_btn_cuo.set_style_radius(20, lv.PART.MAIN|lv.STATE.DISABLED)
screen_reviewcard_btn_cuo.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DISABLED)
screen_reviewcard_btn_cuo.set_style_text_color(lv.color_hex(0x000000), lv.PART.MAIN|lv.STATE.DISABLED)
screen_reviewcard_btn_cuo.set_style_text_font(test_font("montserratMedium", 12), lv.PART.MAIN|lv.STATE.DISABLED)
screen_reviewcard_btn_cuo.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DISABLED)

screen_reviewcard.update_layout()
# Create screen_setting
screen_setting = lv.obj()
g_kb_screen_setting = lv.keyboard(screen_setting)
g_kb_screen_setting.add_event_cb(lambda e: ta_event_cb(e, g_kb_screen_setting), lv.EVENT.ALL, None)
g_kb_screen_setting.add_flag(lv.obj.FLAG.HIDDEN)
g_kb_screen_setting.set_style_text_font(test_font("Acme_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting.set_size(320, 170)
screen_setting.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
# Set style for screen_setting, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_setting.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting.set_style_bg_img_src("B:MicroPython/_screen_setting_bg2_320x170.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting.set_style_bg_img_recolor(lv.color_hex(0x7987a6), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting.set_style_bg_img_recolor_opa(21, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_setting_cont_menu
screen_setting_cont_menu = lv.obj(screen_setting)
screen_setting_cont_menu.set_pos(0, 0)
screen_setting_cont_menu.set_size(320, 170)
screen_setting_cont_menu.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
# Set style for screen_setting_cont_menu, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_setting_cont_menu.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_cont_menu.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_cont_menu.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_cont_menu.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_cont_menu.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_cont_menu.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_cont_menu.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_cont_menu.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
# Create screen_setting_btn_wifi
screen_setting_btn_wifi = lv.btn(screen_setting_cont_menu)
screen_setting_btn_wifi_label = lv.label(screen_setting_btn_wifi)
screen_setting_btn_wifi_label.set_text("")
screen_setting_btn_wifi_label.set_long_mode(lv.label.LONG.WRAP)
screen_setting_btn_wifi_label.set_width(lv.pct(100))
screen_setting_btn_wifi_label.align(lv.ALIGN.CENTER, 0, 0)
screen_setting_btn_wifi.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_setting_btn_wifi.set_pos(80, 43)
screen_setting_btn_wifi.set_size(65, 65)
# Set style for screen_setting_btn_wifi, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_setting_btn_wifi.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_wifi.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_wifi.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_wifi.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_wifi.set_style_bg_img_src("B:MicroPython/_wifi_icon_65x65.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_wifi.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_wifi.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_wifi.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_wifi.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_wifi.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_wifi.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_setting_btn_wifi, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_setting_btn_wifi.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_wifi.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_wifi.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_wifi.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_wifi.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_wifi.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_wifi.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_wifi.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_wifi.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_wifi.set_style_bg_img_src("B:MicroPython/_wifi_icon_65x65.bin", lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_wifi.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_wifi.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_wifi.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_wifi.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_wifi.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
# Set style for screen_setting_btn_wifi, Part: lv.PART.MAIN, State: lv.STATE.PRESSED.
screen_setting_btn_wifi.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.PRESSED)
screen_setting_btn_wifi.set_style_border_width(0, lv.PART.MAIN|lv.STATE.PRESSED)
screen_setting_btn_wifi.set_style_radius(5, lv.PART.MAIN|lv.STATE.PRESSED)
screen_setting_btn_wifi.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.PRESSED)
screen_setting_btn_wifi.set_style_bg_img_src("B:MicroPython/_wifi_icon_65x65.bin", lv.PART.MAIN|lv.STATE.PRESSED)
screen_setting_btn_wifi.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.PRESSED)
screen_setting_btn_wifi.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.PRESSED)
screen_setting_btn_wifi.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.PRESSED)
screen_setting_btn_wifi.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.PRESSED)
screen_setting_btn_wifi.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.PRESSED)

# Create screen_setting_btn_vocab
screen_setting_btn_vocab = lv.btn(screen_setting_cont_menu)
screen_setting_btn_vocab_label = lv.label(screen_setting_btn_vocab)
screen_setting_btn_vocab_label.set_text("")
screen_setting_btn_vocab_label.set_long_mode(lv.label.LONG.WRAP)
screen_setting_btn_vocab_label.set_width(lv.pct(100))
screen_setting_btn_vocab_label.align(lv.ALIGN.CENTER, 0, 0)
screen_setting_btn_vocab.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_setting_btn_vocab.set_pos(172, 42)
screen_setting_btn_vocab.set_size(65, 65)
# Set style for screen_setting_btn_vocab, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_setting_btn_vocab.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_vocab.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_vocab.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_vocab.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_vocab.set_style_bg_img_src("B:MicroPython/_vocab_icon_65x65.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_vocab.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_vocab.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_vocab.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_vocab.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_vocab.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_vocab.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_setting_btn_vocab, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_setting_btn_vocab.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_vocab.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_vocab.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_vocab.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_vocab.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_vocab.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_vocab.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_vocab.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_vocab.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_vocab.set_style_bg_img_src("B:MicroPython/_vocab_icon_65x65.bin", lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_vocab.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_vocab.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_vocab.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_vocab.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_vocab.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_setting_btn_laba
screen_setting_btn_laba = lv.btn(screen_setting_cont_menu)
screen_setting_btn_laba_label = lv.label(screen_setting_btn_laba)
screen_setting_btn_laba_label.set_text("")
screen_setting_btn_laba_label.set_long_mode(lv.label.LONG.WRAP)
screen_setting_btn_laba_label.set_width(lv.pct(100))
screen_setting_btn_laba_label.align(lv.ALIGN.CENTER, 0, 0)
screen_setting_btn_laba.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_setting_btn_laba.set_pos(111, 44)
screen_setting_btn_laba.set_size(65, 65)
# Set style for screen_setting_btn_laba, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_setting_btn_laba.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_laba.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_laba.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_laba.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_laba.set_style_bg_img_src("B:MicroPython/_laba_icon_65x65.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_laba.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_laba.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_laba.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_laba.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_laba.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_laba.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_setting_btn_laba, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_setting_btn_laba.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_laba.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_laba.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_laba.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_laba.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_laba.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_laba.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_laba.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_laba.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_laba.set_style_bg_img_src("B:MicroPython/_laba_icon_65x65.bin", lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_laba.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_laba.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_laba.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_laba.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_laba.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_setting_btn_timer
screen_setting_btn_timer = lv.btn(screen_setting_cont_menu)
screen_setting_btn_timer_label = lv.label(screen_setting_btn_timer)
screen_setting_btn_timer_label.set_text("")
screen_setting_btn_timer_label.set_long_mode(lv.label.LONG.WRAP)
screen_setting_btn_timer_label.set_width(lv.pct(100))
screen_setting_btn_timer_label.align(lv.ALIGN.CENTER, 0, 0)
screen_setting_btn_timer.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_setting_btn_timer.set_pos(197, 41)
screen_setting_btn_timer.set_size(65, 65)
# Set style for screen_setting_btn_timer, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_setting_btn_timer.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_timer.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_timer.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_timer.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_timer.set_style_bg_img_src("B:MicroPython/_timer_icon_65x65.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_timer.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_timer.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_timer.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_timer.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_timer.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_timer.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_setting_btn_timer, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_setting_btn_timer.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_timer.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_timer.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_timer.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_timer.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_timer.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_timer.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_timer.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_timer.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_timer.set_style_bg_img_src("B:MicroPython/_timer_icon_65x65.bin", lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_timer.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_timer.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_timer.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_timer.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_timer.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_setting_btn_ble
screen_setting_btn_ble = lv.btn(screen_setting_cont_menu)
screen_setting_btn_ble_label = lv.label(screen_setting_btn_ble)
screen_setting_btn_ble_label.set_text("")
screen_setting_btn_ble_label.set_long_mode(lv.label.LONG.WRAP)
screen_setting_btn_ble_label.set_width(lv.pct(100))
screen_setting_btn_ble_label.align(lv.ALIGN.CENTER, 0, 0)
screen_setting_btn_ble.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_setting_btn_ble.set_pos(41, 44)
screen_setting_btn_ble.set_size(65, 65)
# Set style for screen_setting_btn_ble, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_setting_btn_ble.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_ble.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_ble.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_ble.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_ble.set_style_bg_img_src("B:MicroPython/_ble_icon_65x65.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_ble.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_ble.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_ble.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_ble.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_ble.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_ble.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_setting_btn_ble, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_setting_btn_ble.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_ble.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_ble.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_ble.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_ble.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_ble.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_ble.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_ble.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_ble.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_ble.set_style_bg_img_src("B:MicroPython/_ble_icon_65x65.bin", lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_ble.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_ble.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_ble.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_ble.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_ble.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_setting_btn_general
screen_setting_btn_general = lv.btn(screen_setting_cont_menu)
screen_setting_btn_general_label = lv.label(screen_setting_btn_general)
screen_setting_btn_general_label.set_text("")
screen_setting_btn_general_label.set_long_mode(lv.label.LONG.WRAP)
screen_setting_btn_general_label.set_width(lv.pct(100))
screen_setting_btn_general_label.align(lv.ALIGN.CENTER, 0, 0)
screen_setting_btn_general.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_setting_btn_general.set_pos(9, 43)
screen_setting_btn_general.set_size(65, 65)
# Set style for screen_setting_btn_general, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_setting_btn_general.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_general.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_general.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_general.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_general.set_style_bg_img_src("B:MicroPython/_general_icon_65x65.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_general.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_general.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_general.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_general.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_general.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_general.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_setting_btn_general, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_setting_btn_general.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_general.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_general.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_general.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_general.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_general.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_general.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_general.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_general.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_general.set_style_bg_img_src("B:MicroPython/_general_icon_65x65.bin", lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_general.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_general.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_general.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_general.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_general.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_setting_btn_data
screen_setting_btn_data = lv.btn(screen_setting_cont_menu)
screen_setting_btn_data_label = lv.label(screen_setting_btn_data)
screen_setting_btn_data_label.set_text("")
screen_setting_btn_data_label.set_long_mode(lv.label.LONG.WRAP)
screen_setting_btn_data_label.set_width(lv.pct(100))
screen_setting_btn_data_label.align(lv.ALIGN.CENTER, 0, 0)
screen_setting_btn_data.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_setting_btn_data.set_pos(148, 43)
screen_setting_btn_data.set_size(65, 65)
# Set style for screen_setting_btn_data, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_setting_btn_data.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_data.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_data.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_data.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_data.set_style_bg_img_src("B:MicroPython/_data_icon_65x65.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_data.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_data.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_data.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_data.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_data.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_data.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_setting_btn_data, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_setting_btn_data.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_data.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_data.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_data.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_data.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_data.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_data.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_data.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_data.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_data.set_style_bg_img_src("B:MicroPython/_data_icon_65x65.bin", lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_data.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_data.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_data.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_data.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_data.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_setting_btn_todo
screen_setting_btn_todo = lv.btn(screen_setting_cont_menu)
screen_setting_btn_todo_label = lv.label(screen_setting_btn_todo)
screen_setting_btn_todo_label.set_text("")
screen_setting_btn_todo_label.set_long_mode(lv.label.LONG.WRAP)
screen_setting_btn_todo_label.set_width(lv.pct(100))
screen_setting_btn_todo_label.align(lv.ALIGN.CENTER, 0, 0)
screen_setting_btn_todo.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_setting_btn_todo.set_pos(239, 40)
screen_setting_btn_todo.set_size(65, 65)
# Set style for screen_setting_btn_todo, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_setting_btn_todo.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_todo.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_todo.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_todo.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_todo.set_style_bg_img_src("B:MicroPython/_todo_icon_65x65.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_todo.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_todo.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_todo.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_todo.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_todo.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_todo.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_setting_btn_todo, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_setting_btn_todo.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_todo.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_todo.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_todo.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_todo.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_todo.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_todo.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_todo.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_todo.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_todo.set_style_bg_img_src("B:MicroPython/_todo_icon_65x65.bin", lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_todo.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_todo.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_todo.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_todo.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_todo.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_setting_label_settings
screen_setting_label_settings = lv.label(screen_setting)
screen_setting_label_settings.set_text("Settings")
screen_setting_label_settings.set_long_mode(lv.label.LONG.WRAP)
screen_setting_label_settings.set_width(lv.pct(100))
screen_setting_label_settings.set_pos(78, 8)
screen_setting_label_settings.set_size(169, 19)
# Set style for screen_setting_label_settings, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_setting_label_settings.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_label_settings.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_label_settings.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_label_settings.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_label_settings.set_style_text_opa(149, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_label_settings.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_label_settings.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_label_settings.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_label_settings.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_label_settings.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_label_settings.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_label_settings.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_label_settings.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_label_settings.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_setting_btn_back
screen_setting_btn_back = lv.btn(screen_setting)
screen_setting_btn_back_label = lv.label(screen_setting_btn_back)
screen_setting_btn_back_label.set_text("<")
screen_setting_btn_back_label.set_long_mode(lv.label.LONG.WRAP)
screen_setting_btn_back_label.set_width(lv.pct(100))
screen_setting_btn_back_label.align(lv.ALIGN.CENTER, 0, 0)
screen_setting_btn_back.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_setting_btn_back.set_pos(7, 7)
screen_setting_btn_back.set_size(20, 20)
# Set style for screen_setting_btn_back, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_setting_btn_back.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_back.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_back.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_back.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_back.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_back.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_back.set_style_text_opa(192, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_btn_back.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_setting_btn_back, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_setting_btn_back.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_back.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_back.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_back.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_back.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_back.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_back.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_back.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_back.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_back.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_back.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_setting_btn_back.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_setting_circular_down
screen_setting_circular_down = lv.img(screen_setting)
screen_setting_circular_down.set_src("B:MicroPython/_Subtract_alpha_220x25.bin")
screen_setting_circular_down.add_flag(lv.obj.FLAG.CLICKABLE)
screen_setting_circular_down.set_pivot(50,50)
screen_setting_circular_down.set_angle(0)
screen_setting_circular_down.set_pos(54, 133)
screen_setting_circular_down.set_size(220, 25)
# Set style for screen_setting_circular_down, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_setting_circular_down.set_style_img_recolor_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_circular_down.set_style_img_recolor(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_circular_down.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_circular_down.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_circular_down.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_setting_circular_up
screen_setting_circular_up = lv.img(screen_setting)
screen_setting_circular_up.set_src("B:MicroPython/_Subtract1_alpha_220x25.bin")
screen_setting_circular_up.add_flag(lv.obj.FLAG.CLICKABLE)
screen_setting_circular_up.set_pivot(50,50)
screen_setting_circular_up.set_angle(0)
screen_setting_circular_up.set_pos(54, 143)
screen_setting_circular_up.set_size(220, 25)
# Set style for screen_setting_circular_up, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_setting_circular_up.set_style_img_recolor_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_circular_up.set_style_img_recolor(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_circular_up.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_circular_up.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_circular_up.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_setting_img_point8
screen_setting_img_point8 = lv.img(screen_setting)
screen_setting_img_point8.set_src("B:MicroPython/_Ellipse_alpha_25x25.bin")
screen_setting_img_point8.add_flag(lv.obj.FLAG.CLICKABLE)
screen_setting_img_point8.set_pivot(50,50)
screen_setting_img_point8.set_angle(0)
screen_setting_img_point8.set_pos(91, 148)
screen_setting_img_point8.set_size(25, 25)
screen_setting_img_point8.add_flag(lv.obj.FLAG.HIDDEN)
# Set style for screen_setting_img_point8, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_setting_img_point8.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_img_point8.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_img_point8.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_setting_img_point3
screen_setting_img_point3 = lv.img(screen_setting)
screen_setting_img_point3.set_src("B:MicroPython/_Ellipse_alpha_25x25.bin")
screen_setting_img_point3.add_flag(lv.obj.FLAG.CLICKABLE)
screen_setting_img_point3.set_pivot(50,50)
screen_setting_img_point3.set_angle(0)
screen_setting_img_point3.set_pos(256, 140)
screen_setting_img_point3.set_size(25, 25)
screen_setting_img_point3.add_flag(lv.obj.FLAG.HIDDEN)
# Set style for screen_setting_img_point3, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_setting_img_point3.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_img_point3.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_img_point3.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_setting_img_point7
screen_setting_img_point7 = lv.img(screen_setting)
screen_setting_img_point7.set_src("B:MicroPython/_Ellipse_alpha_25x25.bin")
screen_setting_img_point7.add_flag(lv.obj.FLAG.CLICKABLE)
screen_setting_img_point7.set_pivot(50,50)
screen_setting_img_point7.set_angle(0)
screen_setting_img_point7.set_pos(47, 140)
screen_setting_img_point7.set_size(25, 25)
screen_setting_img_point7.add_flag(lv.obj.FLAG.HIDDEN)
# Set style for screen_setting_img_point7, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_setting_img_point7.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_img_point7.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_img_point7.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_setting_img_point1
screen_setting_img_point1 = lv.img(screen_setting)
screen_setting_img_point1.set_src("B:MicroPython/_Ellipse_alpha_25x25.bin")
screen_setting_img_point1.add_flag(lv.obj.FLAG.CLICKABLE)
screen_setting_img_point1.set_pivot(50,50)
screen_setting_img_point1.set_angle(0)
screen_setting_img_point1.set_pos(155, 149)
screen_setting_img_point1.set_size(25, 25)
screen_setting_img_point1.add_flag(lv.obj.FLAG.HIDDEN)
# Set style for screen_setting_img_point1, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_setting_img_point1.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_img_point1.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_img_point1.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_setting_img_point2
screen_setting_img_point2 = lv.img(screen_setting)
screen_setting_img_point2.set_src("B:MicroPython/_Ellipse_alpha_25x25.bin")
screen_setting_img_point2.add_flag(lv.obj.FLAG.CLICKABLE)
screen_setting_img_point2.set_pivot(50,50)
screen_setting_img_point2.set_angle(0)
screen_setting_img_point2.set_pos(214, 147)
screen_setting_img_point2.set_size(25, 25)
screen_setting_img_point2.add_flag(lv.obj.FLAG.HIDDEN)
# Set style for screen_setting_img_point2, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_setting_img_point2.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_img_point2.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_img_point2.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_setting_img_point5
screen_setting_img_point5 = lv.img(screen_setting)
screen_setting_img_point5.set_src("B:MicroPython/_Ellipse_alpha_25x25.bin")
screen_setting_img_point5.add_flag(lv.obj.FLAG.CLICKABLE)
screen_setting_img_point5.set_pivot(50,50)
screen_setting_img_point5.set_angle(0)
screen_setting_img_point5.set_pos(155, 130)
screen_setting_img_point5.set_size(25, 25)
screen_setting_img_point5.add_flag(lv.obj.FLAG.HIDDEN)
# Set style for screen_setting_img_point5, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_setting_img_point5.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_img_point5.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_img_point5.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_setting_img_point4
screen_setting_img_point4 = lv.img(screen_setting)
screen_setting_img_point4.set_src("B:MicroPython/_Ellipse_alpha_25x25.bin")
screen_setting_img_point4.add_flag(lv.obj.FLAG.CLICKABLE)
screen_setting_img_point4.set_pivot(50,50)
screen_setting_img_point4.set_angle(0)
screen_setting_img_point4.set_pos(214, 133)
screen_setting_img_point4.set_size(25, 25)
screen_setting_img_point4.add_flag(lv.obj.FLAG.HIDDEN)
# Set style for screen_setting_img_point4, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_setting_img_point4.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_img_point4.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_img_point4.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_setting_img_point6
screen_setting_img_point6 = lv.img(screen_setting)
screen_setting_img_point6.set_src("B:MicroPython/_Ellipse_alpha_25x25.bin")
screen_setting_img_point6.add_flag(lv.obj.FLAG.CLICKABLE)
screen_setting_img_point6.set_pivot(50,50)
screen_setting_img_point6.set_angle(0)
screen_setting_img_point6.set_pos(91, 132)
screen_setting_img_point6.set_size(25, 25)
screen_setting_img_point6.add_flag(lv.obj.FLAG.HIDDEN)
# Set style for screen_setting_img_point6, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_setting_img_point6.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_img_point6.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_setting_img_point6.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

screen_setting.update_layout()
# Create screen_wificfg
screen_wificfg = lv.obj()
g_kb_screen_wificfg = lv.keyboard(screen_wificfg)
g_kb_screen_wificfg.add_event_cb(lambda e: ta_event_cb(e, g_kb_screen_wificfg), lv.EVENT.ALL, None)
g_kb_screen_wificfg.add_flag(lv.obj.FLAG.HIDDEN)
g_kb_screen_wificfg.set_style_text_font(test_font("Acme_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg.set_size(320, 170)
screen_wificfg.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
# Set style for screen_wificfg, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wificfg.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg.set_style_bg_img_src("B:MicroPython/_screen_wifi_bg_320x170.bin", lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg.set_style_bg_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg.set_style_bg_img_recolor_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wificfg_img_network
screen_wificfg_img_network = lv.img(screen_wificfg)
screen_wificfg_img_network.set_src("B:MicroPython/_pomorect_alpha_160x125.bin")
screen_wificfg_img_network.add_flag(lv.obj.FLAG.CLICKABLE)
screen_wificfg_img_network.set_pivot(50,50)
screen_wificfg_img_network.set_angle(0)
screen_wificfg_img_network.set_pos(155, 33)
screen_wificfg_img_network.set_size(160, 125)
# Set style for screen_wificfg_img_network, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wificfg_img_network.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_img_network.set_style_radius(15, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_img_network.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wificfg_btn_back
screen_wificfg_btn_back = lv.btn(screen_wificfg)
screen_wificfg_btn_back_label = lv.label(screen_wificfg_btn_back)
screen_wificfg_btn_back_label.set_text("<")
screen_wificfg_btn_back_label.set_long_mode(lv.label.LONG.WRAP)
screen_wificfg_btn_back_label.set_width(lv.pct(100))
screen_wificfg_btn_back_label.align(lv.ALIGN.CENTER, 0, 0)
screen_wificfg_btn_back.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_wificfg_btn_back.set_pos(5, 5)
screen_wificfg_btn_back.set_size(25, 25)
# Set style for screen_wificfg_btn_back, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wificfg_btn_back.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_back.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_back.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_back.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_back.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_back.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_back.set_style_text_opa(195, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_back.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_wificfg_btn_back, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_wificfg_btn_back.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_back.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_back.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_back.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_back.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_back.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_back.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_back.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_back.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_back.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_back.set_style_text_font(test_font("montserratMedium", 16), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_back.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_wificfg_label_wifi
screen_wificfg_label_wifi = lv.label(screen_wificfg)
screen_wificfg_label_wifi.set_text("Wi-Fi Configuration")
screen_wificfg_label_wifi.set_long_mode(lv.label.LONG.WRAP)
screen_wificfg_label_wifi.set_width(lv.pct(100))
screen_wificfg_label_wifi.set_pos(64, 9)
screen_wificfg_label_wifi.set_size(192, 18)
# Set style for screen_wificfg_label_wifi, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wificfg_label_wifi.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_wifi.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_wifi.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_wifi.set_style_text_font(test_font("SourceHanSerifSC_Regular", 14), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_wifi.set_style_text_opa(157, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_wifi.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_wifi.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_wifi.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_wifi.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_wifi.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_wifi.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_wifi.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_wifi.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_wifi.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wificfg_img_statusbg
screen_wificfg_img_statusbg = lv.img(screen_wificfg)
screen_wificfg_img_statusbg.set_src("B:MicroPython/_pomorect_alpha_145x125.bin")
screen_wificfg_img_statusbg.add_flag(lv.obj.FLAG.CLICKABLE)
screen_wificfg_img_statusbg.set_pivot(50,50)
screen_wificfg_img_statusbg.set_angle(0)
screen_wificfg_img_statusbg.set_pos(5, 33)
screen_wificfg_img_statusbg.set_size(145, 125)
# Set style for screen_wificfg_img_statusbg, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wificfg_img_statusbg.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_img_statusbg.set_style_radius(15, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_img_statusbg.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wificfg_label_status
screen_wificfg_label_status = lv.label(screen_wificfg)
screen_wificfg_label_status.set_text("Connection Status")
screen_wificfg_label_status.set_long_mode(lv.label.LONG.SCROLL_CIRCULAR)
screen_wificfg_label_status.set_width(lv.pct(100))
screen_wificfg_label_status.set_pos(21, 40)
screen_wificfg_label_status.set_size(113, 14)
# Set style for screen_wificfg_label_status, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wificfg_label_status.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status.set_style_text_font(test_font("Alatsi_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wificfg_img_wifiicon
screen_wificfg_img_wifiicon = lv.img(screen_wificfg)
screen_wificfg_img_wifiicon.set_src("B:MicroPython/_wifi_log_2_alpha_110x110.bin")
screen_wificfg_img_wifiicon.add_flag(lv.obj.FLAG.CLICKABLE)
screen_wificfg_img_wifiicon.set_pivot(50,50)
screen_wificfg_img_wifiicon.set_angle(0)
screen_wificfg_img_wifiicon.set_pos(21, 43)
screen_wificfg_img_wifiicon.set_size(110, 110)
# Set style for screen_wificfg_img_wifiicon, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wificfg_img_wifiicon.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_img_wifiicon.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_img_wifiicon.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wificfg_label_status2
screen_wificfg_label_status2 = lv.label(screen_wificfg)
screen_wificfg_label_status2.set_text("Disconnected")
screen_wificfg_label_status2.set_long_mode(lv.label.LONG.WRAP)
screen_wificfg_label_status2.set_width(lv.pct(100))
screen_wificfg_label_status2.set_pos(30, 136)
screen_wificfg_label_status2.set_size(91, 12)
# Set style for screen_wificfg_label_status2, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wificfg_label_status2.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status2.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status2.set_style_text_color(lv.color_hex(0xfacbd3), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status2.set_style_text_font(test_font("Alatsi_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status2.set_style_text_opa(216, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status2.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status2.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status2.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status2.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status2.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status2.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status2.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status2.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_status2.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wificfg_img_wififalse
screen_wificfg_img_wififalse = lv.img(screen_wificfg)
screen_wificfg_img_wififalse.set_src("B:MicroPython/_wifi_false_alpha_20x20.bin")
screen_wificfg_img_wififalse.add_flag(lv.obj.FLAG.CLICKABLE)
screen_wificfg_img_wififalse.set_pivot(50,50)
screen_wificfg_img_wififalse.set_angle(0)
screen_wificfg_img_wififalse.set_pos(98, 71)
screen_wificfg_img_wififalse.set_size(20, 20)
# Set style for screen_wificfg_img_wififalse, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wificfg_img_wififalse.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_img_wififalse.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_img_wififalse.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wificfg_label_net
screen_wificfg_label_net = lv.label(screen_wificfg)
screen_wificfg_label_net.set_text("Available Networks")
screen_wificfg_label_net.set_long_mode(lv.label.LONG.WRAP)
screen_wificfg_label_net.set_width(lv.pct(100))
screen_wificfg_label_net.set_pos(183, 40)
screen_wificfg_label_net.set_size(106, 17)
# Set style for screen_wificfg_label_net, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wificfg_label_net.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_net.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_net.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_net.set_style_text_font(test_font("Alatsi_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_net.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_net.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_net.set_style_text_line_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_net.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_net.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_net.set_style_pad_top(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_net.set_style_pad_right(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_net.set_style_pad_bottom(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_net.set_style_pad_left(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_label_net.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)

# Create screen_wificfg_list_1
screen_wificfg_list_1 = lv.list(screen_wificfg)
screen_wificfg_list_1_item0 = screen_wificfg_list_1.add_btn(lv.SYMBOL.WIFI, "wifi1")
screen_wificfg_list_1_item1 = screen_wificfg_list_1.add_btn(lv.SYMBOL.WIFI, "wifi2")
screen_wificfg_list_1_item2 = screen_wificfg_list_1.add_btn(lv.SYMBOL.WIFI, "wifi3")
screen_wificfg_list_1_item3 = screen_wificfg_list_1.add_btn(lv.SYMBOL.WIFI, "wifi4")
screen_wificfg_list_1_item4 = screen_wificfg_list_1.add_btn(lv.SYMBOL.WIFI, "wifi5")
screen_wificfg_list_1.set_pos(159, 54)
screen_wificfg_list_1.set_size(153, 78)
screen_wificfg_list_1.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
# Set style for screen_wificfg_list_1, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wificfg_list_1.set_style_pad_top(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_list_1.set_style_pad_left(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_list_1.set_style_pad_right(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_list_1.set_style_pad_bottom(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_list_1.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_list_1.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_list_1.set_style_radius(3, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_list_1.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_wificfg_list_1, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_wificfg_list_1.set_style_pad_top(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_list_1.set_style_pad_left(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_list_1.set_style_pad_right(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_list_1.set_style_pad_bottom(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_list_1.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_list_1.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_list_1.set_style_radius(3, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_list_1.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)

# Set style for screen_wificfg_list_1, Part: lv.PART.SCROLLBAR, State: lv.STATE.DEFAULT.
screen_wificfg_list_1.set_style_radius(3, lv.PART.SCROLLBAR|lv.STATE.DEFAULT)
screen_wificfg_list_1.set_style_bg_opa(255, lv.PART.SCROLLBAR|lv.STATE.DEFAULT)
screen_wificfg_list_1.set_style_bg_color(lv.color_hex(0xffffff), lv.PART.SCROLLBAR|lv.STATE.DEFAULT)
screen_wificfg_list_1.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.SCROLLBAR|lv.STATE.DEFAULT)
# Set style for screen_wificfg_list_1, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
style_screen_wificfg_list_1_extra_btns_main_default = lv.style_t()
style_screen_wificfg_list_1_extra_btns_main_default.init()
style_screen_wificfg_list_1_extra_btns_main_default.set_pad_top(3)
style_screen_wificfg_list_1_extra_btns_main_default.set_pad_left(4)
style_screen_wificfg_list_1_extra_btns_main_default.set_pad_right(5)
style_screen_wificfg_list_1_extra_btns_main_default.set_pad_bottom(5)
style_screen_wificfg_list_1_extra_btns_main_default.set_border_width(0)
style_screen_wificfg_list_1_extra_btns_main_default.set_text_color(lv.color_hex(0xffffff))
style_screen_wificfg_list_1_extra_btns_main_default.set_text_font(test_font("Acme_Regular", 12))
style_screen_wificfg_list_1_extra_btns_main_default.set_text_opa(255)
style_screen_wificfg_list_1_extra_btns_main_default.set_radius(3)
style_screen_wificfg_list_1_extra_btns_main_default.set_bg_opa(17)
style_screen_wificfg_list_1_extra_btns_main_default.set_bg_color(lv.color_hex(0xffffff))
style_screen_wificfg_list_1_extra_btns_main_default.set_bg_grad_dir(lv.GRAD_DIR.NONE)
screen_wificfg_list_1_item4.add_style(style_screen_wificfg_list_1_extra_btns_main_default, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_list_1_item3.add_style(style_screen_wificfg_list_1_extra_btns_main_default, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_list_1_item2.add_style(style_screen_wificfg_list_1_extra_btns_main_default, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_list_1_item1.add_style(style_screen_wificfg_list_1_extra_btns_main_default, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_list_1_item0.add_style(style_screen_wificfg_list_1_extra_btns_main_default, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_wificfg_list_1, Part: lv.PART.MAIN, State: lv.STATE.PRESSED.
style_screen_wificfg_list_1_extra_btns_main_pressed = lv.style_t()
style_screen_wificfg_list_1_extra_btns_main_pressed.init()
style_screen_wificfg_list_1_extra_btns_main_pressed.set_pad_top(5)
style_screen_wificfg_list_1_extra_btns_main_pressed.set_pad_left(5)
style_screen_wificfg_list_1_extra_btns_main_pressed.set_pad_right(5)
style_screen_wificfg_list_1_extra_btns_main_pressed.set_pad_bottom(5)
style_screen_wificfg_list_1_extra_btns_main_pressed.set_border_width(0)
style_screen_wificfg_list_1_extra_btns_main_pressed.set_radius(3)
style_screen_wificfg_list_1_extra_btns_main_pressed.set_text_color(lv.color_hex(0x0D3055))
style_screen_wificfg_list_1_extra_btns_main_pressed.set_text_font(test_font("montserratMedium", 12))
style_screen_wificfg_list_1_extra_btns_main_pressed.set_text_opa(255)
style_screen_wificfg_list_1_extra_btns_main_pressed.set_bg_opa(255)
style_screen_wificfg_list_1_extra_btns_main_pressed.set_bg_color(lv.color_hex(0xffffff))
style_screen_wificfg_list_1_extra_btns_main_pressed.set_bg_grad_dir(lv.GRAD_DIR.NONE)
screen_wificfg_list_1_item4.add_style(style_screen_wificfg_list_1_extra_btns_main_pressed, lv.PART.MAIN|lv.STATE.PRESSED)
screen_wificfg_list_1_item3.add_style(style_screen_wificfg_list_1_extra_btns_main_pressed, lv.PART.MAIN|lv.STATE.PRESSED)
screen_wificfg_list_1_item2.add_style(style_screen_wificfg_list_1_extra_btns_main_pressed, lv.PART.MAIN|lv.STATE.PRESSED)
screen_wificfg_list_1_item1.add_style(style_screen_wificfg_list_1_extra_btns_main_pressed, lv.PART.MAIN|lv.STATE.PRESSED)
screen_wificfg_list_1_item0.add_style(style_screen_wificfg_list_1_extra_btns_main_pressed, lv.PART.MAIN|lv.STATE.PRESSED)
# Set style for screen_wificfg_list_1, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
style_screen_wificfg_list_1_extra_btns_main_focused = lv.style_t()
style_screen_wificfg_list_1_extra_btns_main_focused.init()
style_screen_wificfg_list_1_extra_btns_main_focused.set_pad_top(5)
style_screen_wificfg_list_1_extra_btns_main_focused.set_pad_left(5)
style_screen_wificfg_list_1_extra_btns_main_focused.set_pad_right(5)
style_screen_wificfg_list_1_extra_btns_main_focused.set_pad_bottom(5)
style_screen_wificfg_list_1_extra_btns_main_focused.set_border_width(0)
style_screen_wificfg_list_1_extra_btns_main_focused.set_radius(3)
style_screen_wificfg_list_1_extra_btns_main_focused.set_text_color(lv.color_hex(0xffffff))
style_screen_wificfg_list_1_extra_btns_main_focused.set_text_font(test_font("montserratMedium", 12))
style_screen_wificfg_list_1_extra_btns_main_focused.set_text_opa(255)
style_screen_wificfg_list_1_extra_btns_main_focused.set_bg_opa(19)
style_screen_wificfg_list_1_extra_btns_main_focused.set_bg_color(lv.color_hex(0xffffff))
style_screen_wificfg_list_1_extra_btns_main_focused.set_bg_grad_dir(lv.GRAD_DIR.NONE)
screen_wificfg_list_1_item4.add_style(style_screen_wificfg_list_1_extra_btns_main_focused, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_list_1_item3.add_style(style_screen_wificfg_list_1_extra_btns_main_focused, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_list_1_item2.add_style(style_screen_wificfg_list_1_extra_btns_main_focused, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_list_1_item1.add_style(style_screen_wificfg_list_1_extra_btns_main_focused, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_list_1_item0.add_style(style_screen_wificfg_list_1_extra_btns_main_focused, lv.PART.MAIN|lv.STATE.FOCUSED)
# Set style for screen_wificfg_list_1, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
style_screen_wificfg_list_1_extra_texts_main_default = lv.style_t()
style_screen_wificfg_list_1_extra_texts_main_default.init()
style_screen_wificfg_list_1_extra_texts_main_default.set_pad_top(5)
style_screen_wificfg_list_1_extra_texts_main_default.set_pad_left(5)
style_screen_wificfg_list_1_extra_texts_main_default.set_pad_right(5)
style_screen_wificfg_list_1_extra_texts_main_default.set_pad_bottom(5)
style_screen_wificfg_list_1_extra_texts_main_default.set_border_width(0)
style_screen_wificfg_list_1_extra_texts_main_default.set_text_color(lv.color_hex(0xffffff))
style_screen_wificfg_list_1_extra_texts_main_default.set_text_font(test_font("montserratMedium", 12))
style_screen_wificfg_list_1_extra_texts_main_default.set_text_opa(255)
style_screen_wificfg_list_1_extra_texts_main_default.set_radius(3)
style_screen_wificfg_list_1_extra_texts_main_default.set_transform_width(0)
style_screen_wificfg_list_1_extra_texts_main_default.set_bg_opa(255)
style_screen_wificfg_list_1_extra_texts_main_default.set_bg_color(lv.color_hex(0xffffff))
style_screen_wificfg_list_1_extra_texts_main_default.set_bg_grad_dir(lv.GRAD_DIR.NONE)

# Create screen_wificfg_btn_scan
screen_wificfg_btn_scan = lv.btn(screen_wificfg)
screen_wificfg_btn_scan_label = lv.label(screen_wificfg_btn_scan)
screen_wificfg_btn_scan_label.set_text("Scan")
screen_wificfg_btn_scan_label.set_long_mode(lv.label.LONG.WRAP)
screen_wificfg_btn_scan_label.set_width(lv.pct(100))
screen_wificfg_btn_scan_label.align(lv.ALIGN.CENTER, 0, 0)
screen_wificfg_btn_scan.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_wificfg_btn_scan.set_pos(168, 136)
screen_wificfg_btn_scan.set_size(45, 14)
# Set style for screen_wificfg_btn_scan, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wificfg_btn_scan.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_scan.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_scan.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_scan.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_scan.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_scan.set_style_text_font(test_font("Alatsi_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_scan.set_style_text_opa(198, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_scan.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_wificfg_btn_scan, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_wificfg_btn_scan.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_scan.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_scan.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_scan.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_scan.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_scan.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_scan.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_scan.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_scan.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_scan.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_scan.set_style_text_font(test_font("Alatsi_Regular", 12), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_scan.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_wificfg_btn_disconnect
screen_wificfg_btn_disconnect = lv.btn(screen_wificfg)
screen_wificfg_btn_disconnect_label = lv.label(screen_wificfg_btn_disconnect)
screen_wificfg_btn_disconnect_label.set_text("Disconnect")
screen_wificfg_btn_disconnect_label.set_long_mode(lv.label.LONG.WRAP)
screen_wificfg_btn_disconnect_label.set_width(lv.pct(100))
screen_wificfg_btn_disconnect_label.align(lv.ALIGN.CENTER, 0, 0)
screen_wificfg_btn_disconnect.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_wificfg_btn_disconnect.set_pos(242, 136)
screen_wificfg_btn_disconnect.set_size(58, 14)
# Set style for screen_wificfg_btn_disconnect, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wificfg_btn_disconnect.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_disconnect.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_disconnect.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_disconnect.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_disconnect.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_disconnect.set_style_text_font(test_font("Alatsi_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_disconnect.set_style_text_opa(193, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_disconnect.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_wificfg_btn_disconnect, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_wificfg_btn_disconnect.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_disconnect.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_disconnect.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_disconnect.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_disconnect.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_disconnect.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_disconnect.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_disconnect.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_disconnect.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_disconnect.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_disconnect.set_style_text_font(test_font("Alatsi_Regular", 12), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_disconnect.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_wificfg_btn_cancel
screen_wificfg_btn_cancel = lv.btn(screen_wificfg)
screen_wificfg_btn_cancel_label = lv.label(screen_wificfg_btn_cancel)
screen_wificfg_btn_cancel_label.set_text("Cancel")
screen_wificfg_btn_cancel_label.set_long_mode(lv.label.LONG.WRAP)
screen_wificfg_btn_cancel_label.set_width(lv.pct(100))
screen_wificfg_btn_cancel_label.align(lv.ALIGN.CENTER, 0, 0)
screen_wificfg_btn_cancel.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_wificfg_btn_cancel.set_pos(21, 91)
screen_wificfg_btn_cancel.set_size(45, 14)
screen_wificfg_btn_cancel.add_flag(lv.obj.FLAG.HIDDEN)
# Set style for screen_wificfg_btn_cancel, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wificfg_btn_cancel.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_cancel.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_cancel.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_cancel.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_cancel.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_cancel.set_style_text_font(test_font("Alatsi_Regular", 13), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_cancel.set_style_text_opa(198, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_cancel.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_wificfg_btn_cancel, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_wificfg_btn_cancel.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_cancel.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_cancel.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_cancel.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_cancel.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_cancel.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_cancel.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_cancel.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_cancel.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_cancel.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_cancel.set_style_text_font(test_font("Alatsi_Regular", 12), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_cancel.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_wificfg_btn_connect
screen_wificfg_btn_connect = lv.btn(screen_wificfg)
screen_wificfg_btn_connect_label = lv.label(screen_wificfg_btn_connect)
screen_wificfg_btn_connect_label.set_text("Connect")
screen_wificfg_btn_connect_label.set_long_mode(lv.label.LONG.WRAP)
screen_wificfg_btn_connect_label.set_width(lv.pct(100))
screen_wificfg_btn_connect_label.align(lv.ALIGN.CENTER, 0, 0)
screen_wificfg_btn_connect.set_style_pad_all(0, lv.STATE.DEFAULT)
screen_wificfg_btn_connect.set_pos(86, 91)
screen_wificfg_btn_connect.set_size(49, 14)
screen_wificfg_btn_connect.add_flag(lv.obj.FLAG.HIDDEN)
# Set style for screen_wificfg_btn_connect, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wificfg_btn_connect.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_connect.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_connect.set_style_radius(5, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_connect.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_connect.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_connect.set_style_text_font(test_font("Alatsi_Regular", 13), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_connect.set_style_text_opa(198, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_btn_connect.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_wificfg_btn_connect, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_wificfg_btn_connect.set_style_bg_opa(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_connect.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_connect.set_style_radius(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_connect.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_connect.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_connect.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_connect.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_connect.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_connect.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_connect.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_connect.set_style_text_font(test_font("Alatsi_Regular", 12), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_btn_connect.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)

# Create screen_wificfg_ta_password
screen_wificfg_ta_password = lv.textarea(screen_wificfg)
screen_wificfg_ta_password.set_text("")
screen_wificfg_ta_password.set_placeholder_text("")
screen_wificfg_ta_password.set_password_bullet("*")
screen_wificfg_ta_password.set_password_mode(False)
screen_wificfg_ta_password.set_one_line(True)
screen_wificfg_ta_password.set_accepted_chars("")
screen_wificfg_ta_password.set_max_length(32)
screen_wificfg_ta_password.add_event_cb(lambda e: ta_event_cb(e, g_kb_screen_wificfg), lv.EVENT.ALL, None)
screen_wificfg_ta_password.set_pos(11, 60)
screen_wificfg_ta_password.set_size(135, 26)
screen_wificfg_ta_password.add_flag(lv.obj.FLAG.HIDDEN)
screen_wificfg_ta_password.add_flag(lv.obj.FLAG.CLICKABLE)
screen_wificfg_ta_password.add_flag(lv.obj.FLAG.CLICK_FOCUSABLE)
# Set style for screen_wificfg_ta_password, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wificfg_ta_password.set_style_text_color(lv.color_hex(0xb9b9b9), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_ta_password.set_style_text_font(test_font("Acme_Regular", 12), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_ta_password.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_ta_password.set_style_text_letter_space(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_ta_password.set_style_text_align(lv.TEXT_ALIGN.LEFT, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_ta_password.set_style_bg_opa(70, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_ta_password.set_style_bg_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_ta_password.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_ta_password.set_style_border_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_ta_password.set_style_shadow_width(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_ta_password.set_style_pad_top(7, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_ta_password.set_style_pad_right(4, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_ta_password.set_style_pad_left(26, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_ta_password.set_style_radius(7, lv.PART.MAIN|lv.STATE.DEFAULT)
# Set style for screen_wificfg_ta_password, Part: lv.PART.MAIN, State: lv.STATE.FOCUSED.
screen_wificfg_ta_password.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_ta_password.set_style_text_font(test_font("Acme_Regular", 12), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_ta_password.set_style_text_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_ta_password.set_style_bg_opa(120, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_ta_password.set_style_bg_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_ta_password.set_style_bg_grad_dir(lv.GRAD_DIR.NONE, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_ta_password.set_style_border_width(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_ta_password.set_style_shadow_width(5, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_ta_password.set_style_shadow_color(lv.color_hex(0xffffff), lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_ta_password.set_style_shadow_opa(255, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_ta_password.set_style_shadow_spread(1, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_ta_password.set_style_shadow_ofs_x(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_ta_password.set_style_shadow_ofs_y(0, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_ta_password.set_style_pad_top(7, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_ta_password.set_style_pad_right(4, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_ta_password.set_style_pad_left(22, lv.PART.MAIN|lv.STATE.FOCUSED)
screen_wificfg_ta_password.set_style_radius(4, lv.PART.MAIN|lv.STATE.FOCUSED)
# Set style for screen_wificfg_ta_password, Part: lv.PART.SCROLLBAR, State: lv.STATE.DEFAULT.
screen_wificfg_ta_password.set_style_bg_opa(0, lv.PART.SCROLLBAR|lv.STATE.DEFAULT)
screen_wificfg_ta_password.set_style_radius(0, lv.PART.SCROLLBAR|lv.STATE.DEFAULT)

# Create screen_wificfg_img_passicon
screen_wificfg_img_passicon = lv.img(screen_wificfg)
screen_wificfg_img_passicon.set_src("B:MicroPython/_password_icon2_alpha_19x18.bin")
screen_wificfg_img_passicon.add_flag(lv.obj.FLAG.CLICKABLE)
screen_wificfg_img_passicon.set_pivot(50,50)
screen_wificfg_img_passicon.set_angle(0)
screen_wificfg_img_passicon.set_pos(15, 64)
screen_wificfg_img_passicon.set_size(19, 18)
screen_wificfg_img_passicon.add_flag(lv.obj.FLAG.HIDDEN)
# Set style for screen_wificfg_img_passicon, Part: lv.PART.MAIN, State: lv.STATE.DEFAULT.
screen_wificfg_img_passicon.set_style_img_opa(255, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_img_passicon.set_style_radius(0, lv.PART.MAIN|lv.STATE.DEFAULT)
screen_wificfg_img_passicon.set_style_clip_corner(True, lv.PART.MAIN|lv.STATE.DEFAULT)

screen_wificfg.update_layout()

def screen_reppo_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.SCREEN_LOAD_START):
        pass
        

screen_reppo.add_event_cb(lambda e: screen_reppo_event_handler(e), lv.EVENT.ALL, None)

def screen_log_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.SCREEN_LOAD_START):
        pass
        #Write animation: screen_log_reppo_logo zoom
        screen_log_reppo_logo_anim_zoom = lv.anim_t()
        screen_log_reppo_logo_anim_zoom.init()
        screen_log_reppo_logo_anim_zoom.set_var(screen_log_reppo_logo)
        screen_log_reppo_logo_anim_zoom.set_time(1000)
        screen_log_reppo_logo_anim_zoom.set_delay(500)
        screen_log_reppo_logo_anim_zoom.set_custom_exec_cb(lambda e,val: anim_img_zoom_cb(screen_log_reppo_logo,val))
        screen_log_reppo_logo_anim_zoom.set_values(screen_log_reppo_logo.get_zoom(), 0)
        screen_log_reppo_logo_anim_zoom.set_path_cb(lv.anim_t.path_linear)
        screen_log_reppo_logo_anim_zoom.set_repeat_count(1)
        screen_log_reppo_logo_anim_zoom.set_repeat_delay(0)
        screen_log_reppo_logo_anim_zoom.set_playback_time(1000)
        screen_log_reppo_logo_anim_zoom.set_playback_delay(0)
        screen_log_reppo_logo_anim_zoom.start()
        

screen_log.add_event_cb(lambda e: screen_log_event_handler(e), lv.EVENT.ALL, None)

def screen_log_reppo_logo_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        lv.scr_load_anim(screen_main, lv.SCR_LOAD_ANIM.FADE_ON, 200, 200, False)
        

screen_log_reppo_logo.add_event_cb(lambda e: screen_log_reppo_logo_event_handler(e), lv.EVENT.ALL, None)

def screen_main_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.SCREEN_LOAD_START):
        pass
        

screen_main.add_event_cb(lambda e: screen_main_event_handler(e), lv.EVENT.ALL, None)

def screen_main_btn_word_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        lv.scr_load_anim(screen_wordmeun, lv.SCR_LOAD_ANIM.FADE_ON, 200, 200, False)
screen_main_btn_word.add_event_cb(lambda e: screen_main_btn_word_event_handler(e), lv.EVENT.ALL, None)

def screen_main_btn_timer_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        lv.scr_load_anim(screen_pomodoro, lv.SCR_LOAD_ANIM.FADE_ON, 200, 200, False)
screen_main_btn_timer.add_event_cb(lambda e: screen_main_btn_timer_event_handler(e), lv.EVENT.ALL, None)

def screen_main_btn_setting_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        lv.scr_load_anim(screen_setting, lv.SCR_LOAD_ANIM.FADE_ON, 200, 200, False)
screen_main_btn_setting.add_event_cb(lambda e: screen_main_btn_setting_event_handler(e), lv.EVENT.ALL, None)

def screen_main_btn_plane_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        #Write animation: screen_main_img_plane x
        screen_main_img_plane_anim_x = lv.anim_t()
        screen_main_img_plane_anim_x.init()
        screen_main_img_plane_anim_x.set_var(screen_main_img_plane)
        screen_main_img_plane_anim_x.set_time(1000)
        screen_main_img_plane_anim_x.set_delay(0)
        screen_main_img_plane_anim_x.set_custom_exec_cb(lambda e,val: anim_x_cb(screen_main_img_plane,val))
        screen_main_img_plane_anim_x.set_values(screen_main_img_plane.get_x(), 100)
        screen_main_img_plane_anim_x.set_path_cb(lv.anim_t.path_linear)
        screen_main_img_plane_anim_x.set_repeat_count(1)
        screen_main_img_plane_anim_x.set_repeat_delay(0)
        screen_main_img_plane_anim_x.set_playback_time(100)
        screen_main_img_plane_anim_x.set_playback_delay(0)
        screen_main_img_plane_anim_x.start()
        #Write animation: screen_main_img_plane y
        screen_main_img_plane_anim_y = lv.anim_t()
        screen_main_img_plane_anim_y.init()
        screen_main_img_plane_anim_y.set_var(screen_main_img_plane)
        screen_main_img_plane_anim_y.set_time(1000)
        screen_main_img_plane_anim_y.set_delay(0)
        screen_main_img_plane_anim_y.set_custom_exec_cb(lambda e,val: anim_y_cb(screen_main_img_plane,val))
        screen_main_img_plane_anim_y.set_values(screen_main_img_plane.get_y(), 125)
        screen_main_img_plane_anim_y.set_path_cb(lv.anim_t.path_linear)
        screen_main_img_plane_anim_y.set_repeat_count(1)
        screen_main_img_plane_anim_y.set_repeat_delay(0)
        screen_main_img_plane_anim_y.set_playback_time(100)
        screen_main_img_plane_anim_y.set_playback_delay(0)
        screen_main_img_plane_anim_y.start()
        #Write animation: screen_main_img_plane zoom
        screen_main_img_plane_anim_zoom = lv.anim_t()
        screen_main_img_plane_anim_zoom.init()
        screen_main_img_plane_anim_zoom.set_var(screen_main_img_plane)
        screen_main_img_plane_anim_zoom.set_time(1000)
        screen_main_img_plane_anim_zoom.set_delay(0)
        screen_main_img_plane_anim_zoom.set_custom_exec_cb(lambda e,val: anim_img_zoom_cb(screen_main_img_plane,val))
        screen_main_img_plane_anim_zoom.set_values(screen_main_img_plane.get_zoom(), 400)
        screen_main_img_plane_anim_zoom.set_path_cb(lv.anim_t.path_linear)
        screen_main_img_plane_anim_zoom.set_repeat_count(1)
        screen_main_img_plane_anim_zoom.set_repeat_delay(0)
        screen_main_img_plane_anim_zoom.set_playback_time(100)
        screen_main_img_plane_anim_zoom.set_playback_delay(0)
        screen_main_img_plane_anim_zoom.start()
screen_main_btn_plane.add_event_cb(lambda e: screen_main_btn_plane_event_handler(e), lv.EVENT.ALL, None)

def screen_main_btn_todolist_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        lv.scr_load_anim(screen_todolist, lv.SCR_LOAD_ANIM.FADE_ON, 200, 200, False)
screen_main_btn_todolist.add_event_cb(lambda e: screen_main_btn_todolist_event_handler(e), lv.EVENT.ALL, None)

def screen_todolist_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.SCREEN_LOAD_START):
        pass
        

screen_todolist.add_event_cb(lambda e: screen_todolist_event_handler(e), lv.EVENT.ALL, None)

def screen_todolist_btn_back_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        lv.scr_load_anim(screen_main, lv.SCR_LOAD_ANIM.FADE_ON, 200, 200, False)
        

screen_todolist_btn_back.add_event_cb(lambda e: screen_todolist_btn_back_event_handler(e), lv.EVENT.ALL, None)

def screen_todolist_btn_delpage_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

screen_todolist_btn_delpage.add_event_cb(lambda e: screen_todolist_btn_delpage_event_handler(e), lv.EVENT.ALL, None)

def screen_todolist_btn_todo1_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

    if (code == lv.EVENT.FOCUSED):
        pass
        

screen_todolist_btn_todo1.add_event_cb(lambda e: screen_todolist_btn_todo1_event_handler(e), lv.EVENT.ALL, None)

def screen_todolist_btn_todo2_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

    if (code == lv.EVENT.FOCUSED):
        pass
        

screen_todolist_btn_todo2.add_event_cb(lambda e: screen_todolist_btn_todo2_event_handler(e), lv.EVENT.ALL, None)

def screen_todolist_btn_todo3_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

    if (code == lv.EVENT.FOCUSED):
        pass
        

screen_todolist_btn_todo3.add_event_cb(lambda e: screen_todolist_btn_todo3_event_handler(e), lv.EVENT.ALL, None)

def screen_todolist_btn_todo4_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

    if (code == lv.EVENT.FOCUSED):
        pass
        

screen_todolist_btn_todo4.add_event_cb(lambda e: screen_todolist_btn_todo4_event_handler(e), lv.EVENT.ALL, None)

def screen_todolist_btn_addpage_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

screen_todolist_btn_addpage.add_event_cb(lambda e: screen_todolist_btn_addpage_event_handler(e), lv.EVENT.ALL, None)

def screen_todolist_btn_pageminus_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

screen_todolist_btn_pageminus.add_event_cb(lambda e: screen_todolist_btn_pageminus_event_handler(e), lv.EVENT.ALL, None)

def screen_todolist_btn_pageplus_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

screen_todolist_btn_pageplus.add_event_cb(lambda e: screen_todolist_btn_pageplus_event_handler(e), lv.EVENT.ALL, None)

def screen_timing_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.SCREEN_LOAD_START):
        pass
        

screen_timing.add_event_cb(lambda e: screen_timing_event_handler(e), lv.EVENT.ALL, None)

def screen_timing_btn_pomodoro_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        lv.scr_load_anim(screen_main, lv.SCR_LOAD_ANIM.FADE_ON, 200, 200, False)
        

screen_timing_btn_pomodoro.add_event_cb(lambda e: screen_timing_btn_pomodoro_event_handler(e), lv.EVENT.ALL, None)

def screen_timing_btn_back_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        lv.scr_load_anim(screen_pomodoro, lv.SCR_LOAD_ANIM.FADE_ON, 200, 200, False)
        

screen_timing_btn_back.add_event_cb(lambda e: screen_timing_btn_back_event_handler(e), lv.EVENT.ALL, None)

def screen_pomodoro_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.SCREEN_LOAD_START):
        pass
        

screen_pomodoro.add_event_cb(lambda e: screen_pomodoro_event_handler(e), lv.EVENT.ALL, None)

def screen_pomodoro_btn_stopwatch_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

screen_pomodoro_btn_stopwatch.add_event_cb(lambda e: screen_pomodoro_btn_stopwatch_event_handler(e), lv.EVENT.ALL, None)

def screen_pomodoro_btn_countdown_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

screen_pomodoro_btn_countdown.add_event_cb(lambda e: screen_pomodoro_btn_countdown_event_handler(e), lv.EVENT.ALL, None)

def screen_pomodoro_btn_back_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        lv.scr_load_anim(screen_main, lv.SCR_LOAD_ANIM.FADE_ON, 200, 200, False)
        

screen_pomodoro_btn_back.add_event_cb(lambda e: screen_pomodoro_btn_back_event_handler(e), lv.EVENT.ALL, None)

def screen_pomodoro_btn_home_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        lv.scr_load_anim(screen_timing, lv.SCR_LOAD_ANIM.FADE_ON, 200, 200, False)
        

screen_pomodoro_btn_home.add_event_cb(lambda e: screen_pomodoro_btn_home_event_handler(e), lv.EVENT.ALL, None)

def screen_pomodoro_btn_start_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

screen_pomodoro_btn_start.add_event_cb(lambda e: screen_pomodoro_btn_start_event_handler(e), lv.EVENT.ALL, None)

def screen_pomodoro_btn_reset_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

screen_pomodoro_btn_reset.add_event_cb(lambda e: screen_pomodoro_btn_reset_event_handler(e), lv.EVENT.ALL, None)

def screen_pomodoro_btn_addnum_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

screen_pomodoro_btn_addnum.add_event_cb(lambda e: screen_pomodoro_btn_addnum_event_handler(e), lv.EVENT.ALL, None)

def screen_pomodoro_btn_minus_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

screen_pomodoro_btn_minus.add_event_cb(lambda e: screen_pomodoro_btn_minus_event_handler(e), lv.EVENT.ALL, None)

def screen_pomodoro_btn_plus_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

screen_pomodoro_btn_plus.add_event_cb(lambda e: screen_pomodoro_btn_plus_event_handler(e), lv.EVENT.ALL, None)

def screen_wordmeun_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.SCREEN_LOAD_START):
        pass
        

screen_wordmeun.add_event_cb(lambda e: screen_wordmeun_event_handler(e), lv.EVENT.ALL, None)

def screen_wordmeun_btn_back_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        lv.scr_load_anim(screen_main, lv.SCR_LOAD_ANIM.FADE_ON, 200, 200, False)
screen_wordmeun_btn_back.add_event_cb(lambda e: screen_wordmeun_btn_back_event_handler(e), lv.EVENT.ALL, None)

def screen_wordmeun_btn_bookleft_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

screen_wordmeun_btn_bookleft.add_event_cb(lambda e: screen_wordmeun_btn_bookleft_event_handler(e), lv.EVENT.ALL, None)

def screen_wordmeun_btn_bookright_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

screen_wordmeun_btn_bookright.add_event_cb(lambda e: screen_wordmeun_btn_bookright_event_handler(e), lv.EVENT.ALL, None)

def screen_wordmeun_btn_learn_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        lv.scr_load_anim(screen_wordcard, lv.SCR_LOAD_ANIM.FADE_ON, 200, 200, False)
screen_wordmeun_btn_learn.add_event_cb(lambda e: screen_wordmeun_btn_learn_event_handler(e), lv.EVENT.ALL, None)

def screen_wordmeun_btn_review_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        lv.scr_load_anim(screen_reviewcard, lv.SCR_LOAD_ANIM.FADE_ON, 200, 200, False)
screen_wordmeun_btn_review.add_event_cb(lambda e: screen_wordmeun_btn_review_event_handler(e), lv.EVENT.ALL, None)

def screen_wordcard_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.SCREEN_LOAD_START):
        pass
        

screen_wordcard.add_event_cb(lambda e: screen_wordcard_event_handler(e), lv.EVENT.ALL, None)

def screen_wordcard_btn_back_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        lv.scr_load_anim(screen_wordmeun, lv.SCR_LOAD_ANIM.FADE_ON, 200, 200, False)
screen_wordcard_btn_back.add_event_cb(lambda e: screen_wordcard_btn_back_event_handler(e), lv.EVENT.ALL, None)

def screen_wordcard_btn_left_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

screen_wordcard_btn_left.add_event_cb(lambda e: screen_wordcard_btn_left_event_handler(e), lv.EVENT.ALL, None)

def screen_wordcard_btn_right_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

screen_wordcard_btn_right.add_event_cb(lambda e: screen_wordcard_btn_right_event_handler(e), lv.EVENT.ALL, None)

def screen_wordcard_btn_dui_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

screen_wordcard_btn_dui.add_event_cb(lambda e: screen_wordcard_btn_dui_event_handler(e), lv.EVENT.ALL, None)

def screen_wordcard_btn_cuo_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

screen_wordcard_btn_cuo.add_event_cb(lambda e: screen_wordcard_btn_cuo_event_handler(e), lv.EVENT.ALL, None)

def screen_wordcard_btn_home_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        lv.scr_load_anim(screen_main, lv.SCR_LOAD_ANIM.FADE_ON, 200, 200, False)
screen_wordcard_btn_home.add_event_cb(lambda e: screen_wordcard_btn_home_event_handler(e), lv.EVENT.ALL, None)

def screen_reviewcard_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.SCREEN_LOAD_START):
        pass
        

screen_reviewcard.add_event_cb(lambda e: screen_reviewcard_event_handler(e), lv.EVENT.ALL, None)

def screen_reviewcard_btn_back_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        lv.scr_load_anim(screen_wordmeun, lv.SCR_LOAD_ANIM.FADE_ON, 200, 200, False)
        

screen_reviewcard_btn_back.add_event_cb(lambda e: screen_reviewcard_btn_back_event_handler(e), lv.EVENT.ALL, None)

def screen_reviewcard_btn_left_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

screen_reviewcard_btn_left.add_event_cb(lambda e: screen_reviewcard_btn_left_event_handler(e), lv.EVENT.ALL, None)

def screen_reviewcard_btn_right_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

screen_reviewcard_btn_right.add_event_cb(lambda e: screen_reviewcard_btn_right_event_handler(e), lv.EVENT.ALL, None)

def screen_reviewcard_btn_dui_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

screen_reviewcard_btn_dui.add_event_cb(lambda e: screen_reviewcard_btn_dui_event_handler(e), lv.EVENT.ALL, None)

def screen_reviewcard_btn_home_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        lv.scr_load_anim(screen_main, lv.SCR_LOAD_ANIM.FADE_ON, 200, 200, False)
        

screen_reviewcard_btn_home.add_event_cb(lambda e: screen_reviewcard_btn_home_event_handler(e), lv.EVENT.ALL, None)

def screen_reviewcard_btn_cuo_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

screen_reviewcard_btn_cuo.add_event_cb(lambda e: screen_reviewcard_btn_cuo_event_handler(e), lv.EVENT.ALL, None)

def screen_setting_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.SCREEN_LOAD_START):
        pass
        

screen_setting.add_event_cb(lambda e: screen_setting_event_handler(e), lv.EVENT.ALL, None)

def screen_setting_btn_wifi_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.FOCUSED):
        pass
        screen_setting_label_settings.set_text("Wifi Configuration")
        #Write animation: screen_setting_label_settings y
        screen_setting_label_settings_anim_y = lv.anim_t()
        screen_setting_label_settings_anim_y.init()
        screen_setting_label_settings_anim_y.set_var(screen_setting_label_settings)
        screen_setting_label_settings_anim_y.set_time(0)
        screen_setting_label_settings_anim_y.set_delay(0)
        screen_setting_label_settings_anim_y.set_custom_exec_cb(lambda e,val: anim_y_cb(screen_setting_label_settings,val))
        screen_setting_label_settings_anim_y.set_values(screen_setting_label_settings.get_y(), -25)
        screen_setting_label_settings_anim_y.set_path_cb(lv.anim_t.path_linear)
        screen_setting_label_settings_anim_y.set_repeat_count(1)
        screen_setting_label_settings_anim_y.set_repeat_delay(0)
        screen_setting_label_settings_anim_y.set_playback_time(200)
        screen_setting_label_settings_anim_y.set_playback_delay(0)
        screen_setting_label_settings_anim_y.start()
        screen_setting_img_point1.clear_flag(lv.obj.FLAG.HIDDEN)
        
    if (code == lv.EVENT.DEFOCUSED):
        pass
        screen_setting_img_point1.add_flag(lv.obj.FLAG.HIDDEN)
        
    if (code == lv.EVENT.CLICKED):
        pass
        lv.scr_load_anim(screen_wificfg, lv.SCR_LOAD_ANIM.FADE_ON, 200, 200, False)
screen_setting_btn_wifi.add_event_cb(lambda e: screen_setting_btn_wifi_event_handler(e), lv.EVENT.ALL, None)

def screen_setting_btn_vocab_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.FOCUSED):
        pass
        screen_setting_label_settings.set_text("Vocab Import")
        #Write animation: screen_setting_label_settings y
        screen_setting_label_settings_anim_y = lv.anim_t()
        screen_setting_label_settings_anim_y.init()
        screen_setting_label_settings_anim_y.set_var(screen_setting_label_settings)
        screen_setting_label_settings_anim_y.set_time(0)
        screen_setting_label_settings_anim_y.set_delay(0)
        screen_setting_label_settings_anim_y.set_custom_exec_cb(lambda e,val: anim_y_cb(screen_setting_label_settings,val))
        screen_setting_label_settings_anim_y.set_values(screen_setting_label_settings.get_y(), -25)
        screen_setting_label_settings_anim_y.set_path_cb(lv.anim_t.path_linear)
        screen_setting_label_settings_anim_y.set_repeat_count(1)
        screen_setting_label_settings_anim_y.set_repeat_delay(0)
        screen_setting_label_settings_anim_y.set_playback_time(200)
        screen_setting_label_settings_anim_y.set_playback_delay(0)
        screen_setting_label_settings_anim_y.start()
        screen_setting_img_point2.clear_flag(lv.obj.FLAG.HIDDEN)
        
    if (code == lv.EVENT.DEFOCUSED):
        pass
        screen_setting_img_point2.add_flag(lv.obj.FLAG.HIDDEN)
        
screen_setting_btn_vocab.add_event_cb(lambda e: screen_setting_btn_vocab_event_handler(e), lv.EVENT.ALL, None)

def screen_setting_btn_laba_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.FOCUSED):
        pass
        screen_setting_label_settings.set_text("Volume")
        #Write animation: screen_setting_label_settings y
        screen_setting_label_settings_anim_y = lv.anim_t()
        screen_setting_label_settings_anim_y.init()
        screen_setting_label_settings_anim_y.set_var(screen_setting_label_settings)
        screen_setting_label_settings_anim_y.set_time(0)
        screen_setting_label_settings_anim_y.set_delay(0)
        screen_setting_label_settings_anim_y.set_custom_exec_cb(lambda e,val: anim_y_cb(screen_setting_label_settings,val))
        screen_setting_label_settings_anim_y.set_values(screen_setting_label_settings.get_y(), -25)
        screen_setting_label_settings_anim_y.set_path_cb(lv.anim_t.path_linear)
        screen_setting_label_settings_anim_y.set_repeat_count(1)
        screen_setting_label_settings_anim_y.set_repeat_delay(0)
        screen_setting_label_settings_anim_y.set_playback_time(200)
        screen_setting_label_settings_anim_y.set_playback_delay(0)
        screen_setting_label_settings_anim_y.start()
        screen_setting_img_point3.clear_flag(lv.obj.FLAG.HIDDEN)
        
    if (code == lv.EVENT.DEFOCUSED):
        pass
        screen_setting_img_point3.add_flag(lv.obj.FLAG.HIDDEN)
        
screen_setting_btn_laba.add_event_cb(lambda e: screen_setting_btn_laba_event_handler(e), lv.EVENT.ALL, None)

def screen_setting_btn_timer_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.FOCUSED):
        pass
        screen_setting_label_settings.set_text("Time Sync")
        #Write animation: screen_setting_label_settings y
        screen_setting_label_settings_anim_y = lv.anim_t()
        screen_setting_label_settings_anim_y.init()
        screen_setting_label_settings_anim_y.set_var(screen_setting_label_settings)
        screen_setting_label_settings_anim_y.set_time(0)
        screen_setting_label_settings_anim_y.set_delay(0)
        screen_setting_label_settings_anim_y.set_custom_exec_cb(lambda e,val: anim_y_cb(screen_setting_label_settings,val))
        screen_setting_label_settings_anim_y.set_values(screen_setting_label_settings.get_y(), -25)
        screen_setting_label_settings_anim_y.set_path_cb(lv.anim_t.path_linear)
        screen_setting_label_settings_anim_y.set_repeat_count(1)
        screen_setting_label_settings_anim_y.set_repeat_delay(0)
        screen_setting_label_settings_anim_y.set_playback_time(200)
        screen_setting_label_settings_anim_y.set_playback_delay(0)
        screen_setting_label_settings_anim_y.start()
        screen_setting_img_point4.clear_flag(lv.obj.FLAG.HIDDEN)
        
    if (code == lv.EVENT.DEFOCUSED):
        pass
        screen_setting_img_point4.add_flag(lv.obj.FLAG.HIDDEN)
        
screen_setting_btn_timer.add_event_cb(lambda e: screen_setting_btn_timer_event_handler(e), lv.EVENT.ALL, None)

def screen_setting_btn_ble_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.FOCUSED):
        pass
        screen_setting_label_settings.set_text("BlueTooth")
        #Write animation: screen_setting_label_settings y
        screen_setting_label_settings_anim_y = lv.anim_t()
        screen_setting_label_settings_anim_y.init()
        screen_setting_label_settings_anim_y.set_var(screen_setting_label_settings)
        screen_setting_label_settings_anim_y.set_time(0)
        screen_setting_label_settings_anim_y.set_delay(0)
        screen_setting_label_settings_anim_y.set_custom_exec_cb(lambda e,val: anim_y_cb(screen_setting_label_settings,val))
        screen_setting_label_settings_anim_y.set_values(screen_setting_label_settings.get_y(), -25)
        screen_setting_label_settings_anim_y.set_path_cb(lv.anim_t.path_linear)
        screen_setting_label_settings_anim_y.set_repeat_count(1)
        screen_setting_label_settings_anim_y.set_repeat_delay(0)
        screen_setting_label_settings_anim_y.set_playback_time(200)
        screen_setting_label_settings_anim_y.set_playback_delay(0)
        screen_setting_label_settings_anim_y.start()
        screen_setting_img_point5.clear_flag(lv.obj.FLAG.HIDDEN)
        
    if (code == lv.EVENT.DEFOCUSED):
        pass
        screen_setting_img_point5.add_flag(lv.obj.FLAG.HIDDEN)
        
screen_setting_btn_ble.add_event_cb(lambda e: screen_setting_btn_ble_event_handler(e), lv.EVENT.ALL, None)

def screen_setting_btn_general_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.FOCUSED):
        pass
        screen_setting_label_settings.set_text("General Info")
        #Write animation: screen_setting_label_settings y
        screen_setting_label_settings_anim_y = lv.anim_t()
        screen_setting_label_settings_anim_y.init()
        screen_setting_label_settings_anim_y.set_var(screen_setting_label_settings)
        screen_setting_label_settings_anim_y.set_time(0)
        screen_setting_label_settings_anim_y.set_delay(0)
        screen_setting_label_settings_anim_y.set_custom_exec_cb(lambda e,val: anim_y_cb(screen_setting_label_settings,val))
        screen_setting_label_settings_anim_y.set_values(screen_setting_label_settings.get_y(), -25)
        screen_setting_label_settings_anim_y.set_path_cb(lv.anim_t.path_linear)
        screen_setting_label_settings_anim_y.set_repeat_count(1)
        screen_setting_label_settings_anim_y.set_repeat_delay(0)
        screen_setting_label_settings_anim_y.set_playback_time(200)
        screen_setting_label_settings_anim_y.set_playback_delay(0)
        screen_setting_label_settings_anim_y.start()
        screen_setting_img_point6.clear_flag(lv.obj.FLAG.HIDDEN)
        
    if (code == lv.EVENT.DEFOCUSED):
        pass
        screen_setting_img_point6.add_flag(lv.obj.FLAG.HIDDEN)
        
screen_setting_btn_general.add_event_cb(lambda e: screen_setting_btn_general_event_handler(e), lv.EVENT.ALL, None)

def screen_setting_btn_data_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.FOCUSED):
        pass
        screen_setting_label_settings.set_text("Data Analysis")
        #Write animation: screen_setting_label_settings y
        screen_setting_label_settings_anim_y = lv.anim_t()
        screen_setting_label_settings_anim_y.init()
        screen_setting_label_settings_anim_y.set_var(screen_setting_label_settings)
        screen_setting_label_settings_anim_y.set_time(0)
        screen_setting_label_settings_anim_y.set_delay(0)
        screen_setting_label_settings_anim_y.set_custom_exec_cb(lambda e,val: anim_y_cb(screen_setting_label_settings,val))
        screen_setting_label_settings_anim_y.set_values(screen_setting_label_settings.get_y(), -25)
        screen_setting_label_settings_anim_y.set_path_cb(lv.anim_t.path_linear)
        screen_setting_label_settings_anim_y.set_repeat_count(1)
        screen_setting_label_settings_anim_y.set_repeat_delay(0)
        screen_setting_label_settings_anim_y.set_playback_time(200)
        screen_setting_label_settings_anim_y.set_playback_delay(0)
        screen_setting_label_settings_anim_y.start()
        screen_setting_img_point7.clear_flag(lv.obj.FLAG.HIDDEN)
        
    if (code == lv.EVENT.DEFOCUSED):
        pass
        screen_setting_img_point7.add_flag(lv.obj.FLAG.HIDDEN)
        
screen_setting_btn_data.add_event_cb(lambda e: screen_setting_btn_data_event_handler(e), lv.EVENT.ALL, None)

def screen_setting_btn_todo_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.FOCUSED):
        pass
        screen_setting_label_settings.set_text("Tasks Import")
        #Write animation: screen_setting_label_settings y
        screen_setting_label_settings_anim_y = lv.anim_t()
        screen_setting_label_settings_anim_y.init()
        screen_setting_label_settings_anim_y.set_var(screen_setting_label_settings)
        screen_setting_label_settings_anim_y.set_time(0)
        screen_setting_label_settings_anim_y.set_delay(0)
        screen_setting_label_settings_anim_y.set_custom_exec_cb(lambda e,val: anim_y_cb(screen_setting_label_settings,val))
        screen_setting_label_settings_anim_y.set_values(screen_setting_label_settings.get_y(), -25)
        screen_setting_label_settings_anim_y.set_path_cb(lv.anim_t.path_linear)
        screen_setting_label_settings_anim_y.set_repeat_count(1)
        screen_setting_label_settings_anim_y.set_repeat_delay(0)
        screen_setting_label_settings_anim_y.set_playback_time(200)
        screen_setting_label_settings_anim_y.set_playback_delay(0)
        screen_setting_label_settings_anim_y.start()
        screen_setting_img_point8.clear_flag(lv.obj.FLAG.HIDDEN)
        
    if (code == lv.EVENT.DEFOCUSED):
        pass
        screen_setting_img_point8.add_flag(lv.obj.FLAG.HIDDEN)
        
screen_setting_btn_todo.add_event_cb(lambda e: screen_setting_btn_todo_event_handler(e), lv.EVENT.ALL, None)

def screen_setting_btn_back_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        lv.scr_load_anim(screen_main, lv.SCR_LOAD_ANIM.FADE_ON, 200, 200, False)
screen_setting_btn_back.add_event_cb(lambda e: screen_setting_btn_back_event_handler(e), lv.EVENT.ALL, None)

def screen_wificfg_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.SCREEN_LOAD_START):
        pass
        

screen_wificfg.add_event_cb(lambda e: screen_wificfg_event_handler(e), lv.EVENT.ALL, None)

def screen_wificfg_btn_back_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        lv.scr_load_anim(screen_setting, lv.SCR_LOAD_ANIM.FADE_ON, 200, 200, False)
screen_wificfg_btn_back.add_event_cb(lambda e: screen_wificfg_btn_back_event_handler(e), lv.EVENT.ALL, None)

def screen_wificfg_list_1_item1_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        #Write animation: screen_wificfg_img_statusbg height
        screen_wificfg_img_statusbg_anim_height = lv.anim_t()
        screen_wificfg_img_statusbg_anim_height.init()
        screen_wificfg_img_statusbg_anim_height.set_var(screen_wificfg_img_statusbg)
        screen_wificfg_img_statusbg_anim_height.set_time(200)
        screen_wificfg_img_statusbg_anim_height.set_delay(0)
        screen_wificfg_img_statusbg_anim_height.set_custom_exec_cb(lambda e,val: anim_height_cb(screen_wificfg_img_statusbg,val))
        screen_wificfg_img_statusbg_anim_height.set_values(screen_wificfg_img_statusbg.get_height(), 80)
        screen_wificfg_img_statusbg_anim_height.set_path_cb(lv.anim_t.path_linear)
        screen_wificfg_img_statusbg_anim_height.set_repeat_count(1)
        screen_wificfg_img_statusbg_anim_height.set_repeat_delay(0)
        screen_wificfg_img_statusbg_anim_height.set_playback_time(0)
        screen_wificfg_img_statusbg_anim_height.set_playback_delay(0)
        screen_wificfg_img_statusbg_anim_height.start()
        

screen_wificfg_list_1_item1.add_event_cb(lambda e: screen_wificfg_list_1_item1_event_handler(e), lv.EVENT.ALL, None)

def screen_wificfg_list_1_item2_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

        #Write animation: screen_wificfg_img_statusbg height
        screen_wificfg_img_statusbg_anim_height = lv.anim_t()
        screen_wificfg_img_statusbg_anim_height.init()
        screen_wificfg_img_statusbg_anim_height.set_var(screen_wificfg_img_statusbg)
        screen_wificfg_img_statusbg_anim_height.set_time(200)
        screen_wificfg_img_statusbg_anim_height.set_delay(0)
        screen_wificfg_img_statusbg_anim_height.set_custom_exec_cb(lambda e,val: anim_height_cb(screen_wificfg_img_statusbg,val))
        screen_wificfg_img_statusbg_anim_height.set_values(screen_wificfg_img_statusbg.get_height(), 80)
        screen_wificfg_img_statusbg_anim_height.set_path_cb(lv.anim_t.path_linear)
        screen_wificfg_img_statusbg_anim_height.set_repeat_count(1)
        screen_wificfg_img_statusbg_anim_height.set_repeat_delay(0)
        screen_wificfg_img_statusbg_anim_height.set_playback_time(0)
        screen_wificfg_img_statusbg_anim_height.set_playback_delay(0)
        screen_wificfg_img_statusbg_anim_height.start()
screen_wificfg_list_1_item2.add_event_cb(lambda e: screen_wificfg_list_1_item2_event_handler(e), lv.EVENT.ALL, None)

def screen_wificfg_list_1_item3_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

        #Write animation: screen_wificfg_img_statusbg height
        screen_wificfg_img_statusbg_anim_height = lv.anim_t()
        screen_wificfg_img_statusbg_anim_height.init()
        screen_wificfg_img_statusbg_anim_height.set_var(screen_wificfg_img_statusbg)
        screen_wificfg_img_statusbg_anim_height.set_time(200)
        screen_wificfg_img_statusbg_anim_height.set_delay(0)
        screen_wificfg_img_statusbg_anim_height.set_custom_exec_cb(lambda e,val: anim_height_cb(screen_wificfg_img_statusbg,val))
        screen_wificfg_img_statusbg_anim_height.set_values(screen_wificfg_img_statusbg.get_height(), 80)
        screen_wificfg_img_statusbg_anim_height.set_path_cb(lv.anim_t.path_linear)
        screen_wificfg_img_statusbg_anim_height.set_repeat_count(1)
        screen_wificfg_img_statusbg_anim_height.set_repeat_delay(0)
        screen_wificfg_img_statusbg_anim_height.set_playback_time(0)
        screen_wificfg_img_statusbg_anim_height.set_playback_delay(-1)
        screen_wificfg_img_statusbg_anim_height.start()
screen_wificfg_list_1_item3.add_event_cb(lambda e: screen_wificfg_list_1_item3_event_handler(e), lv.EVENT.ALL, None)

def screen_wificfg_list_1_item4_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

        #Write animation: screen_wificfg_img_statusbg height
        screen_wificfg_img_statusbg_anim_height = lv.anim_t()
        screen_wificfg_img_statusbg_anim_height.init()
        screen_wificfg_img_statusbg_anim_height.set_var(screen_wificfg_img_statusbg)
        screen_wificfg_img_statusbg_anim_height.set_time(200)
        screen_wificfg_img_statusbg_anim_height.set_delay(0)
        screen_wificfg_img_statusbg_anim_height.set_custom_exec_cb(lambda e,val: anim_height_cb(screen_wificfg_img_statusbg,val))
        screen_wificfg_img_statusbg_anim_height.set_values(screen_wificfg_img_statusbg.get_height(), 80)
        screen_wificfg_img_statusbg_anim_height.set_path_cb(lv.anim_t.path_linear)
        screen_wificfg_img_statusbg_anim_height.set_repeat_count(1)
        screen_wificfg_img_statusbg_anim_height.set_repeat_delay(0)
        screen_wificfg_img_statusbg_anim_height.set_playback_time(0)
        screen_wificfg_img_statusbg_anim_height.set_playback_delay(0)
        screen_wificfg_img_statusbg_anim_height.start()
screen_wificfg_list_1_item4.add_event_cb(lambda e: screen_wificfg_list_1_item4_event_handler(e), lv.EVENT.ALL, None)

def screen_wificfg_list_1_item5_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

        #Write animation: screen_wificfg_img_statusbg height
        screen_wificfg_img_statusbg_anim_height = lv.anim_t()
        screen_wificfg_img_statusbg_anim_height.init()
        screen_wificfg_img_statusbg_anim_height.set_var(screen_wificfg_img_statusbg)
        screen_wificfg_img_statusbg_anim_height.set_time(200)
        screen_wificfg_img_statusbg_anim_height.set_delay(0)
        screen_wificfg_img_statusbg_anim_height.set_custom_exec_cb(lambda e,val: anim_height_cb(screen_wificfg_img_statusbg,val))
        screen_wificfg_img_statusbg_anim_height.set_values(screen_wificfg_img_statusbg.get_height(), 80)
        screen_wificfg_img_statusbg_anim_height.set_path_cb(lv.anim_t.path_linear)
        screen_wificfg_img_statusbg_anim_height.set_repeat_count(1)
        screen_wificfg_img_statusbg_anim_height.set_repeat_delay(0)
        screen_wificfg_img_statusbg_anim_height.set_playback_time(0)
        screen_wificfg_img_statusbg_anim_height.set_playback_delay(0)
        screen_wificfg_img_statusbg_anim_height.start()
screen_wificfg_list_1_item5.add_event_cb(lambda e: screen_wificfg_list_1_item5_event_handler(e), lv.EVENT.ALL, None)

def screen_wificfg_btn_disconnect_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        screen_wificfg_img_wififalse.clear_flag(lv.obj.FLAG.HIDDEN)
        
        screen_wificfg_label_status2.set_text("Disconnected")
        screen_wificfg_label_status2.set_style_text_color(lv.color_hex(0xdfbcca), 0)
screen_wificfg_btn_disconnect.add_event_cb(lambda e: screen_wificfg_btn_disconnect_event_handler(e), lv.EVENT.ALL, None)

def screen_wificfg_btn_cancel_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        screen_wificfg_img_passicon.add_flag(lv.obj.FLAG.HIDDEN)
        
        screen_wificfg_ta_password.add_flag(lv.obj.FLAG.HIDDEN)
        
        screen_wificfg_btn_connect.add_flag(lv.obj.FLAG.HIDDEN)
        
        screen_wificfg_btn_cancel.add_flag(lv.obj.FLAG.HIDDEN)
        
        screen_wificfg_img_wififalse.add_flag(lv.obj.FLAG.HIDDEN)
        
        screen_wificfg_img_wifiicon.clear_flag(lv.obj.FLAG.HIDDEN)
        
        screen_wificfg_label_status.set_text("Connection Status")
        #Write animation: screen_wificfg_img_statusbg height
        screen_wificfg_img_statusbg_anim_height = lv.anim_t()
        screen_wificfg_img_statusbg_anim_height.init()
        screen_wificfg_img_statusbg_anim_height.set_var(screen_wificfg_img_statusbg)
        screen_wificfg_img_statusbg_anim_height.set_time(200)
        screen_wificfg_img_statusbg_anim_height.set_delay(0)
        screen_wificfg_img_statusbg_anim_height.set_custom_exec_cb(lambda e,val: anim_height_cb(screen_wificfg_img_statusbg,val))
        screen_wificfg_img_statusbg_anim_height.set_values(screen_wificfg_img_statusbg.get_height(), 125)
        screen_wificfg_img_statusbg_anim_height.set_path_cb(lv.anim_t.path_linear)
        screen_wificfg_img_statusbg_anim_height.set_repeat_count(1)
        screen_wificfg_img_statusbg_anim_height.set_repeat_delay(0)
        screen_wificfg_img_statusbg_anim_height.set_playback_time(0)
        screen_wificfg_img_statusbg_anim_height.set_playback_delay(0)
        screen_wificfg_img_statusbg_anim_height.start()
        screen_wificfg_label_status2.clear_flag(lv.obj.FLAG.HIDDEN)
        
        screen_wificfg_label_status2.set_text("Connected")
        screen_wificfg_label_status2.set_style_text_color(lv.color_hex(0xb7f0b8), 0)
screen_wificfg_btn_cancel.add_event_cb(lambda e: screen_wificfg_btn_cancel_event_handler(e), lv.EVENT.ALL, None)

def screen_wificfg_ta_password_event_handler(e):
    code = e.get_code()
    if (code == lv.EVENT.CLICKED):
        pass
        

    if (code == lv.EVENT.FOCUSED):
        pass
        

screen_wificfg_ta_password.add_event_cb(lambda e: screen_wificfg_ta_password_event_handler(e), lv.EVENT.ALL, None)

# content from custom.py

# Load the default screen
lv.scr_load(screen_wificfg)

while SDL.check():
    time.sleep_ms(5)

