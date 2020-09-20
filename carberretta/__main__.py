from carberretta import __version__
from carberretta.bot import Bot


def main():
    bot = Bot(__version__)
    bot.run()


if __name__ == "__main__":
    main()
