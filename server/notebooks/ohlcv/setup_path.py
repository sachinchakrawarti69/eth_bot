"""
Setup script for OHLCV notebooks
Run this at the start of each notebook to set up the path
"""

import sys
from pathlib import Path

def setup_utils_path():
    """Add utils folder to Python path"""
    # Get the current file's directory
    current_dir = Path(__file__).parent.resolve()
    
    # Add utils folder
    utils_path = current_dir / 'utils'
    if utils_path.exists() and str(utils_path) not in sys.path:
        sys.path.insert(0, str(utils_path))
        print(f"✅ Utils path added: {utils_path}")
        return True
    return False

if __name__ == "__main__":
    setup_utils_path()