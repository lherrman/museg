"""Label buttons widget for creating labeled segments."""

from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..core.label_manager import LabelDefinition


class LabelButton(QPushButton):
    """Custom button for label creation."""

    def __init__(self, label_def: LabelDefinition, parent=None):
        super().__init__(label_def.name, parent)
        self.label_def = label_def

        # Style the button with the label's color
        self.setFixedHeight(35)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {label_def.color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 5px 15px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(label_def.color)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(label_def.color, 0.3)};
            }}
        """)

        # Set tooltip
        self.setToolTip(f"{label_def.name}: {label_def.description}")

    def _darken_color(self, hex_color: str, factor: float = 0.2) -> str:
        """Darken a hex color by a factor."""
        # Remove the # if present
        hex_color = hex_color.lstrip("#")

        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Darken
        r = int(r * (1 - factor))
        g = int(g * (1 - factor))
        b = int(b * (1 - factor))

        return f"#{r:02x}{g:02x}{b:02x}"


class LabelButtonsWidget(QFrame):
    """Widget containing all label creation buttons."""

    # Signals
    label_requested = Signal(str)  # label_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(55)
        self.setStyleSheet("""
            QFrame {
                background-color: #3c3c3c;
                border-radius: 8px;
                padding: 5px;
            }
        """)

        self._label_definitions: List[LabelDefinition] = []
        self._current_position: float = 0.0
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title label
        title_label = QLabel("Add Label:")
        title_label.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        title_label.setFixedWidth(80)
        layout.addWidget(title_label)

        # Container for buttons (will be populated when labels are set)
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(5)
        layout.addLayout(self.buttons_layout)

        layout.addStretch()

    def set_label_definitions(self, label_definitions: List[LabelDefinition]) -> None:
        """Set the available label definitions and create buttons."""
        self._label_definitions = label_definitions

        # Clear existing buttons
        while self.buttons_layout.count():
            child = self.buttons_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Create buttons for each label
        for label_def in label_definitions:
            button = LabelButton(label_def)
            button.clicked.connect(
                lambda checked, lid=label_def.id: self.label_requested.emit(lid)
            )
            self.buttons_layout.addWidget(button)

    def set_current_position(self, position_seconds: float) -> None:
        """Update the current position for label creation."""
        self._current_position = position_seconds

    def get_current_position(self) -> float:
        """Get the current position."""
        return self._current_position
