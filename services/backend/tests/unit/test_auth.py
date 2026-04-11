# =============================================================================
# tests/unit/test_auth.py
# =============================================================================
# Tests for JWT validation and auth middleware.
#
# We can't test against a real Keycloak — so we:
# 1. Generate our own RS256 key pair
# 2. Sign tokens with our private key
# 3. Serve the public key via a mocked JWKS endpoint
# 4. Verify that our auth code correctly validates/rejects these tokens
#
# This is exactly what Keycloak does in production — we're just simulating it.
# =============================================================================

import pytest
import time
from unittest.mock import patch, MagicMock
from jose import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.auth import verify_token, TokenData


# =============================================================================
# TEST KEY GENERATION
# We generate a real RSA key pair for tests.
# This is the same algorithm Keycloak uses — RS256.
# =============================================================================

@pytest.fixture(scope="session")
def rsa_key_pair():
    """Generate a test RSA key pair once for the entire test session."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )
    public_key = private_key.public_key()
    return private_key, public_key


@pytest.fixture(scope="session")
def sign_token(rsa_key_pair):
    """
    Factory fixture: returns a function that creates signed JWTs.
    Tests call this to get tokens with specific claims.
    """
    private_key, _ = rsa_key_pair

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    def _sign(claims: dict) -> str:
        # Default claims — tests can override any of these
        default_claims = {
            "sub": "test-user-id-abc",
            "email": "test@example.com",
            "preferred_username": "testuser",
            "realm_access": {"roles": ["user"]},
            "aud": "argus-backend",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,  # Valid for 1 hour
        }
        default_claims.update(claims)
        return jwt.encode(default_claims, private_pem, algorithm="RS256")

    return _sign


@pytest.fixture
def mock_jwks(rsa_key_pair, mocker):
    """
    Mocks the get_jwks() call so auth code uses our test public key
    instead of trying to fetch from Keycloak.
    """
    _, public_key = rsa_key_pair

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    # jose library accepts PEM public keys directly in JWKS-like format
    mocker.patch("app.core.auth.get_jwks", return_value=public_pem)
    # Clear the lru_cache so our mock is used
    from app.core import auth
    auth.get_jwks.cache_clear() if hasattr(auth.get_jwks, 'cache_clear') else None


class TestVerifyToken:
    """Tests for the verify_token dependency."""

    @pytest.mark.unit
    def test_valid_token_returns_token_data(self, sign_token, mock_jwks):
        token = sign_token({
            "sub": "user-123",
            "email": "felix@codai.dev",
            "preferred_username": "felix",
            "realm_access": {"roles": ["user", "admin"]},
        })
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        result = verify_token(credentials)

        assert isinstance(result, TokenData)
        assert result.user_id == "user-123"
        assert result.email == "felix@codai.dev"
        assert result.username == "felix"
        assert "admin" in result.roles

    @pytest.mark.unit
    def test_expired_token_raises_401(self, sign_token, mock_jwks):
        token = sign_token({
            "exp": int(time.time()) - 3600,  # Expired 1 hour ago
        })
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(credentials)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    @pytest.mark.unit
    def test_missing_token_raises_401(self):
        """No Authorization header at all."""
        with pytest.raises(HTTPException) as exc_info:
            verify_token(None)

        assert exc_info.value.status_code == 401

    @pytest.mark.unit
    def test_tampered_token_raises_401(self, sign_token, mock_jwks):
        """A token with a modified payload should fail signature check."""
        token = sign_token({})
        # Tamper with the payload (middle part of JWT)
        parts = token.split(".")
        tampered = parts[0] + ".TAMPERED_PAYLOAD" + parts[2]
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=tampered)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(credentials)

        assert exc_info.value.status_code == 401

    @pytest.mark.unit
    def test_wrong_audience_raises_401(self, sign_token, mock_jwks):
        """Token issued for a different audience (e.g. different service)."""
        token = sign_token({"aud": "some-other-service"})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(credentials)

        assert exc_info.value.status_code == 401

    @pytest.mark.unit
    def test_empty_roles_defaults_to_empty_list(self, sign_token, mock_jwks):
        """Token without realm_access claim should not crash."""
        token = sign_token({"realm_access": {}})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        result = verify_token(credentials)
        assert result.roles == []


class TestRequireRole:
    """Tests for the require_role dependency factory."""

    @pytest.mark.unit
    def test_user_with_role_passes(self):
        from app.core.auth import require_role, TokenData

        user = TokenData(
            user_id="u1", email="a@b.com", username="a", roles=["admin", "user"]
        )
        checker = require_role("admin")
        result = checker(user)
        assert result == user

    @pytest.mark.unit
    def test_user_without_role_raises_403(self):
        from app.core.auth import require_role, TokenData

        user = TokenData(
            user_id="u1", email="a@b.com", username="a", roles=["user"]
        )
        checker = require_role("admin")

        with pytest.raises(HTTPException) as exc_info:
            checker(user)

        assert exc_info.value.status_code == 403
