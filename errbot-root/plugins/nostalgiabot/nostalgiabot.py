from errbot import BotPlugin, botcmd, re_botcmd, ValidationException


class NostalgiaBot(BotPlugin):
    """
    A bot to remind us of what we'd all rather forget we said.

    NostalgiaBot is the Security Compass bot that remembers all
    our funny, and out-of-context quotes!
    """

    @botcmd(split_args_with=None)
    def forget(self, msg, args):
        """
        Forget someone. FOR DEVELOPMENT PURPOSES.
        Syntax:
        "Forget @username"
        """
        self.pop(args[0], None)

    @botcmd(split_args_with=None)
    def remember(self, msg, args):
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
            # Errbot's persistence mechanics. Refer to:
            # http://errbot.io/en/latest/user_guide/plugin_development/persistence.html#caveats #noqa
            with self.mutable(user) as quotes:
                quotes.append(quote)

    @botcmd(split_args_with=None)
    def remind(self, msg, args):
        """
        Return a random quote from person in NostalgiaBot's memory.

        Regex Syntax:
        [Rr]mind me of @([\S]+)

        Example:
        Remind me of @hanif
        """
        print(self[args[-1]])
        pass

    ###################
    # Helper functions
    ###################

    def validate_syntax(self, args):
        #TODO: Standardize error handling
        pass

    def validate_user(self, args: []):
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