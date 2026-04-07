"""Find the player icon on the minimap and map it to a callout."""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np


class PositionDetector:
    def __init__(self, callouts_dir: str | Path, hsv_lower, hsv_upper):
        self.callouts_dir = Path(callouts_dir)
        self.hsv_lower = np.array(hsv_lower, dtype=np.uint8)
        self.hsv_upper = np.array(hsv_upper, dtype=np.uint8)
        self._callouts_cache: dict[str, dict] = {}

    # ---------- player icon detection ----------
    def find_player_position(self, minimap_img: np.ndarray) -> tuple[int, int] | None:
        """Return (x, y) of the player's icon in minimap coordinates, or None."""
        hsv = cv2.cvtColor(minimap_img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.hsv_lower, self.hsv_upper)
        # Clean up noise
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) < 8:
            return None
        M = cv2.moments(largest)
        if M["m00"] == 0:
            return None
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        return cx, cy

    # ---------- callout lookup ----------
    def _load_callouts(self, map_name: str) -> dict:
        if map_name in self._callouts_cache:
            return self._callouts_cache[map_name]
        path = self.callouts_dir / f"{map_name.lower()}.json"
        if not path.exists():
            self._callouts_cache[map_name] = {}
            return {}
        data = json.loads(path.read_text())
        self._callouts_cache[map_name] = data
        return data

    def get_callout(self, map_name: str, position: tuple[int, int]) -> str:
        """Return the callout name for a given minimap position."""
        callouts = self._load_callouts(map_name)
        for name, polygon in callouts.items():
            if name.startswith("_"):  # skip comment keys
                continue
            pts = np.array(polygon, dtype=np.int32)
            if cv2.pointPolygonTest(pts, position, False) >= 0:
                return name
        return "Unknown"
