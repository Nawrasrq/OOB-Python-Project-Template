# Pytest configuration and fixtures
# Provides common test utilities and setup for all tests

import logging
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest

from scripts.child import Child
from utils.api import API
from utils.db import DB
from utils.file import File


@pytest.fixture
def sample_dataframe():
    """
    Create a sample DataFrame for testing.

    Returns
    -------
    pd.DataFrame
        Sample DataFrame with test data.
    """
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
        'amount': [100.50, 250.75, 150.25, 300.00, 75.80],
        'date': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05']),
        'status': ['active', 'inactive', 'active', 'pending', 'active']
    })


@pytest.fixture
def empty_dataframe():
    """
    Create an empty DataFrame for testing edge cases.

    Returns
    -------
    pd.DataFrame
        Empty DataFrame.
    """
    return pd.DataFrame()


@pytest.fixture
def test_logger():
    """
    Create a test logger for testing.

    Returns
    -------
    logging.Logger
        Configured test logger.
    """
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Add console handler for test output
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


@pytest.fixture
def temp_directory():
    """
    Create a temporary directory for test files.

    Yields
    ------
    Path
        Path to temporary directory.
    """
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir

    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_db_engine():
    """
    Create a mock database engine for testing.

    Returns
    -------
    Mock
        Mock database engine.
    """
    engine = Mock()
    engine.begin.return_value.__enter__ = Mock()
    engine.begin.return_value.__exit__ = Mock(return_value=None)
    return engine


@pytest.fixture
def child_instance():
    """
    Create a Child class instance for testing.

    Yields
    ------
    Child
        Child class instance.
    """
    child = Child('test/test_child.log')
    yield child
    child.dispose()


@pytest.fixture
def db_instance():
    """
    Create a DB utility instance for testing.

    Yields
    ------
    DB
        DB utility instance.
    """
    db = DB(instance_id=1)
    yield db
    db.dispose()


@pytest.fixture
def api_instance():
    """
    Create an API utility instance for testing.

    Yields
    ------
    API
        API utility instance.
    """
    api = API(instance_id=1)
    yield api
    # API cleanup if needed


@pytest.fixture
def file_instance(temp_directory, monkeypatch):
    """
    Create a File utility instance for testing.

    Parameters
    ----------
    temp_directory : Path
        Temporary directory fixture.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.

    Yields
    ------
    File
        File utility instance.
    """
    # Set environment variables to use temp directory
    monkeypatch.setenv("INPUT_PATH", str(temp_directory / "input"))
    monkeypatch.setenv("OUTPUT_PATH", str(temp_directory / "output"))
    monkeypatch.setenv("ARCHIVE_PATH", str(temp_directory / "archive"))
    monkeypatch.setenv("TEMP_PATH", str(temp_directory / "temp"))
    monkeypatch.setenv("BACKUP_PATH", str(temp_directory / "backup"))

    file = File(instance_id=1)
    yield file
    # File cleanup if needed


@pytest.fixture
def sample_csv_file(temp_directory, sample_dataframe):
    """
    Create a sample CSV file for testing.

    Parameters
    ----------
    temp_directory : Path
        Temporary directory fixture.
    sample_dataframe : pd.DataFrame
        Sample DataFrame fixture.

    Returns
    -------
    Path
        Path to sample CSV file.
    """
    csv_file = temp_directory / "sample.csv"
    sample_dataframe.to_csv(csv_file, index=False)
    return csv_file


@pytest.fixture
def sample_excel_file(temp_directory, sample_dataframe):
    """
    Create a sample Excel file for testing.

    Parameters
    ----------
    temp_directory : Path
        Temporary directory fixture.
    sample_dataframe : pd.DataFrame
        Sample DataFrame fixture.

    Returns
    -------
    Path
        Path to sample Excel file.
    """
    excel_file = temp_directory / "sample.xlsx"
    sample_dataframe.to_excel(excel_file, index=False)
    return excel_file


@pytest.fixture
def sample_text_file(temp_directory):
    """
    Create a sample text file for testing.

    Parameters
    ----------
    temp_directory : Path
        Temporary directory fixture.

    Returns
    -------
    Path
        Path to sample text file.
    """
    text_file = temp_directory / "sample.txt"
    content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
    text_file.write_text(content, encoding='utf-8')
    return text_file


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """
    Set up test environment variables.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    # Set test environment variables
    test_env_vars = {
        "ENVIRONMENT": "test",
        "DEBUG_MODE": "true",
        "LOG_LEVEL": "DEBUG",
        "API_BASE_URL": "https://api.test.com",
        "API_KEY": "test_api_key",
        "API_TIMEOUT": "10",
        "SQL_TEST_CONN": "sqlite:///test.db"
    }

    for key, value in test_env_vars.items():
        monkeypatch.setenv(key, value)


# Test data constants
TEST_CONFIG = {
    "column_mappings": {
        "old_name": "new_name",
        "source_id": "target_id"
    },
    "data_types": {
        "id": "int64",
        "amount": "float64",
        "date": "datetime64[ns]"
    },
    "validation_rules": {
        "required_columns": ["id", "name"],
        "numeric_columns": ["amount"],
        "date_columns": ["date"]
    }
}

SAMPLE_API_RESPONSE = {
    "data": [
        {"id": 1, "name": "Test Item 1", "value": 100},
        {"id": 2, "name": "Test Item 2", "value": 200}
    ],
    "total": 2,
    "page": 1,
    "per_page": 10
}
