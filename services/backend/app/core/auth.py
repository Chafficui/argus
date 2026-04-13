# =============================================================================
# app/core/auth.py
# =============================================================================
# This is the authentication layer.
#
# HOW KEYCLOAK AUTH WORKS (step by step):
#
# 1. User opens Argus in browser
# 2. Frontend redirects to Keycloak login page
# 3. User enters username + password at Keycloak
# 4. Keycloak issues a JWT (JSON Web Token) — a signed string like:
#    eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyIsImVtY...
# 5. Frontend stores this token and sends it with every API request:
#    Authorization: Bearer eyJhbGciOiJSUzI1...
# 6. THIS FILE validates that token on every request:
#    - Is it a real token? (signed by Keycloak's private key?)
#    - Is it expired?
#    - Does it have the right audience?
# 7. If valid → extract user info and let the request through
# 8. If invalid → return 401 Unauthorized
#
# WHAT IS A JWT?
# A JWT has 3 parts separated by dots: header.payload.signature
# The payload contains claims like:
#   {
#     "sub": "user-123",          ← user ID
#     "email": "felix@codai.dev", ← email
#     "realm_access": {
#       "roles": ["admin", "user"] ← roles assigned in Keycloak
#     },
#     "exp": 1234567890           ← expiry timestamp
#   }
# Anyone can read the payload (it's just base64-encoded).
# But only Keycloak can SIGN it with its private key.
# We verify the signature using Keycloak's PUBLIC key (fetched from JWKS endpoint).
# =============================================================================

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError
from pydantic import BaseModel
import httpx
import structlog
from functools import lru_cache
from app.core.config import get_settings

log = structlog.get_logger()

# HTTPBearer tells FastAPI to look for "Authorization: Bearer <token>" header
# auto_error=False means we handle the error ourselves (better error messages)
security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    """
    The data we extract from a valid JWT token.
    This gets passed to every route handler that requires auth.
    """

    user_id: str  # Keycloak user UUID (the "sub" claim)
    email: str
    username: str
    roles: list[str] = []  # Roles from Keycloak realm_access


@lru_cache(maxsize=1)
def get_jwks() -> dict:
    """
    Fetch Keycloak's public keys (JWKS = JSON Web Key Set).

    Keycloak signs JWTs with its private key.
    To verify a JWT, we need the corresponding public key.
    Keycloak publishes these at a well-known URL.

    lru_cache(maxsize=1) = fetch once, cache forever.
    In production you'd refresh this periodically (keys can rotate).
    """
    settings = get_settings()
    log.info("Fetching Keycloak JWKS", url=settings.keycloak_jwks_url)

    response = httpx.get(settings.keycloak_jwks_url, timeout=10)
    response.raise_for_status()
    return response.json()


def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> TokenData:
    """
    FastAPI dependency — validates the JWT token on every protected route.

    Usage in routes:
        @router.get("/protected")
        def my_route(user: TokenData = Depends(verify_token)):
            return f"Hello {user.email}"

    FastAPI automatically calls this function before the route handler.
    If it raises an exception → request is rejected.
    If it returns TokenData → that's passed as the 'user' argument.
    """
    settings = get_settings()

    # Dev bypass — NEVER enable in production
    if settings.dev_auth_bypass and settings.environment == "development":
        return TokenData(
            user_id="dev-user-id",
            email="dev@localhost",
            username="dev",
            roles=["user", "admin"],
        )

    # No Authorization header at all
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        # jose.jwt.decode() does everything:
        # 1. Fetches the right public key from JWKS (by key ID in token header)
        # 2. Verifies the signature
        # 3. Checks expiry
        # 4. Checks audience
        # 5. Returns the payload as a dict
        payload = jwt.decode(
            token,
            get_jwks(),
            algorithms=["RS256"],  # Keycloak uses RSA-256 by default
            audience=settings.keycloak_audience,
            options={
                "verify_exp": True,  # Always verify expiry
                "verify_aud": True,  # Always verify audience
            },
        )

        # Extract roles from Keycloak's realm_access claim
        realm_access = payload.get("realm_access", {})
        roles = realm_access.get("roles", [])

        return TokenData(
            user_id=payload["sub"],
            email=payload.get("email", ""),
            username=payload.get("preferred_username", ""),
            roles=roles,
        )

    except ExpiredSignatureError:
        log.warning("Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except JWTError as e:
        log.warning("Invalid token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(role: str):
    """
    Factory function that creates a dependency requiring a specific role.

    Usage:
        @router.delete("/sources/{id}")
        def delete_source(user: TokenData = Depends(require_role("admin"))):
            ...

    This means only users with the "admin" role in Keycloak can call this endpoint.
    """

    def role_checker(user: TokenData = Depends(verify_token)) -> TokenData:
        if role not in user.roles:
            log.warning(
                "Access denied — missing role",
                user_id=user.user_id,
                required_role=role,
                user_roles=user.roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
            )
        return user

    return role_checker
