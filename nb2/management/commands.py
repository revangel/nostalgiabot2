import click
from flask import Blueprint, current_app
from mixer.backend.flask import mixer

from nb2.models import Person, Quote
from nb2.service.import_export import import_from_file

bp = Blueprint("commands", __name__, cli_group=None)


@bp.cli.command("generate-data")
@click.argument("people", type=click.INT)
@click.argument("quotes", type=click.INT)
def generate_data(people: int, quotes: int):
    """
    Create people amount of Person objects in the database each
    with quotes amount of Quotes.
    """
    current_app.logger.info(f"Generating {people} People objects with {quotes} Quotes each...")

    # May need to modify this when this command is unit tested
    mixer.init_app(current_app)

    people = mixer.cycle(people).blend(
        Person, slack_user_id=mixer.faker.isbn10, last_name=mixer.faker.last_name
    )
    quotes = mixer.cycle(quotes).blend(Quote, person=mixer.SELECT)

    current_app.logger.info("Generated the following people:")
    for person in people:
        current_app.logger.info(f"{person.slack_user_id} - {person.first_name} {person.last_name}")


@bp.cli.command("bulk-import")
@click.argument("filepath", type=click.STRING)
def bulk_import(filepath: str):
    """
    Bulk import NB data from a file.
    """
    import_from_file(filepath)
