"""One-time calibration tool.

Usage:
    python calibration.py

Takes a full-screen screenshot, lets you click-drag a rectangle around the
minimap, and writes the coordinates back into config.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import mss
import numpy as np

CONFIG_PATH = Path(__file__).parent / "config.json"


def grab_fullscreen() -> np.ndarray:
    with mss.mss() as sct:
        mon = sct.monitors[1]  # primary monitor
        img = np.array(sct.grab(mon))[:, :, :3]
    return img


def select_region(img: np.ndarray) -> tuple[int, int, int, int]:
    print("Draw a rectangle around the minimap, then press ENTER or SPACE.")
    print("Press C to cancel.")
    # Downscale for display if huge
    disp = img.copy()
    scale = 1.0
    if disp.shape[1] > 1600:
        scale = 1600 / disp.shape[1]
        disp = cv2.resize(disp, None, fx=scale, fy=scale)
    roi = cv2.selectROI("Select minimap region", disp, showCrosshair=True)
    cv2.destroyAllWindows()
    x, y, w, h = [int(v / scale) for v in roi]
    return x, y, w, h


def main() -> None:
    img = grab_fullscreen()
    x, y, w, h = select_region(img)
    if w == 0 or h == 0:
        print("No region selected. Aborting.")
        return

    config = json.loads(CONFIG_PATH.read_text())
    config["minimap_region"] = {"left": x, "top": y, "width": w, "height": h}
    config["resolution"] = [img.shape[1], img.shape[0]]
    CONFIG_PATH.write_text(json.dumps(config, indent=2))
    print(f"Saved minimap_region = {config['minimap_region']}")


if __name__ == "__main__":
    main()
