from flask import Blueprint, jsonify, request

from nb2 import db
from nb2.errors import conflict, does_not_exist_error, validation_error
from nb2.models import Person, Quote
from nb2.validators import Validators

bp = Blueprint('api', __name__)


@bp.route('/')
def hello():
    return 'Hello'


@bp.route('/people', methods=['GET'])
def get_all_people():
    return jsonify([person.serialize() for person in Person.query.all()])


@bp.route('/people/<slack_user_id>', methods=['GET'])
def get_person(slack_user_id):
    person = Person.query.filter_by(slack_user_id=slack_user_id).first()

    if person is None:
        error_msg = f"Person with slack_user_id {slack_user_id} does not exist"
        return does_not_exist_error(error_msg)

    return jsonify(person.serialize())


@bp.route('/people', methods=['POST'])
def create_person():
    data = request.get_json() or {}
    slack_user_id = data.get('slack_user_id')

    required_field_errors = Validators.validate_required_fields_are_provided(Person, data)
    if required_field_errors:
        return required_field_errors

    if Person.query.filter(Person.slack_user_id == slack_user_id).first():
        error_msg = f"Person with slack_user_id {slack_user_id} already exists"
        return conflict(error_msg)

    new_person = Person()
    new_person.deserialize(data)
    db.session.add(new_person)
    db.session.commit()
    db.session.refresh(new_person)

    response = jsonify(new_person.serialize())
    response.status_code = 201

    return response

@bp.route('/quotes', methods=['POST'])
def create_quote():
    data = request.get_json() or {}
    slack_user_id = data.get('slack_user_id')

    required_field_errors = Validators.validate_required_fields_are_provided(Quote, data)
    if required_field_errors:
        return required_field_errors

    if not Person.query.filter(Person.slack_user_id == slack_user_id).all():
        error_msg = f"Can't add a quote to Person with slack_user_id {slack_user_id} " \
                     "because they don't exist."
        return validation_error(error_msg)

    new_quote = Quote()
    new_quote.deserialize(data)
    db.session.add(new_quote)
    db.session.commit()
    db.session.refresh(new_quote)

    response = jsonify(new_quote.serialize())
    response.status_code = 201

    return response
