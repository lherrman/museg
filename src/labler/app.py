"""Main application class with clean separation of concerns."""

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QSplitter,
    QFileDialog,
    QMessageBox,
    QDialog,
    QLabel,
)
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent, QIcon
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from .core.config import AppConfig, UIStyles
from .core.music_library import MusicLibrary
from .core.label_manager import LabelManager
from .audio import AudioWorker, AudioData
from .ui import LeftPanel, RightPanel


def get_icon_path() -> Optional[Path]:
    """Get the path to the application icon, handling both dev and bundled environments."""
    # Check if running as PyInstaller bundle
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # PyInstaller bundle - try to find bundled icon first
        bundled_icon = Path(sys._MEIPASS) / "assets" / "icon.png"  # type: ignore
        if bundled_icon.exists():
            return bundled_icon
        # Fallback to using embedded exe icon (return None to use default)
        return None
    else:
        # Development environment
        icon_path = Path(__file__).parent / "assets" / "icon.png"
        return icon_path if icon_path.exists() else None


class MuSegApp(QMainWindow):
    """Main application window for the MuSeg Audio Annotation Tool."""

    def __init__(self):
        """Initialize the application."""
        super().__init__()

        # Setup window
        self._setup_window()

        # Initialize core components
        self._init_audio_system()
        self._init_music_library()
        self._init_label_manager()

        # Setup UI
        self._setup_ui()
        self._setup_toolbar()
        self._apply_styling()

        # Connect signals
        self._connect_signals()

        # Initialize state
        self._current_audio_worker: Optional[AudioWorker] = None
        self._current_file_path: Optional[str] = None

        # Setup timers
        self._setup_timers()

        # Load initial music library
        self._refresh_music_library()

    def _setup_window(self) -> None:
        """Setup main window properties."""
        self.setWindowTitle(AppConfig.APP_NAME)
        self.setGeometry(100, 100, *AppConfig.DEFAULT_WINDOW_SIZE)
        self.setMinimumSize(*AppConfig.MIN_WINDOW_SIZE)

        # Set application icon
        icon_path = get_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(str(icon_path)))

        # Enable drag and drop for the main window
        self.setAcceptDrops(True)

    def _init_audio_system(self) -> None:
        """Initialize the audio playback system."""
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

        # Set initial volume
        self.audio_output.setVolume(0.5)

    def _init_music_library(self) -> None:
        """Initialize the music library manager."""
        self.music_library = MusicLibrary()

    def _init_label_manager(self) -> None:
        """Initialize the label management system."""
        self.label_manager = LabelManager(
            labels_directory=AppConfig.get_labels_directory(),
            config_file=AppConfig.get_label_config_file(),
        )

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Create splitter for resizable panes
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Create panels
        self.left_panel = LeftPanel()
        self.right_panel = RightPanel()

        splitter.addWidget(self.left_panel)
        splitter.addWidget(self.right_panel)

        # Set splitter proportions (left panel width is fixed)
        splitter.setSizes([AppConfig.LEFT_PANEL_WIDTH, 1100])

    def _setup_toolbar(self) -> None:
        """Setup the application toolbar with menus."""
        # Create menubar for better organization
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        # New Project action
        new_project_action = QAction("New Project...", self)
        new_project_action.triggered.connect(self._show_new_project_dialog)
        file_menu.addAction(new_project_action)

        # Open Project action
        open_project_action = QAction("Open Project...", self)
        open_project_action.triggered.connect(self._show_open_project_dialog)
        file_menu.addAction(open_project_action)

        # Project menu
        project_menu = menubar.addMenu("Project")

        # Edit Labels action
        edit_labels_action = QAction("Edit Labels...", self)
        edit_labels_action.triggered.connect(self._show_label_editor)
        project_menu.addAction(edit_labels_action)

        project_menu.addSeparator()

        # Add music action
        add_action = QAction("Add Music Files...", self)
        add_action.triggered.connect(self._show_add_files_dialog)
        project_menu.addAction(add_action)

        # Refresh action
        refresh_action = QAction("Refresh Library", self)
        refresh_action.triggered.connect(self._refresh_music_library)
        project_menu.addAction(refresh_action)

        # Status bar for mode indicator
        self.status_bar = self.statusBar()
        self.mode_label = QLabel()
        self.status_bar.addPermanentWidget(self.mode_label)
        self._update_mode_indicator()

    def _update_mode_indicator(self):
        """Update the mode indicator in the status bar."""
        if hasattr(self, "label_manager"):
            mode = self.label_manager.get_labeling_mode()
            mode_text = f"Mode: {mode.title()}"
            if mode == "segmentation":
                mode_text += " (Connected segments)"
            else:
                mode_text += " (Free placement)"
            self.mode_label.setText(mode_text)
            self.mode_label.setStyleSheet("color: #888; padding: 2px 8px;")

            # Update annotation mode in right panel
            if hasattr(self, "right_panel"):
                self.right_panel.set_annotation_mode(mode == "annotation")

    def _apply_styling(self) -> None:
        """Apply application styling."""
        self.setStyleSheet(UIStyles.MAIN_STYLESHEET)

    def _connect_signals(self) -> None:
        """Connect all signal handlers."""
        # Music library signals
        self.music_library.library_updated.connect(self._refresh_music_library)
        self.music_library.file_add_failed.connect(self._handle_file_add_error)

        # Left panel signals
        self.left_panel.add_files_requested.connect(self._show_add_files_dialog)
        self.left_panel.files_dropped.connect(self._handle_dropped_files)
        self.left_panel.track_selected.connect(self._load_track)
        self.left_panel.remove_file_requested.connect(self._remove_file)

        # Right panel signals
        self.right_panel.play_pause_requested.connect(self._toggle_playback)
        self.right_panel.stop_requested.connect(self._stop_playback)
        self.right_panel.volume_changed.connect(self._set_volume)
        self.right_panel.waveform_position_changed.connect(self._seek_to_position)
        self.right_panel.label_requested.connect(self._create_label_segment)
        self.right_panel.label_boundary_moved.connect(self._move_label_boundary)
        self.right_panel.label_segment_selected.connect(self._select_label_segment)
        self.right_panel.label_segment_deleted.connect(self._delete_label_segment)
        self.right_panel.label_segment_moved.connect(self._move_label_segment)

        # Media player signals
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.playbackStateChanged.connect(self._on_playback_state_changed)

    def _setup_timers(self) -> None:
        """Setup application timers."""
        # Position update timer
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self._update_position)
        self.position_timer.start(AppConfig.POSITION_UPDATE_INTERVAL_MS)

    def _show_add_files_dialog(self) -> None:
        """Show file dialog to add music files."""
        file_filter = "Audio Files (*.mp3 *.wav);;MP3 Files (*.mp3);;WAV Files (*.wav)"
        files, _ = QFileDialog.getOpenFileNames(
            self, "Add Music Files", "", file_filter
        )

        if files:
            self._handle_dropped_files(files)

    def _handle_dropped_files(self, file_paths: list) -> None:
        """
        Handle files dropped onto the application.

        Args:
            file_paths: List of file paths to add
        """
        self.music_library.add_files(file_paths)

    def _handle_file_add_error(self, file_path: str, error_message: str) -> None:
        """
        Handle file addition errors.

        Args:
            file_path: Path to the file that failed
            error_message: Error message
        """
        file_name = Path(file_path).name
        QMessageBox.warning(
            self, "Error Adding File", f"Failed to add {file_name}:\n{error_message}"
        )

    def _refresh_music_library(self) -> None:
        """Refresh the music library display."""
        audio_files = self.music_library.get_audio_files()
        self.left_panel.refresh_music_list(audio_files)

    def _load_track(self, file_path: str) -> None:
        """
        Load a track for playback and visualization.

        Args:
            file_path: Path to the audio file
        """
        self._current_file_path = file_path
        file_name = Path(file_path).name

        # Update UI
        self.right_panel.set_track_loading(file_name)

        # Stop current playback
        self.media_player.stop()

        # Cancel any running audio worker
        if self._current_audio_worker and self._current_audio_worker.isRunning():
            self._current_audio_worker.terminate()
            self._current_audio_worker.wait()

        # Load audio in background thread
        self._current_audio_worker = AudioWorker(file_path)
        self._current_audio_worker.loading_finished.connect(self._on_audio_loaded)
        self._current_audio_worker.loading_failed.connect(self._on_audio_load_failed)
        self._current_audio_worker.start()

        # Set media source
        self.media_player.setSource(QUrl.fromLocalFile(file_path))

        # Initialize labels for this track
        self._init_track_labels(file_path)

    def _on_audio_loaded(self, audio_data: AudioData) -> None:
        """
        Handle successful audio loading.

        Args:
            audio_data: Loaded audio data
        """
        success = self.right_panel.load_audio_data(audio_data)
        if success:
            self.right_panel.set_track_loaded(audio_data.file_name)
            # Set the duration for the label bar
            self.right_panel.set_audio_duration(audio_data.duration)
        else:
            self.right_panel.set_track_error("Failed to display waveform")

    def _on_audio_load_failed(self, file_path: str, error_message: str) -> None:
        """
        Handle audio loading failure.

        Args:
            file_path: Path to the file that failed
            error_message: Error message
        """
        self.right_panel.set_track_error(error_message)

    def _toggle_playback(self) -> None:
        """Toggle between play and pause."""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def _stop_playback(self) -> None:
        """Stop playback."""
        self.media_player.stop()

    def _set_volume(self, volume: float) -> None:
        """
        Set audio volume.

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.audio_output.setVolume(volume)

    def _seek_to_position(self, position_seconds: float) -> None:
        """
        Seek to a specific position in the track.

        Args:
            position_seconds: Position in seconds
        """
        position_ms = int(position_seconds * 1000)
        self.media_player.setPosition(position_ms)

    def _on_position_changed(self, position_ms: int) -> None:
        """
        Handle position changes from media player.

        Args:
            position_ms: Current position in milliseconds
        """
        self.right_panel.set_position(position_ms)

    def _on_duration_changed(self, duration_ms: int) -> None:
        """
        Handle duration changes from media player.

        Args:
            duration_ms: Duration in milliseconds
        """
        self.right_panel.set_duration(duration_ms)

    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        """
        Handle playback state changes.

        Args:
            state: New playback state
        """
        self.right_panel.set_playback_state(state)

    def _update_position(self) -> None:
        """Update position display (called by timer)."""
        # This is handled by media player signals, but kept for future use
        pass

    def closeEvent(self, event) -> None:
        """Handle application close event."""
        # Stop any running audio worker
        if self._current_audio_worker and self._current_audio_worker.isRunning():
            self._current_audio_worker.terminate()
            self._current_audio_worker.wait()

        # Stop media player
        self.media_player.stop()

        event.accept()

    # Label management methods

    def _init_track_labels(self, file_path: str) -> None:
        """Initialize labels for a track."""
        # Load track labels
        track_labels = self.label_manager.load_track_labels(file_path)

        # Set up label definitions in UI
        label_definitions = self.label_manager.get_label_definitions()
        self.right_panel.set_label_definitions(label_definitions)

        # Set current segments
        segments = track_labels.get_segments()
        self.right_panel.set_label_segments(segments)

        # Connect track labels signals
        track_labels.labels_changed.connect(self._on_labels_changed)

    def _on_labels_changed(self) -> None:
        """Handle changes to track labels."""
        # Update label definitions in UI (colors, names, etc.)
        label_definitions = self.label_manager.get_label_definitions()
        self.right_panel.set_label_definitions(label_definitions)

        # Update the display
        self._update_label_display()

    def _create_label_segment(self, label_id: str, end_position: float) -> None:
        """Create a new label segment."""
        track_labels = self.label_manager.get_current_track_labels()
        if not track_labels:
            return

        # Get the current labeling mode
        labeling_mode = self.label_manager.get_labeling_mode()

        if labeling_mode == "segmentation":
            # Calculate start position (either 0 or end of last segment)
            start_position = track_labels.get_last_segment_end()
        else:  # annotation mode
            # In annotation mode, use current position as start
            current_position = self.right_panel.waveform_widget.current_position
            start_position = current_position
            # Default to 5 seconds duration, or until end of track
            duration = 5.0
            audio_duration = getattr(self.right_panel.waveform_widget, "duration", 0)
            if audio_duration > 0:
                end_position = min(start_position + duration, audio_duration)
            else:
                end_position = start_position + duration

        # Ensure we have a valid segment
        if end_position <= start_position:
            print(f"Invalid segment: end ({end_position}) <= start ({start_position})")
            return

        # Add the segment with the current labeling mode
        success = track_labels.add_segment(
            label_id, start_position, end_position, labeling_mode
        )
        if not success:
            print(
                f"Failed to add segment: {label_id} from {start_position} to {end_position}"
            )

    def _move_label_boundary(
        self, segment_index: int, boundary_type: str, new_time: float
    ) -> None:
        """Move a label boundary, behavior depends on labeling mode."""
        track_labels = self.label_manager.get_current_track_labels()
        if not track_labels:
            return

        segments = track_labels.get_segments()
        if not (0 <= segment_index < len(segments)):
            return

        # Get the current labeling mode
        labeling_mode = self.label_manager.get_labeling_mode()

        if boundary_type == "start":
            self._move_start_boundary(
                track_labels, segments, segment_index, new_time, labeling_mode
            )
        elif boundary_type == "end":
            self._move_end_boundary(
                track_labels, segments, segment_index, new_time, labeling_mode
            )

        # Update the label bar display
        self._update_label_display()

    def _move_start_boundary(
        self,
        track_labels,
        segments,
        segment_index: int,
        new_time: float,
        labeling_mode: str,
    ) -> None:
        """Move the start boundary of a segment."""
        segment = segments[segment_index]

        if labeling_mode == "segmentation":
            # Segmentation mode: maintain connections, no overlaps
            min_time = (
                segments[segment_index - 1].start_seconds if segment_index > 0 else 0.0
            )
            max_time = (
                segment.end_seconds - 1.0
            )  # Leave at least 1 second for the segment
            new_time = max(min_time, min(max_time, new_time))

            # Update current segment's start (use unchecked method for connected segments)
            track_labels.update_segment_unchecked(
                segment_index, new_time, segment.end_seconds
            )

            # Update previous segment's end to maintain connection
            if segment_index > 0:
                prev_segment = segments[segment_index - 1]
                track_labels.update_segment_unchecked(
                    segment_index - 1, prev_segment.start_seconds, new_time
                )
        else:
            # Annotation mode: free movement, overlaps allowed
            max_time = (
                segment.end_seconds - 0.1
            )  # Leave at least 0.1 second for the segment
            new_time = max(0.0, min(max_time, new_time))

            # Simply update the segment's start time
            track_labels.update_segment_unchecked(
                segment_index, new_time, segment.end_seconds
            )

        # Save changes
        track_labels._save_labels()

    def _move_end_boundary(
        self,
        track_labels,
        segments,
        segment_index: int,
        new_time: float,
        labeling_mode: str,
    ) -> None:
        """Move the end boundary of a segment."""
        segment = segments[segment_index]

        if labeling_mode == "segmentation":
            # Segmentation mode: maintain connections, no overlaps
            min_time = (
                segment.start_seconds + 1.0
            )  # Leave at least 1 second for the segment
            max_time = (
                segments[segment_index + 1].end_seconds
                if segment_index < len(segments) - 1
                else float("inf")
            )
            new_time = max(min_time, min(max_time, new_time))

            # Update current segment's end (use unchecked method for connected segments)
            track_labels.update_segment_unchecked(
                segment_index, segment.start_seconds, new_time
            )

            # Update next segment's start to maintain connection
            if segment_index < len(segments) - 1:
                next_segment = segments[segment_index + 1]
                track_labels.update_segment_unchecked(
                    segment_index + 1, new_time, next_segment.end_seconds
                )
        else:
            # Annotation mode: free movement, overlaps allowed
            # Get audio duration to clamp the end time
            audio_duration = getattr(
                self.right_panel.waveform_widget, "duration", float("inf")
            )
            min_time = (
                segment.start_seconds + 0.1
            )  # Leave at least 0.1 second for the segment
            max_time = audio_duration
            new_time = max(min_time, min(max_time, new_time))

            # Simply update the segment's end time
            track_labels.update_segment_unchecked(
                segment_index, segment.start_seconds, new_time
            )

        # Save changes
        track_labels._save_labels()

    def _select_label_segment(self, segment_index: int) -> None:
        """Handle label segment selection."""
        track_labels = self.label_manager.get_current_track_labels()
        if not track_labels:
            return

        segments = track_labels.get_segments()
        if 0 <= segment_index < len(segments):
            segment = segments[segment_index]
            # Update the right panel to show selection
            self.right_panel.set_selected_label_segment(segment_index)
            # Seek to the start of the selected segment
            self._seek_to_position(segment.start_seconds)
            print(
                f"Selected segment: {segment.label_id} ({segment.start_seconds:.2f}s - {segment.end_seconds:.2f}s)"
            )

    def _delete_label_segment(self, segment_index: int) -> None:
        """Delete a label segment."""
        track_labels = self.label_manager.get_current_track_labels()
        if not track_labels:
            return

        segments = track_labels.get_segments()
        if 0 <= segment_index < len(segments):
            segment = segments[segment_index]
            success = track_labels.remove_segment(segment_index)
            if success:
                print(
                    f"Deleted segment: {segment.label_id} ({segment.start_seconds:.2f}s - {segment.end_seconds:.2f}s)"
                )
                # Update the label bar display
                self._update_label_display()
                # Clear selection
                self.right_panel.clear_label_selection()
            else:
                print(f"Failed to delete segment {segment_index}")

    def _move_label_segment(
        self, segment_index: int, new_start_time: float, new_end_time: float
    ) -> None:
        """Move an entire label segment to a new position (annotation mode only)."""
        track_labels = self.label_manager.get_current_track_labels()
        if not track_labels:
            return

        segments = track_labels.get_segments()
        if not (0 <= segment_index < len(segments)):
            return

        # Only allow segment moving in annotation mode
        labeling_mode = self.label_manager.get_labeling_mode()
        if labeling_mode != "annotation":
            return

        # Get the segment to move
        segment = segments[segment_index]

        # Update segment times
        segment.start_seconds = new_start_time
        segment.end_seconds = new_end_time

        # Save the changes
        track_labels._save_labels()

        # Update the display
        self._update_label_display()

        print(
            f"Moved segment {segment_index}: {segment.label_id} to {new_start_time:.2f}s - {new_end_time:.2f}s"
        )

    def _update_label_display(self) -> None:
        """Update the label display in the right panel."""
        track_labels = self.label_manager.get_current_track_labels()
        if not track_labels:
            return

        segments = track_labels.get_segments()

        # Get audio duration from the media player (convert from ms to seconds)
        duration_ms = self.media_player.duration()
        duration = duration_ms / 1000.0 if duration_ms > 0 else 0.0

        # Update the right panel
        self.right_panel.set_label_segments(segments)
        self.right_panel.set_audio_duration(duration)

    def _show_new_project_dialog(self) -> None:
        """Show dialog to create a new project."""
        project_dir = QFileDialog.getExistingDirectory(
            self, "Select Folder for New Project", "", QFileDialog.Option.ShowDirsOnly
        )

        if project_dir:
            self._create_new_project(Path(project_dir))

    def _show_open_project_dialog(self) -> None:
        """Show dialog to open an existing project by selecting label_config.json."""
        config_file, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project - Select label_config.json",
            "",
            "JSON Files (*.json);;All Files (*)",
        )

        if config_file:
            config_path = Path(config_file)
            if config_path.name == "label_config.json":
                project_dir = config_path.parent
                self._set_project_directory(project_dir)
            else:
                QMessageBox.warning(
                    self,
                    "Invalid Project File",
                    "Please select a label_config.json file.",
                )

    def _create_new_project(self, project_dir: Path) -> None:
        """Create a new project with all necessary folders and files."""
        try:
            # Create project structure
            music_dir = project_dir / "music"
            labels_dir = project_dir / "labels"
            config_file = project_dir / "label_config.json"

            # Create directories
            music_dir.mkdir(parents=True, exist_ok=True)
            labels_dir.mkdir(parents=True, exist_ok=True)

            # Create default label configuration
            AppConfig._create_default_label_config(config_file)

            # Set as current project
            self._set_project_directory(project_dir)

            # Show label editor for new project
            self._show_label_editor()

            QMessageBox.information(
                self,
                "Project Created",
                f"New project created in:\n{project_dir}\n\n"
                "You can now add music files to the project.",
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Error Creating Project", f"Failed to create project:\n{str(e)}"
            )

    def _show_label_editor(self) -> None:
        """Show the label editor dialog."""
        if AppConfig._current_project_dir:
            from .ui.label_editor import LabelEditor

            editor = LabelEditor(self.label_manager, self)
            editor.labels_changed.connect(self._on_labels_changed)
            if editor.exec() == QDialog.DialogCode.Accepted:
                # Reload label definitions in the label manager
                self.label_manager.label_config._load_config()

                # Update the right panel with new label definitions
                label_definitions = self.label_manager.get_label_definitions()
                self.right_panel.set_label_definitions(label_definitions)

                # Update the mode indicator
                self._update_mode_indicator()
        else:
            QMessageBox.warning(
                self, "No Project", "Please create or open a project first."
            )

    def _set_project_directory(self, project_dir: Path) -> None:
        """Set the project directory and update all components."""
        # Update configuration
        AppConfig.set_project_directory(project_dir)

        # Update window title to show current project
        self.setWindowTitle(f"{AppConfig.APP_NAME} - {project_dir.name}")

        # Update music library
        self.music_library.set_project_directory(project_dir)

        # Update label manager
        self.label_manager.set_project_directory(project_dir)

        # Set label definitions in the right panel
        label_definitions = self.label_manager.get_label_definitions()
        self.right_panel.set_label_definitions(label_definitions)

        # Update mode indicator
        self._update_mode_indicator()

        # Refresh the music library
        self._refresh_music_library()

        # Clear current audio
        self._stop_playback()
        self.right_panel.reset()

    def _remove_file(self, file_path: str) -> None:
        """Remove a file from the library and its associated labels."""
        from PySide6.QtWidgets import QMessageBox

        # Confirm deletion
        file_name = Path(file_path).name
        reply = QMessageBox.question(
            self,
            "Remove File",
            f"Are you sure you want to remove '{file_name}' and all its labels?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Stop media player completely and clear any file references
            self.media_player.stop()
            self.media_player.setSource(QUrl())  # Clear the source

            # Stop playback and clear current state if this is the current file
            if self._current_file_path == file_path:
                self._stop_playback()
                self.right_panel.reset()
                self._current_file_path = None
                if self._current_audio_worker:
                    self._current_audio_worker = None

            # Small delay to ensure file handles are released
            from PySide6.QtCore import QTimer

            QTimer.singleShot(
                100, lambda: self._perform_file_removal(file_path, file_name)
            )

    def _perform_file_removal(self, file_path: str, file_name: str) -> None:
        """Perform the actual file removal after ensuring handles are released."""
        from PySide6.QtWidgets import QMessageBox

        # Remove labels first
        labels_removed = self.label_manager.remove_track_labels(file_path)
        print(f"Labels removed: {labels_removed}")

        # Remove the music file
        file_removed = self.music_library.remove_file(file_path)
        print(f"File removed: {file_removed}")

        if file_removed:
            QMessageBox.information(
                self, "File Removed", f"'{file_name}' and its labels have been removed."
            )
        else:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to remove '{file_name}'. The file may be in use or protected.",
            )

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter events for the main window."""
        if event.mimeData().hasUrls():
            # Check if any of the dragged files are supported audio files
            from .audio.processor import AudioProcessor

            processor = AudioProcessor()

            supported_files = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if processor.is_supported_format(file_path):
                    supported_files.append(file_path)

            if supported_files:
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop events for the main window."""
        from .audio.processor import AudioProcessor

        processor = AudioProcessor()

        supported_files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if processor.is_supported_format(file_path):
                supported_files.append(file_path)

        if supported_files:
            self._handle_dropped_files(supported_files)
            event.acceptProposedAction()
        else:
            event.ignore()

    def keyPressEvent(self, event) -> None:
        """Handle global keyboard events."""
        if event.key() == Qt.Key.Key_Space:
            # Space key always toggles play/pause
            self._toggle_playback()
            event.accept()
        else:
            # Let other widgets handle their own key events
            super().keyPressEvent(event)


def create_app() -> QApplication:
    """
    Create and configure the QApplication.

    Returns:
        Configured QApplication instance
    """
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use modern style

    # Set application metadata
    app.setApplicationName(AppConfig.APP_NAME)
    app.setApplicationVersion(AppConfig.APP_VERSION)
    app.setOrganizationName(AppConfig.ORGANIZATION_NAME)

    # Set global application icon
    icon_path = get_icon_path()
    if icon_path:
        app.setWindowIcon(QIcon(str(icon_path)))

    return app


def main() -> None:
    """Main application entry point."""
    app = create_app()

    # Create and show main window
    window = MuSegApp()
    window.show()

    # Start the application
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nApplication closed by user")
        sys.exit(0)
