"""
Pytest configuration for co_scientist_service tests.

Handles import path setup and common fixtures.
"""

import sys
import os
import pytest

# Get the src directory path
SRC_DIR = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, SRC_DIR)

# Also add the parent directory to handle 'src' prefix imports
SERVICE_DIR = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, SERVICE_DIR)
