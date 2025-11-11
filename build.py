#!/usr/bin/env python3
"""Build script for creating PyInstaller executables."""

import subprocess
import sys
from pathlib import Path

def main():
    """Build the application using PyInstaller."""
    
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    print("Building executable...")
    subprocess.check_call([
        sys.executable, "-m", "PyInstaller", 
        "tasks.spec", 
        "--clean"
    ])
    
    print("Build complete! Executable is in dist/")

if __name__ == "__main__":
    main()
