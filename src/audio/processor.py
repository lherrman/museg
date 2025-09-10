"""Audio processing and management module."""

import librosa
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
from PySide6.QtCore import QThread, Signal

from ..core.config import AppConfig


class AudioData:
    """Container for audio data and metadata."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.waveform: Optional[np.ndarray] = None
        self.sample_rate: Optional[float] = None
        self.duration: float = 0.0
        self.loaded: bool = False

    @property
    def file_name(self) -> str:
        """Get the filename without path."""
        return self.file_path.name

    @property
    def display_name(self) -> str:
        """Get a display-friendly name."""
        return self.file_path.stem


class AudioProcessor:
    """Handles audio file loading and processing."""

    @staticmethod
    def load_audio(file_path: str) -> AudioData:
        """
        Load audio file and return AudioData object.

        Args:
            file_path: Path to the audio file

        Returns:
            AudioData object with loaded audio information

        Raises:
            Exception: If audio loading fails
        """
        audio_data = AudioData(file_path)

        try:
            # Load audio file with librosa
            y, sr = librosa.load(file_path, sr=None)

            audio_data.waveform = y
            audio_data.sample_rate = sr
            audio_data.duration = len(y) / sr
            audio_data.loaded = True

            return audio_data

        except Exception as e:
            raise Exception(f"Failed to load audio file: {str(e)}")

    @staticmethod
    def prepare_waveform_for_display(
        audio_data: AudioData,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare waveform data for display by downsampling if necessary.

        Args:
            audio_data: AudioData object with loaded audio

        Returns:
            Tuple of (time_axis, amplitude_data) for plotting
        """
        if not audio_data.loaded or audio_data.waveform is None:
            raise ValueError("Audio data not loaded")

        y = audio_data.waveform
        duration = audio_data.duration

        # Downsample for display if too many samples
        max_points = AppConfig.MAX_WAVEFORM_POINTS
        if len(y) > max_points:
            step = len(y) // max_points
            y_display = y[::step]
            time_display = np.linspace(0, duration, len(y_display))
        else:
            y_display = y
            time_display = np.linspace(0, duration, len(y))

        return time_display, y_display

    @staticmethod
    def is_supported_format(file_path: str) -> bool:
        """
        Check if the file format is supported.

        Args:
            file_path: Path to the file

        Returns:
            True if format is supported
        """
        path = Path(file_path)
        return path.suffix.lower() in AppConfig.SUPPORTED_AUDIO_FORMATS


class AudioWorker(QThread):
    """Worker thread for loading audio files without blocking the UI."""

    # Signals
    loading_started = Signal(str)  # file_path
    loading_finished = Signal(AudioData)  # audio_data
    loading_failed = Signal(str, str)  # file_path, error_message

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self._processor = AudioProcessor()

    def run(self):
        """Run the audio loading in background thread."""
        try:
            self.loading_started.emit(self.file_path)
            audio_data = self._processor.load_audio(self.file_path)
            self.loading_finished.emit(audio_data)
        except Exception as e:
            self.loading_failed.emit(self.file_path, str(e))
