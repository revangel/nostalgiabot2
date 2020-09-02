import pytest

from nb2.commands import generate_data
from nb2.models import Person, Quote


@pytest.fixture()
def cli_runner(app):
    return app.test_cli_runner()


@pytest.mark.parametrize('num_people', ['1', '10'])
def test_generate_data_creates_num_people(num_people, session, cli_runner):
    # Set quotes to 1 since quotes aren't being tested here
    num_quotes = '1'

    result = cli_runner.invoke(generate_data, [num_people, num_quotes])

    assert result.exit_code == 0  # success
    assert Person.query.count() == int(num_people)


@pytest.mark.parametrize('num_quotes', ['1', '10'])
def test_generate_data_creates_num_quotes(num_quotes, session, cli_runner):
    # Set people to 1 since people aren't being tested here
    num_people = '1'

    result = cli_runner.invoke(generate_data, [num_people, num_quotes])

    assert result.exit_code == 0  # success
    assert Quote.query.count() == int(num_quotes)
