# ui_map.py
from typing import Optional, Protocol, Any

# ── 콜러블 시그니처 정의 (mypy/pyright 친화)
class LogAppendFn(Protocol):
  def __call__(self, msg: str) -> None: ...

class LogClearFn(Protocol):
  def __call__(self) -> None: ...

class SetProgressFn(Protocol):
  def __call__(self, frac: float) -> None: ...

class SetServiceMsgFn(Protocol):
  def __call__(self, msg_or_key: str, **fmt: Any) -> None: ...

class SetConvertButtonsActiveFn(Protocol):
  def __call__(self, active: bool) -> None: ...


# ── 기본은 no-op (키워드 인수도 안전하게 수용)
log_append: LogAppendFn = lambda msg: None
log_clear: LogClearFn = lambda: None
set_progress: SetProgressFn = lambda frac: None
set_service_msg: SetServiceMsgFn = lambda msg_or_key, **fmt: None
set_convert_buttons_active: SetConvertButtonsActiveFn = lambda active: None


def bind_ui(
  log_append_fn: Optional[LogAppendFn] = None,
  log_clear_fn: Optional[LogClearFn] = None,
  set_progress_fn: Optional[SetProgressFn] = None,
  set_service_msg_fn: Optional[SetServiceMsgFn] = None,
  set_convert_buttons_active_fn: Optional[SetConvertButtonsActiveFn] = None,
) -> None:
  """convert가 호출할 UI 함수들을 런타임에 주입."""
  global log_append, log_clear, set_progress, set_service_msg, set_convert_buttons_active

  if log_append_fn is not None:
    log_append = log_append_fn
  if log_clear_fn is not None:
    log_clear = log_clear_fn
  if set_progress_fn is not None:
    set_progress = set_progress_fn
  if set_service_msg_fn is not None:
    set_service_msg = set_service_msg_fn
  if set_convert_buttons_active_fn is not None:
    set_convert_buttons_active = set_convert_buttons_active_fn
