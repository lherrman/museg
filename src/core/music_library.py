"""Music library management and file operations."""

import shutil
import re
from pathlib import Path
from typing import List, Optional
from PySide6.QtCore import QObject, Signal

from ..core.config import AppConfig
from ..audio.processor import AudioProcessor


class MusicLibrary(QObject):
    """Manages the music library and file operations."""

    # Signals
    library_updated = Signal()
    file_added = Signal(str)  # file_path
    file_add_failed = Signal(str, str)  # file_path, error_message
    file_removed = Signal(str)  # file_path

    def __init__(self, project_dir: Optional[Path] = None):
        super().__init__()
        if project_dir:
            self._music_directory = project_dir / "music"
        else:
            self._music_directory = AppConfig.get_music_directory()
        self._music_directory.mkdir(parents=True, exist_ok=True)
        self._processor = AudioProcessor()

    def set_project_directory(self, project_dir: Path) -> None:
        """Set a new project directory for the music library."""
        self._music_directory = project_dir / "music"
        self._music_directory.mkdir(parents=True, exist_ok=True)
        self.library_updated.emit()

    @property
    def music_directory(self) -> Path:
        """Get the music directory path."""
        return self._music_directory

    def _get_next_track_number(self) -> int:
        """
        Get the next available track number by examining existing files.

        Returns:
            Next available track number (0-based)
        """
        existing_files = self.get_audio_files()
        max_number = -1

        # Pattern to match files starting with 5-digit numbers
        number_pattern = re.compile(r"^(\d{5})_")

        for file_path in existing_files:
            match = number_pattern.match(file_path.name)
            if match:
                number = int(match.group(1))
                max_number = max(max_number, number)

        return max_number + 1

    def get_audio_files(self) -> List[Path]:
        """
        Get all audio files in the music library.

        Returns:
            List of Path objects for audio files, sorted by track number prefix
        """
        audio_files = []
        for file_path in self._music_directory.glob("*"):
            if self._processor.is_supported_format(str(file_path)):
                audio_files.append(file_path)

        # Sort files by track number prefix, then by name
        def sort_key(path: Path) -> tuple:
            filename = path.name
            # Check if filename starts with 5-digit number
            number_match = re.match(r"^(\d{5})_", filename)
            if number_match:
                return (int(number_match.group(1)), filename.lower())
            else:
                # Files without number prefix go at the end
                return (999999, filename.lower())

        return sorted(audio_files, key=sort_key)

    def add_files(self, file_paths: List[str]) -> None:
        """
        Add files to the music library by copying them.

        Args:
            file_paths: List of file paths to add
        """
        for file_path in file_paths:
            try:
                self._add_single_file(file_path)
            except Exception as e:
                self.file_add_failed.emit(file_path, str(e))

        self.library_updated.emit()

    def _add_single_file(self, file_path: str) -> None:
        """
        Add a single file to the library.

        Args:
            file_path: Path to the file to add

        Raises:
            Exception: If file addition fails
        """
        source_path = Path(file_path)

        # Check if file format is supported
        if not self._processor.is_supported_format(file_path):
            raise Exception(f"Unsupported file format: {source_path.suffix}")

        # Generate destination path
        dest_path = self._get_unique_destination_path(source_path)

        # Copy file
        shutil.copy2(file_path, dest_path)
        self.file_added.emit(str(dest_path))

    def _get_unique_destination_path(self, source_path: Path) -> Path:
        """
        Get a unique destination path with auto-incrementing number prefix.

        Args:
            source_path: Source file path

        Returns:
            Unique destination path with format: 00000_filename.ext
        """
        # Get the next available track number
        track_number = self._get_next_track_number()

        # Format as 5-digit number with leading zeros
        number_prefix = f"{track_number:05d}"

        # Create new filename with prefix
        new_filename = f"{number_prefix}_{source_path.name}"
        dest_path = self._music_directory / new_filename

        # This should be unique due to the incrementing number system,
        # but double-check just in case
        counter = 1
        while dest_path.exists():
            stem = source_path.stem
            suffix = source_path.suffix
            new_filename = f"{number_prefix}_{stem}_{counter}{suffix}"
            dest_path = self._music_directory / new_filename
            counter += 1

        return dest_path

    def remove_file(self, file_path: str) -> bool:
        """
        Remove a file from the library.

        Args:
            file_path: Path to the file to remove

        Returns:
            True if file was successfully removed
        """
        try:
            path = Path(file_path)
            if path.exists() and path.parent == self._music_directory:
                path.unlink()
                self.file_removed.emit(str(path))
                self.library_updated.emit()
                return True
            else:
                return False
        except Exception as e:
            print(f"Error removing file {file_path}: {e}")
            return False

    def file_exists(self, file_name: str) -> bool:
        """
        Check if a file exists in the library.

        Args:
            file_name: Name of the file to check

        Returns:
            True if file exists
        """
        return (self._music_directory / file_name).exists()
