import asyncio
import logging
import os

from pykeybasebot import Bot

logging.basicConfig(level=logging.DEBUG)


class Handler:
    async def __call__(self, bot, event):
        print(event)


async def start(bot, channel):
    await asyncio.gather(
        bot.chat.send(channel, "My process just started :computer:"),
        bot.start({
            "local": False,
            "wallet": False,
            "dev": False,
            "hide-exploding": False,
            "filter_channel": channel
        })
    )


def start_keybase_bot():
    # Validation
    validated = True
    if not os.environ.get("KEYBASE_USERNAME"):
        print("Error: KEYBASE_USERNAME must be set")
        validated = False
    if not os.environ.get("KEYBASE_PAPERKEY"):
        print("Error: KEYBASE_PAPERKEY must be set")
        validated = False
    if not os.environ.get("KEYBASE_TEAM"):
        print("Error: KEYBASE_TEAM must be set")
        validated = False
    if not os.environ.get("KEYBASE_CHANNEL"):
        print("Error: KEYBASE_CHANNEL must be set")
        validated = False
    if not validated:
        return

    # Start the bot
    bot = Bot(
        username=os.environ.get("KEYBASE_USERNAME"),
        paperkey=os.environ.get("KEYBASE_PAPERKEY"),
        handler=Handler()
    )
    channel = {
        "name": os.environ.get("KEYBASE_TEAM"),
        "topic_name": os.environ.get("KEYBASE_CHANNEL"),
        "members_type": "team"
    }

    asyncio.run(start(bot, channel))


if __name__ == '__main__':
    start_keybase_bot()
