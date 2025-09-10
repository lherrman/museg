"""Left panel containing music library and controls."""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont

from ..core.config import UIColors, AppConfig
from .music_list_widget import MusicListWidget


class LeftPanel(QFrame):
    """Left panel containing the music library."""

    # Signals
    add_files_requested = Signal()
    files_dropped = Signal(list)  # List of file paths
    track_selected = Signal(str)  # File path
    remove_file_requested = Signal(str)  # File path

    def __init__(self, parent=None):
        """Initialize the left panel."""
        super().__init__(parent)

        # Setup panel
        self.setFixedWidth(AppConfig.LEFT_PANEL_WIDTH)

        # Setup UI
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Music Library")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {UIColors.TEXT_PRIMARY}; padding: 10px;")
        layout.addWidget(title)

        # Instructions
        instructions = QLabel("Drop audio files here or use the button below")
        instructions.setFont(QFont("Arial", 9))
        instructions.setStyleSheet(
            f"color: {UIColors.TEXT_SECONDARY}; padding: 5px; font-style: italic;"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Music list
        self.music_list = MusicListWidget()
        layout.addWidget(self.music_list)

        # Add music button
        self.add_button = QPushButton("Add Music Files")
        layout.addWidget(self.add_button)

        # Remove music button
        self.remove_button = QPushButton("Remove Selected File")
        self.remove_button.setEnabled(False)  # Disabled until a file is selected
        layout.addWidget(self.remove_button)
        layout.addWidget(self.remove_button)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self.add_button.clicked.connect(self.add_files_requested.emit)
        self.remove_button.clicked.connect(self._remove_selected_file)
        self.music_list.files_dropped.connect(self.files_dropped.emit)
        self.music_list.track_selected.connect(self.track_selected.emit)
        self.music_list.track_selected.connect(self._on_track_selected)

    def _remove_selected_file(self) -> None:
        """Remove the currently selected file."""
        selected_file = self.music_list.get_selected_file_path()
        if selected_file:
            self.remove_file_requested.emit(selected_file)

    def _on_track_selected(self, file_path: str) -> None:
        """Handle track selection to enable/disable remove button."""
        self.remove_button.setEnabled(bool(file_path))

    def refresh_music_list(self, file_paths: list) -> None:
        """
        Refresh the music list with new file paths.

        Args:
            file_paths: List of file paths to display
        """
        self.music_list.refresh_from_file_list([str(path) for path in file_paths])

    def get_selected_file_path(self) -> str:
        """Get the currently selected file path."""
        return self.music_list.get_selected_file_path()

    def select_file(self, file_path: str) -> bool:
        """
        Select a specific file in the list.

        Args:
            file_path: Path to the file to select

        Returns:
            True if file was found and selected
        """
        return self.music_list.select_file(file_path)
