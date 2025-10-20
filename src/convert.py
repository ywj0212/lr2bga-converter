# convert.py
import dearpygui.dearpygui as dpg
import os, tempfile, re, subprocess, threading, signal

from src.env import IS_WINDOWS, get_ffmpeg_path, get_ffprobe_path
from src.states import global_state
from src.cmdline import build_ffmpeg_args, ffprobe_duration_sec, quant50_up, \
     update_command

import src.ui_map as ui_map
from src.util import bytes_to_human

# ★ 모듈 전역 상태 (여기에서 선언)
current_proc = None
cancel_requested = False
probe_paths: set[str] = set()
current_outpath: str = ""
encoding_active = False

def make_temp_outpath(base_dir: str | None, outname: str, mux_k: int) -> str:
  if base_dir and os.path.isdir(base_dir):
    return os.path.join(base_dir, f".{outname}.probe_mux{mux_k}.tmp.mpg")
  return os.path.join(tempfile.gettempdir(), f"{outname}.probe_mux{mux_k}.tmp.mpg")

def safe_remove(path: str):
  try:
    if path and os.path.exists(path):
      os.remove(path)
  except Exception:
    pass

def ffmpeg_attempt_mux(mux_k: int, itr: int, *, final_output: bool) -> tuple[bool, bool, str]:
  global current_proc, current_outpath, probe_paths

  inpath = global_state["input_path"]
  outdir = global_state["output_dir"]
  outname = global_state["output_name"] or "output"

  outpath = os.path.join(outdir if outdir else ".", f"{outname}.mpg") if final_output \
            else make_temp_outpath(outdir, outname, mux_k)

  args = build_ffmpeg_args(override_mux_k=mux_k, override_outpath=outpath)
  dur = ffprobe_duration_sec(inpath)

  base_args = args.copy()
  if "-f" in base_args:
    f_idx = base_args.index("-f")
    cmd2 = base_args[:f_idx] + ["-progress", "pipe:1", "-nostats"] + base_args[f_idx:]
  else:
    cmd2 = base_args[:-1] + ["-progress", "pipe:1", "-nostats", base_args[-1]]

  if not final_output:
    ui_map.log_append(f"[TRY] MUX={quant50_up(mux_k)}k")
    ui_map.set_service_msg("msg.searching_mux", itr=itr, mux=mux_k)
  else:
    ui_map.log_append(f"[OUTPUT] MUX={quant50_up(mux_k)}k")
    ui_map.set_service_msg("msg.working")

  dpg.set_value("mux_input", mux_k)
  ui_map.set_progress(0.0)

  if cancel_requested:
    safe_remove(outpath)
    return (False, False, outpath)

  prog_regex = re.compile(r"out_time=(\d+):(\d+):(\d+\.?\d*)")
  underflow_regex = re.compile(r"buffer underflow", re.IGNORECASE)

  current_outpath = outpath
  if not final_output:
    probe_paths.add(outpath)

  proc = subprocess.Popen(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
  current_proc = proc
  underflow_hit = False

  def reader_stdout():
    nonlocal underflow_hit
    for line in proc.stdout:  # type: ignore
      if cancel_requested:
        try: proc.terminate()
        except Exception: pass
        break
      s = line.strip()
      m = prog_regex.search(s)
      if m:
        hh, mm, ss = m.groups()
        secs = int(hh) * 3600 + int(mm) * 60 + float(ss)
        if dur > 0:
          ui_map.set_progress(min(1.0, secs / dur))
      if underflow_regex.search(s) and not underflow_hit:
        underflow_hit = True
        try: proc.terminate()
        except Exception: pass
        ui_map.log_append(f"  [WARN] {s}")
        break

  def reader_stderr():
    nonlocal underflow_hit
    for line in proc.stderr:  # type: ignore
      if cancel_requested:
        try: proc.terminate()
        except Exception: pass
        break
      s = line.rstrip()
      if underflow_regex.search(s) and not underflow_hit:
        underflow_hit = True
        try: proc.terminate()
        except Exception: pass
        ui_map.log_append(f"  [WARN] {s}")
        break

  t1 = threading.Thread(target=reader_stdout, daemon=True)
  t2 = threading.Thread(target=reader_stderr, daemon=True)
  t1.start(); t2.start()
  code = proc.wait()
  t1.join(); t2.join()
  # current_proc 해제는 cancel에서 kill 할 수 있으니 여기선 그대로 두거나 None 처리
  # current_proc = None

  if cancel_requested:
    safe_remove(outpath)
    ui_map.log_append("  [CANCEL] Cancelled by user")
    return (False, False, outpath)

  if underflow_hit:
    safe_remove(outpath)
    ui_map.log_append("  [ABORT] buffer underflow → stop & removed temp files")
    return (False, True, outpath)

  ui_map.set_progress(1.0)
  if code == 0:
    ui_map.log_append("  [OK] Done ffmpeg (No underflow)")
    return (True, False, outpath)
  else:
    safe_remove(outpath)
    ui_map.log_append(f"  [ERROR] ffmpeg exit code: {code}")
    return (False, False, outpath)

def find_min_safe_mux(start_mux_k: int, *, max_mux_k: int = 20000, max_attempts: int = 12) -> int | None:
  start_mux_k = quant50_up(int(start_mux_k))
  attempts = 0
  unlimited = (max_attempts is None) or (int(max_attempts) <= 0)

  def can_try() -> bool:
    return unlimited or (attempts < max_attempts)

  if cancel_requested:
    return None

  if not can_try():
    return None
  ok, uf, _ = ffmpeg_attempt_mux(start_mux_k, attempts+1, final_output=False)
  attempts += 1
  if cancel_requested:
    return None

  if ok and not uf:
    low_unsafe = 0
    high_safe = start_mux_k
  else:
    low_unsafe = start_mux_k
    step = 50
    cur = start_mux_k + step
    high_safe = None
    while can_try() and cur <= max_mux_k:
      if cancel_requested:
        return None
      ok, uf, _ = ffmpeg_attempt_mux(cur, attempts+1, final_output=False)
      attempts += 1
      if ok and not uf:
        high_safe = cur
        break
      low_unsafe = cur
      step *= 2
      cur = quant50_up(cur + step)
    if high_safe is None:
      ui_map.log_append("[FAIL] 안전 상한을 찾지 못함 (max_mux_k 초과)")
      return None

  while can_try() and (high_safe - low_unsafe) > 50:
    if cancel_requested:
      return None
    mid = quant50_up((low_unsafe + high_safe) // 2)
    if mid == high_safe or mid == low_unsafe:
      break
    ok, uf, _ = ffmpeg_attempt_mux(mid, attempts+1, final_output=False)
    attempts += 1
    if ok and not uf:
      high_safe = mid
    else:
      low_unsafe = mid

  return high_safe

def _terminate_proc(proc):
  if not proc:
    return
  try:
    if IS_WINDOWS:
      proc.terminate()
    else:
      proc.send_signal(signal.SIGTERM)
  except Exception:
    try:
      proc.terminate()
    except Exception:
      pass
  try:
    proc.wait(timeout=1.5)
  except Exception:
    try:
      proc.kill()
    except Exception:
      pass

def cancel_encoding(sender=None, app_data=None, user_data=None):
  global cancel_requested, current_outpath, probe_paths, current_proc
  cancel_requested = True
  ui_map.set_service_msg("msg.cancel_requested")
  _terminate_proc(current_proc)
  try:
    if current_outpath:
      safe_remove(current_outpath)
    for p in list(probe_paths):
      safe_remove(p)
      probe_paths.discard(p)
  except Exception:
    pass
  ui_map.set_convert_buttons_active(False)
  ui_map.log_append("[CANCEL] Cancelled by user")

def run_convert():
  ui_map.log_clear()
  if not global_state["input_path"] or not os.path.exists(global_state["input_path"]):
    ui_map.log_append("[ERROR] Invalid input file path!")
    ui_map.set_service_msg("msg.invalid_input")
    return
  if not global_state["output_dir"]:
    ui_map.log_append("[ERROR] Invalid output path!")
    ui_map.set_service_msg("msg.invalid_input")
    return

  def worker():
    global cancel_requested, probe_paths, current_outpath, encoding_active
    cancel_requested = False
    probe_paths = set()
    current_outpath = ""
    encoding_active = True
    ui_map.set_convert_buttons_active(True)

    try:
      start_mux = quant50_up(int(global_state["mux_k"]))
      auto = bool(dpg.get_value("mux_auto_chk")) if dpg.does_item_exist("mux_auto_chk") else bool(global_state.get("mux_auto", True))
      max_mux_k = quant50_up(int(global_state.get("bitrate_k", 0)) * 4)
      max_attempts = int(global_state.get("auto_max_attempts", 0))

      if auto:
        best = find_min_safe_mux(start_mux_k=start_mux, max_mux_k=max_mux_k, max_attempts=max_attempts)
        if cancel_requested:
          return
        if best is None:
          return

        global_state["mux_k"] = best
        if dpg.does_item_exist("mux_input"):
          dpg.set_value("mux_input", int(best))
        update_command()

        ui_map.log_append(f"[FINAL] Generating file with final safe MUX={best}k")
        ok, uf, outpath = ffmpeg_attempt_mux(best, 0, final_output=True)
        if cancel_requested:
          return
        if uf:
          ui_map.set_service_msg("msg.fail_underflow")
          ui_map.log_append("[FAIL] Underflow occurred!")
        elif not ok:
          ui_map.set_service_msg("msg.fail")
          ui_map.log_append("[FAIL] Failed to generate file")
        else:
          try:
            size_bytes = os.path.getsize(outpath) if outpath and os.path.exists(outpath) else 0
            # dpg.set_value("service_msg_text", f"변환 완료! (최종 파일 사이즈: {human})")
            ui_map.set_service_msg("msg.done", size=(bytes_to_human, size_bytes))
          except Exception:
            ui_map.set_service_msg("msg.done_nofs")
          ui_map.log_append("[DONE] Successfully generated file")
      else:
        update_command()
        ui_map.log_append(f"[FINAL] Generating file with user defined MUX={start_mux}k")
        ok, uf, outpath = ffmpeg_attempt_mux(start_mux, 0, final_output=True)
        if cancel_requested:
          return
        if uf:
          ui_map.set_service_msg("msg.fail_underflow")
          ui_map.log_append("[FAIL] Underflow occurred!")
        elif not ok:
          ui_map.set_service_msg("msg.fail")
          ui_map.log_append("[FAIL] Failed to generate file")
        else:
          try:
            size_bytes = os.path.getsize(outpath) if outpath and os.path.exists(outpath) else 0
            human = bytes_to_human(size_bytes)
            ui_map.set_service_msg("msg.done", size=(bytes_to_human, size_bytes))
          except Exception:
            ui_map.set_service_msg("msg.done_nofs")
          ui_map.log_append("[DONE] Successfully generated file")
    except Exception as e:
      ui_map.log_append(f"[EXC] {e}")
    finally:
      for p in list(probe_paths):
        safe_remove(p)
        probe_paths.discard(p)
      encoding_active = False
      ui_map.set_convert_buttons_active(False)

  threading.Thread(target=worker, daemon=True).start()

def run_convert_custom():
  if not dpg.does_item_exist("cmd_preview"):
    ui_map.log_append("[ERROR] No cmd_preview")
    return
  cmdline = (dpg.get_value("cmd_preview") or "").strip()
  if not cmdline:
    ui_map.log_append("[ERROR] Empty cmd line")
    return
  
  def worker():
    import shlex
    global cancel_requested, current_proc, current_outpath, probe_paths, encoding_active
    cancel_requested = False
    probe_paths = set()
    current_outpath = ""
    encoding_active = True
    ui_map.set_convert_buttons_active(True)

    try:
      args = shlex.split(cmdline, posix=(not IS_WINDOWS))
      if not args:
        ui_map.log_append("[ERROR] No parsed args")
        return

      exe_base = os.path.basename(args[0]).lower()
      if exe_base in ("ffmpeg", "ffmpeg.exe"):
        args[0] = get_ffmpeg_path()
      elif exe_base in ("ffprobe", "ffprobe.exe"):
        args[0] = get_ffprobe_path()

      is_ffmpeg = ("ffmpeg" in os.path.basename(args[0]).lower())
      if is_ffmpeg:
        insert_pos = 1
        if "-progress" not in args:
          args[insert_pos:insert_pos] = ["-progress", "pipe:1", "-nostats"]
          insert_pos += 3
        if "-y" not in args and "-n" not in args:
          args[insert_pos:insert_pos] = ["-y"]
          insert_pos += 1

      def guess_inputs(_args):
        ins = []
        for i, tok in enumerate(_args):
          if tok == "-i" and i + 1 < len(_args):
            ins.append(_args[i + 1])
        return ins

      def guess_output(_args):
        for tok in reversed(_args):
          if not tok.startswith("-") and not tok.startswith("pipe:"):
            return tok
        return ""

      inputs = guess_inputs(args) if is_ffmpeg else []
      outpath = guess_output(args) if is_ffmpeg else ""
      try:
        if outpath:
          outpath = os.path.abspath(outpath)
      except Exception:
        pass
      current_outpath = outpath
      dur = ffprobe_duration_sec(inputs[0]) if inputs else 0.0

      ui_map.log_append("[INFO] Executing custom command")
      ui_map.log_append(">> " + " ".join(args))
      ui_map.set_service_msg("msg.direct_running")

      prog_regex = re.compile(r"out_time=(\d+):(\d+):(\d+\.?\d*)")
      underflow_regex = re.compile(r"buffer underflow", re.IGNORECASE)

      proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
      current_proc = proc
      underflow_hit = False

      def reader_stdout():
        nonlocal underflow_hit
        for line in proc.stdout:  # type: ignore
          if cancel_requested:
            try: proc.terminate()
            except Exception: pass
            break
          s = (line or "").strip()
          m = prog_regex.search(s)
          if m and dur > 0:
            hh, mm, ss = m.groups()
            secs = int(hh) * 3600 + int(mm) * 60 + float(ss)
            ui_map.set_progress(min(1.0, secs / dur))
          if underflow_regex.search(s):
            underflow_hit = True
            ui_map.log_append(f"[WARN] {s}")
          else:
            ui_map.log_append(f"  [*] {s}")

      def reader_stderr():
        nonlocal underflow_hit
        for line in proc.stderr:  # type: ignore
          if cancel_requested:
            try: proc.terminate()
            except Exception: pass
            break
          s = (line or "").rstrip()
          if underflow_regex.search(s):
            underflow_hit = True
            ui_map.log_append(f"[WARN] {s}")
          else:
            ui_map.log_append(f"  [*] {s}")

      t1 = threading.Thread(target=reader_stdout, daemon=True)
      t2 = threading.Thread(target=reader_stderr, daemon=True)
      t1.start(); t2.start()
      code = proc.wait()
      t1.join(); t2.join()

      if cancel_requested:
        if current_outpath:
          safe_remove(current_outpath)
        ui_map.set_service_msg("msg.cancel_requested")
        ui_map.log_append("[CANCEL] Cancelled by user")
        return

      if code == 0:
        ui_map.set_progress(1.0)
        try:
          if current_outpath and os.path.exists(current_outpath):
            sz = os.path.getsize(current_outpath)
            if underflow_hit:
              ui_map.set_service_msg("msg.done_underflow", size=(bytes_to_human, sz))
            else:
              ui_map.set_service_msg("msg.done", size=(bytes_to_human, sz))

          else:
            if underflow_hit:
              ui_map.set_service_msg("msg.done_nofs_underflow")
            else:
              ui_map.set_service_msg("msg.done_nofs")
        except Exception:
          if underflow_hit:
            ui_map.set_service_msg("msg.done_nofs_underflow")
          else:
            ui_map.set_service_msg("msg.done_nofs")
        ui_map.log_append("[DONE] Successfully generated file")
      else:
        if current_outpath:
          safe_remove(current_outpath)
        ui_map.set_service_msg("msg.fail")
        ui_map.log_append(f"[ERROR] ffmpeg exit code: {code}")

    except Exception as e:
      ui_map.log_append(f"[EXC] {e}")
      try:
        if current_outpath:
          safe_remove(current_outpath)
      except Exception:
        pass
      ui_map.set_service_msg("msg.fail")
    finally:
      ui_map.set_convert_buttons_active(False)
      encoding_active = False

  threading.Thread(target=worker, daemon=True).start()
