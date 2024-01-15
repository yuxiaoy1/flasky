from random import randint

import click
import sqlalchemy as sa
from faker import Faker
from flask import Blueprint, current_app
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Post, Role, User

command = Blueprint("command", __name__, cli_group=None)


@command.cli.command()
def initdb():
    """Create database."""
    db.drop_all()
    db.create_all()
    print("Database created.")
    Role.insert_roles()
    print("Roles created.")
    user = User(
        email=current_app.config["ADMIN_EMAIL"],
        username=current_app.config["ADMIN_NAME"],
        password="123",
        confirmed=True,
    )
    db.session.add(user)
    db.session.commit()
    print(f"Admin {current_app.config["ADMIN_NAME"]} created.")


@command.cli.command()
@click.argument("user_count", default=20)
@click.argument("post_count", default=100)
def fake(user_count, post_count):
    """Generate fake data."""
    faker = Faker()
    i = 0
    while i < user_count:
        user = User(
            email=faker.email(),
            username=faker.user_name(),
            password="123",
            confirmed=True,
            name=faker.name(),
            location=faker.city(),
            about_me=faker.text(),
            member_since=faker.past_date(),
        )
        db.session.add(user)
        try:
            db.session.commit()
            i += 1
        except IntegrityError:
            db.session.rollback()
    print(f"{user_count} users created.")

    user_count = db.session.scalar(db.select(sa.func.count(User.id)))
    for i in range(post_count):
        post = Post(
            body=faker.text(),
            timestamp=faker.past_date(),
            author=db.session.get(User, randint(1, user_count)),
        )
        db.session.add(post)
    db.session.commit()
    print(f"{post_count} posts created.")


@command.cli.command()
def email():
    """Start email server."""
    import subprocess

    subprocess.call(
        f"aiosmtpd -n -c aiosmtpd.handlers.Debugging -l {current_app.config['MAIL_SERVER']}:{current_app.config['MAIL_PORT']}",
        shell=True,
    )


@command.cli.command()
def test():
    """Run the unit tests."""
    import unittest

    tests = unittest.TestLoader().discover("tests")
    unittest.TextTestRunner(verbosity=2).run(tests)
