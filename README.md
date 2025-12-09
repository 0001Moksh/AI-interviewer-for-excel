# AI-Powered Excel Mock Interviewer

This repository contains the source code for an **AI-Powered Excel Mock Interviewer**, a web-based application designed to assess candidates' Microsoft Excel skills for finance, operations, and data analytics roles. The project was developed as part of the **Gen AI Engineer Assignment** for Coding Ninjas, addressing the bottleneck in manual Excel skill assessments during hiring.

## Project Overview

The application simulates a structured mock interview, presenting candidates with Excel-related questions, evaluating their answers using the Google Gemini LLM, and providing a detailed performance summary via a webpage and email. It uses Flask for the backend, Firebase for data storage, and Google Sheets for question management.

### Features
- **Structured Interview Flow**: Users log in, view guidelines, answer sequential questions, and receive a performance summary.
- **Intelligent Evaluation**: Google Gemini evaluates answers for accuracy, completeness, and clarity, assigning scores (0-10) with feedback.
- **State Management**: Flask sessions and Firebase track user progress and store results.
- **Feedback Report**: Generates a summary with average score, strengths, weaknesses, and detailed feedback, sent via email.
- **Leaderboard**: Displays top performers’ scores (bonus feature).
- **Deployment**: Hosted at [https://ai-interviewer-by-moksh.onrender.com/](https://ai-interviewer-by-moksh.onrender.com/).

## Repository Structure
```
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── .env.example              # Template for environment variables
├── templates/                # HTML templates
│   ├── login.html            # Login page
│   ├── guidelines.html       # Instructions page
│   ├── interview.html        # Question and answer page
│   ├── summary.html          # Performance summary page
│   ├── summary_mail.html     # Email template for summary
├── README.md                 # This file
```

## Setup Instructions

### Prerequisites
- Python 3.8+
- A Google Cloud account with Gemini API keys
- A Firebase project with Firestore enabled
- A Gmail account for sending summary emails
- A Google Sheet with questions (columns: `q` for question, `exp` for expected answer)

### Steps
1. **Clone the Repository**
   ```bash
   git clone https://github.com/0001Moksh/AI-interviewer-for-excel.git
   cd AI-interviewer-for-excel
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**
   - Copy `.env.example` to `.env` and fill in the required values:
     ```plaintext
     SECRET_KEY=your_flask_secret_key
     GEMINI_API_KEY1=your_gemini_api_key_1
     GEMINI_API_KEY2=your_gemini_api_key_2
     GEMINI_API_KEY3=your_gemini_api_key_3
     GEMINI_API_KEY4=your_gemini_api_key_4
     EMAIL_USER=your_gmail_address
     EMAIL_PASS=your_gmail_app_password
     FIREBASE_CREDENTIALS_JSON=base64_encoded_firebase_credentials_json
     ```
   - Generate Firebase credentials JSON from your Firebase project, encode it in base64, and add to `.env`.
   - Use Gmail’s App Password for `EMAIL_PASS` (enable 2FA and generate via Google Account settings).

4. **Configure Google Sheet**
   - Create a Google Sheet with columns `q` (question) and `exp` (expected answer). Example:
     | q                                    | exp                                                                 |
     |--------------------------------------|--------------------------------------------------------------------|
     | What is the purpose of VLOOKUP?      | Searches for a value in the first column and returns a value from another column. |
     | How do you create a PivotTable?      | Select data, Insert > PivotTable, configure fields in Rows/Columns/Values. |
   - Make the sheet publicly accessible as a CSV export.
   - Update `SHEET_ID` in `app.py` with your sheet’s ID (from the URL: `https://docs.google.com/spreadsheets/d/<SHEET_ID>/...`).

5. **Run the Application**
   ```bash
   python app.py
   ```
   - Access at `http://localhost:5000`.

6. **Deploy (Optional)**
   - Push the repo to GitHub.
   - Connect to Render.com, set up a Python web service, and configure environment variables.
   - Deploy to get a public URL (e.g., https://ai-interviewer-by-moksh.onrender.com/).

## Usage
1. Open the app URL or localhost.
2. Enter a name and email to log in.
3. Follow the guidelines and answer Excel questions one-by-one.
4. Submit answers to receive real-time feedback from Gemini LLM.
5. View the final summary (average score, strengths, weaknesses) and receive an email report.
6. Check the leaderboard for top scores.

## Technology Stack
- **Backend**: Flask (lightweight, Python-based).
- **LLM**: Google Gemini (gemini-1.5-flash) for answer evaluation.
- **Database**: Firebase Firestore for user and session data.
- **Data Source**: Google Sheets for questions and expected answers.
- **Libraries**: Pandas (data handling), smtplib (email), LangChain (LLM integration).
- **Hosting**: Render.com for deployment.

## Notes
- The Google Sheet must have `q` and `exp` columns; add ~15 questions for a robust interview.
- Ensure Firebase security rules restrict unauthorized access (default rules suffice for PoC).
- The app sanitizes inputs to prevent injection and handles API failures gracefully.
- For production, consider rotating Gemini API keys dynamically and adding rate-limiting.

## Future Enhancements
- Adaptive questioning based on user performance.
- Support for Excel file uploads to evaluate practical tasks.
- Integration with HR systems (e.g., ATS).
- Voice mode using speech-to-text (e.g., xAI’s Grok voice mode).

## Contact
For issues or questions, contact Moksh Bhardwaj at [mokshbhardwaj2333@gmail.com](mailto:mokshbhardwaj2333@gmail.com).  
Portfolio: [https://mokshbhardwaj.netlify.app/](https://mokshbhardwaj.netlify.app/)  
CV: [Google Drive Link](https://drive.google.com/file/d/1mXnS-dNLi5DShw50UvgzyJ93ldOqgcMU/view)
