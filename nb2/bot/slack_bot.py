import re
from collections import namedtuple
from typing import Union

from slack import WebClient
from slack_sdk.errors import SlackApiError

from nb2.models import Person, Quote
from nb2.service.dtos import AddQuoteDTO, CreateGhostPersonDTO, CreatePersonDTO
from nb2.service.exceptions import QuoteAlreadyExistsException
from nb2.service.person_service import create_person, get_person, get_random_person
from nb2.service.quote_service import add_quote_to_person, get_random_quotes_from_person
from nb2.service.slack_service import mention_users, trim_mention


class SlackBot:
    """
    A class representing Nostalgiabot's interface with Slack.
    """

    # Container used by Actions to group returned data
    # Fields:
    #   ok: (bool) True if the Action succeeded. False otherwise.
    #   message: (str) text to send back to the Slack client.
    Result = namedtuple("Result", ["ok", "message"])

    # remember (that|when) <ghost_user_id|slack_user_id> said "some quote"
    REMEMBER_REGEX = (
        '^remember\\s+((that\\s+)|(when\\s+))?(?P<user_id>\\w+|<@\\w+>)\\s+said\\s+"(?P<quote>.*)"$'
    )

    # remind (me | <@user_id_to_remind>+ ) of <ghost_user_id_to_quote|slack_user_id_to_quote>
    REMIND_REGEX = (
        "^remind\\s+(?P<slack_user_targets>me|(<@\\w+>\\s*)+)\\s+"
        "of\\s+(?P<nostalgia_user_target>\\w+|<@\\w+>)$"
    )

    # quote <ghost_user_id_to_quote|slack_user_id_to_quote>
    QUOTE_REGEX = "^quote\\s+(?P<nostalgia_user_target>\\w+|<@\\w+>)$"
    # random
    RANDOM_REGEX = "^random\\s+quote$"

    # converse <ghost_user_id_to_quote|slack_user_id_to_quote>{2,}
    CONVERSE_REGEX = (
        "^converse\\s+(?P<nostalgia_user_targets>(\\w+|<@\\w+>)(,\\s*(\\w+|<@\\w+>))+)$"
    )

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

    @property
    def unknown_error(self) -> Result:
        """
        Generic error message when unknown issue arises.
        """
        return self.Result(ok=False, message="I wasn't able to make sense of this message.")

    def run_action(self, payload: dict, channel: str) -> None:
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
        command = command.strip()

        if self.is_hello(command):
            result = self.hello()
            self.send_text(result.message, channel)

        if self.is_help(command):
            result = self.help()
            self.send_blocks(result.message, channel)

        if self.is_remember_action(command):
            result = self.remember(command)
            return self.send_text(result.message, channel)

        if self.is_quote_action(command):
            result = self.quote(command)
            return self.send_text(result.message, channel)

        if self.is_remind_action(command):
            result = self.remind(command, sender)
            return self.send_text(result.message, channel)

        if self.is_random_action(command):
            result = self.random()
            return self.send_text(result.message, channel)

        if self.is_converse_action(command):
            result = self.converse(command)
            return self.send_text(result.message, channel)

        return self.send_text(self.unknown_error, channel)

    #############################
    # Actions
    #############################

    def hello(self) -> Result:
        """
        Say hello!

        Returns:
            "Hello!"
        """
        return self.Result(ok=True, message="Hello!")

    def help(self) -> Result:
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
            ">`nb2 remind (me|<person>+) of <person>` Digs up a memorable quote from the past, and "
            "remind the person."
        )

        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": msg}}]

        return self.Result(ok=True, message=blocks)

    def remember(self, message: str) -> Result:
        """
        Add quote to a NB's memory of a Person, if they exist.
        If they don't exist, look up their info and create a new Person in memory first.

        Args:
            message: A message that was sent to the bot.

        Returns:
            A Result namedtuple.
        """
        matched = re.match(self.REMEMBER_REGEX, message, re.I)

        if not matched:
            return self.unknown_error

        target_user_id = trim_mention(matched.group("user_id"))
        quote = matched.group("quote")
        person = get_person(target_user_id)

        # The Person doesn't exist, so create a new Person from information fetched
        # from Slack. If the user id could not be found in Slack, create a ghost Person.
        if person is None:
            try:
                user_info = self.fetch_user_info(target_user_id)
                real_name = user_info.get("real_name")
                first_name, last_name = real_name.split()
                display_name = user_info.get("name")
                create_person_dto = CreatePersonDTO(
                    slack_user_id=target_user_id, first_name=first_name, ghost_user_id=display_name
                )
            except SlackApiError:
                create_person_dto = CreateGhostPersonDTO(
                    # TODO: Need a better way to manage first_name in this case
                    ghost_user_id=target_user_id,
                    first_name=target_user_id,
                )

            person = create_person(create_person_dto)

        add_quote_dto = AddQuoteDTO(person=person, content=quote)

        try:
            add_quote_to_person(add_quote_dto)
        except QuoteAlreadyExistsException:
            return self.Result(ok=True, message="This quote already exists.")

        return self.Result(ok=True, message="Memory stored!")

    def _random_quote(self, nostalgia_user_target: str) -> (Union[Person, str], Quote):
        """
        Fetch a random quote from NB's memory of a Person with nostalgia_user_target, if they exist.

        Args:
            nostalgia_user_target: string representing slack_user_id or ghost_user_id
                                   for Person to retrieve quote.

        Returns:
            A tuple. If the Person doesn't exist, the tuple will be a string with a string
            identifier and None. Otherwise, the tuple will contain a Person and a Quote.
        """
        person = get_person(nostalgia_user_target)

        # The Person doesn't exist in the database, so return their first name,
        # or the provided nostalgia_user_target with None as the Quote.
        if person is None:
            try:
                user_info = self.fetch_user_info(nostalgia_user_target)
                real_name = user_info.get("real_name").split()[0]
                return real_name, None
            except SlackApiError:
                return nostalgia_user_target, None

        quote = get_random_quotes_from_person(person)

        # The Person doesn't have any quotes saves so return their first name,
        # with None as the Quote.
        if not quote:
            return person.first_name, None

        # Success!
        return person, quote[0]

    def quote(self, message: str) -> Result:
        """
        Recall a quote from NB's memory of a Person, if they exist.

        Args:
            message: A message that was sent to the bot.

        Returns:
            A Result namedtuple.
        """
        matched = re.match(self.QUOTE_REGEX, message, re.I)

        if not matched:
            return self.unknown_error

        nostalgia_user_target = trim_mention(matched.group("nostalgia_user_target"))

        person, quote = self._random_quote(nostalgia_user_target)

        if quote is None:
            return self.Result(ok=True, message=f"I don't remember {person}.")

        return self.Result(ok=True, message=quote.content)

    def remind(self, message: str, sender: str) -> Result:
        """
        Recall a quote from NB's memory of a Person, if they exist,
        and ping users to remind them of that Person.

        Args:
            message: A message that was sent to the bot.
            sender: A slack_user_id of a Person that sent the message.

        Returns:
            A Result namedtuple.
        """
        matched = re.match(self.REMIND_REGEX, message, re.I)

        if not matched:
            return self.unknown_error

        slack_user_targets = trim_mention(matched.group("slack_user_targets").split())
        nostalgia_user_target = trim_mention(matched.group("nostalgia_user_target"))

        person, quote = self._random_quote(nostalgia_user_target)

        if quote is None:
            return self.Result(ok=True, message=f"I don't remember {person}.")

        # Replace "me" with the sender slack_user_id so that the sender can be pinged
        slack_user_targets = [sender if target == "me" else target for target in slack_user_targets]

        message = (
            f"{mention_users(slack_user_targets)} Do you remember this?\n\n"
            f'"{quote.content}" - {person.first_name}'
        )
        return self.Result(ok=True, message=message)

    def random(self) -> Result:
        """
        Recall a random quote from NB's memory.

        Returns:
            A Result namedtuple.
        """
        person = get_random_person()

        if person is None:
            return self.Result(ok=True, message="No memories to remember")

        person, quote = self._random_quote(person)

        # TODO: Maybe try to fetch another person or prevent getting Persons with no Quotes?
        if quote is None:
            return self.Result(ok=True, message="No memories to remember")

        message = f'"{quote.content}" - {person.first_name}'
        return self.Result(ok=True, message=message)

    def converse(self, message: str) -> Result:
        """
        Output a series of random quotes from nostalgia_user_targets to represent a "conversation".

        Args:
            message: A message that was sent to the bot.

        Notes:
        - There must be at least two target users in nostalgia_user_targets
        - The above is already verified by is_converse_action, however.
        """
        QUOTES_PER_PERSON = 2
        matched = re.match(self.CONVERSE_REGEX, message, re.I)

        if not matched:
            return self.unknown_error

        nostalgia_user_targets = trim_mention(
            re.split(",\\s+", matched.group("nostalgia_user_targets"))
        )
        persons = [get_person(target) for target in nostalgia_user_targets]

        unknown_persons = [
            nostalgia_user_targets[i] for i, person in enumerate(persons) if person is None
        ]

        if unknown_persons:
            return self.Result(ok=False, message=f"I don't recognize {', '.join(unknown_persons)}")

        quotes_by_slack_user_id = {
            person.slack_user_id
            or person.ghost_user_id: get_random_quotes_from_person(person, QUOTES_PER_PERSON)
            for person in persons
        }

        names_by_slack_user_id = {
            person.slack_user_id or person.ghost_user_id: person.first_name for person in persons
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
        return command == "help"

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
        return re.match(self.REMEMBER_REGEX, command, re.I) is not None

    def is_quote_action(self, command: str) -> bool:
        """
        Return True if the command string indicates a call to NB's "quote" action.

        A valid "quote" action is a command of the form:
        'quote <@NB_user_id>'

        Notes:
        - Only one target user is allowed.
        """
        return re.match(self.QUOTE_REGEX, command, re.I) is not None

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
        return re.match(self.REMIND_REGEX, command, re.I) is not None

    def is_random_action(self, command: str) -> bool:
        """
        Return True if the command string indicates a call to NB's "random" quote action.

        A valid "random" action is a command of the form:
        'random quote'

        Notes:
        - Only one target user is allowed.
        """
        return re.match(self.RANDOM_REGEX, command, re.I) is not None

    def is_converse_action(self, command: str) -> bool:
        """
        Return True if the command string indicates a call to NB's "converse" action.

        A valid "converse" action is a command of the form:
        '<@NB_user_id> converse <@target_user_id>, *"'

        Notes:
        - There must be at least two <@target_user_id>s
        """
        return re.match(self.CONVERSE_REGEX, command, re.I) is not None

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
        return self.web_client.users_info(user=slack_user_id).validate().data["user"]
