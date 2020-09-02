from nb2 import db


class DeserializableModelMixin:
    def deserialize(self, data):
        """
        Update the editable fields on a person with `data`.
        """
        # Should this be for all fields?
        for field in self.editable_fields:
            if field in data:
                setattr(self, field, data[field])

class Person(db.Model, DeserializableModelMixin):
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

    required_fields = ['slack_user_id', 'first_name']
    editable_fields = ['slack_user_id', 'first_name', 'last_name']

    def __repr__(self):
        return f"<Person: {self.slack_user_id} | Name: {self.first_name} | Id: {self.id}>"

    def serialize(self):
        return {
            'id': self.id,
            'slack_user_id': self.slack_user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'quotes': [quote.content for quote in self.quotes]
        }


class Quote(db.Model, DeserializableModelMixin):
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

    required_fields = ['person_id', 'content']
    editable_fields = ['content']

    def __repr__(self):
        return f"<Quote: {self.content} | Id: {self.id}>"
