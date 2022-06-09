from typing import Tuple, Union

from nb2 import db
from nb2.models import Person, Quote
from nb2.service.dtos import CreateGhostPersonDTO, CreatePersonDTO
from nb2.service.exceptions import EmptyRequiredFieldException
from nb2.service.quote_service import get_all_quotes_from_person


def get_all_people():
    """
    Return a list of all Person objects in the database.

    Returns:
        List of Person objects in the database.
        Empty list if no People in the database.
    """
    return Person.query.all()


def get_person(user_id: str) -> Tuple[Person, bool]:
    """
    Return Person with slack_user_id, ghost_user_id or display_name equal to user_id.

    Args:
        user_id: Either a slack_user_id or a ghost_user_id

    Returns:
        A tuple:
        - First item is the Person object if one exists in the db, otherwise
        None.
        - Second item is a boolean: True if the user is referenced via
        slack_user_id ("active"), and False if it's referenced via
        display name or ghost_user_id, or no Person is found.
    """
    slack_user = get_person_by_slack_user_id(user_id)
    if slack_user:
        return slack_user, True

    return get_person_by_display_name(user_id) or get_person_by_ghost_user_id(user_id), False


def get_person_by_slack_user_id(slack_user_id: str):
    """
    Return Person with slack_user_id if it exists.

    Required Args:
        slack_user_id: String representing the unique Slack identifier for a Person.

    Returns:
        Person object if one exists in the db with slack_user_id
        None if no such person exists.
    """
    return Person.query.filter_by(slack_user_id=slack_user_id).one_or_none()


def get_person_by_display_name(display_name: str):
    """
    Return Person with display_name if it exists.

    Required Args:
        ghost_user_id: String representing the unique ghost name for a Person.

    Returns:
        Person object if one exists in the db with ghost_user_id
        None if no such person exists.
    """
    return Person.query.filter_by(display_name=display_name).one_or_none()


def get_person_by_ghost_user_id(ghost_user_id: str):
    """
    Return Person with ghost_user_id if it exists.

    Required Args:
        ghost_user_id: String representing the unique ghost name for a Person.

    Returns:
        Person object if one exists in the db with ghost_user_id
        None if no such person exists.
    """
    return Person.query.filter_by(ghost_user_id=ghost_user_id).one_or_none()


def get_person_name_by_slack_user_id(slack_user_id: str):
    """
    Return Person's name with slack_user_id if it exists.

    Required Args:
        slack_user_id: string representing the Person's primary Slack id.

    Returns:
        If the Person with slack_user_id exists in the db return
        their first name as a string, otherwise return None.
    """
    person = Person.query.filter_by(slack_user_id=slack_user_id).one_or_none()

    if person is not None:
        return person.first_name


def get_person_by_quote(quote: Quote):
    """
    Return the Person object who said the quote.
    Returns:
        The Person object related to the quote, or None if this Person does not exist.
    """
    return Person.query.get(quote.person_id)


def create_person(data: Union[CreatePersonDTO, CreateGhostPersonDTO]):
    """
    Add a new Person object to the database.

    Required args:
        data: An AddPersonDTO instance.

    Raises:
        IntegrityError if a Person with slack_user_id or ghost_user_id already exists.

    Returns:
        Newly created Person object on success.
    """
    empty_required_fields = data.get_empty_required_fields()
    if empty_required_fields:
        raise EmptyRequiredFieldException(
            f"Can't add Quote to Person with these fields empty: {empty_required_fields}"
        )

    slack_user_id = getattr(data, "slack_user_id", None)
    ghost_user_id = getattr(data, "ghost_user_id", None)
    # ghosts don't have a display_name, so we use their ghost_user_id
    display_name = getattr(data, "display_name", ghost_user_id)

    new_person = Person(
        slack_user_id=slack_user_id,
        ghost_user_id=ghost_user_id,
        first_name=data.first_name,
        last_name=data.last_name,
        display_name=display_name,
    )

    db.session.add(new_person)
    db.session.commit()
    db.session.refresh(new_person)

    return new_person


def update_person(person: Person, **kwargs):
    """
    Update an existing Person object's display_name.

    Required args:
        display_name: The new display_name.

    Returns:
        The same Person object with a new display_name.
    """
    person.first_name = kwargs.get("first_name") or person.first_name
    person.last_name = kwargs.get("last_name") or person.last_name
    person.display_name = kwargs.get("display_name") or person.display_name
    person.slack_user_id = kwargs.get("slack_user_id") or person.slack_user_id
    person.ghost_user_id = kwargs.get("ghost_user_id") or person.ghost_user_id

    db.session.commit()
    db.session.refresh(person)

    return person


def remove_user(person: Person):
    """
    Remove a Person and their quotes from the db.

    Required args:
        person: A Person.
    """
    for quote in get_all_quotes_from_person(person):
        db.session.delete(quote)

    db.session.delete(person)
    db.session.commit()
