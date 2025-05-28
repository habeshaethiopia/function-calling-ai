import datetime
from db import Database, TransactionType

# from storage import FileStorage, TransactionType
from api import ExchangeRateAPI
import logging

logger = logging.getLogger(__name__)


class FinancialFunctions:
    def __init__(self):
        self.db = Database()
        # self.storage = FileStorage()
        self.exchange_api = ExchangeRateAPI()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialized FinancialFunctions")

    def log_expense(
        self, amount: float, category: str, date: str = None, user_id: int = None
    ) -> dict:
        """
        Log an expense transaction.

        Args:
            amount (float): The amount of the expense
            category (str): The category of the expense
            date (str, optional): The date of the expense in YYYY-MM-DD format
            user_id (int, optional): The ID of the user making the transaction

        Returns:
            dict: Result of the operation
        """
        try:
            if not user_id:
                return {
                    "success": False,
                    "error": "User ID is required for transactions",
                }

            if not date:
                date = datetime.datetime.now().strftime("%Y-%m-%d")

            # Validate amount
            if not isinstance(amount, (int, float)) or amount <= 0:
                return {"success": False, "error": "Amount must be a positive number"}

            # Validate category
            if not category or not isinstance(category, str):
                return {
                    "success": False,
                    "error": "Category must be a non-empty string",
                }

            # Validate date format
            try:
                datetime.datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                return {"success": False, "error": "Date must be in YYYY-MM-DD format"}

            # Add transaction to database
            self.db.add_transaction(
                user_id=user_id,
                amount=amount,
                category=category,
                date=date,
                transaction_type="expense",
            )

            self.logger.info(
                f"Logged expense: {amount} in {category} for user {user_id}"
            )
            return {
                "success": True,
                "message": f"Expense of ${amount:.2f} for {category} on {date} has been logged.",
            }
        except Exception as e:
            self.logger.error(f"Error logging expense: {str(e)}")
            return {"success": False, "error": str(e)}

    def log_income(
        self, amount: float, source: str, date: str = None, user_id: int = None
    ) -> dict:
        """
        Log an income transaction.

        Args:
            amount (float): The amount of the income
            source (str): The source of the income
            date (str, optional): The date of the income in YYYY-MM-DD format
            user_id (int, optional): The ID of the user making the transaction

        Returns:
            dict: Result of the operation
        """
        try:
            if not user_id:
                return {
                    "success": False,
                    "error": "User ID is required for transactions",
                }

            if not date:
                date = datetime.datetime.now().strftime("%Y-%m-%d")

            # Validate amount
            if not isinstance(amount, (int, float)) or amount <= 0:
                return {"success": False, "error": "Amount must be a positive number"}

            # Validate source
            if not source or not isinstance(source, str):
                return {"success": False, "error": "Source must be a non-empty string"}

            # Validate date format
            try:
                datetime.datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                return {"success": False, "error": "Date must be in YYYY-MM-DD format"}

            # Add transaction to database
            self.db.add_transaction(
                user_id=user_id,
                amount=amount,
                category=source,
                date=date,
                transaction_type="income",
            )

            self.logger.info(
                f"Logged income: {amount} from {source} for user {user_id}"
            )
            return {
                "success": True,
                "message": f"Income of ${amount:.2f} from {source} on {date} has been logged.",
            }
        except Exception as e:
            self.logger.error(f"Error logging income: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_monthly_summary(
        self, month: int = None, year: int = None, user_id: int = None
    ) -> dict:
        """
        Get a summary of transactions for a specific month.

        Args:
            month (int, optional): The month number (1-12)
            year (int, optional): The year
            user_id (int, optional): The ID of the user

        Returns:
            dict: Summary of transactions
        """
        try:
            if not user_id:
                return {
                    "success": False,
                    "error": "User ID is required for transactions",
                }

            # Use current month/year if not specified
            if not month or not year:
                now = datetime.datetime.now()
                month = month or now.month
                year = year or now.year

            # Validate month and year
            if not isinstance(month, int) or not 1 <= month <= 12:
                return {
                    "success": False,
                    "error": "Month must be a number between 1 and 12",
                }
            if not isinstance(year, int) or year < 1900 or year > 2100:
                return {"success": False, "error": "Year must be a valid year"}

            # Calculate start and end dates for the month
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year + 1}-01-01"
            else:
                end_date = f"{year}-{month + 1:02d}-01"

            # Get transactions from database
            transactions = self.db.get_transactions(
                user_id=user_id, start_date=start_date, end_date=end_date
            )

            # Calculate summary
            total_income = sum(
                t["amount"] for t in transactions if t["transaction_type"] == "income"
            )
            total_expenses = sum(
                t["amount"] for t in transactions if t["transaction_type"] == "expense"
            )
            balance = total_income - total_expenses

            self.logger.info(
                f"Retrieved monthly summary for user {user_id}: {year}-{month:02d}"
            )
            return {
                "success": True,
                "summary": {
                    "income": total_income,
                    "expenses": total_expenses,
                    "balance": balance,
                    "transactions": len(transactions),
                },
            }
        except Exception as e:
            self.logger.error(f"Error getting monthly summary: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_exchange_rate(
        self, from_currency: str, to_currency: str, user_id: int = None
    ) -> dict:
        """
        Get the exchange rate between two currencies.

        Args:
            from_currency (str): The source currency code
            to_currency (str): The target currency code
            user_id (int, optional): The ID of the user

        Returns:
            dict: Exchange rate information
        """
        try:
            if not user_id:
                return {
                    "success": False,
                    "error": "User ID is required for transactions",
                }

            # Validate currency codes
            if not from_currency or not to_currency:
                return {"success": False, "error": "Both currency codes are required"}

            # Get exchange rate from API
            rate = self.exchange_api.get_exchange_rate(from_currency, to_currency)

            if not rate:
                return {"success": False, "error": "Failed to get exchange rate"}

            self.logger.info(
                f"Retrieved exchange rate: {from_currency} to {to_currency} for user {user_id}"
            )
            return {
                "success": True,
                "rate": {
                    "from": from_currency,
                    "to": to_currency,
                    "rate": rate["rate"],
                    "date": rate["date"],
                },
            }
        except Exception as e:
            self.logger.error(f"Error getting exchange rate: {str(e)}")
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    financial_functions = FinancialFunctions()
    # Test log_expense function
    expense_result = financial_functions.log_expense(amount=100, category="Food")
    print(expense_result)
    # Test log_income function
    income_result = financial_functions.log_income(amount=500, category="Salary")
    print(income_result)
    # Test get_monthly_summary function
    summary_result = financial_functions.get_monthly_summary(year=2024, month=1)
    print(summary_result)
    # Test get_exchange_rate function
    exchange_rate_result = financial_functions.get_exchange_rate(
        from_currency="USD", to_currency="ETB"
    )
    print(exchange_rate_result)
