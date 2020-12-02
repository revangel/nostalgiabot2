from mixer.backend.flask import mixer

from nb2.service.slack_service import (
    get_quote_content_from_remember_command,
    get_user_ids_from_command,
    mention_users,
)


def test_get_user_ids_from_command(client, session):
    command_string = "Yada Yada <@foo>, &#<@emin>, @gotcha, and <@U123>!"
    expected = ["foo", "emin", "U123"]
    assert get_user_ids_from_command(command_string) == expected


def test_get_quote_content_from_remember_command_returns_content_on_valid_command(client, session):
    mock_content = mixer.faker.sentence()
    command_string = f'remember that <@U123> said "{mock_content}"'
    assert get_quote_content_from_remember_command(command_string) == mock_content


def test_mention_users_add_mention_tokens(client, session):
    user_ids = ["abc", "123"]
    expected = "<@abc> <@123>"

    result = mention_users(user_ids)

    assert result == expected
