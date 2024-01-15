import unittest

from app.models import AnonymousUser, Permission, User


class UserModelTestCase(unittest.TestCase):
    def test_password_setter(self):
        user = User(password="cat")
        self.assertTrue(user.password_hash is not None)

    def test_no_password_getter(self):
        user = User(password="cat")
        with self.assertRaises(AttributeError):
            user.password

    def test_password_verification(self):
        user = User(password="cat")
        self.assertTrue(user.check_password("cat"))
        self.assertFalse(user.check_password("dog"))

    def test_password_salts_are_random(self):
        user1 = User(password="cat")
        user2 = User(password="cat")
        self.assertTrue(user1.password_hash != user2.password_hash)

    def test_user_role(self):
        user = User(email="susan@a.com", password="cat")
        self.assertTrue(user.can(Permission.FOLLOW))
        self.assertTrue(user.can(Permission.COMMENT))
        self.assertTrue(user.can(Permission.WRITE))
        self.assertFalse(user.can(Permission.MODERATE))
        self.assertFalse(user.can(Permission.ADMIN))

    def test_anonymouse_user_role(self):
        user = AnonymousUser()
        self.assertFalse(user.can(Permission.FOLLOW))
        self.assertFalse(user.can(Permission.COMMENT))
        self.assertFalse(user.can(Permission.WRITE))
        self.assertFalse(user.can(Permission.MODERATE))
        self.assertFalse(user.can(Permission.ADMIN))
