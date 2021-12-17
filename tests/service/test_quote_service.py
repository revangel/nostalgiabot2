import pytest
from mixer.backend.flask import mixer

from nb2.models import Person, Quote
from nb2.service.dtos import AddQuoteDTO
from nb2.service.exceptions import EmptyRequiredFieldException, QuoteAlreadyExistsException
from nb2.service.quote_service import (
    add_quote_to_person,
    delete_quote,
    get_all_quotes_from_person,
    get_quote_from_person,
    get_random_quotes_from_person,
)


def test_get_quote_from_person(client, session):
    person = mixer.blend(Person, slack_user_id=mixer.RANDOM)
    expected_quote = mixer.blend(Quote, person=person)

    actual_quote = get_quote_from_person(person, expected_quote.id)

    assert actual_quote == expected_quote


@pytest.mark.parametrize("num_quotes", [0, 1, 5])
def test_get_random_quotes_from_person(client, session, num_quotes):
    person = mixer.blend(Person, slack_user_id=mixer.RANDOM)
    expected_quotes = mixer.cycle().blend(Quote, person=person)

    random_quotes = get_random_quotes_from_person(person, num_quotes)

    assert set(random_quotes).issubset(expected_quotes)
    assert len(random_quotes) == num_quotes


def test_get_random_quotes_from_person_defaults_to_one(client, session):
    person = mixer.blend(Person, slack_user_id=mixer.RANDOM)
    expected_quotes = mixer.cycle().blend(Quote, person=person)

    random_quotes = get_random_quotes_from_person(person)

    assert set(random_quotes).issubset(expected_quotes)
    assert len(random_quotes) == 1


@pytest.mark.parametrize("num_quotes", [0, 1, 5])
def test_get_all_quotes_from_person(num_quotes, client, session):
    person = mixer.blend(Person, slack_user_id=mixer.RANDOM)
    expected_quotes = mixer.cycle(num_quotes).blend(Quote, person=person)

    actual_quotes = get_all_quotes_from_person(person)

    assert actual_quotes == expected_quotes


def test_add_quote_to_person(client, session):
    person = mixer.blend(Person, slack_user_id=mixer.RANDOM)

    assert len(person.quotes) == 0

    content = "My face always looks like such a tomato."
    data = AddQuoteDTO(person, content)

    add_quote_to_person(data)

    assert len(person.quotes) == 1
    assert person.has_said(content)


def test_quote_service_raises_exception_if_quote_content_already_exists(client, session):
    person = mixer.blend(Person, slack_user_id=mixer.RANDOM)
    quote = mixer.blend(Quote, person=person)

    with pytest.raises(QuoteAlreadyExistsException):
        data = AddQuoteDTO(person, quote.content)
        add_quote_to_person(data)


def test_quote_service_raises_exception_if_required_fields_are_empty(client, session):
    data = AddQuoteDTO(None, None)

    with pytest.raises(EmptyRequiredFieldException):
        add_quote_to_person(data)


def test_delete_quote(client, session):
    person = mixer.blend(Person, slack_user_id=mixer.RANDOM)
    quote = mixer.blend(Quote, person=person)

    assert len(Quote.query.all()) == 1

    delete_quote(quote)

    assert len(Quote.query.all()) == 0
