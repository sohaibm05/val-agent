"""Screen capture module — grabs the Valorant minimap region."""
from __future__ import annotations

import numpy as np

try:
    import mss
except ImportError:  # Allow import without mss installed (for docs/tests)
    mss = None


class ScreenCapture:
    """Lightweight minimap grabber using `mss`.

    The minimap in Valorant is fixed in the top-left corner of the screen.
    Configure the region once via `calibration.py` and reuse it here.
    """

    def __init__(self, region: dict):
        """region = {"left": int, "top": int, "width": int, "height": int}"""
        if mss is None:
            raise RuntimeError("mss is not installed. Run: pip install mss")
        self.region = region
        self.sct = mss.mss()

    def grab_minimap(self) -> np.ndarray:
        """Return the minimap as a BGR NumPy array (H, W, 3)."""
        raw = self.sct.grab(self.region)
        img = np.array(raw)[:, :, :3]  # drop alpha
        return img  # already BGR from mss

    def close(self) -> None:
        self.sct.close()
