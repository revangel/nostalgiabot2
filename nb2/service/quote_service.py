from typing import List

from sqlalchemy.sql.expression import func

from nb2 import db
from nb2.models import Person, Quote
from nb2.service.dtos import AddQuoteDTO
from nb2.service.exceptions import EmptyRequiredFieldException, QuoteAlreadyExistsException


def get_quote_from_person(person: Person, quote_id: int):
    """
    Get a Quote from a Person.

    Required Args:
        person: A Person.
        quote_id: The primary key of a Quote.

    Returns:
        A single Quote object if it exists, else None.
    """
    return (
        Quote.query.filter(Quote.id == quote_id)
        .join(Person)
        .filter(Person.id == person.id)
        .one_or_none()
    )


def has_quotes() -> bool:
    """
    Check if there are any quotes in the table.

    Returns:
        A bool representing if there are any quotes.
    """
    return bool(Quote.query.first())


def get_random_quote_from_any_person() -> Quote:
    """
    Get a random Quote from any Person.

    Returns:
        A random Quote object if it exists, else None.
    """
    return Quote.query.order_by(func.random()).first()


def get_random_quotes_from_person(person: Person, num_quotes: int = 1) -> List[Quote]:
    """
    Get <num_quotes> random Quote(s) from a Person.

    Required Args:
        person: A Person.
        num_quotes: The maximum number of random quotes to receive (defaults to 1).

    Returns:
        A list of random Quote objects if it exists, else None.

    Notes:
        If num_quotes > the total amount of quotes for slack_user_id, then a list
        of all their quotes will be returned.
    """
    return (
        Quote.query.order_by(func.random())
        .join(Person)
        .filter(Person.id == person.id)
        .limit(num_quotes)
        .all()
    )


def get_all_quotes_from_person(person: Person):
    """
    Get all Quote from a Person.

    Required Args:
        slack_user_id: String representing the unique Slack identifier for a Person.

    Returns:
        A list of Quote objects.
    """
    return Quote.query.join(Person).filter(Person.id == person.id).all()


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
        EmptyRequiredFieldException if there are empty fields in the AddQuoteDTO.
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

    target_person = data.person

    if target_person.has_said(data.content):
        raise QuoteAlreadyExistsException

    new_quote = Quote()
    new_quote.content = data.content
    new_quote.person_id = target_person.id

    db.session.add(new_quote)
    db.session.commit()
    db.session.refresh(new_quote)

    return new_quote


def delete_quote(quote: Quote):
    """
    Remove a Quote from the db.

    Required args:
        quote: A Quote.
    """
    db.session.delete(quote)
    db.session.commit()


def update_quote(quote: Quote, **kwargs):
    """
    Update an existing Quote object's person or content.

    Required args:
        quote: The quote object we wish to update

    Returns:
        The same Quote object with a new content or person.
    """
    new_content = kwargs.get("content", quote.content)
    target_person = kwargs.get("person")

    if not target_person:
        target_person = Person.query.filter(Person.id == quote.person_id).one_or_none()

    # Confirm content isn't already a quote for the person
    if target_person.has_said(new_content):
        raise QuoteAlreadyExistsException

    quote.content = new_content
    quote.person_id = target_person.id

    db.session.commit()
    db.session.refresh(quote)

    return quote


def get_quote(quote_id: int):
    """
    Get a Quote.

    Required Args:
        quote_id: The primary key of a Quote.

    Returns:
        A single Quote object if it exists, else None.
    """
    return Quote.query.filter(Quote.id == quote_id).one_or_none()
