from typing import Union

from sqlalchemy import func

from nb2 import db
from nb2.models import Person
from nb2.service.dtos import CreateGhostPersonDTO, CreatePersonDTO
from nb2.service.exceptions import EmptyRequiredFieldException


def get_all_people():
    """
    Return a list of all Person objects in the database.

    Returns:
        List of Person objects in the database.
        Empty list if no People in the database.
    """
    return Person.query.all()


def get_person(user_id: str):
    """
    Return Person with slack_user_id or ghost_user_id equal to user_id.

    Args:
        user_id: Either a slack_user_id or a ghost_user_id

    Returns:
        Person object if one exists in the db, otherwise None.
    """
    return get_person_by_slack_user_id(user_id) or get_person_by_ghost_user_id(user_id)


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


def get_random_person() -> str:
    """
    Return random Person's slack_user_id.

    Returns:
        If there are any Persons in the system, return the slack_user_id
        or ghost_user_id of one of them, otherwise return None.
    """
    person = Person.query.order_by(func.random()).first()

    if person is not None:
        return person.slack_user_id or person.ghost_user_id


def create_person(data: Union[CreatePersonDTO, CreateGhostPersonDTO]):
    """
    Add a new Person object to the database.

    Required args:
        data: An AddPersonDTO instance.

    Raises:
        IntegrityError if a Person with slack_user_id already exists.

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

    new_person = Person(
        slack_user_id=slack_user_id,
        ghost_user_id=ghost_user_id,
        first_name=data.first_name,
        last_name=data.last_name,
    )

    db.session.add(new_person)
    db.session.commit()
    db.session.refresh(new_person)

    return new_person
