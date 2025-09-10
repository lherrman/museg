#!/usr/bin/env python3
"""
Standalone entry point for the Music Segment Labeler application.
Run this file directly to start the application.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

if __name__ == "__main__":
    # Import and run the main application
    from labler.app import main

    main()
