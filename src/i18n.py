# i18n.py
import os, json, locale
from typing import Any, Dict, List, Optional, Callable
import dearpygui.dearpygui as dpg
from src.env import resource_path

# ────────────────────────────── fmt 평가 ──────────────────────────────
def _eval_fmt(fmt: dict | None) -> dict:
  if not fmt:
    return {}
  out = {}
  for k, v in fmt.items():
    if callable(v):
      out[k] = v()
    elif isinstance(v, tuple) and v and callable(v[0]):
      f, *args = v
      out[k] = f(*args)
    else:
      out[k] = v
  return out

# ────────────────────────────── 로딩/초기화 ──────────────────────────────
_LANG = "en"
LANG_CHOICES = ["한국어", "English", "日本語"]
NAME_TO_CODE = {"한국어": "ko", "English": "en", "日本語": "ja"}
CODE_TO_NAME = {v: k for k, v in NAME_TO_CODE.items()}
_DICT: Dict[str, Any] = {}

def pick_lang() -> str:
  try:
    locale.setlocale(locale.LC_CTYPE, "")
  except locale.Error:
    pass
  code = (locale.getlocale()[0] or "")
  if not code:
    code = os.environ.get("LANG", "en").split(".")[0]
  lang = code.split("_")[0].lower() if code else "en"
  return {"ko": "ko", "ja": "ja", "en": "en"}.get(lang, "en")
def load_dict(lang: str) -> Dict[str, Any]:
  path = resource_path(f"i18n/{lang}.json")
  if os.path.exists(path):
    with open(path, "r", encoding="utf-8") as f:
      return json.load(f)
  return {}
def init(lang: Optional[str] = None):
  global _LANG, _DICT
  _LANG = lang or pick_lang()
  _DICT = load_dict(_LANG)

# ────────────────────────────── 조회/치환 ──────────────────────────────
def _get_from_path(d: Dict[str, Any], dotted: str, default: Any = "") -> Any:
  cur = d
  for part in dotted.split("."):
    if isinstance(cur, dict) and part in cur:
      cur = cur[part]
    else:
      return default
  return cur
def t(key: str, **fmt) -> str:
  """문자열 반환. {name} 치환 + fmt의 함수/튜플 평가 지원"""
  val = _get_from_path(_DICT, key, key)
  if isinstance(val, (list, dict)):
    return str(val)
  try:
    if fmt:
      fmt = _eval_fmt(fmt)
      return str(val).format(**fmt)
    return str(val)
  except Exception:
    return str(val)
def t_list(key: str) -> List[str]:
  """리스트 반환 (없으면 빈 리스트)"""
  val = _get_from_path(_DICT, key, [])
  if isinstance(val, list):
    return [str(v) for v in val]
  return []

def current_lang() -> str:
  return _LANG

# ────────────────────────────── 바인딩 레지스트리 ──────────────────────────────
# kind: "value" → dpg.set_value(tag, text)
#     "label" → dpg.configure_item(tag, label=text)
#     "items" → dpg.configure_item(tag, items=[...])
_BINDINGS: List[Dict[str, Any]] = []
_ON_CHANGE: List[Callable[[str], None]] = []

def _upsert_binding(tag: str, kind: str, key: str, *, fmt: dict | None = None, post=None):
  # 같은 tag & kind가 있으면 교체(중복 방지)
  found = False
  for b in _BINDINGS:
    if b["tag"] == tag and b["kind"] == kind:
      b["key"] = key
      b["fmt"] = fmt or {}
      b["post"] = post
      found = True
      break
  if not found:
    _BINDINGS.append({"tag": tag, "key": key, "kind": kind, "fmt": fmt or {}, "post": post})
def bind_value(tag: str, key: str, **fmt):
  _upsert_binding(tag, "value", key, fmt=fmt)
def bind_label(tag: str, key: str, **fmt):
  _upsert_binding(tag, "label", key, fmt=fmt)
def bind_items(tag: str, key: str, post: Optional[Callable[[List[str]], List[str]]] = None):
  _upsert_binding(tag, "items", key, post=post)

def bind_text(tag: str, key: str, **fmt):
  bind_value(tag, key, **fmt)
def bind_item_label(tag: str, key: str, **fmt):
  bind_label(tag, key, **fmt)
def unbind(tag: str):
  """특정 tag 바인딩 제거"""
  global _BINDINGS
  _BINDINGS = [b for b in _BINDINGS if b["tag"] != tag]
def on_change(cb: Callable[[str], None]):
  _ON_CHANGE.append(cb)
def refresh():
  """현재 언어 기준으로 모든 바인딩 재적용"""
  for b in _BINDINGS:
    tag = b["tag"]
    kind = b["kind"]
    if not dpg.does_item_exist(tag):
      continue
    if kind == "value":
      txt = t(b["key"], **b.get("fmt", {}))
      dpg.set_value(tag, txt)
    elif kind == "label":
      txt = t(b["key"], **b.get("fmt", {}))
      dpg.configure_item(tag, label=txt)
    elif kind == "items":
      arr = t_list(b["key"])
      post = b.get("post")
      if callable(post):
        arr = post(arr)
      dpg.configure_item(tag, items=arr)
def set_lang(lang: str):
  """언어 변경 + 전체 UI 갱신"""
  global _LANG, _DICT
  _LANG = lang
  _DICT = load_dict(lang)
  refresh()
  for cb in _ON_CHANGE:
    try:
      cb(lang)
    except Exception:
      pass

def add_text_i18n(
  key: str,
  *,
  tag: Optional[str] = None,
  parent: int | str | None = None,
  fmt: dict | None = None,
  **kwargs: Any
) -> str:
  txt = t(key, **(fmt or {}))
  _tag = tag or f"i18n_txt_{id(key)}_{len(_BINDINGS)}"
  params: Dict[str, Any] = {"tag": _tag, **kwargs}
  if parent is not None:
    params["parent"] = parent
  dpg.add_text(txt, **params)
  bind_value(_tag, key, **(fmt or {}))
  return _tag
def add_button_i18n(
  key: str,
  *,
  tag: Optional[str] = None,
  parent: int | str | None = None,
  callback: Optional[Callable[..., Any]] = None,
  fmt: dict | None = None,
  **kwargs: Any
) -> str:
  lbl = t(key, **(fmt or {}))
  _tag = tag or f"i18n_btn_{id(key)}_{len(_BINDINGS)}"
  params: Dict[str, Any] = {"label": lbl, "tag": _tag, **kwargs}
  if parent is not None:
    params["parent"] = parent
  if callback is not None:         # ← None이면 전달하지 않음
    params["callback"] = callback
  dpg.add_button(**params)
  bind_label(_tag, key, **(fmt or {}))
  return _tag
def add_checkbox_i18n(
  key: str,
  *,
  tag: Optional[str] = None,
  parent: int | str | None = None,
  default_value: bool = False,
  callback: Optional[Callable[..., Any]] = None,
  fmt: dict | None = None,
  **kwargs: Any
) -> str:
  lbl = t(key, **(fmt or {}))
  _tag = tag or f"i18n_chk_{id(key)}_{len(_BINDINGS)}"
  params: Dict[str, Any] = {
    "label": lbl,
    "tag": _tag,
    "default_value": default_value,
    **kwargs,
  }
  if parent is not None:
    params["parent"] = parent
  if callback is not None:
    params["callback"] = callback
  dpg.add_checkbox(**params)
  bind_label(_tag, key, **(fmt or {}))
  return _tag

def _apply_title(_):
  dpg.set_viewport_title(t("app.title"))
on_change(_apply_title)
