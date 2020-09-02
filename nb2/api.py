from flask import Blueprint
from flask_restful import abort, Api, fields, marshal, reqparse, Resource
from sqlalchemy.exc import IntegrityError

from nb2.models import Person, Quote


bp = Blueprint("api", __name__)
api = Api(bp)


class IncludeFilterMixin:

    def __init__(self, *args, **kwargs):
        if not hasattr(self, 'fields'):
            self.fields = {}

        if not hasattr(self, 'parser'):
            self.parser = reqparse.RequestParser(bundle_errors=True)

        self.parser.add_argument('include', type=str, location='args')

        self.include_fields()
        super(IncludeFilterMixin, self).__init__(*args, **kwargs)

    def include_fields(self):
        parsed_args = self.parser.parse_args()
        include_fields = parsed_args['include'] or []

        if include_fields:
            include_fields = include_fields.split(',')

        for field in include_fields:
            field_type = getattr(self, f"get_{field}_field_type", None)

            if field_type:
                self.fields[field] = field_type


class PersonResourceBase(Resource):

    def __init__(self, *args, **kwargs):
        self.fields = {
            "id": fields.Integer,
            "slack_user_id": fields.String,
            "first_name": fields.String,
            "last_name": fields.String,
        }

        self.parser = reqparse.RequestParser(bundle_errors=True)

        super(PersonResourceBase, self).__init__(*args, **kwargs)

    @property
    def get_quotes_field_type(self):
        return fields.List(fields.String(attribute='content'))


class PersonResource(PersonResourceBase, IncludeFilterMixin):

    ERRORS = {
        "does_not_exist": "Person with slack_user_id {slack_user_id} does not exist"
    }

    def get(self, slack_user_id):
        person = Person.query.filter_by(slack_user_id=slack_user_id).one_or_none()

        if person is None:
            abort(404, message=self.ERRORS["does_not_exist"].format(slack_user_id=slack_user_id))

        return marshal(person, self.fields), 200


class PersonListResource(PersonResourceBase, IncludeFilterMixin):

    ERRORS = {
        "slack_user_id_missing": "slack_user_id is required",
        "first_name_missing": "first_name is required",
        "already_exists": "Person with slack_user_id {slack_user_id} already exists"
    }

    def __init__(self, *args, **kwargs):
        super(PersonListResource, self).__init__(*args, **kwargs)
        self.parser.add_argument(
            "slack_user_id",
            dest="slack_user_id",
            required=True,
            type=str,
            help=self.ERRORS.get("slack_user_id_missing"),
        )
        self.parser.add_argument(
            "first_name",
            dest="first_name",
            required=True,
            type=str,
            help=self.ERRORS.get("first_name_missing"),
        )
        self.parser.add_argument(
            "last_name",
            dest="last_name",
            type=str,
        )

    def get(self):
        people = Person.query.all()
        return marshal(people, self.fields), 200

    def post(self):
        parsed_args = self.parser.parse_args()
        slack_user_id = parsed_args.get('slack_user_id')

        try:
            new_person = Person.create(parsed_args)
        except IntegrityError:
            return abort(409, message=self.ERRORS.get('already_exists').format(slack_user_id=slack_user_id))

        return marshal(new_person, self.fields), 201


class QuoteResourceBase(Resource):

    def __init__(self, *args, **kwargs):
        self.fields = {
            "id": fields.Integer,
            "content": fields.String,
            "person": fields.Integer(),
            "created": fields.DateTime
        }

        self.parser = reqparse.RequestParser(bundle_errors=True)

        super(QuoteResourceBase, self).__init__(*args, **kwargs)

    @property
    def get_quotes_field_type(self):
        return fields.List(fields.String(attribute='content'))

#
# @bp.route('/quotes', methods=['POST'])
# def create_quote():
#     data = request.get_json() or {}
#     slack_user_id = data.get('slack_user_id')
#
#     required_field_errors = Validators.validate_required_fields_are_provided(Quote, data)
#     if required_field_errors:
#         return required_field_errors
#
#     target_person = Person.query.filter(Person.slack_user_id==slack_user_id).one_or_none()
#
#     if not target_person:
#         error_msg = f"Can't add a quote to Person with slack_user_id {slack_user_id} " \
#                      "because they don't exist."
#         return validation_error(error_msg)
#
#     if target_person.has_said(data.get('content')):
#         error_msg = f"The Quote content provided can't be added because it already exists " \
#                      "for this Person."
#         return validation_error(error_msg)
#
#     new_quote = Quote()
#     new_quote.deserialize(data)
#     db.session.add(new_quote)
#     db.session.commit()
#     db.session.refresh(new_quote)
#
#     response = jsonify(new_quote.serialize())
#     response.status_code = 201
#
#     return response


api.add_resource(PersonListResource, "/people")
api.add_resource(PersonResource, "/people/<string:slack_user_id>")
