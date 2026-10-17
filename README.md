# MEDExplain AI - Medical Report Explanation Assistant

MEDExplain AI is a healthcare information web application designed to help users understand complex medical laboratory reports in clear, empathetic, doctor-style language across multiple languages.

## Key Features

1. **User Authentication & Security**:
   - Secure email/password registration & login with password hashing (`werkzeug.security`).
   - "Continue with Google" OAuth 2.0 implementation.
   - Protected dashboard and user-isolated report history.
2. **Personalized User Experience**:
   - Natural, human greetings based on local time ("Good evening, Padma 🌿", "Good morning, Padma ☀️").
   - Profile management with preferred default language selection.
3. **Multi-Format Report Upload**:
   - PDF medical reports (`.pdf`).
   - Medical report photos (`.jpg`, `.jpeg`, `.png`, `.webp`) with image OCR text extraction.
   - Direct text input ("Paste or type your medical report") with character counter.
   - Live drag & drop zone with file type/size validation and thumbnail previews.
4. **Multilingual Doctor-Style Explanation**:
   - 8 Supported Languages: English, Telugu, Hindi, Tamil, Kannada, Malayalam, Bengali, Marathi.
   - Structured sections:
     - 🧾 What does this report say?
     - 🔬 Important test results
     - 🟢 Results within reference range
     - 🟠 Results that may need attention
     - 🔴 Results significantly outside reference range
     - 💡 What does this mean in simple words?
     - 👨‍⚕️ What should I discuss with my doctor?
     - ⚠️ When should I seek medical attention?
     - 📋 Questions you can ask your doctor
5. **Visual Lab Indicators**:
   - Color-coded lab status indicators (Normal 🟢, Needs attention 🟠, High 🔴, Low 🔴).
   - Test name, observed value, unit, reference range, status, and simple explanation.
6. **Isolated Report History**:
   - Private user history with search and filter controls (Date, File type, Language).
   - Delete report action.
7. **Medical Safety & Non-Diagnostic Guarantee**:
   - Educational disclaimers on every explanation.

---

## Project Structure

```
Medico/
├── app.py                      # Main Flask application & authentication routes
├── ai_engine.py                # Gemini AI orchestration & doctor-style JSON parser
├── report_parser.py            # PDF text extraction & Image OCR processing
├── database.db                 # SQLite database storing users and report history
├── generate_sample_pdf.py      # Synthetic sample PDF generator
├── sample_medical_report.pdf   # 1-click synthetic demo report
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (API Keys, Secrets)
├── .env.example                # Template for environment variables
│
├── templates/
│   ├── base.html               # Main layout header, nav, profile popover & footer
│   ├── landing.html            # Public landing page with hero & disclaimer
│   ├── login.html              # Sign In interface with Google button
│   ├── signup.html             # Account creation interface
│   ├── forgot_password.html    # Password reset interface
│   ├── dashboard.html          # Personalized dashboard with upload & recent history
│   ├── result.html             # Doctor-style structured explanation view
│   ├── history.html            # Dedicated isolated report history page
│   ├── profile.html            # User profile & language preference settings
│   └── about.html              # Educational safety & about page
│
├── static/
│   ├── css/
│   │   └── style.css           # Modern, calm healthcare design system
│   └── js/
│       └── app.js              # Drag & drop, preview, text counter & AJAX handlers
│
└── uploads/                    # Temporary secure file upload directory
```

---

## Setup & Running Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and enter your Gemini API Key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
FLASK_SECRET_KEY=your_flask_secret_key
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
```

### 3. Google OAuth Setup (Optional)
To enable "Continue with Google":
1. Go to [Google Cloud Console Credentials](https://console.cloud.google.com/apis/credentials).
2. Create an **OAuth 2.0 Client ID** (Web application).
3. Add Authorized redirect URI: `http://127.0.0.1:5000/auth/google/callback`.
4. Copy the Client ID and Client Secret into your `.env` file.

### 4. Run Application
```bash
python app.py
```
Open your browser at `http://127.0.0.1:5000`.

---

## Testing

Run automated integration tests:
```bash
python scratch/test_integration.py
```
