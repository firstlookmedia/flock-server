import asyncio
import logging
import os
import subprocess
from concurrent.futures import TimeoutError

import pykeybasebot

logging.basicConfig(level=logging.DEBUG)


class Handler:
    def __init__(self):
        self.cmds = {
            "help": {
                "exec": self.help,
                "desc": "List of commands that I know"
            },
            "list_users": {
                "exec": self.list_users,
                "desc": "List the UUIDs of flock agents"
            }
        }

    async def __call__(self, bot, event):
        #print(event)

        # Ignore if sender is the bot itself
        if event.msg.sender.username == os.environ.get('KEYBASE_USERNAME'):
            return

        # Only listen for remote chat messages
        if event.type == pykeybasebot.EventType.CHAT and event.source == pykeybasebot.Source.REMOTE:
            if event.msg.channel.members_type == pykeybasebot.MembersType.TEAM:
                # Is the bot mentioned?
                mentioned = False
                if type(event.msg.content) is not pykeybasebot.OmitIfEmpty and event.msg.content.text.userMentions:
                    for user_mention in event.msg.content.text.userMentions:
                        if user_mention.text == os.environ.get("KEYBASE_USERNAME"):
                            mentioned = True
                            break
                if not mentioned:
                    return
            else:
                if event.msg.channel.members_type == pykeybasebot.MembersType.IMPTEAMNATIVE:
                    # This is a direct message
                    pass
                else:
                    # This isn't in the team or a direct message, so ignore
                    return

            # Only answer to admins
            keybase_admins = os.environ.get('KEYBASE_ADMIN_USERNAMES').split(',')
            if event.msg.sender.username not in keybase_admins:
                print("{} tried talking to me, but that user is not an admin".format(event.msg.sender.username))
                await bot.chat.send(event.msg.channel.replyable_dict(),
                    "Sorry @{}. I'm not configured to talk to you.".format(
                        event.msg.sender.username))
                return

            # Parse the command
            cmd_parts_with_mention = event.msg.content.text.body.split()
            if event.msg.channel.name == os.environ.get('KEYBASE_CHANNEL'):
                # If this is in the team, strip to mention
                cmd_parts = []
                for cmd_part in cmd_parts_with_mention:
                    if cmd_part != '@{}'.format(os.environ.get("KEYBASE_USERNAME")):
                        cmd_parts.append(cmd_part)
                if len(cmd_parts) == 0:
                    return
            else:
                cmd_parts = cmd_parts_with_mention

            # Execute the command
            cmd = cmd_parts[0]
            if cmd in self.cmds:
                print(cmd_parts)
                await self.cmds[cmd]['exec'](bot, event, cmd_parts)
            else:
                await bot.chat.send(event.msg.channel.replyable_dict(),
                    "@{}: unknown command".format(event.msg.sender.username))

    async def help(self, bot, event, cmd_parts):
        formatted_commands = ['**{}**: {}'.format(cmd, self.cmds[cmd]['desc']) for cmd in self.cmds]
        await bot.chat.send(event.msg.channel.replyable_dict(),
            "@{}: These are the commands I know:\n{}".format(
                event.msg.sender.username,
                '\n'.join(formatted_commands)))

    async def list_users(self, bot, event, cmd_parts):
        await bot.chat.send(event.msg.channel.replyable_dict(),
            "@{}: **list_users** command is not implemented yet".format(
                event.msg.sender.username))


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
