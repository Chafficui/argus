import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestGetDb:

    @pytest.mark.unit
    async def test_yields_session_and_commits(self):
        mock_session = AsyncMock()

        mock_factory = MagicMock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_session
        mock_factory.return_value = mock_context

        with patch("app.db.database.AsyncSessionLocal", mock_factory):
            from app.db.database import get_db

            gen = get_db()
            session = await gen.__anext__()
            assert session is mock_session

            # Finish the generator (triggers commit)
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass

            mock_session.commit.assert_awaited_once()

    @pytest.mark.unit
    async def test_rolls_back_on_exception(self):
        mock_session = AsyncMock()
        mock_session.commit.side_effect = Exception("db error")

        mock_factory = MagicMock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_session
        mock_factory.return_value = mock_context

        with patch("app.db.database.AsyncSessionLocal", mock_factory):
            from app.db.database import get_db

            gen = get_db()
            await gen.__anext__()

            with pytest.raises(Exception, match="db error"):
                await gen.__anext__()

            mock_session.rollback.assert_awaited_once()


class TestInitDb:

    @pytest.mark.unit
    async def test_creates_tables(self):
        mock_conn = AsyncMock()

        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_conn
        mock_cm.__aexit__.return_value = False

        mock_engine = MagicMock()
        mock_engine.begin.return_value = mock_cm

        with patch("app.db.database.engine", mock_engine):
            from app.db.database import init_db
            await init_db()

        mock_conn.run_sync.assert_awaited_once()
