from flask_pagedown.fields import PageDownField
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
    ValidationError,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp

from app.extensions import db
from app.models import Role, User


class loginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Login")


class RegistrationForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(1, 64),
            Regexp(
                "^[A-Za-z][A-Za-z0-9_.]*$",
                0,
                "Username must have only letters, numbers, dots or underscores",
            ),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            EqualTo("password2", message="Password must match."),
        ],
    )
    password2 = PasswordField("Confirm password", validators=[DataRequired()])
    submit = SubmitField("Login")

    def validate_email(self, field):
        if db.session.scalar(db.select(User).filter_by(email=field.data)):
            raise ValidationError("Email already registered.")

    def validate_username(self, field):
        if db.session.scalar(db.select(User).filter_by(username=field.data)):
            raise ValidationError("Username already in use.")


class EditProfileForm(FlaskForm):
    name = StringField("Real name", validators=[Length(0, 64)])
    location = StringField("Location", validators=[Length(0, 64)])
    about_me = TextAreaField("About me")
    submit = SubmitField("Submit")


class EditProfileAdmminForm(FlaskForm):
    email = StringField(
        "Real name", validators=[DataRequired(), Length(1, 64), Email()]
    )
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(1, 64),
            Regexp(
                "^[A-Za-z][A-Za-z0-9_.]*$",
                0,
                "Username must have only letters, numbers, dots or underscores",
            ),
        ],
    )
    confirmed = BooleanField("Confirmed")
    role = SelectField("Role", coerce=int)
    name = StringField("Real name", validators=[Length(0, 64)])
    location = StringField("Location", validators=[Length(0, 64)])
    about_me = TextAreaField("About me")
    submit = SubmitField("Submit")

    def __init__(self, user, *args, **kwargs):
        super().__init__()
        self.role.choices = [
            (role.id, role.name)
            for role in db.session.scalars(db.select(Role).order_by(Role.name))
        ]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and db.session.scalar(
            db.select(User).filter_by(email=field.data)
        ):
            raise ValidationError("Email already registered.")

    def validate_username(self, field):
        if field.data != self.user.username and db.session.scalar(
            db.select(User).filter_by(username=field.data)
        ):
            raise ValidationError("Username already in use.")


class PostForm(FlaskForm):
    body = PageDownField("What's on your mind?", validators=[DataRequired()])
    submit = SubmitField("Submit")


class CommentForm(FlaskForm):
    body = StringField("Enter your comments", validators=[DataRequired()])
    submit = SubmitField("Submit")
