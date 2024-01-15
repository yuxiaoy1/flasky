from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.email import send_confirmation_mail
from app.extensions import db
from app.forms import RegistrationForm, loginForm
from app.models import User

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    form = loginForm()
    if form.validate_on_submit():
        user = db.session.scalar(db.select(User).filter_by(email=form.email.data))
        if user is not None and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next = request.args.get("next")
            if not next or urlsplit(next).netloc != "":
                next = url_for("post.index")
            return redirect(next)
        flash("Invalid username or password.", "warning")
    return render_template("auth/login.html", form=form)


@auth.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            username=form.username.data,
            password=form.password.data,
        )
        db.session.add(user)
        db.session.commit()
        send_confirmation_mail(user)
        flash("A confirmation email has been sent to you by email.")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@auth.get("/confirm/<token>")
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for("post.index"))
    if current_user.confirm(token):
        db.session.commit()
        flash("You have confirmed your account. Thanks!")
    else:
        flash("The confirmation link is invalid or has expired.")
    return redirect(url_for("post.index"))


@auth.get("/unconfirmed")
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for("post.index"))
    return render_template("auth/unconfirmed.html")


@auth.get("/confirm")
@login_required
def resend_confirmation():
    send_confirmation_mail(current_user)
    flash("A new confirmation email has been sent to you by email.")
    return redirect(url_for("post.index"))


@auth.get("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("post.index"))
