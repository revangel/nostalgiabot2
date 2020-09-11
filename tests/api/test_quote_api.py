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
    yield mixer.blend(Person)


@pytest.fixture()
def prepared_quote(client, session, prepared_user):
    yield mixer.blend(Quote)


def test_get_quote_from_person(client, session, prepared_quote):
    expected_data = get_serialized_quote(prepared_quote)

    response = client.get(
        url_for(
            "api.personquoteresource",
            slack_user_id=prepared_quote.person.slack_user_id,
            quote_id=prepared_quote.id,
        )
    )

    response_json = response.json
    assert response.status_code == 200
    assert response_json == expected_data


def test_get_quote_raises_404_if_person_does_not_exist(client, session):
    slack_user_id = "foo"
    expected_error = f"Person with slack_user_id {slack_user_id} does not exist"

    response = client.get(
        url_for("api.personquoteresource", slack_user_id=slack_user_id, quote_id=1)
    )

    response_json = response.json
    assert response.status_code == 404
    assert response_json.get("message") == expected_error


def test_get_quote_raises_404_if_quote_does_not_exist(client, session, prepared_user):
    quote_id = 1
    expected_error = (
        f"Quote with id {quote_id} does not exist for person "
        f"with slack_user_id {prepared_user.slack_user_id}"
    )

    response = client.get(
        url_for(
            "api.personquoteresource", slack_user_id=prepared_user.slack_user_id, quote_id=quote_id
        )
    )

    response_json = response.json
    assert response.status_code == 404
    assert response_json.get("message") == expected_error


def test_create_quote(client, session, prepared_user):
    data = {
        "slack_user_id": prepared_user.slack_user_id,
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
    data = {"slack_user_id": prepared_user.slack_user_id, "content": "the more poking the better"}

    response = client.post(
        url_for("api.quotelistresource"), data=json.dumps(data), content_type="application/json"
    )

    # Intentional duplicate call to test validation against
    # duplicate quotes
    response = client.post(
        url_for("api.quotelistresource"), data=json.dumps(data), content_type="application/json"
    )

    assert response.status_code == 400

    expected_error_msg = (
        "The Quote content provided can't be added because it already exists for this Person."
    )
    assert response.json.get("message") == expected_error_msg
