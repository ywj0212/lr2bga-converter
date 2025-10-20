import unicodedata
import secrets, string

_generated_ids = set()
def random_string(length=9):
    alphabet = string.ascii_letters + string.digits
    while True:
        s = ''.join(secrets.choice(alphabet) for _ in range(length))
        if s not in _generated_ids:
            _generated_ids.add(s)
            return s

def nfc(s):
  if s is None:
    return ""
  if isinstance(s, bytes):
    s = s.decode("utf-8", errors="replace")
  return unicodedata.normalize("NFC", str(s))

def bytes_to_human(n: int) -> str:
  units = ["B", "KB", "MB", "GB", "TB"]
  s = float(n)
  i = 0
  while s >= 1024.0 and i < len(units) - 1:
    s /= 1024.0
    i += 1
  return f"{s:.2f} {units[i]}"