from nb2 import db
from nb2.models import Person, Quote
from nb2.service.dtos import AddQuoteDTO
from nb2.service.exceptions import (
    EmptyRequiredFieldException,
    PersonDoesNotExistException,
    QuoteAlreadyExistsException,
)


def get_quote_from_person(slack_user_id: str, quote_id: int):
    """
    Get a Quote from a Person.

    Required Args:
        slack_user_id: The unique Slack identifier for a Person.
        quote_id: The primary key of a Quote.

    Returns:
        A single Quote object if it exists, else None.
    """
    return (
        Quote.query.filter(Quote.id == quote_id)
        .join(Person)
        .filter(Person.slack_user_id == slack_user_id)
        .one_or_none()
    )


def add_quote_to_person(data: AddQuoteDTO):
    """
    Add a Quote to a Person's quotes.

    IMPORTANT: This function will not automatically create Person if they
    don't already exist. It is the caller's responsibility to ensure that
    a Person with slack_user_id exists before trying to add a Quote to
    them using this function.

    Required Args:
        data: An AddQuoteDTO instance.

    Returns:
        Newly created Quote on success.

    Raises:
        PersonDoesNotExistException if no Person with slack_user_id exists.
        QuoteAlreadyExistsException if trying to add a Quote containing content
        that already exists in one of Person's Quotes.

    Notes:
        - Timestamp (created) is populated automatically by the db to default
          to datetime.utc now
    """
    empty_fields = data.get_empty_fields()
    if empty_fields:
        raise EmptyRequiredFieldException(
            f"Can't add Quote to Person with these fields empty: {empty_fields}"
        )

    target_person = Person.query.filter_by(slack_user_id=data.slack_user_id).one_or_none()

    if not target_person:
        raise PersonDoesNotExistException
    if target_person.has_said(data.content):
        raise QuoteAlreadyExistsException

    new_quote = Quote()
    new_quote.content = data.content
    new_quote.person_id = target_person.id

    db.session.add(new_quote)
    db.session.commit()
    db.session.refresh(new_quote)

    return new_quote
