from slack import WebClient
from slackeventsapi import SlackEventAdapter


class SlackBot:
    def __init__(self):
        self.web_client = None
        self.event_adapter = None

    def init_app(self, token, signing_secret, event_url, app):
        self.web_client = WebClient(token=token)
        self.event_adapter = SlackEventAdapter(signing_secret, event_url, app)

    def send_text(self, text, channel):
        self.web_client.chat_postMessage(text=text, channel=channel)

    def send_blocks(self, blocks, channel):
        self.web_client.chat_postMessage(blocks=blocks, channel=channel)

    def get_user_info(self, slack_user_id: str):
        """
        Return Slack's representation of a user with id slack_user_id.

        Args:
            slack_user_id: string representing the Person's primary Slack id.

        Returns:
            {} containing Slack user information.
        """
        return self.web_client.users_info(user=slack_user_id).data["user"]
