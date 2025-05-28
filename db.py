import sqlite3
from datetime import datetime
from enum import Enum
import logging
import threading
from queue import Queue
import time

logger = logging.getLogger(__name__)


class TransactionType(Enum):
    INCOME = "income"
    EXPENSE = "expense"


class Database:
    _instance = None
    _lock = threading.Lock()
    _connection_pool = Queue()
    _max_connections = 5
    _connection_timeout = 5  # seconds

    def __new__(cls, db_path="transactions.db"):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Database, cls).__new__(cls)
                cls._instance.db_path = db_path
                cls._instance._initialize_pool()
            return cls._instance

    def _initialize_pool(self):
        """Initialize the connection pool"""
        for _ in range(self._max_connections):
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self._connection_pool.put(conn)
        logger.info(
            f"Initialized connection pool with {self._max_connections} connections"
        )

    def _get_connection(self):
        """Get a connection from the pool with timeout"""
        try:
            conn = self._connection_pool.get(timeout=self._connection_timeout)
            return conn
        except Queue.Empty:
            logger.error("Connection pool timeout")
            raise Exception("Database connection timeout")

    def _return_connection(self, conn):
        """Return a connection to the pool"""
        self._connection_pool.put(conn)

    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """
            )
            conn.commit()
            logger.info("Database tables created/verified")
        finally:
            self._return_connection(conn)

    def add_transaction(
        self, type_: TransactionType, category: str, amount: float, date: str = None
    ):
        """
        Add a new transaction to the database

        Args:
            type_ (TransactionType): Type of transaction (income/expense)
            category (str): Category of the transaction
            amount (float): Amount of the transaction
            date (str, optional): Date in YYYY-MM-DD format. Defaults to today.

        Returns:
            int: ID of the created transaction
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO transactions (type, category, amount, date, created_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (type_.value, category, amount, date, datetime.now().isoformat()),
            )

            transaction_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Added new {type_.value} transaction: {amount} in {category}")
            return transaction_id
        except Exception as e:
            logger.error(f"Error adding transaction: {str(e)}")
            raise
        finally:
            self._return_connection(conn)

    def get_transactions(self, start_date: str = None, end_date: str = None):
        """
        Get transactions within a date range

        Args:
            start_date (str, optional): Start date in YYYY-MM-DD format
            end_date (str, optional): End date in YYYY-MM-DD format

        Returns:
            list: List of transaction dictionaries
        """
        query = "SELECT * FROM transactions"
        params = []

        if start_date or end_date:
            conditions = []
            if start_date:
                conditions.append("date >= ?")
                params.append(start_date)
            if end_date:
                conditions.append("date <= ?")
                params.append(end_date)
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY date DESC"

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            transactions = []
            for row in cursor.fetchall():
                transaction = dict(row)
                transaction["type"] = TransactionType(transaction["type"])
                transactions.append(transaction)
            logger.info(f"Retrieved {len(transactions)} transactions")
            return transactions
        except Exception as e:
            logger.error(f"Error retrieving transactions: {str(e)}")
            raise
        finally:
            self._return_connection(conn)

    def get_monthly_summary(self, year: int, month: int):
        """
        Get summary of transactions for a specific month

        Args:
            year (int): Year
            month (int): Month (1-12)

        Returns:
            dict: Summary of transactions including income, expenses, and balance
        """
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                    SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expenses,
                    COUNT(*) as transactions
                FROM transactions
                WHERE date >= ? AND date < ?
            """,
                (start_date, end_date),
            )

            result = cursor.fetchone()
            income = result[0] or 0
            expenses = result[1] or 0
            transactions = result[2] or 0

            summary = {
                "income": income,
                "expenses": expenses,
                "balance": income - expenses,
                "transactions": transactions,
            }
            logger.info(f"Generated monthly summary for {year}-{month:02d}")
            return summary
        except Exception as e:
            logger.error(f"Error generating monthly summary: {str(e)}")
            raise
        finally:
            self._return_connection(conn)

    def __del__(self):
        """Close all database connections when object is destroyed"""
        while not self._connection_pool.empty():
            conn = self._connection_pool.get()
            conn.close()
        logger.info("All database connections closed")
