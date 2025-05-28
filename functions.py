from datetime import datetime
from db import Database, TransactionType
from api import ExchangeRateAPI


class FinancialFunctions:
    def __init__(self):
        self.db = Database()
        self.exchange_api = ExchangeRateAPI()

    def log_expense(self, user_id, category, amount, date=None):
        """
        Log an expense transaction

        Args:
            user_id (int): The ID of the user
            category (str): The category of the expense
            amount (float): The amount of the expense
            date (str, optional): The date of the expense in YYYY-MM-DD format

        Returns:
            dict: Result of the operation
        """
        try:
            if date:
                date = datetime.strptime(date, "%Y-%m-%d")
            transaction_id = self.db.add_transaction(
                user_id=user_id,
                type_=TransactionType.EXPENSE,
                category=category,
                amount=float(amount),
                date=date,
            )
            return {
                "success": True,
                "message": f"Expense logged successfully with ID: {transaction_id}",
                "transaction_id": transaction_id,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def log_income(self, user_id, category, amount, date=None):
        """
        Log an income transaction

        Args:
            user_id (int): The ID of the user
            category (str): The category of the income
            amount (float): The amount of the income
            date (str, optional): The date of the income in YYYY-MM-DD format

        Returns:
            dict: Result of the operation
        """
        try:
            if date:
                date = datetime.strptime(date, "%Y-%m-%d")
            transaction_id = self.db.add_transaction(
                user_id=user_id,
                type_=TransactionType.INCOME,
                category=category,
                amount=float(amount),
                date=date,
            )
            return {
                "success": True,
                "message": f"Income logged successfully with ID: {transaction_id}",
                "transaction_id": transaction_id,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_monthly_summary(self, user_id, year, month):
        """
        Get a summary of transactions for a specific month

        Args:
            user_id (int): The ID of the user
            year (int): The year
            month (int): The month (1-12)

        Returns:
            dict: Monthly summary including income, expenses, and balance
        """
        try:
            summary = self.db.get_monthly_summary(user_id, year, month)
            return {"success": True, "summary": summary}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_exchange_rate(self, from_currency, to_currency, date=None):
        """
        Get the exchange rate between two currencies

        Args:
            from_currency (str): The source currency code
            to_currency (str): The target currency code
            date (str, optional): The date in YYYY-MM-DD format

        Returns:
            dict: Exchange rate information
        """
        try:
            result = self.exchange_api.get_exchange_rate(
                from_currency, to_currency, date
            )
            if "error" in result:
                return {"success": False, "error": result["error"]}
            return {"success": True, "rate": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
