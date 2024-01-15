from functools import wraps

from flask import abort
from flask_login import current_user

from app.models import Permission


def permission_required(perm):
    def decorator(f):
        @wraps(f)
        def inner(*args, **kwargs):
            if not current_user.can(perm):
                abort(403)
            return f(*args, **kwargs)

        return inner

    return decorator


def admin_required(f):
    return permission_required(Permission.ADMIN)(f)
