import json
from datetime import datetime

import pytest
from dateutil.parser import parse
from flask import url_for
from flask_restful import fields
from mixer.backend.flask import mixer

from nb2.models import Person, Quote


def get_serialized_quote(quote):
    return {
        "id": quote.id,
        "content": quote.content,
        "person_id": quote.person_id,
        "created": fields.DateTime().format(quote.created),
    }


@pytest.fixture()
def prepared_user(client, session):
    yield mixer.blend(Person, slack_user_id=mixer.RANDOM)


@pytest.fixture()
def prepared_quote(client, session, prepared_user):
    yield mixer.blend(Quote, person=mixer.blend(Person, slack_user_id=mixer.RANDOM))


def test_get_quote_from_person(client, session, prepared_quote):
    expected_data = get_serialized_quote(prepared_quote)

    response = client.get(
        url_for(
            "api.personquoteresource",
            user_id=prepared_quote.person.slack_user_id,
            quote_id=prepared_quote.id,
        )
    )

    response_json = response.json
    assert response.status_code == 200
    assert response_json == expected_data


def test_get_quote_raises_404_if_person_does_not_exist(client, session):
    user_id = "foo"
    expected_error = f"Person with user_id {user_id} does not exist"

    response = client.get(url_for("api.personquoteresource", user_id=user_id, quote_id=1))

    response_json = response.json
    assert response.status_code == 404
    assert response_json.get("message") == expected_error


def test_get_quote_raises_404_if_quote_does_not_exist(client, session, prepared_user):
    quote_id = 1
    expected_error = (
        f"Quote with id {quote_id} does not exist for person "
        f"with user_id {prepared_user.slack_user_id}"
    )

    response = client.get(
        url_for("api.personquoteresource", user_id=prepared_user.slack_user_id, quote_id=quote_id)
    )

    response_json = response.json
    assert response.status_code == 404
    assert response_json.get("message") == expected_error


@pytest.mark.parametrize("num_quotes", [0, 1, 5])
def test_get_all_quotes_from_person(num_quotes, client, session, prepared_user):
    quotes = mixer.cycle(num_quotes).blend(Quote, person=prepared_user)
    expected_data = [get_serialized_quote(quote) for quote in quotes]

    response = client.get(
        url_for(
            "api.personquotelistresource",
            user_id=prepared_user.slack_user_id,
        )
    )

    response_json = response.json
    assert response.status_code == 200
    assert len(response_json) == num_quotes
    assert response_json == expected_data


def test_get_all_quotes_raises_404_if_person_does_not_exist(client, session):
    user_id = "foo"
    expected_error = f"Person with user_id {user_id} does not exist"

    response = client.get(url_for("api.personquotelistresource", user_id=user_id, quote_id=1))

    response_json = response.json
    assert response.status_code == 404
    assert response_json.get("message") == expected_error


def test_create_quote(client, session, prepared_user):
    data = {
        "user_id": prepared_user.slack_user_id,
        "content": "Make Bikram productive",
    }

    response = client.post(
        url_for("api.quotelistresource"), data=json.dumps(data), content_type="application/json"
    )

    response_json = response.json
    created_date = parse(response_json.get("created"))

    assert response.status_code == 201

    assert isinstance(response_json.get("id"), int)
    assert isinstance(response_json.get("content"), str)
    assert isinstance(created_date, datetime)


def test_cannot_create_duplicate_quote(client, session, prepared_user):
    data = {"user_id": prepared_user.slack_user_id, "content": "the more poking the better"}

    response = client.post(
        url_for("api.quotelistresource"), data=json.dumps(data), content_type="application/json"
    )

    # Intentional duplicate call to test validation against
    # duplicate quotes
    response = client.post(
        url_for("api.quotelistresource"), data=json.dumps(data), content_type="application/json"
    )

    assert response.status_code == 409

    expected_error_msg = (
        "The Quote content provided can't be added because it already exists for this Person."
    )
    assert response.json.get("message") == expected_error_msg


def test_delete_quote(client, session, prepared_quote):
    response = client.delete(
        url_for(
            "api.personquoteresource",
            user_id=prepared_quote.person.slack_user_id,
            quote_id=prepared_quote.id,
        )
    )

    assert response.status_code == 204


def test_delete_raises_404_if_quote_does_not_exist(client, prepared_user):
    quote_id = 1
    expected_error = (
        f"Quote with id {quote_id} does not exist for person "
        f"with user_id {prepared_user.slack_user_id}"
    )

    response = client.delete(
        url_for(
            "api.personquoteresource",
            user_id=prepared_user.slack_user_id,
            quote_id=quote_id,
        )
    )

    response_json = response.json
    assert response.status_code == 404
    assert response_json.get("message") == expected_error


def test_delete_raises_404_if_person_does_not_exist(client, session):
    user_id = "foo"
    expected_error = f"Person with user_id {user_id} does not exist"

    response = client.delete(url_for("api.personquoteresource", user_id=user_id, quote_id=1))

    response_json = response.json
    assert response.status_code == 404
    assert response_json.get("message") == expected_error


def test_edit_quote_person(client, session, prepared_quote, prepared_user):
    data = {
        "user_id": prepared_user.slack_user_id,
    }

    response = client.patch(
        url_for("api.quoteresource", quote_id=prepared_quote.id),
        data=json.dumps(data),
        content_type="application/json",
    )

    response_json = response.json
    assert response.status_code == 200
    assert response_json.get("person_id") == prepared_user.id


def test_edit_quote_content(client, session, prepared_quote):
    data = {
        "content": "edited field",
    }

    response = client.patch(
        url_for("api.quoteresource", quote_id=prepared_quote.id),
        data=json.dumps(data),
        content_type="application/json",
    )

    response_json = response.json
    assert response.status_code == 200
    assert response_json.get("content") == data.get("content")


def test_edit_raises_404_if_person_does_not_exist(client, session, prepared_quote):
    user_id = "foo"
    data = {
        "user_id": user_id,
    }
    expected_error = f"Can't add a quote to Person with user_id {user_id} because they don't exist."

    response = client.patch(
        url_for("api.quoteresource", quote_id=prepared_quote.id),
        data=json.dumps(data),
        content_type="application/json",
    )

    response_json = response.json
    assert response.status_code == 404
    assert response_json.get("message") == expected_error


def test_edit_raises_404_if_quote_does_not_exist(client, session):
    quote_id = 1
    expected_error = f"Can't find a quote with quote_id {quote_id} because it don't exist."

    response = client.get(url_for("api.quoteresource", quote_id=quote_id))

    response_json = response.json
    assert response.status_code == 404
    assert response_json.get("message") == expected_error


def test_edit_raises_409_if_a_quote_with_the_same_content_already_exists_for_current_person(
    client, session, prepared_user
):
    quote_to_edit = mixer.blend(Quote, person=prepared_user, content="Foo")
    existing_quote = mixer.blend(Quote, person=prepared_user, content="Existing")
    data = {
        "content": existing_quote.content,
    }
    expected_error = (
        "The Quote content provided can't be added because " "it already exists for this Person."
    )

    response = client.patch(
        url_for("api.quoteresource", quote_id=quote_to_edit.id),
        data=json.dumps(data),
        content_type="application/json",
    )

    response_json = response.json
    assert response.status_code == 409
    assert response_json.get("message") == expected_error


def test_edit_raises_409_if_a_quote_with_the_same_content_already_exists_for_new_person(
    client, session, prepared_user, prepared_quote
):
    # Existing quote
    mixer.blend(Quote, person=prepared_user, content=prepared_quote.content)
    data = {
        "user_id": prepared_user.slack_user_id,
    }
    expected_error = (
        "The Quote content provided can't be added because " "it already exists for this Person."
    )

    response = client.patch(
        url_for("api.quoteresource", quote_id=prepared_quote.id),
        data=json.dumps(data),
        content_type="application/json",
    )

    response_json = response.json
    assert response.status_code == 409
    assert response_json.get("message") == expected_error


def test_get_quote_by_id_raises_404_if_quote_does_not_exist(client, session):
    quote_id = 1
    expected_error = "Can't find a quote with quote_id " f"{quote_id} because it don't exist."

    response = client.get(url_for("api.quoteresource", quote_id=quote_id))

    response_json = response.json
    assert response.status_code == 404
    assert response_json.get("message") == expected_error


def test_get_quote_by_id(client, session, prepared_quote):
    expected_data = get_serialized_quote(prepared_quote)

    response = client.get(
        url_for(
            "api.quoteresource",
            quote_id=prepared_quote.id,
        )
    )

    response_json = response.json
    assert response.status_code == 200
    assert response_json == expected_data
