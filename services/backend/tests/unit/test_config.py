import pytest
from app.core.config import Settings


class TestSettings:

    @pytest.mark.unit
    def test_postgres_url_format(self):
        s = Settings(
            postgres_user="u",
            postgres_password="p",
            postgres_host="h",
            postgres_port=5432,
            postgres_db="d",
        )
        assert s.postgres_url == "postgresql+asyncpg://u:p@h:5432/d"

    @pytest.mark.unit
    def test_keycloak_jwks_url(self):
        s = Settings(keycloak_url="http://kc:8080/realms/test")
        assert s.keycloak_jwks_url == "http://kc:8080/realms/test/protocol/openid-connect/certs"

    @pytest.mark.unit
    def test_keycloak_token_url(self):
        s = Settings(keycloak_url="http://kc:8080/realms/test")
        assert s.keycloak_token_url == "http://kc:8080/realms/test/protocol/openid-connect/token"
