# env.py
import platform, os, sys, stat

IS_MAC = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"

def is_frozen_build() -> bool:
  """PyInstaller onefile로 패키징된 실행 여부"""
  return bool(getattr(sys, "frozen", False)) and hasattr(sys, "_MEIPASS")

def resource_path(p: str) -> str:
  """정적 리소스 경로. (빌드 시 _MEIPASS, 개발 시 현재 폴더)"""
  base = getattr(sys, "_MEIPASS", os.path.abspath(".")) if is_frozen_build() else os.path.abspath(".")
  return os.path.join(base, p)

def bin_path(name: str) -> str:
  return resource_path(os.path.join("bin", name))

def _ensure_exec_bit(path: str) -> None:
  """유닉스 계열에서 실행권한 없으면 추가(실패해도 무시)."""
  if not IS_WINDOWS and os.path.isfile(path) and not os.access(path, os.X_OK):
    try:
      st = os.stat(path)
      os.chmod(path, st.st_mode | stat.S_IXUSR)
    except Exception:
      pass

def get_ffmpeg_path() -> str:
  """
  - PyInstaller 빌드: 내장 bin/ffmpeg*(존재 시) 사용, 없으면 PATH의 ffmpeg로 폴백
  - 개발/비빌드: 무조건 PATH의 ffmpeg/ffmpeg.exe 사용
  """
  if is_frozen_build():
    cand = [bin_path("ffmpeg.exe")] if IS_WINDOWS else [bin_path("ffmpeg")]
    for c in cand:
      if os.path.isfile(c):
        _ensure_exec_bit(c)
        return c
  # 빌드가 아니면 항상 시스템 ffmpeg 사용
  return "ffmpeg.exe" if IS_WINDOWS else "ffmpeg"

def get_ffprobe_path() -> str:
  """
  - PyInstaller 빌드: 내장 bin/ffprobe*(존재 시) 사용, 없으면 PATH의 ffprobe로 폴백
  - 개발/비빌드: 무조건 PATH의 ffprobe/ffprobe.exe 사용
  """
  if is_frozen_build():
    cand = [bin_path("ffprobe.exe")] if IS_WINDOWS else [bin_path("ffprobe")]
    for c in cand:
      if os.path.isfile(c):
        _ensure_exec_bit(c)
        return c
  return "ffprobe.exe" if IS_WINDOWS else "ffprobe"

def path_native(p: str) -> str:
  """윈도우에서는 백슬래시로 정규화, 그 외는 원본 유지."""
  try:
    return os.path.normpath(p) if IS_WINDOWS else p
  except Exception:
    return p
