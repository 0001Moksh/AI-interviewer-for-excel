import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
import datetime

# Load environment variables (like dotenv_values)
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY not found in .env file. Please add it and restart.")
    st.stop()

# Configure Gemini API (once, like in FastAPI)
genai.configure(api_key=GEMINI_API_KEY)

# Knowledge base (unchanged)
import pandas as pd
df = pd.read_excel('questions/interview_questions.xlsx')
questions = df.to_dict(orient='records')

def evaluate_answer(question, expected, user_answer, history):
    current_time = datetime.datetime.now().strftime("%H:%M")
    current_date = datetime.datetime.now().strftime("%d %B %Y, %A")
    
    prompt = f"""
    Current Time: {current_time} | Date: {current_date}
    Question: {question}
    Expected Answer: {expected}
    User Answer: {user_answer}
    
    Evaluate the user's answer for accuracy, completeness, and clarity. Score from 0-10 (10=perfect match/explanation). Provide a 1-2 sentence feedback.
    IMPORTANT: Respond EXACTLY in this format, nothing else:
    Score: X/10
    Feedback: [brief text]
    """
    
    if not user_answer:
        return {"error": "Message cannot be empty"}
    
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",  # Stable model from your FastAPI code
            system_instruction="""You are an expert Excel Mock Interviewer for finance, ops, and analytics roles. Evaluate responses objectively and provide constructive feedback. Always use the exact output format: Score: X/10\nFeedback: [1-2 sentences]."""
        )
        chat_session = model.start_chat(history=history)  # Pass full history like in FastAPI
        response = chat_session.send_message(prompt)
        model_response = response.text.strip()

        # Append to history (exactly like in FastAPI: "parts" list)
        history.append({"role": "user", "parts": [prompt]})
        history.append({"role": "model", "parts": [model_response]})
        
        return model_response  # Return string for parsing

    except Exception as e:
        error_msg = {"error": str(e)}
        return f"Score: 0/10\nFeedback: {error_msg['error']}"  # Mimic format for parsing

# Streamlit app
st.title("AI-Powered Excel Mock Interviewer")

# Sidebar for reset
if st.sidebar.button("Reset Interview"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# Initialize session state (with shared history like history_gemini.memory)
if "step" not in st.session_state:
    st.session_state.step = 0
    st.session_state.scores = []
    st.session_state.feedbacks = []
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm your AI Excel Interviewer. We'll go through 10 questions on Excel skills for finance, ops, and analytics. Answer each one, and I'll evaluate. Type your response below. Ready? Let's start with Question 1."},
        {"role": "assistant", "content": f"Question 1: {questions[0]['q']}"}
    ]
    st.session_state.history = [{"role": "model", "parts": ["Starting Excel interview evaluation session."]}]  # Fixed: "parts" instead of "content"

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
user_input = st.chat_input("Your response:")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    if st.session_state.step < len(questions):
        # Evaluate current question (FastAPI-inspired)
        q_data = questions[st.session_state.step]
        eval_result = evaluate_answer(q_data["q"], q_data["exp"], user_input, st.session_state.history)

        # Debug: Show raw response (remove after testing)
        with st.expander("Debug: Raw Evaluation Response"):
            st.write(eval_result)

        # Parse score and feedback (robust)
        try:
            score_str = eval_result.split("Score: ")[1].split("/10")[0].strip()
            score = int(float(score_str))
            feedback = eval_result.split("Feedback: ")[1].strip() if "Feedback: " in eval_result else "No feedback generated."
        except (IndexError, ValueError):
            score = 0
            feedback = "Parsing failed; response format incorrect."
            eval_result = f"Score: 0/10\nFeedback: {feedback}"

        st.session_state.scores.append(score)
        st.session_state.feedbacks.append(feedback)

        # Prepare next step
        st.session_state.step += 1

        # Add feedback and next question (or summary)
        if st.session_state.step < len(questions):
            feedback_msg = f"Thanks! {eval_result}\n\nNow, Question {st.session_state.step + 1}: {questions[st.session_state.step]['q']}"
        else:
            avg_score = sum(st.session_state.scores) / len(st.session_state.scores)
            basics_avg = sum(st.session_state.scores[:3]) / 3
            advanced_avg = sum(st.session_state.scores[6:]) / 4
            strengths = "Strong in basics" if basics_avg > 7 else "Room for improvement in basics"
            weaknesses = "Improve advanced skills" if advanced_avg < 7 else "Solid advanced skills"
            summary = f"""Overall Score: {avg_score:.1f}/10
Strengths: {strengths}
Weaknesses: {weaknesses}
Detailed Feedback:
""" + "\n".join([f"Q{i+1}: {fb}" for i, fb in enumerate(st.session_state.feedbacks)])
            feedback_msg = f"Thanks! {eval_result}\n\nInterview complete. Here's your summary:\n{summary}"

        st.session_state.messages.append({"role": "assistant", "content": feedback_msg})

    st.rerun()
