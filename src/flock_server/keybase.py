import asyncio
import logging
import os

from pykeybasebot import Bot

logging.basicConfig(level=logging.DEBUG)


class Handler:
    async def __call__(self, bot, event):
        print(event)


def start_keybase_bot():

    bot = Bot(
        username=os.environ["KEYBASE_USERNAME"],
        paperkey=os.environ["KEYBASE_PAPERKEY"],
        handler=Handler()
    )
    asyncio.run(bot.start({
        "local": True,
        "wallet": False,
        "dev": True,
        "hide-exploding": False,
        "filter_channel": None,
        "filter_channels": None,
    }))
