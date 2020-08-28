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
