import dearpygui.dearpygui as dpg
import os, subprocess, re, math, json
from typing import Tuple

from src.states import get_state, set_update_callback, ffmpeg_cmd
from src.env import path_native, get_ffmpeg_path, get_ffprobe_path
from src.util import nfc, bytes_to_human
from src import i18n

LETTERBOX_TOLERANCE_PX = 5

def is_letterbox_needed(state) -> bool:
  try:
    w = int(state.get("width", 0))
    h = int(state.get("height", 0))
    src_w = int(state.get("source_width", 0))
    src_h = int(state.get("source_height", 0))
  except Exception:
    return True
  if w <= 0 or h <= 0 or src_w <= 0 or src_h <= 0:
    return True
  scaled_w = round(h * src_w / src_h)
  scaled_h = round(w * src_h / src_w)
  return not (
    abs(scaled_w - w) <= LETTERBOX_TOLERANCE_PX and
    abs(scaled_h - h) <= LETTERBOX_TOLERANCE_PX
  )

def _normalize_letterbox_color(state) -> tuple[int, int, int]:
  raw = state.get("letterbox_color", (0, 0, 0))
  if isinstance(raw, (list, tuple)) and len(raw) >= 3:
    try:
      r, g, b = raw[:3]
      return (
        max(0, min(255, int(round(r)))),
        max(0, min(255, int(round(g)))),
        max(0, min(255, int(round(b))))
      )
    except Exception:
      pass
  return (0, 0, 0)


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
def ffprobe_video_resolution(path: str) -> Tuple[int, int]:
    if not path or not os.path.exists(path):
        return (0, 0)

    def _run(cmd: list[str]) -> str:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).strip()

    ffprobe = get_ffprobe_path()

    # 1) 빠른 경로: stream-level width/height (+probe/analyze 증대)
    try:
        cmd1 = [
            ffprobe,
            "-v", "error",
            "-probesize", "50M",
            "-analyzeduration", "50M",
            "-select_streams", "v:0",
            "-show_entries", "stream=codec_type,width,height,coded_width,coded_height",
            "-of", "json",
            path_native(path),
        ]
        data = json.loads(_run(cmd1))
        streams = data.get("streams", [])
        for st in streams:
            if st.get("codec_type") != "video":
                continue
            w = int(st.get("width") or 0)
            h = int(st.get("height") or 0)
            if w > 0 and h > 0:
                return (w, h)
            # fallback to coded_* if display size가 비어있을 때
            cw = int(st.get("coded_width") or 0)
            ch = int(st.get("coded_height") or 0)
            if cw > 0 and ch > 0:
                return (cw, ch)
    except Exception:
        pass

    # 2) 최후 수단: 첫 프레임을 살짝 디코드해서 frame-level width/height 얻기
    #   -read_intervals %+#1 : 첫 구간 1프레임만
    try:
        cmd2 = [
            ffprobe,
            "-v", "error",
            "-read_intervals", "%+#1",
            "-select_streams", "v:0",
            "-show_entries", "frame=width,height",
            "-of", "csv=p=0:s=x",
            path_native(path),
        ]
        out = _run(cmd2)
        # 예: "720x480" (여러 줄일 수 있으므로 첫 줄만)
        if out:
            line = out.splitlines()[0].strip()
            if "x" in line:
                w_str, h_str = line.split("x", 1)
                return (int(float(w_str)), int(float(h_str)))
    except Exception:
        pass

    return (0, 0)

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
  codec = state.get("codec", "MPEG1")
  use_h264 = (codec == "H.264")
  inpath = path_native(state["input_path"] or "<input>")
  outdir = path_native(state["output_dir"] or "<out_dir>")
  outname = state["output_name"] or "output"
  ext = "mp4" if use_h264 else "mpg"
  container = "mp4" if use_h264 else "mpeg"
  outpath = path_native(os.path.join(outdir, f"{outname}.{ext}"))

  vf = f'scale={w}:{h}:force_original_aspect_ratio=decrease,' \
       f'pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps}'
  lines = [
    f'{os.path.basename(get_ffmpeg_path())} -hide_banner -y -fflags +genpts \\\n',
    f'  -i "{inpath}" \\\n',
    f'  -filter:v "{vf}" \\\n',
    f'  -r {fps} -fps_mode cfr \\\n',
  ]
  if use_h264:
    lines.append('  -c:v libx264 -pix_fmt yuv420p \\\n')
  else:
    lines.append('  -c:v mpeg1video -pix_fmt yuv420p \\\n')
  lines.append('  -g 18 -keyint_min 1 -bf 2 -sc_threshold 40 \\\n')
  lines.append(
    f'  -b:v {br}k -minrate {br}k -maxrate {br}k -bufsize {buf}k \\\n'
  )
  if use_h264:
    lines.append('  -movflags +faststart \\\n')
    lines.append(f'  -an -f {container} \\\n')
  else:
    lines.append(f'  -muxrate {mux}k -an -f {container} \\\n')
  lines.append(f'  "{outpath}"')
  _cmd = "".join(lines)
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
def _build_letterbox_filter(state, fps: float) -> tuple[str, str, str | None]:
  w = int(state.get("width", 0))
  h = int(state.get("height", 0))
  if w <= 0 or h <= 0:
    return ("filter:v", f'scale={w}:{h},setsar=1,fps={fps}', None)

  if not is_letterbox_needed(state):
    vf = f'scale={w}:{h},setsar=1,fps={fps}'
    return ("filter:v", vf, None)

  mode = str(state.get("letterbox_mode", "black") or "black").lower()
  if mode == "blur":
    radius = state.get("letterbox_blur_radius", 20)
    try:
      radius = int(radius)
    except Exception:
      radius = 20
    radius = max(4, min(120, radius))
    brightness = state.get("letterbox_blur_brightness", 100)
    try:
      brightness = int(brightness)
    except Exception:
      brightness = 100
    brightness = max(20, min(100, brightness))
    brightness_factor = brightness / 100.0
    brightness_filter = ""
    if brightness < 100:
      brightness_expr = f"{brightness_factor:.3f}".rstrip("0").rstrip(".")
      if not brightness_expr:
        brightness_expr = "1"
      brightness_filter = f",lutyuv=y='val*{brightness_expr}':u=val:v=val"
    vf = (
      f'[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,'
      f'crop={w}:{h}:(iw-ow)/2:(ih-oh)/2,boxblur={radius}{brightness_filter}[lb_bg];'
      f'[0:v]scale={w}:{h}:force_original_aspect_ratio=decrease[lb_fg];'
      f'[lb_bg][lb_fg]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2,'
      f'setsar=1,fps={fps}[vout]'
    )
    return ("filter_complex", vf, "[vout]")

  pad = f'pad={w}:{h}:(ow-iw)/2:(oh-ih)/2'
  if mode == "solid":
    r, g, b = _normalize_letterbox_color(state)
    pad = f'{pad}:color=0x{r:02x}{g:02x}{b:02x}'

  vf = (
    f'scale={w}:{h}:force_original_aspect_ratio=decrease,'
    f'{pad},setsar=1,fps={fps}'
  )
  return ("filter:v", vf, None)
def build_ffmpeg_args(*, override_mux_k: int | None = None, override_outpath: str | None = None) -> list[str]:
  state = get_state()
  w = state["width"]
  h = state["height"]
  fps = state["fps"] if not state["fps_locked"] else 30
  br = state["bitrate_k"]
  buf = state["buffer_k"] if not state["buffer_locked"] else 2900
  codec = state.get("codec", "MPEG1")
  use_h264 = (codec == "H.264")
  mux = override_mux_k if override_mux_k is not None else state["mux_k"]
  if not use_h264:
    mux = quant50_up(int(mux))  # 50k 정렬

  inpath = state["input_path"]
  outdir = state["output_dir"]
  outname = state["output_name"] or "output"
  ext = "mp4" if use_h264 else "mpg"
  outpath = override_outpath if override_outpath else os.path.join(outdir if outdir else ".", f"{outname}.{ext}")

  vf = f"scale={w}:{h}:force_original_aspect_ratio=decrease," \
       f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps}"

  args = [
    get_ffmpeg_path(), "-hide_banner", "-y", "-fflags", "+genpts",
    "-i", path_native(inpath) if inpath else "IN.MP4",
    "-filter:v", vf,
    "-r", str(fps), "-fps_mode", "cfr",
    "-c:v", "libx264" if use_h264 else "mpeg1video", "-pix_fmt", "yuv420p",
    "-g", "18", "-keyint_min", "1", "-bf", "2", "-sc_threshold", "40",
    "-b:v", f"{br}k", "-minrate", f"{br}k", "-maxrate", f"{br}k", "-bufsize", f"{buf}k",
  ]
  if use_h264:
    args.extend([
      "-movflags", "+faststart",
      "-an", "-f", "mp4", path_native(outpath)
    ])
  else:
    args.extend([
      "-muxrate", f"{mux}k",
      "-an", "-f", "mpeg", path_native(outpath)
    ])
  return args
