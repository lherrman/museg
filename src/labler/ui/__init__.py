"""UI module __init__."""

from .left_panel import LeftPanel
from .right_panel import RightPanel
from .waveform_widget import WaveformWidget
from .music_list_widget import MusicListWidget
from .audio_controls import ModernPlayControls
from .label_bar import LabelBar
from .label_buttons import LabelButton, LabelButtonsWidget

__all__ = [
    "LeftPanel",
    "RightPanel",
    "WaveformWidget",
    "MusicListWidget",
    "ModernPlayControls",
    "LabelBar",
    "LabelButton",
    "LabelButtonsWidget",
]
