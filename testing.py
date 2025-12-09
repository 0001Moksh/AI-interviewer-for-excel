import os
# Ye line OS module ko import karta hai, jo file system ke saath kaam karne ke liye use hota hai, jaise file paths ya environment variables ko access karna.

import logging
# Logging module import kiya, jo program ke execution ke logs (jaise errors, info) ko track karne ke liye use hota hai.

import re
# Regular expression (regex) module import kiya, jo string patterns ko match ya validate karne ke liye kaam aata hai.

import datetime
# Datetime module import kiya, jo date aur time ke saath kaam karne ke liye use hota hai, jaise current time ya date ko format karna.

import pandas as pd
# Pandas library import ki, jo data manipulation ke liye use hoti hai, jaise Google Sheet se data read karna.

from dotenv import load_dotenv
# Dotenv module se load_dotenv import kiya, jo .env file se environment variables ko load karta hai, jaise API keys ya sensitive data.

from flask import Flask, render_template, request, session, redirect, url_for, abort, make_response
# Flask se important components import kiye, jo web app banane ke liye use hote hain:
# Flask: Web app ka main framework.
# render_template: HTML templates ko render karne ke liye.
# request: User ke HTTP requests (jaise form data) ko handle karne ke liye.
# session: User ke session data ko store karne ke liye.
# redirect, url_for: Page redirection ke liye.
# abort: Error responses ke liye.
# make_response: Custom HTTP response banane ke liye.

import firebase_admin
# Firebase admin SDK import kiya, jo Firebase services (jaise Firestore) ke saath kaam karne ke liye use hota hai.

from firebase_admin import credentials, firestore
# Firebase se credentials aur firestore import kiye:
# credentials: Firebase authentication ke liye.
# firestore: Firestore database ke saath kaam karne ke liye.

from google.cloud.firestore_v1 import FieldFilter
# Firestore ke FieldFilter ko import kiya, jo specific queries (jaise email se user find karna) ke liye use hota hai.

import smtplib
# SMTPlib module import kiya, jo emails bhejne ke liye use hota hai, jaise Gmail SMTP server se.

from email.mime.text import MIMEText
# MIMEText import kiya, jo email ke text content ko format karne ke liye use hota hai.

from email.mime.multipart import MIMEMultipart
# MIMEMultipart import kiya, jo email ke multiple parts (jaise HTML aur text) ko handle karta hai.

import uuid
# UUID module import kiya, jo unique IDs generate karne ke liye use hota hai, jaise session IDs.

import random
# Random module import kiya, jo random strings ya numbers generate karne ke liye use hota hai.

import string
# String module import kiya, jo predefined character sets (jaise letters, digits) provide karta hai.

from datetime import timedelta
# Timedelta import kiya, jo time durations (jaise session expiry time) ko define karne ke liye use hota hai.

import json
# JSON module import kiya, jo JSON data ko parse ya generate karne ke liye use hota hai.

import base64
# Base64 module import kiya, jo data ko encode/decode karne ke liye use hota hai, jaise Firebase credentials.

import requests
# Requests module import kiya, jo HTTP requests (jaise Google Sheet se data fetch karna) ke liye use hota hai.

import io
# IO module import kiya, jo in-memory file operations ke liye use hota hai, jaise Google Sheet ka CSV data read karna.

from langchain_google_genai import ChatGoogleGenerativeAI
# LangChain se Google Generative AI ka Chat module import kiya, jo Gemini AI model ke saath interaction ke liye use hota hai.

from langchain.prompts import ChatPromptTemplate
# ChatPromptTemplate import kiya, jo AI ke liye structured prompts banane ke liye use hota hai.

from langchain_core.messages import HumanMessage, AIMessage
# LangChain se HumanMessage aur AIMessage import kiye, jo user aur AI ke messages ko represent karte hain.

import signal
# Signal module import kiya, jo system signals (jaise Ctrl+C) ko handle karne ke liye use hota hai.

import sys
# Sys module import kiya, jo system-level operations (jaise program exit) ke liye use hota hai.

# Configure logging
logging.basicConfig(level=logging.INFO)
# Logging ko configure kiya, INFO level ke messages (aur usse higher) ko log karega, jaise info, warnings, errors.

logger = logging.getLogger(__name__)
# Logger object banaya, jo current module ke naam se logs record karega.

# Initialize Flask app
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Current file ka directory path BASE_DIR me store kiya, jo templates ya files ko locate karne ke liye use hota hai.

template_dir = os.path.join(BASE_DIR, "templates")
# Template directory ka path banaya, jahan HTML templates store hote hain.

app = Flask(__name__, template_folder=template_dir)
# Flask app initialize kiya, aur template folder ko specify kiya.

app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")
# Flask app ka secret key set kiya, jo session data ko secure karta hai. Environment variable se lete hain, nahi to default "supersecretkey" use hota hai.

app.permanent_session_lifetime = timedelta(minutes=30)
# Session ka lifetime 30 minutes set kiya, iske baad session automatically expire ho jata hai.

# Load environment variables
load_dotenv()
# .env file se environment variables load kiye, jaise API keys ya email credentials.

GEMINI_API_KEYS = [
    os.getenv("GEMINI_API_KEY1"),
    os.getenv("GEMINI_API_KEY2"),
    os.getenv("GEMINI_API_KEY3"),
    os.getenv("GEMINI_API_KEY4")
]
# Gemini API keys ka list banaya, multiple keys environment variables se liye.

# Use only the first valid key to reduce API calls and internet usage
GEMINI_API_KEY = next((key for key in GEMINI_API_KEYS if key), None)
# Pehla valid API key select kiya, taaki unnecessary API calls na hon.

EMAIL_USER = os.getenv("EMAIL_USER")
# Email user (sender ka email) environment variable se liya.

EMAIL_PASS = os.getenv("EMAIL_PASS")
# Email password environment variable se liya.

FIREBASE_CREDENTIALS_JSON = os.getenv("FIREBASE_CREDENTIALS_JSON")
# Firebase credentials ka JSON string environment variable se liya.

# Validate critical environment variables
if not GEMINI_API_KEY:
    logger.error("No valid GEMINI_API_KEY provided")
    raise ValueError("Missing GEMINI_API_KEY")
# Agar GEMINI_API_KEY nahi mila, to error log karke program stop kar diya.

if not EMAIL_USER or not EMAIL_PASS:
    logger.error("Missing EMAIL_USER or EMAIL_PASS")
    raise ValueError("Missing EMAIL_USER or EMAIL_PASS")
# Agar EMAIL_USER ya EMAIL_PASS nahi mila, to error log karke program stop kar diya.

if not FIREBASE_CREDENTIALS_JSON:
    logger.error("Missing FIREBASE_CREDENTIALS_JSON")
    raise ValueError("Missing FIREBASE_CREDENTIALS_JSON")
# Agar FIREBASE_CREDENTIALS_JSON nahi mila, to error log karke program stop kar diya.

# Google Sheet configuration
SHEET_ID = "1C8WBBdpZYdbiCTh9_GgTgCG-wjIl4YZj4EnxP689R7U"
# Google Sheet ka ID define kiya, jahan se questions fetch honge.

SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
# Google Sheet ka URL banaya, jo CSV format me data export karta hai.

# Initialize Firebase
db = None
# Firestore database ka variable initialize kiya, abhi None set kiya.

try:
    logger.info("Initializing Firebase from environment variable")
    # Firebase initialize karne ka attempt log kiya.
    
    cred_dict = json.loads(base64.b64decode(FIREBASE_CREDENTIALS_JSON).decode('utf-8'))
    # Firebase credentials JSON ko base64 se decode karke dictionary me convert kiya.
    
    cred = credentials.Certificate(cred_dict)
    # Credentials object banaya, jo Firebase authentication ke liye use hoga.
    
    firebase_admin.initialize_app(cred)
    # Firebase app initialize kiya credentials ke saath.
    
    db = firestore.client()
    # Firestore client initialize kiya, jo database operations ke liye use hoga.
    
    logger.info("Firebase initialized successfully")
    # Firebase successfully initialize hone ka log kiya.
except Exception as e:
    logger.error(f"Error initializing Firebase: {str(e)}")
    # Agar Firebase initialize me error aaya, to error log kiya.
    
    raise ValueError("Failed to initialize Firebase")
    # Error ke saath program stop kiya.

# Load questions lazily from Google Sheet (cached to reduce internet usage)
def get_questions():
    # Questions ko Google Sheet se load karne ka function define kiya.
    
    if not hasattr(get_questions, 'cache'):
        # Agar cache nahi hai, to Google Sheet se data fetch karenge.
        
        try:
            response = requests.get(SHEET_URL)
            # Google Sheet ka URL se CSV data fetch kiya.
            
            response.raise_for_status()
            # Agar HTTP request fail hua (jaise 404), to error raise kiya.
            
            df = pd.read_csv(io.StringIO(response.text))
            # CSV data ko Pandas DataFrame me convert kiya.
            
            if 'q' not in df.columns or 'exp' not in df.columns:
                # Agar DataFrame me 'q' ya 'exp' columns nahi hain, to error raise kiya.
                
                raise ValueError("Google Sheet must have 'q' and 'exp' columns")
            
            df = df[['q', 'exp']].dropna()
            # Sirf 'q' aur 'exp' columns select kiye aur null values remove kiye.
            
            get_questions.cache = df.to_dict(orient="records")
            # DataFrame ko dictionary list me convert karke cache me store kiya.
            
            logger.info(f"Loaded {len(get_questions.cache)} questions from Google Sheet")
            # Kitne questions load hue, wo log kiya.
        except Exception as e:
            logger.error(f"Error loading questions from Google Sheet: {str(e)}")
            # Agar questions load me error aaya, to error log kiya.
            
            get_questions.cache = []
            # Error case me empty cache set kiya.
    
    return get_questions.cache
    # Cached questions return kiye.

questions = get_questions()
# Questions ko load kiya aur global variable me store kiya.

num_questions = len(questions)
# Total questions ki count calculate ki.

MAX_SCORE = 10
# Maximum score per question define kiya (10).

# Sanitize input to prevent injection
def sanitize_input(text):
    # User input ko sanitize karne ka function, taaki malicious code na chale.
    
    if not isinstance(text, str):
        # Agar input string nahi hai, to empty string return karo.
        
        return ""
    
    text = re.sub(r'[<>;{}]', '', text)
    # Dangerous characters (jaise <, >, ;, {}) ko remove kiya.
    
    return text.strip()[:1000]
    # Input ko trim kiya aur max 1000 characters tak limit kiya.

# Generate random user_id
def generate_user_id(name):
    # User ke naam se unique user ID generate karne ka function.
    
    name = sanitize_input(name)
    # Naam ko sanitize kiya.
    
    base = name.replace(" ", "").lower()[:10]
    # Naam se spaces hata kar, lowercase kiya aur pehle 10 characters liye.
    
    counter = 1
    # Counter initialize kiya unique ID ke liye.
    
    while True:
        # Loop chalaya jab tak unique ID na ban jaye.
        
        if counter == 1:
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            # Pehli baar random 6-character suffix banaya (letters aur digits).
        else:
            random_suffix = f"{counter:02d}{''.join(random.choices(string.ascii_lowercase + string.digits, k=4))}"
            # Dusri baar counter aur 4-character suffix add kiya.
        
        user_id = f"{base}{random_suffix}"
        # Base aur suffix combine karke user ID banaya.
        
        if len(user_id) > 20:
            user_id = user_id[:20]
            # Agar ID 20 characters se bada hai, to truncate kiya.
        
        try:
            if not db.collection("users").document(user_id).get().exists:
                # Firestore me check kiya ki user_id already exist nahi karta.
                
                return user_id
                # Unique ID mil gaya, to return kiya.
        except Exception as e:
            logger.error(f"Error checking user_id {user_id}: {str(e)}")
            # ID check karte waqt error aaya, to log kiya.
            
            counter += 1
            # Counter increment kiya aur dobara try kiya.
        
        if counter > 100:
            # Agar 100 attempts ke baad bhi unique ID nahi bana, to error raise kiya.
            
            raise Exception("Failed to generate unique user_id")

# Email sending function
def send_summary_email(user_email, user_name, user_id, summary_data):
    # Interview summary email bhejne ka function.
    
    try:
        msg = MIMEMultipart()
        # MIMEMultipart object banaya, jo email ke multiple parts ko handle karta hai.
        
        msg["From"] = EMAIL_USER
        # Sender ka email set kiya.
        
        msg["To"] = user_email
        # Receiver ka email set kiya.
        
        msg["Subject"] = "AI Interview Summary"
        # Email ka subject set kiya.
        
        html_body = render_template(
            "summary_mail.html",
            user_name=user_name,
            user_id=user_id,
            summary_data=summary_data,
            max_score=MAX_SCORE,
            current_year=datetime.datetime.now().year
        )
        # HTML template se email body banaya, jisme user data aur summary pass kiya.
        
        msg.attach(MIMEText(html_body, "html"))
        # HTML body ko email me attach kiya.
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
        # Gmail SMTP server se connect kiya (port 587).
        
        server.starttls()
        # TLS encryption start kiya, jo secure connection ke liye use hota hai.
        
        server.login(EMAIL_USER, EMAIL_PASS)
        # Email user aur password se login kiya.
        
        server.sendmail(EMAIL_USER, user_email, msg.as_string())
        # Email bheja.
        
        server.quit()
        # SMTP server connection close kiya.
        
        logger.info(f"Summary email sent to {user_email}")
        # Email successfully bhejne ka log kiya.
    except Exception as e:
        logger.error(f"Error sending email to {user_email}: {str(e)}")
        # Email bhejne me error aaya, to log kiya.

# Simplified LangChain-based evaluation function (no history to reduce size and API usage)
def evaluate_answer(question, expected, user_answer):
    # User ke jawab ko evaluate karne ka function, jo Gemini AI use karta hai.
    
    question = sanitize_input(question)
    # Question ko sanitize kiya.
    
    expected = sanitize_input(expected)
    # Expected answer ko sanitize kiya.
    
    user_answer = sanitize_input(user_answer)
    # User ka jawab sanitize kiya.
    
    if not GEMINI_API_KEY:
        logger.error("No valid Gemini API key available")
        return f"Score: 0/{MAX_SCORE}\nFeedback: API configuration error"
        # Agar API key nahi hai, to error return kiya.
    
    if not user_answer:
        return f"Score: 0/{MAX_SCORE}\nFeedback: Empty answer"
        # Agar user ne koi jawab nahi diya, to 0 score aur feedback return kiya.
    
    # Simplified prompt without history for independent evaluation and reduced token usage
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """You are an expert Excel Mock Interviewer for finance, ops, and analytics roles. 
        Evaluate responses objectively and provide constructive feedback. 
        Always output exactly: Score: X/10\nFeedback: [1-2 sentences]"""),
        # System prompt set kiya, jo AI ko batata hai ki jawab kaise evaluate karna hai.
        
        ("human", """
        Current Time: {current_time} | Date: {current_date}
        Question: {question}
        Expected Answer: {expected}
        User Answer: {user_answer}
        Evaluate the user's answer for accuracy, completeness, and clarity.
        Score from 0-{max_score} ({max_score}=perfect). Provide 1-2 sentence feedback.
        """)
        # Human prompt set kiya, jisme question, expected answer, aur user answer pass honge.
    ])

    current_time = datetime.datetime.now().strftime("%H:%M")
    # Current time ko HH:MM format me liya.
    
    current_date = datetime.datetime.now().strftime("%d %B %Y, %A")
    # Current date ko format kiya (e.g., 19 September 2025, Friday).
    
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=GEMINI_API_KEY,
            temperature=0.3
        )
        # Gemini AI model initialize kiya (model: gemini-1.5-flash, temperature: 0.3 for less randomness).
        
        chain = prompt_template | llm
        # Prompt aur LLM ko combine karke chain banaya.
        
        response = chain.invoke({
            "question": question,
            "expected": expected,
            "user_answer": user_answer,
            "current_time": current_time,
            "current_date": current_date,
            "max_score": MAX_SCORE
        })
        # AI se response liya, jisme question, expected, aur user answer pass kiye.
        
        model_response = response.content.strip()
        # AI ka response liya aur extra spaces hata diye.
        
        logger.info(f"Evaluation completed for question using Gemini API")
        # Evaluation successful hone ka log kiya.
        
        return model_response
        # AI ka response return kiya.
    except Exception as e:
        logger.error(f"Error with Gemini API: {str(e)}")
        # Gemini API me error aaya, to log kiya.
        
        return f"Score: 0/{MAX_SCORE}\nFeedback: Evaluation failed due to API error"
        # Error case me default response return kiya.

# Validate session ID
def validate_session_id(session_id):
    # Session ID ko validate karne ka function.
    
    try:
        doc = db.collection("sessions").document(session_id).get()
        # Firestore se session ID check kiya.
        
        if not doc.exists:
            logger.warning(f"Session {session_id} does not exist")
            return False
            # Agar session ID nahi milta, to False return kiya.
        
        return True
        # Session valid hai, to True return kiya.
    except Exception as e:
        logger.error(f"Error validating session ID {session_id}: {str(e)}")
        # Validation me error aaya, to log kiya.
        
        return False
        # Error case me False return kiya.

# Make session permanent
@app.before_request
def make_session_permanent():
    # Har request se pehle session ko permanent banane ka function.
    
    session.permanent = True
    # Session ko permanent set kiya, taaki 30-minute lifetime apply ho.

@app.route("/")
def home():
    # Home page ka route define kiya.
    
    session.clear()
    # Session data clear kiya, taaki nayi shuruaat ho.
    
    return render_template("login.html", num_questions=num_questions)
    # Login page ka HTML template render kiya, aur total questions pass kiye.

@app.route("/login", methods=["POST"])
def login():
    # Login route define kiya, jo POST requests handle karta hai.
    
    email = sanitize_input(request.form.get("email", ""))
    # Form se email liya aur sanitize kiya.
    
    name = sanitize_input(request.form.get("name", ""))
    # Form se name liya aur sanitize kiya.
    
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    # Email validation ke liye regex pattern define kiya.
    
    if not re.match(email_regex, email):
        # Agar email format galat hai, to error message ke saath login page render kiya.
        
        return render_template("login.html", error="Invalid email format", num_questions=num_questions)
    
    if not name or len(name) < 2:
        # Agar name khali hai ya 2 characters se chhota hai, to error message ke saath login page render kiya.
        
        return render_template("login.html", error="Name must be at least 2 characters", num_questions=num_questions)
    
    try:
        email_query = db.collection("users").where(filter=FieldFilter("email", "==", email)).get()
        # Firestore me email se user check kiya.
        
        if email_query:
            # Agar user milta hai:
            
            user_doc = email_query[0]
            # User ka document liya.
            
            user_id = user_doc.id
            # User ka ID liya.
            
            if user_doc.to_dict().get("name") != name:
                # Agar stored name aur input name alag hain, to name update kiya.
                
                db.collection("users").document(user_id).update({"name": name})
            
            logger.info(f"User {user_id} logged in")
            # User login ka log kiya.
        else:
            # Agar user nahi milta:
            
            user_id = generate_user_id(name)
            # Naya user ID generate kiya.
            
            db.collection("users").document(user_id).set({
                "name": name,
                "email": email,
                "created_at": firestore.SERVER_TIMESTAMP
            })
            # Firestore me naya user create kiya.
            
            logger.info(f"New user created with User ID: {user_id}")
            # New user creation ka log kiya.
        
        session["user_id"] = user_id
        # Session me user ID store kiya.
        
        session["user_email"] = email
        # Session me user email store kiya.
        
        session["user_name"] = name
        # Session me user name store kiya.
        
        session["session_id"] = str(uuid.uuid4())
        # Unique session ID generate kiya aur session me store kiya.
        
        session.modified = True  # Ensure session updates
        # Session ko modified flag set kiya, taaki changes save hon.
        
        db.collection("sessions").document(session["session_id"]).set({
            "user_id": user_id,
            "created_at": firestore.SERVER_TIMESTAMP
        })
        # Firestore me session data store kiya.
        
        logger.info(f"Session {session['session_id']} created for user {user_id}")
        # Session creation ka log kiya.
        
        return redirect(url_for("guidelines", session_id=session["session_id"]))
        # User ko guidelines page pe redirect kiya.
    except Exception as e:
        logger.error(f"Login/Registration error: {str(e)}")
        # Login ya registration me error aaya, to log kiya.
        
        return render_template("login.html", error=f"Registration failed: {str(e)[:100]}", num_questions=num_questions)
        # Error message ke saath login page render kiya.

@app.route("/guidelines/<session_id>")
def guidelines(session_id):
    # Guidelines page ka route define kiya.
    
    if session.get("session_id") != session_id or not validate_session_id(session_id):
        # Agar session ID invalid hai ya session mismatch hai, to error throw kiya.
        
        logger.error(f"Invalid session access attempt for session_id: {session_id}")
        abort(403, description="Invalid session")
    
    return render_template("guidelines.html", session_id=session_id)
    # Guidelines page ka HTML template render kiya.

@app.route("/start/<session_id>")
def start(session_id):
    # Interview start karne ka route define kiya.
    
    if session.get("session_id") != session_id or not validate_session_id(session_id):
        # Agar session ID invalid hai, to error throw kiya.
        
        logger.error(f"Invalid session access attempt for session_id: {session_id}")
        abort(403, description="Invalid or tampered session URL")
    
    session["step"] = 0
    # Interview ka step 0 se start kiya.
    
    session["scores"] = []
    # Scores ka empty list initialize kiya.
    
    session["feedbacks"] = []
    # Feedbacks ka empty list initialize kiya.
    
    session["questions_asked"] = []
    # Questions asked ka empty list initialize kiya.
    
    session.modified = True  # Ensure session updates
    # Session ko modified flag set kiya.
    
    logger.info(f"Interview started for session {session_id}")
    # Interview start hone ka log kiya.
    
    return redirect(url_for("interview", session_id=session_id))
    # Interview page pe redirect kiya.

@app.route("/interview/<session_id>", methods=["GET", "POST"])
def interview(session_id):
    # Interview page ka route define kiya, jo GET aur POST requests handle karta hai.
    
    if session.get("step") is None:
        # Agar step session me nahi hai, to start page pe redirect kiya.
        
        logger.error(f"Session step not initialized for session {session_id}")
        return redirect(url_for("start", session_id=session_id))
    
    if session.get("session_id") != session_id or not validate_session_id(session_id):
        # Agar session ID invalid hai, to error throw kiya.
        
        logger.error(f"Invalid session access attempt for session_id: {session_id}")
        abort(403, description="Invalid or tampered session URL")
    
    step = session.get("step", 0)
    # Current step session se liya, default 0.
    
    if step >= num_questions:
        # Agar saare questions ho gaye, to summary page pe redirect kiya.
        
        return redirect(url_for("summary", session_id=session_id))
    
    q_data = questions[step]
    # Current step ka question data liya.
    
    question_text = q_data["q"]
    # Question text extract kiya.
    
    logger.info(f"Displaying question {step + 1} for session {session_id}")
    # Current question display hone ka log kiya.
    
    if request.method == "POST":
        # Agar request POST hai (user ne answer submit kiya):
        
        user_input = sanitize_input(request.form.get("answer", ""))
        # User ka answer liya aur sanitize kiya.
        
        if user_input:
            # Agar answer khali nahi hai:
            
            try:
                eval_result = evaluate_answer(q_data["q"], q_data["exp"], user_input)
                # Answer ko evaluate kiya Gemini AI se.
                
                score_str = eval_result.split("Score: ")[1].split(f"/{MAX_SCORE}")[0].strip()
                # Evaluation result se score extract kiya.
                
                score = int(float(score_str))
                # Score ko integer me convert kiya.
                
                feedback = eval_result.split("Feedback: ")[1].strip()
                # Feedback extract kiya.
            except Exception as e:
                logger.error(f"Error parsing evaluation for session {session_id}: {str(e)}")
                # Evaluation parse me error aaya, to log kiya.
                
                score = 0
                # Error case me score 0 set kiya.
                
                feedback = "Evaluation failed"
                # Error case me default feedback set kiya.
            
            session["scores"].append(score)
            # Score ko session me add kiya.
            
            session["feedbacks"].append(feedback)
            # Feedback ko session me add kiya.
            
            session["questions_asked"].append(question_text)
            # Question ko session me add kiya.
            
            session["step"] = step + 1
            # Step increment kiya.
            
            session.modified = True  # Ensure session updates
            # Session ko modified flag set kiya.
            
            if session["step"] >= num_questions:
                # Agar saare questions ho gaye, to summary page pe redirect kiya.
                
                return redirect(url_for("summary", session_id=session_id))
            
            return redirect(url_for("interview", session_id=session_id))
            # Agle question ke liye interview page pe redirect kiya.
    
    response = make_response(render_template("interview.html", step=step+1, question=question_text, num_questions=num_questions, session_id=session_id))
    # Interview page ka HTML template render kiya, aur step, question, aur session ID pass kiye.
    
    session_cookie = response.headers.get("Set-Cookie")
    # Response se session cookie liya.
    
    if session_cookie:
        # Agar cookie hai:
        
        cookie_size = len(session_cookie.encode("utf-8"))
        # Cookie ka size bytes me calculate kiya.
        
        logger.info(f"Session cookie size: {cookie_size} bytes")
        # Cookie size ka log kiya.
    
    return response
    # Response return kiya.

@app.route("/summary/<session_id>")
def summary(session_id):
    # Summary page ka route define kiya.
    
    if session.get("session_id") != session_id or not validate_session_id(session_id):
        # Agar session ID invalid hai, to error throw kiya.
        
        logger.error(f"Invalid session access attempt for session_id: {session_id}")
        abort(403, description="Invalid or tampered session URL")
    
    scores = session.get("scores", [])
    # Session se scores liye.
    
    feedbacks = session.get("feedbacks", [])
    # Session se feedbacks liye.
    
    questions_asked = session.get("questions_asked", [])
    # Session se questions liye.
    
    user_id = session.get("user_id")
    # Session se user ID liya.
    
    user_email = session.get("user_email")
    # Session se user email liya.
    
    user_name = session.get("user_name")
    # Session se user name liya.
    
    if not scores:
        # Agar koi scores nahi hain, to home page pe redirect kiya.
        
        return redirect(url_for("home"))
    
    try:
        avg_score = sum(scores) / len(scores)
        # Average score calculate kiya.
        
        basics_avg = sum(scores[:3]) / min(3, len(scores)) if len(scores) >= 3 else 0
        # Pehle 3 questions ka average score calculate kiya (basics ke liye).
        
        advanced_avg = sum(scores[6:]) / len(scores[6:]) if len(scores) > 6 else 0
        # Last ke questions ka average score calculate kiya (advanced ke liye).
        
        strengths = "Strong in basics" if basics_avg > 7 else "Needs basics improvement"
        # Basics ke average ke hisaab se strengths set kiya.
        
        weaknesses = "Improve advanced skills" if advanced_avg < 7 else "Good advanced skills"
        # Advanced ke average ke hisaab se weaknesses set kiya.
        
        detailed_feedback = list(zip(questions_asked, feedbacks, scores))
        # Questions, feedbacks, aur scores ko combine kiya.
        
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
        # Interview results Firestore me store kiye.
        
        # Send summary email
        summary_data = {
            "avg_score": avg_score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "detailed_feedback": detailed_feedback
        }
        # Summary data ek dictionary me organize kiya.
        
        send_summary_email(user_email, user_name, user_id, summary_data)
        # User ko summary email bheja.
        
        # Clear session after summary
        session.clear()
        # Summary ke baad session clear kiya.
        
        logger.info(f"Session {session_id} cleared after summary")
        # Session clear hone ka log kiya.
        
        return render_template(
            "summary.html",
            avg_score=avg_score,
            strengths=strengths,
            weaknesses=weaknesses,
            detailed_feedback=detailed_feedback,
            max_score=MAX_SCORE,
            num_questions=num_questions
        )
        # Summary page ka HTML template render kiya, aur data pass kiya.
    except Exception as e:
        logger.error(f"Error processing summary for session {session_id}: {str(e)}")
        # Summary process me error aaya, to log kiya.
        
        return render_template("error.html", error="Failed to generate summary")
        # Error page render kiya.

# Handle graceful shutdown
def handle_shutdown(signum, frame):
    # Server shutdown ko handle karne ka function.
    
    logger.info("Shutting down Flask server")
    # Shutdown ka log kiya.
    
    sys.exit(0)
    # Program gracefully exit kiya.

signal.signal(signal.SIGINT, handle_shutdown)
# SIGINT (Ctrl+C) signal ko handle_shutdown function se link kiya.

signal.signal(signal.SIGTERM, handle_shutdown)
# SIGTERM signal ko handle_shutdown function se link kiya.

@app.route("/leaderboard")
def leaderboard():
    # Leaderboard page ka route define kiya.
    
    try:
        # Fetch all users from Firestore
        users_ref = db.collection("users").stream()
        # Firestore se saare users fetch kiye.
        
        leaderboard_data = []
        # Leaderboard data ke liye empty list banaya.
        
        # Iterate through users and their interviews
        for user in users_ref:
            # Har user ke liye loop chalaya.
            
            user_data = user.to_dict()
            # User ka data dictionary me liya.
            
            user_id = user.id
            # User ka ID liya.
            
            user_name = user_data.get("name", "Unknown")
            # User ka name liya, agar nahi hai to "Unknown" set kiya.
            
            interviews_ref = db.collection("users").document(user_id).collection("interviews").stream()
            # User ke interviews fetch kiye.
            
            # Get the latest interview for each user
            latest_interview = None
            # Latest interview ke liye variable initialize kiya.
            
            latest_timestamp = None
            # Latest timestamp ke liye variable initialize kiya.
            
            for interview in interviews_ref:
                # Har interview ke liye loop chalaya.
                
                interview_data = interview.to_dict()
                # Interview ka data dictionary me liya.
                
                timestamp = interview_data.get("timestamp")
                # Interview ka timestamp liya.
                
                if timestamp and (latest_timestamp is None or timestamp > latest_timestamp):
                    # Agar timestamp hai aur latest se naya hai:
                    
                    latest_timestamp = timestamp
                    # Latest timestamp update kiya.
                    
                    latest_interview = interview_data
                    # Latest interview update kiya.
            
            if latest_interview:
                # Agar latest interview mila:
                
                avg_score = latest_interview.get("average_score", 0)
                # Average score liya.
                
                timestamp = latest_timestamp.strftime("%Y-%m-%d %H:%M:%S") if latest_timestamp else "N/A"
                # Timestamp ko format kiya.
                
                leaderboard_data.append({
                    "user_id": user_id,
                    "user_name": user_name,
                    "avg_score": round(avg_score, 2),
                    "timestamp": timestamp
                })
                # Leaderboard data me user ka info add kiya.
        
        # Sort by average score in descending order
        leaderboard_data = sorted(leaderboard_data, key=lambda x: x["avg_score"], reverse=True)
        # Leaderboard ko average score ke hisaab se descending order me sort kiya.
        
        logger.info("Leaderboard data fetched successfully")
        # Leaderboard data successfully fetch hone ka log kiya.
        
        return render_template("leaderboard.html", leaderboard_data=leaderboard_data)
        # Leaderboard page ka HTML template render kiya, aur data pass kiya.
    except Exception as e:
        logger.error(f"Error fetching leaderboard data: {str(e)}")
        # Leaderboard fetch me error aaya, to log kiya.
        
        return render_template("error.html", error="Failed to load leaderboard")
        # Error page render kiya.

if __name__ == "__main__":
    # Agar script directly run ho raha hai:
    
    try:
        app.run(debug=False)
        # Flask app start kiya, debug mode off kiya.
    except Exception as e:
        logger.error(f"Flask server error: {str(e)}")
        # Server start me error aaya, to log kiya.
        
        sys.exit(1)
        # Program exit kiya with error code 1.