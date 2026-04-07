"""End-to-end pipeline test with a synthetic minimap.

Creates a fake 430x430 minimap with a green "player" blob at a chosen pixel,
runs it through PositionDetector + CoachingEngine, and verifies we get the
expected callout + coaching data. No Valorant or screen capture required.

Run:
    python -m pytest tests/ -v
or simply:
    python tests/test_pipeline.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.core.position_detector import PositionDetector  # noqa: E402
from src.core.coaching_engine import CoachingEngine  # noqa: E402


def make_fake_minimap(player_xy: tuple[int, int], size: int = 430) -> np.ndarray:
    """Return a BGR image with a bright-green blob at player_xy."""
    img = np.full((size, size, 3), 30, dtype=np.uint8)  # dark gray background
    cv2.circle(img, player_xy, 8, (0, 255, 0), -1)  # green blob
    return img


def run_case(pos_det, coach, map_name, xy, agent, side, expected_callout):
    img = make_fake_minimap(xy)
    detected_xy = pos_det.find_player_position(img)
    assert detected_xy is not None, f"player icon not detected at {xy}"
    callout = pos_det.get_callout(map_name, detected_xy)
    coaching = coach.get_coaching(map_name, callout, agent, side)

    print(f"  {map_name} @ {xy} -> '{callout}' ({agent}/{side}): "
          f"lineups={len(coaching['lineups'])} "
          f"setups={len(coaching['setups'])} "
          f"peeks={len(coaching['peek_angles'])}")
    assert callout == expected_callout, (
        f"[{map_name}] expected '{expected_callout}' at {xy}, got '{callout}'"
    )
    return coaching


def main() -> int:
    pos_det = PositionDetector(
        ROOT / "data" / "callout_maps",
        hsv_lower=[35, 100, 100],
        hsv_upper=[85, 255, 255],
    )
    coach = CoachingEngine(ROOT / "data" / "coaching")

    # Each test case uses the placeholder polygons in data/callout_maps/*.json.
    cases = [
        # (map, xy, agent, side, expected callout)
        ("ascent", (100, 60),   "Sova",    "attack",  "A Main"),
        ("ascent", (300, 75),   "Cypher",  "defense", "A Site"),
        ("ascent", (200, 200),  "Sova",    "attack",  "Mid"),
        ("ascent", (100, 400),  "Killjoy", "defense", "B Main"),
        ("bind",   (300, 200),  "Sova",    "attack",  "A Site"),
        ("bind",   (100, 90),   "Viper",   "attack",  "B Long"),
        ("bind",   (100, 400),  "Killjoy", "defense", "B Site"),
        ("haven",  (75, 80),    "Sova",    "attack",  "A Short"),
        ("haven",  (200, 320),  "Cypher",  "defense", "B Site"),
        ("haven",  (200, 400),  "Sova",    "attack",  "C Site"),
        ("split",  (350, 60),   "Sova",    "attack",  "A Main"),
        ("split",  (90, 300),   "Killjoy", "defense", "B Site"),
        ("lotus",  (350, 200),  "Cypher",  "defense", "A Site"),
        ("lotus",  (80, 350),   "Killjoy", "defense", "C Site"),
    ]

    print(f"Running {len(cases)} end-to-end pipeline cases...\n")
    passed = 0
    failed = []
    for case in cases:
        try:
            run_case(pos_det, coach, *case)
            passed += 1
        except AssertionError as e:
            failed.append(str(e))
            print(f"  FAIL: {e}")

    print(f"\n{passed}/{len(cases)} passed")
    if failed:
        print("\nFailures:")
        for f in failed:
            print(f"  - {f}")
        return 1
    print("All good! ✔")
    return 0


if __name__ == "__main__":
    sys.exit(main())
