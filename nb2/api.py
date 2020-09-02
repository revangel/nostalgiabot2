from flask import Blueprint
from flask_restful import abort, Api, fields, marshal, reqparse, Resource
from sqlalchemy.exc import IntegrityError

from nb2.models import Person, Quote


bp = Blueprint("api", __name__)
api = Api(bp)


class IncludeFilterMixin:
    """
    A mixin for optionally including fields in an API response

    To optionally include an API field, the relevant Resource class
    should inherit from this mixin. The Resource class should then
    implement a `get_<fieldname>_field_type` property method that
    returns the type definition of the field to include.

    Example:
        To optionally include a string field named `foo` implement to following
        on the appropriate Resource class

        @property
        def get_foo_field_type(self):
            return fields.String

        See flask-restful docs for defining field types
        https://flask-restful.readthedocs.io/en/latest/fields.html#basic-usage

    To include these the fields in the api response, add the query parameter
    `include=fieldname`. Multiple fieldnames are allowed as well:
    `include=fieldname,fieldname,fieldname`.

    Note that this mixin will modify or create `self.field` and `self.parser`
    properties on the class.
    """

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


class PersonResourceBase(Resource, IncludeFilterMixin):
    """
    A base class for the Person resource to define common properties and methods.

    This class defines a `get_quotes_field_type` method that will allow
    all Resources that inherit from it to optionally include a `quotes` field
    in the response.
    """

    def __init__(self, *args, **kwargs):
        self.fields = {
            "id": fields.Integer,
            "slack_user_id": fields.String,
            "first_name": fields.String,
            "last_name": fields.String,
        }

        self.parser = reqparse.RequestParser(bundle_errors=True)

        super().__init__(*args, **kwargs)

    @property
    def get_quotes_field_type(self):
        return fields.List(fields.String(attribute="content"))


class PersonResource(PersonResourceBase):
    """
    Implements the API methods for operating on a single Person.

    The `get` method is implemented to fetch a specific
    person by a `slack_user_id`.
    """

    ERRORS = {
        "does_not_exist":
            "Person with slack_user_id {slack_user_id} does not exist"
    }

    def get(self, slack_user_id):
        person = Person.query.filter_by(
            slack_user_id=slack_user_id
        ).one_or_none()

        if person is None:
            abort(
                404,
                message=self.ERRORS["does_not_exist"].format(
                    slack_user_id=slack_user_id
                )
            )

        return marshal(person, self.fields), 200


class PersonListResource(PersonResourceBase):
    """
    Implements the API methods for operating on multiple Persons.

    The `get` method is implemented to fetch all people.

    The `post` method is implemented to create a new Person.
    """

    ERRORS = {
        "slack_user_id_missing": "slack_user_id is required",
        "first_name_missing": "first_name is required",
        "already_exists":
            "Person with slack_user_id {slack_user_id} already exists",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        slack_user_id = parsed_args.get("slack_user_id")

        try:
            new_person = Person.create(parsed_args)
        except IntegrityError:
            return abort(
                409,
                message=self.ERRORS.get("already_exists").format(
                    slack_user_id=slack_user_id
                ),
            )

        return marshal(new_person, self.fields), 201


class QuoteResourceBase(Resource):
    """
    A base class for the Quote resource to define common properties and methods.
    """

    def __init__(self, *args, **kwargs):
        self.fields = {
            "id": fields.Integer,
            "content": fields.String,
            "person_id": fields.Integer(),
            "created": fields.DateTime,
        }

        self.parser = reqparse.RequestParser(bundle_errors=True)

        super().__init__(*args, **kwargs)


class QuoteListResource(QuoteResourceBase):
    """
    Implements the API methods for operating on multiple Quotes.

    The `post` method is implemented to create a new Quote.
    """

    ERRORS = {
        "slack_user_id_missing": "slack_user_id is required",
        "content_missing": "content is required",
        "person_does_not_exist": (
            "Can't add a quote to Person with slack_user_id "
            "{slack_user_id} because they don't exist."
        ),
        "already_exists": (
            "The Quote content provided can't be added because "
            "it already exists for this Person."
        )
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.parser.add_argument(
            "slack_user_id",
            dest="slack_user_id",
            required=True,
            type=str,
            help=self.ERRORS.get("slack_user_id_missing"),
        )
        self.parser.add_argument(
            "content",
            dest="content",
            required=True,
            type=str,
            help=self.ERRORS.get("content_missing"),
        )

    def post(self):
        parsed_args = self.parser.parse_args()
        slack_user_id = parsed_args.get("slack_user_id")

        target_person = Person.query.filter(
            Person.slack_user_id == slack_user_id
        ).one_or_none()

        if not target_person:
            return abort(
                400,
                message=self.ERRORS.get("person_does_not_exist").format(
                    slack_user_id=slack_user_id
                ),
            )

        if target_person.has_said(parsed_args.get("content")):
            return abort(
                400,
                message=self.ERRORS.get("already_exists").format(
                    slack_user_id=slack_user_id
                ),
            )

        new_quote = Quote.create(parsed_args)

        return marshal(new_quote, self.fields), 201


api.add_resource(PersonListResource, "/people")
api.add_resource(PersonResource, "/people/<string:slack_user_id>")
api.add_resource(QuoteListResource, "/quotes")
