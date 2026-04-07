"""Detect which Valorant map is currently being played.

Uses OpenCV template matching against reference minimap images stored in
`data/map_templates/<map_name>.png`.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


class MapDetector:
    def __init__(self, templates_dir: str | Path):
        self.templates_dir = Path(templates_dir)
        self.templates: dict[str, np.ndarray] = self._load_templates()

    def _load_templates(self) -> dict[str, np.ndarray]:
        templates = {}
        if not self.templates_dir.exists():
            return templates
        for path in self.templates_dir.glob("*.png"):
            img = cv2.imread(str(path))
            if img is not None:
                templates[path.stem.lower()] = img
        return templates

    def detect_map(self, minimap_img: np.ndarray, threshold: float = 0.55) -> str | None:
        """Return the detected map name, or None if no confident match."""
        if not self.templates:
            return None

        best_name = None
        best_score = 0.0

        for name, template in self.templates.items():
            # Resize template to match the live minimap if needed
            t = template
            if t.shape[:2] != minimap_img.shape[:2]:
                t = cv2.resize(t, (minimap_img.shape[1], minimap_img.shape[0]))
            result = cv2.matchTemplate(minimap_img, t, cv2.TM_CCOEFF_NORMED)
            score = float(result.max())
            if score > best_score:
                best_score = score
                best_name = name

        return best_name if best_score >= threshold else None
