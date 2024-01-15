from flask import current_app, request

from app.api import api
from app.extensions import db
from app.models import Comment, Post


@api.get("/posts/<int:id>/comments")
def get_post_comments(id):
    post = db.get_or_404(Post, id)
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config["COMMENTS_PER_PAGE"]
    return Comment.to_json_collection(
        post.comments.select(), page, per_page, "api.get_post_comments"
    )
