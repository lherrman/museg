"""Music library list widget with drag and drop support."""

from pathlib import Path
from typing import List
from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtCore import Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtCore import Qt

from ..core.config import UIStyles
from ..audio.processor import AudioProcessor


class MusicListWidget(QListWidget):
    """Custom list widget for music library with drag and drop support."""

    # Signals
    files_dropped = Signal(list)  # List of file paths
    track_selected = Signal(str)  # File path

    def __init__(self, parent=None):
        """Initialize the music list widget."""
        super().__init__(parent)

        # Setup drag and drop
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.DropOnly)

        # Apply styling
        self.setStyleSheet(UIStyles.LIST_WIDGET_STYLESHEET)

        # Connect signals
        self.currentItemChanged.connect(self._on_current_item_changed)

        # Audio processor for format checking
        self._processor = AudioProcessor()

    def add_audio_file(self, file_path: str) -> None:
        """
        Add an audio file to the list.

        Args:
            file_path: Path to the audio file
        """
        path = Path(file_path)
        item = QListWidgetItem(path.name)
        item.setData(Qt.ItemDataRole.UserRole, str(file_path))
        item.setToolTip(str(path))  # Show full path on hover
        self.addItem(item)

    def refresh_from_file_list(self, file_paths: List[str]) -> None:
        """
        Refresh the list from a list of file paths.

        Args:
            file_paths: List of file paths to display
        """
        self.clear()
        for file_path in file_paths:
            self.add_audio_file(file_path)

    def get_selected_file_path(self) -> str:
        """
        Get the file path of the currently selected item.

        Returns:
            File path string, empty if no selection
        """
        current_item = self.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return ""

    def select_file(self, file_path: str) -> bool:
        """
        Select a specific file in the list.

        Args:
            file_path: Path to the file to select

        Returns:
            True if file was found and selected
        """
        for i in range(self.count()):
            item = self.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == file_path:
                self.setCurrentItem(item)
                return True
        return False

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            # Check if any of the dragged files are supported
            supported_files = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if self._processor.is_supported_format(file_path):
                    supported_files.append(file_path)

            if supported_files:
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop events."""
        supported_files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if self._processor.is_supported_format(file_path):
                supported_files.append(file_path)

        if supported_files:
            self.files_dropped.emit(supported_files)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def _on_current_item_changed(
        self, current: QListWidgetItem, previous: QListWidgetItem
    ) -> None:
        """Handle item selection changes."""
        if current:
            file_path = current.data(Qt.ItemDataRole.UserRole)
            if file_path:
                self.track_selected.emit(file_path)
