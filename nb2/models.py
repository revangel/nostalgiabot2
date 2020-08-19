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

    def __repr__(self):
        return f"<Person: {self.slack_user_id}; Name: {self.first_name}>"
