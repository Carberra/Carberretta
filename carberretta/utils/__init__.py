from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
DEFAULT_EMBED_COLOUR = 0xE33939

# Dependant on above constants.
from .emoji import EmojiGetter
from .loc import CodeCounter
from .ready import Ready
from .search import Search
