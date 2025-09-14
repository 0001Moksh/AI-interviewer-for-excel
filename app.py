import os
import logging
import re
import datetime
import pandas as pd
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, redirect, url_for, abort
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import FieldFilter  # Added for Firestore query
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uuid
import random
import string
from datetime import timedelta
import google.auth.exceptions
import json
import base64
import requests
import io  # Added for StringIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(BASE_DIR, "templates")
app = Flask(__name__, template_folder=template_dir)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")
app.permanent_session_lifetime = timedelta(minutes=30)

# Load environment variables
load_dotenv()
GEMINI_API_KEYS = [
    os.getenv("GEMINI_API_KEY1"),
    os.getenv("GEMINI_API_KEY2"),
    os.getenv("GEMINI_API_KEY3"),
    os.getenv("GEMINI_API_KEY4")
]
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# Validate critical environment variables
if not any(GEMINI_API_KEYS) or not EMAIL_USER or not EMAIL_PASS:
    raise ValueError("Missing critical environment variables: GEMINI_API_KEYS, EMAIL_USER, or EMAIL_PASS")

# Google Sheet configuration
SHEET_ID = "1C8WBBdpZYdbiCTh9_GgTgCG-wjIl4YZj4EnxP689R7U"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

# Initialize Firebase
db = None
try:
    cred_path = os.path.join(BASE_DIR, "firebase-adminsdk.json")
    logger.info(f"Loading credentials from: {cred_path}")
    if not os.path.exists(cred_path):
        logger.warning(f"Missing {cred_path}. Checking environment variable.")
        firebase_json_b64 = os.getenv("FIREBASE_CREDENTIALS_JSON")
        if firebase_json_b64:
            try:
                cred_dict = json.loads(base64.b64decode(firebase_json_b64).decode('utf-8'))
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                db = firestore.client()
                logger.info("Firebase initialized successfully from env.")
            except Exception as e:
                logger.error(f"Firebase init from env failed: {str(e)}")
        else:
            logger.warning("No Firebase credentials found (file or env). Proceeding without Firebase.")
    else:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        logger.info("Firebase initialized successfully from file.")
except google.auth.exceptions.RefreshError as e:
    logger.error(f"Firebase authentication failed: Invalid JWT Signature. Check firebase-adminsdk.json or FIREBASE_CREDENTIALS_JSON. Error: {str(e)}")
    logger.warning("Proceeding without Firebase initialization.")
except Exception as e:
    logger.error(f"Error initializing Firebase: {str(e)}")
    logger.warning("Proceeding without Firebase initialization.")

# Load questions lazily from Google Sheet
def get_questions():
    if not hasattr(get_questions, 'cache'):
        try:
            # Fetch CSV from Google Sheet (public export)
            response = requests.get(SHEET_URL)
            response.raise_for_status()  # Raise error if fetch fails
            df = pd.read_csv(io.StringIO(response.text))  # Use io.StringIO
            # Validate columns
            if 'q' not in df.columns or 'exp' not in df.columns:
                raise ValueError("Google Sheet must have 'q' and 'exp' columns.")
            df = df[['q', 'exp']].dropna()  # Select required columns, drop empty rows
            get_questions.cache = df.to_dict(orient="records")
            logger.info(f"Loaded {len(get_questions.cache)} questions from Google Sheet.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch Google Sheet: {str(e)}. Using empty list.")
            get_questions.cache = []
        except ValueError as e:
            logger.error(f"Google Sheet format error: {str(e)}. Using empty list.")
            get_questions.cache = []
        except Exception as e:
            logger.error(f"Unexpected error loading questions from Google Sheet: {str(e)}. Using empty list.")
            get_questions.cache = []
    return get_questions.cache

questions = get_questions()
num_questions = len(questions)

MAX_SCORE = 10  # Fixed max score per question

# Function to generate random user_id with fallback
def generate_user_id(name):
    base = name.replace(" ", "").lower()[:10]
    counter = 1
    while True:
        if counter == 1:
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        else:
            random_suffix = f"{counter:02d}{''.join(random.choices(string.ascii_lowercase + string.digits, k=4))}"
        user_id = f"{base}{random_suffix}"
        if len(user_id) > 20:
            user_id = user_id[:20]
        if not db or not db.collection("users").document(user_id).get().exists:
            return user_id
        counter += 1
        if counter > 100:
            raise Exception("Failed to generate unique user_id after 100 attempts.")

# Email sending function
# Email sending function
def send_summary_email(user_email, user_name, user_id, summary_data):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = user_email
        msg["Subject"] = "AI Interview Summary"

        # Render the HTML template
        html_body = render_template(
            "summary_mail.html",
            user_name=user_name,
            user_id=user_id,
            summary_data=summary_data,
            max_score=MAX_SCORE,
            current_year=datetime.datetime.now().year
        )

        # Attach HTML content
        msg.attach(MIMEText(html_body, "html"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, user_email, msg.as_string())
        server.quit()
        logger.info(f"Summary email sent to {user_email}")
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")

# Gemini evaluation function
def evaluate_answer(question, expected, user_answer, history):
    if not any(GEMINI_API_KEYS):
        logger.error("No valid Gemini API keys available")
        return f"Score: 0/{MAX_SCORE}\nFeedback: API configuration error."
    current_time = datetime.datetime.now().strftime("%H:%M")
    current_date = datetime.datetime.now().strftime("%d %B %Y, %A")

    prompt = f"""
    Current Time: {current_time} | Date: {current_date}
    Question: {question}
    Expected Answer: {expected}
    User Answer: {user_answer}

    Evaluate the user's answer for accuracy, completeness, and clarity.
    Score from 0-{MAX_SCORE} ({MAX_SCORE}=perfect). Provide 1-2 sentence feedback.

    Format:
    Score: X/{MAX_SCORE}
    Feedback: [text]
    """

    if not user_answer:
        return f"Score: 0/{MAX_SCORE}\nFeedback: Empty answer."

    for api_key in GEMINI_API_KEYS:
        if not api_key:
            continue
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction="""You are an expert Excel Mock Interviewer for finance, ops, and analytics roles. 
                Evaluate responses objectively and provide constructive feedback. 
                Always output: Score: X/10\nFeedback: [1-2 sentences]."""
            )
            chat_session = model.start_chat(history=history)
            response = chat_session.send_message(prompt)
            model_response = response.text.strip()

            history.append({"role": "user", "parts": [prompt]})
            history.append({"role": "model", "parts": [model_response]})
            return model_response
        except Exception as e:
            logger.warning(f"Error with API key {api_key[:10]}...: {str(e)}")
            continue

    return f"Score: 0/{MAX_SCORE}\nFeedback: All API keys failed."

# Middleware to validate session ID
def validate_session_id(session_id):
    if not db:
        logger.warning("Firebase not initialized, skipping session validation")
        return True
    try:
        doc = db.collection("sessions").document(session_id).get()
        if not doc.exists:
            logger.warning(f"Session {session_id} does not exist")
        return doc.exists
    except Exception as e:
        logger.error(f"Error validating session ID {session_id}: {str(e)}")
        return False

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route("/")
def home():
    session.clear()
    return render_template("login.html", num_questions=num_questions)

@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email", "").strip()
    name = request.form.get("name", "").strip()

    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return render_template("login.html", error="Invalid email format.", num_questions=num_questions)
    if not name or len(name.strip()) < 2:
        return render_template("login.html", error="Name must be at least 2 characters.", num_questions=num_questions)

    try:
        if db:
            email_query = db.collection("users").where(filter=FieldFilter("email", "==", email)).get()
            if email_query:
                user_doc = email_query[0]
                user_id = user_doc.id
                if user_doc.to_dict().get("name") != name:
                    db.collection("users").document(user_id).update({"name": name})
                logger.info(f"User {user_id} logged in.")
            else:
                user_id = generate_user_id(name)
                db.collection("users").document(user_id).set({
                    "name": name,
                    "email": email,
                    "created_at": firestore.SERVER_TIMESTAMP
                })
                logger.info(f"New user created with User ID: {user_id}")
        else:
            user_id = generate_user_id(name)  # Generate locally if no Firebase
            logger.info(f"User {user_id} created locally (no Firebase)")

        session["user_id"] = user_id
        session["user_email"] = email
        session["user_name"] = name
        session["session_id"] = str(uuid.uuid4())
        if db:
            db.collection("sessions").document(session["session_id"]).set({
                "user_id": user_id,
                "created_at": firestore.SERVER_TIMESTAMP
            })
        logger.info(f"Session {session['session_id']} created for user {user_id}")
        return redirect(url_for("guidelines", session_id=session["session_id"]))
    except Exception as e:
        logger.error(f"Login/Registration error: {str(e)}")
        return render_template("login.html", error=f"Registration failed: {str(e)[:100]}...", num_questions=num_questions)

@app.route("/guidelines/<session_id>")
def guidelines(session_id):
    if session.get("session_id") != session_id or not validate_session_id(session_id):
        logger.error(f"Invalid session access attempt for session_id: {session_id}")
        abort(403, description="Invalid session.")
    return render_template("guidelines.html", session_id=session_id)

@app.route("/start/<session_id>")
def start(session_id):
    if session.get("session_id") != session_id or not validate_session_id(session_id):
        logger.error(f"Invalid session access attempt for session_id: {session_id}")
        abort(403, description="Invalid or tampered session URL.")
    session["step"] = 0
    session["scores"] = []
    session["feedbacks"] = []
    session["questions_asked"] = []
    session["history"] = [{"role": "model", "parts": ["Starting Excel interview session."]}]
    logger.info(f"Interview started for session {session_id}")
    return redirect(url_for("interview", session_id=session_id))

@app.route("/interview/<session_id>", methods=["GET", "POST"])
def interview(session_id):
    if session.get("step") is None:
        logger.error(f"Session step not initialized for session {session_id}")
        return redirect(url_for("start", session_id=session_id))
    if session.get("session_id") != session_id or not validate_session_id(session_id):
        logger.error(f"Invalid session access attempt for session_id: {session_id}")
        abort(403, description="Invalid or tampered session URL.")

    step = session.get("step", 0)
    if step >= num_questions:
        return redirect(url_for("summary", session_id=session_id))

    q_data = questions[step]
    question_text = q_data["q"]
    logger.info(f"Displaying question {step + 1} for session {session_id}")

    if request.method == "POST":
        user_input = request.form.get("answer", "").strip()
        if user_input:
            eval_result = evaluate_answer(q_data["q"], q_data["exp"], user_input, session["history"])
            try:
                score_str = eval_result.split("Score: ")[1].split(f"/{MAX_SCORE}")[0].strip()
                score = int(float(score_str))
                feedback = eval_result.split("Feedback: ")[1].strip()
            except Exception as e:
                logger.error(f"Error parsing evaluation for session {session_id}: {str(e)}")
                score = 0
                feedback = "Evaluation failed."
            session["scores"].append(score)
            session["feedbacks"].append(feedback)
            session["questions_asked"].append(question_text)
            session["step"] = step + 1
            if session["step"] >= num_questions:
                return redirect(url_for("summary", session_id=session_id))
            else:
                return redirect(url_for("interview", session_id=session_id))

    return render_template("interview.html", step=step+1, question=question_text, num_questions=num_questions, session_id=session_id)

@app.route("/summary/<session_id>")
def summary(session_id):
    if session.get("session_id") != session_id or not validate_session_id(session_id):
        logger.error(f"Invalid session access attempt for session_id: {session_id}")
        abort(403, description="Invalid or tampered session URL.")

    scores = session.get("scores", [])
    feedbacks = session.get("feedbacks", [])
    questions_asked = session.get("questions_asked", [])
    user_id = session.get("user_id")
    user_email = session.get("user_email")
    user_name = session.get("user_name")

    if not scores:
        return redirect(url_for("home"))

    avg_score = sum(scores) / len(scores) if scores else 0
    basics_avg = sum(scores[:3]) / min(3, len(scores)) if scores else 0
    advanced_avg = sum(scores[6:]) / len(scores[6:]) if len(scores) > 6 else 0

    strengths = "Strong in basics" if basics_avg > 7 else "Needs basics improvement"
    weaknesses = "Improve advanced skills" if advanced_avg < 7 else "Good advanced skills"
    detailed_feedback = list(zip(questions_asked, feedbacks, scores))

    # Store results in Firebase if available
    if db:
        try:
            db.collection("users").document(user_id).collection("interviews").add({
                "timestamp": firestore.SERVER_TIMESTAMP,
                "scores": scores,
                "feedbacks": feedbacks,
                "questions": questions_asked,
                "average_score": avg_score,
                "strengths": strengths,
                "weaknesses": weaknesses
            })
        except Exception as e:
            logger.error(f"Error saving to Firestore: {str(e)}")

    # Send summary email
    summary_data = {
        "avg_score": avg_score,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "detailed_feedback": detailed_feedback
    }
    send_summary_email(user_email, user_name, user_id, summary_data)

    return render_template(
        "summary.html",
        avg_score=avg_score,
        strengths=strengths,
        weaknesses=weaknesses,
        detailed_feedback=detailed_feedback,
        max_score=MAX_SCORE,
        num_questions=num_questions
    )

if __name__ == "__main__":
    app.run(debug=True)