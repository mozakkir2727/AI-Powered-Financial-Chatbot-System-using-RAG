# backend/app/mock_bank.py
# Simple in-process mock bank operations.
from .models import Transaction, User, Beneficiary
from sqlmodel import Session, select
from datetime import datetime

def get_balance(session: Session, user_id: int):
    user = session.get(User, user_id)
    return user.balance

def credit_user(session: Session, user_id: int, amount: float, note: str = None):
    user = session.get(User, user_id)
    user.balance += amount
    tx = Transaction(user_id=user_id, beneficiary_id=None, amount=amount, status="credit", note=note)
    session.add(tx)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user.balance

def debit_user(session: Session, user_id: int, beneficiary_id: int, amount: float, note: str = None):
    user = session.get(User, user_id)
    if user.balance < amount:
        return False, "insufficient"
    user.balance -= amount
    tx = Transaction(user_id=user_id, beneficiary_id=beneficiary_id, amount=amount, status="debit", note=note)
    session.add(tx)
    session.add(user)
    session.commit()
    return True, tx
