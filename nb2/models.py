from nb2 import db


class Person(db.Model):
    """
    Represents someone that Nostalgiabot has quotes for;
    usually an SDE employee.
    """
    id = db.Column(db.Integer, primary_key=True)
    slack_user_id = db.Column(
        db.String(16),
        index=True,
        unique=True,
        nullable=False
    )
    first_name = db.Column(db.String(32), nullable=False)
    last_name = db.Column(db.String(32))
    quotes = db.relationship('Quote', backref='person', lazy=True)

    def __repr__(self):
        return f"<Person: {self.slack_user_id}; Name: {self.first_name}>"


class Quote(db.Model):
    """
    Represents something a Person has said;
    usually something funny.
    """
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    person_id = db.Column(
        db.Integer,
        db.ForeignKey('person.id'),
        nullable=False
    )
    created = db.Column(db.DateTime, nullable=False)