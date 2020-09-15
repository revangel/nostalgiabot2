import re


def get_target_slack_user_ids(command: str) -> [str]:
    """
    Parse a command string that targets one or multiple slack users for
    those target slack users' ids.

    e.g.
    "Do something to <@foobar>" -> ["foobar"]
    "Converse <@a> <@b> <@c>!" -> ["a", "b", "c"]

    Args:
        - command: string representing a command intending to perform an
                   action on a target slack user or users.

    Returns:
        List of strings contining the target slack users' slack_user_ids.
    """
    # Matches everything between a <@ and a >
    # noise!@#<@target>123 -> target
    slack_user_id_pattern = "(?<=<@)(.*?)(?=>)"
    return [user_id.group() for user_id in re.finditer(slack_user_id_pattern, command)]
