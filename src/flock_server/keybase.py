import asyncio
import logging
import os
import subprocess
import shlex

import pykeybasebot
from elasticsearch.exceptions import RequestError
from elasticsearch_dsl import Index, Search

from .elasticsearch import es, User, KeybaseNotification
from .keybase_notifications import KeybaseNotifications


class Handler:
    def __init__(self):
        self.keybase_notifications = KeybaseNotifications()
        self.cmds = {
            "help": {"exec": self.help, "args": [], "desc": "Show this message"},
            "list_users": {
                "exec": self.list_users,
                "args": [],
                "desc": "List all registered users",
            },
            "delete_user": {
                "exec": self.delete_user,
                "args": ["username"],
                "desc": "Delete a user",
            },
            "rename_user": {
                "exec": self.rename_user,
                "args": ["username", "name"],
                "desc": "Rename a user",
            },
            "list_notifications": {
                "exec": self.list_notifications,
                "args": [],
                "desc": "List the enabled state of keybase notifications",
            },
            "enable_notification": {
                "exec": self.enable_notification,
                "args": ["notification_name"],
                "desc": "Enable a notification",
            },
            "disable_notification": {
                "exec": self.disable_notification,
                "args": ["notification_name"],
                "desc": "Disable a notification",
            },
        }

    async def __call__(self, bot, event):
        # print(event)

        # Ignore if sender is the bot itself
        if event.msg.sender.username == os.environ.get("KEYBASE_USERNAME"):
            return

        # Only listen for remote chat messages
        if (
            event.type == pykeybasebot.EventType.CHAT
            and event.source == pykeybasebot.Source.REMOTE
        ):
            # Only answer to admins
            keybase_admins = os.environ.get("KEYBASE_ADMIN_USERNAMES").split(",")
            if event.msg.sender.username not in keybase_admins:
                print(
                    "{} tried talking to me, but that user is not an admin".format(
                        event.msg.sender.username
                    )
                )
                try:
                    await bot.chat.send(
                        event.msg.conv_id,
                        "Sorry @{}. I'm not configured to talk to you.".format(
                            event.msg.sender.username
                        ),
                    )
                except asyncio.exceptions.TimeoutError:
                    pass
                return

            # Parse the command
            cmd_parts_with_mention = shlex.split(event.msg.content.text.body)
            cmd_parts = []
            for cmd_part in cmd_parts_with_mention:
                if cmd_part != "@{}".format(os.environ.get("KEYBASE_USERNAME")):
                    cmd_parts.append(cmd_part)
            if len(cmd_parts) == 0:
                return

            # Validate the command
            cmd = cmd_parts.pop(0)
            if cmd not in self.cmds:
                await self._send(
                    bot, event, "@{}: unknown command".format(event.msg.sender.username)
                )
                return
            args = cmd_parts
            if len(args) != len(self.cmds[cmd]["args"]):
                await self._reply_with_usage(bot, event, cmd)
                return

            # Execute the command
            await self.cmds[cmd]["exec"](bot, event, args)

    async def _send(self, bot, event, message):
        print("Sending message to {}: {}".format(event.msg.conv_id, repr(message)))
        try:
            await bot.chat.send(event.msg.conv_id, message)
        except asyncio.exceptions.TimeoutError:
            pass

    def _usage(self, cmd):
        if len(self.cmds[cmd]["args"]) > 0:
            return "**{} [{}]**: {}".format(
                cmd, "] [".join(self.cmds[cmd]["args"]), self.cmds[cmd]["desc"]
            )
        else:
            return "**{}**: {}".format(cmd, self.cmds[cmd]["desc"])

    async def _reply_with_usage(self, bot, event, cmd):
        await self._send(
            bot,
            event,
            "@{}: Here is how to use this command:\n{}".format(
                event.msg.sender.username, self._usage(cmd)
            ),
        )

    async def _validate_username_and_get_user(self, bot, event, username):
        # Validate the username
        valid = True
        valid_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"
        for c in username:
            if c not in valid_chars:
                valid = False
                break
        if not valid:
            await self._send(
                bot,
                event,
                "@{}: The username you gave me contains invalid characters. You're not trying to be sneaky, are you?".format(
                    event.msg.sender.username
                ),
            )
            return False

        # Get the user
        results = User.search().query("match", username=username).execute()
        if len(results) == 0:
            await self._send(
                bot,
                event,
                "@{}: No users with that username are registered :astonished:".format(
                    event.msg.sender.username
                ),
            )
            return False

        user = results[0]
        return user

    async def _validate_notification(self, bot, event, notification_name):
        if notification_name not in self.keybase_notifications.notifications:
            await self._send(
                bot,
                event,
                "@{}: That notification does not exist :zany_face:".format(
                    event.msg.sender.username
                ),
            )
            return False
        return True

    async def help(self, bot, event, args):
        formatted = [self._usage(cmd) for cmd in self.cmds]
        await self._send(
            bot,
            event,
            "@{}: These are the commands I know:\n{}".format(
                event.msg.sender.username, "\n".join(formatted)
            ),
        )

    async def list_users(self, bot, event, args):
        # Get all users
        user_r = Search(index="user").query("match_all").execute()

        # Start gathering data on users
        users = {}
        for user_hit in user_r:
            key = (user_hit.name, user_hit.username)
            users[key] = {}

            # Get last updated
            try:
                r = (
                    Search(index="flock-*")
                    .query("match", hostIdentifier=user_hit.username)
                    .sort("-@timestamp")[0:1]
                    .execute()
                )

                if len(r) > 0:
                    hit = r[0]
                    users[key]["last_updated"] = hit.calendarTime
            except RequestError:
                # Ignoring this exception, because it will get triggered if an index it's searching doesn't
                # have a mapping for @timestamp, which happens in the tests. And there doesn't seem to be
                # a way to use elasticsearch_dsl to call `.sort` with `ignore_unmapped`...
                # RequestError(400, 'search_phase_execution_exception', 'No mapping found for [@timestamp] in order to sort on')
                pass

            # Get OS version
            try:
                r = (
                    Search(index="flock-*")
                    .query("match", hostIdentifier=user_hit.username)
                    .query("match", name="os_version")
                    .sort("-@timestamp")[0:1]
                    .execute()
                )
                if len(r) > 0:
                    hit = r[0]
                    users[key][
                        "os_version"
                    ] = f"{hit.columns.name} {hit.columns.version}"
            except RequestError:
                pass

        # Display response output, sorted by name
        response_str = ""
        for name, username in sorted(users.keys()):
            response_str += f"**{name}**\n"
            response_str += f"username :point_right: {username}\n"
            for key in users[name, username]:
                if key != "name":
                    response_str += f"{key} :point_right: {users[name,username][key]}\n"
            response_str += "\n"

        if len(users) == 0:
            await self._send(
                bot,
                event,
                "@{}: There are no registered users :cry:".format(
                    event.msg.sender.username
                ),
            )
        else:
            await self._send(
                bot,
                event,
                "@{}: Here are all registered users:\n\n{}".format(
                    event.msg.sender.username, response_str
                ),
            )

    async def delete_user(self, bot, event, args):
        username = args.pop(0)

        user = await self._validate_username_and_get_user(bot, event, username)
        if not user:
            return

        # Delete the user
        user.delete()
        Index("user").refresh()
        await self._send(
            bot,
            event,
            "@{}: User **{}** has been deleted.".format(
                event.msg.sender.username, username
            ),
        )

    async def rename_user(self, bot, event, args):
        username = args.pop(0)
        name = args.pop(0)

        user = await self._validate_username_and_get_user(bot, event, username)
        if not user:
            return

        # Rename the user
        user.update(name=name)
        user.save()
        Index("user").refresh()

        await self._send(
            bot,
            event,
            "@{}: Renamed user **{}** to **{}**".format(
                event.msg.sender.username, username, name
            ),
        )

    async def list_notifications(self, bot, event, args):
        enabled_state = self.keybase_notifications.get_enabled_state()
        notifications = []
        for name in enabled_state:
            if enabled_state[name]:
                notifications.append(
                    ":white_check_mark: **{}** :point_right: {}".format(
                        name, self.keybase_notifications.notifications[name]
                    )
                )
            else:
                notifications.append(
                    ":x: **{}** :point_right: {}".format(
                        name, self.keybase_notifications.notifications[name]
                    )
                )
        await self._send(
            bot,
            event,
            "@{}: Here's the enabled state of keybase notifications:\n{}".format(
                event.msg.sender.username, "\n".join(notifications)
            ),
        )

    async def enable_notification(self, bot, event, args):
        notification_name = args.pop(0)
        if await self._validate_notification(bot, event, notification_name):
            enabled_state = self.keybase_notifications.get_enabled_state()
            if enabled_state[notification_name]:
                await self._send(
                    bot,
                    event,
                    "@{}: Notification already enabled".format(
                        event.msg.sender.username
                    ),
                )
            else:
                self.keybase_notifications.enable(notification_name)
                await self._send(
                    bot,
                    event,
                    "@{}: Notification enabled".format(event.msg.sender.username),
                )

    async def disable_notification(self, bot, event, args):
        notification_name = args.pop(0)
        if await self._validate_notification(bot, event, notification_name):
            enabled_state = self.keybase_notifications.get_enabled_state()
            if not enabled_state[notification_name]:
                await self._send(
                    bot,
                    event,
                    "@{}: Notification already disabled".format(
                        event.msg.sender.username
                    ),
                )
            else:
                self.keybase_notifications.disable(notification_name)
                await self._send(
                    bot,
                    event,
                    "@{}: Notification disabled".format(event.msg.sender.username),
                )


async def notification_checker(conv_id, bot):
    keybase_notifications = KeybaseNotifications()
    while True:
        await asyncio.sleep(30)

        results = KeybaseNotification.search().query("match", delivered=False).execute()
        for keybase_notification in results:
            msg = keybase_notifications.format(
                keybase_notification.notification_type, keybase_notification.details
            )
            print("Sending notification: {}".format(repr(msg)))
            try:
                await bot.chat.send(conv_id, msg)
            except asyncio.exceptions.TimeoutError:
                pass

            keybase_notification.update(delivered=True)
            keybase_notification.save()
        Index("keybase_notification").refresh()


async def welcome_message(conv_id, bot):
    # Wait for keybase to be available
    tries = 1
    while True:
        try:
            await asyncio.sleep(5)
            print("Ensuring bot is initialized...")
            await bot.chat.send(conv_id, ":zzz:" * tries)
            break
        except asyncio.exceptions.TimeoutError:
            tries += 1

    # Send welcome message
    await bot.chat.send(
        conv_id,
        "Hello, friends! I'm a :robot_face:, and my process just woke up. Ask me for `help` for a list of commands.",
    )


async def start(bot, conv_id):
    await asyncio.gather(
        bot.start({"convs": True}),
        notification_checker(conv_id, bot),
        welcome_message(conv_id, bot),
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
    if not os.environ.get("KEYBASE_CONV_ID"):
        print("Error: KEYBASE_CONV_ID must be set")
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
        handler=Handler(),
    )
    conv_id = os.environ.get("KEYBASE_CONV_ID")

    # Start the bot
    asyncio.run(start(bot, conv_id))


if __name__ == "__main__":
    start_keybase_bot()
