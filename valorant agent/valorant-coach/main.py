"""Valorant Real-Time Coaching Overlay — entry point.

Usage:
    1. pip install -r requirements.txt
    2. python calibration.py          # one-time: draw a box around the minimap
    3. python main.py                 # run the overlay while Valorant is open
       (press F6 to show/hide)
"""
from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path

from PyQt6.QtWidgets import QApplication

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from src.core.capture import ScreenCapture  # noqa: E402
from src.core.map_detector import MapDetector  # noqa: E402
from src.core.position_detector import PositionDetector  # noqa: E402
from src.core.agent_detector import AgentDetector  # noqa: E402
from src.core.coaching_engine import CoachingEngine  # noqa: E402
from src.ui.overlay import CoachingOverlay  # noqa: E402
from src.utils.hotkeys import HotkeyListener  # noqa: E402


CONFIG_PATH = ROOT / "config.json"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def run_detection_loop(
    capture: ScreenCapture,
    map_det: MapDetector,
    pos_det: PositionDetector,
    agent_det: AgentDetector,
    coach: CoachingEngine,
    overlay: CoachingOverlay,
    fps: int,
    side: str,
    forced_map: str | None = None,
) -> None:
    current_map = forced_map
    sleep = 1.0 / max(fps, 1)

    while True:
        try:
            frame = capture.grab_minimap()

            if current_map is None:
                current_map = map_det.detect_map(frame)
                if current_map is None:
                    overlay.update_coaching({
                        "map": "Detecting...", "callout": "—",
                        "agent": agent_det.detect(), "side": side,
                        "peek_angles": [], "lineups": [], "setups": [],
                        "tips": ["Waiting for map detection. Are you in-game?"],
                    })
                    time.sleep(sleep)
                    continue

            position = pos_det.find_player_position(frame)
            callout = pos_det.get_callout(current_map, position) if position else "Unknown"
            agent = agent_det.detect()

            coaching = coach.get_coaching(current_map, callout, agent, side)
            overlay.update_coaching(coaching)

        except Exception as exc:  # keep the loop alive
            print(f"[loop] error: {exc}")

        time.sleep(sleep)


def main() -> int:
    config = load_config()

    app = QApplication(sys.argv)
    overlay = CoachingOverlay()
    overlay.show()

    capture = ScreenCapture(config["minimap_region"])
    map_det = MapDetector(ROOT / "data" / "map_templates")
    pos_det = PositionDetector(
        ROOT / "data" / "callout_maps",
        config["player_icon_hsv"]["lower"],
        config["player_icon_hsv"]["upper"],
    )
    agent_det = AgentDetector(config.get("agent", "Sova"))
    coach = CoachingEngine(ROOT / "data" / "coaching")

    # Hotkey: toggle overlay visibility
    def _toggle():
        overlay.setVisible(not overlay.isVisible())

    try:
        hk = HotkeyListener(f"<{config['hotkeys']['toggle_overlay']}>", _toggle)
        hk.start()
    except Exception as e:
        print(f"[hotkeys] disabled: {e}")

    # Background detection thread
    # For development without a map template yet, force_map can be set in config.
    forced_map = config.get("force_map")  # e.g. "ascent"
    t = threading.Thread(
        target=run_detection_loop,
        args=(capture, map_det, pos_det, agent_det, coach, overlay,
              config.get("capture_fps", 3), config.get("side", "attack"), forced_map),
        daemon=True,
    )
    t.start()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
