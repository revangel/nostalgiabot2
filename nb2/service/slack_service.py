import re
from typing import Union


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


def trim_mention(slack_user_id: Union[str, list]) -> str:
    """
    Remove the tokens from a slack_user_id that are required for pinging, leaving
    just the raw slack_user_id. Also supports removing mentions from a list of
    slack_user_ids.

    e.g.
    "<@u1>" -> "u1"
    ["<@u1>"] -> ["u1"]

    Args:
        - slack_user_id: a string or list of strings that may or may not be wrapped in a mention.

    Returns:
        A string that represents the raw slack_user_id.
    """
    if isinstance(slack_user_id, list):
        return [user_id.strip("<@>") for user_id in slack_user_id]

    return slack_user_id.strip("<@>")


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
