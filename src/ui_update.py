import dearpygui.dearpygui as dpg
from src.util import nfc
from src.convert import run_convert, run_convert_custom, cancel_encoding
from src import i18n

def log_clear():
  dpg.set_value("ffmpeg_log", "")
  dpg.set_value("ffmpeg_log2", "")
def log_append(msg: str, color=None):
  prev = dpg.get_value("ffmpeg_log") or ""
  new = prev + (msg.rstrip() + "\n")
  dpg.set_value("ffmpeg_log", nfc(new))
  dpg.set_value("ffmpeg_log2", nfc(new))
def set_progress(frac: float):
  v = max(0.0, min(1.0, float(frac)))
  if dpg.does_item_exist("progress"):
    dpg.set_value("progress", v)
  if dpg.does_item_exist("progress2"):
    dpg.set_value("progress2", v)

_SERVICE_LAST = {
    "is_key": False,   # True면 i18n 키로 기억, False면 literal
    "key": "",
    "fmt": {},         # i18n.t에 넘길 포맷 파라미터 (함수/튜플 포함 가능)
    "literal": "",
}

def set_service_msg(msg_or_key: str, **fmt):
  """
  i18n 지원 서비스 메시지 표시:
    - msg_or_key가 i18n 키면 번역해서 표시
    - 키가 아니면 literal로 그대로 표시
  fmt에는 i18n.t의 확장 포맷을 그대로 지원합니다.
  """
  txt = i18n.t(msg_or_key, **fmt)

  # 실제 표시
  if dpg.does_item_exist("service_msg_text"):
    dpg.set_value("service_msg_text", txt)
  if dpg.does_item_exist("service_msg_text2"):
    dpg.set_value("service_msg_text2", txt)

  # 키/리터럴로 기록 (언어 변경 시 재번역 목적)
  is_key = (i18n.t(msg_or_key) != msg_or_key) or ("." in msg_or_key)
  _SERVICE_LAST["is_key"] = is_key
  if is_key:
    _SERVICE_LAST["key"] = msg_or_key
    _SERVICE_LAST["fmt"] = fmt or {}
    _SERVICE_LAST["literal"] = ""
  else:
    _SERVICE_LAST["key"] = ""
    _SERVICE_LAST["fmt"] = {}
    _SERVICE_LAST["literal"] = txt
def _refresh_service_msg_on_lang_change(_lang: str):
  """i18n.set_lang() 호출 시 현재 메시지 다시 적용"""
  if not dpg.does_item_exist("service_msg_text"):
    return
  if _SERVICE_LAST["is_key"] and _SERVICE_LAST["key"]:
    txt = i18n.t(_SERVICE_LAST["key"], **_SERVICE_LAST["fmt"])
  else:
    txt = _SERVICE_LAST["literal"]

  dpg.set_value("service_msg_text", txt)
  if dpg.does_item_exist("service_msg_text2"):
    dpg.set_value("service_msg_text2", txt)
i18n.on_change(_refresh_service_msg_on_lang_change)

CONVERT_BTNS = ("convert_btn1", "convert_btn2")
_convert_active = False
def _refresh_convert_btn_labels():
  """현재 상태(_convert_active)에 맞는 라벨을 i18n으로 다시 적용"""
  label_key = "button.stop" if _convert_active else "button.convert"
  text = i18n.t(label_key)
  for t in CONVERT_BTNS:
    if dpg.does_item_exist(t):
      # 콜백/테마는 건드리지 않고 라벨만 갱신
      dpg.configure_item(t, label=text)
i18n.on_change(lambda _lang: _refresh_convert_btn_labels())
def set_convert_buttons_active(active: bool):
  global _convert_active
  _convert_active = active

  for t in CONVERT_BTNS:
    if not dpg.does_item_exist(t):
      continue

    if active:
      # 변환 중: 중단 버튼 + 위험 테마
      dpg.configure_item(t, label=i18n.t("button.stop"), callback=cancel_encoding)
      dpg.bind_item_theme(t, "theme_danger_button")
    else:
      # 변환 전/후: 각 탭 기본 콜백으로 복구 + 기본 테마
      default_cb = run_convert if t == "convert_btn1" else run_convert_custom
      dpg.configure_item(t, label=i18n.t("button.convert"), callback=default_cb)
      dpg.bind_item_theme(t, "theme_primary_button")