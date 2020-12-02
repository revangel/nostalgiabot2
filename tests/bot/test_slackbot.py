import pytest
from mixer.backend.flask import mixer

from nb2.bot.slack_bot import SlackBot
from nb2.models import Person, Quote
from nb2.service.quote_service import add_quote_to_person  # noqa (linter doesn't see use in patch)


class MockSlackResponse:
    def __init__(self, data):
        self.data = data


@pytest.fixture()
def mock_bot(mocker):
    """
    Bot for tests with a standardized slack_user_id.
    """
    mock_bot = SlackBot()
    mock_bot.slack_user_id = "UB0T"
    mocker.patch.object(mock_bot, "web_client")
    return mock_bot


def test_init_bot_slack_user_id(client, session, mocker):
    mock_auth_test_object = {
        "ok": True,
        "url": "https://fake.slack.com/",
        "team": "Fake Workspace",
        "user": "Nostalgiabot 2",
        "team_id": "T12345678",
        "user_id": "U12345678",
    }

    # Create a sterile instance of SlackBot to ensure the initialization
    # works properly from a clean slate.
    mock_bot = SlackBot()

    mocker.patch.object(mock_bot, "web_client")
    mocker.patch.object(mock_bot.web_client, "auth_test", return_value=mock_auth_test_object)

    mock_bot._init_bot_slack_user_id()

    assert mock_bot.slack_user_id is not None
    assert mock_bot.slack_user_id == mock_auth_test_object.get("user_id")


def test_fetch_user_info(client, session, mock_bot, mocker):
    mock_slack_user_id = mixer.faker.pystr(10)
    mock_name = mixer.faker.name()

    mock_slack_user_object = {
        "id": mock_slack_user_id,
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

    mocker.patch.object(
        mock_bot.web_client, "users_info", return_value=MockSlackResponse(mock_response)
    )

    response = mock_bot.fetch_user_info(mock_slack_user_id)

    assert isinstance(response, dict)
    assert response.get("id") == mock_slack_user_id
    assert response.get("name") == mock_name


@pytest.mark.parametrize(
    "test_message, all_occurrences, expected_result",
    (
        ("<@bot>", False, ""),
        ("<@bot> <@bot>", False, "<@bot>"),
        ("<@bot> <@bot>", True, ""),
        ("<@bot> remind me of @user", False, "remind me of @user"),
        ("<@bot> remind me of <@bot>", False, "remind me of <@bot>"),
        ("<@bot>   remind me of <@bot>  ", True, "remind me of "),
    ),
)
def test_remove_bot_user_id_reference(mock_bot, test_message, all_occurrences, expected_result):
    mock_bot.slack_user_id = "bot"

    result = mock_bot._remove_bot_user_id_reference(test_message, all_occurrences)

    assert result == expected_result


def test_remember_creates_new_person_if_they_dont_exist(client, session, mock_bot, mocker):
    mock_slack_user_id = mixer.faker.pystr(10)
    mock_name = mixer.faker.name()

    assert Person.query.filter(Person.slack_user_id == mock_slack_user_id).one_or_none() is None

    mocker.patch(f"{__name__}.add_quote_to_person")
    mocker.patch.object(mock_bot, "fetch_user_info", return_value={"name": mock_name})

    mock_bot.remember(mock_slack_user_id, "Test")

    new_person = Person.query.filter(Person.slack_user_id == mock_slack_user_id).one_or_none()

    assert new_person.first_name == mock_name.split()[0]


def test_remember_adds_quote_to_existing_person(client, session, mock_bot):
    mock_slack_user_id = mixer.faker.pystr(10)
    mock_first_name = mixer.faker.first_name()
    mock_last_name = mixer.faker.last_name()
    mock_quote = mixer.faker.sentence()

    session.add(
        Person(
            slack_user_id=mock_slack_user_id, first_name=mock_first_name, last_name=mock_last_name
        )
    )
    session.commit()

    new_person = Person.query.filter(Person.slack_user_id == mock_slack_user_id).one_or_none()

    assert len(new_person.quotes) == 0

    mock_bot.remember(mock_slack_user_id, mock_quote)

    # Check that remember did not create a duplicate Person
    assert Person.query.count() == 1

    assert len(new_person.quotes) == 1

    assert new_person.quotes[0].content == mock_quote


def test_remind_gets_a_random_quote_for_person(client, session, mock_bot):
    mock_nostalgia_person = mixer.blend(Person)
    mock_target_person = mixer.blend(Person)
    mock_quote = mixer.blend(Quote, person=mock_nostalgia_person)
    expected_message = (
        f"<@{mock_target_person.slack_user_id}> Do you remember this?"
        f'\n\n"{mock_quote.content}" - {mock_nostalgia_person.first_name}'
    )

    session.bulk_save_objects([mock_nostalgia_person, mock_target_person, mock_quote])
    session.commit()

    result = mock_bot.remind(
        mock_nostalgia_person.slack_user_id, [mock_target_person.slack_user_id]
    )

    assert expected_message == result.message


def test_remind_pings_multiple_targes(client, session, mock_bot):
    mock_nostalgia_person = mixer.blend(Person)
    mock_target_persons = mixer.cycle(3).blend(Person)
    mock_quote = mixer.blend(Quote, person=mock_nostalgia_person)
    target_user_ids = [target.slack_user_id for target in mock_target_persons]
    expected_message = (
        f"{' '.join(f'<@{user_id}>' for user_id in target_user_ids)} Do you remember this?"
        f'\n\n"{mock_quote.content}" - {mock_nostalgia_person.first_name}'
    )

    session.bulk_save_objects([mock_nostalgia_person, *mock_target_persons, mock_quote])
    session.commit()

    result = mock_bot.remind(mock_nostalgia_person.slack_user_id, target_user_ids)

    assert expected_message == result.message


def test_remind_does_not_remember_person_that_doesnt_exist(mocker, client, session, mock_bot):
    # this first user does not get added to the database,
    # but is a user in slack that the database doesn't know about
    mock_nostalgia_person = mixer.blend(Person)
    mock_target_person = mixer.blend(Person)
    expected_message = f"I don't remember {mock_nostalgia_person.first_name}."

    session.add(mock_target_person)
    session.commit()

    # mock the return of user info lookup for the response message
    mocker.patch.object(
        mock_bot, "fetch_user_info", return_value={"real_name": mock_nostalgia_person.first_name}
    )

    result = mock_bot.remind(
        mock_nostalgia_person.slack_user_id, [mock_target_person.slack_user_id]
    )

    assert expected_message == result.message


def test_remind_does_not_remember_person_that_doesnt_have_quotes(mocker, client, session, mock_bot):
    mock_nostalgia_person = mixer.blend(Person)
    mock_target_person = mixer.blend(Person)
    expected_message = f"I don't remember {mock_nostalgia_person.first_name}."

    session.bulk_save_objects([mock_target_person, mock_nostalgia_person])
    session.commit()

    # mock the return of user info lookup for the response message
    mocker.patch.object(
        mock_bot, "fetch_user_info", return_value={"real_name": mock_nostalgia_person.first_name}
    )

    result = mock_bot.remind(
        mock_nostalgia_person.slack_user_id, [mock_target_person.slack_user_id]
    )

    assert expected_message == result.message


def test_is_remember_action_returns_true_on_valid_command(client, session, mock_bot):
    assert mock_bot.is_remember_action(
        'remember that <@U1> said "This is a valid remember command!"'
    )
    assert mock_bot.is_remember_action(
        'REMEMBER THAT <@U1> said "This is a valid remember command!"'
    )
    assert mock_bot.is_remember_action(
        'remember when <@U1> said "This is a valid remember command!"'
    )
    assert mock_bot.is_remember_action(
        'remember that <@U1> said "This is a valid remember command!"'
    )
    assert mock_bot.is_remember_action(
        'remember that <@U2> said "This is a valid remember command, <@U3>!"'
    )

    # Technically, anything is allowed between "remember" and the target user.
    # Might not be allowed in the future?
    assert mock_bot.is_remember_action(
        'remember that that guy <@U1> said "This is a valid remember command!"'
    )


def test_is_remember_action_returns_false_when_there_are_too_many_target_users(
    client, session, mock_bot
):
    assert not mock_bot.is_remember_action(
        'remember that <@U1> <@U2> said "This is not a valid command, <@0>!"'
    )


def test_is_remember_action_returns_false_when_single_quotes_are_used(client, session, mock_bot):
    assert not mock_bot.is_remember_action(
        "remember that <@U11111111> said 'I am using single quotes.'"
    )


def test_is_remember_action_returns_false_if_there_are_no_target_users(client, session, mock_bot):
    assert not mock_bot.is_remember_action(
        'remember that said "This is not a valid command, <@0>!"'
    )
    assert not mock_bot.is_remember_action(
        'remember that <U1> said "This is not a valid command, <@0>!"'
    )


def test_is_remind_action_returns_false_if_remind_not_in_command(client, session, mock_bot):
    assert not (mock_bot.is_remind_action("me of <U1>"))
    assert not (mock_bot.is_remind_action("rmind me of <U1>"))


def test_is_remind_action_returns_false_if_not_me_or_targets(client, session, mock_bot):
    assert not (mock_bot.is_remind_action("remind you of <U1>"))


def test_is_remind_action_returns_false_if_not_nostalgia_target(client, session, mock_bot):
    assert not (mock_bot.is_remind_action("remind me of me"))


def test_is_remind_action_returns_false_if_many_nostalgia_targets(client, session, mock_bot):
    assert not (mock_bot.is_remind_action("remind me of <U1> <U2>"))


def test_is_remind_action_returns_true_for_me_or_targets(client, session, mock_bot):
    assert not (mock_bot.is_remind_action("remind me of <U1>"))

    assert not (mock_bot.is_remind_action("remind <U1> of <U1>"))

    assert not (mock_bot.is_remind_action("remind <U1> <U2> of <U3>"))

    assert not (mock_bot.is_remind_action("remind <U1> me <U2> of <U3>"))
