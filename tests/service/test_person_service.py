import pytest

from mixer.backend.flask import mixer

from nb2.service.dtos import CreatePersonDTO
from nb2.service.exceptions import EmptyRequiredFieldException
from nb2.service.person_service import *


@pytest.mark.parametrize('num_people', (2, 10))
def test_get_all_people_returns_all_people(client, session, num_people):
    mixer.cycle(num_people).blend(Person)

    assert len(get_all_people()) == num_people


def test_get_person_by_slack_user_id(client, session):
    person = mixer.blend(Person)
    retrieved_person = get_person_by_slack_user_id(person.slack_user_id)

    assert person.id == retrieved_person.id


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

