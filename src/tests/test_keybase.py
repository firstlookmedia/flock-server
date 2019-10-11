import os
import time
import pytest
import asyncio
import pykeybasebot


def create_event(sender_username, body, members_type=None):
    # Calculate user_mentions
    user_mentions = []
    for part in body.split():
        if part.startswith("@"):
            user_mentions.append(part[1:])

    channel_name = "keybase_team_name"
    topic_name = "flock_notifications_channel"

    if members_type:
        members_type = "team"
    else:
        members_type = "impteamnative"  # direct chat

    channel = pykeybasebot.types.chat1.ChatChannel(
        name=channel_name,
        public=False,
        members_type=members_type,
        topic_type="chat",
        topic_name=topic_name,
    )
    sender = pykeybasebot.types.chat1.MsgSender(
        uid="uid",
        device_id="device_id",
        username=sender_username,
        device_name="device_name",
    )
    content_text = pykeybasebot.types.chat1.MessageText(
        body=body, user_mentions=user_mentions
    )
    content = pykeybasebot.types.chat1.MsgContent(type_name="text", text=content_text)
    msg = pykeybasebot.types.chat1.MsgSummary(
        id=123,
        conv_id="conv_id",
        channel=channel,
        sender=sender,
        sent_at=int(time.time()),
        sent_at_ms=int(time.time() * 1000),
        content=content,
        unread=True,
    )
    event = pykeybasebot.KbEvent(
        type=pykeybasebot.EventType.CHAT, source=pykeybasebot.Source.REMOTE, msg=msg
    )
    return event


@pytest.mark.asyncio
async def test_not_admin(handler, bot):
    event = create_event("hacker", "@flockbot help")
    await handler.__call__(bot, event)
    assert bot.said("I'm not configured to talk to you.")


@pytest.mark.asyncio
async def test_ignore_self(handler, bot):
    event = create_event("flockbot", "@flockbot help")
    await handler.__call__(bot, event)
    assert bot.stayed_silent()


@pytest.mark.asyncio
async def test_help(handler, bot):
    event = create_event("kbusername1", "@flockbot help")
    await handler.__call__(bot, event)
    assert bot.said("These are the commands I know:")


@pytest.mark.asyncio
async def test_list_users_empty(client, handler, bot):
    event = create_event("kbusername1", "@flockbot list_users")
    await handler.__call__(bot, event)
    assert bot.said("There are no registered users")


@pytest.mark.asyncio
async def test_list_users_with_users(client, handler, bot):
    res = client.post("/register", data={"username": "UUID1", "name": "Nick Fury"})
    assert res.status_code == 200

    res = client.post("/register", data={"username": "UUID2", "name": "Jessica Jones"})
    assert res.status_code == 200

    event = create_event("kbusername1", "@flockbot list_users")
    await handler.__call__(bot, event)
    assert bot.didnt_say("There are no registered users")
    assert bot.said("UUID1")
    assert bot.said("Nick Fury")
    assert bot.said("UUID2")
    assert bot.said("Jessica Jones")


@pytest.mark.asyncio
async def test_rename_user_invalid_username(client, handler, bot):
    res = client.post("/register", data={"username": "UUID1", "name": "Nick Fury"})
    assert res.status_code == 200

    event = create_event(
        "kbusername1", '@flockbot rename_user inval!d_userN4me "Jessica Jones"'
    )
    await handler.__call__(bot, event)
    assert bot.didnt_say("Renamed user")
    assert bot.said("The username you gave me contains invalid characters")

    event = create_event("kbusername1", '@flockbot rename_user UUID2 "Jessica Jones"')
    await handler.__call__(bot, event)
    assert bot.didnt_say("Renamed user")
    assert bot.said("No users with that username are registered")


@pytest.mark.asyncio
async def test_rename_user(client, handler, bot):
    res = client.post("/register", data={"username": "UUID1", "name": "Nick Fury"})
    assert res.status_code == 200

    event = create_event("kbusername1", "@flockbot list_users")
    await handler.__call__(bot, event)
    assert bot.said("Nick Fury")

    event = create_event("kbusername1", '@flockbot rename_user UUID1 "Jessica Jones"')
    await handler.__call__(bot, event)
    assert bot.said("Renamed user")

    event = create_event("kbusername1", "@flockbot list_users")
    await handler.__call__(bot, event)
    assert bot.didnt_say("Nick Fury")
    assert bot.said("Jessica Jones")


@pytest.mark.asyncio
async def test_delete_user_invalid_username(client, handler, bot):
    res = client.post("/register", data={"username": "UUID1", "name": "Nick Fury"})
    assert res.status_code == 200

    event = create_event("kbusername1", "@flockbot delete_user inval!d_userN4me")
    await handler.__call__(bot, event)
    assert bot.didnt_say("has been deleted")
    assert bot.said("The username you gave me contains invalid characters")

    event = create_event("kbusername1", "@flockbot delete_user UUID2")
    await handler.__call__(bot, event)
    assert bot.didnt_say("has been deleted")
    assert bot.said("No users with that username are registered")


@pytest.mark.asyncio
async def test_delete_user(client, handler, bot):
    event = create_event("kbusername1", "@flockbot list_users")
    await handler.__call__(bot, event)
    assert bot.said("There are no registered users")

    res = client.post("/register", data={"username": "UUID1", "name": "Nick Fury"})
    assert res.status_code == 200

    event = create_event("kbusername1", "@flockbot list_users")
    await handler.__call__(bot, event)
    assert bot.didnt_say("There are no registered users")
    assert bot.said("Nick Fury")

    event = create_event("kbusername1", "@flockbot delete_user UUID1")
    await handler.__call__(bot, event)
    assert bot.said("has been deleted")

    event = create_event("kbusername1", "@flockbot list_users")
    await handler.__call__(bot, event)
    assert bot.said("There are no registered users")
    assert bot.didnt_say("Nick Fury")


@pytest.mark.asyncio
async def test_list_notifications(keybase_notifications, handler, bot):
    event = create_event("kbusername1", "@flockbot list_notifications")
    await handler.__call__(bot, event)
    assert bot.said("user_registered")
    assert bot.said("A user has registered with the server")
    # Make all settings are enabled
    for line in bot.message.split("\n")[1:]:
        assert line.startswith(":white_check_mark:")


@pytest.mark.asyncio
async def test_enable_notification_invalid(keybase_notifications, handler, bot):
    event = create_event("kbusername1", "@flockbot enable_notification foobar")
    await handler.__call__(bot, event)
    assert bot.said("That notification does not exist")


@pytest.mark.asyncio
async def test_enable_notification(keybase_notifications, handler, bot):
    event = create_event("kbusername1", "@flockbot enable_notification user_registered")
    await handler.__call__(bot, event)
    assert bot.said("Notification already enabled")

    event = create_event(
        "kbusername1", "@flockbot disable_notification user_registered"
    )
    await handler.__call__(bot, event)
    assert bot.said("Notification disabled")

    event = create_event("kbusername1", "@flockbot list_notifications")
    await handler.__call__(bot, event)
    assert bot.said(":x: **user_registered**")

    event = create_event("kbusername1", "@flockbot enable_notification user_registered")
    await handler.__call__(bot, event)
    assert bot.said("Notification enabled")

    event = create_event("kbusername1", "@flockbot list_notifications")
    await handler.__call__(bot, event)
    assert bot.said(":white_check_mark: **user_registered**")
    assert bot.said(":white_check_mark: **user_already_exists**")


@pytest.mark.asyncio
async def test_disable_notification_invalid(keybase_notifications, handler, bot):
    event = create_event("kbusername1", "@flockbot disable_notification foobar")
    await handler.__call__(bot, event)
    assert bot.said("That notification does not exist")


@pytest.mark.asyncio
async def test_disable_notification(keybase_notifications, handler, bot):
    event = create_event(
        "kbusername1", "@flockbot disable_notification user_registered"
    )
    await handler.__call__(bot, event)
    assert bot.said("Notification disabled")

    event = create_event(
        "kbusername1", "@flockbot disable_notification user_registered"
    )
    await handler.__call__(bot, event)
    assert bot.said("Notification already disabled")

    event = create_event("kbusername1", "@flockbot list_notifications")
    await handler.__call__(bot, event)
    assert bot.said(":x: **user_registered**")
    assert bot.said(":white_check_mark: **user_already_exists**")
