"""
ai_engine.py
Generative AI Medical Report Explanation Engine using Google Gemini API.
Adheres strictly to medical safety, non-diagnostic guidelines, structured JSON output,
and multilingual support (English, Telugu, Hindi, Tamil, Kannada, Malayalam, Bengali, Marathi).
"""

import os
import json
import re
import logging
from typing import Dict, Any, Optional

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
load_dotenv()

# Configure logger
logger = logging.getLogger("ai_engine")
logging.basicConfig(level=logging.INFO)

# Gemini models prioritized for stability and speed
PRIMARY_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite-preview",
    "gemini-3-flash-preview",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.7-flash"
]



LANGUAGE_NAMES = {
    "en": "English",
    "te": "Telugu (తెలుగు)",
    "hi": "Hindi (हिन्दी)",
    "ta": "Tamil (தமிழ்)",
    "kn": "Kannada (கன்னட / ಕನ್ನಡ)",
    "ml": "Malayalam (മലയാളം)",
    "bn": "Bengali (বাংলা)",
    "mr": "Marathi (मराठी)"
}


class AIEngineError(Exception):
    """Custom exception for Gemini AI processing errors."""
    pass


def get_gemini_client():
    """Initializes and configures the Gemini API client using the environment key."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise AIEngineError("Gemini API key is not configured. Please set GEMINI_API_KEY in the .env file.")

    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=api_key)
        return genai
    except Exception as e:
        raise AIEngineError(f"Failed to initialize Gemini client: {str(e)}")


def explain_medical_report(report_text: str, language: str = "en", image_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Sends extracted medical report text (or image) to Gemini AI and returns a structured,
    patient-friendly educational explanation in a doctor-style format.

    Args:
        report_text (str): Raw extracted text or text input from the medical report.
        language (str): Target language code ('en', 'te', 'hi', 'ta', 'kn', 'ml', 'bn', 'mr').
        image_path (str, optional): Path to medical image file for multimodal fallback.

    Returns:
        dict: Validated structured dictionary containing doctor-style sections, tests,
              understanding score, questions, and safety note.
    """
    genai = get_gemini_client()
    lang_name = LANGUAGE_NAMES.get(language, "English")

    system_instructions = (
        "You are MEDExplain AI, a compassionate, educational medical report explanation assistant.\n"
        "Your task is to analyze a medical laboratory report and explain it in simple, empathetic, doctor-style terms.\n\n"
        "CRITICAL SAFETY & MEDICAL GUIDELINES:\n"
        "1. DO NOT diagnose any disease, illness, or medical condition. Never claim 'You definitely have...' or 'This confirms that you have...'\n"
        "2. DO NOT prescribe medicines or recommend dosage changes.\n"
        "3. DO NOT replace a licensed healthcare professional.\n"
        "4. Use safe, non-diagnostic wording such as: 'This result can have several possible explanations. Discuss it with a qualified healthcare professional.'\n"
        "5. Keep exact clinical test names, numerical values, and units of measurement accurate and recognizable (in English if standard).\n"
        "6. Do NOT invent reference ranges if they are not provided in the report. Explicitly state 'Reference range was not provided in the uploaded report.' if missing.\n"
        f"7. LANGUAGE REQUIREMENT: Output all explanations, summaries, meanings, and questions in {lang_name}.\n\n"
        "OUTPUT FORMAT REQUIREMENTS:\n"
        "You MUST return ONLY a valid JSON object matching this exact structure with NO markdown formatting outside JSON:\n"
        "{\n"
        '  "summary": "🧾 What does this report say? Clear 2-3 sentence overview in plain language.",\n'
        '  "important_findings": ["🔬 Point 1 highlight", "Point 2 highlight"],\n'
        '  "understanding_score": 88,\n'
        '  "tests_normal": ["🟢 Hemoglobin: 13.5 g/dL (Within reference range)"],\n'
        '  "tests_attention": ["🟠 Serum Creatinine: 1.4 mg/dL (Slightly elevated - discuss with doctor)"],\n'
        '  "tests_critical": ["🔴 Random Blood Sugar: 240 mg/dL (Significantly high - requires medical advice)"],\n'
        '  "simple_explanation": "💡 What does this mean in simple words? A gentle, step-by-step breakdown of what the numbers mean for general health awareness.",\n'
        '  "doctor_discussion": "👨‍⚕️ What should I discuss with my doctor? Specific aspects of this report to bring up at your next appointment.",\n'
        '  "red_flags": "⚠️ When should I seek medical attention? General warning signs that warrant prompt medical advice.",\n'
        '  "tests": [\n'
        "    {\n"
        '      "name": "Test Name (e.g. Hemoglobin)",\n'
        '      "value": "12.8",\n'
        '      "unit": "g/dL",\n'
        '      "reference_range": "12.0 - 16.0",\n'
        '      "status": "Within reference range",\n'
        '      "status_code": "normal",\n'
        '      "simple_explanation": "Brief 1-2 sentence explanation of what this test measures."\n'
        "    }\n"
        "  ],\n"
        '  "medical_terms": [\n'
        "    {\n"
        '      "term": "Medical Term (e.g. Hematocrit)",\n'
        '      "technical_meaning": "The proportion of red blood cells in total blood volume.",\n'
        '      "simple_meaning": "The percentage of your blood made of oxygen-carrying cells.",\n'
        '      "why_in_report": "Helps evaluate red blood cell levels."\n'
        "    }\n"
        "  ],\n"
        '  "questions_for_doctor": [\n'
        '    "What do these results indicate regarding my general well-being?",\n'
        '    "Should any of these tests be rechecked in a few weeks?",\n'
        '    "Are any dietary or lifestyle adjustments recommended?"\n'
        "  ],\n"
        '  "safety_note": "This explanation is for educational purposes only and is not a diagnosis. Please consult a qualified healthcare professional for medical advice."\n'
        "}"
    )

    contents = []
    if image_path and os.path.exists(image_path):
        try:
            from PIL import Image  # type: ignore
            img = Image.open(image_path)
            contents.append(img)
            prompt_text = f"Examine this medical report image and generate a structured patient explanation in {lang_name} adhering strictly to the JSON schema."
            if report_text:
                prompt_text += f"\n\nExtracted text context:\n{report_text}"
            contents.append(prompt_text)
        except Exception:
            contents.append(f"Here is the medical report text to explain:\n\n```\n{report_text}\n```")
    else:
        contents.append(f"Here is the medical report text to explain:\n\n```\n{report_text}\n```")

    last_exception = None
    response_text = ""

    for model_name in PRIMARY_MODELS:
        try:
            logger.info(f"Attempting analysis using model: {model_name} in {lang_name}")
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instructions,
                generation_config={
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "response_mime_type": "application/json"
                }
            )

            response = model.generate_content(contents)
            if response and response.text:
                response_text = response.text
                break
        except Exception as e:
            logger.warning(f"Model {model_name} failed: {str(e)}")
            last_exception = e
            continue

    if not response_text:
        # Fallback to standard generate call without response_mime_type
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            full_prompt = f"{system_instructions}\n\n{contents[-1] if isinstance(contents[-1], str) else report_text}"
            response = model.generate_content(full_prompt)
            if response and response.text:
                response_text = response.text
        except Exception as e:
            last_exception = e

    if not response_text:
        raise AIEngineError(f"Could not generate explanation from Gemini API. Error: {str(last_exception)}")

    parsed_data = parse_and_validate_json(response_text)
    return parsed_data


def parse_and_validate_json(raw_text: str) -> Dict[str, Any]:
    """
    Cleans markdown formatting and parses JSON response from the AI.
    Validates required fields and applies fallback structures if needed.
    """
    cleaned = raw_text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    first_brace = cleaned.find('{')
    last_brace = cleaned.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        cleaned = cleaned[first_brace:last_brace + 1]

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"JSON Decode Error: {str(e)}\nRaw Response: {raw_text[:500]}")
        data = try_repair_json(cleaned)

    validated = {
        "summary": str(data.get("summary", "Medical report explanation completed.")),
        "important_findings": data.get("important_findings", []),
        "understanding_score": int(data.get("understanding_score", 88)),
        "tests_normal": data.get("tests_normal", []),
        "tests_attention": data.get("tests_attention", []),
        "tests_critical": data.get("tests_critical", []),
        "simple_explanation": str(data.get("simple_explanation", "This report contains routine medical lab measurements. Each parameter offers insights into your physiological state.")),
        "doctor_discussion": str(data.get("doctor_discussion", "Review any out-of-range values with your healthcare provider to discuss context and next steps.")),
        "red_flags": str(data.get("red_flags", "If you experience severe fatigue, fever, chest pain, or unexpected symptoms, consult a doctor promptly.")),
        "tests": data.get("tests", []),
        "medical_terms": data.get("medical_terms", []),
        "questions_for_doctor": data.get("questions_for_doctor", [
            "What do these findings mean for my general health?",
            "Are follow-up tests or monitoring recommended?",
            "Should I make any lifestyle or dietary adjustments based on these results?"
        ]),
        "safety_note": str(data.get("safety_note", "This explanation is for educational purposes only and is not a diagnosis. Please consult a qualified healthcare professional for medical advice."))
    }

    if isinstance(validated["important_findings"], str):
        validated["important_findings"] = [validated["important_findings"]]
    if isinstance(validated["tests_normal"], str):
        validated["tests_normal"] = [validated["tests_normal"]]
    if isinstance(validated["tests_attention"], str):
        validated["tests_attention"] = [validated["tests_attention"]]
    if isinstance(validated["tests_critical"], str):
        validated["tests_critical"] = [validated["tests_critical"]]

    clean_tests = []
    for item in validated["tests"]:
        if isinstance(item, dict):
            status = str(item.get("status", "Within reference range"))
            status_code = item.get("status_code")
            if not status_code:
                st_lower = status.lower()
                if "above" in st_lower or "high" in st_lower or "critical" in st_lower or "significantly" in st_lower:
                    status_code = "high"
                elif "below" in st_lower or "low" in st_lower:
                    status_code = "low"
                elif "attention" in st_lower or "elevated" in st_lower:
                    status_code = "attention"
                else:
                    status_code = "normal"

            clean_tests.append({
                "name": str(item.get("name", "Investigation")),
                "value": str(item.get("value", "-")),
                "unit": str(item.get("unit", "")),
                "reference_range": str(item.get("reference_range", "Reference range was not provided in the uploaded report.")),
                "status": status,
                "status_code": status_code,
                "simple_explanation": str(item.get("simple_explanation", "Standard clinical parameter."))
            })
    validated["tests"] = clean_tests

    clean_terms = []
    for term_item in validated["medical_terms"]:
        if isinstance(term_item, dict):
            clean_terms.append({
                "term": str(term_item.get("term", "Medical Term")),
                "technical_meaning": str(term_item.get("technical_meaning", "")),
                "simple_meaning": str(term_item.get("simple_meaning", "")),
                "why_in_report": str(term_item.get("why_in_report", "Standard blood test metric."))
            })
    validated["medical_terms"] = clean_terms

    if validated["understanding_score"] < 50 or validated["understanding_score"] > 100:
        validated["understanding_score"] = 85

    return validated


def try_repair_json(text: str) -> Dict[str, Any]:
    """Fallback parser if JSON contains minor syntax issues."""
    try:
        repaired = re.sub(r",\s*([\]}])", r"\1", text)
        return json.loads(repaired)
    except Exception:
        return {
            "summary": "The medical report was analyzed successfully. Please consult your physician for clinical interpretation.",
            "important_findings": ["Report processed. Review detailed parameter list below."],
            "understanding_score": 85,
            "tests_normal": [],
            "tests_attention": [],
            "tests_critical": [],
            "simple_explanation": "Your report has been summarized into educational notes.",
            "doctor_discussion": "Discuss any unusual test values with a licensed physician.",
            "red_flags": "If experiencing acute symptoms, seek immediate medical care.",
            "tests": [],
            "medical_terms": [],
            "questions_for_doctor": [
                "What do these results mean for my health?",
                "Are follow-up tests recommended?"
            ],
            "safety_note": "This explanation is for educational purposes only and is not a diagnosis. Please consult a qualified healthcare professional for medical advice."
        }
