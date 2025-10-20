import dearpygui.dearpygui as dpg
from src import i18n

from src.cmdline import update_command
from src.ui_map import bind_ui
import src.ui_update as ui_update

import src.tabs.basic as basic, src.tabs.manual as manual, \
       src.tabs.settings as settings

def init_ui():
  with dpg.window(tag="main",
                  no_title_bar=True, no_resize=True, no_move=True,
                  no_collapse=True, no_scrollbar=False):

    with dpg.tab_bar():
      basic.init()     # 기본 설정 탭
      manual.init()    # 직접 설정 탭
      settings.init()  # 환결 설정 탭

  # ─────────────── 초기 락 상태 반영 및 명령어 생성 ─────────────────
  # dpg.set_value("w_display", "512")
  # dpg.set_value("h_display", "512")
  # apply_lock_pair("w_custom", "w_display", True)
  # apply_lock_pair("h_custom", "h_display", True)
  # apply_lock_pair("fps_input", "fps_display", True)
  # apply_lock_pair("buf_input", "buf_display", True)
  update_command()

  bind_ui(
    log_append_fn=ui_update.log_append,
    log_clear_fn=ui_update.log_clear,
    set_progress_fn=ui_update.set_progress,
    set_service_msg_fn=ui_update.set_service_msg,
    set_convert_buttons_active_fn=ui_update.set_convert_buttons_active,
  )

  # ────────────────────────────── 실행 ──────────────────────────────
  dpg.create_viewport(title=i18n.t("app.title"), width=800, height=860)
  dpg.setup_dearpygui()
  dpg.set_primary_window("main", True)
  dpg.show_viewport()
  dpg.start_dearpygui()
  dpg.destroy_context()
