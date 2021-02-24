from flask import Blueprint
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

from nb2 import bot

bp = Blueprint("slack_socket_mode", __name__)


class FlaskSocketModeClient(SocketModeClient):
    def __init__(self, app, app_token, web_client):
        super().__init__(app_token=app_token, web_client=web_client)
        self.app = app
        self.socket_mode_request_listeners.append(self.process)
        self.connect()

    def process(self, client: SocketModeClient, req: SocketModeRequest):
        if req.type == "events_api":
            # Acknowledge the request anyway
            response = SocketModeResponse(envelope_id=req.envelope_id)
            client.send_socket_mode_response(response)

            if (
                req.payload["event"]["type"] == "message"
                or req.payload["event"]["type"] == "app_mention"
            ) and req.payload["event"].get("subtype") is None:
                with self.app.app_context():
                    bot.run_action(req.payload, req.payload["event"]["channel"])
