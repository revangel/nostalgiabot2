import json

import pytest
from flask import url_for
from mixer.backend.flask import mixer

from nb2.models import Person, Quote


def get_serialized_person(person, include_quotes=False):
    data = {
        "id": person.id,
        "slack_user_id": person.slack_user_id,
        "first_name": person.first_name,
        "last_name": person.last_name,
        "ghost_user_id": None,
    }

    if include_quotes:
        data.update({"quotes": [quote.content for quote in person.quotes]})

    return data


@pytest.fixture()
def prepared_user(client, session):
    return mixer.blend(Person, slack_user_id=mixer.RANDOM)


@pytest.mark.parametrize("num_people", (0, 2))
def test_get_all_people(num_people, client, session):
    mixer.cycle(num_people).blend(Person, slack_user_id=mixer.RANDOM)

    response = client.get(url_for("api.personlistresource"))

    response_json = response.json
    assert response.status_code == 200
    assert len(response_json) == num_people


@pytest.mark.parametrize("num_quotes", (0, 2))
def test_get_all_people_with_quotes(num_quotes, client, session):
    person1, person2 = mixer.cycle(2).blend(Person, slack_user_id=mixer.RANDOM)
    mixer.cycle(num_quotes).blend(Quote, person=person1)
    mixer.cycle(num_quotes).blend(Quote, person=person2)
    expected_result = [
        get_serialized_person(person, include_quotes=True) for person in (person1, person2)
    ]

    response = client.get(url_for("api.personlistresource", include="quotes"))

    response_json = response.json
    assert response.status_code == 200
    assert response_json == expected_result


def test_get_person(prepared_user, client, session):
    expected_data = get_serialized_person(prepared_user)

    response = client.get(url_for("api.personresource", user_id=prepared_user.slack_user_id))

    response_json = response.json
    assert response.status_code == 200
    assert response_json == expected_data


@pytest.mark.parametrize("num_quotes", (0, 2))
def test_get_person_with_quotes(prepared_user, num_quotes, client, session):
    mixer.cycle(num_quotes).blend(Quote, person=prepared_user)
    expected_result = get_serialized_person(prepared_user, include_quotes=True)

    response = client.get(
        url_for("api.personresource", user_id=prepared_user.slack_user_id, include="quotes")
    )

    response_json = response.json
    assert response.status_code == 200
    assert response_json == expected_result


def test_get_correct_person_by_slack_user_id(prepared_user, client, session):
    other_person = mixer.blend(Person, slack_user_id=mixer.RANDOM)
    expected_data = get_serialized_person(prepared_user)

    assert (
        prepared_user.id != other_person.id
        and prepared_user.slack_user_id != other_person.slack_user_id
    )

    response = client.get(url_for("api.personresource", user_id=prepared_user.slack_user_id))

    response_json = response.json
    assert response.status_code == 200
    assert response_json == expected_data


def test_get_person_raises_404_if_person_does_not_exist(client, session):
    existing_person = mixer.blend(Person, slack_user_id=mixer.RANDOM)
    slack_user_id_lookup = mixer.faker.pystr(16)

    # Make sure slack_user_id_lookup doesn't already exist in db
    while slack_user_id_lookup == existing_person.slack_user_id:
        slack_user_id_lookup = mixer.faker.pystr(16)

    expected_error = f"Person with user_id {slack_user_id_lookup} does not exist"

    response = client.get(url_for("api.personresource", user_id=slack_user_id_lookup))

    response_json = response.json
    assert response.status_code == 404
    assert response_json.get("message") == expected_error


def test_create_person(client, session):
    data = {
        "slack_user_id": "foobar",
        "first_name": "foo",
        "last_name": "bar",
        "ghost_user_id": "foobar",
    }

    response = client.post(
        url_for("api.personlistresource"), data=json.dumps(data), content_type="application/json"
    )

    response_json = response.json
    assert response.status_code == 201
    assert isinstance(response_json.get("id"), int)
    for field, value in data.items():
        assert response_json.get(field) == value


def test_cannot_create_person_with_duplicate_slack_user_id(client, session):
    existing_person = mixer.blend(Person, slack_user_id=mixer.RANDOM)
    data = {
        "slack_user_id": existing_person.slack_user_id,
        "first_name": "foo",
        "last_name": "bar",
        "ghost_user_id": "foobar",
    }
    expected_error = (
        f"Person with id {data['slack_user_id']} or {data['ghost_user_id']} already exists"
    )

    response = client.post(
        url_for("api.personlistresource"), data=json.dumps(data), content_type="application/json"
    )

    response_json = response.json
    assert response.status_code == 409
    assert response_json.get("message") == expected_error


@pytest.mark.parametrize("field", ["ghost_user_id", "first_name"])
def test_cannot_create_person_with_missing_required_fields(field, client, session):
    data = {
        "slack_user_id": "foobar",
        "first_name": "foo",
        "last_name": "bar",
        "ghost_user_id": "foobar",
    }
    expected_error = {field: f"{field} is required"}
    data.pop(field)

    response = client.post(
        url_for("api.personlistresource"), data=json.dumps(data), content_type="application/json"
    )

    response_json = response.json
    assert response.status_code == 400
    assert response_json.get("message") == expected_error
