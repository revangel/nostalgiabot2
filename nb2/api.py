from flask import jsonify, Blueprint

from nb2 import db
from nb2.models import Person

bp = Blueprint('api', __name__)


@bp.route('/')
def hello():
    return 'Hello'

@bp.route('/people')
def get_all_people():
    return jsonify([person.serialize() for person in Person.query.all()])
