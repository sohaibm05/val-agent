"""Coaching engine — turns (map, callout, agent, side) into coaching tips."""
from __future__ import annotations

import json
from pathlib import Path


class CoachingEngine:
    def __init__(self, coaching_dir: str | Path):
        self.coaching_dir = Path(coaching_dir)
        self._cache: dict[str, dict] = {}

    def _load(self, map_name: str) -> dict:
        key = map_name.lower()
        if key in self._cache:
            return self._cache[key]
        path = self.coaching_dir / f"{key}.json"
        if not path.exists():
            self._cache[key] = {}
            return {}
        data = json.loads(path.read_text())
        self._cache[key] = data
        return data

    def get_coaching(
        self,
        map_name: str,
        callout: str,
        agent: str,
        side: str = "attack",
    ) -> dict:
        data = self._load(map_name)
        location = data.get("callouts", {}).get(callout, {})

        peek_angles = [
            p for p in location.get("peek_angles", [])
            if p.get("side", "both") in (side, "both")
        ]
        lineups = location.get("lineups", {}).get(agent, [])
        setups = location.get("setups", {}).get(agent, [])
        tips = location.get("tips", [])

        return {
            "map": map_name,
            "callout": callout,
            "agent": agent,
            "side": side,
            "peek_angles": peek_angles,
            "lineups": lineups,
            "setups": setups,
            "tips": tips,
        }
