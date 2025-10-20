# config.py
import json, os
from pathlib import Path
from src.env import IS_WINDOWS, IS_MAC

def user_config_dir() -> Path:
    if IS_WINDOWS:
      base = os.environ.get("APPDATA")
    elif IS_MAC:
      base = os.path.expanduser("~/Library/Application Support")
    else:
      base = os.path.expanduser("~/.config")
    if base is None:
      raise Exception
    # ↓ 프로젝트 폴더명 확인 (기존 코드가 'l2rbga'였는데 오타면 'lr2bga'로 바꾸세요)
    p = Path(base) / "lr2bga"
    p.mkdir(parents=True, exist_ok=True)
    return p

CFG = user_config_dir() / "config.json"

def load_cfg() -> dict:
  try:
    return json.loads(CFG.read_text("utf-8")) if CFG.exists() else {}
  except Exception:
    return {}

def save_cfg(d) -> None:
  CFG.write_text(json.dumps(d, ensure_ascii=False, indent=2), "utf-8")


# ───────── 언어 설정 전용 헬퍼 ─────────
_SUPPORTED_LANGS = {"ko", "en", "ja"}

def get_lang_pref(default: str | None = None) -> str | None:
  """config.json에서 선택 언어(ko/en/ja)를 읽어온다. 없거나 잘못되면 default 반환."""
  cfg = load_cfg()
  lang = cfg.get("lang")
  return lang if isinstance(lang, str) and lang in _SUPPORTED_LANGS else default

def set_lang_pref(lang: str) -> None:
  """선택 언어를 config.json에 저장(ko/en/ja만 유효)."""
  if lang not in _SUPPORTED_LANGS:
    return
  cfg = load_cfg()
  cfg["lang"] = lang
  save_cfg(cfg)
