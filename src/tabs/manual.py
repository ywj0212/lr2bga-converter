import dearpygui.dearpygui as dpg
from src.ui_components import p
from src.convert import run_convert_custom
from src import i18n

def init():
  with dpg.tab(label=i18n.t("tab.manual"), tag="tab_manual"):
    i18n.bind_label("tab_manual", "tab.manual")

    with dpg.child_window(tag="cmd_preview_wrap",
                          autosize_x=True, height=420,
                          horizontal_scrollbar=True, border=False):
      dpg.add_input_text(tag="cmd_preview",
                        multiline=True,
                        width=1920,
                        height=-1,
                        no_horizontal_scroll=True,
                        tab_input=True,
                        callback=lambda s, a: None)
    with dpg.table(header_row=False, policy=dpg.mvTable_SizingStretchProp):
      dpg.add_table_column(init_width_or_weight=1)
      dpg.add_table_column(width_fixed=True, init_width_or_weight=140)

    with dpg.table(header_row=False, policy=dpg.mvTable_SizingStretchProp):
      dpg.add_table_column(init_width_or_weight=1)
      dpg.add_table_column(width_fixed=True, init_width_or_weight=120)
      with dpg.table_row():
        p("", tag="service_msg_text2", color=(255, 255, 0, 255))
        dpg.add_button(label=i18n.t("button.convert"), width=-1, tag="convert_btn2", callback=run_convert_custom)
        i18n.bind_label("convert_btn2", "button.open")
        # convert_btn2도 런타임 라벨 변경 가능성이 있으므로 바인딩 생략(필요시 동적 코드에서 i18n.t() 사용)

    dpg.add_separator()

    dpg.add_progress_bar(tag="progress2", default_value=0.0, width=-1, height=10)
    dpg.add_input_text(tag="ffmpeg_log2", multiline=True, readonly=True,
                      width=-1, height=-1, default_value="",
                      tracked=True)
    dpg.bind_item_font(dpg.last_item(), "mono")
  