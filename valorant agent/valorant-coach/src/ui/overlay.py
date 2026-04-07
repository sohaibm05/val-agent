"""Transparent always-on-top PyQt6 overlay window."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QMainWindow,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


STYLESHEET = """
QWidget#root {
    background-color: rgba(10, 12, 20, 200);
    border: 1px solid rgba(255, 70, 85, 180);
    border-radius: 8px;
}
QLabel { color: #EEEEEE; font-family: 'Segoe UI', sans-serif; }
QLabel#header { color: #FF4655; font-size: 14pt; font-weight: bold; padding: 6px; }
QLabel#section { color: #FF4655; font-size: 10pt; font-weight: bold; padding-top: 6px; }
QLabel#item { color: #EEEEEE; font-size: 9pt; padding: 2px 10px; }
QLabel#desc { color: #AAAAAA; font-size: 8pt; padding: 0 18px 4px 18px; }
QFrame#sep { background-color: rgba(255, 70, 85, 80); max-height: 1px; }
"""


class CoachingOverlay(QMainWindow):
    coaching_updated = pyqtSignal(dict)

    def __init__(self, x: int = 1480, y: int = 80, w: int = 420, h: int = 560):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(x, y, w, h)
        self.setStyleSheet(STYLESHEET)

        root = QWidget(objectName="root")
        self.setCentralWidget(root)

        self.layout = QVBoxLayout(root)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(4)

        self.header = QLabel("Waiting for Valorant...", objectName="header")
        self.layout.addWidget(self.header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.content)
        self.layout.addWidget(self.scroll)

        self.coaching_updated.connect(self._render)

    # Called from any thread
    def update_coaching(self, coaching: dict) -> None:
        self.coaching_updated.emit(coaching)

    @pyqtSlot(dict)
    def _render(self, coaching: dict) -> None:
        # Clear old content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        header_text = (
            f"🎯 {coaching.get('callout', '?')}  —  "
            f"{coaching.get('map', '?')}  ({coaching.get('side', '').title()})"
        )
        self.header.setText(header_text)

        self._add_section("PEEK ANGLES", coaching.get("peek_angles", []))
        self._add_section("LINEUPS", coaching.get("lineups", []))
        self._add_section("SETUPS", coaching.get("setups", []))

        tips = coaching.get("tips", [])
        if tips:
            self.content_layout.addWidget(QLabel("TIPS", objectName="section"))
            for tip in tips:
                lbl = QLabel(f"• {tip}", objectName="item")
                lbl.setWordWrap(True)
                self.content_layout.addWidget(lbl)

    def _add_section(self, title: str, items: list[dict]) -> None:
        if not items:
            return
        self.content_layout.addWidget(QLabel(title, objectName="section"))
        for item in items:
            name = item.get("name", "Unnamed")
            desc = item.get("description", "")
            name_lbl = QLabel(f"• {name}", objectName="item")
            name_lbl.setWordWrap(True)
            self.content_layout.addWidget(name_lbl)
            if desc:
                desc_lbl = QLabel(desc, objectName="desc")
                desc_lbl.setWordWrap(True)
                self.content_layout.addWidget(desc_lbl)
        sep = QFrame(objectName="sep")
        sep.setFrameShape(QFrame.Shape.HLine)
        self.content_layout.addWidget(sep)
