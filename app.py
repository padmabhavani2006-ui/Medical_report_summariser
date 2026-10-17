"""
app.py
Main Flask application for MEDExplain AI - Medical Report Explanation Assistant.
Handles user authentication (email/password & Google OAuth), multi-format report parsing
(PDF, Medical Images via OCR, Text), Gemini AI orchestration, user profile, and report history.
"""

import os
import re
import uuid
import json
import sqlite3
import datetime
import logging
from functools import wraps
# pyrefly: ignore [missing-import]
from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    session, jsonify, send_file, abort
)
# pyrefly: ignore [missing-import]
from werkzeug.utils import secure_filename
# pyrefly: ignore [missing-import]
from werkzeug.security import generate_password_hash, check_password_hash

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
load_dotenv()

from report_parser import (
    extract_text_from_pdf,
    extract_text_from_image,
    ExtractionError
)
from ai_engine import explain_medical_report, AIEngineError, LANGUAGE_NAMES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("medexplain_app")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "medexplain_secure_secret_key_2026_prod")

# Configure upload folder and limits
UPLOAD_FOLDER = os.path.join(app.root_path, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
ALLOWED_EXTENSIONS = {"pdf"}.union(ALLOWED_IMAGE_EXTENSIONS)

DB_PATH = os.path.join(app.root_path, "database.db")


def init_db():
    """Initializes SQLite database tables for users and user-isolated report history."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    google_id TEXT,
                    preferred_language TEXT DEFAULT 'en',
                    profile_photo TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Report history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS report_history (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    user_email TEXT,
                    filename TEXT NOT NULL,
                    file_type TEXT DEFAULT 'pdf',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    language TEXT DEFAULT 'en',
                    understanding_score INTEGER DEFAULT 85,
                    summary TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            # Schema Migration Check
            cursor.execute("PRAGMA table_info(report_history)")
            cols = [row[1] for row in cursor.fetchall()]
            if "file_type" not in cols:
                cursor.execute("ALTER TABLE report_history ADD COLUMN file_type TEXT DEFAULT 'pdf'")
            conn.commit()
    except sqlite3.DatabaseError as e:
        logger.error(f"Database init error: {str(e)}")



# Initialize database
init_db()


def get_db():
    """Returns sqlite connection with dictionary row access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_greeting(user_name: str) -> str:
    """Generates a natural, warm, personalized greeting based on current time."""
    current_hour = datetime.datetime.now().hour
    first_name = user_name.split()[0] if user_name else "there"
    
    if 5 <= current_hour < 12:
        return f"Good morning, {first_name} ☀️"
    elif 12 <= current_hour < 17:
        return f"Good afternoon, {first_name} 👋"
    else:
        return f"Good evening, {first_name} 🌿"


def allowed_file(filename: str) -> bool:
    """Validates file extension for PDF and medical image uploads."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_type(filename: str) -> str:
    """Returns 'pdf' or 'image' based on extension."""
    ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return "image"
    return "pdf"


def login_required(f):
    """Decorator requiring an authenticated user session for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get("user")
        if not user:
            if request.is_json:
                return jsonify({"error": "Authentication required. Please sign in."}), 401
            flash("Please sign in to access your MEDExplain AI dashboard.", "info")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# -----------------------------------------------------------------------------
# Auth & User Account Routes
# -----------------------------------------------------------------------------

@app.route("/")
def index():
    """Landing page showcasing product features and medical disclaimer."""
    user = session.get("user")
    if user:
        return redirect(url_for("dashboard"))
    return render_template("landing.html", user=user)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Handles new user account registration."""
    if session.get("user"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Validation checks
        if not name or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return render_template("signup.html", name=name, email=email)

        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "danger")
            return render_template("signup.html", name=name, email=email)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "warning")
            return render_template("signup.html", name=name, email=email)

        # Check existing email
        db = get_db()
        existing_user = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing_user:
            flash("An account with this email already exists. Please sign in.", "warning")
            return render_template("signup.html", name=name, email=email)

        # Create user with hashed password
        user_id = str(uuid.uuid4())
        pwd_hash = generate_password_hash(password)

        try:
            db.execute(
                "INSERT INTO users (id, name, email, password_hash, preferred_language) VALUES (?, ?, ?, ?, 'en')",
                (user_id, name, email, pwd_hash)
            )
            db.commit()

            # Auto log in user after signup
            session["user"] = {
                "uid": user_id,
                "name": name,
                "email": email,
                "preferred_language": "en",
                "photo": None
            }
            flash(f"Welcome to MEDExplain AI, {name}!", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            logger.error(f"Signup DB error: {str(e)}")
            flash("Something went wrong while creating your account. Please try again.", "danger")
            return render_template("signup.html", name=name, email=email)

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handles user sign in with email and password."""
    if session.get("user"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember")

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template("login.html", email=email)

        db = get_db()
        user_row = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if not user_row or not user_row["password_hash"] or not check_password_hash(user_row["password_hash"], password):
            flash("Email or password is incorrect.", "danger")
            return render_template("login.html", email=email)

        # Successful login
        session.permanent = bool(remember)
        session["user"] = {
            "uid": user_row["id"],
            "name": user_row["name"],
            "email": user_row["email"],
            "preferred_language": user_row["preferred_language"] or "en",
            "photo": user_row["profile_photo"]
        }
        flash(f"Welcome back, {user_row['name']}!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Forgot password interface and email reset simulation."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        flash("If an account exists with this email, password reset instructions have been sent.", "info")
        return redirect(url_for("login"))
    return render_template("forgot_password.html")


@app.route("/auth/google")
def google_auth():
    """
    Initiates Google OAuth 2.0 flow or fallback authentication.
    """
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
    if not client_id:
        flash("Google Sign-In requires configuring GOOGLE_CLIENT_ID in environment variables. You can sign in using email/password.", "info")
        return redirect(url_for("login"))

    # If configured, redirect to Google OAuth login
    redirect_uri = url_for("google_callback", _external=True)
    google_oauth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&redirect_uri={redirect_uri}&"
        f"response_type=code&scope=openid%20email%20profile"
    )
    return redirect(google_oauth_url)


@app.route("/auth/google/callback")
def google_callback():
    """Handles OAuth 2.0 callback from Google."""
    code = request.args.get("code")
    if not code:
        flash("Google authentication was cancelled.", "warning")
        return redirect(url_for("login"))

    client_id = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret:
        flash("Google OAuth credentials missing on server.", "danger")
        return redirect(url_for("login"))

    try:
        import requests
        # Exchange code for tokens
        token_resp = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": url_for("google_callback", _external=True)
            },
            timeout=10
        )
        token_json = token_resp.json()
        access_token = token_json.get("access_token")

        if not access_token:
            flash("Could not obtain access token from Google.", "danger")
            return redirect(url_for("login"))

        # Fetch user info
        userinfo_resp = requests.get(
            "https://www.googleapis.com/userinfo/v2/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        uinfo = userinfo_resp.json()

        google_id = uinfo.get("id")
        email = uinfo.get("email", "").lower()
        name = uinfo.get("name") or email.split("@")[0]
        picture = uinfo.get("picture")

        db = get_db()
        existing = db.execute("SELECT * FROM users WHERE email = ? OR google_id = ?", (email, google_id)).fetchone()

        if existing:
            user_id = existing["id"]
            db.execute("UPDATE users SET google_id = ?, profile_photo = COALESCE(profile_photo, ?) WHERE id = ?", (google_id, picture, user_id))
            db.commit()
            pref_lang = existing["preferred_language"] or "en"
        else:
            user_id = str(uuid.uuid4())
            db.execute(
                "INSERT INTO users (id, name, email, google_id, profile_photo, preferred_language) VALUES (?, ?, ?, ?, ?, 'en')",
                (user_id, name, email, google_id, picture)
            )
            db.commit()
            pref_lang = "en"

        session["user"] = {
            "uid": user_id,
            "name": name,
            "email": email,
            "preferred_language": pref_lang,
            "photo": picture
        }
        flash(f"Signed in as {name}", "success")
        return redirect(url_for("dashboard"))

    except Exception as e:
        logger.error(f"Google OAuth callback error: {str(e)}")
        flash("Something went wrong while signing you in with Google. Please try again.", "danger")
        return redirect(url_for("login"))


@app.route("/logout", methods=["GET", "POST"])
def logout():
    """Clears user session and redirects to landing page."""
    session.clear()
    if request.is_json:
        return jsonify({"success": True, "redirect": url_for("index")})
    flash("You have been signed out.", "success")
    return redirect(url_for("index"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """User profile management (update name, preferred language)."""
    user = session.get("user")
    user_id = user["uid"] # pyright: ignore[reportOptionalSubscript]
    db = get_db()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        preferred_language = request.form.get("preferred_language", "en")

        if name:
            db.execute(
                "UPDATE users SET name = ?, preferred_language = ? WHERE id = ?",
                (name, preferred_language, user_id)
            )
            db.commit()
            session["user"]["name"] = name
            session["user"]["preferred_language"] = preferred_language
            flash("Profile updated successfully.", "success")
            return redirect(url_for("profile"))

    user_data = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    report_count = db.execute("SELECT COUNT(*) as count FROM report_history WHERE user_id = ?", (user_id,)).fetchone()["count"]

    return render_template(
        "profile.html",
        user=session.get("user"),
        user_data=user_data,
        report_count=report_count,
        languages=LANGUAGE_NAMES
    )


# -----------------------------------------------------------------------------
# Main Application Dashboard & Reports
# -----------------------------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    """Personalized healthcare dashboard."""
    user = session.get("user")
    user_id = user["uid"] # pyright: ignore[reportOptionalSubscript]

    greeting = get_greeting(user.get("name", "")) # type: ignore
    history_items = get_user_history(user_id)

    return render_template(
        "dashboard.html",
        user=user,
        greeting=greeting,
        history=history_items,
        languages=LANGUAGE_NAMES
    )


@app.route("/result/<report_id>")
@login_required
def view_result(report_id):
    """Displays structured doctor-style explanation for a report."""
    user = session.get("user")
    user_id = user["uid"] # pyright: ignore[reportOptionalSubscript]

    report = get_report_by_id(report_id, user_id)
    if not report:
        flash("Report not found or you do not have permission to view it.", "warning")
        return redirect(url_for("dashboard"))

    try:
        report_data = json.loads(report["result_json"])
    except Exception:
        flash("Could not parse report data.", "danger")
        return redirect(url_for("dashboard"))

    return render_template(
        "result.html",
        report=report,
        data=report_data,
        languages=LANGUAGE_NAMES,
        user=user
    )


@app.route("/about")
def about():
    """About & Educational Safety page."""
    user = session.get("user")
    return render_template("about.html", user=user)


@app.route("/history")
@login_required
def history_page():
    """Dedicated report history page with isolated user access."""
    user = session.get("user")
    user_id = user["uid"] # pyright: ignore[reportOptionalSubscript]
    history_items = get_user_history(user_id)
    return render_template("history.html", user=user, history=history_items, languages=LANGUAGE_NAMES)


# -----------------------------------------------------------------------------
# Report Analysis API
# -----------------------------------------------------------------------------

@app.route("/analyze", methods=["POST"])
@login_required
def analyze_report():
    """
    Handles PDF, Image (OCR), or Text medical report uploads and triggers Gemini AI analysis.
    """
    user = session.get("user")
    user_id = user["uid"] # pyright: ignore[reportOptionalSubscript]
    user_email = user.get("email", "") # type: ignore

    language = request.form.get("language", user.get("preferred_language", "en")) # pyright: ignore[reportOptionalMemberAccess]
    if language not in LANGUAGE_NAMES:
        language = "en"

    input_mode = request.form.get("input_mode", "file")
    text_content = request.form.get("text_content", "").strip()

    extracted_text = ""
    filename_recorded = "Medical_Report_Text.txt"
    file_type = "text"
    temp_path = None

    if input_mode == "text" or (not request.files and text_content):
        if not text_content:
            return jsonify({"success": False, "error": "Please enter or paste your medical report text before analyzing."}), 400
        extracted_text = text_content
        filename_recorded = "Pasted Medical Text"
        file_type = "text"

    else:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file uploaded. Please select a PDF or image report."}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected. Please select a medical report file."}), 400

        if not allowed_file(file.filename): # pyright: ignore[reportArgumentType]
            return jsonify({
                "success": False,
                "error": "Unsupported file format. Please upload a PDF (.pdf) or image (.jpg, .jpeg, .png, .webp)."
            }), 400

        file_type = get_file_type(file.filename) # pyright: ignore[reportArgumentType]
        filename_recorded = secure_filename(file.filename) # pyright: ignore[reportArgumentType]
        temp_filename = f"{uuid.uuid4().hex}_{filename_recorded}"
        temp_path = os.path.join(app.config["UPLOAD_FOLDER"], temp_filename)

        try:
            file.save(temp_path)
        except Exception as e:
            return jsonify({"success": False, "error": f"Failed to save upload: {str(e)}"}), 500

        try:
            if file_type == "pdf":
                extracted_text = extract_text_from_pdf(temp_path)
                if "scanned images" in extracted_text.lower():
                    # Attempt multimodal image vision via Gemini
                    extracted_text = "Medical report scanned document image."
            else:
                # Image file
                extracted_text = extract_text_from_image(temp_path)
                if not extracted_text:
                    # Provide image path directly to Gemini vision
                    extracted_text = "Medical report image file."

        except ExtractionError as ee:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({"success": False, "error": str(ee)}), 422

    # Check minimum text check
    if not extracted_text or (len(extracted_text.strip()) < 10 and not temp_path):
        return jsonify({
            "success": False,
            "error": "We couldn't read enough text from this input. Please upload a clearer report or paste complete text."
        }), 422

    try:
        # Explain report via Gemini AI
        ai_result = explain_medical_report(extracted_text, language=language, image_path=temp_path if file_type == "image" else None)

        # Store in DB with isolated user ownership
        report_id = str(uuid.uuid4().hex[:12])
        save_report_history(
            report_id=report_id,
            user_id=user_id,
            user_email=user_email,
            filename=filename_recorded,
            file_type=file_type,
            language=language,
            understanding_score=ai_result.get("understanding_score", 88),
            summary=ai_result.get("summary", "Analysis completed."),
            result_json=json.dumps(ai_result)
        )

        return jsonify({
            "success": True,
            "report_id": report_id,
            "redirect_url": url_for("view_result", report_id=report_id)
        })

    except AIEngineError as ae:
        logger.error(f"AI Engine Error: {str(ae)}")
        return jsonify({"success": False, "error": "We couldn't connect to the analysis service. Please check your connection and try again."}), 502
    except Exception as e:
        logger.error(f"Unexpected analysis failure: {str(e)}")
        return jsonify({"success": False, "error": "Something went wrong while processing your report. Please try again."}), 500
    finally:
        # Secure cleanup
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


@app.route("/analyze-demo", methods=["POST"])
@login_required
def analyze_demo():
    """1-Click Instant Analysis using synthetic sample report."""
    user = session.get("user")
    user_id = user["uid"] # pyright: ignore[reportOptionalSubscript]
    user_email = user.get("email", "") # type: ignore

    data = request.get_json(silent=True) or {}
    language = data.get("language") or request.form.get("language", "en")
    if language not in LANGUAGE_NAMES:
        language = "en"

    demo_pdf_path = os.path.join(app.root_path, "sample_medical_report.pdf")
    if not os.path.exists(demo_pdf_path):
        from generate_sample_pdf import generate_sample_pdf
        generate_sample_pdf(demo_pdf_path)

    try:
        extracted_text = extract_text_from_pdf(demo_pdf_path)
        ai_result = explain_medical_report(extracted_text, language=language)

        report_id = str(uuid.uuid4().hex[:12])
        save_report_history(
            report_id=report_id,
            user_id=user_id,
            user_email=user_email,
            filename="Sample_Blood_Test_Report.pdf (Synthetic Demo)",
            file_type="pdf",
            language=language,
            understanding_score=ai_result.get("understanding_score", 90),
            summary=ai_result.get("summary", "Demo analysis completed."),
            result_json=json.dumps(ai_result)
        )

        return jsonify({
            "success": True,
            "report_id": report_id,
            "redirect_url": url_for("view_result", report_id=report_id)
        })
    except Exception as e:
        logger.error(f"Demo analysis error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to analyze demo report."}), 500


@app.route("/api/history", methods=["GET"])
@login_required
def api_get_history():
    """Returns isolated user report history."""
    user = session.get("user")
    items = get_user_history(user["uid"]) # pyright: ignore[reportOptionalSubscript]
    return jsonify({"success": True, "history": items})


@app.route("/api/history/<report_id>", methods=["DELETE", "POST"])
@login_required
def api_delete_history(report_id):
    """Deletes a report history item belonging to the current logged-in user."""
    user = session.get("user")
    user_id = user["uid"] # pyright: ignore[reportOptionalSubscript]

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM report_history WHERE id = ? AND user_id = ?", (report_id, user_id))
        conn.commit()

    if request.is_json or request.method == "DELETE":
        return jsonify({"success": True, "message": "Report removed from history."})
    flash("Report removed from history.", "info")
    return redirect(url_for("history_page"))


@app.route("/download-sample")
def download_sample():
    """Serves sample medical PDF for testing."""
    demo_pdf_path = os.path.join(app.root_path, "sample_medical_report.pdf")
    if not os.path.exists(demo_pdf_path):
        from generate_sample_pdf import generate_sample_pdf
        generate_sample_pdf(demo_pdf_path)

    return send_file(
        demo_pdf_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="sample_medical_report.pdf"
    )


# -----------------------------------------------------------------------------
# Database Helper Functions
# -----------------------------------------------------------------------------

def save_report_history(report_id, user_id, user_email, filename, file_type, language, understanding_score, summary, result_json):
    """Saves report metadata into SQLite."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO report_history (id, user_id, user_email, filename, file_type, language, understanding_score, summary, result_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report_id, user_id, user_email, filename, file_type, language, understanding_score, summary, result_json,
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()


def get_user_history(user_id: str):
    """Fetches past report summaries strictly isolated to the specified user_id."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, filename, file_type, created_at, language, understanding_score, summary
            FROM report_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 50
        """, (user_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_report_by_id(report_id: str, user_id: str):
    """Fetches report record by ID, verifying user isolation."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM report_history
            WHERE id = ? AND user_id = ?
        """, (report_id, user_id))
        row = cursor.fetchone()
        return dict(row) if row else None


# -----------------------------------------------------------------------------
# Application Entry Point
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("MEDExplain AI - Medical Report Explanation Assistant")
    print("Running on http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True, use_reloader=False)
