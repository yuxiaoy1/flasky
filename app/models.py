from datetime import datetime, timezone
from hashlib import md5
from time import time
from typing import Optional

import bleach
import jwt
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import current_app, url_for
from flask_login import AnonymousUserMixin, UserMixin
from markdown import markdown
from werkzeug.security import check_password_hash, generate_password_hash

from app.api.error import ValidationError
from app.extensions import db

follow = db.Table(
    "follow",
    sa.Column("following_id", sa.ForeignKey("user.id"), primary_key=True),
    sa.Column("followed_id", sa.ForeignKey("user.id"), primary_key=True),
)


class PaginatedAPIMixin:
    @staticmethod
    def to_json_collection(query, page, per_page, endpoint, **kwargs):
        resources = db.paginate(query, page=page, per_page=per_page, error_out=False)
        return {
            "items": [item.to_dict() for item in resources.items],
            "_meta": {
                "page": page,
                "per_page": per_page,
                "total_pages": resources.pages,
                "total_items": resources.total,
            },
            "_links": {
                "self": url_for(endpoint, page=page, per_page=per_page, **kwargs),
                "next": url_for(endpoint, page=page + 1, per_page=per_page, **kwargs)
                if resources.has_next
                else None,
                "prev": url_for(endpoint, page=page - 1, per_page=per_page, **kwargs)
                if resources.has_prev
                else None,
            },
        }


class User(UserMixin, PaginatedAPIMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True, index=True)
    name: so.Mapped[Optional[str]] = so.mapped_column(sa.String(64))
    location: so.Mapped[Optional[str]] = so.mapped_column(sa.String(64))
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.Text)
    member_since: so.Mapped[datetime] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    last_seen: so.Mapped[datetime] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    role_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey("role.id"))
    role: so.Mapped["Role"] = so.relationship(back_populates="users")
    password_hash: so.Mapped[str] = so.mapped_column(sa.String(128))
    confirmed: so.Mapped[bool] = so.mapped_column(default=False)
    posts: so.WriteOnlyMapped["Post"] = so.relationship(back_populates="author")
    following: so.WriteOnlyMapped["User"] = so.relationship(
        secondary=follow,
        primaryjoin=(follow.c.followed_id == id),
        secondaryjoin=(follow.c.following_id == id),
        back_populates="followed",
    )
    followed: so.WriteOnlyMapped["User"] = so.relationship(
        secondary=follow,
        primaryjoin=(follow.c.following_id == id),
        secondaryjoin=(follow.c.followed_id == id),
        back_populates="following",
    )
    comments: so.WriteOnlyMapped["Comment"] = so.relationship(back_populates="author")
    token: so.Mapped[Optional[str]] = so.mapped_column(
        sa.String(32), index=True, unique=True
    )
    token_expiration: so.Mapped[Optional[datetime]]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config["ADMIN_EMAIL"]:
                self.role = db.session.scalar(db.select(Role).filter_by(name="Admin"))
            else:
                self.role = db.session.scalar(db.select(Role).filter_by(default=True))

    @property
    def password(self):
        raise AttributeError("password is not a readble attribute")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if self.password_hash:
            return check_password_hash(self.password_hash, password)

    def avatar(self, size=128):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return f"https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}"

    def get_confirmation_token(self, expires_in=3600):
        return jwt.encode(
            {"confirm": self.id, "exp": time() + expires_in},
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

    def confirm(self, token):
        try:
            id = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )["confirm"]
        except Exception:
            return
        if id == self.id:
            self.confirmed = True
            return True

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_admin(self):
        return self.can(Permission.ADMIN)

    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        return (
            db.session.scalar(self.following.select().filter_by(id=user.id)) is not None
        )

    def is_followed_by(self, user):
        return (
            db.session.scalar(self.followed.select().filter_by(id=user.id)) is not None
        )

    @property
    def following_count(self):
        return db.session.scalar(
            db.select(sa.func.count()).select_from(self.following.select().subquery())
        )

    @property
    def followed_count(self):
        return db.session.scalar(
            db.select(sa.func.count()).select_from(self.followed.select().subquery())
        )

    @property
    def following_posts(self):
        Author = so.aliased(User)
        Following = so.aliased(User)
        return (
            db.select(Post)
            .join(Post.author.of_type(Author))
            .join(Author.followed.of_type(Following), isouter=True)
            .where(sa.or_(Following.id == self.id, Author.id == self.id))
            .group_by(Post)
        )

    @property
    def posts_count(self):
        return db.session.scalar(
            db.select(sa.func.count()).select_from(self.posts.subquery())
        )

    def get_api_token(self, expires_in=600):
        return jwt.encode(
            {"user": self.id, "exp": time() + expires_in},
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

    def revoke_token(self):
        # Need extra token table to revoke user token.
        pass

    @staticmethod
    def check_api_token(token):
        try:
            id = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )["user"]
        except Exception:
            return
        return db.session.get(User, id)

    def to_json(self):
        return {
            "username": self.username,
            "member_since": self.member_since,
            "last_seen": self.last_seen,
            "posts_count": self.posts_count,
            "_links": {
                "self": url_for("api.get_user", id=self.id),
                "posts": url_for("api.get_user_posts", id=self.id),
                "following_posts": url_for("api.get_user_following_posts", id=self.id),
            },
        }


class AnonymousUser(AnonymousUserMixin):
    def can(self, perm):
        return False

    def is_admin(self):
        return False


class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


class Role(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True)
    users: so.WriteOnlyMapped["User"] = so.relationship(back_populates="role")
    default: so.Mapped[bool] = so.mapped_column(default=False, index=True)
    permissions: so.Mapped[int] = so.mapped_column(default=0)

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    @staticmethod
    def insert_roles():
        roles = {
            "User": [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            "Moderator": [
                Permission.FOLLOW,
                Permission.COMMENT,
                Permission.WRITE,
                Permission.MODERATE,
            ],
            "Admin": [
                Permission.FOLLOW,
                Permission.COMMENT,
                Permission.WRITE,
                Permission.MODERATE,
                Permission.ADMIN,
            ],
        }
        default_role = "User"
        for r in roles:
            role = db.session.scalar(db.select(Role).filter_by(name=r))
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = role.name == default_role
            db.session.add(role)
        db.session.commit()


class Post(PaginatedAPIMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.Text)
    body_html: so.Mapped[str] = so.mapped_column(sa.Text)
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc)
    )
    author_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id"))
    author: so.Mapped["User"] = so.relationship(back_populates="posts")
    comments: so.WriteOnlyMapped["Comment"] = so.relationship(back_populates="post")

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = [
            "a",
            "abbr",
            "acronym",
            "b",
            "blockquote",
            "code",
            "em",
            "i",
            "li",
            "ol",
            "pre",
            "strong",
            "ul",
            "h1",
            "h2",
            "h3",
            "p",
        ]
        target.body_html = bleach.linkify(
            bleach.clean(
                markdown(value, output_format="html"), tags=allowed_tags, strip=True
            )
        )

    @property
    def comments_count(self):
        return db.session.scalar(
            db.select(sa.func.count()).select_from(self.comments.select().subquery())
        )

    def to_json(self):
        return {
            "body": self.body,
            "body_html": self.body_html,
            "timestamp": self.timestamp,
            "comments_count": self.comments_count,
            "_links": {
                "self": url_for("api.get_post", id=self.id),
                "author": url_for("api.get_user", id=self.author_id),
                "comments": url_for("api.get_post_comments", id=self.id),
            },
        }

    @staticmethod
    def from_json(post):
        body = post.get("body")
        if body is None or body == "":
            raise ValidationError("post does not have a body")
        return Post(body=body)


class Comment(PaginatedAPIMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.Text)
    body_html: so.Mapped[str] = so.mapped_column(sa.Text)
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc)
    )
    disabled: so.Mapped[Optional[bool]]
    author_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id"))
    author: so.Mapped["User"] = so.relationship(back_populates="comments")
    post_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("post.id"))
    post: so.Mapped["Post"] = so.relationship(back_populates="comments")

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ["a", "abbr", "acronym", "b", "code", "em", "i", "strong"]
        target.body_html = bleach.linkify(
            bleach.clean(
                markdown(value, output_format="html"), tags=allowed_tags, strip=True
            )
        )

    def to_json(self):
        return {
            "body": self.body,
            "body_html": self.body_html,
            "timestamp": self.timestamp,
            "disabled": self.disabled,
            "_links": {
                "self": url_for("api.get_comment", id=self.id),
                "author": url_for("api.get_user", id=self.author_id),
                "post": url_for("api.get_post", id=self.post_id),
            },
        }


db.event.listen(Post.body, "set", Post.on_changed_body)
db.event.listen(Comment.body, "set", Comment.on_changed_body)
