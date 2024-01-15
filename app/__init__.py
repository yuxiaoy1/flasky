from flask import Flask

from app.api import api
from app.blueprints.auth import auth
from app.blueprints.command import command
from app.blueprints.error import error
from app.blueprints.post import post
from app.blueprints.user import user
from app.config import config
from app.extensions import bootstrap, db, login, mail, moment, pagedown
from app.models import Permission


def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    register_blueprints(app)
    register_extensions(app)
    register_template_context(app)

    return app


def register_extensions(app: Flask):
    bootstrap.init_app(app)
    db.init_app(app)
    login.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    pagedown.init_app(app)


def register_blueprints(app: Flask):
    app.register_blueprint(command)
    app.register_blueprint(error)
    app.register_blueprint(post)
    app.register_blueprint(api, url_prefix="/api")
    app.register_blueprint(user, url_prefix="/user")
    app.register_blueprint(auth, url_prefix="/auth")


def register_template_context(app: Flask):
    @app.context_processor
    def template_context():
        return dict(Permission=Permission)
