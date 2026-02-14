"""
Tests for OAuth endpoint URLs, CSRF state tokens, token expiry, and HTML escaping.
"""

import time
import pytest

from outlook_auth_server import (
    generate_state_token,
    validate_state_token,
    escape_html,
    _state_tokens,
    STATE_TOKEN_EXPIRY,
)
from auth.token_manager import is_token_expired


# ---------------------------------------------------------------------------
# /consumers/ endpoint URL tests
# ---------------------------------------------------------------------------

class TestConsumersEndpoint:
    """Verify all OAuth URLs use the /consumers/ tenant endpoint."""

    def test_auth_server_authorize_url(self):
        """outlook_auth_server.py builds authorize URL with /consumers/."""
        import inspect
        from outlook_auth_server import auth
        source = inspect.getsource(auth)
        assert "login.microsoftonline.com/consumers/" in source

    def test_auth_server_token_url(self):
        """outlook_auth_server.py exchanges code via /consumers/ token endpoint."""
        import inspect
        from outlook_auth_server import exchange_code_for_tokens
        source = inspect.getsource(exchange_code_for_tokens)
        assert "login.microsoftonline.com/consumers/oauth2/v2.0/token" in source

    def test_token_manager_refresh_url(self):
        """auth/token_manager.py refreshes tokens via /consumers/ endpoint."""
        import inspect
        from auth.token_manager import refresh_access_token
        source = inspect.getsource(refresh_access_token)
        assert "login.microsoftonline.com/consumers/oauth2/v2.0/token" in source


# ---------------------------------------------------------------------------
# State token (CSRF) tests
# ---------------------------------------------------------------------------

class TestStateTokens:
    """CSRF state token generation and validation."""

    def setup_method(self):
        _state_tokens.clear()

    def test_generate_returns_string(self):
        token = generate_state_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_stores_token(self):
        token = generate_state_token()
        assert token in _state_tokens

    def test_validate_accepts_valid_token(self):
        token = generate_state_token()
        assert validate_state_token(token) is True

    def test_validate_is_one_time_use(self):
        token = generate_state_token()
        assert validate_state_token(token) is True
        assert validate_state_token(token) is False

    def test_validate_rejects_unknown_token(self):
        assert validate_state_token("bogus-token-value") is False

    def test_validate_rejects_expired_token(self):
        token = generate_state_token()
        # Backdate the token past the expiry window
        _state_tokens[token] = time.time() - STATE_TOKEN_EXPIRY - 1
        assert validate_state_token(token) is False


# ---------------------------------------------------------------------------
# Token expiry tests
# ---------------------------------------------------------------------------

class TestIsTokenExpired:
    """auth/token_manager.is_token_expired() edge cases."""

    def test_future_expiry_not_expired(self):
        tokens = {"expires_at": time.time() + 3600}
        assert is_token_expired(tokens) is False

    def test_past_expiry_is_expired(self):
        tokens = {"expires_at": time.time() - 3600}
        assert is_token_expired(tokens) is True

    def test_missing_expires_at_is_expired(self):
        tokens = {"access_token": "tok"}
        assert is_token_expired(tokens) is True

    def test_empty_dict_is_expired(self):
        assert is_token_expired({}) is True


# ---------------------------------------------------------------------------
# HTML escaping tests
# ---------------------------------------------------------------------------

class TestEscapeHtml:
    """escape_html() prevents XSS in error pages."""

    def test_escapes_angle_brackets(self):
        assert "&lt;script&gt;" in escape_html("<script>")

    def test_escapes_ampersand(self):
        assert "&amp;" in escape_html("&")

    def test_escapes_quotes(self):
        result = escape_html('"hello"')
        assert "&quot;" in result

    def test_empty_string_returns_empty(self):
        assert escape_html("") == ""

    def test_none_returns_empty(self):
        assert escape_html(None) == ""
