"""Waveform visualization widget."""

import matplotlib

matplotlib.use("Qt5Agg")  # Ensure Qt backend is used

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Signal, QTimer
from typing import Optional

from ..core.config import UIColors
from ..audio.processor import AudioData, AudioProcessor


class WaveformWidget(FigureCanvas):
    """Custom widget for displaying audio waveforms with interactive controls."""

    # Signals
    position_changed = Signal(float)  # position in seconds

    def __init__(self, parent=None):
        """Initialize the waveform widget."""
        # Create figure with dark background and minimal margins for better alignment
        self.figure = Figure(
            figsize=(12, 4),
            facecolor=UIColors.BACKGROUND,
            tight_layout={"pad": 0.3, "w_pad": 0.0, "h_pad": 0.0},
        )
        super().__init__(self.figure)
        self.setParent(parent)

        # Setup plot axes
        self.axes = self.figure.add_subplot(111, facecolor=UIColors.BACKGROUND)
        self._setup_axes_style()

        # Audio data
        self._audio_data: Optional[AudioData] = None
        self._position_line = None
        self._current_position = 0.0
        self._drag_position_line = None  # Line showing drag position

        # Loading animation
        self._loading_timer = QTimer()
        self._loading_timer.timeout.connect(self._update_loading_animation)
        self._loading_dots = 0
        self._loading_file_name = ""

        # Setup event handling
        self.mpl_connect("button_press_event", self._on_click)

        # Show initial empty state
        self._show_empty_state()

    def _setup_axes_style(self) -> None:
        """Setup the visual style of the axes."""
        self.axes.tick_params(colors=UIColors.TEXT_PRIMARY)
        for spine in self.axes.spines.values():
            spine.set_color(UIColors.TEXT_PRIMARY)

    def _show_empty_state(self) -> None:
        """Display empty state message."""
        self.axes.clear()
        self.axes.text(
            0.5,
            0.5,
            "No audio loaded\nDrag and drop audio files or select from library",
            horizontalalignment="center",
            verticalalignment="center",
            transform=self.axes.transAxes,
            color=UIColors.TEXT_PRIMARY,
            fontsize=14,
        )
        self._apply_axes_style()
        self.draw()

    def show_loading_state(self, file_name: str = "") -> None:
        """Display loading state message with animation."""
        self._loading_file_name = file_name
        self._loading_dots = 0

        # Start animation timer
        self._loading_timer.start(500)  # Update every 500ms

        # Show initial loading state
        self._update_loading_animation()

    def _update_loading_animation(self) -> None:
        """Update the loading animation."""
        self.axes.clear()

        # Create animated dots
        dots = "." * (self._loading_dots % 4)
        loading_text = f"Loading audio waveform{dots}"
        if self._loading_file_name:
            loading_text += f"\n{self._loading_file_name}"

        self.axes.text(
            0.5,
            0.5,
            loading_text,
            horizontalalignment="center",
            verticalalignment="center",
            transform=self.axes.transAxes,
            color=UIColors.TEXT_PRIMARY,
            fontsize=14,
            alpha=0.8,  # Slightly dimmed to indicate processing
        )
        self._apply_axes_style()
        self.draw()

        self._loading_dots += 1

    def hide_loading_state(self) -> None:
        """Hide loading state and stop animation."""
        self._loading_timer.stop()
        self._loading_file_name = ""
        self._loading_dots = 0

    def _show_error_state(self, error_message: str) -> None:
        """Display error state message."""
        self.axes.clear()
        self.axes.text(
            0.5,
            0.5,
            f"Error loading audio:\n{error_message}",
            horizontalalignment="center",
            verticalalignment="center",
            transform=self.axes.transAxes,
            color=UIColors.TEXT_ERROR,
            fontsize=12,
        )
        self._apply_axes_style()
        self.draw()

    def _apply_axes_style(self) -> None:
        """Apply consistent styling to axes."""
        self.axes.set_xlim(0, 1)
        self.axes.set_ylim(0, 1)
        self.axes.set_facecolor(UIColors.BACKGROUND)
        self.axes.tick_params(colors=UIColors.TEXT_PRIMARY)
        for spine in self.axes.spines.values():
            spine.set_color(UIColors.TEXT_PRIMARY)

    def load_audio_data(self, audio_data: AudioData) -> bool:
        """
        Load and display audio data.

        Args:
            audio_data: AudioData object with loaded audio

        Returns:
            True if successfully displayed
        """
        try:
            # Hide loading state
            self.hide_loading_state()

            if not audio_data.loaded:
                raise ValueError("Audio data not loaded")

            self._audio_data = audio_data

            # Prepare waveform for display
            time_axis, amplitude_data = AudioProcessor.prepare_waveform_for_display(
                audio_data
            )

            # Clear and plot waveform
            self.axes.clear()
            self.axes.plot(
                time_axis,
                amplitude_data,
                color=UIColors.WAVEFORM_COLOR,
                linewidth=0.8,
                alpha=0.8,
            )

            # Setup axes
            self.axes.set_xlim(0, audio_data.duration)
            self.axes.set_ylim(-1.1, 1.1)
            # Move x-axis label to the top to reduce separation with label bar
            self.axes.xaxis.set_label_position("top")
            self.axes.set_xlabel(
                "Time (seconds)", color=UIColors.TEXT_PRIMARY, fontsize=10
            )
            # Remove y-axis label to maximize plot width for alignment with label bar
            self.axes.set_ylabel("")
            self.axes.grid(True, alpha=0.2, color=UIColors.GRID_COLOR, linewidth=0.5)

            # Apply styling
            self.axes.set_facecolor(UIColors.BACKGROUND)
            self.axes.tick_params(colors=UIColors.TEXT_PRIMARY, labelsize=9)
            # Remove y-axis ticks to save space and move x-axis ticks to top
            self.axes.tick_params(
                left=False,
                labelleft=False,
                top=True,
                labeltop=True,
                bottom=False,
                labelbottom=False,
            )
            for spine in self.axes.spines.values():
                spine.set_color(UIColors.TEXT_PRIMARY)

            # Add position indicator
            self._position_line = self.axes.axvline(
                x=0, color=UIColors.POSITION_LINE_COLOR, linewidth=2, alpha=0.9
            )

            # Force redraw
            self.figure.tight_layout()
            self.draw()

            return True

        except Exception as e:
            self.hide_loading_state()
            self._show_error_state(str(e))
            return False

    def update_position(self, position_seconds: float) -> None:
        """
        Update the position indicator on the waveform.

        Args:
            position_seconds: Current position in seconds
        """
        if (
            self._position_line is not None
            and self._audio_data is not None
            and self._audio_data.duration > 0
        ):
            self._current_position = position_seconds
            self._position_line.set_xdata([position_seconds])
            self.draw_idle()

    def clear(self) -> None:
        """Clear the waveform and show empty state."""
        self._audio_data = None
        self._position_line = None
        self._current_position = 0.0
        self._drag_position_line = None
        self._show_empty_state()

    def _on_click(self, event) -> None:
        """
        Handle mouse clicks on the waveform.

        Args:
            event: Matplotlib mouse event
        """
        if (
            event.inaxes == self.axes
            and self._audio_data is not None
            and self._audio_data.duration > 0
        ):
            clicked_time = event.xdata
            if clicked_time is not None:
                # Clamp to valid range
                clicked_time = max(0, min(clicked_time, self._audio_data.duration))
                self.position_changed.emit(clicked_time)

    @property
    def has_audio(self) -> bool:
        """Check if audio data is loaded."""
        return self._audio_data is not None and self._audio_data.loaded

    @property
    def duration(self) -> float:
        """Get the duration of loaded audio."""
        if self._audio_data:
            return self._audio_data.duration
        return 0.0

    @property
    def current_position(self) -> float:
        """Get the current position in seconds."""
        return self._current_position

    def show_drag_position(self, position_seconds: float) -> None:
        """
        Show a drag position indicator on the waveform.

        Args:
            position_seconds: Position in seconds to show the drag line
        """
        if (
            self._audio_data is not None
            and self._audio_data.loaded
            and self._audio_data.duration > 0
        ):
            # Remove existing drag line if any
            if self._drag_position_line is not None:
                self._drag_position_line.remove()

            # Add new drag position line (fine gray line)
            self._drag_position_line = self.axes.axvline(
                x=position_seconds,
                color="#888888",  # Gray color
                linewidth=1,
                alpha=0.7,
                linestyle="--",  # Dashed line to distinguish from position line
            )
            self.draw_idle()

    def hide_drag_position(self) -> None:
        """Hide the drag position indicator."""
        if self._drag_position_line is not None:
            self._drag_position_line.remove()
            self._drag_position_line = None
            self.draw_idle()
