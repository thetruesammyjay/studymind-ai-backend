"""Tests for custom exception classes."""

from app.utils.exceptions import (
    AppError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)


class TestAppError:
    def test_defaults(self):
        err = AppError("something broke")
        assert err.message == "something broke"
        assert err.status_code == 400
        assert str(err) == "something broke"

    def test_custom_status(self):
        err = AppError("conflict", status_code=409)
        assert err.status_code == 409


class TestNotFoundError:
    def test_message_and_status(self):
        err = NotFoundError("Session")
        assert err.message == "Session not found"
        assert err.status_code == 404


class TestValidationError:
    def test_message_and_status(self):
        err = ValidationError("invalid input")
        assert err.message == "invalid input"
        assert err.status_code == 422


class TestAuthenticationError:
    def test_defaults(self):
        err = AuthenticationError()
        assert err.message == "Not authenticated"
        assert err.status_code == 401

    def test_custom_message(self):
        err = AuthenticationError("Token expired")
        assert err.message == "Token expired"


class TestAuthorizationError:
    def test_defaults(self):
        err = AuthorizationError()
        assert err.message == "Not authorized"
        assert err.status_code == 403
