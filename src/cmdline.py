import dearpygui.dearpygui as dpg
import os, subprocess, re, math

from src.states import get_state, set_update_callback, ffmpeg_cmd
from src.env import path_native, get_ffmpeg_path, get_ffprobe_path
from src.util import nfc, bytes_to_human
from src import i18n

def ffprobe_duration_sec(path: str) -> float:
  if not path or not os.path.exists(path):
    return 0.0
  try:
    cmd = [
      get_ffprobe_path(),
      "-v", "error",
      "-show_entries", "format=duration",
      "-of", "default=noprint_wrappers=1:nokey=1",
      path_native(path),
    ]
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).strip()
    return float(out) if out else 0.0
  except Exception:
    return 0.0

def _fmt_estimated_size_value() -> str:
  """'{size}' 치환값을 동적으로 계산해 반환."""
  est = estimate_output_size_bytes()  # 이미 있는 함수
  return i18n.t("msg.size_dash") if est is None else bytes_to_human(est)
def estimate_output_size_bytes() -> int | None:
  state = get_state()
  dur = ffprobe_duration_sec(state.get("input_path", ""))
  if not dur or dur <= 0:
    return None
  
  br_k = int(state.get("bitrate_k", 0))
  # mux_k = int(state.get("mux_k", 0))
  # eff_kbps = max(br_k, mux_k)
  eff_kbps = br_k

  # ffmpeg의 k는 1000 기준
  bytes_est = int((eff_kbps * 1000 / 8.0) * dur)
  return max(0, bytes_est)

def update_estimated_size():
  if not dpg.does_item_exist("est_size_text"):
      return
  # 현재 언어 기준으로 즉시 포맷해서 세팅
  txt = i18n.t("label.estimated_size", size=_fmt_estimated_size_value())
  dpg.set_value("est_size_text", txt)
i18n.on_change(lambda _lang: update_estimated_size())
def update_command():
  state = get_state()
  global ffmpeg_cmd

  w = state["width"]; h = state["height"]
  fps = state["fps"] if not state["fps_locked"] else 30
  br = state["bitrate_k"]
  buf = state["buffer_k"] if not state["buffer_locked"] else 2900
  mux = state["mux_k"]
  inpath = path_native(state["input_path"] or "<input>")
  outdir = path_native(state["output_dir"] or "<out_dir>")
  outname = state["output_name"] or "output"
  outpath = path_native(os.path.join(outdir, f"{outname}.mpg"))

  vf = f'scale={w}:{h}:force_original_aspect_ratio=decrease,' \
       f'pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps}'
  _cmd = (
    f'{os.path.basename(get_ffmpeg_path())} -hide_banner -y -fflags +genpts \\\n'
    f'  -i "{inpath}" \\\n'
    f'  -filter:v "{vf}" \\\n'
    f'  -r {fps} -fps_mode cfr \\\n'
    f'  -c:v mpeg1video -pix_fmt yuv420p \\\n'
    f'  -g 18 -keyint_min 1 -bf 2 -sc_threshold 40 \\\n'
    f'  -b:v {br}k -minrate {br}k -maxrate {br}k -bufsize {buf}k \\\n'
    f'  -muxrate {mux}k -an -f mpeg \\\n'
    f'  "{outpath}"'
  )
  if dpg.does_item_exist("cmd_preview"):
    dpg.set_value("cmd_preview", nfc(_cmd))
  ffmpeg_cmd = _cmd
  update_estimated_size()
set_update_callback(update_command)

def quant50_up(k: int) -> int:
  """50k 단위 상향 양자화 (2134 -> 2150)"""
  return int(math.ceil(k / 50.0)) * 50
def quant50_down(k: int) -> int:
  """50k 단위 하향 양자화 (2134 -> 2100)"""
  return (int(k) // 50) * 50
def _sanitize_cmdline(s: str) -> str:
  s = s.replace("\r\n", "\n").replace("\r", "\n")
  s = re.sub(r"[\\^]\s*\n", " ", s)
  s = s.replace("\n", " ")
  return s.strip()
def build_ffmpeg_args(*, override_mux_k: int | None = None, override_outpath: str | None = None) -> list[str]:
  state = get_state()
  w = state["width"]
  h = state["height"]
  fps = state["fps"] if not state["fps_locked"] else 30
  br = state["bitrate_k"]
  buf = state["buffer_k"] if not state["buffer_locked"] else 2900
  mux = override_mux_k if override_mux_k is not None else state["mux_k"]
  mux = quant50_up(int(mux))  # 50k 정렬

  inpath = state["input_path"]
  outdir = state["output_dir"]
  outname = state["output_name"] or "output"
  outpath = override_outpath if override_outpath else os.path.join(outdir if outdir else ".", f"{outname}.mpg")

  vf = f"scale={w}:{h}:force_original_aspect_ratio=decrease," \
       f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps}"

  args = [
    get_ffmpeg_path(), "-hide_banner", "-y", "-fflags", "+genpts",
    "-i", path_native(inpath) if inpath else "IN.MP4",
    "-filter:v", vf,
    "-r", str(fps), "-fps_mode", "cfr",
    "-c:v", "mpeg1video", "-pix_fmt", "yuv420p",
    "-g", "18", "-keyint_min", "1", "-bf", "2", "-sc_threshold", "40",
    "-b:v", f"{br}k", "-minrate", f"{br}k", "-maxrate", f"{br}k", "-bufsize", f"{buf}k",
    "-muxrate", f"{mux}k",
    "-an", "-f", "mpeg", path_native(outpath)
  ]
  return args
