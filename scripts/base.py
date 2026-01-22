# Base parent class for all ETL and automation classes
# Contains common functionality and utility access for all child classes
# Initializes logging, utility objects, and provides abstract ETL methods

import abc
import logging
import os
from typing import Any, Dict, List, Optional

import pandas as pd
from dotenv import load_dotenv

from utils.api import API
from utils.db import DB
from utils.file import File


class Base(abc.ABC):
    _instance_count = 0

    def __init__(self, file_path: str):
        """
        Initialize the base class.

        Parameters
        ----------
        file_path : str
            The path to the log file including the file name.
        """
        # Logging
        Base._instance_count += 1
        self.instance_id = Base._instance_count
        self.file_handler: Optional[logging.FileHandler] = None
        self.configure_logging(file_path=file_path)

        logger_name = f"scripts.base.instance_{self.instance_id}"
        self.base_logger = logging.getLogger(logger_name)
        self.logger = self.base_logger
        self.logger.info("Initialized scripts.base class")

        # Environment variables
        load_dotenv()

        # Utility objects
        try:
            self.db = DB(instance_id=self.instance_id)
            self.api = API(instance_id=self.instance_id)
            self.file = File(instance_id=self.instance_id)

        except Exception as e:
            self.logger.error(f"Failed to initialize utility objects: {e}")
            raise

    # MARK: Wrappers
    def read(
        self,
        engine_name: str,
        schema: str,
        table: str,
        table_columns: Optional[List[str]] = None,
        where_clause: Optional[str] = None,
        query: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Read a table from the database using the DB utility wrapper.

        Parameters
        ----------
        engine_name : str
            Database alias from DSN map
        schema : str
            Database schema name
        table : str
            Table name to read
        table_columns : List[str], optional
            Column names to select. Defaults to None (all columns).
        where_clause : str, optional
            SQL WHERE clause without 'WHERE' keyword. Defaults to None.
        query : str, optional
            Custom SQL query. Defaults to None (uses table/columns).

        Returns
        -------
        pd.DataFrame
            Query results as DataFrame
        """
        try:
            return self.db.read(engine_name, schema, table, table_columns, where_clause, query)
        except Exception as e:
            self.logger.error(f"Error in wrapper read method: {e}")
            raise

    # MARK: Base Methods
    def configure_logging(self, file_path: str) -> None:
        """
        Setup instance-specific logging for this object and all utilities.

        Parameters
        ----------
        file_path : str
            Path to log file from logs/ directory (e.g., 'child/process.log')
        """
        try:
            # Create directory structure if it doesn't exist
            log_dir = os.path.dirname(file_path)
            if log_dir:
                full_log_dir = os.path.join("logs", log_dir)
            else:
                full_log_dir = "logs"
            if not os.path.exists(full_log_dir):
                os.makedirs(full_log_dir)

            # Configure logging with full path
            full_log_path = os.path.join("logs", file_path)

            # Create a file handler for the instance
            self.file_handler = logging.FileHandler(full_log_path, mode="w")
            self.file_handler.setLevel(logging.INFO)

            # Create formatter
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            self.file_handler.setFormatter(formatter)

            # Set up instance-specific loggers for all modules
            base_modules = [
                "scripts.base",
                "scripts.child",
                "utils.api",
                "utils.file",
                "utils.db",
                "tools.tool",
            ]

            for module_name in base_modules:
                instance_logger_name = f"{module_name}.instance_{self.instance_id}"
                logger = logging.getLogger(instance_logger_name)
                logger.setLevel(logging.INFO)
                logger.addHandler(self.file_handler)
                logger.propagate = False

        except Exception as e:
            print(f"Error in configure_logging method: {e}")
            raise

    def dispose(self) -> None:
        """
        Clean up logging resources and close file handlers.
        """
        try:
            self.base_logger.info("Disposing of base class")

            # Clean up file handler
            if self.file_handler:
                base_modules = [
                    "scripts.base",
                    "scripts.child",
                    "utils.api",
                    "utils.file",
                    "utils.db",
                    "tools.tool",
                ]
                for module_name in base_modules:
                    instance_logger_name = f"{module_name}.instance_{self.instance_id}"
                    logger = logging.getLogger(instance_logger_name)
                    if self.file_handler in logger.handlers:
                        logger.removeHandler(self.file_handler)

                # Close the file handler
                self.file_handler.close()
                self.file_handler = None

        except Exception as e:
            if hasattr(self, "logger") and self.logger:
                self.logger.error(f"Error in dispose method: {e}")
            else:
                print(f"Error in dispose method: {e}")
            raise

    # MARK: Abstract ETL Methods
    @abc.abstractmethod
    def extract(self) -> None:
        """
        Extract data from source systems.

        Raises
        ------
        NotImplementedError
            If child class does not implement this method
        """
        pass

    @abc.abstractmethod
    def transform(self) -> None:
        """
        Transform extracted data according to business rules.

        Raises
        ------
        NotImplementedError
            If child class does not implement this method
        """
        pass

    @abc.abstractmethod
    def load(self) -> None:
        """
        Load transformed data to destination systems.

        Raises
        ------
        NotImplementedError
            If child class does not implement this method
        """
        pass

    @abc.abstractmethod
    def main(self) -> Dict[str, Any]:
        """
        Main execution method that orchestrates the complete workflow.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing execution results, status, and metrics

        Raises
        ------
        NotImplementedError
            If child class does not implement this method
        """
        pass
