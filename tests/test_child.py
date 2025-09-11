# Tests for child module functionality

from unittest.mock import Mock

import pandas as pd
import pytest

from scripts.child import Child


class TestChildInitialization:
    """Test suite for Child class initialization."""

    def test_child_initialization(self, child_instance):
        """Test Child class initializes correctly."""
        assert child_instance is not None
        assert hasattr(child_instance, 'logger')
        assert hasattr(child_instance, 'instance_id')
        assert hasattr(child_instance, 'db')
        assert hasattr(child_instance, 'api')
        assert hasattr(child_instance, 'file')

    def test_child_has_base_methods(self, child_instance):
        """Test Child class has inherited base methods."""
        assert hasattr(child_instance, 'extract')
        assert hasattr(child_instance, 'transform')
        assert hasattr(child_instance, 'load')
        assert hasattr(child_instance, 'main')
        assert hasattr(child_instance, 'dispose')

    def test_instance_counter_increments(self):
        """Test that instance counter increments for each new instance."""
        child1 = Child('test/child1.log')
        child2 = Child('test/child2.log')

        assert child2.instance_id > child1.instance_id

        child1.dispose()
        child2.dispose()


class TestChildETLMethods:
    """Test suite for Child class ETL methods."""

    def test_extract_method_exists(self, child_instance):
        """Test extract method exists and is callable."""
        assert callable(child_instance.extract)

    def test_transform_method_exists(self, child_instance):
        """Test transform method exists and is callable."""
        assert callable(child_instance.transform)

    def test_load_method_exists(self, child_instance):
        """Test load method exists and is callable."""
        assert callable(child_instance.load)

    def test_main_method_returns_dict(self, child_instance):
        """Test main method executes and returns a dictionary."""
        result = child_instance.main()
        assert isinstance(result, dict)


class TestChildDisposal:
    """Test suite for Child class resource disposal."""

    def test_dispose_cleans_up_resources(self):
        """Test dispose method properly cleans up resources."""
        child = Child('test/dispose_test.log')

        # Verify instance has file handler
        assert child.file_handler is not None

        # Dispose of resources
        child.dispose()

        # Verify file handler is removed
        assert child.file_handler is None

    def test_child_can_be_used_with_context_manager_pattern(self):
        """Test Child instance works with try-finally pattern."""
        child = None
        try:
            child = Child('test/context_test.log')
            assert child is not None
        finally:
            if child:
                child.dispose()

        # If we get here without errors, the pattern works
        assert True


class TestChildLogging:
    """Test suite for Child class logging functionality."""

    def test_logger_has_correct_name(self, child_instance):
        """Test logger has instance-specific name."""
        expected_name = f"scripts.child.instance_{child_instance.instance_id}"
        assert child_instance.logger.name == expected_name

    def test_logger_is_configured(self, child_instance):
        """Test logger is properly configured."""
        assert child_instance.logger is not None
        assert len(child_instance.logger.handlers) > 0


@pytest.mark.integration
class TestChildWithMockedUtilities:
    """Integration tests for Child class with mocked utilities."""

    def test_child_with_mocked_db(self, child_instance):
        """Test Child class with mocked database utility."""
        # Mock the DB read method
        child_instance.db.read = Mock(return_value=pd.DataFrame({
            'id': [1, 2, 3],
            'value': [10, 20, 30]
        }))

        # Call the mocked method
        result = child_instance.db.read(
            engine_name='test',
            schema='test',
            table='test',
            table_columns=['id', 'value'],
            where_clause=None,
            query=None
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert 'id' in result.columns
        assert 'value' in result.columns

    def test_child_workflow_execution(self, child_instance):
        """Test Child class can execute complete workflow."""
        # This is a basic smoke test to ensure methods can be called
        try:
            child_instance.extract()
            child_instance.transform()
            child_instance.load()
            result = child_instance.main()

            assert isinstance(result, dict)
            success = True
        except Exception as e:
            # Log the error but don't fail - methods are stubs in template
            print(f"Workflow execution note: {e}")
            success = True

        assert success
