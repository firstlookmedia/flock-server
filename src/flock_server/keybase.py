import asyncio
import logging
import os
import subprocess
from concurrent.futures import TimeoutError

import pykeybasebot

#logging.basicConfig(level=logging.DEBUG)


class Handler:
    def __init__(self):
        self.cmds = {
            "help": {
                "exec": self.help,
                "desc": "Show this message"
            },
            "list_users": {
                "exec": self.list_users,
                "desc": "List all registered users"
            },
            "delete_user": {
                "exec": self.delete_user,
                "args": ["username"],
                "desc": "Delete a user"
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
            cmd_parts = []
            for cmd_part in cmd_parts_with_mention:
                if cmd_part != '@{}'.format(os.environ.get("KEYBASE_USERNAME")):
                    cmd_parts.append(cmd_part)
            if len(cmd_parts) == 0:
                return

            # Execute the command
            cmd = cmd_parts[0]
            if cmd in self.cmds:
                await self.cmds[cmd]['exec'](bot, event, cmd_parts)
            else:
                await self._send(bot, event, "@{}: unknown command".format(event.msg.sender.username))

    async def _send(self, bot, event, message):
        print("Sending message to {}: {}".format(event.msg.channel.name, message))
        await bot.chat.send(event.msg.channel.replyable_dict(), message)

    async def help(self, bot, event, cmd_parts):
        formatted = []
        for cmd in self.cmds:
            if 'args' in self.cmds[cmd]:
                formatted.append('**{} [{}]**: {}'.format(cmd, '] ['.join(self.cmds[cmd]['args']), self.cmds[cmd]['desc']))
            else:
                formatted.append('**{}**: {}'.format(cmd, self.cmds[cmd]['desc']))

        await self._send(bot, event, "@{}: These are the commands I know:\n{}".format(event.msg.sender.username, '\n'.join(formatted)))

    async def list_users(self, bot, event, cmd_parts):
        await self._send(bot, event, "@{}: **list_users** command is not implemented yet".format(event.msg.sender.username))

    async def delete_user(self, bot, event, cmd_parts):
        await self._send(bot, event, "@{}: **delete_user** command is not implemented yet".format(event.msg.sender.username))


async def start(bot, channel):
    # Wait for keybase to be available
    tries = 1
    while True:
        try:
            print("Ensuring bot is initialized...")
            await bot.chat.send(channel, ":zzz:"*tries)
            break
        except TimeoutError:
            print("Timed out, waiting 2 seconds")
            tries += 1
            await asyncio.sleep(2)

    # Send welcome message and start listening
    await asyncio.gather(
        bot.chat.send(channel,
            "Hello, friends! I'm a :robot_face:, and my process just woke up. Ask me for `help` for a list of commands.".format(
                os.environ.get('KEYBASE_USERNAME')
            )),
        bot.start({
            "local": False,
            "wallet": False,
            "dev": False,
            "hide-exploding": False,
            "filter_channels": None,
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
