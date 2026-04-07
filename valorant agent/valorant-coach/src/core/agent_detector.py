"""Agent detection.

MVP: manual selection via config.json.
Stretch: OCR the agent name from the HUD, or template-match the portrait.
"""
from __future__ import annotations


VALID_AGENTS = {
    # Duelists
    "Jett", "Raze", "Reyna", "Phoenix", "Neon", "Yoru", "Iso",
    # Initiators
    "Sova", "Breach", "Skye", "Fade", "Gekko", "KAY/O",
    # Controllers
    "Omen", "Brimstone", "Viper", "Astra", "Harbor", "Clove",
    # Sentinels
    "Cypher", "Killjoy", "Sage", "Chamber", "Deadlock", "Vyse",
}


class AgentDetector:
    """MVP agent 'detector' — just reads from config.

    Replace `detect()` with OCR or template matching later.
    """

    def __init__(self, configured_agent: str):
        self.agent = configured_agent

    def detect(self, hud_img=None) -> str:
        return self.agent
