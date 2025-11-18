# frontend/streamlit_app.py
import streamlit as st
import requests
from requests.auth import HTTPBasicAuth

API_BASE = st.sidebar.text_input("Backend URL", "http://localhost:8000")

st.title("AI Financial Chatbot (MVP)")

username = st.sidebar.text_input("username")
password = st.sidebar.text_input("password", type="password")
role = st.sidebar.selectbox("Role", ["customer", "admin"])

if st.sidebar.button("Login"):
    if not username or not password:
        st.warning("Enter credentials")
    else:
        st.success("Logged in (UI-level)")

if role == "customer":
    st.header("Customer actions")
    tab = st.radio("Action", ["Check Balance","Add Beneficiary","Transfer","Transactions"])
    if tab == "Check Balance":
        if st.button("Get Balance"):
            r = requests.get(f"{API_BASE}/customer/balance", auth=HTTPBasicAuth(username,password))
            st.write(r.json())
    if tab == "Add Beneficiary":
        name = st.text_input("Name")
        bank = st.text_input("Bank")
        iban = st.text_input("IBAN")
        country = st.text_input("Country")
        if st.button("Add"):
            r = requests.post(f"{API_BASE}/customer/add_beneficiary", params={"name":name,"bank":bank,"iban":iban,"country":country}, auth=HTTPBasicAuth(username,password))
            st.write(r.json())
    if tab == "Transfer":
        beneficiary_id = st.number_input("Beneficiary ID", min_value=1, step=1)
        amount = st.number_input("Amount", min_value=0.0, step=1.0)
        if st.button("Transfer"):
            r = requests.post(f"{API_BASE}/customer/transfer", params={"beneficiary_id":beneficiary_id,"amount":amount}, auth=HTTPBasicAuth(username,password))
            st.write(r.status_code, r.json())
    if tab == "Transactions":
        if st.button("Show"):
            r = requests.get(f"{API_BASE}/customer/transactions", auth=HTTPBasicAuth(username,password))
            st.write(r.json())

else:
    st.header("Admin actions")
    tab = st.radio("Admin", ["Upload Document","Manage Balances","Users"])
    if tab == "Upload Document":
        uploaded_file = st.file_uploader("Upload docx or txt")
        if st.button("Upload") and uploaded_file:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            r = requests.post(f"{API_BASE}/admin/upload_doc", files=files, auth=HTTPBasicAuth(username,password))
            st.write(r.json())
    if tab == "Manage Balances":
        target = st.text_input("Target username")
        op = st.selectbox("Operation", ["credit","debit"])
        amt = st.number_input("Amount", min_value=0.0, step=1.0)
        if st.button("Modify"):
            r = requests.post(f"{API_BASE}/admin/modify_balance", params={"target_username":target, "amount":amt, "op":op}, auth=HTTPBasicAuth(username,password))
            st.write(r.json())
    if tab == "Users":
        st.write("Admin can view/manage users via DB (future enhancement).")
