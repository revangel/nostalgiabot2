import json
from typing import list

from flask import current_app

from nb2.service.dtos import AddQuoteDTO, CreatePersonDTO
from nb2.service.person_service import create_person, get_person_by_slack_user_id
from nb2.service.quote_service import add_quote_to_person


def import_from_file(filepath: str):
    """
    Parse through a memory file to import the Persons and Quotes contained.

    Schema (TODO: Replace with validation via schema library)
    [
        {
            "slack_user_id": str,
            "first_name": str,
            "last_name": str, (optional),
            "quotes": [str]
        },
    ]
    """
    try:
        file = open(filepath)
    except FileNotFoundError:
        current_app.logger.error(f"[Import Error]: Cannot open file {filepath}")

    with file:
        records = json.load(file)

        for record in records:
            slack_user_id = record.get("slack_user_id")

            _process_person(
                slack_user_id=slack_user_id,
                first_name=record.get("first_name"),
                last_name=record.get("last_name"),
            )

            _process_quotes(slack_user_id=slack_user_id, quotes=record.get("quotes"))

    file.close()


def _process_person(slack_user_id: str, first_name: str, last_name: str = None, **kwargs):
    """
    Add a new Person to the DB if they don't already exist.
    """
    if get_person_by_slack_user_id(slack_user_id) is not None:
        # This Person already exists
        return

    create_person_dto = CreatePersonDTO(
        slack_user_id=slack_user_id, first_name=first_name, last_name=kwargs.get("last_name")
    )

    create_person(create_person_dto)


def _process_quotes(slack_user_id: str, quotes: list[str]):
    """
    Add quotes to the DB for Person with slack_user_id.

    Note: Assumes that Person with slack_user_id already exists in the DB.
    """
    for quote in quotes:
        add_quote_dto = AddQuoteDTO(slack_user_id=slack_user_id, content=quote)
        add_quote_to_person(add_quote_dto)
