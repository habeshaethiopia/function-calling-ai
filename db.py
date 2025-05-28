from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Enum,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

Base = declarative_base()


class TransactionType(enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    transactions = relationship("Transaction", back_populates="user")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(Enum(TransactionType), nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="transactions")


class Database:
    def __init__(self, db_path="sqlite:///financial_assistant.db"):
        self.engine = create_engine(db_path)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def add_user(self, name):
        user = User(name=name)
        self.session.add(user)
        self.session.commit()
        return user.id

    def add_transaction(self, user_id, type_, category, amount, date=None):
        if date is None:
            date = datetime.utcnow()
        transaction = Transaction(
            user_id=user_id, type=type_, category=category, amount=amount, date=date
        )
        self.session.add(transaction)
        self.session.commit()
        return transaction.id

    def get_user_transactions(self, user_id, start_date=None, end_date=None):
        query = self.session.query(Transaction).filter(Transaction.user_id == user_id)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        return query.all()

    def get_monthly_summary(self, user_id, year, month):
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        transactions = self.get_user_transactions(user_id, start_date, end_date)

        summary = {
            "income": sum(
                t.amount for t in transactions if t.type == TransactionType.INCOME
            ),
            "expenses": sum(
                t.amount for t in transactions if t.type == TransactionType.EXPENSE
            ),
            "transactions": len(transactions),
        }
        summary["balance"] = summary["income"] - summary["expenses"]
        return summary
