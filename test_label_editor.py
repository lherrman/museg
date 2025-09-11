#!/usr/bin/env python3
"""Test script for the label editor."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication
from src.ui.label_editor import LabelEditor
from src.core.label_manager import LabelManager

def main():
    app = QApplication(sys.argv)
    
    # Create a label manager for testing
    labels_dir = Path("projects/test/labels")
    config_file = Path("projects/test/musegproject.json") 
    
    # Create directories if they don't exist
    labels_dir.mkdir(parents=True, exist_ok=True)
    
    label_manager = LabelManager(labels_dir, config_file)
    
    # Open the label editor
    editor = LabelEditor(label_manager)
    editor.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
