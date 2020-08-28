from flask import Blueprint, jsonify, request

from nb2 import db
from nb2.errors import conflict, validation_error
from nb2.models import Person

bp = Blueprint('api', __name__)


@bp.route('/')
def hello():
    return 'Hello'


@bp.route('/people', methods=['GET'])
def get_all_people():
    return jsonify([person.serialize() for person in Person.query.all()])


@bp.route('/people', methods=['POST'])
def create_person():
    data = request.get_json() or {}
    slack_user_id = data.get('slack_user_id')
    missing_required_fields = set(Person.required_fields) - set(data.keys())

    if missing_required_fields:
        error_msg = f"Missing required field(s): {', '.join(missing_required_fields)}"
        return validation_error(error_msg)

    if Person.query.filter(Person.slack_user_id == slack_user_id).first():
        error_msg = f"Person with slack_user_id = '{slack_user_id}' already exists"
        return conflict(error_msg)

    new_person = Person()
    new_person.deserialize(data)
    db.session.add(new_person)
    db.session.commit()
    db.session.refresh(new_person)

    response = jsonify(new_person.serialize())
    response.status_code = 201

    return response
