# Valorant Real-Time Coaching Overlay — Implementation Plan

## Overview

A desktop overlay application that runs alongside Valorant, reads the minimap via screen capture + computer vision, detects your agent/map/position in real-time, and provides contextual coaching: peek angles, lineups, sentinel setups, and positional tips.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Main Loop (~2-5 FPS)              │
│                                                     │
│  ┌──────────┐   ┌──────────────┐   ┌────────────┐  │
│  │  Screen   │──▶│  CV Pipeline │──▶│  Coaching   │  │
│  │  Capture  │   │  (OpenCV)    │   │  Engine     │  │
│  └──────────┘   └──────────────┘   └─────┬──────┘  │
│                                          │         │
│                                   ┌──────▼──────┐  │
│                                   │  Overlay UI  │  │
│                                   │ (Transparent │  │
│                                   │   Window)    │  │
│                                   └─────────────┘  │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Data Layer      │
│  (JSON/SQLite)   │
│  - Lineups       │
│  - Peek angles   │
│  - Setups        │
│  - Map templates │
└─────────────────┘
```

---

## Tech Stack

| Component | Technology | Why |
|---|---|---|
| Language | **Python 3.10+** | Great CV/ML ecosystem, you're intermediate level |
| Screen Capture | **mss** (or `dxcam` for GPU-accelerated) | Fast, low-overhead capture |
| Computer Vision | **OpenCV + NumPy** | Minimap parsing, template matching |
| OCR (optional) | **Tesseract / EasyOCR** | Read agent name, map name, round info |
| Overlay UI | **PyQt6** (transparent frameless window) | Stays on top of Valorant |
| Data Storage | **JSON files** (MVP) → SQLite later | Simple, easy to edit and extend |
| Image Matching | **OpenCV template matching** | Match minimap icons to known positions |

---

## Phase 1: Screen Capture & Minimap Extraction

### Goal
Capture the Valorant minimap region in real-time and isolate it for processing.

### Steps

1. **Calibrate capture region**
   - The minimap is always in the **top-left corner** of the screen
   - Create a calibration script that lets you draw a rectangle around the minimap once
   - Save the region coordinates (x, y, width, height) to a `config.json`
   - Support common resolutions: 1920x1080, 2560x1440, 3840x2160

2. **Capture loop**
   ```python
   # core/capture.py
   import mss
   import numpy as np

   class ScreenCapture:
       def __init__(self, region: dict):
           self.sct = mss.mss()
           self.region = region  # {"left": x, "top": y, "width": w, "height": h}

       def grab_minimap(self) -> np.ndarray:
           img = self.sct.grab(self.region)
           return np.array(img)[:, :, :3]  # Drop alpha channel
   ```

3. **Frame rate target**: 2-5 FPS is sufficient (minimap doesn't change every frame)

### Key files
```
src/
  core/
    capture.py         # Screen capture logic
    config.json        # Saved region coordinates, resolution
  calibration.py       # One-time setup script
```

---

## Phase 2: Computer Vision Pipeline

### Goal
From the minimap image, detect: which map, which agent, player position (x, y on minimap).

### 2A: Map Detection

1. **Store reference minimap images** for each map (Ascent, Bind, Haven, Split, Icebox, Breeze, Fracture, Pearl, Lotus, Sunset, Abyss)
2. **Use template matching or feature matching** (ORB/SIFT) to identify the current map
3. Map only needs to be detected **once per match** — cache the result

```python
# core/map_detector.py
import cv2

class MapDetector:
    def __init__(self, templates_dir: str):
        self.templates = self._load_templates(templates_dir)

    def detect_map(self, minimap_img) -> str:
        best_match = None
        best_score = 0
        for map_name, template in self.templates.items():
            result = cv2.matchTemplate(minimap_img, template, cv2.TM_CCOEFF_NORMED)
            score = result.max()
            if score > best_score:
                best_score = score
                best_match = map_name
        return best_match
```

### 2B: Player Position Detection

The player icon on the minimap is a **colored cone/arrow**. Detection approach:

1. **Color filtering** — isolate the player icon by its unique color (green for you, different colors per team)
   - Convert to HSV, threshold for the green player icon
   - Find contours, get the centroid → that's your (x, y) on the minimap

2. **Map the pixel position to a named callout**
   - Create a **callout map** for each Valorant map: a grid/polygon overlay where each region maps to a callout name (e.g., "A Main", "B Site", "Mid Window")
   - Store as JSON polygons:
   ```json
   {
     "ascent": {
       "A Site": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],
       "A Main": [[...], ...],
       "Mid": [[...], ...]
     }
   }
   ```

3. **Point-in-polygon test** to determine which callout the player is in

```python
# core/position_detector.py
import cv2
import numpy as np

class PositionDetector:
    def __init__(self, callout_data: dict):
        self.callouts = callout_data

    def find_player_position(self, minimap_img) -> tuple:
        hsv = cv2.cvtColor(minimap_img, cv2.COLOR_BGR2HSV)
        # Green player icon range (tune these values)
        mask = cv2.inRange(hsv, (35, 100, 100), (85, 255, 255))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            M = cv2.moments(largest)
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            return (cx, cy)
        return None

    def get_callout(self, map_name: str, position: tuple) -> str:
        for callout, polygon in self.callouts[map_name].items():
            if self._point_in_polygon(position, polygon):
                return callout
        return "Unknown"
```

### 2C: Agent Detection

Two approaches (pick one):

- **Option A — OCR**: Read the agent name from the HUD (bottom of screen or agent select screen). Use EasyOCR to capture it once at round start.
- **Option B — Template matching**: Store small icon images for each agent and match against the agent portrait in the HUD.
- **Option C — Manual selection**: Let the user pick their agent from a dropdown before the match starts (simplest for MVP).

**Recommendation for MVP**: Option C (manual) + Option A (OCR) as a stretch goal.

### Key files
```
src/
  core/
    map_detector.py
    position_detector.py
    agent_detector.py
  data/
    map_templates/       # Reference minimap images per map
    callout_maps/        # JSON polygon callout regions per map
    agent_icons/         # Agent icon templates (for Option B)
```

---

## Phase 3: Coaching Data Layer

### Goal
Build a structured database of coaching knowledge: lineups, peek angles, setups.

### 3A: Data Schema

```json
// data/coaching/ascent.json
{
  "map": "Ascent",
  "callouts": {
    "A Main": {
      "peek_angles": [
        {
          "name": "A Main to A Site default",
          "description": "Common angle holding A Site from A Main entrance",
          "image": "ascent_a_main_peek_1.png",
          "side": "attack",
          "difficulty": "easy"
        }
      ],
      "lineups": {
        "Sova": [
          {
            "name": "A Site recon from A Main",
            "type": "recon_bolt",
            "description": "Stand in A Main corner, aim at...",
            "image": "sova_ascent_a_recon_1.png",
            "video_url": "optional_youtube_link",
            "bounces": 1,
            "power": "full"
          }
        ],
        "Viper": [
          {
            "name": "A Site one-way smoke",
            "type": "poison_cloud",
            "description": "Place on top of A Site box...",
            "image": "viper_ascent_a_oneway.png"
          }
        ]
      },
      "setups": {
        "Cypher": [
          {
            "name": "A Site retake setup",
            "description": "Tripwire across A Main entrance, cam on...",
            "side": "defense",
            "images": ["cypher_ascent_a_trip.png", "cypher_ascent_a_cam.png"]
          }
        ],
        "Killjoy": [
          {
            "name": "A Site lockdown",
            "description": "Turret watching A Main, alarm bot behind box...",
            "side": "defense",
            "images": ["kj_ascent_a_turret.png", "kj_ascent_a_alarm.png"]
          }
        ]
      },
      "tips": [
        "Don't wide-peek A Site from A Main — use the wall for a shoulder peek",
        "Listen for audio cues from A Tree before pushing"
      ]
    }
  }
}
```

### 3B: Data Sources

Where to get this coaching data:

1. **Manual curation** — Watch pro player POVs and lineup guides (Valorant YouTubers like Jonas, Snapiex, etc.) and record the data
2. **Community wikis** — Scrape/reference blitz.gg, valoplant.gg (lineup tool), tracker.gg
3. **Crowdsource later** — Let users contribute lineups with screenshots

### 3C: Agent Categories

| Category | Agents | Coaching Focus |
|---|---|---|
| Duelists | Jett, Raze, Reyna, Phoenix, Neon, Yoru, Iso | Entry paths, peek angles, flash timings |
| Initiators | Sova, Breach, Skye, Fade, Gekko, KAY/O | Lineups (recon/flash), info-gathering spots |
| Controllers | Omen, Brimstone, Viper, Astra, Harbor, Clove | Smoke placements, one-ways, wall positions |
| Sentinels | Cypher, Killjoy, Sage, Chamber, Deadlock, Vyse | Trap setups, cam spots, defensive positions |

### Key files
```
src/
  data/
    coaching/
      ascent.json
      bind.json
      haven.json
      ... (one per map)
    images/
      lineups/
      peek_angles/
      setups/
```

---

## Phase 4: Coaching Engine

### Goal
Take the detected state (map + position + agent + side) and return relevant coaching tips.

```python
# core/coaching_engine.py
class CoachingEngine:
    def __init__(self, coaching_data: dict):
        self.data = coaching_data

    def get_coaching(self, map_name: str, callout: str, agent: str, side: str) -> dict:
        location_data = self.data[map_name]["callouts"].get(callout, {})

        result = {
            "peek_angles": [],
            "lineups": [],
            "setups": [],
            "tips": []
        }

        # Peek angles for this position + side
        result["peek_angles"] = [
            p for p in location_data.get("peek_angles", [])
            if p["side"] in (side, "both")
        ]

        # Agent-specific lineups
        result["lineups"] = location_data.get("lineups", {}).get(agent, [])

        # Agent-specific setups (mainly sentinels/controllers)
        result["setups"] = location_data.get("setups", {}).get(agent, [])

        # General tips
        result["tips"] = location_data.get("tips", [])

        return result
```

---

## Phase 5: Overlay UI

### Goal
Display coaching info as a transparent overlay on top of Valorant.

### Design

```
┌────────────────────────────────────┐
│  🎯 A Main (Ascent) — Attack      │  ← Current position header
├────────────────────────────────────┤
│  PEEK ANGLES                       │
│  • A Main to Site default (easy)   │
│    [thumbnail]                     │
├────────────────────────────────────┤
│  SOVA LINEUPS                      │
│  • A Site recon bolt [1 bounce]    │
│    [thumbnail] — Press [H] to view │
├────────────────────────────────────┤
│  TIPS                              │
│  • Shoulder peek, don't wide swing │
└────────────────────────────────────┘
```

### Implementation

```python
# ui/overlay.py
from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer

class CoachingOverlay(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Position overlay in bottom-right or top-right
        self.setGeometry(1500, 100, 400, 500)  # Adjust for resolution

        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout(self.central)

        # Hotkey to toggle visibility (e.g., F6)
        # Use pynput or keyboard library for global hotkeys

    def update_coaching(self, coaching_data: dict):
        # Clear existing widgets and rebuild with new data
        ...
```

### Key features
- **Semi-transparent dark background** so it doesn't obstruct gameplay
- **Toggle hotkey** (e.g., F6) to show/hide the overlay
- **Compact mode** vs **expanded mode** (press H to see full lineup image)
- **Auto-hide** when in the buy phase or agent select

---

## Phase 6: Main Loop (Putting It All Together)

```python
# main.py
import time
from core.capture import ScreenCapture
from core.map_detector import MapDetector
from core.position_detector import PositionDetector
from core.coaching_engine import CoachingEngine
from ui.overlay import CoachingOverlay

def main():
    # Load config
    config = load_config("config.json")

    # Initialize components
    capture = ScreenCapture(config["minimap_region"])
    map_detector = MapDetector("data/map_templates")
    position_detector = PositionDetector(load_callouts())
    coaching_engine = CoachingEngine(load_coaching_data())
    overlay = CoachingOverlay()

    current_map = None
    agent = config.get("agent", "Sova")  # Manual selection for MVP
    side = config.get("side", "attack")  # Could auto-detect later

    while True:
        frame = capture.grab_minimap()

        # Detect map (only once per match)
        if current_map is None:
            current_map = map_detector.detect_map(frame)

        # Detect player position
        position = position_detector.find_player_position(frame)
        if position:
            callout = position_detector.get_callout(current_map, position)

            # Get coaching for this state
            coaching = coaching_engine.get_coaching(
                current_map, callout, agent, side
            )

            # Update overlay
            overlay.update_coaching(coaching)

        time.sleep(0.3)  # ~3 FPS

if __name__ == "__main__":
    main()
```

---

## Project Structure (Final)

```
valorant-coach/
├── main.py                    # Entry point
├── calibration.py             # One-time minimap region setup
├── config.json                # User settings (resolution, region, agent)
├── requirements.txt           # Dependencies
│
├── src/
│   ├── core/
│   │   ├── capture.py         # Screen capture
│   │   ├── map_detector.py    # Map identification
│   │   ├── position_detector.py  # Player position + callout
│   │   ├── agent_detector.py  # Agent detection (OCR/template)
│   │   └── coaching_engine.py # Coaching logic
│   │
│   ├── ui/
│   │   ├── overlay.py         # PyQt6 overlay window
│   │   └── styles.py          # UI theming/colors
│   │
│   └── utils/
│       ├── hotkeys.py         # Global hotkey listener
│       └── helpers.py         # Shared utility functions
│
├── data/
│   ├── map_templates/         # Reference minimap images
│   │   ├── ascent.png
│   │   ├── bind.png
│   │   └── ...
│   │
│   ├── callout_maps/          # Polygon regions per map
│   │   ├── ascent.json
│   │   └── ...
│   │
│   ├── coaching/              # Coaching knowledge base
│   │   ├── ascent.json
│   │   ├── bind.json
│   │   └── ...
│   │
│   └── images/                # Lineup/setup screenshots
│       ├── lineups/
│       ├── peek_angles/
│       └── setups/
│
└── tests/
    ├── test_capture.py
    ├── test_map_detector.py
    └── test_position_detector.py
```

---

## Dependencies (requirements.txt)

```
opencv-python>=4.8.0
numpy>=1.24.0
mss>=9.0.0
PyQt6>=6.5.0
pynput>=1.7.6        # Global hotkeys
easyocr>=1.7.0       # Optional: agent/map OCR
Pillow>=10.0.0
```

---

## Build Order (Recommended)

### Sprint 1 (Week 1-2): Foundation
- [ ] Set up project structure and virtual environment
- [ ] Implement screen capture + calibration tool
- [ ] Build map detection with template matching
- [ ] Test with screenshots from each map

### Sprint 2 (Week 3-4): Position Tracking
- [ ] Implement player icon color detection
- [ ] Create callout polygon maps for 2-3 maps (start with Ascent, Bind, Haven)
- [ ] Build point-in-polygon callout detection
- [ ] Test with live gameplay

### Sprint 3 (Week 5-6): Coaching Data
- [ ] Design and populate coaching JSON for 2-3 maps
- [ ] Curate 5-10 peek angles per map
- [ ] Curate 5-10 Sova lineups per map
- [ ] Curate sentinel setups (Cypher, Killjoy) for each site
- [ ] Build the coaching engine query logic

### Sprint 4 (Week 7-8): Overlay UI
- [ ] Build transparent PyQt6 overlay
- [ ] Add hotkey toggle (show/hide)
- [ ] Wire up coaching engine → overlay display
- [ ] Add compact/expanded modes
- [ ] Add image viewer for lineup screenshots

### Sprint 5 (Week 9-10): Polish & Expand
- [ ] Add remaining maps
- [ ] Add more agents (Viper walls, Omen smokes, etc.)
- [ ] Auto-detect attack/defense side
- [ ] Auto-detect agent from HUD
- [ ] Performance optimization (caching, lazy loading)
- [ ] Package as an executable (.exe) with PyInstaller

---

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| **Vanguard anti-cheat flags the overlay** | PyQt overlay only reads pixels (no memory injection). This is the same approach OBS/Discord use — read-only screen capture is safe. |
| **Minimap color detection fails with skins/color settings** | Allow user to tune HSV thresholds in config; provide a calibration tool |
| **Too many lineups overwhelm the UI** | Filter by relevance (side, position), show top 3 with "see more" option |
| **Performance impact on game** | Cap capture at 2-3 FPS, use mss (very lightweight), run CV on a background thread |
| **Map updates break detection** | Version the template images, update when Riot patches maps |

---

## Future Enhancements (Post-MVP)

1. **AI-powered coaching** — Feed minimap state to a vision model for dynamic advice ("enemy likely rotating based on minimap pings")
2. **Voice coaching** — Text-to-speech for tips so you don't have to read the overlay
3. **Round economy advisor** — OCR the credit count and suggest buy/save
4. **Team composition tips** — Suggest agent swaps based on team comp
5. **Replay analysis** — Record position data throughout a match and review decision-making afterward
6. **Community marketplace** — Let users upload and share lineups/setups
