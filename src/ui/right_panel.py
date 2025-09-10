"""Right panel containing waveform and audio controls."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtMultimedia import QMediaPlayer

from ..core.config import UIColors, AppConfig
from ..audio.processor import AudioData
from .waveform_widget import WaveformWidget
from .audio_controls import ModernPlayControls
from .label_buttons import LabelButtonsWidget
from .label_bar import LabelBar


class RightPanel(QWidget):
    """Right panel containing waveform display and modern play controls."""

    # Signals
    play_pause_requested = Signal()
    stop_requested = Signal()
    volume_changed = Signal(float)
    waveform_position_changed = Signal(float)  # Position in seconds
    label_requested = Signal(str, float)  # label_id, position_seconds
    label_boundary_moved = Signal(
        int, str, float
    )  # segment_index, boundary_type, new_time
    label_segment_selected = Signal(int)  # segment_index
    label_segment_deleted = Signal(int)  # segment_index
    label_segment_moved = Signal(
        int, float, float
    )  # segment_index, new_start_time, new_end_time

    def __init__(self, parent=None):
        """Initialize the right panel."""
        super().__init__(parent)

        # Setup UI
        self._setup_ui()
        self._connect_signals()

        # State
        self._current_track_name = ""

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)  # Reduce overall spacing

        # Current track info
        self.track_info = QLabel("No track selected")
        self.track_info.setFont(QFont("Arial", 12))
        self.track_info.setStyleSheet(
            f"color: {UIColors.TEXT_PRIMARY}; "
            f"padding: 10px; "
            f"background-color: {UIColors.PANEL_BACKGROUND}; "
            f"border-radius: 5px;"
        )
        layout.addWidget(self.track_info)

        # Modern play controls above waveform
        self.play_controls = ModernPlayControls()
        layout.addWidget(self.play_controls)

        # Waveform display container
        waveform_container = QFrame()
        waveform_container.setFixedHeight(AppConfig.WAVEFORM_HEIGHT)
        waveform_layout = QVBoxLayout(waveform_container)
        waveform_layout.setContentsMargins(0, 0, 0, 0)
        waveform_layout.setSpacing(0)

        self.waveform_widget = WaveformWidget()
        waveform_layout.addWidget(self.waveform_widget)

        layout.addWidget(waveform_container)

        # Label visualization bar - positioned directly below waveform with minimal spacing
        self.label_bar = LabelBar()
        waveform_layout.addWidget(self.label_bar)

        # Add small spacing before label buttons
        layout.addSpacing(10)

        # Label creation buttons
        self.label_buttons = LabelButtonsWidget()
        layout.addWidget(self.label_buttons)

        # Add stretch to push everything to top
        layout.addStretch()

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        # Waveform signals
        self.waveform_widget.position_changed.connect(
            self.waveform_position_changed.emit
        )
        self.waveform_widget.position_changed.connect(
            self.label_buttons.set_current_position
        )

        # Modern play controls signals (play, stop, and volume)
        self.play_controls.play_pause_requested.connect(self.play_pause_requested.emit)
        self.play_controls.stop_requested.connect(self.stop_requested.emit)
        self.play_controls.volume_changed.connect(self.volume_changed.emit)

        # Label creation signals
        self.label_buttons.label_requested.connect(self._on_label_requested)

        # Label bar signals
        self.label_bar.boundary_moved.connect(self.label_boundary_moved.emit)
        self.label_bar.segment_selected.connect(self.label_segment_selected.emit)
        self.label_bar.segment_deleted.connect(self.label_segment_deleted.emit)
        self.label_bar.segment_moved.connect(self.label_segment_moved.emit)

        # Connect boundary dragging signals for waveform feedback
        self.label_bar.boundary_drag_started.connect(self.show_drag_position)
        self.label_bar.boundary_drag_position.connect(self.show_drag_position)
        self.label_bar.boundary_drag_ended.connect(self.hide_drag_position)

    def _on_label_requested(self, label_id: str) -> None:
        """Handle label creation request."""
        current_position = self.label_buttons.get_current_position()
        self.label_requested.emit(label_id, current_position)

    def set_track_loading(self, track_name: str) -> None:
        """
        Set the track info to loading state.

        Args:
            track_name: Name of the track being loaded
        """
        self._current_track_name = track_name
        self.track_info.setText(f"Loading: {track_name}")

        # Show loading state in waveform
        self.waveform_widget.show_loading_state(track_name)

    def set_track_loaded(self, track_name: str) -> None:
        """
        Set the track info to loaded state.

        Args:
            track_name: Name of the loaded track
        """
        self._current_track_name = track_name
        self.track_info.setText(f"♪ {track_name}")

    def set_track_error(self, error_message: str) -> None:
        """
        Set the track info to error state.

        Args:
            error_message: Error message to display
        """
        self.track_info.setText(f"Error: {error_message}")

    def load_audio_data(self, audio_data: AudioData) -> bool:
        """
        Load audio data into the waveform widget.

        Args:
            audio_data: AudioData object to display

        Returns:
            True if successfully loaded
        """
        return self.waveform_widget.load_audio_data(audio_data)

    def update_waveform_position(self, position_seconds: float) -> None:
        """
        Update the position indicator on the waveform.

        Args:
            position_seconds: Current position in seconds
        """
        self.waveform_widget.update_position(position_seconds)

    def set_playback_state(self, state: QMediaPlayer.PlaybackState) -> None:
        """
        Update controls based on playback state.

        Args:
            state: Current playback state
        """
        # Update the modern play controls
        is_playing = state == QMediaPlayer.PlaybackState.PlayingState
        self.play_controls.update_play_state(is_playing)

    def set_duration(self, duration_ms: int) -> None:
        """
        Set the total duration (no longer needed without position slider).

        Args:
            duration_ms: Duration in milliseconds
        """
        # Duration display no longer needed since we removed the position slider
        pass

    def set_position(self, position_ms: int) -> None:
        """
        Set the current position (only update waveform now).

        Args:
            position_ms: Position in milliseconds
        """
        # Only update waveform position since we removed the position slider
        position_seconds = position_ms / 1000.0
        self.update_waveform_position(position_seconds)

    def reset(self) -> None:
        """Reset the panel to initial state."""
        self.track_info.setText("No track selected")
        self.waveform_widget.clear()
        self.play_controls.update_play_state(False)
        self._current_track_name = ""

    def set_label_definitions(self, label_definitions) -> None:
        """Set the available label definitions."""
        self.label_buttons.set_label_definitions(label_definitions)
        self.label_bar.set_label_definitions(label_definitions)

    def set_label_segments(self, segments) -> None:
        """Set the current label segments."""
        self.label_bar.set_segments(segments)

    def set_audio_duration(self, duration_seconds: float) -> None:
        """Set the audio duration for the label bar."""
        self.label_bar.set_duration(duration_seconds)

    @property
    def current_track_name(self) -> str:
        """Get the current track name."""
        return self._current_track_name

    @property
    def has_audio(self) -> bool:
        """Check if audio is loaded."""
        return self.waveform_widget.has_audio

    def set_selected_label_segment(self, segment_index):
        """Set the selected segment in the label bar."""
        self.label_bar.set_selected_segment(segment_index)

    def clear_label_selection(self):
        """Clear the label selection."""
        self.label_bar.clear_selection()

    def set_annotation_mode(self, enabled: bool) -> None:
        """Set whether annotation mode (segment dragging) is enabled."""
        self.label_bar.set_annotation_mode(enabled)

    def show_drag_position(self, position_seconds: float) -> None:
        """Show drag position indicator in the waveform."""
        self.waveform_widget.show_drag_position(position_seconds)

    def hide_drag_position(self) -> None:
        """Hide drag position indicator in the waveform."""
        self.waveform_widget.hide_drag_position()
