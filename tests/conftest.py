"""
Pytest configuration and fixtures
"""

import sys
import os

# Add project root to Python path so src can be imported as absolute
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)
