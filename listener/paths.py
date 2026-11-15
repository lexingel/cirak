"""Where the listener keeps its files: per user, never next to the code (that may be read-only)."""
import os
from pathlib import Path

DATA = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "Cirak"
