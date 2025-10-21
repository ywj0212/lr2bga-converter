from typing import Any, Callable, Dict, Optional

global_state = {
  "input_path": "",
  "output_dir": "",
  "output_name": "",
  "res_preset": "512x512",
  "width": 512,
  "height": 512,
  "fps_locked": True,
  "fps": 30,
  "bitrate_k": 1600,
  "buffer_locked": True,
  "buffer_k": 2900,
  "mux_k": 2100,
  "mux_auto": True,
  "codec": "MPEG1",
  "source_width": 0,
  "source_height": 0,
  "verbose": True,
  "auto_max_attempts": 0
}
ffmpeg_cmd = "";
_on_change: Optional[Callable[[], None]] = None

def set_update_callback(cb: Callable[[], None]) -> None:
  global _on_change
  _on_change = cb

def get_state() -> Dict[str, Any]:
  return global_state

def set_state(key: str, value: Any) -> None:
  global_state[key] = value
  if _on_change is not None:
    _on_change()