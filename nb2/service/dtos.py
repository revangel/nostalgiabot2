from dataclasses import dataclass


class BaseDTO:
    REQUIRED_FIELDS = []

    def get_empty_fields(self):
        """
        Return a list of field names that have a value of None.
        """
        return [f for f in self.__dict__ if not self.__dict__[f]]

    def get_empty_required_fields(self):
        """
        Return a list of field names that have a value of None
        and are listed in REQUIRED_FIELDS.
        """
        empty_fields = self.get_empty_fields()
        return [f for f in empty_fields if f in self.REQUIRED_FIELDS]


@dataclass
class CreatePersonDTO(BaseDTO):
    """
    Data transfer object for adding a Person to the db.

    Required Fields:
        slack_user_id: string representing the Person's primary Slack id.
        first_name: string representing Person's first name.
    """

    REQUIRED_FIELDS = ["slack_user_id", "first_name"]

    slack_user_id: str
    first_name: str
    last_name: str = None


@dataclass
class AddQuoteDTO(BaseDTO):
    """
    Data transfer object for adding a Quote to a Person.

    Required Fields:
        slack_user_id: string representing the Person's primary Slack id.
        content: string representing a Quote the Person has said.
    """

    slack_user_id: str
    content: str
