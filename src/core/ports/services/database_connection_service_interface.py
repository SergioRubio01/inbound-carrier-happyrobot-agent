from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional


class DatabaseConnectionServicePort(ABC):
    """Interface for database connection services"""

    @abstractmethod
    async def get_pool(self):
        """
        Get the connection pool, creating it if it doesn't exist

        Returns:
            Connection pool
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the connection pool"""
        pass

    @abstractmethod
    @asynccontextmanager
    async def connection(self):
        """
        Get a connection from the pool

        Yields:
            Database connection
        """
        pass

    @abstractmethod
    @asynccontextmanager
    async def transaction(self):
        """
        Start a transaction

        Yields:
            Transaction connection
        """
        pass

    @abstractmethod
    async def execute(self, query: str, *args, **kwargs) -> str:
        """
        Execute a query

        Args:
            query: SQL query to execute
            *args: Arguments to pass to the query
            **kwargs: Keyword arguments to pass to the query

        Returns:
            Query result
        """
        pass

    @abstractmethod
    async def fetch(self, query: str, *args, **kwargs) -> List[Dict[str, Any]]:
        """
        Execute a query and return all results

        Args:
            query: SQL query to execute
            *args: Arguments to pass to the query
            **kwargs: Keyword arguments to pass to the query

        Returns:
            List of query results
        """
        pass

    @abstractmethod
    async def fetchrow(self, query: str, *args, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Execute a query and return the first result

        Args:
            query: SQL query to execute
            *args: Arguments to pass to the query
            **kwargs: Keyword arguments to pass to the query

        Returns:
            First query result or None if no results
        """
        pass

    @abstractmethod
    async def fetchval(self, query: str, *args, **kwargs) -> Any:
        """
        Execute a query and return a single value

        Args:
            query: SQL query to execute
            *args: Arguments to pass to the query
            **kwargs: Keyword arguments to pass to the query

        Returns:
            Single value from the first row
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the database connection is healthy

        Returns:
            True if the connection is healthy, False otherwise
        """
        pass
