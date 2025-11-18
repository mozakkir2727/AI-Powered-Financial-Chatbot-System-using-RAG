# backend/app/main.py
import os
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel, create_engine, Session, select
from .models import User, Beneficiary, Transaction
from .auth import basic_auth, get_session, engine
from .rag_store import RAGStore
from .mock_bank import get_balance, credit_user, debit_user
from .utils import get_daily_total

app = FastAPI(title="AI Financial Chatbot Backend (MVP)")

RAG = RAGStore(index_path="faiss.index", meta_path="faiss_meta.pkl")

@app.on_event("startup")
def on_start():
    SQLModel.metadata.create_all(engine)
    # create sample admin & customer if not exist
    with Session(engine) as s:
        q = select(User).where(User.username == "admin")
        if not s.exec(q).first():
            s.add(User(username="admin", password="adminpass", role="admin", balance=0.0))
        q2 = select(User).where(User.username == "alice")
        if not s.exec(q2).first():
            s.add(User(username="alice", password="alice123", role="customer", balance=1200.0))
        s.commit()

# Admin: upload doc (RAG ingestion)
@app.post("/admin/upload_doc")
def upload_doc(file: UploadFile = File(...), user=Depends(basic_auth), session: Session = Depends(get_session)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="admin only")
    content = file.file.read().decode(errors="ignore")
    # Basic chunking: split by paragraphs
    paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
    docs = []
    for p in paragraphs:
        doc_type ="rule" if "limit" in p.lower() or "daily" in p.lower() else "sanction" if "blacklist" in p.lower() or "sanction" in p.lower() or "country" in p.lower() else "rule"
        docs.append({"text": p, "source": file.filename, "type": doc_type})
    RAG.add_documents(docs)
    return {"status": "ok", "added": len(docs)}

# Customer: add beneficiary
@app.post("/customer/add_beneficiary")
def add_beneficiary(name: str, bank: str, iban: str, country: str, user=Depends(basic_auth), session: Session = Depends(get_session)):
    b = Beneficiary(user_id=user.id, name=name, bank=bank, iban=iban, country=country)
    session.add(b)
    session.commit()
    return {"status":"ok", "beneficiary_id": b.id}

# Customer: balance
@app.get("/customer/balance")
def balance(user=Depends(basic_auth), session: Session = Depends(get_session)):
    bal = get_balance(session, user.id)
    return {"balance": bal}

# Customer: transfer flow
@app.post("/customer/transfer")
def transfer(beneficiary_id: int, amount: float, user=Depends(basic_auth), session: Session = Depends(get_session)):
    # 1) fetch beneficiary
    b = session.get(Beneficiary, beneficiary_id)
    if not b or b.user_id != user.id:
        raise HTTPException(status_code=404, detail="beneficiary not found")
    # 2) check sanctions via RAG (query by iban and country)
    qtext = f"{b.iban} {b.country} {b.name}"
    hits = RAG.query(qtext, top_k=5)
    for h in hits:
        if h.get("type") == "sanction" and ("blacklist" in h.get("text","").lower() or b.country.lower() in h.get("text","").lower()):
            return JSONResponse(status_code=403, content={"status":"blocked", "reason":"sanctions matched", "evidence": h})
    # 3) check rule limits via RAG
    # simple approach: query by "transfer limit" context
    rules = RAG.query("transfer limit per transaction daily limit", top_k=5)
    # default rule values
    daily_limit = 1000.0
    per_tx_limit = 500.0
    for r in rules:
        txt = r["text"].lower()
        if "daily" in txt and "limit" in txt:
            # crude parse numbers
            import re
            m = re.search(r"(\d+)\s*bd", txt)
            if m:
                daily_limit = float(m.group(1))
        if "per transaction" in txt or "per-transaction" in txt or "per transaction limit" in txt:
            import re
            m = re.search(r"(\d+)\s*bd", txt)
            if m:
                per_tx_limit = float(m.group(1))
    # enforce per transaction
    if amount > per_tx_limit:
        return JSONResponse(status_code=403, content={"status":"rule_violation", "reason":"per transaction limit exceeded", "limit": per_tx_limit})
    # enforce daily
    daily_total = get_daily_total(session, user.id)
    if (daily_total + amount) > daily_limit:
        return JSONResponse(status_code=403, content={"status":"rule_violation", "reason": "daily limit exceeded", "daily_total": daily_total, "limit": daily_limit})
    # balance
    bal = get_balance(session, user.id)
    if bal < amount:
        return JSONResponse(status_code=400, content={"status":"insufficient_balance", "balance": bal})
    # execute mock transfer (debit)
    success, tx = debit_user(session, user.id, beneficiary_id, amount, note=f"transfer to {b.name}")
    if not success:
        return JSONResponse(status_code=400, content={"status":"failed", "reason":"debit failed"})
    return {"status":"success", "tx_id": tx.id}

# Admin: credit/debit
@app.post("/admin/modify_balance")
def modify_balance(target_username: str, amount: float, op: str = "credit", user=Depends(basic_auth), session: Session = Depends(get_session)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="admin only")
    stmt = select(User).where(User.username == target_username)
    target = session.exec(stmt).first()
    if not target:
        raise HTTPException(status_code=404, detail="user not found")
    if op == "credit":
        newbal = credit_user(session, target.id, amount, note="admin credit")
    else:
        ok, _ = debit_user(session, target.id, None, amount, note="admin debit")
        if not ok:
            raise HTTPException(status_code=400, detail="insufficient")
        newbal = get_balance(session, target.id)
    return {"status":"ok", "new_balance": newbal}

# Transaction history
@app.get("/customer/transactions")
def tx_history(user=Depends(basic_auth), session: Session = Depends(get_session)):
    stmt = select(Transaction).where(Transaction.user_id == user.id).order_by(Transaction.created_at.desc())
    txs = session.exec(stmt).all()
    return {"transactions":[{"id":t.id,"amount":t.amount,"status":t.status,"created_at":t.created_at.isoformat(),"note":t.note} for t in txs]}
