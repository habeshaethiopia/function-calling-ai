import json
from datetime import datetime
from enum import Enum
import os


class TransactionType(Enum):
    INCOME = "income"
    EXPENSE = "expense"


class FileStorage:
    def __init__(self, file_path="transactions.json"):
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Ensure the transactions file exists with proper structure"""
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump({"transactions": []}, f)

    def _read_transactions(self):
        """Read all transactions from the file"""
        with open(self.file_path, "r") as f:
            return json.load(f)["transactions"]

    def _write_transactions(self, transactions):
        """Write transactions to the file"""
        with open(self.file_path, "w") as f:
            json.dump({"transactions": transactions}, f, indent=2)

    def add_transaction(self, type_, category, amount, date=None):
        """Add a new transaction"""
        if date is None:
            date = datetime.utcnow()
        elif isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d")

        transactions = self._read_transactions()

        # Generate new ID (max existing ID + 1)
        new_id = 1
        if transactions:
            new_id = max(t["id"] for t in transactions) + 1

        transaction = {
            "id": new_id,
            "type": type_.value,
            "category": category,
            "amount": float(amount),
            "date": date.isoformat(),
        }

        transactions.append(transaction)
        self._write_transactions(transactions)
        return new_id

    def get_transactions(self, start_date=None, end_date=None):
        """Get all transactions within a date range"""
        transactions = self._read_transactions()

        if start_date:
            start_date = start_date.isoformat()
            transactions = [t for t in transactions if t["date"] >= start_date]

        if end_date:
            end_date = end_date.isoformat()
            transactions = [t for t in transactions if t["date"] <= end_date]

        return transactions

    def get_monthly_summary(self, year, month):
        """Get summary of transactions for a specific month"""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        transactions = self.get_transactions(start_date, end_date)

        summary = {
            "income": sum(
                float(t["amount"])
                for t in transactions
                if t["type"] == TransactionType.INCOME.value
            ),
            "expenses": sum(
                float(t["amount"])
                for t in transactions
                if t["type"] == TransactionType.EXPENSE.value
            ),
            "transactions": len(transactions),
        }
        summary["balance"] = summary["income"] - summary["expenses"]
        return summary
