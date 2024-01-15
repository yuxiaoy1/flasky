from werkzeug.exceptions import HTTPException
from werkzeug.http import HTTP_STATUS_CODES

from app.api import api


def error_response(status_code, message=None):
    payload = {"error": HTTP_STATUS_CODES.get(status_code, "Unkown error")}
    if message:
        payload["message"] = message
    return payload, status_code


def bad_request(message):
    return error_response(400, message)


def unauthorized(message):
    return error_response(401, message)


def forbidden(message):
    return error_response(403, message)


class ValidationError(ValueError):
    pass


@api.errorhandler(HTTPException)
def handle_exception(e):
    return error_response(e.code)


@api.errorhandler(ValidationError)
def validation_error(e):
    return bad_request(e.args[0])
