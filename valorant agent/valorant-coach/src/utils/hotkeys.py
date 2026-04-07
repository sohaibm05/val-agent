"""Global hotkey listener (F6 to toggle overlay)."""
from __future__ import annotations

from typing import Callable

try:
    from pynput import keyboard
except ImportError:
    keyboard = None


class HotkeyListener:
    def __init__(self, toggle_key: str = "<f6>", on_toggle: Callable[[], None] | None = None):
        if keyboard is None:
            raise RuntimeError("pynput is not installed. Run: pip install pynput")
        self.on_toggle = on_toggle or (lambda: None)
        self._listener = keyboard.GlobalHotKeys({toggle_key: self.on_toggle})

    def start(self) -> None:
        self._listener.start()

    def stop(self) -> None:
        self._listener.stop()
