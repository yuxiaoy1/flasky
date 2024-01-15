from datetime import datetime, timezone

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.decorators import permission_required
from app.extensions import db
from app.forms import CommentForm, PostForm
from app.models import Comment, Permission, Post

post = Blueprint("post", __name__)


@post.before_app_request
def before_app_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
        if (
            not current_user.confirmed
            and request.blueprint != "auth"
            and request.endpoint != "static"
        ):
            return redirect(url_for("auth.unconfirmed"))


@post.route("/", methods=["GET", "POST"])
@login_required
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for("post.index"))
    show_following = False
    if current_user.is_authenticated:
        show_following = bool(request.cookies.get("show_following", ""))
    if show_following:
        query = current_user.following_posts
    else:
        query = db.select(Post)
    posts = db.paginate(
        query.order_by(Post.timestamp.desc()),
        per_page=current_app.config["POSTS_PER_PAGE"],
    )
    return render_template(
        "index.html", form=form, posts=posts, show_following=show_following
    )


@post.get("/all")
@login_required
def show_all():
    res = make_response(redirect(url_for("post.index")))
    res.set_cookie("show_following", "", max_age=30 * 24 * 60 * 60)
    return res


@post.get("/following")
@login_required
def show_following():
    res = make_response(redirect(url_for("post.index")))
    res.set_cookie("show_following", "1", max_age=30 * 24 * 60 * 60)
    return res


@post.route("/post/<int:id>", methods=["GET", "POST"])
def get_post(id):
    post = db.get_or_404(Post, id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            body=form.body.data, post=post, author=current_user._get_current_object()
        )
        db.session.add(comment)
        db.session.commit()
        flash("Your comment has been published.")
        return redirect(url_for("post.get_post", id=post.id))
    comments = db.paginate(
        post.comments.select().order_by(Comment.timestamp.desc()),
        per_page=current_app.config["COMMENTS_PER_PAGE"],
    )
    return render_template(
        "post/index.html", posts=[post], form=form, comments=comments
    )


@post.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_post(id):
    post = db.get_or_404(Post, id)
    if current_user != post.author and not current_user.can(Permission.ADMIN):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.commit()
        flash("The post has been updated.")
        return redirect(url_for("post.get_post", id=post.id))
    form.body.data = post.body
    return render_template("post/edit_post.html", form=form)


@post.get("/moderate")
@login_required
@permission_required(Permission.MODERATE)
def moderate():
    comments = db.paginate(
        db.select(Comment).order_by(Comment.timestamp.desc()),
        per_page=current_app.config["COMMENTS_PER_PAGE"],
    )
    return render_template("post/moderate.html", comments=comments, moderate=True)


@post.get("/moderate/enable/<int:id>")
@login_required
@permission_required(Permission.MODERATE)
def moderate_enable(id):
    comment = db.get_or_404(Comment, id)
    comment.disabled = False
    db.session.commit()
    return redirect(url_for("post.moderate"))


@post.get("/moderate/disable/<int:id>")
@login_required
@permission_required(Permission.MODERATE)
def moderate_disable(id):
    comment = db.get_or_404(Comment, id)
    comment.disabled = True
    db.session.commit()
    return redirect(url_for("post.moderate"))
