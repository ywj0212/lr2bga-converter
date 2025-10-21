import dearpygui.dearpygui as dpg
from src.explorer import open_dir_native, open_file_native
from src.states import set_state
from src.cmdline import update_command, _fmt_estimated_size_value
from src.ui_components import p, \
     make_lock_pair_float, make_lock_pair_int, apply_lock_pair
from src.ui_callbacks import on_res_preset, on_float_value, on_int_value, \
     on_fps_lock_toggle, on_buffer_lock_toggle, on_codec_change
from src.convert import run_convert
from src import i18n

def init():
  with dpg.tab(label=i18n.t("tab.basic"), tag="tab_basic"):
    # 탭 라벨 i18n 바인딩
    i18n.bind_label("tab_basic", "tab.basic")

    with dpg.table(header_row=False,
                  policy=dpg.mvTable_SizingStretchProp,
                  resizable=False, borders_innerV=False, borders_innerH=False,
                  borders_outerV=False, borders_outerH=False):
      dpg.add_table_column(width_fixed=True, init_width_or_weight=160)
      dpg.add_table_column(init_width_or_weight=1)
      dpg.add_table_column(width_fixed=True, init_width_or_weight=120)

      # 원본 파일 경로
      with dpg.table_row():
        p("label.input_path")  # i18n 키 자동 인식
        dpg.add_input_text(tag="in_path", width=-1, readonly=True)
        dpg.add_button(label=i18n.t("button.open"), width=-1, tag="btn_open_in", callback=open_file_native)
        i18n.bind_label("btn_open_in", "button.open")

      # 출력 경로
      with dpg.table_row():
        p("label.output_dir")
        dpg.add_input_text(tag="out_dir", width=-1, readonly=True)
        dpg.add_button(label=i18n.t("button.open"), width=-1, tag="btn_open_out", callback=open_dir_native)
        i18n.bind_label("btn_open_out", "button.open")

      # 출력 파일명(확장자 제외)
      with dpg.table_row():
        with dpg.group(horizontal=True):
          p("label.output_name")
          p("(?)", color=(150,150,150))
          with dpg.tooltip(dpg.last_item()):
            p("tooltip.output_name")
        dpg.add_input_text(tag="out_name", width=-1, callback=lambda s,a: set_state("output_name", a))
        dpg.add_spacer(width=100)

    # 구분선
    dpg.add_separator()

    with dpg.table(header_row=False,
                  policy=dpg.mvTable_SizingStretchProp,
                  resizable=False, borders_innerV=False, borders_innerH=False,
                  borders_outerV=False, borders_outerH=False):
      dpg.add_table_column(width_fixed=True, init_width_or_weight=160)
      dpg.add_table_column(width_fixed=True, init_width_or_weight=220)
      dpg.add_table_column(init_width_or_weight=1)

      with dpg.table_row():
        with dpg.group(horizontal=True):
          p("label.resolution")
          p("(?)", color=(150,150,150))
          with dpg.tooltip(dpg.last_item()):
            p("tooltip.resolution")
        
        dpg.add_combo(items=["256x256", "512x512", "640x480", "1280x720", "720p", "1080p", "Custom"],
                      default_value="512x512", width=180, callback=on_res_preset, tag="res_preset")
        # 콤보 items i18n 바인딩(언어 변경 시 항목 전체 갱신)
        i18n.bind_items("res_preset", "combo.res_preset_items")

        with dpg.group(horizontal=True):
          # Custom 폭/높이 (입력/표시 페어)
          dpg.add_input_int(tag="w_custom", default_value=512, width=120, step=1, min_value=1, min_clamped=True,
                            callback=lambda s,a: (set_state("width", int(a)), refresh_letterbox_controls(), update_command()))
          p("", tag="w_display", show=True)  # 초기엔 프리셋=락 → 표시용 보이기
          p("x")
          dpg.add_input_int(tag="h_custom", default_value=512, width=120, step=1, min_value=1, min_clamped=True,
                            callback=lambda s,a: (set_state("height", int(a)), refresh_letterbox_controls(), update_command()))
          p("", tag="h_display", show=True)
          dpg.bind_item_theme("w_display", "theme_locked_text")
          dpg.bind_item_theme("h_display", "theme_locked_text")

      with dpg.table_row():
        with dpg.group(horizontal=True, tag="letterbox_label_group"):
          p("label.letterbox_options", tag="letterbox_label")
          p("(?)", color=(150,150,150), tag="letterbox_help")
          with dpg.tooltip(dpg.last_item(), tag="tooltip_letterbox_help"):
            p("tooltip.letterbox")
        with dpg.tooltip("letterbox_label_group", tag="tooltip_letterbox_disabled", show=False):
          p("tooltip.letterbox_disabled", tag="tooltip_letterbox_disabled_text")

        dpg.add_combo(
          items=i18n.t_list("combo.letterbox_items") or ["Black", "Solid", "Blur"],
          default_value=get_letterbox_mode_label(),
          width=180,
          callback=on_letterbox_mode,
          tag="letterbox_combo",
        )
        i18n.bind_items("letterbox_combo", "combo.letterbox_items")

        with dpg.group(horizontal=True, tag="letterbox_extra_group"):
          color_edit = dpg.add_color_edit(
            tag="letterbox_color_edit",
            default_value=(255, 255, 255, 255),
            no_alpha=True,
            input_mode=dpg.mvColorEdit_input_rgb,
            width=220,
            show=False,
            callback=on_letterbox_color,
          )
          with dpg.tooltip(color_edit, tag="tooltip_letterbox_color"):
            p("tooltip.letterbox_color")

          blur_slider = dpg.add_slider_int(
            tag="letterbox_blur_slider",
            min_value=4,
            max_value=120,
            default_value=20,
            width=220,
            show=False
          )
          with dpg.item_handler_registry() as h:
            dpg.add_item_deactivated_after_edit_handler(callback=lambda sender: on_letterbox_blur(sender, dpg.get_value("letterbox_blur_slider")))
          dpg.bind_item_handler_registry("letterbox_blur_slider", h)
          with dpg.tooltip(blur_slider, tag="tooltip_letterbox_blur"):
            p("tooltip.letterbox_blur")

      with dpg.table_row(height=20):
        pass

      with dpg.table_row():
        with dpg.group(horizontal=True):
          p("label.fps")
          p("(?)", color=(150,150,150))
          with dpg.tooltip(dpg.last_item()):
            p("tooltip.fps")
        
        make_lock_pair_float("FPS", "fps_input", "fps_display",
                              width=130, default_value=30.0,
                              cb=on_float_value("fps", "fps_input"))
        dpg.add_checkbox(tag="fps_lock", label=i18n.t("checkbox.lock"), default_value=True, callback=on_fps_lock_toggle)
        i18n.bind_label("fps_lock", "checkbox.lock")

      with dpg.table_row():
        p("label.bitrate")
        with dpg.group(horizontal=True):
          dpg.add_input_int(tag="br_input", default_value=1600, width=130, step=50, min_value=1, min_clamped=True,
                            callback=on_int_value("bitrate_k", "br_input"))
          p("k")
        dpg.add_spacer()

      with dpg.table_row():
        with dpg.group(horizontal=True):
          p("label.buffer_size")
          p("(?)", color=(150,150,150))
          with dpg.tooltip(dpg.last_item()):
            p("tooltip.buffer")

        make_lock_pair_int("버퍼사이즈", "buf_input", "buf_display",
                            width=130, default_value=2900, cb=on_int_value("buffer_k", "buf_input"),
                            unit_text="k")
        dpg.add_checkbox(tag="buf_lock", label=i18n.t("checkbox.lock"), default_value=True, callback=on_buffer_lock_toggle)
        i18n.bind_label("buf_lock", "checkbox.lock")

      with dpg.table_row():
        with dpg.group(horizontal=True):
          p("label.mux_rate")
          p("(?)", color=(150,150,150))
          with dpg.tooltip(dpg.last_item()):
            p("tooltip.mux", tag="tooltip_mux_text")

        with dpg.group(horizontal=True):
          dpg.add_input_int(tag="mux_input", default_value=2100, width=130, step=50, min_value=1, min_clamped=True,
                            callback=on_int_value("mux_k", "mux_input"))
          p("k", tag="mux_unit_text")
        with dpg.group(horizontal=True):  
          dpg.add_checkbox(tag="mux_auto_chk",
                            label=i18n.t("checkbox.mux_auto"),
                            default_value=True,
                            callback=lambda s,a: set_state("mux_auto", bool(a)))
          i18n.bind_label("mux_auto_chk", "checkbox.mux_auto")
          with dpg.tooltip(dpg.last_item()):
            p("tooltip.mux_auto", tag="tooltip_mux_auto_text")
    
      with dpg.table_row(height=20):
        pass

      with dpg.table_row():
        with dpg.group(horizontal=True):
          p("label.codec")
          p("(?)", color=(150,150,150))
          with dpg.tooltip(dpg.last_item()):
            p("tooltip.codec", tag="tooltip_codec_text")
        dpg.add_combo(items=["MPEG1", "H.264"],
                      default_value="MPEG1", width=180, callback=on_codec_change, tag="codec_combo")
        i18n.bind_items("codec_combo", "combo.codec_items")
        dpg.add_spacer()

      with dpg.table_row():
        dpg.add_spacer()   # 1열
        dpg.add_spacer()   # 2열
        # 초기 표시는 현지화된 기본 텍스트(동적 업데이트는 별도 함수가 갱신)
        p(
          "label.estimated_size",
          i18n_key="label.estimated_size",       # 키를 명시 → 즉시 포맷 + 바인딩
          fmt={"size": _fmt_estimated_size_value},  # {size}는 함수로 전달(언어 변경 시 재평가)
          align="right",
          tag="est_size_text"
        )

    with dpg.table(header_row=False, policy=dpg.mvTable_SizingStretchProp):
      dpg.add_table_column(init_width_or_weight=1)
      dpg.add_table_column(width_fixed=True, init_width_or_weight=120)
      with dpg.table_row():
        p("", tag="service_msg_text", color=(255, 255, 0, 255))
        dpg.add_button(label=i18n.t("button.convert"), width=-1, tag="convert_btn1", callback=run_convert)

    dpg.add_separator()

    # 진행바
    dpg.add_progress_bar(tag="progress", default_value=0.0, width=-1, height=10)

    # 로그 (멀티라인 텍스트 박스)
    dpg.add_input_text(tag="ffmpeg_log", multiline=True, readonly=True,
                      width=-1, height=-1, default_value="", tab_input=True,
                      tracked=True)
    dpg.bind_item_font(dpg.last_item(), "mono")
    
    dpg.set_value("w_display", "512")
  
  dpg.set_value("h_display", "512")
  apply_lock_pair("w_custom", "w_display", True)
  apply_lock_pair("h_custom", "h_display", True)
  apply_lock_pair("fps_input", "fps_display", True)
  apply_lock_pair("buf_input", "buf_display", True)
  refresh_letterbox_controls()