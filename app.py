from flask import Flask, render_template, request, redirect, session, url_for
from watsonx_api import generate_quiz
from pinecone_utils import store_student_answer
from user_utils import store_quiz_metadata, get_all_quiz_data
from user_utils import save_user_info, get_user_level, set_user_level
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import google.oauth2.credentials

app = Flask(__name__)
app.secret_key = 'super_secret_key'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/quiz', methods=['POST'])
def quiz():
    topic = request.form['user_input']
    student_id = session.get('email', 'guest_user')
    level = get_user_level(student_id)
    prompt = f"Generate a {level} level multiple choice quiz on the topic: {topic}."
    quiz = generate_quiz(prompt)
    store_student_answer(student_id, quiz)
    store_quiz_metadata(student_id, topic, score=None)  # For now
    return render_template('quiz.html', quiz=quiz)

@app.route('/diagnostic')
def diagnostic():
    student_id = session.get('email', 'guest_user')
    quiz = generate_quiz("Diagnostic test with 5 questions to assess learning level")
    set_user_level(student_id, 'beginner')  # Simulated default
    return render_template('quiz.html', quiz=quiz)

@app.route('/login')
def login():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/classroom.courses.readonly',
                'https://www.googleapis.com/auth/userinfo.profile',
                'https://www.googleapis.com/auth/userinfo.email',
                'openid'],
        redirect_uri='http://localhost:5001/callback'
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    return redirect(auth_url)

@app.route('/callback')
def callback():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/classroom.courses.readonly',
                'https://www.googleapis.com/auth/userinfo.profile',
                'https://www.googleapis.com/auth/userinfo.email',
                'openid'],
        redirect_uri='http://localhost:5001/callback'
    )
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)

    from googleapiclient.discovery import build
    service = build('oauth2', 'v2', credentials=credentials)
    user_info = service.userinfo().get().execute()

    session['email'] = user_info.get('email')
    session['name'] = user_info.get('name')
    session['role'] = 'student'  # default

    save_user_info(session['email'], session['name'], session['role'])
    return redirect(url_for('student_dashboard'))

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

from user_utils import get_user_quiz_data  # New function we’ll add

@app.route('/student-dashboard')
def student_dashboard():
    credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    service = googleapiclient.discovery.build('classroom', 'v1', credentials=credentials)
    courses = service.courses().list().execute().get('courses', [])
    
    email = session.get('email', 'guest_user')
    quiz_data = get_user_quiz_data(email)  # Only this student's history

    return render_template('student_dashboard.html', name=session['name'], courses=courses, quiz_data=quiz_data)

@app.route('/educator-dashboard')
def educator_dashboard():
    quiz_data = get_all_quiz_data()
    return render_template('educator_dashboard.html', quiz_data=quiz_data)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, port=5001)