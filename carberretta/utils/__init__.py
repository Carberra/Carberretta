from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
DEFAULT_EMBED_COLOUR = 0x00CD99

# Dependant on above constants.
from .loc import CodeCounter
from .ready import Ready
