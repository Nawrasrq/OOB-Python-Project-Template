import logging
import os
import uuid
from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


class DB:
    def __init__(self, instance_id=None):
        """
        Initialize the DB utility.

        Parameters
        ----------
        instance_id : int, optional
            The instance ID for logging purposes. If not provided, uses default logger.
        """
        # Logging
        if instance_id:
            logger_name = f"utils.db.instance_{instance_id}"
        else:
            logger_name = "utils.db"
        self.logger = logging.getLogger(logger_name)

        # Engines
        self._dsn_map = {
            "database": os.getenv("SQL_DATABASE_CONN"),
        }
        self._engines: Dict[str, Engine] = {}
        self.logger.info("DB utility initialized")

    def get_engine(self, name: str) -> Engine:
        """
        Get the engine for the given database alias, create it if it doesn't exist.

        Parameters
        ----------
        name : str
            The alias of the database.

        Returns
        -------
        Engine
            The engine for the given database alias.

        Raises
        ------
        ValueError
            If the database alias is not found.
        EnvironmentError
            If the connection string for the database alias is not set.
        SQLAlchemyError
            If SQL fails to create the engine.
        Exception
            If unexpected error occurs.
        """
        try:
            # Check if the engine is already created
            if name not in self._dsn_map:
                raise ValueError(f"Unknown database alias: {name}")
            if name in self._engines:
                return self._engines[name]

            # Get the connection string
            dsn = self._dsn_map[name]
            if not dsn:
                self.logger.error(f"Connection string for '{name}' is not set")
                raise EnvironmentError(f"Set the connection string for '{name}' in your environment")

            # Create the engine
            engine = create_engine(
                dsn,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_size=10,          # tune for your workload
                max_overflow=20,       # tune for your workload
                pool_timeout=30,       # fail fast if pool exhausted
                fast_executemany=True, # mssql+pyodbc bulk inserts
                future=True,           # SQLAlchemy 2.x style
            )
            self.logger.info(f"Initialized engine for '{name}'")
            self._engines[name] = engine
            return engine

        except SQLAlchemyError as e:
            self.logger.error(f"SQL error while initializing engine '{name}': {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error while initializing engine '{name}': {e}")
            raise

    def dispose(self, name: Optional[str] = None) -> None:
        """
        Dispose one engine or all engines.

        Parameters
        ----------
        name : str, optional
            The alias of the database to dispose.
        """
        try:
            if name:
                eng = self._engines.pop(name, None)
                if eng:
                    eng.dispose()
                    self.logger.info(f"Disposed engine '{name}'")
            else:
                for k, eng in list(self._engines.items()):
                    eng.dispose()
                    self.logger.info(f"Disposed engine '{k}'")
                self._engines.clear()

        except Exception as e:
            self.logger.error(f"Error disposing engine(s): {e}")
            raise

    def read(
        self,
        engine_name: str,
        schema: str,
        table: str,
        table_columns: List[str] = [],
        where_clause: str = "",
        query: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Read a table from the database.

        Parameters
        ----------
        engine_name : str
            The name of the engine to read from.
        schema : str
            The schema of the table.
        table : str
            The table to read.
        table_columns : List[str], optional
            The columns to read.
        where_clause : str, optional
            The where clause to filter the table.
        query : str, optional
            The query to read the table.

        Returns
        -------
        pd.DataFrame
            A dataframe with the specified columns.

        Raises
        ------
        SQLAlchemyError
            If read SQL operation fails.
        Exception
            If unexpected error occurs.
        """
        try:
            engine = self.get_engine(engine_name)

            # Build query if not provided
            if query is None:
                cols = ", ".join(table_columns) if table_columns else "*"
                query = f"SELECT {cols} FROM {schema}.{table}"
                if where_clause:
                    query += f" WHERE {where_clause}"

            # Read table
            with engine.begin() as conn:
                stmt = text(query)
                df = pd.read_sql_query(stmt, conn)
            self.logger.info(f"Read {len(df)} rows from {engine_name}.{schema}.{table}")

            # Check if the dataframe is empty
            if df.empty:
                self.logger.warning(f"No data found in {engine_name}.{schema}.{table}")
                df = pd.DataFrame()
            return df

        except SQLAlchemyError as e:
            self.logger.error(f"Read SQL error for table {schema}.{table}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error reading table {schema}.{table}: {e}")
            raise

    def filter(
        self,
        df: pd.DataFrame,
        engine_name: str,
        schema: str,
        table: str,
        join_cols: List[str],
        change_detection_cols: List[str]
    ) -> pd.DataFrame:
        """
        Filter a dataframe to only include the specified columns.

        Parameters
        ----------
        df : pd.DataFrame
            The dataframe to filter.
        engine_name : str
            The database to read from.
        schema : str
            The schema of the table.
        table : str
            The table to filter.
        join_cols : List[str]
            The columns to join on.
        change_detection_cols : List[str]
            The columns to use for change detection.

        Returns
        -------
        pd.DataFrame
            A dataframe with the specified columns.

        Raises
        ------
        SQLAlchemyError
            If filter SQL operation fails.
        Exception
            If unexpected error occurs.
        """
        try:
            if df.empty:
                self.logger.warning(f"Failed to filter using table {schema}.{table}, DataFrame is empty")
                return pd.DataFrame()

            # If no existing data, return all upload data
            existing_df = self.read(engine_name=engine_name, schema=schema, table=table, table_columns=join_cols + change_detection_cols)
            if existing_df.empty:
                self.logger.warning(f"Warning, no existing data found for table {schema}.{table}, returning unfiltered DataFrame")
                return df

            # Filter based on change detection columns
            merged_df = pd.merge(df, existing_df, on=join_cols, how='left', suffixes=('', '_existing'))
            filtered_df = merged_df[merged_df.apply(lambda row: any(row[col] != row[f'{col}_existing'] for col in change_detection_cols), axis=1)]

            # Drop the existing columns
            filtered_df = filtered_df.drop(columns=[f'{col}_existing' for col in change_detection_cols])
            self.logger.info(f"Filtered {len(filtered_df)} rows from {len(df)} upload rows for table {schema}.{table}")

            # Return the filtered dataframe
            return filtered_df

        except SQLAlchemyError as e:
            self.logger.error(f"Filter SQL error for table {schema}.{table}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in filter for table {schema}.{table}: {e}")
            raise

    def insert(
        self,
        df: pd.DataFrame,
        engine_name: str,
        schema: str,
        table: str,
        where_clause: str = "",
        table_columns: List[str] = [],
        query: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        Perform a bulk insert into target table.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to insert.
        engine_name : str
            The name of the engine to insert to.
        schema : str
            The schema of the table.
        table : str
            The table to insert to.
        where_clause : str, optional
            The where clause to filter the table.
        table_columns : List[str], optional
            The columns to read.
        query : str, optional
            The query to insert the table.

        Returns
        -------
        Dict[str, int]
            Dictionary with 'inserted' key containing count of inserted rows

        Raises
        ------
        SQLAlchemyError
            If insert SQL operation fails.
        Exception
            If unexpected error occurs.
        """
        try:
            # Check for empty or missing columns in dataframe
            if df.empty:
                self.logger.warning(f"Failed to insert for table {schema}.{table}, DataFrame is empty")
                return {'inserted': 0}

            # Build insert SQL
            if query is None:
                insert_cols = ", ".join(table_columns)
                insert_vals = ", ".join([f"source.{c}" for c in table_columns])
                insert_sql = f"""
                INSERT INTO {schema}.{table} ({insert_cols})
                VALUES ({insert_vals});
                """
                if where_clause:
                    insert_sql += f" WHERE {where_clause}"
            else:
                insert_sql = query

            # Write dataframe to target table
            with self.get_engine(engine_name).begin() as conn:
                conn.execute(text(insert_sql))
                inserted_count = len(df)
                self.logger.info(f"Inserted {inserted_count} rows into {schema}.{table}")
                return {'inserted': inserted_count}

        except SQLAlchemyError as e:
            self.logger.error(f"Insert SQL error for table {schema}.{table}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in insert for table {schema}.{table}: {e}")
            raise

    def upsert(
        self,
        df: pd.DataFrame,
        engine_name: str,
        schema: str,
        table: str,
        on_condition: str,
        table_columns: List[str] = []
    ) -> Dict[str, int]:
        """
        Upsert DataFrame to database table using MERGE statement.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to upsert.
        engine_name : str
            The database to upsert to.
        schema : str
            Target schema.
        table : str
            Target table.
        on_condition : str
            MERGE ON condition
        table_columns : List[str], optional
            Target table columns.

        Returns
        -------
        Dict[str, int]
            Dictionary with 'inserted' and 'updated' row counts.

        Raises
        ------
        SQLAlchemyError
            If upsert SQL operation fails.
        Exception
            If unexpected error occurs.
        """
        try:
            if df.empty:
                self.logger.warning(f"Failed to upsert for table {schema}.{table}, DataFrame is empty")
                return {'inserted': 0, 'updated': 0}

            # Get connection
            conn = self.get_engine(engine_name)

            # Set columns
            if not table_columns:
                table_columns = df.columns.tolist()

            # Build MERGE query
            temp_table = f'#temp{str(uuid.uuid4()).replace("-", "_")}'
            with conn.begin() as conn:
                # Upload data to temp table first
                df[table_columns].to_sql(
                    name=temp_table,
                    con=conn,
                    schema=schema,
                    if_exists='replace',
                    index=False
                )

                # Build default MERGE query
                update_set_clause = ', '.join([f"target.[{col}] = source.[{col}]"  for col in table_columns])
                insert_columns_clause = ', '.join([f"[{col}]" for col in table_columns])
                insert_values_clause = ', '.join([f"source.[{col}]" for col in table_columns])

                upsert_query = text(f"""
                MERGE {schema}.{table} AS target
                USING {temp_table} AS source
                    ON {on_condition}
                WHEN MATCHED THEN
                    UPDATE SET {update_set_clause}
                WHEN NOT MATCHED THEN
                    INSERT ({insert_columns_clause})
                    VALUES ({insert_values_clause})
                OUTPUT $action;
                """)

                # Execute the merge and get row counts
                result = conn.execute(upsert_query)
                rows = result.fetchall()

                # Count inserts and updates
                inserted = sum(1 for row in rows if row[0] == 'INSERT')
                updated = sum(1 for row in rows if row[0] == 'UPDATE')

                self.logger.info(f"Upsert completed for {schema}.{table}: {inserted} inserted, {updated} updated")

                return {'inserted': inserted, 'updated': updated}

        except SQLAlchemyError as e:
            self.logger.error(f"Upsert SQL error for table {schema}.{table}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in upsert for table {schema}.{table}: {e}")
            raise
