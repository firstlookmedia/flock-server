import os
import time
import pytest
import pykeybasebot


def create_event(channel_name, topic_name, sender_username, body, members_type=None):
    # Calculate user_mentions
    user_mentions = []
    for part in body.split():
        if part.startswith("@"):
            user_mentions.append(part[1:])

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
    event = create_event("keybase_team_name", "flock_notifications_channel", "hacker",
        "@flockbot help")
    await handler.__call__(bot, event)
    assert bot.said("I'm not configured to talk to you.")
