"""Quick diagnostic: test the full Gemini pipeline."""
import os
from dotenv import load_dotenv
load_dotenv()

import warnings
warnings.filterwarnings("ignore")

import google.generativeai as genai # type: ignore

api_key = os.environ.get("GEMINI_API_KEY", "").strip()
print("API key set:", bool(api_key))

genai.configure(api_key=api_key)

# Test 1: basic call
print("\n--- Test 1: basic generate ---")
try:
    model = genai.GenerativeModel("gemini-3.6-flash")
    resp = model.generate_content("Say OK in one word")
    print("PASS:", resp.text.strip())
except Exception as e:
    print("FAIL:", e)

# Test 2: with system_instruction + JSON mime type
print("\n--- Test 2: system_instruction + response_mime_type=application/json ---")
try:
    model = genai.GenerativeModel(
        model_name="gemini-3.6-flash",
        system_instruction="You return valid JSON only.",
        generation_config={
            "temperature": 0.2,
            "response_mime_type": "application/json"
        }
    )
    resp = model.generate_content('Return this JSON exactly: {"status": "ok", "value": 42}')
    print("PASS:", resp.text.strip()[:120])
except Exception as e:
    print("FAIL:", e)

# Test 3: full medical report prompt (short)
print("\n--- Test 3: full medical prompt (short) ---")
SAMPLE = """
Patient: John Doe | Age: 45 | Date: 2026-09-01
Test: Hemoglobin | Result: 10.2 g/dL | Reference: 13.0-17.0 g/dL
Test: Fasting Glucose | Result: 105 mg/dL | Reference: 70-100 mg/dL
"""
try:
    from ai_engine import explain_medical_report
    result = explain_medical_report(SAMPLE, language="en")
    print("PASS: summary =", result.get("summary", "")[:80])
    print("      tests found:", len(result.get("tests", [])))
except Exception as e:
    print("FAIL:", e)
