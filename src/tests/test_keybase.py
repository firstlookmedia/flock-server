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
        members_type = pykeybasebot.MembersType.TEAM # team
    else:
        members_type = pykeybasebot.MembersType.IMPTEAMNATIVE # direct chat
    channel = pykeybasebot.Channel(channel_name, False, members_type, pykeybasebot.TopicType.CHAT, topic_name=topic_name)

    sender = pykeybasebot.Sender("uid", sender_username, "device_id", "device_name")

    content_text = pykeybasebot.ContentText(body, None, user_mentions, [])
    content = pykeybasebot.Content(pykeybasebot.ContentType.TEXT, text=content_text)

    msg = pykeybasebot.Message(123, channel, sender, int(time.time()), int(time.time()*1000), content)

    event = pykeybasebot.KbEvent(pykeybasebot.EventType.CHAT, pykeybasebot.Source.REMOTE, msg=msg)
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
    res = client.post('/register', data={'username': "UUID1", "name": "Nick Fury"})
    assert res.status_code == 200

    res = client.post('/register', data={'username': "UUID2", "name": "Jessica Jones"})
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
    res = client.post('/register', data={'username': "UUID1", "name": "Nick Fury"})
    assert res.status_code == 200

    event = create_event("kbusername1", '@flockbot rename_user inval!d_userN4me "Jessica Jones"')
    await handler.__call__(bot, event)
    assert bot.didnt_say("Renamed user")
    assert bot.said("The username you gave me contains invalid characters")

    event = create_event("kbusername1", '@flockbot rename_user UUID2 "Jessica Jones"')
    await handler.__call__(bot, event)
    assert bot.didnt_say("Renamed user")
    assert bot.said("No users with that username are registered")


@pytest.mark.asyncio
async def test_rename_user(client, handler, bot):
    res = client.post('/register', data={'username': "UUID1", "name": "Nick Fury"})
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
    res = client.post('/register', data={'username': "UUID1", "name": "Nick Fury"})
    assert res.status_code == 200

    event = create_event("kbusername1", '@flockbot delete_user inval!d_userN4me')
    await handler.__call__(bot, event)
    assert bot.didnt_say("has been deleted")
    assert bot.said("The username you gave me contains invalid characters")

    event = create_event("kbusername1", '@flockbot delete_user UUID2')
    await handler.__call__(bot, event)
    assert bot.didnt_say("has been deleted")
    assert bot.said("No users with that username are registered")


@pytest.mark.asyncio
async def test_delete_user(client, handler, bot):
    event = create_event("kbusername1", "@flockbot list_users")
    await handler.__call__(bot, event)
    assert bot.said("There are no registered users")

    res = client.post('/register', data={'username': "UUID1", "name": "Nick Fury"})
    assert res.status_code == 200

    event = create_event("kbusername1", "@flockbot list_users")
    await handler.__call__(bot, event)
    assert bot.didnt_say("There are no registered users")
    assert bot.said("Nick Fury")

    event = create_event("kbusername1", '@flockbot delete_user UUID1')
    await handler.__call__(bot, event)
    assert bot.said("has been deleted")

    event = create_event("kbusername1", "@flockbot list_users")
    await handler.__call__(bot, event)
    assert bot.said("There are no registered users")
    assert bot.didnt_say("Nick Fury")
