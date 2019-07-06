import random
import re

from errbot import BotPlugin, botcmd, re_botcmd, ValidationException
from typing import Dict, List, Tuple

class NostalgiaBot(BotPlugin):
    """
    A bot to remind us of what we'd all rather forget we said.

    NostalgiaBot is the Security Compass bot that remembers all
    our funny, and out-of-context quotes!
    """

    #######################
    # Main social functions
    #######################

    @botcmd(split_args_with=None)
    def forget(self, msg, args):
        """
        Forget someone. FOR DEVELOPMENT PURPOSES.
        Syntax:
        "Forget @username"
        """
        self.pop(args[0], None)

    @botcmd(split_args_with=None)
    def converse(self, msg, participants: List[str]):
        """
        Output quotes from persons in NostalgiaBot's memory.

        Regex Syntax:
        [Cc]onverse @(\w+)

        Example:
        Converse @jeff @kelly
        """

        MAX_PARTICIPANTS = 5
        MAX_QUOTES = 5

        # Assume that quotes should not be repeated in a dialog.
        # If the total number of quotes stored for a participant is less than
        # MAX_QUOTES, then limit the conversation to that many quotes.
        min_total_quotes = min([len(self[person]) for person in participants])

        num_quotes = min(MAX_QUOTES, min_total_quotes)

        # List of (person, quote) tuples
        quotes = self.get_person_quote_pairs(
            self.get_random_quotes(participants, num_quotes)
        )

        for quote in quotes:
            yield("{}: {}".format(quote[0], quote[1]))

    @botcmd(split_args_with=None)
    def remember(self, msg, args: List[str]):
        """
        Insert a quote into NostalgiaBot's memory for a person.

        Regex Syntax:
        [Rr]emember (that|when) @([\S]+) said ".*"

        Example:
        Remember when @akram said
        "The only chinese food I've had before is Sushi"
        """

        args = [arg.lower() for arg in args]

        try:
            self.validate_user(args)
        except ValidationException as e:
            return e

        user = args[args.index("said") - 1]
        quote_start_index = args.index("said") + 1
        quote = " ".join(args[quote_start_index:])

        # TODO: Validate quote

        if user not in self:
            self[user] = [quote]
        else:
            # The mutable context manager must be used as a caveat of
            # Errbot's persistence mechanics.
            with self.mutable(user) as quotes:
                quotes.append(quote)

    @botcmd(split_args_with=None)
    def remind(self, msg, args: List[str]):
        """
        Return a random quote from person or persons in NostalgiaBot's memory.

        Regex Syntax:
        [Rr]emind me of @(\w+)

        Example:
        Remind me of @hanif
        Remind me of @ellen @sri
        """

        user_prefix_expression = re.compile("@.*")

        # Need to list() the filter because we iterate through it multiple times
        # to check and then to output.
        users = list(filter(user_prefix_expression.match, args))

        # TODO: Can we check user validity then output more smoothly?
        for user in users:
            if user not in self:
                print("I don't know who {} is!".format(user))
                return

        print("Do you remember this?")

        for user in users:
            quote = random.choice(self[user])
            print("{}: {}".format(user, quote))

    ##################
    # Helper functions
    ##################

    def validate_syntax(self, args: List[str]):
        #TODO: Standardize error handling
        pass

    def validate_user(self, args: List[str]):
        """
        Check that the user is valid on slack by checking if it starts with
        an "@". [Could be improved in the future by doing an
        actual system check]
        """

        if args.index("said") == 0:
            raise ValidationException(
                "You need to provide a username before 'said'."
            )

        user = args[args.index("said") - 1]

        if user[0] != "@":
            raise ValidationException("Username must start with '@'")

    def get_random_quotes(self, people: List[str], n: int):
        """
        Return a dict of lists of n quotes from people randomly sampled from
        NostalgiaBot's memory.

        get_random_quotes(["@leta", "@harry"], 2)
        > {"@leta": [<quote>, <quote>], "@harry": [<quote>, <quote>]}
        """

        #TODO: Validate username, check if in memory

        quotes = {person: [] for person in people}

        for person in people:
            quotes[person] = random.sample(self[person], n)

        return quotes

    def get_person_quote_pairs(self, quotes: Dict):
        """
        Return list of (person, quote) tuples from quotes.

        d = {"@ijeff": [<quote1>, <quote2>], "@pranoy": [<quote3>, <quote4>]}
        get_person_quote_pairs(d)
        >
        [
            ("@ijeff", <quote1>), ("@ijeff", <quote2),
            ("@pranoy", <quote3>), ("@pranoy", <quote4>)
        ]
        """

        quote_pairs = []

        for person in quotes:
            for quote in quotes[person]:
                quote_pairs.append((person, quote))

        return quote_pairs