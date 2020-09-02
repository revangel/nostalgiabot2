from datetime import datetime

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

    required_fields = ['slack_user_id', 'first_name']
    editable_fields = ['slack_user_id', 'first_name', 'last_name']

    def __repr__(self):
        return f"<Person: {self.slack_user_id} | Name: {self.first_name} | Id: {self.id}>"

    @staticmethod
    def create(data):
        """
        Update the editable fields on a person with `data`.
        """
        new_person = Person()
        for field in Person.editable_fields:
            if field in data:
                setattr(new_person, field, data[field])

        db.session.add(new_person)
        db.session.commit()
        db.session.refresh(new_person)

        return new_person

    def has_said(self, quote:str) -> bool:
        """
        Check if quote already exists in Nostalgiabot's memory for this Person.

        Args:
            quote: a string representing something this Person said.

        Returns:
            True if a Quote record in the db for this Person has the same content
            as quote. False otherwise
        """
        return any(q for q in self.quotes if q.content.lower()==quote.lower())


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

    required_fields = ['slack_user_id', 'content']
    editable_fields = ['content']

    def __repr__(self):
        return f"<Quote: {self.content} | Id: {self.id}>"

    def serialize(self):
        return {
            'id': self.id,
            'content': self.content,
            'person_id': self.person_id,
            'created': self.created,
        }

    def deserialize(self, data):
        person_id = Person.query.filter(Person.slack_user_id==data['slack_user_id']) \
                    .one() \
                    .id
        setattr(self, 'content', data['content'])
        setattr(self, 'person_id', person_id)
        setattr(self, 'created', datetime.now())

