"""Modern audio playback controls widget."""

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QLabel,
)
from PySide6.QtCore import Qt, Signal

from ..core.config import UIColors


class ModernPlayControls(QWidget):
    """Modern compact play controls with volume control."""

    # Signals
    play_pause_requested = Signal()
    stop_requested = Signal()
    volume_changed = Signal(float)  # Volume as 0.0-1.0

    def __init__(self, parent=None):
        """Initialize the modern play controls."""
        super().__init__(parent)

        # State
        self._is_playing = False

        # Setup UI
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(15)

        # Play/Pause button - modern circular design
        self.play_button = QPushButton("Play")
        self.play_button.setFixedSize(60, 36)
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 12px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)

        # Stop button - modern circular design
        self.stop_button = QPushButton("Stop")
        self.stop_button.setFixedSize(50, 32)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 11px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #a61e1e;
            }
        """)

        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 11px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #a61e1e;
            }
        """)

        # Volume control
        volume_label = QLabel("Volume:")
        volume_label.setStyleSheet(f"color: {UIColors.TEXT_PRIMARY}; font-size: 11px;")

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(120)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 6px;
                background: #555;
                margin: 2px 0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                border: 1px solid #4CAF50;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #4CAF50;
                border-radius: 3px;
            }
        """)

        layout.addWidget(self.play_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(volume_label)
        layout.addWidget(self.volume_slider)
        layout.addStretch()

    def _connect_signals(self) -> None:
        """Connect signals."""
        self.play_button.clicked.connect(self.play_pause_requested.emit)
        self.stop_button.clicked.connect(self.stop_requested.emit)
        self.volume_slider.valueChanged.connect(
            lambda value: self.volume_changed.emit(value / 100.0)
        )

    def update_play_state(self, is_playing: bool) -> None:
        """Update the play button state."""
        self._is_playing = is_playing

        # Use text labels that are clear and readable
        if is_playing:
            self.play_button.setText("Pause")
        else:
            self.play_button.setText("Play")
