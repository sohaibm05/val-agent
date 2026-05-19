# Valorant Real-Time Coaching Overlay

A Python desktop overlay that watches your Valorant minimap in real-time via screen capture, detects your map and on-map position with OpenCV template matching, and surfaces agent-specific lineups, peek angles, and sentinel setups in a transparent PyQt6 window.

> The runnable project lives in [`valorant agent/valorant-coach/`](./valorant%20agent/valorant-coach). See [IMPLEMENTATION_PLAN.md](./valorant%20agent/IMPLEMENTATION_PLAN.md) for the architecture write-up.

## Highlights
- Real-time minimap capture loop (~2–5 FPS) using `mss`
- Map auto-detection via OpenCV template matching against reference minimaps
- Position detection by player-icon color thresholding (tunable HSV)
- Agent-specific coaching engine — Sova recon/shock, Viper walls, Cypher trips, Killjoy lockdowns, etc.
- Peek-angle recommendations keyed off callout + attack/defense side
- Transparent always-on-top overlay (PyQt6) with F6 toggle hotkey
- Anti-cheat safe — only reads pixels (same approach as OBS / Discord overlays); never injects into the game or reads memory

## Architecture
```
Screen capture (mss)
        │
        ▼
CV pipeline (OpenCV)
  ├─ MapDetector       — template match against minimap reference images
  ├─ PositionDetector  — find player icon, map to callout polygon
  └─ AgentDetector     — read agent name from minimap region
        │
        ▼
CoachingEngine — looks up tips in data/coaching/<map>.json
        │
        ▼
Transparent PyQt6 overlay
```

Coaching data is JSON, organized per map (`ascent`, `bind`, `haven`, `lotus`, `split`), making it easy to extend.

## Setup
```bash
cd "valorant agent/valorant-coach"
pip install -r requirements.txt
python calibration.py     # one-time: drag a box around the minimap, press ENTER
```
Edit `config.json` to set your agent and side:
```json
{ "agent": "Sova", "side": "attack" }
```
Then run:
```bash
python main.py
```
Press **F6** to toggle the overlay.

## Tech stack
Python 3.10+ · OpenCV · NumPy · mss · PyQt6 · pynput

## Status
MVP scaffold. All glue code works; the system is data-bound — capturing reference minimap templates, tuning callout polygons, and expanding coaching JSON per map is the bulk of remaining work (see "Status of the MVP" section in the inner project's README).

## License
MIT — see [LICENSE](LICENSE).
