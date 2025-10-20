import dearpygui.dearpygui as dpg
import os
from src.env import IS_MAC, resource_path

CJK_FONT_BOLD_PATH    = resource_path("fonts/PretendardJP-Bold.otf")
CJK_FONT_REGULAR_PATH = resource_path("fonts/PretendardJP-Regular.otf")
MONO_FONT_PATH        = resource_path("fonts/D2Coding-Ver1.3.2-20180524.ttf")

VIR_EM_SIZE     = 30 if IS_MAC else 25
H1_SIZE         = int(1.4 * VIR_EM_SIZE)
H2_SIZE         = int(1.2 * VIR_EM_SIZE)
P_SIZE          = int(1.0 * VIR_EM_SIZE)
SM_SIZE         = int(0.6 * VIR_EM_SIZE)
PHY_EM_SIZE     = 21
GLOBAL_SCALE    = (PHY_EM_SIZE/VIR_EM_SIZE)

# KS X 1001 완성형 한글 2,350자 유니코드 구간 & 일본어 문자 세트
from src.codepoints import KSX1001_HANGUL_RANGES, JAPANESE_MIN_RANGES

def setup():
  dpg.create_context()
  dpg.set_global_font_scale(GLOBAL_SCALE)

  # ───────────────── 폰트 생성 ─────────────────
  with dpg.font_registry():
    if not (os.path.exists(CJK_FONT_BOLD_PATH) 
            and os.path.exists(CJK_FONT_REGULAR_PATH)):
      raise FileNotFoundError("필요한 폰트가 존재하지 않습니다.")
    
    fonts = [
      # { "tag": "h1",   "path": CJK_FONT_BOLD_PATH,    "size": H1_SIZE, "range": "compact" },
      # { "tag": "h2",   "path": CJK_FONT_BOLD_PATH,    "size": H2_SIZE, "range": "compact" },
      { "tag": "p",    "path": CJK_FONT_REGULAR_PATH, "size": P_SIZE,  "range": "full" },
      { "tag": "mono", "path": MONO_FONT_PATH,        "size": SM_SIZE, "range": "full" },
    ]

    for f in fonts:  
      with dpg.font(f["path"], f["size"], tag=f["tag"]):
        if f["range"] == "full":
          dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
          dpg.add_font_range_hint(dpg.mvFontRangeHint_Korean)
          dpg.add_font_range_hint(dpg.mvFontRangeHint_Japanese)
          dpg.add_font_chars(KSX1001_HANGUL_RANGES)
          dpg.add_font_chars(JAPANESE_MIN_RANGES)
          dpg.add_font_range(0x2000, 0x206F)   # General Punctuation
          dpg.add_font_range(0x3000, 0x303F)   # CJK Symbols and Punctuation
        else:
          dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
          dpg.add_font_chars(KSX1001_HANGUL_RANGES)
          dpg.add_font_chars(JAPANESE_MIN_RANGES)
    dpg.bind_font("p")

  # ───────────────── 버튼 테마 ─────────────────
  with dpg.theme(tag="theme_primary_button"):
    with dpg.theme_component(dpg.mvButton):
      dpg.add_theme_color(dpg.mvThemeCol_Button, (40, 120, 220, 255))          # 기본
      dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (50, 150, 255, 255))   # 마우스 오버
      dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 90, 180, 255))     # 클릭 중
      dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))           # 텍스트 색

  with dpg.theme(tag="theme_danger_button"):
    with dpg.theme_component(dpg.mvButton):
      dpg.add_theme_color(dpg.mvThemeCol_Button, (200, 60, 60, 255))
      dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (230, 80, 80, 255))
      dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (160, 40, 40, 255))
      dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))

  # ───────────────── 잠금 테마 ─────────────────
  with dpg.theme(tag="theme_locked_text"):
    with dpg.theme_component(dpg.mvAll):
      dpg.add_theme_style(dpg.mvStyleVar_Alpha, 0.45, category=dpg.mvThemeCat_Core)
    with dpg.theme_component(dpg.mvText):
      dpg.add_theme_color(dpg.mvThemeCol_Text, (150, 150, 150, 255))