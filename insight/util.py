"""Enable import of util.whatever."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utilities import *  # noqa: F403

class Priority:
    HIGH = 0
    MEDIUM = 1
    LOW = 2
