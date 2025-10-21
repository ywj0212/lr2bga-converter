import dearpygui.dearpygui as dpg

from src.states import set_state, get_state
from src.ui_components import apply_lock_pair
from src.cmdline import update_command, update_estimated_size, is_letterbox_needed
from src import i18n

LETTERBOX_MODES = ["black", "solid", "blur"]

def _letterbox_labels() -> list[str]:
  labels = i18n.t_list("combo.letterbox_items")
  if labels:
    return [str(x) for x in labels]
  return ["Black", "Solid", "Blur"]

def _letterbox_mode_to_label(mode: str | None = None) -> str:
  labels = _letterbox_labels()
  try:
    idx = LETTERBOX_MODES.index((mode or get_state().get("letterbox_mode", LETTERBOX_MODES[0])).lower())
  except ValueError:
    idx = 0
  if idx >= len(labels):
    idx = 0
  return labels[idx] if labels else LETTERBOX_MODES[0]

def _label_to_letterbox_mode(label: str) -> str:
  labels = _letterbox_labels()
  try:
    idx = labels.index(label)
  except ValueError:
    idx = 0
  if idx >= len(LETTERBOX_MODES):
    idx = 0
  return LETTERBOX_MODES[idx]

def get_letterbox_mode_label(mode: str | None = None) -> str:
  return _letterbox_mode_to_label(mode)

def _letterbox_color_vec() -> list[int]:
  raw = get_state().get("letterbox_color", (0, 0, 0))
  if isinstance(raw, (list, tuple)) and len(raw) >= 3:
    try:
      r, g, b = raw[:3]
    except Exception:
      r = g = b = 0
  else:
    r = g = b = 0
  def _clamp(v):
    try:
      return max(0, min(255, int(round(v))))
    except Exception:
      return 0
  return [_clamp(r), _clamp(g), _clamp(b), 255]

def refresh_letterbox_controls():
  state = get_state()
  enabled = is_letterbox_needed(state)
  mode = str(state.get("letterbox_mode", LETTERBOX_MODES[0]) or LETTERBOX_MODES[0]).lower()
  if mode not in LETTERBOX_MODES:
    mode = LETTERBOX_MODES[0]
  label_value = _letterbox_mode_to_label(mode)

  if dpg.does_item_exist("letterbox_combo"):
    dpg.set_value("letterbox_combo", label_value)
    dpg.configure_item("letterbox_combo", enabled=enabled)
    dpg.bind_item_theme("letterbox_combo", 0 if enabled else "theme_locked_text")

  if dpg.does_item_exist("letterbox_label_group"):
    dpg.bind_item_theme("letterbox_label_group", 0 if enabled else "theme_locked_text")

  for tag in ("letterbox_label", "letterbox_help"):
    if dpg.does_item_exist(tag):
      dpg.bind_item_theme(tag, 0 if enabled else "theme_locked_text")

  if dpg.does_item_exist("tooltip_letterbox_help"):
    dpg.configure_item("tooltip_letterbox_help", show=enabled)
  if dpg.does_item_exist("tooltip_letterbox_disabled"):
    dpg.configure_item("tooltip_letterbox_disabled", show=not enabled)

  if dpg.does_item_exist("letterbox_extra_group"):
    dpg.configure_item("letterbox_extra_group", show=enabled)
    dpg.bind_item_theme("letterbox_extra_group", 0 if enabled else "theme_locked_text")

  color_vec = _letterbox_color_vec()
  show_color = enabled and mode == "solid"
  if dpg.does_item_exist("letterbox_color_edit"):
    dpg.configure_item("letterbox_color_edit", show=show_color, enabled=enabled)
    dpg.bind_item_theme("letterbox_color_edit", 0 if enabled else "theme_locked_text")
    if show_color:
      dpg.set_value("letterbox_color_edit", color_vec)
  if dpg.does_item_exist("tooltip_letterbox_color"):
    dpg.configure_item("tooltip_letterbox_color", show=show_color)

  show_blur = enabled and mode == "blur"
  blur_val = state.get("letterbox_blur_radius", 20)
  try:
    blur_val = int(blur_val)
  except Exception:
    blur_val = 20
  blur_val = max(4, min(120, blur_val))
  if dpg.does_item_exist("letterbox_blur_slider"):
    dpg.configure_item("letterbox_blur_slider", show=show_blur, enabled=enabled)
    dpg.bind_item_theme("letterbox_blur_slider", 0 if enabled else "theme_locked_text")
    dpg.set_value("letterbox_blur_slider", blur_val)
  if dpg.does_item_exist("tooltip_letterbox_blur"):
    dpg.configure_item("tooltip_letterbox_blur", show=show_blur)

def on_letterbox_mode(sender, app_data):
  mode = _label_to_letterbox_mode(str(app_data))
  set_state("letterbox_mode", mode)
  refresh_letterbox_controls()
  update_command()

def on_letterbox_color(sender, app_data):
  if not isinstance(app_data, (list, tuple)) or len(app_data) < 3:
    return
  try:
    r, g, b = app_data[:3]
    color = (
      max(0, min(255, int(round(r)))),
      max(0, min(255, int(round(g)))),
      max(0, min(255, int(round(b)))),
    )
  except Exception:
    color = (0, 0, 0)
  set_state("letterbox_color", color)
  update_command()

def on_letterbox_blur(sender, app_data):
  try:
    radius = int(app_data)
  except Exception:
    radius = get_state().get("letterbox_blur_radius", 20)
  radius = max(4, min(120, int(radius)))
  set_state("letterbox_blur_radius", radius)
  if dpg.does_item_exist("letterbox_blur_slider"):
    dpg.set_value("letterbox_blur_slider", radius)
  update_command()

def on_custom_width(sender, app_data):
  set_state("width", int(app_data))
  refresh_letterbox_controls()
  update_command()
def on_custom_height(sender, app_data):
  set_state("height", int(app_data))
  refresh_letterbox_controls()
  update_command()

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
    preset_lower = str(preset).lower()
    if preset in ("720p", "1080p"):
      target_h = 720 if preset == "720p" else 1080
      state = get_state()
      src_w = int(state.get("source_width", 0) or 0)
      src_h = int(state.get("source_height", 0) or 0)
      if src_w > 0 and src_h > 0:
        aspect = src_w / src_h
        target_w = int(round(target_h * aspect))
        if target_w % 2:
          target_w += 1
      else:
        target_w = 1280 if target_h == 720 else 1920
      w, h = max(1, target_w), target_h
    else:
      try:
        w, h = map(int, preset_lower.split("x"))
      except Exception:
        w, h = 512, 512
    dpg.set_value("w_custom", w); dpg.set_value("h_custom", h)
    dpg.set_value("w_display", str(w)); dpg.set_value("h_display", str(h))
    set_state("width", w); set_state("height", h)
  refresh_letterbox_controls()
  update_command()

def _configure_mux_tooltips(disabled: bool):
  if dpg.does_item_exist("tooltip_mux_container"):
    dpg.configure_item("tooltip_mux_container", show=not disabled)
  if not disabled and dpg.does_item_exist("tooltip_mux_text"):
    dpg.set_value("tooltip_mux_text", i18n.t("tooltip.mux"))
    i18n.bind_value("tooltip_mux_text", "tooltip.mux")

  if dpg.does_item_exist("tooltip_mux_auto_container"):
    dpg.configure_item("tooltip_mux_auto_container", show=not disabled)
  if not disabled and dpg.does_item_exist("tooltip_mux_auto_text"):
    dpg.set_value("tooltip_mux_auto_text", i18n.t("tooltip.mux_auto"))
    i18n.bind_value("tooltip_mux_auto_text", "tooltip.mux_auto")
  if dpg.does_item_exist("tooltip_mux_disabled"):
    dpg.configure_item("tooltip_mux_disabled", show=disabled)
  if dpg.does_item_exist("tooltip_mux_disabled_text") and disabled:
    dpg.set_value("tooltip_mux_disabled_text", i18n.t("tooltip.mux_disabled"))
    i18n.bind_value("tooltip_mux_disabled_text", "tooltip.mux_disabled")

def on_codec_change(sender, app_data):
  codec = str(app_data)
  set_state("codec", codec)
  use_h264 = (codec == "H.264")

  targets = ("mux_input", "mux_auto_chk")
  for item in targets:
    if dpg.does_item_exist(item):
      dpg.configure_item(item, enabled=not use_h264)
      dpg.bind_item_theme(item, "theme_locked_text" if use_h264 else 0)

  if dpg.does_item_exist("mux_unit_text"):
    if use_h264:
      dpg.bind_item_theme("mux_unit_text", "theme_locked_text")
    else:
      dpg.bind_item_theme("mux_unit_text", 0)

  for tag in ("mux_label_text", "mux_label_help"):
    if dpg.does_item_exist(tag):
      dpg.bind_item_theme(tag, "theme_locked_text" if use_h264 else 0)

  _configure_mux_tooltips(use_h264)

  update_command()

def _bind_mux_tooltips(mux_key: str, auto_key: str):
  if dpg.does_item_exist("tooltip_mux_text"):
    dpg.set_value("tooltip_mux_text", i18n.t(mux_key))
    i18n.bind_value("tooltip_mux_text", mux_key)
  if dpg.does_item_exist("tooltip_mux_auto_text"):
    dpg.set_value("tooltip_mux_auto_text", i18n.t(auto_key))
    i18n.bind_value("tooltip_mux_auto_text", auto_key)
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

i18n.on_change(lambda _lang: refresh_letterbox_controls())
