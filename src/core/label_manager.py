"""Label management and configuration system."""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal


@dataclass
class LabelDefinition:
    """Definition of a label type."""

    id: str
    name: str
    color: str
    description: str


@dataclass
class LabelSegment:
    """A labeled segment in a track."""

    label_id: str
    start_seconds: float
    end_seconds: float

    def duration(self) -> float:
        """Get the duration of this segment."""
        return self.end_seconds - self.start_seconds


class LabelConfig:
    """Manages label configuration from JSON file."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._label_definitions: Dict[str, LabelDefinition] = {}
        self._labeling_mode: str = "segmentation"  # Default mode
        self._load_config()

    def _load_config(self) -> None:
        """Load label configuration from JSON file."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            # Load labeling mode
            self._labeling_mode = config_data.get("labeling_mode", "segmentation")

            self._label_definitions.clear()
            for label_data in config_data.get("label_definitions", []):
                label_def = LabelDefinition(
                    id=label_data["id"],
                    name=label_data["name"],
                    color=label_data["color"],
                    description=label_data.get("description", ""),
                )
                self._label_definitions[label_def.id] = label_def

        except Exception as e:
            print(f"Error loading label config: {e}")
            # Fallback to default labels
            self._create_default_labels()

    def _create_default_labels(self) -> None:
        """Create default label definitions."""
        default_labels = [
            LabelDefinition("intro", "Intro", "#FF6B6B", "Track introduction"),
            LabelDefinition("main", "Main", "#4ECDC4", "Main section/theme"),
            LabelDefinition("buildup", "Buildup", "#45B7D1", "Energy building section"),
            LabelDefinition(
                "mini_break", "Mini Break", "#96CEB4", "Breakdown/calm section"
            ),
            LabelDefinition("drop", "Drop", "#459448", "Energy release/climax"),
            LabelDefinition(
                "breakdown", "Breakdown", "#6867A0", "Breakdown/calm section"
            ),
            LabelDefinition("outro", "Outro", "#DDA0DD", "Track ending"),
        ]

        self._label_definitions = {label.id: label for label in default_labels}

    def get_label_definitions(self) -> List[LabelDefinition]:
        """Get all available label definitions."""
        return list(self._label_definitions.values())

    def get_label_definition(self, label_id: str) -> Optional[LabelDefinition]:
        """Get a specific label definition by ID."""
        return self._label_definitions.get(label_id)

    def get_labeling_mode(self) -> str:
        """Get the current labeling mode."""
        return self._labeling_mode

    def set_labeling_mode(self, mode: str) -> None:
        """Set the labeling mode and save to config file."""
        if mode not in ["segmentation", "annotation"]:
            raise ValueError("Mode must be 'segmentation' or 'annotation'")

        self._labeling_mode = mode
        self._save_config()

    def _save_config(self) -> None:
        """Save the current configuration to file."""
        config_data = {
            "labeling_mode": self._labeling_mode,
            "label_definitions": [
                {
                    "id": label_def.id,
                    "name": label_def.name,
                    "color": label_def.color,
                    "hotkey": str(i + 1),  # Auto-assign hotkeys
                    "description": label_def.description,
                }
                for i, label_def in enumerate(self._label_definitions.values())
            ],
        }

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)


class TrackLabels(QObject):
    """Manages labels for a single track."""

    # Signals
    labels_changed = Signal()  # Emitted when labels are modified

    def __init__(self, track_file_path: str, labels_directory: Path):
        super().__init__()
        self.track_file_path = track_file_path
        self.labels_directory = labels_directory
        self.labels_directory.mkdir(exist_ok=True)

        # Extract track ID from filename (the 5-digit prefix)
        track_filename = Path(track_file_path).name
        if track_filename.startswith(
            ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
        ):
            # Extract the 5-digit prefix
            self.track_id = track_filename[:5]
        else:
            # Fallback: use the full filename without extension
            self.track_id = Path(track_file_path).stem

        self.labels_file = self.labels_directory / f"{self.track_id}.json"
        self._segments: List[LabelSegment] = []
        self._load_labels()

    def _load_labels(self) -> None:
        """Load labels from JSON file."""
        if not self.labels_file.exists():
            self._create_empty_labels_file()
            return

        try:
            with open(self.labels_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._segments.clear()
            for segment_data in data.get("labels", []):
                segment = LabelSegment(
                    label_id=segment_data["label_id"],
                    start_seconds=segment_data["start_seconds"],
                    end_seconds=segment_data["end_seconds"],
                )
                self._segments.append(segment)

            # Sort segments by start time
            self._segments.sort(key=lambda s: s.start_seconds)

        except Exception as e:
            print(f"Error loading labels: {e}")
            self._segments.clear()

    def _create_empty_labels_file(self) -> None:
        """Create an empty labels file."""
        data = {
            "track_file": Path(self.track_file_path).name,
            "track_id": self.track_id,
            "labels": [],
        }

        with open(self.labels_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _save_labels(self) -> None:
        """Save labels to JSON file."""
        data = {
            "track_file": Path(self.track_file_path).name,
            "track_id": self.track_id,
            "labels": [
                {
                    "label_id": segment.label_id,
                    "start_seconds": segment.start_seconds,
                    "end_seconds": segment.end_seconds,
                }
                for segment in self._segments
            ],
        }

        with open(self.labels_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        self.labels_changed.emit()

    def add_segment(
        self,
        label_id: str,
        start_seconds: float,
        end_seconds: float,
        labeling_mode: str = "segmentation",
    ) -> bool:
        """
        Add a new label segment.

        Args:
            label_id: ID of the label type
            start_seconds: Start time in seconds
            end_seconds: End time in seconds
            labeling_mode: "segmentation" or "annotation"

        Returns:
            True if segment was added successfully
        """
        if start_seconds >= end_seconds:
            return False

        if labeling_mode == "segmentation":
            return self._add_segment_segmentation(label_id, start_seconds, end_seconds)
        else:  # annotation mode
            return self._add_segment_annotation(label_id, start_seconds, end_seconds)

    def _add_segment_segmentation(
        self, label_id: str, start_seconds: float, end_seconds: float
    ) -> bool:
        """Add segment in segmentation mode (connected segments)."""
        # For connected segments, only check for overlaps if not connecting
        # Allow segments to connect at boundaries
        for existing in self._segments:
            if (
                start_seconds < existing.end_seconds
                and end_seconds > existing.start_seconds
                and start_seconds != existing.end_seconds
                and end_seconds != existing.start_seconds
            ):
                return False  # True overlap detected (not just touching)

        segment = LabelSegment(label_id, start_seconds, end_seconds)
        self._segments.append(segment)
        self._segments.sort(key=lambda s: s.start_seconds)
        self._save_labels()
        return True

    def _add_segment_annotation(
        self, label_id: str, start_seconds: float, end_seconds: float
    ) -> bool:
        """Add segment in annotation mode (free placement, overlaps allowed)."""
        # In annotation mode, segments can overlap freely
        segment = LabelSegment(label_id, start_seconds, end_seconds)
        self._segments.append(segment)
        self._segments.sort(key=lambda s: s.start_seconds)
        self._save_labels()
        return True

    def update_segment_unchecked(
        self, index: int, start_seconds: float, end_seconds: float
    ) -> bool:
        """Update a segment's timing without overlap checking (for connected segments)."""
        if not (0 <= index < len(self._segments)):
            return False

        if start_seconds >= end_seconds:
            return False

        self._segments[index].start_seconds = start_seconds
        self._segments[index].end_seconds = end_seconds
        self._segments.sort(key=lambda s: s.start_seconds)
        self._save_labels()
        return True

    def remove_segment(self, index: int) -> bool:
        """Remove a segment by index."""
        if 0 <= index < len(self._segments):
            del self._segments[index]
            self._save_labels()
            return True
        return False

    def update_segment(
        self, index: int, start_seconds: float, end_seconds: float
    ) -> bool:
        """Update a segment's timing."""
        if not (0 <= index < len(self._segments)):
            return False

        if start_seconds >= end_seconds:
            return False

        # Check for overlaps with other segments
        for i, existing in enumerate(self._segments):
            if i != index and (
                start_seconds < existing.end_seconds
                and end_seconds > existing.start_seconds
            ):
                return False  # Overlap detected

        self._segments[index].start_seconds = start_seconds
        self._segments[index].end_seconds = end_seconds
        self._segments.sort(key=lambda s: s.start_seconds)
        self._save_labels()
        return True

    def get_segments(self) -> List[LabelSegment]:
        """Get all label segments."""
        return self._segments.copy()

    def get_last_segment_end(self) -> float:
        """Get the end time of the last segment, or 0.0 if no segments exist."""
        if not self._segments:
            return 0.0
        return max(segment.end_seconds for segment in self._segments)

    def clear_all_segments(self) -> None:
        """Clear all label segments."""
        self._segments.clear()
        self._save_labels()


class LabelManager(QObject):
    """Central manager for label configuration and track labels."""

    def __init__(self, labels_directory: Path, config_file: Path):
        super().__init__()
        self.labels_directory = labels_directory
        self.labels_directory.mkdir(exist_ok=True)

        # Load label configuration
        self.label_config = LabelConfig(config_file)

        # Current track labels
        self._current_track_labels: Optional[TrackLabels] = None

    def load_track_labels(self, track_file_path: str) -> TrackLabels:
        """Load labels for a specific track."""
        self._current_track_labels = TrackLabels(track_file_path, self.labels_directory)
        return self._current_track_labels

    def get_current_track_labels(self) -> Optional[TrackLabels]:
        """Get the currently loaded track labels."""
        return self._current_track_labels

    def get_label_definitions(self) -> List[LabelDefinition]:
        """Get all available label definitions."""
        return self.label_config.get_label_definitions()

    def get_label_definition(self, label_id: str) -> Optional[LabelDefinition]:
        """Get a specific label definition."""
        return self.label_config.get_label_definition(label_id)

    def get_labeling_mode(self) -> str:
        """Get the current labeling mode."""
        return self.label_config.get_labeling_mode()

    def set_labeling_mode(self, mode: str) -> None:
        """Set the labeling mode."""
        self.label_config.set_labeling_mode(mode)

    def set_project_directory(self, project_dir: Path) -> None:
        """Set a new project directory for the label manager."""
        self.labels_directory = project_dir / "labels"
        self.labels_directory.mkdir(parents=True, exist_ok=True)

        # Update label configuration path
        config_file = project_dir / "musegproject.json"
        self.label_config = LabelConfig(config_file)

        # Clear current track labels as they're from the old project
        self._current_track_labels = None

    def remove_track_labels(self, track_file_path: str) -> bool:
        """Remove all labels for a specific track."""
        try:
            track_labels = TrackLabels(track_file_path, self.labels_directory)

            if track_labels.labels_file.exists():
                track_labels.labels_file.unlink()

                # Clear current track labels if this is the current track
                if (
                    self._current_track_labels
                    and self._current_track_labels.track_file_path == track_file_path
                ):
                    self._current_track_labels = None

                return True
        except Exception:
            pass
        return False

    def get_labels(self) -> List[Dict[str, Any]]:
        """Get all label definitions as a list of dictionaries."""
        definitions = self.label_config.get_label_definitions()
        return [
            {
                "name": label_def.name,
                "color": label_def.color,
                "key": None,  # Will be assigned when used
            }
            for label_def in definitions
        ]

    def set_labels(self, labels: List[Dict[str, Any]]) -> None:
        """Set label definitions from a list of dictionaries."""
        # Convert to LabelDefinition objects
        definitions = []
        for i, label_data in enumerate(labels):
            label_def = LabelDefinition(
                id=f"label_{i}",
                name=label_data["name"],
                color=label_data["color"],
                description=label_data.get("description", ""),
            )
            definitions.append(label_def)

        # Update the label config
        self.label_config._label_definitions = {
            label_def.id: label_def for label_def in definitions
        }

    def is_label_in_use(self, label_name: str) -> bool:
        """Check if a label is currently being used in any segments."""
        if not self._current_track_labels:
            return False

        # Find the label definition by name
        label_def = None
        for definition in self.label_config.get_label_definitions():
            if definition.name == label_name:
                label_def = definition
                break

        if not label_def:
            return False

        # Check if any segments use this label
        segments = self._current_track_labels.get_segments()
        return any(segment.label_id == label_def.id for segment in segments)

    def save_config(self) -> None:
        """Save the current configuration to file."""
        self.label_config._save_config()
