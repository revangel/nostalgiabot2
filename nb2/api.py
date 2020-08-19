from flask import Blueprint


bp = Blueprint('api', __name__)


@bp.route('/')
def hello():
    return 'Hello'
