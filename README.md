# MuSeg Audio Annotation Tool

MuSeg is a powerful and intuitive audio annotation tool designed for segmentation and labeling of audio files for machine learning datasets. Built specifically for researchers, data scientists, and ML engineers who need to create labeled training data from audio content.

## Features

### Core Functionality
- **Audio Segmentation**: Create time-based segments for data labeling
- **Visual Waveform Display**: Interactive waveform visualization for easy navigation
- **Multiple Label Support**: Assign custom labels and categories to audio segments
- **Dataset Management**: Organize your work with project-based file management
- **Real-time Playback**: Play segments with audio controls for review

### Technical Capabilities
- **Audio Format Support**: MP3 and WAV file formats
- **Waveform Visualization**: Clear display for audio analysis and labeling
- **JSON Export**: Export annotations in structured JSON format for ML training pipelines
- **Keyboard Shortcuts**: Efficient workflow with keyboard navigation
- **Cross-platform**: Built with Python and Qt for multi-platform compatibility

## Installation & Usage

### Option 1: Pre-built Executable (Windows)

1. **Download**: Get the latest `museg_win_64.exe` from the releases
2. **Run**: Double-click the executable to launch MuSeg
3. **No Installation Required**: The executable is self-contained

### Option 2: Python Environment

#### Prerequisites
- Python 3.13 or later
- uv package manager (recommended) or pip

#### Setup
```bash
# Clone or download the project
cd path/to/museg

# Create virtual environment and install dependencies
uv sync

# Run the application
uv run run_labeler.py
```

