from nb2 import db
from nb2.models import Person
from nb2.service.dtos import CreatePersonDTO
from nb2.service.exceptions import EmptyRequiredFieldException


def get_all_people():
    """
    Return a list of all Person objects in the database.

    Returns:
        List of Person objects in the database.
        Empty list if no People in the database.
    """
    return Person.query.all()


def get_person_by_slack_user_id(slack_user_id: str):
    """
    Return Person with slack_user_id if it exists.

    Required Args:
        slack_user_id: string representing the Person's primary Slack id.

    Returns:
        Person object if one exists in the db with slack_user_id
        None if no such person exists.
    """
    return Person.query.filter_by(slack_user_id=slack_user_id).one_or_none()


def create_person(data: CreatePersonDTO):
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

    new_person = Person(
        slack_user_id=data.slack_user_id,
        first_name=data.first_name,
        last_name=data.last_name
    )

    db.session.add(new_person)
    db.session.commit()
    db.session.refresh(new_person)

    return new_person
