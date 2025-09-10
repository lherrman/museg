"""Configuration constants for the Music Segment Labeler application."""

from pathlib import Path
from typing import Optional


class AppConfig:
    """Application configuration constants."""

    # Application metadata
    APP_NAME = "MuSeg Audio Annotation Tool"
    APP_VERSION = "0.1.0"
    ORGANIZATION_NAME = "TechnoSeg"

    # Window settings
    DEFAULT_WINDOW_SIZE = (1400, 800)
    MIN_WINDOW_SIZE = (800, 600)

    # Audio settings
    SUPPORTED_AUDIO_FORMATS = [".mp3", ".wav"]
    MAX_WAVEFORM_POINTS = 10000
    POSITION_UPDATE_INTERVAL_MS = 100

    # UI settings
    LEFT_PANEL_WIDTH = 300
    WAVEFORM_HEIGHT = 300
    CONTROLS_HEIGHT = 120

    # Current project directory
    _current_project_dir: Optional[Path] = None

    @classmethod
    def set_project_directory(cls, project_dir: Path) -> None:
        """Set the current project directory."""
        cls._current_project_dir = project_dir

        # Create necessary subdirectories
        music_dir = cls.get_music_directory()
        labels_dir = cls.get_labels_directory()

        music_dir.mkdir(parents=True, exist_ok=True)
        labels_dir.mkdir(parents=True, exist_ok=True)

        # Create default label config if it doesn't exist
        config_file = cls.get_label_config_file()
        if not config_file.exists():
            cls._create_default_label_config(config_file)

    @staticmethod
    def _create_default_label_config(config_file: Path) -> None:
        """Create a default label configuration file."""
        import json

        default_config = {
            "labeling_mode": "segmentation",  # "segmentation" or "annotation"
            "label_definitions": [
                {
                    "id": "intro",
                    "name": "Intro",
                    "color": "#FF6B6B",
                    "hotkey": "1",
                    "description": "Track introduction",
                },
                {
                    "id": "main",
                    "name": "Main",
                    "color": "#4ECDC4",
                    "hotkey": "2",
                    "description": "Main section/theme",
                },
                {
                    "id": "buildup",
                    "name": "Buildup",
                    "color": "#45B7D1",
                    "hotkey": "3",
                    "description": "Energy building section",
                },
                {
                    "id": "mini_break",
                    "name": "Mini Break",
                    "color": "#96CEB4",
                    "hotkey": "4",
                    "description": "Breakdown/calm section",
                },
                {
                    "id": "drop",
                    "name": "Drop",
                    "color": "#459448",
                    "hotkey": "5",
                    "description": "Energy release/climax",
                },
                {
                    "id": "breakdown",
                    "name": "Breakdown",
                    "color": "#6867A0",
                    "hotkey": "6",
                    "description": "Breakdown/calm section",
                },
                {
                    "id": "outro",
                    "name": "Outro",
                    "color": "#DDA0DD",
                    "hotkey": "7",
                    "description": "Track ending",
                },
            ],
        }

        with open(config_file, "w") as f:
            json.dump(default_config, f, indent=2)

    # File paths
    @classmethod
    def get_music_directory(cls) -> Path:
        """Get the music directory path."""
        if cls._current_project_dir:
            return cls._current_project_dir / "music"
        return Path(__file__).parent.parent.parent.parent / "music"

    @classmethod
    def get_labels_directory(cls) -> Path:
        """Get the labels directory path."""
        if cls._current_project_dir:
            return cls._current_project_dir / "labels"
        return Path(__file__).parent.parent.parent.parent / "labels"

    @classmethod
    def get_label_config_file(cls) -> Path:
        """Get the label configuration file path."""
        if cls._current_project_dir:
            return cls._current_project_dir / "label_config.json"
        return Path(__file__).parent.parent.parent.parent / "label_config.json"


class UIColors:
    """UI color scheme constants."""

    # Main colors
    BACKGROUND = "#2b2b2b"
    PANEL_BACKGROUND = "#3c3c3c"
    PRIMARY = "#4CAF50"
    PRIMARY_HOVER = "#45a049"
    PRIMARY_PRESSED = "#3d8b40"
    ACCENT = "#FF5722"

    # Text colors
    TEXT_PRIMARY = "white"
    TEXT_SECONDARY = "#aaa"
    TEXT_ERROR = "red"

    # Waveform colors
    WAVEFORM_COLOR = "#4CAF50"
    POSITION_LINE_COLOR = "#FF5722"
    GRID_COLOR = "gray"


class UIStyles:
    """UI style constants."""

    MAIN_STYLESHEET = f"""
        QMainWindow {{
            background-color: {UIColors.BACKGROUND};
            color: {UIColors.TEXT_PRIMARY};
        }}
        QFrame {{
            background-color: {UIColors.PANEL_BACKGROUND};
            border-radius: 8px;
            padding: 5px;
        }}
        QPushButton {{
            background-color: {UIColors.PRIMARY};
            color: {UIColors.TEXT_PRIMARY};
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
            font-size: 12px;
        }}
        QPushButton:hover {{
            background-color: {UIColors.PRIMARY_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {UIColors.PRIMARY_PRESSED};
        }}
        QSlider::groove:horizontal {{
            border: 1px solid #999999;
            height: 6px;
            background: #555;
            margin: 2px 0;
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {UIColors.PRIMARY};
            border: 1px solid {UIColors.PRIMARY};
            width: 16px;
            margin: -5px 0;
            border-radius: 8px;
        }}
        QSlider::sub-page:horizontal {{
            background: {UIColors.PRIMARY};
            border-radius: 3px;
        }}
        QToolBar {{
            background-color: {UIColors.PANEL_BACKGROUND};
            border: none;
            spacing: 3px;
            padding: 5px;
        }}
        QToolBar QAction {{
            padding: 8px;
            margin: 2px;
        }}
    """

    LIST_WIDGET_STYLESHEET = f"""
        QListWidget {{
            background-color: {UIColors.PANEL_BACKGROUND};
            border: 1px solid #555;
            border-radius: 8px;
            padding: 5px;
            color: {UIColors.TEXT_PRIMARY};
            font-size: 12px;
        }}
        QListWidget::item {{
            padding: 8px;
            border-radius: 4px;
            margin: 2px;
        }}
        QListWidget::item:selected {{
            background-color: {UIColors.PRIMARY};
        }}
        QListWidget::item:hover {{
            background-color: #555;
        }}
    """

    PLAY_BUTTON_STYLESHEET = """
        QPushButton {
            font-size: 18px;
            font-weight: bold;
        }
    """
