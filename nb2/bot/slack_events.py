from nb2 import bot


@bot.event_adapter.on("app_mention")
def handle_app_mention(payload):
    """
    A Slackbot event handler that is intended to be mapped to the
    `app_mention` Slack event.

    TODO
    This currently just responds with a friendly greeting, but
    should be updated to parse commands and respond accordingly.
    """
    event = payload.get("event", {})
    channel = event.get("channel")
    bot.run_action(payload, channel)
