"""Core __init__ module."""

from .config import AppConfig, UIColors, UIStyles
from .music_library import MusicLibrary
from .label_manager import LabelManager, LabelDefinition, LabelSegment, TrackLabels

__all__ = [
    "AppConfig",
    "UIColors",
    "UIStyles",
    "MusicLibrary",
    "LabelManager",
    "LabelDefinition",
    "LabelSegment",
    "TrackLabels",
]
