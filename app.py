import os
import logging
import re
import datetime
import pandas as pd
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, redirect, url_for, abort, make_response
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import FieldFilter
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uuid
import random
import string
from datetime import timedelta
import json
import base64
import requests
import io
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
import signal
import sys

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
# Use only the first valid key to reduce API calls and internet usage
GEMINI_API_KEY = next((key for key in GEMINI_API_KEYS if key), None)
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
FIREBASE_CREDENTIALS_JSON = os.getenv("FIREBASE_CREDENTIALS_JSON")

# Validate critical environment variables
if not GEMINI_API_KEY:
    logger.error("No valid GEMINI_API_KEY provided")
    raise ValueError("Missing GEMINI_API_KEY")
if not EMAIL_USER or not EMAIL_PASS:
    logger.error("Missing EMAIL_USER or EMAIL_PASS")
    raise ValueError("Missing EMAIL_USER or EMAIL_PASS")
if not FIREBASE_CREDENTIALS_JSON:
    logger.error("Missing FIREBASE_CREDENTIALS_JSON")
    raise ValueError("Missing FIREBASE_CREDENTIALS_JSON")

# Google Sheet configuration
SHEET_ID = "1C8WBBdpZYdbiCTh9_GgTgCG-wjIl4YZj4EnxP689R7U"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

# Initialize Firebase
db = None
try:
    logger.info("Initializing Firebase from environment variable")
    cred_dict = json.loads(base64.b64decode(FIREBASE_CREDENTIALS_JSON).decode('utf-8'))
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    logger.info("Firebase initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Firebase: {str(e)}")
    raise ValueError("Failed to initialize Firebase")

# Load questions lazily from Google Sheet (cached to reduce internet usage)
def get_questions():
    if not hasattr(get_questions, 'cache'):
        try:
            response = requests.get(SHEET_URL)
            response.raise_for_status()
            df = pd.read_csv(io.StringIO(response.text))
            if 'q' not in df.columns or 'exp' not in df.columns:
                raise ValueError("Google Sheet must have 'q' and 'exp' columns")
            df = df[['q', 'exp']].dropna()
            get_questions.cache = df.to_dict(orient="records")
            logger.info(f"Loaded {len(get_questions.cache)} questions from Google Sheet")
        except Exception as e:
            logger.error(f"Error loading questions from Google Sheet: {str(e)}")
            get_questions.cache = []
    return get_questions.cache

questions = get_questions()
num_questions = len(questions)
MAX_SCORE = 10

# Sanitize input to prevent injection
def sanitize_input(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r'[<>;{}]', '', text)
    return text.strip()[:1000]  # Limit length to prevent abuse

# Generate random user_id
def generate_user_id(name):
    name = sanitize_input(name)
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
        try:
            if not db.collection("users").document(user_id).get().exists:
                return user_id
        except Exception as e:
            logger.error(f"Error checking user_id {user_id}: {str(e)}")
            counter += 1
        if counter > 100:
            raise Exception("Failed to generate unique user_id")

# Email sending function
def send_summary_email(user_email, user_name, user_id, summary_data):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = user_email
        msg["Subject"] = "AI Interview Summary"
        html_body = render_template(
            "summary_mail.html",
            user_name=user_name,
            user_id=user_id,
            summary_data=summary_data,
            max_score=MAX_SCORE,
            current_year=datetime.datetime.now().year
        )
        msg.attach(MIMEText(html_body, "html"))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, user_email, msg.as_string())
        server.quit()
        logger.info(f"Summary email sent to {user_email}")
    except Exception as e:
        logger.error(f"Error sending email to {user_email}: {str(e)}")

# Simplified LangChain-based evaluation function (no history to reduce size and API usage)
def evaluate_answer(question, expected, user_answer):
    question = sanitize_input(question)
    expected = sanitize_input(expected)
    user_answer = sanitize_input(user_answer)
    
    if not GEMINI_API_KEY:
        logger.error("No valid Gemini API key available")
        return f"Score: 0/{MAX_SCORE}\nFeedback: API configuration error"
    
    if not user_answer:
        return f"Score: 0/{MAX_SCORE}\nFeedback: Empty answer"

    # Simplified prompt without history for independent evaluation and reduced token usage
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """You are an expert Excel Mock Interviewer for finance, ops, and analytics roles. 
        Evaluate responses objectively and provide constructive feedback. 
        Always output exactly: Score: X/10\nFeedback: [1-2 sentences]"""),
        ("human", """
        Current Time: {current_time} | Date: {current_date}
        Question: {question}
        Expected Answer: {expected}
        User Answer: {user_answer}
        Evaluate the user's answer for accuracy, completeness, and clarity.
        Score from 0-{max_score} ({max_score}=perfect). Provide 1-2 sentence feedback.
        """)
    ])

    current_time = datetime.datetime.now().strftime("%H:%M")
    current_date = datetime.datetime.now().strftime("%d %B %Y, %A")

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=GEMINI_API_KEY,
            temperature=0.3
        )
        chain = prompt_template | llm
        response = chain.invoke({
            "question": question,
            "expected": expected,
            "user_answer": user_answer,
            "current_time": current_time,
            "current_date": current_date,
            "max_score": MAX_SCORE
        })
        model_response = response.content.strip()
        logger.info(f"Evaluation completed for question using Gemini API")
        return model_response
    except Exception as e:
        logger.error(f"Error with Gemini API: {str(e)}")
        return f"Score: 0/{MAX_SCORE}\nFeedback: Evaluation failed due to API error"

# Validate session ID
def validate_session_id(session_id):
    try:
        doc = db.collection("sessions").document(session_id).get()
        if not doc.exists:
            logger.warning(f"Session {session_id} does not exist")
            return False
        return True
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
    email = sanitize_input(request.form.get("email", ""))
    name = sanitize_input(request.form.get("name", ""))

    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return render_template("login.html", error="Invalid email format", num_questions=num_questions)
    if not name or len(name) < 2:
        return render_template("login.html", error="Name must be at least 2 characters", num_questions=num_questions)

    try:
        email_query = db.collection("users").where(filter=FieldFilter("email", "==", email)).get()
        if email_query:
            user_doc = email_query[0]
            user_id = user_doc.id
            if user_doc.to_dict().get("name") != name:
                db.collection("users").document(user_id).update({"name": name})
            logger.info(f"User {user_id} logged in")
        else:
            user_id = generate_user_id(name)
            db.collection("users").document(user_id).set({
                "name": name,
                "email": email,
                "created_at": firestore.SERVER_TIMESTAMP
            })
            logger.info(f"New user created with User ID: {user_id}")

        session["user_id"] = user_id
        session["user_email"] = email
        session["user_name"] = name
        session["session_id"] = str(uuid.uuid4())
        session.modified = True  # Ensure session updates
        db.collection("sessions").document(session["session_id"]).set({
            "user_id": user_id,
            "created_at": firestore.SERVER_TIMESTAMP
        })
        logger.info(f"Session {session['session_id']} created for user {user_id}")
        return redirect(url_for("guidelines", session_id=session["session_id"]))
    except Exception as e:
        logger.error(f"Login/Registration error: {str(e)}")
        return render_template("login.html", error=f"Registration failed: {str(e)[:100]}", num_questions=num_questions)

@app.route("/guidelines/<session_id>")
def guidelines(session_id):
    if session.get("session_id") != session_id or not validate_session_id(session_id):
        logger.error(f"Invalid session access attempt for session_id: {session_id}")
        abort(403, description="Invalid session")
    return render_template("guidelines.html", session_id=session_id)

@app.route("/start/<session_id>")
def start(session_id):
    if session.get("session_id") != session_id or not validate_session_id(session_id):
        logger.error(f"Invalid session access attempt for session_id: {session_id}")
        abort(403, description="Invalid or tampered session URL")
    session["step"] = 0
    session["scores"] = []
    session["feedbacks"] = []
    session["questions_asked"] = []
    session.modified = True  # Ensure session updates
    logger.info(f"Interview started for session {session_id}")
    return redirect(url_for("interview", session_id=session_id))

@app.route("/interview/<session_id>", methods=["GET", "POST"])
def interview(session_id):
    if session.get("step") is None:
        logger.error(f"Session step not initialized for session {session_id}")
        return redirect(url_for("start", session_id=session_id))
    if session.get("session_id") != session_id or not validate_session_id(session_id):
        logger.error(f"Invalid session access attempt for session_id: {session_id}")
        abort(403, description="Invalid or tampered session URL")

    step = session.get("step", 0)
    if step >= num_questions:
        return redirect(url_for("summary", session_id=session_id))

    q_data = questions[step]
    question_text = q_data["q"]
    logger.info(f"Displaying question {step + 1} for session {session_id}")

    if request.method == "POST":
        user_input = sanitize_input(request.form.get("answer", ""))
        if user_input:
            try:
                eval_result = evaluate_answer(q_data["q"], q_data["exp"], user_input)
                score_str = eval_result.split("Score: ")[1].split(f"/{MAX_SCORE}")[0].strip()
                score = int(float(score_str))
                feedback = eval_result.split("Feedback: ")[1].strip()
            except Exception as e:
                logger.error(f"Error parsing evaluation for session {session_id}: {str(e)}")
                score = 0
                feedback = "Evaluation failed"
            session["scores"].append(score)
            session["feedbacks"].append(feedback)
            session["questions_asked"].append(question_text)
            session["step"] = step + 1
            session.modified = True  # Ensure session updates
            if session["step"] >= num_questions:
                return redirect(url_for("summary", session_id=session_id))
            return redirect(url_for("interview", session_id=session_id))

    response = make_response(render_template("interview.html", step=step+1, question=question_text, num_questions=num_questions, session_id=session_id))
    session_cookie = response.headers.get("Set-Cookie")
    if session_cookie:
        cookie_size = len(session_cookie.encode("utf-8"))
        logger.info(f"Session cookie size: {cookie_size} bytes")
    return response

@app.route("/summary/<session_id>")
def summary(session_id):
    if session.get("session_id") != session_id or not validate_session_id(session_id):
        logger.error(f"Invalid session access attempt for session_id: {session_id}")
        abort(403, description="Invalid or tampered session URL")

    scores = session.get("scores", [])
    feedbacks = session.get("feedbacks", [])
    questions_asked = session.get("questions_asked", [])
    user_id = session.get("user_id")
    user_email = session.get("user_email")
    user_name = session.get("user_name")

    if not scores:
        return redirect(url_for("home"))

    try:
        avg_score = sum(scores) / len(scores)
        basics_avg = sum(scores[:3]) / min(3, len(scores)) if len(scores) >= 3 else 0
        advanced_avg = sum(scores[6:]) / len(scores[6:]) if len(scores) > 6 else 0
        strengths = "Strong in basics" if basics_avg > 7 else "Needs basics improvement"
        weaknesses = "Improve advanced skills" if advanced_avg < 7 else "Good advanced skills"
        detailed_feedback = list(zip(questions_asked, feedbacks, scores))

        # Store results in Firestore (no history needed)
        db.collection("users").document(user_id).collection("interviews").add({
            "timestamp": firestore.SERVER_TIMESTAMP,
            "scores": scores,
            "feedbacks": feedbacks,
            "questions": questions_asked,
            "average_score": avg_score,
            "strengths": strengths,
            "weaknesses": weaknesses
        })

        # Send summary email
        summary_data = {
            "avg_score": avg_score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "detailed_feedback": detailed_feedback
        }
        send_summary_email(user_email, user_name, user_id, summary_data)

        # Clear session after summary
        session.clear()
        logger.info(f"Session {session_id} cleared after summary")

        return render_template(
            "summary.html",
            avg_score=avg_score,
            strengths=strengths,
            weaknesses=weaknesses,
            detailed_feedback=detailed_feedback,
            max_score=MAX_SCORE,
            num_questions=num_questions
        )
    except Exception as e:
        logger.error(f"Error processing summary for session {session_id}: {str(e)}")
        return render_template("error.html", error="Failed to generate summary")

# Handle graceful shutdown
def handle_shutdown(signum, frame):
    logger.info("Shutting down Flask server")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

@app.route("/leaderboard")
def leaderboard():
    try:
        # Fetch all users from Firestore
        users_ref = db.collection("users").stream()
        leaderboard_data = []

        # Iterate through users and their interviews
        for user in users_ref:
            user_data = user.to_dict()
            user_id = user.id
            user_name = user_data.get("name", "Unknown")
            interviews_ref = db.collection("users").document(user_id).collection("interviews").stream()
            
            # Get the latest interview for each user
            latest_interview = None
            latest_timestamp = None
            for interview in interviews_ref:
                interview_data = interview.to_dict()
                timestamp = interview_data.get("timestamp")
                if timestamp and (latest_timestamp is None or timestamp > latest_timestamp):
                    latest_timestamp = timestamp
                    latest_interview = interview_data

            if latest_interview:
                avg_score = latest_interview.get("average_score", 0)
                timestamp = latest_timestamp.strftime("%Y-%m-%d %H:%M:%S") if latest_timestamp else "N/A"
                leaderboard_data.append({
                    "user_id": user_id,
                    "user_name": user_name,
                    "avg_score": round(avg_score, 2),
                    "timestamp": timestamp
                })

        # Sort by average score in descending order
        leaderboard_data = sorted(leaderboard_data, key=lambda x: x["avg_score"], reverse=True)
        
        logger.info("Leaderboard data fetched successfully")
        return render_template("leaderboard.html", leaderboard_data=leaderboard_data)
    except Exception as e:
        logger.error(f"Error fetching leaderboard data: {str(e)}")
        return render_template("error.html", error="Failed to load leaderboard")
    
if __name__ == "__main__":
    try:
        app.run(debug=False)
    except Exception as e:
        logger.error(f"Flask server error: {str(e)}")
        sys.exit(1)