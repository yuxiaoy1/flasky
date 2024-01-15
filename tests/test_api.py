import json
import unittest

from app import create_app
from app.extensions import db
from app.models import Role, User


class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_no_auth(self):
        # TODO: this raise error, need fix
        response = self.client.get(
            "/api/posts", headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 401)

    def test_posts(self):
        # add new user
        role = db.session.scalar(db.select(Role).filter_by(name="User"))
        self.assertIsNotNone(role)
        user = User(
            email="susan@example.com",
            username="susan",
            password="cat",
            confirmed=True,
            role=role,
        )
        db.session.add(user)
        db.session.commit()
        # add new post
        response = self.client.post(
            "/api/posts",
            json={"token": user.get_api_token(), "body": "body of the *blog* post"},
        )
        self.assertEqual(response.status_code, 201)
        url = response.headers.get("Location")
        self.assertIsNotNone(url)
        # get new post
        response = self.client.get(url, json={"token": user.get_api_token()})
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response["_links"]["self"], url)
        self.assertEqual(json_response["body"], "body of the *blog* post")
        self.assertEqual(
            json_response["body_html"], "<p>body of the <em>blog</em> post</p>"
        )
