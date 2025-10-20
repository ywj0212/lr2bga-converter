import dearpygui.dearpygui as dpg
from src.ui_components import h1, h2, p
from src.ui_callbacks import on_lang_change
from src import i18n

def init():
  with dpg.tab(label=i18n.t("tab.settings"), tag="tab_settings"):
    i18n.bind_label("tab_settings", "tab.settings")
    # 언어 설정
    with dpg.table(header_row=False, policy=dpg.mvTable_SizingStretchProp,
                    resizable=False, borders_innerV=False, borders_innerH=False,
                    borders_outerV=False, borders_outerH=False):
      dpg.add_table_column(width_fixed=True, init_width_or_weight=90)
      dpg.add_table_column(init_width_or_weight=1)

      with dpg.table_row():
        p("label.language")  # "언어"
        dpg.add_radio_button(
          items=i18n.LANG_CHOICES,
          horizontal=True,
          tag="lang_selector",
          default_value=i18n.CODE_TO_NAME.get(i18n.current_lang(), "English"),
          callback=on_lang_change
        )
