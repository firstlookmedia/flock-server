import asyncio
import logging
import os
import subprocess
import shlex
from concurrent.futures import TimeoutError

import pykeybasebot
from elasticsearch_dsl import Index, Search

from .elasticsearch import es, User, KeybaseNotification
from .keybase_notifications import KeybaseNotifications


class Handler:
    def __init__(self):
        self.cmds = {
            "help": {
                "exec": self.help,
                "args": [],
                "desc": "Show this message"
            },
            "list_users": {
                "exec": self.list_users,
                "args": [],
                "desc": "List all registered users"
            },
            "delete_user": {
                "exec": self.delete_user,
                "args": ["username"],
                "desc": "Delete a user"
            },
            "rename_user": {
                "exec": self.rename_user,
                "args": ["username", "name"],
                "desc": "Rename a user"
            },
            "list_notifications": {
                "exec": self.list_notifications,
                "args": [],
                "desc": "List the enabled state of keybase notifications"
            },
            "enable_notification": {
                "exec": self.enable_notification,
                "args": ["notification_name"],
                "desc": "Enable a notification"
            },
            "disable_notification": {
                "exec": self.disable_notification,
                "args": ["notification_name"],
                "desc": "Disable a notification"
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
                if type(event.msg.content) != pykeybasebot.OmitIfEmpty and event.msg.content.text.userMentions:
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
            cmd_parts_with_mention = shlex.split(event.msg.content.text.body)
            cmd_parts = []
            for cmd_part in cmd_parts_with_mention:
                if cmd_part != '@{}'.format(os.environ.get("KEYBASE_USERNAME")):
                    cmd_parts.append(cmd_part)
            if len(cmd_parts) == 0:
                return

            # Validate the command
            cmd = cmd_parts.pop(0)
            if cmd not in self.cmds:
                await self._send(bot, event, "@{}: unknown command".format(event.msg.sender.username))
                return
            args = cmd_parts
            if len(args) != len(self.cmds[cmd]['args']):
                await self._reply_with_usage(bot, event, cmd)
                return

            # Execute the command
            await self.cmds[cmd]['exec'](bot, event, args)

    async def _send(self, bot, event, message):
        print("Sending message to {}: {}".format(event.msg.channel.name, repr(message)))
        await bot.chat.send(event.msg.channel.replyable_dict(), message)

    def _usage(self, cmd):
        if len(self.cmds[cmd]['args']) > 0:
            return '**{} [{}]**: {}'.format(cmd, '] ['.join(self.cmds[cmd]['args']), self.cmds[cmd]['desc'])
        else:
            return '**{}**: {}'.format(cmd, self.cmds[cmd]['desc'])

    async def _reply_with_usage(self, bot, event, cmd):
        await self._send(bot, event, "@{}: Here is how to use this command:\n{}".format(
            event.msg.sender.username, self._usage(cmd)))

    async def _validate_username_and_get_user(self, bot, event, username):
        # Validate the username
        valid = True
        valid_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-'
        for c in username:
            if c not in valid_chars:
                valid = False
                break
        if not valid:
            await self._send(bot, event, "@{}: The username you gave me contains invalid characters. You're not trying to be sneaky, are you?".format(event.msg.sender.username))
            return False

        # Get the user
        results = User.search().query('match', username=username).execute()
        if len(results) == 0:
            await self._send(bot, event, "@{}: No users with that username are registered :astonished:".format(event.msg.sender.username))
            return False

        user = results[0]
        return user

    async def help(self, bot, event, args):
        formatted = [self._usage(cmd) for cmd in self.cmds]
        await self._send(bot, event, "@{}: These are the commands I know:\n{}".format(event.msg.sender.username, '\n'.join(formatted)))

    async def list_users(self, bot, event, args):
        r = Search(index="user").query("match_all").execute()
        users = ['**{}** :point_right: **{}**'.format(str(hit['username']), str(hit['name'])) for hit in r]
        if len(users) == 0:
            await self._send(bot, event, "@{}: There are no registered users :cry:".format(event.msg.sender.username))
        else:
            await self._send(bot, event, "@{}: Here are all registered users:\n{}".format(event.msg.sender.username, '\n'.join(users)))

    async def delete_user(self, bot, event, args):
        username = args.pop(0)

        user = await self._validate_username_and_get_user(bot, event, username)
        if not user:
            return

        # Delete the user
        user.delete()
        Index('user').refresh()
        await self._send(bot, event, "@{}: User **{}** has been deleted.".format(event.msg.sender.username, username))

    async def rename_user(self, bot, event, args):
        username = args.pop(0)
        name = args.pop(0)

        user = await self._validate_username_and_get_user(bot, event, username)
        if not user:
            return

        # Rename the user
        user.update(name=name)
        user.save()
        Index('user').refresh()

        await self._send(bot, event, "@{}: Renamed user **{}** to **{}**".format(event.msg.sender.username, username, name))

    async def list_notifications(self, bot, event, args):
        keybase_notifications = KeybaseNotifications()
        enabled_state = keybase_notifications.get_enabled_state()

        notifications = []
        for name in enabled_state:
            if enabled_state[name]:
                notifications.append(':white_check_mark: **{}** :point_right: {}'.format(name, keybase_notifications.notifications[name]))
            else:
                notifications.append(':x: **{}** :point_right: {}'.format(name, keybase_notifications.notifications[name]))
        await self._send(bot, event, "@{}: Here's the enabled state of keybase notifications:\n{}".format(event.msg.sender.username, '\n'.join(notifications)))

    async def enable_notification(self, bot, event, args):
        #notification_name = args.pop(0)
        await self._send(bot, event, "@{}: not implemented yet".format(event.msg.sender.username, username))

    async def disable_notification(self, bot, event, args):
        #notification_name = args.pop(0)
        await self._send(bot, event, "@{}: not implemented yet".format(event.msg.sender.username, username))


async def notification_checker(channel, bot):
    keybase_notifications = KeybaseNotifications()
    while True:
        await asyncio.sleep(30)

        results = KeybaseNotification.search().query('match', delivered=False).execute()
        for keybase_notification in results:
            msg = keybase_notifications.format(keybase_notification.notification_type, keybase_notification.details)
            print("Sending notification: {}".format(repr(msg)))
            try:
                await bot.chat.send(channel, msg)
            except TimeoutError:
                pass

            keybase_notification.update(delivered=True)
            keybase_notification.save()
        Index('keybase_notification').refresh()


async def start(bot, channel):
    # Wait for keybase to be available
    tries = 1
    while True:
        try:
            await asyncio.sleep(5)
            print("Ensuring bot is initialized...")
            await bot.chat.send(channel, ":zzz:"*tries)
            break
        except TimeoutError:
            tries += 1

    # Send welcome message and start listening
    await asyncio.gather(
        bot.chat.send(channel,
            "Hello, friends! I'm a :robot_face:, and my process just woke up. Ask me for `help` for a list of commands."),
        bot.start({
            "local": False,
            "wallet": False,
            "dev": False,
            "hide-exploding": False,
            "filter_channels": None,
            "filter_channel": channel
        }),
        notification_checker(channel, bot)
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
