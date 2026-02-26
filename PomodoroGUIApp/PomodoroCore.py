# app.py
import sys
import time
import json
from pathlib import Path
from dataclasses import dataclass
from enum import Enum, auto

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame
)

# ----------------------------
# Config
# ----------------------------

DEFAULT_CONFIG = {
    "work_minutes": 25,
    "short_break_minutes": 5,
    "long_break_minutes": 15,
    "long_break_every": 4,
    "ui": {
        "theme_file": "theme.qss",
        "window_title": "Pomodoro",
        "always_on_top": False,
        "opacity": 1.0,
        "tick_ms": 100,          # how often UI timer fires
        "hotkeys": True
    }
}

def load_config(path: str = "config.json") -> dict:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))  # deep-ish copy
    p = Path(path)
    if not p.exists():
        return cfg

    user_cfg = json.loads(p.read_text(encoding="utf-8"))

    # shallow merge top-level
    for k, v in user_cfg.items():
        if k != "ui":
            cfg[k] = v

    # merge ui
    if isinstance(user_cfg.get("ui"), dict):
        cfg["ui"].update(user_cfg["ui"])

    # sanity checks
    for k in ["work_minutes", "short_break_minutes", "long_break_minutes", "long_break_every"]:
        if not isinstance(cfg.get(k), int) or cfg[k] <= 0:
            raise ValueError(f"{k} must be a positive int")

    if not (0.2 <= float(cfg["ui"].get("opacity", 1.0)) <= 1.0):
        raise ValueError("ui.opacity must be between 0.2 and 1.0")

    if not isinstance(cfg["ui"].get("tick_ms", 100), int) or cfg["ui"]["tick_ms"] <= 0:
        raise ValueError("ui.tick_ms must be a positive int")

    return cfg

def try_load_qss(app: QApplication, theme_path: str) -> None:
    p = Path(theme_path)
    if p.exists():
        app.setStyleSheet(p.read_text(encoding="utf-8"))

# ----------------------------
# Engine (no UI / no sleeps)
# ----------------------------

class Mode(Enum):
    WORK = auto()
    SHORT_BREAK = auto()
    LONG_BREAK = auto()

@dataclass
class Snapshot:
    mode: Mode
    remaining: int
    paused: bool
    work_sessions_done: int

def format_hhmmss(secs: int) -> str:
    secs = max(0, int(secs))
    h = secs // 3600
    m = (secs % 3600) // 60
    s = secs % 60
    return f"{h:02}:{m:02}:{s:02}"

class PomodoroEngine:
    def __init__(self, work_secs: int, short_break_secs: int, long_break_secs: int, long_break_every: int = 4):
        self.work_secs = int(work_secs)
        self.short_break_secs = int(short_break_secs)
        self.long_break_secs = int(long_break_secs)
        self.long_break_every = int(long_break_every)

        self.on_change = None  # optional callback(snapshot)
        self.reset()

    def reset(self):
        self.mode = Mode.WORK
        self.remaining = self.work_secs
        self.paused = True
        self.work_sessions_done = 0
        self._acc = 0.0
        self._emit()

    def start(self):
        self.paused = False
        self._emit()

    def toggle_pause(self):
        self.paused = not self.paused
        self._emit()

    def skip(self):
        self._advance_session()
        self._emit()

    def tick(self, dt: float):
        if self.paused:
            return

        self._acc += float(dt)
        while self._acc >= 1.0:
            self._acc -= 1.0
            if self.remaining > 0:
                self.remaining -= 1
                self._emit()
            else:
                self._advance_session()
                self._emit()

    def _advance_session(self):
        if self.mode == Mode.WORK:
            self.work_sessions_done += 1
            if self.work_sessions_done % self.long_break_every == 0:
                self.mode = Mode.LONG_BREAK
                self.remaining = self.long_break_secs
            else:
                self.mode = Mode.SHORT_BREAK
                self.remaining = self.short_break_secs
        else:
            self.mode = Mode.WORK
            self.remaining = self.work_secs

    def snapshot(self) -> Snapshot:
        return Snapshot(self.mode, self.remaining, self.paused, self.work_sessions_done)

    def _emit(self):
        if callable(self.on_change):
            self.on_change(self.snapshot())

# ----------------------------
# UI
# ----------------------------

class PomodoroWindow(QWidget):
    def __init__(self, cfg: dict):
        super().__init__()
        self.cfg = cfg

        self.setWindowTitle(cfg["ui"]["window_title"])
        self.setObjectName("Root")

        if cfg["ui"].get("always_on_top", False):
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        self.setWindowOpacity(float(cfg["ui"].get("opacity", 1.0)))

        self.engine = PomodoroEngine(
            work_secs=cfg["work_minutes"] * 60,
            short_break_secs=cfg["short_break_minutes"] * 60,
            long_break_secs=cfg["long_break_minutes"] * 60,
            long_break_every=cfg["long_break_every"],
        )
        self.engine.on_change = self.render

        # Labels
        self.mode_lbl = QLabel("WORK")
        self.mode_lbl.setObjectName("ModeLabel")
        self.mode_lbl.setAlignment(Qt.AlignCenter)

        self.time_lbl = QLabel("00:00:00")
        self.time_lbl.setObjectName("TimeLabel")
        self.time_lbl.setAlignment(Qt.AlignCenter)

        self.meta_lbl = QLabel("")
        self.meta_lbl.setObjectName("MetaLabel")
        self.meta_lbl.setAlignment(Qt.AlignCenter)

        # Buttons
        self.start_btn = QPushButton("Start")
        self.start_btn.setObjectName("PrimaryButton")

        self.pause_btn = QPushButton("Pause/Resume")
        self.pause_btn.setObjectName("Button")

        self.skip_btn = QPushButton("Skip")
        self.skip_btn.setObjectName("Button")

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setObjectName("DangerButton")

        self.start_btn.clicked.connect(self.engine.start)
        self.pause_btn.clicked.connect(self.engine.toggle_pause)
        self.skip_btn.clicked.connect(self.engine.skip)
        self.reset_btn.clicked.connect(self.engine.reset)

        # Layout
        top = QVBoxLayout()
        top.addWidget(self.mode_lbl)

        divider = QFrame()
        divider.setObjectName("Divider")
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Plain)
        top.addWidget(divider)

        top.addWidget(self.time_lbl)
        top.addWidget(self.meta_lbl)

        row = QHBoxLayout()
        row.addWidget(self.start_btn)
        row.addWidget(self.pause_btn)
        row.addWidget(self.skip_btn)
        row.addWidget(self.reset_btn)
        top.addLayout(row)

        self.setLayout(top)

        # Hotkeys
        if cfg["ui"].get("hotkeys", True):
            QShortcut(QKeySequence("Space"), self, activated=self.engine.toggle_pause)  # Space
            QShortcut(QKeySequence("P"), self, activated=self.engine.toggle_pause)      # P
            QShortcut(QKeySequence("S"), self, activated=self.engine.skip)             # S
            QShortcut(QKeySequence("R"), self, activated=self.engine.reset)            # R
            QShortcut(QKeySequence("Esc"), self, activated=self.close)                # Esc

        # Timer (UI drives engine)
        self._last = time.monotonic()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_tick)
        self.timer.start(int(cfg["ui"].get("tick_ms", 100)))

        # initial paint
        self.render(self.engine.snapshot())

    def on_tick(self):
        now = time.monotonic()
        dt = now - self._last
        self._last = now
        self.engine.tick(dt)

    def render(self, snap: Snapshot):
        mode_text = {
            Mode.WORK: "WORK",
            Mode.SHORT_BREAK: "SHORT BREAK",
            Mode.LONG_BREAK: "LONG BREAK",
        }[snap.mode]

        if snap.paused:
            mode_text += "  •  PAUSED"

        self.mode_lbl.setText(mode_text)
        self.time_lbl.setText(format_hhmmss(snap.remaining))
        self.meta_lbl.setText(f"Work sessions done: {snap.work_sessions_done}")

# ----------------------------
# Entrypoint
# ----------------------------

def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    cfg = load_config(config_path)

    app = QApplication(sys.argv)
    try_load_qss(app, cfg["ui"].get("theme_file", "theme.qss"))

    w = PomodoroWindow(cfg)
    w.resize(520, 260)
    w.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()