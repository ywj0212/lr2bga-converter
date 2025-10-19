import dearpygui.dearpygui as dpg
import subprocess, os
import tkinter as tk
from tkinter import filedialog

from env import IS_MAC
from util import nfc
from states import set_state
from cmdline import update_command, update_estimated_size

def _mac_choose_file(prompt="원본 파일 선택"):
  # Finder 네이티브 파일 선택
  script = f'POSIX path of (choose file with prompt "{prompt}")'
  r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
  return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None
def _mac_choose_folder(prompt="출력 폴더 선택"):
  script = f'POSIX path of (choose folder with prompt "{prompt}")'
  r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
  return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None
def _tk_choose_file():
  root = tk.Tk(); root.withdraw()
  path = filedialog.askopenfilename(title="원본 파일 선택")
  root.destroy()
  return path or None
def _tk_choose_folder():
  root = tk.Tk(); root.withdraw()
  path = filedialog.askdirectory(title="출력 폴더 선택")
  root.destroy()
  return path or None
def pick_file_native():
  if IS_MAC:
    return _mac_choose_file()
  return _tk_choose_file()
def pick_folder_native():
  if IS_MAC:
    return _mac_choose_folder()
  return _tk_choose_folder()
def open_file_native(sender=None, app_data=None, user_data=None):
  path = pick_file_native()
  if not path:
    return
  path = os.path.abspath(path)

  # 입력 파일 경로/이름 반영
  dpg.set_value("in_path", nfc(path))
  set_state("input_path", path)
  base = os.path.splitext(os.path.basename(path))[0]
  dpg.set_value("out_name", nfc(base))
  set_state("output_name", base)

  # * 입력 파일과 같은 폴더를 출력 폴더로 자동 설정
  out_dir = os.path.dirname(path)
  dpg.set_value("out_dir", nfc(out_dir))
  set_state("output_dir", out_dir)

  # 프리뷰/예상 사이즈 갱신
  update_command()
  update_estimated_size()
def open_dir_native(sender=None, app_data=None, user_data=None):
  path = pick_folder_native()
  if not path:
    return
  dpg.set_value("out_dir", nfc(path))
  set_state("output_dir", path)
  update_command()
  update_estimated_size()
