import re


def get_user_ids_from_command(command: str) -> [str]:
    """
    Parse a command string that targets one or multiple slack users for
    those target slack users' ids.

    e.g.
    "Do something to <@foobar>" -> ["foobar"]
    "Converse <@a> <@b> <@c>!" -> ["a", "b", "c"]

    Args:
        - command: string representing a command intending to perform an
                   Action on a target slack user or users.

    Returns:
        List of strings contining the target slack users' slack_user_ids.
    """
    # Matches everything between a <@ and a >
    # noise!@#<@target>123 -> target
    slack_user_id_pattern = "(?<=<@)(.*?)(?=>)"
    return [user_id.group() for user_id in re.finditer(slack_user_id_pattern, command)]


def mention_users(slack_user_ids: [str]) -> [str]:
    """
    Add the required tokens to each slack_user_id so that the corresponding users
    will be pinged in a slack message.

    e.g.
    ["u1", "u2"] -> "<@u1> <@u2>"

    Args:
        - slack_user_ids: list of strings representing slack user ids.

    Returns:
        A string that can be added to a slack message to ping users.
    """

    return " ".join([f"<@{user_id}>" for user_id in slack_user_ids])


def get_quote_content_from_remember_command(command: str) -> str:
    """
    Parse a command string invoking a "remember" Action and return the content for the
    Quote to be stored into memory.

    Notes:
        - A VALID command string for a "remember" Action is of the form:
          'remember that <@user_id> said "<content>"'
        - The content must be enclosed in double quotes.

    Args:
        command: string representing a valid command invoking a "remember" Action.

    Returns:
        String representing the content of the Quote.
    """
    return re.search('(?<=").*(?=")', command).group()
