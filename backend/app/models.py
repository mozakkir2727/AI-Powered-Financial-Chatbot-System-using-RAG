# backend/app/models.py
from typing import Optional
from datetime import datetime, date
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import func

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password: str  # in production -> hashed
    role: str = Field(default="customer")  # 'admin' or 'customer'
    balance: float = Field(default=0.0)

class Beneficiary(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    name: str
    bank: str
    iban: str
    country: str

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    beneficiary_id: Optional[int] = Field(default=None, foreign_key="beneficiary.id")
    amount: float
    status: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    note: Optional[str] = None
