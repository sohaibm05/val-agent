# Valorant Real-Time Coaching Overlay

A Python desktop overlay that watches your Valorant minimap in real-time and shows agent-specific lineups, peek angles, and setup tips based on where you are on the map.

## Features (MVP)

- 🎯 Real-time minimap position tracking via screen capture + OpenCV
- 🗺️ Map auto-detection (template matching)
- 🏹 Agent-specific lineups (Sova recon/shock, Viper walls, etc.)
- 🛡️ Sentinel setups (Cypher trips, Killjoy lockdowns)
- 👀 Peek angle recommendations per callout + side
- 🖼️ Transparent always-on-top PyQt6 overlay
- ⌨️ F6 hotkey to toggle the overlay on/off

## Setup

```bash
pip install -r requirements.txt
```

### 1. Calibrate the minimap region (one-time)
```bash
python calibration.py
```
A screenshot of your desktop will appear. Drag a rectangle around the Valorant minimap in the top-left corner, then press ENTER. The coordinates get saved to `config.json`.

> 💡 **Tip:** Run Valorant in the background (or be on the main menu / practice range) so the minimap is visible when you calibrate.

### 2. Set your agent
Edit `config.json`:
```json
{
  "agent": "Sova",
  "side": "attack"
}
```

### 3. Run
```bash
python main.py
```
Press **F6** to toggle the overlay.

## Status of the MVP

This scaffold is functional but needs **data** to be useful:

- [ ] Capture reference minimap images for each map and drop into `data/map_templates/<map>.png`
- [ ] Tune callout polygons in `data/callout_maps/<map>.json` to match your minimap region size
- [ ] Expand coaching data in `data/coaching/<map>.json` (lineups, setups, peek angles)
- [ ] Tune HSV thresholds in `config.json` for the player icon (may vary with display settings)

## Safety / Anti-Cheat

This tool only reads pixels via `mss` (a standard screen capture library). It does **not** inject into the Valorant process or read game memory. This is the same approach used by OBS, Discord, and Nvidia ShadowPlay, which are all allowed by Vanguard. Overlays that read pixels and display info in a separate window are safe; do not attempt to read game memory.

## Project Layout

```
valorant-coach/
├── main.py                # Entry point
├── calibration.py         # One-time minimap region setup
├── config.json            # User settings
├── requirements.txt
│
├── src/
│   ├── core/
│   │   ├── capture.py
│   │   ├── map_detector.py
│   │   ├── position_detector.py
│   │   ├── agent_detector.py
│   │   └── coaching_engine.py
│   ├── ui/
│   │   └── overlay.py
│   └── utils/
│       └── hotkeys.py
│
└── data/
    ├── map_templates/     # Reference minimap PNGs per map
    ├── callout_maps/      # Polygon regions per map (JSON)
    ├── coaching/          # Coaching database (JSON per map)
    └── images/            # Lineup/setup screenshots
```

## Next Steps

1. **Populate map templates** — Take clean minimap screenshots on each map and save them.
2. **Tune callout polygons** — Use an image editor + the calibration tool to map each callout area.
3. **Expand the coaching database** — The included `ascent.json` is a sample; add more agents, maps, and lineups.
4. **Auto-detect side & agent** — Replace the manual config with HUD OCR (see `agent_detector.py`).
5. **Add image previews** — Show lineup screenshots in the overlay when the user presses `H`.
