from flask import Blueprint, render_template, request

from app.api.error import error_response as api_error_response

error = Blueprint("error", __name__)


def wants_json_response():
    return (
        request.accept_mimetypes["application/json"]
        >= request.accept_mimetypes["test/html"]
    )


@error.app_errorhandler(400)
def bad_request(e):
    return api_error_response(40) if wants_json_response() else render_template(
        "error/400.html"
    ), 400


@error.app_errorhandler(404)
def not_found(e):
    return api_error_response(404) if wants_json_response() else render_template(
        "error/404.html"
    ), 404


@error.app_errorhandler(500)
def internal_error(e):
    return api_error_response(500) if wants_json_response() else render_template(
        "error/500.html"
    ), 500
