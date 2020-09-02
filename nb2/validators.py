from nb2.errors import conflict, validation_error


class Validators:

    @staticmethod
    def validate_required_fields_are_provided(model: object, data: dict):
        """
        Raise a validation_error exception if data does not contain one of
        the required fields defined in model.

        Args:
            model: The model to validate fields for.
            data: A dict representing a JSON request body.

        Returns:
            None if model has no required fields or if all required fields
            are provided.
            validation_error if a required field is missing.
        """
        if not hasattr(model, 'required_fields'):
            return


        missing_required_fields = set(model.required_fields) - set(data.keys())

        if missing_required_fields:
            error_msg = f"Missing required field(s): {', '.join(missing_required_fields)}"
            return validation_error(error_msg)

        return
