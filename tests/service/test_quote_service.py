import pytest

from mixer.backend.flask import mixer

from nb2.service.dtos import AddQuoteDTO
from nb2.service.exceptions import EmptyRequiredFieldException, PersonDoesNotExistException, QuoteAlreadyExistsException
from nb2.service.quote_service import *


def test_quote_service(client, session):
    person = mixer.blend(Person)

    assert len(person.quotes) == 0

    content = "My face always looks like such a tomato."
    data = AddQuoteDTO(person.slack_user_id, content)

    add_quote_to_person(data)

    assert len(person.quotes) == 1
    assert person.has_said(content)


def test_quote_service_raises_exception_if_person_does_not_exist(client, session):
    data = AddQuoteDTO("nonexistent", "Should not be saved!")

    with pytest.raises(PersonDoesNotExistException):
        add_quote_to_person(data)


def test_quote_service_raises_exception_if_quote_content_already_exists(client, session):
    assert Person.query.count() == 0

    # Note: mixer will also create the pre-requisite Person when making this Quote
    quote = mixer.blend(Quote)

    # Since there were no people before, the person created should have id == 1
    person = Person.query.get(1)

    assert person.has_said(quote.content)

    with pytest.raises(QuoteAlreadyExistsException):
        data = AddQuoteDTO(person.slack_user_id, quote.content)
        add_quote_to_person(data)

def test_quote_service_raises_exception_if_required_fields_are_empty(client, session):
    data = AddQuoteDTO(None, None)

    with pytest.raises(EmptyRequiredFieldException):
        add_quote_to_person(data)
