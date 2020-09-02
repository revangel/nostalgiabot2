from flask import jsonify


def _error_response(status_code, message):
    """
    Helper method for returning an API error response.
    """
    payload = {
        'message': message
    }

    response = jsonify(payload)
    response.status_code = status_code

    return response


def validation_error(message):
    """
    Helper method for raising validation errors with 400 status code.
    """
    return _error_response(400, message)


def does_not_exist_error(message):
    """
    Helper method for raising does not exist errors with 404 status code.
    """
    return _error_response(404, message)


def conflict(message):
    """
    Helper method for raising conflict errors with 409 status code.
    """
    return _error_response(409, message)

