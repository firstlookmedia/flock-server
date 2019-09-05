import asyncio
import logging
import os
import subprocess
from concurrent.futures import TimeoutError

import pykeybasebot

logging.basicConfig(level=logging.DEBUG)


class Handler:
    async def __call__(self, bot, event):
        print(event)
        # Only listen for remote chat messages
        if event.type == pykeybasebot.EventType.CHAT and event.source == pykeybasebot.Source.REMOTE:

            # Am I mentioned?
            mentioned = False
            if event.msg.content.text.userMentions:
                for user_mention in event.msg.content.text.userMentions:
                    if user_mention.text == os.environ.get("KEYBASE_USERNAME"):
                        mentioned = True
                        break
            if not mentioned:
                return

            # Only answer to admins
            keybase_admins = os.environ.get('KEYBASE_ADMIN_USERNAMES').split(',')
            if event.msg.sender.username not in keybase_admins:
                await bot.chat.send(event.msg.channel.replyable_dict(),
                    "Sorry @{}. I'm not configured to talk to you.".format(event.msg.sender.username))
                return

            # Parse the command
            cmd_parts_with_mention = event.msg.content.text.body.split()
            cmd_parts = []
            for cmd_part in cmd_parts_with_mention:
                if cmd_part != '@{}'.format(os.environ.get("KEYBASE_USERNAME")):
                    cmd_parts.append(cmd_part)
            if len(cmd_parts) == 0:
                return

            # help
            if cmd_parts[0] == 'help':
                await bot.chat.send(event.msg.channel.replyable_dict(),
                    "@{}: **help** isn't implemented yet".format(event.msg.sender.username))
                return

            # Unknown command
            else:
                await bot.chat.send(event.msg.channel.replyable_dict(),
                    "@{}: unknown command".format(event.msg.sender.username))
                return



async def start(bot, channel):
    # Keep trying to post welcome message until it works
    while True:
        try:
            print("Trying to post keybase message...")
            await bot.chat.send(channel,
                "Hello, friends. I'm a :robot_face:, and my process just started.\nFor a list of commands: `@{} help`".format(os.environ.get('KEYBASE_USERNAME')))
            break
        except TimeoutError:
            print("Timed out, waiting 1 second")
            await asyncio.sleep(1)

    await bot.start({
        "local": False,
        "wallet": False,
        "dev": False,
        "hide-exploding": False,
        "filter_channels": None,
        "filter_channel": channel
    })


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
    if not os.environ.get("KEYBASE_ADMIN_USERNAMES"):
        print("Error: KEYBASE_ADMIN_USERNAMES must be set")
        validated = False
    if not validated:
        return

    # Run keybase service
    subprocess.call(["run_keybase", "-g"])

    # Create the bot
    bot = pykeybasebot.Bot(
        username=os.environ.get("KEYBASE_USERNAME"),
        paperkey=os.environ.get("KEYBASE_PAPERKEY"),
        handler=Handler()
    )
    channel = {
        "name": os.environ.get("KEYBASE_TEAM"),
        "topic_name": os.environ.get("KEYBASE_CHANNEL"),
        "members_type": "team"
    }

    # Start the bot
    asyncio.run(start(bot, channel))


if __name__ == '__main__':
    start_keybase_bot()
