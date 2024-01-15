import re
import unittest

from app import create_app, db
from app.models import Role, User


class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        response = self.client.get("/", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("Please log in" in response.get_data(as_text=True))

    def test_register_and_login(self):
        # register new user
        response = self.client.post(
            "/auth/register",
            data={
                "email": "susan@example.com",
                "username": "susan",
                "password": "cat",
                "password2": "cat",
            },
        )
        self.assertEqual(response.status_code, 302)
        # login
        response = self.client.post(
            "/auth/login",
            data={"email": "susan@example.com", "password": "cat"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(re.search("Hello, susan!", response.get_data(as_text=True)))
        self.assertTrue(
            "You have not confirmed your account yet" in response.get_data(as_text=True)
        )
        # confirm token
        user = db.session.scalar(db.select(User).filter_by(email="susan@example.com"))
        token = user.get_confirmation_token()
        response = self.client.get(f"/auth/confirm/{token}", follow_redirects=True)
        user.confirm(token)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            "You have confirmed your account" in response.get_data(as_text=True)
        )
        # logout
        response = self.client.get("/auth/logout", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("Please log in" in response.get_data(as_text=True))
