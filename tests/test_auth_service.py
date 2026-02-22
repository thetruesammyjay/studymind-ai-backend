"""Tests for AuthService — JWT tokens and password hashing."""

import time
import uuid

import jwt
import pytest

from app.services.auth_service import AuthService


class TestPasswordHashing:
    def test_hash_and_verify(self, auth_service: AuthService):
        hashed = auth_service.hash_password("MyPassword123")
        assert hashed != "MyPassword123"
        assert auth_service.verify_password("MyPassword123", hashed)

    def test_wrong_password_fails(self, auth_service: AuthService):
        hashed = auth_service.hash_password("correct")
        assert not auth_service.verify_password("wrong", hashed)

    def test_different_hashes_for_same_password(self, auth_service: AuthService):
        h1 = auth_service.hash_password("same")
        h2 = auth_service.hash_password("same")
        assert h1 != h2  # bcrypt salts differ


class TestAccessToken:
    def test_create_and_verify(self, auth_service: AuthService):
        user_id = str(uuid.uuid4())
        token = auth_service.create_access_token(user_id)
        result = auth_service.verify_token(token, "access")
        assert result == user_id

    def test_decode_payload(self, auth_service: AuthService, test_settings):
        user_id = str(uuid.uuid4())
        token = auth_service.create_access_token(user_id)
        payload = jwt.decode(token, test_settings.JWT_SECRET, algorithms=[test_settings.JWT_ALGORITHM])
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_wrong_type_rejected(self, auth_service: AuthService):
        token = auth_service.create_access_token("user1")
        assert auth_service.verify_token(token, "refresh") is None


class TestRefreshToken:
    def test_create_and_verify(self, auth_service: AuthService):
        user_id = str(uuid.uuid4())
        token = auth_service.create_refresh_token(user_id)
        result = auth_service.verify_token(token, "refresh")
        assert result == user_id

    def test_wrong_type_rejected(self, auth_service: AuthService):
        token = auth_service.create_refresh_token("user1")
        assert auth_service.verify_token(token, "access") is None


class TestVerifyToken:
    def test_expired_token(self, test_settings):
        """Manually craft an expired token."""
        payload = {"sub": "user1", "type": "access", "exp": int(time.time()) - 100}
        token = jwt.encode(payload, test_settings.JWT_SECRET, algorithm=test_settings.JWT_ALGORITHM)
        auth = AuthService(test_settings)
        assert auth.verify_token(token, "access") is None

    def test_invalid_token(self, auth_service: AuthService):
        assert auth_service.verify_token("not.a.token", "access") is None

    def test_tampered_token(self, auth_service: AuthService):
        token = auth_service.create_access_token("user1")
        tampered = token[:-5] + "XXXXX"
        assert auth_service.verify_token(tampered, "access") is None
