from flask import current_app, g, request

from app.api import api
from app.extensions import db
from app.models import Post, User


@api.get("/users")
def get_users():
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config["POSTS_PER_PAGE"]
    return User.to_json_collection(db.select(User), page, per_page, "api.get_users")


@api.get("/users/<int:id>")
def get_user(id):
    user = db.get_or_404(User, id)
    return user.to_json()


@api.get("/users/<int:id>/posts")
def get_user_posts(id):
    user = db.get_or_404(User, id)
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config["POSTS_PER_PAGE"]
    return Post.to_json_collection(
        user.posts.select(), page, per_page, "api.get_user_posts"
    )


@api.get("/users/<int:id>/following-posts")
def get_following_posts(id):
    user = db.get_or_404(User, id)
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config["POSTS_PER_PAGE"]
    return Post.to_json_collection(
        user.following_posts.order_by(Post.timestamp.desc()),
        page,
        per_page,
        "api.get_following_posts",
    )


@api.post("/follow/<int:id>")
def follow(id):
    current_user = g.current_user
    user = db.get_or_404(User, id)
    if not current_user.is_following(user):
        current_user.follow(user)
        db.session.commit()
    return user.to_json()


@api.delete("/follow/<int:id>")
def unfollow(id):
    current_user = g.current_user
    user = db.get_or_404(User, id)
    if current_user.is_following(user):
        current_user.unfollow(user)
        db.session.commit()
    return "", 204
