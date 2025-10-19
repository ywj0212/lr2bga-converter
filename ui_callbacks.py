import dearpygui.dearpygui as dpg

from states import set_state
from ui_components import apply_lock_pair
from cmdline import update_command
from cmdline import update_estimated_size
import i18n

def on_custom_width(sender, app_data):
  set_state("width", int(app_data))
def on_custom_height(sender, app_data):
  set_state("height", int(app_data))

def on_fps_lock_toggle(sender, app_data):
  locked = dpg.get_value("fps_lock")
  set_state("fps_locked", locked)
  if locked:
    dpg.set_value("fps_input", 30.0)
    set_state("fps", 30.0)
  apply_lock_pair("fps_input", "fps_display", locked)
def on_buffer_lock_toggle(sender, app_data):
  locked = dpg.get_value("buf_lock")
  set_state("buffer_locked", locked)
  if locked:
    dpg.set_value("buf_input", 2900)
    set_state("buffer_k", 2900)
  apply_lock_pair("buf_input", "buf_display", locked)
def on_res_preset(sender, app_data):
  preset = app_data
  set_state("res_preset", preset)
  is_custom = (preset == "Custom")
  apply_lock_pair("w_custom", "w_display", not is_custom)
  apply_lock_pair("h_custom", "h_display", not is_custom)
  if not is_custom:
    try:
      w, h = map(int, preset.lower().split("x"))
    except Exception:
      w, h = 512, 512
    dpg.set_value("w_custom", w); dpg.set_value("h_custom", h)
    dpg.set_value("w_display", str(w)); dpg.set_value("h_display", str(h))
    set_state("width", w); set_state("height", h)
  update_command()

def on_float_value(key, item_tag):
  def _cb(sender, app_data):
    try:
      v = float(app_data)
    except Exception:
      v = 0
    dpg.set_value(item_tag, v)
    update_estimated_size()
    set_state(key, v)
  return _cb
def on_int_value(key, item_tag):
  def _cb(sender, app_data):
    try:
      v = int(app_data)
    except Exception:
      v = 0
    dpg.set_value(item_tag, v)
    update_estimated_size()
    set_state(key, v)
  return _cb

def on_lang_change(sender, app_data, user_data):
  """라디오 버튼 선택 시 언어 변경"""
  # app_data 는 선택된 문자열(예: "한국어")
  lang_code = i18n.NAME_TO_CODE.get(str(app_data))
  if not lang_code:
    return
  # i18n 적용 (등록된 bind_value / bind_label / bind_items 모두 자동 refresh)
  i18n.set_lang(lang_code)
