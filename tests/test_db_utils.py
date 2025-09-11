# Tests for the DB utility class
# Tests database operations, connection management, and error handling

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from sqlalchemy.exc import SQLAlchemyError

from utils.db import DB


class TestDBInitialization:
    """Test suite for DB class initialization."""

    def test_db_initialization_with_instance_id(self):
        """Test DB class initialization with instance ID."""
        db = DB(instance_id=1)

        assert db is not None
        assert hasattr(db, 'logger')
        assert db.logger.name == "utils.db.instance_1"
        assert hasattr(db, '_dsn_map')
        assert hasattr(db, '_engines')

        db.dispose()

    def test_db_initialization_without_instance_id(self):
        """Test DB class initialization without instance ID."""
        db = DB()

        assert db is not None
        assert db.logger.name == "utils.db"

        db.dispose()

    def test_db_has_dsn_map(self, db_instance):
        """Test DB instance has DSN mapping."""
        assert isinstance(db_instance._dsn_map, dict)
        assert 'database' in db_instance._dsn_map


class TestEngineManagement:
    """Test suite for database engine management."""

    def test_get_engine_creates_new_engine(self, db_instance, monkeypatch):
        """Test get_engine creates a new engine when needed."""
        # Set environment variable for test connection
        monkeypatch.setenv("SQL_DATABASE_CONN", "sqlite:///:memory:")

        engine = db_instance.get_engine('database')

        assert engine is not None
        assert 'database' in db_instance._engines

    def test_get_engine_returns_existing_engine(self, db_instance, monkeypatch):
        """Test get_engine returns existing engine if already created."""
        monkeypatch.setenv("SQL_DATABASE_CONN", "sqlite:///:memory:")

        # Get engine first time
        engine1 = db_instance.get_engine('database')

        # Get engine second time
        engine2 = db_instance.get_engine('database')

        # Should return same engine instance
        assert engine1 is engine2

    def test_get_engine_raises_error_for_unknown_alias(self, db_instance):
        """Test get_engine raises ValueError for unknown database alias."""
        with pytest.raises(ValueError, match="Unknown database alias"):
            db_instance.get_engine('nonexistent_db')

    def test_get_engine_raises_error_for_missing_connection_string(self, db_instance):
        """Test get_engine raises EnvironmentError if connection string not set."""
        # The 'database' key exists but env var is not set (None)
        with pytest.raises(EnvironmentError, match="Set the connection string"):
            db_instance.get_engine('database')

    def test_dispose_single_engine(self, db_instance, monkeypatch):
        """Test disposing a single engine."""
        monkeypatch.setenv("SQL_DATABASE_CONN", "sqlite:///:memory:")

        # Create an engine
        db_instance.get_engine('database')
        assert 'database' in db_instance._engines

        # Dispose specific engine
        db_instance.dispose('database')
        assert 'database' not in db_instance._engines

    def test_dispose_all_engines(self, db_instance, monkeypatch):
        """Test disposing all engines."""
        monkeypatch.setenv("SQL_DATABASE_CONN", "sqlite:///:memory:")

        # Create an engine
        db_instance.get_engine('database')
        assert len(db_instance._engines) > 0

        # Dispose all engines
        db_instance.dispose()
        assert len(db_instance._engines) == 0


class TestDataOperations:
    """Test suite for database data operations."""

    @pytest.fixture
    def mock_engine(self):
        """Create a mock SQLAlchemy engine."""
        engine = MagicMock()
        connection = MagicMock()
        engine.begin.return_value.__enter__.return_value = connection
        engine.begin.return_value.__exit__.return_value = None
        return engine

    @patch('utils.db.pd.read_sql_query')
    def test_read_table_with_columns(self, mock_read_sql, db_instance, sample_dataframe, monkeypatch):
        """Test reading table with specific columns."""
        monkeypatch.setenv("SQL_DATABASE_CONN", "sqlite:///:memory:")
        mock_read_sql.return_value = sample_dataframe

        # Mock the engine
        with patch.object(db_instance, 'get_engine') as mock_get_engine:
            mock_engine = MagicMock()
            mock_get_engine.return_value = mock_engine

            result = db_instance.read(
                engine_name='database',
                schema='test_schema',
                table='test_table',
                table_columns=['id', 'name'],
                where_clause=None,
                query=None
            )

            assert isinstance(result, pd.DataFrame)
            mock_read_sql.assert_called_once()

    @patch('utils.db.pd.read_sql_query')
    def test_read_table_with_where_clause(self, mock_read_sql, db_instance, sample_dataframe, monkeypatch):
        """Test reading table with WHERE clause."""
        monkeypatch.setenv("SQL_DATABASE_CONN", "sqlite:///:memory:")
        mock_read_sql.return_value = sample_dataframe

        with patch.object(db_instance, 'get_engine') as mock_get_engine:
            mock_engine = MagicMock()
            mock_get_engine.return_value = mock_engine

            result = db_instance.read(
                engine_name='database',
                schema='test_schema',
                table='test_table',
                table_columns=['id', 'name'],
                where_clause="id > 5",
                query=None
            )

            assert isinstance(result, pd.DataFrame)

    @patch('utils.db.pd.read_sql_query')
    def test_read_table_returns_empty_dataframe(self, mock_read_sql, db_instance, empty_dataframe, monkeypatch):
        """Test reading table returns empty DataFrame when no data."""
        monkeypatch.setenv("SQL_DATABASE_CONN", "sqlite:///:memory:")
        mock_read_sql.return_value = empty_dataframe

        with patch.object(db_instance, 'get_engine') as mock_get_engine:
            mock_engine = MagicMock()
            mock_get_engine.return_value = mock_engine

            result = db_instance.read(
                engine_name='database',
                schema='test_schema',
                table='test_table',
                table_columns=None,
                where_clause=None,
                query=None
            )

            assert isinstance(result, pd.DataFrame)
            assert result.empty

    def test_read_table_with_custom_query(self, db_instance, sample_dataframe, monkeypatch):
        """Test reading table with custom query."""
        monkeypatch.setenv("SQL_DATABASE_CONN", "sqlite:///:memory:")

        with patch('utils.db.pd.read_sql_query') as mock_read_sql:
            mock_read_sql.return_value = sample_dataframe

            with patch.object(db_instance, 'get_engine') as mock_get_engine:
                mock_engine = MagicMock()
                mock_get_engine.return_value = mock_engine

                custom_query = "SELECT * FROM test_table WHERE id IN (1, 2, 3)"
                result = db_instance.read(
                    engine_name='database',
                    schema='test_schema',
                    table='test_table',
                    table_columns=None,
                    where_clause=None,
                    query=custom_query
                )

                assert isinstance(result, pd.DataFrame)
                mock_read_sql.assert_called_once()


@pytest.mark.db
class TestDataIntegrationWithSQLite:
    """Integration tests using actual SQLite database."""

    @pytest.fixture
    def sqlite_db(self, monkeypatch):
        """Create a DB instance with SQLite in-memory database."""
        monkeypatch.setenv("SQL_DATABASE_CONN", "sqlite:///:memory:")
        db = DB(instance_id=999)
        yield db
        db.dispose()

    def test_real_database_read_empty_result(self, sqlite_db):
        """Test reading from actual SQLite database with no results."""
        # SQLite allows queries even if table doesn't exist (will raise error)
        # This tests error handling
        with pytest.raises(Exception):
            sqlite_db.read(
                engine_name='database',
                schema='main',
                table='nonexistent_table',
                table_columns=None,
                where_clause=None,
                query=None
            )


class TestErrorHandling:
    """Test suite for DB error handling."""

    def test_read_handles_database_error(self, db_instance, monkeypatch):
        """Test that read method handles database errors gracefully."""
        monkeypatch.setenv("SQL_DATABASE_CONN", "sqlite:///:memory:")

        with patch.object(db_instance, 'get_engine') as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.begin.side_effect = SQLAlchemyError("Database error")
            mock_get_engine.return_value = mock_engine

            with pytest.raises(Exception):
                db_instance.read(
                    engine_name='database',
                    schema='test',
                    table='test',
                    table_columns=None,
                    where_clause=None,
                    query=None
                )
