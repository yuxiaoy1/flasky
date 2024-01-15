from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask_login import current_user, login_required

from app.decorators import admin_required, permission_required
from app.extensions import db
from app.forms import EditProfileAdmminForm, EditProfileForm
from app.models import Permission, Post, Role, User

user = Blueprint("user", __name__)


@user.get("/<username>")
def index(username):
    user = db.first_or_404(db.select(User).filter_by(username=username))
    posts = db.paginate(
        user.posts.select().order_by(Post.timestamp.desc()),
        per_page=current_app.config["POSTS_PER_PAGE"],
    )
    return render_template("user/index.html", user=user, posts=posts)


@user.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your profile has been updated.")
        return redirect(url_for("user.index", username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template("user/edit_profile.html", form=form)


@user.route("/edit-profile/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_profile_admin(id):
    user = db.get_or_404(User, id)
    form = EditProfileAdmminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = db.session.get(Role, form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.commit()
        flash("The profile has been updated.")
        return redirect(url_for("user.index", username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template("user/edit_profile.html", form=form, user=user)


@user.get("/follow/<username>")
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = db.session.scalar(db.select(User).filter_by(username=username))
    if user is None:
        flash("Invalid user.", "warning")
        return redirect(url_for("post.index"))
    if current_user.is_following(user):
        flash("You are already following this user.")
        return redirect(url_for("user.index", username=username))
    current_user.follow(user)
    db.session.commit()
    flash(f"You are now following {username}.")
    return redirect(url_for("user.index", username=username))


@user.get("/unfollow/<username>")
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = db.session.scalar(db.select(User).filter_by(username=username))
    if user is None:
        flash("Invalid user.", "warning")
        return redirect(url_for("post.index"))
    if not current_user.is_following(user):
        flash("You are not following this user.")
        return redirect(url_for("user.index", username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(f"You are not following {username} anymore.")
    return redirect(url_for("user.index", username=username))


@user.get("/following/<username>")
def following(username):
    user = db.session.scalar(db.select(User).filter_by(username=username))
    if user is None:
        flash("Invalid user.", "warning")
        return redirect(url_for("post.index"))
    follows = db.paginate(
        user.following.select(), per_page=current_app.config["FOLLOWS_PER_PAGE"]
    )
    return render_template(
        "user/follows.html", title="Followers of", user=user, follows=follows
    )


@user.get("/followed/<username>")
def followed_by(username):
    user = db.session.scalar(db.select(User).filter_by(username=username))
    if user is None:
        flash("Invalid user.", "warning")
        return redirect(url_for("post.index"))
    follows = db.paginate(
        user.followed.select(), per_page=current_app.config["FOLLOWS_PER_PAGE"]
    )
    return render_template(
        "user/follows.html", title="Followed by", user=user, follows=follows
    )
