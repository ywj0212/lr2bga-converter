import dearpygui.dearpygui as dpg
from util import random_string, nfc
from typing import Optional, Dict, Any
import i18n

def _resolve_i18n(text_or_key: str,
                  i18n_key: Optional[str],
                  fmt: Optional[Dict[str, Any]]) -> tuple[str, Optional[str]]:
    """
    표시할 텍스트, 바인딩에 사용할 키를 반환.
    - i18n_key가 명시되면 그 키로 번역해서 표시 + 바인딩
    - i18n_key가 없고, 첫 인자(text_or_key)가 사전에 존재하는 키면 그 키로 번역 + 바인딩
    - 둘 다 아니면 그대로 표시(바인딩 없음)
    """
    # 1) i18n_key가 있으면 그걸 우선
    if i18n_key:
        display = i18n.t(i18n_key, **(fmt or {}))
        return display, i18n_key

    # 2) 첫 인자가 키로 존재하면 키로 취급
    prob = str(text_or_key)
    translated = i18n.t(prob)
    if translated != prob:
        # 실제 번역이 있었던 경우
        return translated, prob

    # 3) 번역 없음 → 그냥 원문
    return str(text_or_key), None
def _add_text_with_font(text_or_key: str,
                        font_tag: str,
                        tag: str = "",
                        align: str = "left",
                        *,
                        i18n_key: Optional[str] = None,
                        fmt: Optional[Dict[str, Any]] = None,
                        **kwargs) -> str:
    """
    align: 'left' | 'right' | 'center'
    """
    parent = kwargs.pop("parent", None)
    if "tag" in kwargs:
        raise ValueError("tag는 매개변수로만 지정하세요.")

    identifier = tag or random_string()
    safe_kwargs = {k: v for k, v in kwargs.items() if v is not None}

    # i18n 처리
    display_text, bind_key = _resolve_i18n(text_or_key, i18n_key, fmt)

    def _add_text(parent_id=None):
        if parent_id is None:
            dpg.add_text(nfc(display_text), tag=identifier, **safe_kwargs)
        else:
            dpg.add_text(nfc(display_text), tag=identifier, parent=parent_id, **safe_kwargs)

    if align in ("right", "center"):
        # 텍스트 픽셀폭 추정
        pad_px = 6
        if "wrap" in safe_kwargs and isinstance(safe_kwargs["wrap"], (int, float)) and safe_kwargs["wrap"] > 0:
            mid_width = int(safe_kwargs["wrap"])
        else:
            try:
                mid_width = int(dpg.get_text_size(nfc(display_text))[0]) + pad_px
            except Exception:
                mid_width = 240

        # ★ parent가 있을 때만 parent 키를 넣는다
        table_kwargs = dict(
            label="",
            header_row=False,
            policy=dpg.mvTable_SizingStretchProp,
            resizable=False,
            borders_innerV=False, borders_innerH=False,
            borders_outerV=False, borders_outerH=False
        )
        if parent is not None:
            table_kwargs["parent"] = parent

        with dpg.table(**table_kwargs):
            if align == "center":
                dpg.add_table_column(init_width_or_weight=1)
                dpg.add_table_column(width=int(mid_width), width_fixed=True)
                dpg.add_table_column(init_width_or_weight=1)
                with dpg.table_row():
                    dpg.add_spacer()
                    _add_text()
                    dpg.add_spacer()
            else:  # right
                dpg.add_table_column(init_width_or_weight=1)
                dpg.add_table_column(width=int(mid_width), width_fixed=True)
                with dpg.table_row():
                    dpg.add_spacer()
                    _add_text()
    else:
        _add_text(parent)

    dpg.bind_item_font(identifier, font_tag)

    # i18n 바인딩(언어 변경 시 자동 갱신)
    if bind_key:
        i18n.bind_value(identifier, bind_key, **(fmt or {}))

    return identifier

def p(text_or_key: str,
      tag: str = "",
      align: str = "left",
      *,
      i18n_key: Optional[str] = None,
      fmt: Optional[Dict[str, Any]] = None,
      **kwargs) -> str:
    """
    예)
      p("label.input_path")             # i18n 키 자동 판별 → 번역/바인딩
      p("원본 파일 경로")               # 그냥 텍스트
      p("label.bytes", i18n_key="label.bytes", fmt={"n": 42})
    """
    return _add_text_with_font(text_or_key, "p", tag=tag, align=align,
                               i18n_key=i18n_key, fmt=fmt, **kwargs)
def h1(text_or_key: str,
       tag: str = "",
       align: str = "left",
       *,
       i18n_key: Optional[str] = None,
       fmt: Optional[Dict[str, Any]] = None,
       **kwargs) -> str:
    return _add_text_with_font(text_or_key, "h1", tag=tag, align=align,
                               i18n_key=i18n_key, fmt=fmt, **kwargs)
def h2(text_or_key: str,
       tag: str = "",
       align: str = "left",
       *,
       i18n_key: Optional[str] = None,
       fmt: Optional[Dict[str, Any]] = None,
       **kwargs) -> str:
    return _add_text_with_font(text_or_key, "h2", tag=tag, align=align,
                               i18n_key=i18n_key, fmt=fmt, **kwargs)

def make_lock_pair_int(label_text: str, input_tag: str, display_tag: str,
                       *, width: int = -1, default_value: int = 0, step: int = 50,
                       cb=None, unit_text: str | None = None):
  with dpg.group(horizontal=True):
    dpg.add_input_int(tag=input_tag, default_value=default_value, width=width,
                      step=step, min_value=1, min_clamped=True,
                      callback=cb or (lambda s, a: None))
    p("", tag=display_tag, show=False)
    dpg.bind_item_theme(display_tag, "theme_locked_text")
    if unit_text:
      p(unit_text)
def make_lock_pair_float(label_text: str, input_tag: str, display_tag: str,
                         *, width: int = -1, default_value: float = 30.0, step: float = 0.01,
                         cb=None, unit_text: str | None = None):
  with dpg.group(horizontal=True):
    dpg.add_input_float(tag=input_tag, default_value=default_value, width=width,
                        step=step, min_value=0.01, min_clamped=True, format="%.2f",
                        callback=cb or (lambda s, a: None))
    p("", tag=display_tag, show=False)
    dpg.bind_item_theme(display_tag, "theme_locked_text")
    if unit_text:
      p(unit_text)
def apply_lock_pair(input_tag: str, display_tag: str, locked: bool, *, suffix: str = ""):
  if locked:
    val = dpg.get_value(input_tag)
    s = f"{int(val)}{suffix}" if isinstance(val, int) or (isinstance(val, float) and val.is_integer()) else f"{val}{suffix}"
    dpg.set_value(display_tag, s)
    dpg.configure_item(input_tag, show=False)
    dpg.configure_item(display_tag, show=True)
  else:
    dpg.configure_item(display_tag, show=False)
    dpg.configure_item(input_tag, show=True)