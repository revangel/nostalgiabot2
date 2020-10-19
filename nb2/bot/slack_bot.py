import re
from collections import namedtuple

from slack import WebClient

from nb2.service.dtos import AddQuoteDTO, CreatePersonDTO
from nb2.service.person_service import create_person, get_person_by_slack_user_id
from nb2.service.quote_service import add_quote_to_person
from nb2.service.slack_service import (
    get_quote_content_from_remember_command,
    get_user_ids_from_command,
)


class SlackBot:
    """
    A class representing Nostalgiabot's interface with Slack.
    """

    # Container used by Actions to group returned data
    # Fields:
    #   ok: (bool) True if the Action succeeded. False otherwise.
    #   message: (str) text to send back to the Slack client.
    Result = namedtuple("Result", ["ok", "message"])

    def __init__(self):
        self.web_client = None
        self.slack_user_id = None

    def init_app(self, token):
        self.web_client = WebClient(token=token)

    def _init_bot_slack_user_id(self):
        """
        Initialize bot's slack_user_id by fetching it from Slack. This is performed separately
        outside of init_app() so that a SlackBot instance can be created without the need for
        a live connection with the Slack API (e.g. for testing purposes).
        """
        self.slack_user_id = self.fetch_bot_info().get("user_id")

    def get_bot_slack_user_id(self) -> str:
        """
        Return this SlackBot's slack_user_id if it has one, or initialize it
        if it does not.
        """
        if self.slack_user_id is None:
            self._init_bot_slack_user_id()
        return self.slack_user_id

    def run_action(self, payload: dict, channel: str):
        """
        Parse the user command from the payload from a Slack event response and run the
        most applicable action inferred from the command.

        Args:
            payload: dict payload sent by Slack as a response to an event.
            channel: string denoting the Slack channel where the command was issued.
        """
        command = payload.get("event").get("text")

        if self.is_hello(command):
            self.send_text(self.hello().message, channel)

        if self.is_remember_action(command):
            target_slack_user_ids = [
                id
                for id in get_user_ids_from_command(command)
                if id != self.get_bot_slack_user_id()
            ]

            if len(target_slack_user_ids) != 1:
                # TODO: inappropriate amount of target users
                return

            target_slack_user_id = target_slack_user_ids[0]

            content = get_quote_content_from_remember_command(command)

            result = self.remember(target_slack_user_id, content)

            self.send_text(result.message, channel)

    #############################
    # Actions
    #############################

    def hello(self):
        """
        Say hello!

        Returns:
            "Hello!"
        """
        return self.Result(ok=True, message="Hello!")

    def remember(self, target_slack_user_id: str, quote: str):
        """
        Add quote to a NB's memory of a Person with target_slack_user_id, if they exist.
        If they don't exist, look up their info and create a new Person in memory first.

        Args:
            target_slack_user_id: string representing slack user id for Person to insert
                                  quote into.
            quote: string representing content of Quote to store.

        Returns:
            A Result namedtuple.
        """
        if not get_person_by_slack_user_id(target_slack_user_id):
            user_info = self.fetch_user_info(target_slack_user_id)
            name = user_info.get("name")
            first_name = name.split()[0]

            create_person_dto = CreatePersonDTO(
                slack_user_id=target_slack_user_id, first_name=first_name
            )

            create_person(create_person_dto)

        add_quote_dto = AddQuoteDTO(slack_user_id=target_slack_user_id, content=quote)

        add_quote_to_person(add_quote_dto)

        return self.Result(ok=True, message="Memory stored!")

    #############################
    # Action matching functions
    #############################

    def is_hello(self, command: str) -> bool:
        """
        Return True if the command string is a greeting.

        The valid form for a hello is:
        "<@NB_user_id> <greeting>"

        where <greeting> is a word in valid_greetings.
        """
        valid_greetings = ["hello", "greetings", "salutations", "howdy"]
        content = [token for token in command.split()]

        if len(content) > 2:
            return False

        cleaned_content = [re.sub(r"\W+", "", token).lower() for token in content]

        if cleaned_content[1] in valid_greetings:
            return True

        return False

    def is_remember_action(self, command: str) -> bool:
        """
        Return True if the command string indicates a call to NB's "remember" action.

        A valid "remember" action is a command of the form:
        '<@NB_user_id> remember .* <@target_user_id> said ".*"'

        Notes:
        - <@NB_user_id> is optional; it may not be present if a command is issued
          in a DM with the bot.
        - Only one target user is allowed.
        - Quote content (".*") must be encapsulated in double quotes.
        """
        double_quote_indeces = [i for i in re.finditer('"', command)]

        if len(double_quote_indeces) != 2:
            # No suitable quote form found
            return False

        quote_start_index = double_quote_indeces[0].start()
        action_segment = command[:quote_start_index]

        user_ids_mentioned = get_user_ids_from_command(action_segment)

        target_slack_user_ids = [
            user_id for user_id in user_ids_mentioned if user_id != self.get_bot_slack_user_id()
        ]

        if len(target_slack_user_ids) != 1:
            return False

        return True

    #############################
    # External Slack Methods
    #############################

    def send_text(self, text, channel):
        self.web_client.chat_postMessage(text=text, channel=channel)

    def send_blocks(self, blocks, channel):
        self.web_client.chat_postMessage(blocks=blocks, channel=channel)

    def fetch_bot_info(self) -> dict:
        """
        Return an object containing info about this bot.
        """
        return self.web_client.auth_test()

    def fetch_user_info(self, slack_user_id: str) -> dict:
        """
        Return Slack's representation of a user with id slack_user_id.

        Args:
            slack_user_id: string representing the Person's primary Slack id.

        Returns:
            {} containing Slack user information.
        """
        return self.web_client.users_info(user=slack_user_id).data["user"]
