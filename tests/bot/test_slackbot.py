from mixer.backend.flask import mixer
from slack import WebClient

from nb2 import bot


class MockSlackResponse:
    def __init__(self, data):
        self.data = data


def test_get_user_info(client, session, mocker):
    mock_id = mixer.faker.pystr(10)
    mock_name = mixer.faker.name()

    mock_slack_user_object = {
        "id": mock_id,
        "team_id": "TFWDXKU4U",
        "name": mock_name,
        "deleted": False,
        "color": "e0a729",
        "real_name": mock_name,
        "tz": "America/Los_Angeles",
        "tz_label": "Pacific Daylight Time",
        "tz_offset": -25200,
        "profile": {
            "title": "",
            "phone": "",
            "skype": "",
            "real_name": mock_name,
            "real_name_normalized": mock_name,
            "display_name": "",
            "display_name_normalized": "",
            "fields": None,
            "status_text": "",
            "status_emoji": "",
            "status_expiration": 0,
            "avatar_hash": "g73e9ce19aea",
            "api_app_id": "A019Y9H4CBS",
            "always_active": False,
            "bot_id": "B0198LAKV5Z",
            "status_text_canonical": "",
            "team": "TFWDXKU4U",
        },
        "is_admin": False,
        "is_owner": False,
        "is_primary_owner": False,
        "is_restricted": False,
        "is_ultra_restricted": False,
        "is_bot": True,
        "is_app_user": False,
        "updated": 1597982710,
    }

    mock_response = {"user": mock_slack_user_object}

    mocker.patch.object(WebClient, "users_info", return_value=MockSlackResponse(mock_response))

    response = bot.get_user_info(mock_id)

    assert isinstance(response, dict)
    assert "id" in response
    assert "name" in response
    assert response.get("id") == mock_id
    assert response.get("name") == mock_name
