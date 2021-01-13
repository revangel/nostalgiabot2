import re
from collections import namedtuple
from typing import List

from slack import WebClient

from nb2.service.dtos import AddQuoteDTO, CreatePersonDTO
from nb2.service.exceptions import QuoteAlreadyExistsException
from nb2.service.person_service import (
    create_person,
    get_person_by_slack_user_id,
    get_person_name_by_slack_user_id,
    get_random_person,
)
from nb2.service.quote_service import add_quote_to_person, get_random_quotes_from_person
from nb2.service.slack_service import (
    get_quote_content_from_remember_command,
    get_user_ids_from_command,
    mention_users,
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

    def _remove_bot_user_id_reference(self, message: str, all_occurrences=False) -> str:
        """
        Return the result of removing the bot user id from the first token in
        the message. If all is True, remove all references of the bot user id.
        """
        target_token = self.get_bot_slack_user_id()
        regex_pattern = f"<@{target_token}>\\s*"
        count = 0 if all_occurrences else 1

        result = re.sub(regex_pattern, "", message, count=count)

        return result

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
        sender = payload.get("event").get("user")
        command = payload.get("event").get("text")
        command = self._remove_bot_user_id_reference(command, all_occurrences=True)
        slack_user_id_mentions = [id for id in get_user_ids_from_command(command)]

        if self.is_hello(command):
            self.send_text(self.hello().message, channel)

        if self.is_help(command):
            self.send_blocks(self.help().message, channel)

        if self.is_remember_action(command):
            if len(slack_user_id_mentions) != 1:
                # TODO: inappropriate amount of target users
                return

            target_slack_user_id = slack_user_id_mentions[0]

            content = get_quote_content_from_remember_command(command)

            result = self.remember(target_slack_user_id, content)

            return self.send_text(result.message, channel)

        if self.is_quote_action(command):
            nostalgia_user_target = slack_user_id_mentions[0]
            result = self.quote(nostalgia_user_target)

            return self.send_text(result.message, channel)

        if self.is_remind_action(command):
            nostalgia_user_target = slack_user_id_mentions[-1]
            slack_user_targets = slack_user_id_mentions[:-1] or [sender]

            result = self.remind(nostalgia_user_target, slack_user_targets)

            return self.send_text(result.message, channel)

        if self.is_random_action(command):
            result = self.random()

            return self.send_text(result.message, channel)

        if self.is_converse_action(command):
            result = self.converse(slack_user_id_mentions)
            return self.send_text(result.message, channel)

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

    def help(self):
        """
        Provide help with the bot's available commands.

        Returns:
            A string with all of the available commands.
        """
        msg = (
            "The following commands are available for nostalgiabot2:\n\n"
            ">`nb2 help` Provides a list of available commands.\n"
            ">`nb2 hello` Sends a greeting.\n"
            ">`nb2 converse <person1>, <person2> [, <person3>...]` Starts a nonsensical convo.\n"
            ">`nb2 quote <person>` Digs up a memorable quote from the past.\n"
            ">`nb2 random quote` Digs up a random memory from a random person.\n"
            '>`nb2 remember (that|when) <person> said "<quote>"` Stores a new quote, to forever '
            "remain in the planes of Nostalgia.\n"
            ">`nb2 remind (me|<person>) of <person>` Digs up a memorable quote from the past, and "
            "remind the person."
        )

        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": msg}}]

        return self.Result(ok=True, message=blocks)

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

        try:
            add_quote_to_person(add_quote_dto)
        except QuoteAlreadyExistsException:
            return self.Result(ok=True, message="This quote already exists.")

        return self.Result(ok=True, message="Memory stored!")

    def _random_quote(self, nostalgia_user_target):
        """
        Fetch a random quote from NB's memory of a Person with nostalgia_user_target, if they exist.

        Args:
            nostalgia_user_target: string representing slack user id for Person
                                   to retrieve quote.

        Returns:
            A tuple with a person's name and a Quote (or None if no quotes were found)
        """
        person = get_person_name_by_slack_user_id(nostalgia_user_target)
        user_info = self.fetch_user_info(nostalgia_user_target)
        real_name = user_info.get("real_name")

        if person is None:
            return real_name, None

        quote = get_random_quotes_from_person(nostalgia_user_target)

        if not quote:
            return real_name, None

        return person, quote[0]

    def quote(self, nostalgia_user_target: str):
        """
        Recall a quote from NB's memory of a Person with nostalgia_user_target, if they exist.

        Args:
            nostalgia_user_target: string representing slack user id for Person
                                   to retrieve quote

        Returns:
            A Result namedtuple.
        """
        real_name, quote = self._random_quote(nostalgia_user_target)

        if quote is None:
            return self.Result(ok=True, message=f"I don't remember {real_name}.")

        return self.Result(ok=True, message=quote.content)

    def remind(self, nostalgia_user_target: str, slack_user_targets: List[str]):
        """
        Recall a quote from NB's memory of a Person with target_slack_user_id, if they exist,
        and ping the slack_user_targets to remind them of that Person.

        Args:
            slack_user_targets: list of strings representing slack user ids to remind
            nostalgia_user_target: string representing slack user id for Person
                                   to retrieve quote

        Returns:
            A Result namedtuple.
        """
        real_name, quote = self._random_quote(nostalgia_user_target)

        if quote is None:
            return self.Result(ok=True, message=f"I don't remember {real_name}.")

        message = (
            f"{mention_users(slack_user_targets)} Do you remember this?\n\n"
            f'"{quote.content}" - {real_name}'
        )
        return self.Result(ok=True, message=message)

    def random(self):
        """
        Recall a random quote from NB's memory.
        Returns:
            A Result namedtuple.
        """
        person = get_random_person()

        if person is None:
            return self.Result(ok=True, message="No memories to remember")

        real_name, quote = self._random_quote(person)

        if quote is None:
            return self.Result(ok=True, message="No memories to remember")

        message = f'"{quote.content}" - {real_name}'
        return self.Result(ok=True, message=message)

    def converse(self, nostalgia_user_targets: List[str]):
        """
        Output a series of random quotes from nostalgia_user_targets to represent a "conversation"

        Args:
            nostalgia_user_targets: list of strings representing slack user ids to
                                    retrieve quotes from

        Notes:
        - There must be at least two target users in nostalgia_user_targets
        - The above is already verified by is_converse_action, however.
        """
        QUOTES_PER_PERSON = 2

        quotes_by_slack_user_id = {
            person: get_random_quotes_from_person(person, QUOTES_PER_PERSON)
            for person in nostalgia_user_targets
        }
        names_by_slack_user_id = {
            slack_user_id: get_person_name_by_slack_user_id(slack_user_id)
            for slack_user_id in nostalgia_user_targets
        }

        slack_user_ids_with_no_quotes = [
            slack_user_id
            for slack_user_id in quotes_by_slack_user_id
            if not quotes_by_slack_user_id.get(slack_user_id)
        ]

        if any(slack_user_ids_with_no_quotes):
            missing_people = ", ".join(slack_user_ids_with_no_quotes)
            message = f"I don't recognize {missing_people}"
            return self.Result(ok=False, message=message)

        message = ""

        for i in range(QUOTES_PER_PERSON):
            for slack_user_id in quotes_by_slack_user_id:
                name = names_by_slack_user_id[slack_user_id]
                num_quotes_for_person = len(quotes_by_slack_user_id[slack_user_id])
                # Since not every person may have the same amount of quotes, if they run out
                # during the iteration, then just loop back and reuse quotes in order
                quote = quotes_by_slack_user_id[slack_user_id][i % num_quotes_for_person].content
                message += f"{name}: {quote}\n"

        return self.Result(ok=True, message=message)

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

        return command in valid_greetings

    def is_help(self, command: str) -> bool:
        """
        Return True if the command string is a help request.

        The valid form for a help request is:
        "<@NB_user_id> help"
        """
        return command.strip() == "help"

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
        if not command.lower().startswith("remember"):
            return False

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

    def is_quote_action(self, command: str) -> bool:
        """
        Return True if the command string indicates a call to NB's "quote" action.

        A valid "quote" action is a command of the form:
        'quote <@NB_user_id>'

        Notes:
        - Only one target user is allowed.
        """
        if not command.startswith("quote"):
            return False

        user_ids_mentioned = get_user_ids_from_command(command)

        target_slack_user_ids = [
            user_id for user_id in user_ids_mentioned if user_id != self.get_bot_slack_user_id()
        ]

        return len(target_slack_user_ids) > 0

    def is_remind_action(self, command: str) -> bool:
        """
        Return True if the command string indicates a call to NB's "remind" action.

        A valid "remind" action is a command of the form:
        '<@NB_user_id> remind (me | <@user_id_to_remind>+ ) of <@user_id_to_remember>'

        Notes:
        - <@NB_user_id> is optional; it may not be present if a command is issued
          in a DM with the bot.
        - Tag the sender in the response if remind is followed by "me", otherwise
          tag  <@user_id_to_remind>
        - Only one <@user_id_to_remember> is allowed.
        """
        regex_pattern = "^remind\\s+(me|(<@.*>)+)\\s+of\\s+<@.*>\\s*$"
        return re.match(regex_pattern, command, re.I) is not None

    def is_random_action(self, command: str) -> bool:
        """
        Return True if the command string indicates a call to NB's "random" quote action.

        A valid "random" action is a command of the form:
        'random quote'

        Notes:
        - Only one target user is allowed.
        """
        regex_pattern = "^random\\s+quote$"
        return re.match(regex_pattern, command, re.I) is not None

    def is_converse_action(self, command: str) -> bool:
        """
        Return True if the command string indicates a call to NB's "converse" action.

        A valid "converse" action is a command of the form:
        '<@NB_user_id> converse <@target_user_id>, *"'

        Notes:
        - There must be at least two <@target_user_id>s
        """
        regex_pattern = "^converse\\s+(<@.*>*){2,}\\s*"
        return re.match(regex_pattern, command, re.I) is not None

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
