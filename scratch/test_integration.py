"""
test_integration.py
Automated integration test for MEDExplain AI backend and database logic.
"""

import os
import sys
sys.path.insert(0, os.path.abspath('.'))

import json
import sqlite3
from app import app, init_db, DB_PATH
# pyrefly: ignore [missing-import]
from werkzeug.security import check_password_hash

def run_tests():
    print("--- Starting MEDExplain AI Integration Tests ---")
    
    # Initialize DB
    init_db()
    client = app.test_client()
    
    # 1. Test Landing Page
    res = client.get("/")
    assert res.status_code == 200, f"Landing page failed: {res.status_code}"
    print("[OK] Landing page test passed")
    
    # 2. Test User Signup
    signup_data = {
        "name": "Padma Reddy",
        "email": "padma.test@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    }
    res = client.post("/signup", data=signup_data, follow_redirects=True)
    assert res.status_code == 200, f"Signup failed: {res.status_code}"
    print("[OK] User signup test passed")

    # 3. Test Duplicate Signup Error
    res = client.post("/signup", data=signup_data, follow_redirects=True)
    assert b"An account with this email already exists" in res.data
    print("[OK] Duplicate signup validation passed")
    
    # 4. Test User Logout & Login
    client.get("/logout", follow_redirects=True)
    login_data = {
        "email": "padma.test@example.com",
        "password": "Password123!",
        "remember": "1"
    }
    res = client.post("/login", data=login_data, follow_redirects=True)
    assert res.status_code == 200, f"Login failed: {res.status_code}"
    assert b"Good" in res.data or b"Welcome" in res.data
    print("[OK] User login and personalized greeting test passed")

    # 5. Test Synthetic Demo Report Analysis
    res = client.post("/analyze-demo", json={"language": "te"}, follow_redirects=True)
    data = res.get_json()
    assert data and data.get("success") is True, f"Demo analysis failed: {data}"
    report_id = data.get("report_id")
    print(f"[OK] Synthetic demo report analysis passed. Report ID: {report_id}")

    # 6. Test Result View Page
    res = client.get(f"/result/{report_id}")
    assert res.status_code == 200, f"View result failed: {res.status_code}"
    assert b"What does this report say?" in res.data
    print("[OK] Doctor-style structured explanation view passed")

    # 7. Test User History Isolation & Fetch
    res = client.get("/api/history")
    hist_json = res.get_json()
    assert hist_json and len(hist_json.get("history", [])) > 0
    print("[OK] User report history retrieval passed")

    # 8. Test Delete Report
    res = client.delete(f"/api/history/{report_id}")
    assert res.status_code == 200
    print("[OK] Report deletion passed")

    print("==========================================")
    print(" ALL INTEGRATION TESTS PASSED SUCCESSFULLY! ")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
