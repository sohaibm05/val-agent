"""Visual polygon annotator for callout regions.

Usage:
    python annotate_callouts.py <map_name>
    # e.g. python annotate_callouts.py ascent

Workflow:
    1. Loads data/map_templates/<map>.png as the background.
       If missing, grabs the current minimap from the live screen
       (using the region in config.json) and uses that instead.
    2. Opens an OpenCV window. For each callout you want to define:
        - LEFT-CLICK to add polygon vertices.
        - RIGHT-CLICK (or press 'c') to close the polygon and name it.
        - Press 'u' to undo the last point.
        - Press 'n' to start a new callout without finishing the current one.
        - Press 's' to save and exit.
        - Press 'q' to quit without saving.
    3. Polygons are written to data/callout_maps/<map>.json.

Controls summary (shown on screen):
    L-click: add point   |  R-click / c: close polygon
    u: undo point        |  s: save & quit  |  q: quit
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).parent
TEMPLATE_DIR = ROOT / "data" / "map_templates"
CALLOUT_DIR = ROOT / "data" / "callout_maps"
CONFIG_PATH = ROOT / "config.json"

WINDOW = "Callout Annotator"
HELP = [
    "L-click: add vertex",
    "R-click / c: close polygon",
    "u: undo   n: new   s: save   q: quit",
]


class Annotator:
    def __init__(self, map_name: str, background: np.ndarray, existing: dict):
        self.map_name = map_name
        self.bg = background
        self.polygons: dict[str, list[list[int]]] = dict(existing)
        self.current: list[tuple[int, int]] = []

    # ---- mouse ----
    def on_mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.current.append((x, y))
        elif event == cv2.EVENT_RBUTTONDOWN:
            self._close_polygon()

    def _close_polygon(self):
        if len(self.current) < 3:
            print("[!] need at least 3 points")
            return
        name = input("Callout name: ").strip()
        if not name:
            print("[!] empty name, discarded")
            self.current.clear()
            return
        self.polygons[name] = [list(p) for p in self.current]
        print(f"[+] saved '{name}' ({len(self.current)} pts)")
        self.current.clear()

    # ---- render ----
    def render(self) -> np.ndarray:
        img = self.bg.copy()
        # Existing polygons
        for name, pts in self.polygons.items():
            arr = np.array(pts, dtype=np.int32)
            cv2.polylines(img, [arr], True, (80, 220, 80), 2)
            cx, cy = arr.mean(axis=0).astype(int)
            cv2.putText(img, name, (cx - 20, cy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (80, 220, 80), 1)
        # In-progress polygon
        if self.current:
            arr = np.array(self.current, dtype=np.int32)
            cv2.polylines(img, [arr], False, (0, 165, 255), 2)
            for p in self.current:
                cv2.circle(img, p, 3, (0, 165, 255), -1)
        # Help overlay
        for i, line in enumerate(HELP):
            cv2.putText(img, line, (8, 16 + 16 * i),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1)
        return img


def load_background(map_name: str) -> np.ndarray:
    template_path = TEMPLATE_DIR / f"{map_name}.png"
    if template_path.exists():
        img = cv2.imread(str(template_path))
        if img is not None:
            print(f"[bg] using {template_path}")
            return img
    # Fall back to live capture
    print(f"[bg] {template_path} not found, grabbing live minimap...")
    import mss
    config = json.loads(CONFIG_PATH.read_text())
    region = config["minimap_region"]
    with mss.mss() as sct:
        img = np.array(sct.grab(region))[:, :, :3]
    return img


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python annotate_callouts.py <map_name>")
        return 1
    map_name = sys.argv[1].lower()

    CALLOUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CALLOUT_DIR / f"{map_name}.json"
    existing: dict = {}
    if out_path.exists():
        try:
            raw = json.loads(out_path.read_text())
            existing = {k: v for k, v in raw.items() if not k.startswith("_")}
            print(f"[load] {len(existing)} existing callouts")
        except json.JSONDecodeError:
            existing = {}

    bg = load_background(map_name)
    ann = Annotator(map_name, bg, existing)

    cv2.namedWindow(WINDOW)
    cv2.setMouseCallback(WINDOW, ann.on_mouse)

    while True:
        cv2.imshow(WINDOW, ann.render())
        key = cv2.waitKey(20) & 0xFF
        if key == ord("q"):
            print("[quit] not saving"); break
        elif key == ord("s"):
            out_path.write_text(json.dumps(ann.polygons, indent=2))
            print(f"[save] wrote {len(ann.polygons)} callouts -> {out_path}")
            break
        elif key == ord("u"):
            if ann.current:
                ann.current.pop()
        elif key == ord("c"):
            ann._close_polygon()
        elif key == ord("n"):
            ann.current.clear()

    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    sys.exit(main())
