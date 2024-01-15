from flask import Blueprint, g, request

api = Blueprint("api", __name__)

from app.api import comment, error, post, user  # noqa:F401,E402


@api.before_request
def before_api_request():
    from app.models import User

    if request.json is None:
        return error.bad_request("Invalid json in body.")
    token = request.json.get("token")
    if not token:
        return error.unauthorized("Authentication token not provided.")
    current_user = User.check_api_token(token)
    if not current_user:
        return error.unauthorized("Invalid authentication token.")
    g.current_user = current_user
