from nb2.service.slack_service import get_target_slack_user_ids


def test_get_target_slack_user_ids(client, session):
    command_string = "Yada Yada <@foo>, &#<@emin>, @gotcha, and <@U123>!"
    expected = ["foo", "emin", "U123"]
    assert get_target_slack_user_ids(command_string) == expected
