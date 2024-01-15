from flask import g, request, url_for

from app.api import api
from app.api.decorators import permission_required
from app.api.error import forbidden
from app.extensions import db
from app.models import Permission, Post


@api.get("/posts")
def get_posts():
    posts = db.session.scalars(db.select(Post))
    return {"posts": [post.to_json() for post in posts]}


@api.get("/posts/<int:id>")
def get_post(id):
    post = db.get_or_404(Post, id)
    return post.to_json()


@api.post("/posts")
@permission_required(Permission.WRITE)
def new_post():
    post = Post.from_json(request.json)
    post.author = g.current_user
    db.session.add(post)
    db.session.commit()
    return post.to_json(), 201, {"Location": url_for("api.get_post", id=post.id)}


@api.put("/posts/<int:id>")
@permission_required(Permission.WRITE)
def update_post(id):
    post = db.get_or_404(Post, id)
    current_user = g.current_user
    if current_user != post.author and not current_user.can(Permission.ADMIN):
        return forbidden("Insufficient permissions")
    post.body = request.json.get("body", post.body)
    db.session.commit()
    return post.to_json()
