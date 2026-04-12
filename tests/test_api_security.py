from __future__ import annotations

import unittest

from api.security import (
    create_api_token,
    hash_password,
    normalize_role,
    verify_api_token,
    verify_password_hash,
)


class APISecurityTest(unittest.TestCase):
    def test_should_hash_and_verify_password(self) -> None:
        password_hash = hash_password("example-secret")
        self.assertTrue(verify_password_hash("example-secret", password_hash))
        self.assertFalse(verify_password_hash("wrong-secret", password_hash))

    def test_should_embed_role_inside_jwt_token(self) -> None:
        token = create_api_token(identifier="admin-user", role="operator")
        payload = verify_api_token(token)

        self.assertEqual(payload.get("sub"), "admin-user")
        self.assertEqual(payload.get("role"), "operator")

    def test_should_normalize_unknown_role_to_viewer(self) -> None:
        self.assertEqual(normalize_role("ADMIN"), "admin")
        self.assertEqual(normalize_role("unknown-role"), "viewer")


if __name__ == "__main__":
    unittest.main()
