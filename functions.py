from datetime import datetime
from db import Database, TransactionType
# from storage import FileStorage, TransactionType
from api import ExchangeRateAPI
import logging

logger = logging.getLogger(__name__)


class FinancialFunctions:
    def __init__(self):
        self.storage = Database()
        # self.storage = FileStorage()
        self.exchange_api = ExchangeRateAPI()
        logger.info("Initialized FinancialFunctions")

    def log_expense(self, category, amount, date=None):
        """
        Log an expense transaction

        Args:
            category (str): The category of the expense
            amount (float): The amount of the expense
            date (str, optional): The date of the expense in YYYY-MM-DD format

        Returns:
            dict: Result of the operation
        """
        try:
            transaction_id = self.storage.add_transaction(
                type_=TransactionType.EXPENSE,
                category=category,
                amount=float(amount),
                date=date,
            )
            logger.info(f"Logged expense: {amount} in {category}")
            return {
                "success": True,
                "message": f"Expense logged successfully with ID: {transaction_id}",
                "transaction_id": transaction_id,
            }
        except Exception as e:
            logger.error(f"Error logging expense: {str(e)}")
            return {"success": False, "error": str(e)}

    def log_income(self, category, amount, date=None):
        """
        Log an income transaction

        Args:
            category (str): The category of the income
            amount (float): The amount of the income
            date (str, optional): The date of the income in YYYY-MM-DD format

        Returns:
            dict: Result of the operation
        """
        try:
            transaction_id = self.storage.add_transaction(
                type_=TransactionType.INCOME,
                category=category,
                amount=float(amount),
                date=date,
            )
            logger.info(f"Logged income: {amount} in {category}")
            return {
                "success": True,
                "message": f"Income logged successfully with ID: {transaction_id}",
                "transaction_id": transaction_id,
            }
        except Exception as e:
            logger.error(f"Error logging income: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_monthly_summary(self, year, month):
        """
        Get a summary of transactions for a specific month

        Args:
            year (int): The year
            month (int): The month (1-12)

        Returns:
            dict: Monthly summary including income, expenses, and balance
        """
        try:
            summary = self.storage.get_monthly_summary(year, month)
            logger.info(f"Retrieved monthly summary for {year}-{month:02d}")
            return {"success": True, "summary": summary}
        except Exception as e:
            logger.error(f"Error getting monthly summary: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_exchange_rate(self, from_currency, to_currency, date=None):
        """
        Get exchange rate between two currencies
        """
        try:
            result = self.exchange_api.get_exchange_rate(
                from_currency, to_currency, date
            )
            if result["success"]:
                logger.info(
                    f"Retrieved exchange rate: {from_currency} to {to_currency}"
                )
                return {
                    "success": True,
                    "rate": {
                        "from": result["from"],
                        "to": result["to"],
                        "rate": result["rate"],
                        "date": result["date"],
                    },
                }
            logger.error(f"Error getting exchange rate: {result.get('error')}")
            return result
        except Exception as e:
            logger.error(f"Error in get_exchange_rate: {str(e)}")
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
