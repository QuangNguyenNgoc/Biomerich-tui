"""
Stub replacement for the deprecated Eel/WebSocket bridge.

The original bridge.py provided FastAPI + WebSocket + pywebview integration.
It has been archived to deprecated/bridge.py.

This stub provides no-op replacements so that existing core modules
(e.g. ram_trim.py) that import `from core import bridge as eel` don't crash
during the transition to TUI. All eel.js_* calls become silent no-ops.
"""


class _JsNoOp:
    """Returns a callable no-op for any attribute access, mimicking eel.js_xxx()()."""

    def __call__(self, *args, **kwargs):
        return self

    def __getattr__(self, name):
        return self


_noop = _JsNoOp()


def init(*args, **kwargs):
    """No-op: web root initialization is no longer needed."""
    pass


def start(*args, **kwargs):
    """No-op: the Eel server loop is replaced by the TUI app."""
    pass


def expose(fn=None, *, name=None):
    """No-op decorator: @eel.expose is no longer needed."""
    if fn is None:
        return lambda f: f
    return fn


def __getattr__(name: str):
    """Any eel.js_xxx(...) call returns a silent no-op callable."""
    if name.startswith("js_"):
        return _noop
    raise AttributeError(f"module 'core.bridge' has no attribute {name!r}")
