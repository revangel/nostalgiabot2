import json

import pytest
from mixer.backend.flask import mixer
from flask import url_for

from nb2.models import Person


def get_serialized_person(person):
    return {
        "id": person.id,
        "slack_user_id": person.slack_user_id,
        "first_name": person.first_name,
        "last_name": person.last_name,
        "quotes": person.quotes
    }


@pytest.mark.parametrize('num_people', (0, 2))
def test_get_all_people(num_people, client, session):
    mixer.cycle(num_people).blend(Person)

    response = client.get(url_for('api.get_all_people'))

    response_json = response.json
    assert response.status_code == 200
    assert len(response_json) == num_people


def test_get_person(client, session):
    expected_person = mixer.blend(Person)
    expected_data = get_serialized_person(expected_person)

    response = client.get(url_for('api.get_person', slack_user_id=expected_person.slack_user_id))

    response_json = response.json
    assert response.status_code == 200
    assert response_json == expected_data


def test_get_correct_person_by_slack_user_id(client, session):
    expected_person = mixer.blend(Person)
    other_person = mixer.blend(Person)
    expected_data = get_serialized_person(expected_person)

    assert expected_person.id != other_person.id and expected_person.slack_user_id != other_person.slack_user_id

    response = client.get(url_for('api.get_person', slack_user_id=expected_person.slack_user_id))

    response_json = response.json
    assert response.status_code == 200
    assert response_json == expected_data


def test_get_person_raises_404_if_person_does_not_exist(client, session):
    existing_person = mixer.blend(Person)
    slack_user_id_lookup = mixer.faker.pystr(16)

    # Make sure slack_user_id_lookup doesn't already exist in db
    while slack_user_id_lookup == existing_person.slack_user_id:
        slack_user_id_lookup = mixer.faker.pystr(16)

    expected_error = f"Person with slack_user_id {slack_user_id_lookup} does not exist"

    response = client.get(url_for('api.get_person', slack_user_id=slack_user_id_lookup))

    response_json = response.json
    assert response.status_code == 404
    assert response_json.get("message") == expected_error


def test_create_person(client, session):
    data = {
        "slack_user_id": "foobar",
        "first_name": "foo",
        "last_name": "bar"
    }

    response = client.post(
        url_for('api.create_person'),
        data=json.dumps(data),
        content_type='application/json'
    )

    response_json = response.json
    assert response.status_code == 201
    assert isinstance(response_json.get("id"), int)
    assert isinstance(response_json.get('quotes'), list)
    for field, value in data.items():
        assert response_json.get(field) == value


def test_cannot_create_person_with_duplicate_slack_user_id(client, session):
    existing_person = mixer.blend(Person)
    data = {
        "slack_user_id": existing_person.slack_user_id,
        "first_name": "foo",
        "last_name": "bar"
    }
    expected_error = f"Person with slack_user_id = '{data['slack_user_id']}' already exists"

    response = client.post(
        url_for('api.create_person'),
        data=json.dumps(data),
        content_type='application/json'
    )

    response_json = response.json
    assert response.status_code == 409
    assert response_json.get("message") == expected_error


@pytest.mark.parametrize('field', Person.required_fields)
def test_cannot_create_person_with_duplicate_slack_user_id(field, client, session):
    data = {
        "slack_user_id": "foobar",
        "first_name": "foo",
        "last_name": "bar"
    }
    expected_error = f"Missing required field(s): {field}"
    data.pop(field)

    response = client.post(
        url_for('api.create_person'),
        data=json.dumps(data),
        content_type='application/json'
    )

    response_json = response.json
    assert response.status_code == 400
    assert response_json.get("message") == expected_error
