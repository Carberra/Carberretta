from typing import Final
from os import getenv

from dotenv import load_dotenv


# Load the .env development environment if exists
load_dotenv()


class Config:
    # Production token is provided by a file, whereas the development token is
    # given in .env.
    try:
        with open(getenv("TOKEN", "")) as f:
            token = f.read()
    except FileNotFoundError:
        token = getenv("TOKEN", "")

    TOKEN: Final = token
    OWNER_IDS: Final[set] = set([385807530913169426, 102733198231863296])
    PREFIX: Final = getenv("PREFIX", "+")

    GUILD_ID: Final = int(getenv("GUILD_ID", ""))
    STDOUT_ID: Final = int(getenv("STDOUT_ID", ""))
    COMMANDS_ID: Final = int(getenv("COMMANDS_ID", ""))
    RELAY_ID: Final = int(getenv("RELAY_ID", ""))
    MODMAIL_ID: Final = int(getenv("MODMAIL_ID", ""))

    HUB_GUILD_ID: Final = int(getenv("HUB_GUILD_ID", GUILD_ID))
    HUB_STDOUT_ID: Final = int(getenv("HUB_STDOUT_ID", STDOUT_ID))
    HUB_COMMANDS_ID: Final = int(getenv("HUB_COMMANDS_ID", COMMANDS_ID))
    HUB_RELAY_ID: Final = int(getenv("HUB_COMMANDS_ID", RELAY_ID))
