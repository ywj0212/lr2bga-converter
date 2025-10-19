from config import get_lang_pref, set_lang_pref
from ui_setup import setup
from ui import init_ui
import i18n

if __name__=="__main__":
  pref = get_lang_pref()
  i18n.init(pref)
  i18n.on_change(set_lang_pref)

  setup()
  init_ui()
