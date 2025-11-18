# backend/app/utils.py
from datetime import datetime, timedelta
from sqlmodel import Session, select
from .models import Transaction

def get_daily_total(session: Session, user_id: int, day: datetime = None):
    if day is None:
        day = datetime.utcnow()
    start = datetime(day.year, day.month, day.day)
    stmt = select(Transaction).where(Transaction.user_id == user_id).where(Transaction.created_at >= start).where(Transaction.status == "debit")
    txs = session.exec(stmt).all()
    return sum(t.amount for t in txs)
