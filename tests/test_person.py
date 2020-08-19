import pytest
from nb2.models import Person


def test_create_person(session):
    """
    Test that a Person can be created with the correct
    fields provided.
    """
    slack_user_id = "U018KSY2DNF"
    first_name = "Emin"
    last_name = "Tham"

    emin = Person(
        slack_user_id="fnaweifoen",
        first_name=first_name,
        last_name=last_name
    )

    session.add(emin)
    session.commit()

    # TODO
    # Call the function (when it exists)
