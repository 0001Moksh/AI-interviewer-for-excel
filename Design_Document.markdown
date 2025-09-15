# Design Document: AI-Powered Excel Mock Interviewer

# 1. Problem Understanding & Solution Overview

**Business Context:** Coding Ninjas is scaling its Finance, Operations, and Data Analytics divisions, where advanced Microsoft Excel proficiency is critical. The current manual interview process for assessing Excel skills is time-consuming, inconsistent, and a bottleneck in the hiring pipeline, slowing growth.

**Mission:** As the founding AI Product Engineer, my goal is to design and build an automated system to assess candidates’ Excel skills efficiently, ensuring consistency, scalability, and actionable feedback.

**Proposed Solution:** A web-based **AI-Powered Excel Mock Interviewer** that conducts a structured, multi-turn interview. Candidates log in, answer curated Excel questions, receive real-time evaluations via an LLM (Google Gemini), and get a detailed performance summary via a webpage and email. This solution prioritizes simplicity, cost-efficiency, and a structured flow over a fully conversational chatbot to ensure reliable assessments within the PoC scope.

**Why This Approach?**

- **Structured Flow:** Sequential questions mimic real interviews, ensuring coverage of key Excel topics (basics to advanced) while keeping LLM token usage low.
- **Scalability:** Web app (Flask + Firebase) supports multiple users; Google Sheets enables easy question updates.
- **Evaluation:** Gemini LLM provides objective scoring (0-10) and feedback, bootstrapped with a curated question bank.
- **Future Potential:** Can evolve to adaptive questioning or multi-modal inputs (e.g., Excel file uploads).

---

## 2. Approach Strategy

### 2.1 User Flow

1. **Login:** Users enter name and email; a unique user_id is generated and stored in Firebase.
2. **Guidelines:** Instructions are displayed to set expectations.
3. **Interview:** Questions are pulled from a Google Sheet, presented one-by-one. Users submit text answers, evaluated by Gemini LLM for accuracy, completeness, and clarity.
4. **Summary:** Post-interview, users see a performance report (average score, strengths, weaknesses, detailed feedback). A summary email is sent, and results are logged in Firebase.
5. **Leaderboard (Bonus):** Displays top performers’ scores, enhancing engagement.

### 2.2 Intelligent Answer Evaluation

- **Core Mechanism:** Each answer is evaluated using Google Gemini (gemini-1.5-flash) with a prompt instructing it to score (0-10) and provide 1-2 sentences of feedback based on the question, expected answer (from Google Sheet), and user input.
- **Prompt Design:** Structured to enforce consistent output (e.g., `Score: X/10\nFeedback: [Text]`). Temperature set to 0.3 for reliability.
- **Bootstrap Strategy:** A curated Google Sheet with \~15 questions (covering VLOOKUP, PivotTables, etc.) serves as the initial dataset, addressing the "cold start" problem. Expected answers are expert-written to guide the LLM.
- **Improvement Plan:** Collect anonymized user responses to build a dataset for fine-tuning the LLM or implementing Retrieval-Augmented Generation (RAG) to refine evaluations.

### 2.3 Agentic Behavior & State Management

- **Interviewer Role:** The LLM acts as an interviewer by generating constructive feedback per answer, simulating a human evaluator’s tone.
- **State Management:** Flask sessions track user progress (step, scores, feedback). Firebase stores user data and interview results for persistence.
- **Error Handling:** Sanitizes inputs, handles API failures (default score: 0), and validates sessions to prevent tampering.

### 2.4 Success Metrics

- **Accuracy:** Evaluation scores align with human expert reviews (target: &gt;85% correlation, to be validated post-PoC).
- **Completion Rate:** &gt;90% of users complete the interview.
- **Time Savings:** Automates 80% of manual interview effort (estimated 30 mins per candidate).
- **User Satisfaction:** Post-interview survey (future feature) to measure clarity and usefulness of feedback.

### 2.5 Bootstrapping & Iteration

- **Initial Setup:** Google Sheet with curated questions/expected answers avoids needing a pre-existing dataset.
- **Iteration Plan:**
  - Log user answers (anonymized) to expand the question bank.
  - A/B test LLM prompts for better scoring consistency.
  - Add adaptive questioning (e.g., harder questions for high scorers) using score thresholds.
  - Explore integrating xAI’s Grok for lower-cost evaluations.

---

## 3. Technology Stack Justification

- **Frontend/Backend: Flask**
  - **Why?** Lightweight, Python-based, ideal for rapid PoC development. Django was considered but deemed overkill for a single-purpose app.
  - **Trade-off:** Limited built-in features (e.g., no ORM), but sufficient for session-based flow.
- **LLM: Google Gemini (gemini-1.5-flash)**
  - **Why?** Fast, cost-effective for structured text evaluation. Multiple API keys ensure reliability. Alternatives (e.g., OpenAI) were costlier; Grok not yet integrated but viable for future.
  - **Trade-off:** Flash model prioritizes speed over deep reasoning; sufficient for PoC but could upgrade to pro models.
- **Database: Firebase Firestore**
  - **Why?** Real-time, scalable, free tier supports PoC needs. Stores user data, sessions, and interview results.
  - **Trade-off:** Vendor lock-in; but easy setup outweighs for demo purposes.
- **Data Source: Google Sheets**
  - **Why?** Easy to update questions without redeploying. Accessible via Pandas for CSV export.
  - **Trade-off:** Manual curation initially; automation possible with user data.
- **Hosting: Render.com**
  - **Why?** Free tier, auto-deploys from GitHub, reliable for demos. Alternatives (Heroku, Vercel) similar but Render’s Python support is seamless.
- **Other Libraries:**
  - **Pandas:** Processes Google Sheet data efficiently.
  - **smtplib:** Sends summary emails without external services.
  - **LangChain:** Simplifies LLM prompt management.
- **Security:** Input sanitization prevents injection; env vars hide secrets; Firebase rules restrict access.

---

## 4. Challenges & Future Enhancements

### 4.1 Challenges Addressed

- **Cold Start:** Curated Google Sheet with expert questions/answers bootstraps the system. No initial dataset needed.
- **Evaluation Accuracy:** Gemini’s structured prompt ensures consistent scoring; fallback mechanisms handle API failures.
- **Scalability:** Firebase and Render support multiple users; Flask sessions manage state efficiently.

### 4.2 Future Enhancements

- **Adaptive Questioning:** Adjust question difficulty based on user performance (e.g., &gt;7/10 triggers advanced questions).
- **Multi-Modal Inputs:** Allow Excel file uploads for practical tasks (e.g., evaluate a PivotTable).
- **HR Integration:** Sync with ATS (Applicant Tracking Systems) for seamless hiring.
- **Voice Mode:** Add speech-to-text (e.g., using xAI’s Grok voice mode if available) for accessibility.
- **Analytics Dashboard:** Visualize candidate trends for recruiters (e.g., average scores by role).

---

## 5. System Architecture

\[Diagram: Created using Draw.io, exported as PNG\]

- **User:** Accesses web app via browser.
- **Flask App:** Handles routes (login, interview, summary), session management.
- **Google Sheets:** Stores questions/expected answers, fetched via Pandas.
- **Gemini LLM:** Evaluates answers via API.
- **Firebase Firestore:** Stores user data, sessions, and results.
- **SMTP:** Sends summary emails.
- **Render.com:** Hosts the app.

![Architecture Diagram](https://via.placeholder.com/600x300.png?text=System+Architecture)\---