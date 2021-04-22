from datetime import datetime

from sqlalchemy import CheckConstraint

from nb2 import db


class Person(db.Model):
    """
    Represents someone that Nostalgiabot has quotes for;
    usually an SDE employee.

    Most Persons will have a slack_user_id if they still have a Slack account
    where the bot is deployed. For non-Slack users, called Ghost Person,
    a ghost_user_id is used to refer to the Person.
    """

    # A Person must have either a slack_user_id OR a ghost_user_id
    # Some Persons may have both if they were a slack user at some point
    # that has since been deactivated. Those deactivated Persons should be
    # assigned a ghost_user_id to keep accessing their quotes.
    __table_args__ = (CheckConstraint("NOT(slack_user_id IS NULL AND ghost_user_id IS NULL)"),)

    id = db.Column(db.Integer, primary_key=True)
    slack_user_id = db.Column(
        db.String(16),
        index=True,
        unique=True,
    )
    ghost_user_id = db.Column(
        db.String(16),
        index=True,
        unique=True,
    )
    first_name = db.Column(db.String(32), nullable=False)
    last_name = db.Column(db.String(32))
    quotes = db.relationship("Quote", backref="person", lazy=True)

    def __repr__(self):
        user_id = self.slack_user_id or self.ghost_user_id
        return f"<Person: {user_id} | Name: {self.first_name} | Id: {self.id}>"

    def has_said(self, quote: str) -> bool:
        """
        Check if quote already exists in Nostalgiabot's memory for this Person.

        Args:
            quote: a string representing something this Person said.

        Returns:
            True if a Quote record in the db for this Person has the same content
            as quote. False otherwise
        """
        return any(q for q in self.quotes if q.content.lower() == quote.lower())


class Quote(db.Model):
    """
    Represents something a Person has said;
    usually something funny.
    """

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey("person.id"), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<Quote: {self.content} | Id: {self.id}>"
