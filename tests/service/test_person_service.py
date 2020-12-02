import pytest
from mixer.backend.flask import mixer

from nb2.models import Person
from nb2.service.dtos import CreatePersonDTO
from nb2.service.exceptions import EmptyRequiredFieldException
from nb2.service.person_service import (
    create_person,
    get_all_people,
    get_person_by_slack_user_id,
    get_random_person,
)


@pytest.mark.parametrize("num_people", (2, 10))
def test_get_all_people_returns_all_people(client, session, num_people):
    mixer.cycle(num_people).blend(Person)

    assert len(get_all_people()) == num_people


def test_get_person_by_slack_user_id(client, session):
    person = mixer.blend(Person)
    retrieved_person = get_person_by_slack_user_id(person.slack_user_id)

    assert person.id == retrieved_person.id


def test_get_random_person(client, session):
    people = mixer.cycle().blend(Person)
    slack_user_ids = [person.slack_user_id for person in people]
    different_user_returned = False

    random_person = get_random_person()

    assert random_person in slack_user_ids

    # Note because this part of the test tests randomness it could be flaky,
    # but the probability of returning the same user 6 times is quite low.
    for _ in range(5):
        new_random_person = get_random_person()
        if new_random_person != random_person:
            different_user_returned = True
            break

    assert different_user_returned


def test_create_person(client, session):
    slack_user_id = "Foo123"
    first_name = "Leta"
    last_name = "Moneypoli"
    data = CreatePersonDTO(slack_user_id, first_name, last_name)
    create_person(data)

    assert len(Person.query.all()) == 1

    created_person = Person.query.get(1)

    for attr, val in vars(data).items():
        assert getattr(created_person, attr) == val


def test_create_person_raises_exception_when_required_fields_are_empty(client, session):
    data = CreatePersonDTO(None, None, None)

    with pytest.raises(EmptyRequiredFieldException):
        create_person(data)
