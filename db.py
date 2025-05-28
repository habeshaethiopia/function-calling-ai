import sqlite3
from datetime import datetime
from enum import Enum
import logging
import threading
from queue import Queue
import time
import hashlib
import secrets

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
                cls._instance._create_tables()  # Create tables on initialization
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
        """Create the necessary database tables if they don't exist."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Create users table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        session_token TEXT UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP
                    )
                    """
                )

                # Create transactions table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        amount REAL NOT NULL,
                        category TEXT NOT NULL,
                        date TEXT NOT NULL,
                        transaction_type TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                    """
                )

                # Create exchange_rates table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS exchange_rates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        from_currency TEXT NOT NULL,
                        to_currency TEXT NOT NULL,
                        rate REAL NOT NULL,
                        date TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(from_currency, to_currency, date)
                    )
                    """
                )

                conn.commit()
                logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise

    def create_user(self, username: str, email: str, password: str) -> str:
        """
        Create a new user

        Args:
            username (str): Username
            email (str): Email address
            password (str): Password

        Returns:
            str: Session token if successful, None if failed
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            password_hash = hashlib.sha256((password).encode()).hexdigest()

            # Generate session token
            session_token = secrets.token_hex(32)

            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash, session_token, created_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    username,
                    email,
                    password_hash,
                    session_token,
                    datetime.now().isoformat(),
                ),
            )

            conn.commit()
            logger.info(f"Created new user: {username}")
            return session_token
        except sqlite3.IntegrityError as e:
            logger.error(f"Error creating user: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return None
        finally:
            self._return_connection(conn)

    def authenticate_user(self, username: str, password: str) -> str:
        """
        Authenticate a user

        Args:
            username (str): Username
            password (str): Password

        Returns:
            str: Session token if successful, None if failed
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, password_hash FROM users WHERE username = ?",
                (username,),
            )
            user = cursor.fetchone()

            if not user:
                return None

            # Verify password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if password_hash != user["password_hash"]:
                return None

            # Generate new session token
            session_token = secrets.token_hex(32)

            # Update user's session token and last login
            cursor.execute(
                """
                UPDATE users 
                SET session_token = ?, last_login = ?
                WHERE id = ?
            """,
                (session_token, datetime.now().isoformat(), user["id"]),
            )
            conn.commit()

            return session_token
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return None
        finally:
            self._return_connection(conn)

    def get_user_by_token(self, session_token: str) -> dict:
        """
        Get user by session token

        Args:
            session_token (str): Session token

        Returns:
            dict: User information with success status
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, username, email 
                FROM users 
                WHERE session_token = ? AND last_login > datetime('now', '-24 hours')
                """,
                (session_token,),
            )
            user = cursor.fetchone()

            if not user:
                return {"success": False, "error": "Invalid or expired session token"}

            return {
                "success": True,
                "user_id": user["id"],
                "username": user["username"],
                "email": user["email"],
            }
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            self._return_connection(conn)

    def add_transaction(
        self,
        user_id: int,
        amount: float,
        category: str,
        date: str,
        transaction_type: str,
    ) -> int:
        """
        Add a new transaction to the database.

        Args:
            user_id (int): The ID of the user making the transaction
            amount (float): The amount of the transaction
            category (str): The category of the transaction
            date (str): The date of the transaction in YYYY-MM-DD format
            transaction_type (str): The type of transaction ('income' or 'expense')

        Returns:
            int: The ID of the newly created transaction
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO transactions (user_id, amount, category, date, transaction_type)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, amount, category, date, transaction_type),
                )
                conn.commit()
                transaction_id = cursor.lastrowid
                self.logger.info(
                    f"Added {transaction_type} transaction: {amount} in {category} for user {user_id}"
                )
                return transaction_id
        except Exception as e:
            self.logger.error(f"Error adding transaction: {str(e)}")
            raise

    def get_transactions(
        self, user_id: int, start_date: str = None, end_date: str = None
    ):
        """
        Get transactions within a date range

        Args:
            user_id (int): ID of the user
            start_date (str, optional): Start date in YYYY-MM-DD format
            end_date (str, optional): End date in YYYY-MM-DD format

        Returns:
            list: List of transaction dictionaries
        """
        query = "SELECT * FROM transactions WHERE user_id = ?"
        params = [user_id]

        if start_date or end_date:
            conditions = []
            if start_date:
                conditions.append("date >= ?")
                params.append(start_date)
            if end_date:
                conditions.append("date <= ?")
                params.append(end_date)
            query += " AND " + " AND ".join(conditions)

        query += " ORDER BY date DESC"

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            transactions = []
            for row in cursor.fetchall():
                transaction = dict(row)
                transaction["type"] = TransactionType(transaction["transaction_type"])
                transactions.append(transaction)
            logger.info(f"Retrieved {len(transactions)} transactions")
            return transactions
        except Exception as e:
            logger.error(f"Error retrieving transactions: {str(e)}")
            raise
        finally:
            self._return_connection(conn)

    def get_monthly_summary(self, user_id: int, year: int, month: int):
        """
        Get summary of transactions for a specific month

        Args:
            user_id (int): ID of the user
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
                    SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as income,
                    SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) as expenses,
                    COUNT(*) as transactions
                FROM transactions
                WHERE user_id = ? AND date >= ? AND date < ?
                """,
                (user_id, start_date, end_date),
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

    def verify_database_setup(self):
        """
        Verify that all required tables exist and have the correct structure
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Check users table
            cursor.execute(
                """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='users'
            """
            )
            if not cursor.fetchone():
                self.logger.error("Users table does not exist")
                return False

            # Check transactions table
            cursor.execute(
                """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='transactions'
            """
            )
            if not cursor.fetchone():
                self.logger.error("Transactions table does not exist")
                return False

            # Verify users table structure
            cursor.execute("PRAGMA table_info(users)")
            columns = {row[1] for row in cursor.fetchall()}
            required_columns = {
                "id",
                "username",
                "email",
                "password_hash",
                "session_token",
                "created_at",
                "last_login",
            }
            if not required_columns.issubset(columns):
                self.logger.error(
                    f"Users table missing required columns: {required_columns - columns}"
                )
                return False

            # Verify transactions table structure
            cursor.execute("PRAGMA table_info(transactions)")
            columns = {row[1] for row in cursor.fetchall()}
            required_columns = {
                "id",
                "user_id",
                "amount",
                "category",
                "date",
                "transaction_type",
                "created_at",
            }
            if not required_columns.issubset(columns):
                self.logger.error(
                    f"Transactions table missing required columns: {required_columns - columns}"
                )
                return False

            self.logger.info("Database setup verified successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error verifying database setup: {str(e)}")
            return False
        finally:
            self._return_connection(conn)

    def __init__(self, db_path="transactions.db"):
        """Initialize database and verify setup"""

        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialized Database")
        if not self.verify_database_setup():
            logger.error("Database setup verification failed")
            raise Exception("Database setup verification failed")

    def __del__(self):
        """Close all database connections when object is destroyed"""
        while not self._connection_pool.empty():
            conn = self._connection_pool.get()
            conn.close()
        logger.info("All database connections closed")

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> dict:
        """
        Get the exchange rate between two currencies.

        Args:
            from_currency (str): The source currency code
            to_currency (str): The target currency code

        Returns:
            dict: Exchange rate information or None if not found
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT rate, date 
                FROM exchange_rates 
                WHERE from_currency = ? AND to_currency = ? 
                ORDER BY date DESC 
                LIMIT 1
                """,
                (from_currency.upper(), to_currency.upper()),
            )
            result = cursor.fetchone()

            if not result:
                return None

            return {
                "rate": result["rate"],
                "date": result["date"],
            }
        except Exception as e:
            logger.error(f"Error getting exchange rate: {str(e)}")
            raise
        finally:
            self._return_connection(conn)

    def add_exchange_rate(
        self, from_currency: str, to_currency: str, rate: float, date: str = None
    ) -> bool:
        """
        Add a new exchange rate to the database.

        Args:
            from_currency (str): The source currency code
            to_currency (str): The target currency code
            rate (float): The exchange rate
            date (str, optional): The date of the rate in YYYY-MM-DD format

        Returns:
            bool: True if successful, False otherwise
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO exchange_rates (from_currency, to_currency, rate, date)
                VALUES (?, ?, ?, ?)
                """,
                (from_currency.upper(), to_currency.upper(), rate, date),
            )
            conn.commit()
            logger.info(
                f"Added exchange rate: {from_currency} to {to_currency} = {rate}"
            )
            return True
        except Exception as e:
            logger.error(f"Error adding exchange rate: {str(e)}")
            return False
        finally:
            self._return_connection(conn)
