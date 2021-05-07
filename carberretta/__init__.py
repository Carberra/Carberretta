from toml import loads
from pathlib import Path

from carberretta.config import Config


__version__ = loads(open(Path(__name__).resolve().parents[0] / "pyproject.toml").read())["tool"]["poetry"]["version"]
