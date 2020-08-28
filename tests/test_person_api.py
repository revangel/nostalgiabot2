import json

import pytest
from mixer.backend.flask import mixer
from flask import url_for

from nb2.models import Person


@pytest.mark.parametrize('num_people', (0, 2))
def test_get_all_people(num_people, client, session):
    mixer.cycle(num_people).blend(Person)

    response = client.get(url_for('api.get_all_people'))

    response_json = response.json
    assert response.status_code == 200
    assert len(response_json) == num_people


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
