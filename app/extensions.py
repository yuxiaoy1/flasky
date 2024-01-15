from flask_bootstrap import Bootstrap5
from flask_login import LoginManager
from flask_mailman import Mail
from flask_moment import Moment
from flask_pagedown import PageDown
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
bootstrap = Bootstrap5()
moment = Moment()
mail = Mail()
login = LoginManager()
pagedown = PageDown()


@login.user_loader
def load_user(id):
    from app.models import User

    return db.session.get(User, id)


from app.models import AnonymousUser  # noqa:E402

login.login_view = "auth.login"
login.login_message_category = "warning"
login.anonymous_user = AnonymousUser
