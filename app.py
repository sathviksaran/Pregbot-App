from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
# import nltk
import random
import numpy as np
import json
# import pickle
# from nltk.stem import WordNetLemmatizer
# from tensorflow.keras.models import load_model # type: ignore
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
# from flask_mail import Message,Mail
from twilio.rest import Client
import os
import requests
from datetime import datetime, timezone, timedelta
from deep_translator import GoogleTranslator
# from functools import lru_cache
# from nltk.corpus import wordnet
# import signal
import time
from zoneinfo import ZoneInfo

HF_API_URL = 'https://sathviksaran-pregbot-ml.hf.space/predict'

def predict_intent_remote(text):
    response = requests.post(
        HF_API_URL,
        json={"text": text},
        timeout=5
    )
    response.raise_for_status()
    return response.json()["intent"]

def translate_message(message, target_language): 
    translated_message = GoogleTranslator(
        source='auto',
        target=target_language
    ).translate(message)
    return translated_message

with open('bot.json') as json_file:
    intents = json.load(json_file)


# LAUNCH_TIME = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))  # IST

LAUNCH_TIME = datetime(
    2026, 1, 2, 11, 0, 0,
    tzinfo=timezone(timedelta(hours=5, minutes=30))  # IST
)


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)



BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
SENDER_EMAIL = 'pregbotapp@gmail.com'
SENDER_NAME = 'PREGBOT'

# Configure Flask-Mail
# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 587  # Use the appropriate port
# app.config['MAIL_USE_TLS'] = True  # Or MAIL_USE_SSL=True for SSL
# app.config['MAIL_USERNAME'] = 'mypregbot@gmail.com'
# app.config['MAIL_PASSWORD'] = 'ijaefbyibmwtmobf'
# app.config['MAIL_DEFAULT_SENDER'] = 'mypregbot@gmail.com'

# mail = Mail(app)

# Twilio account credentials
account_sid = 'AC4923a8ee90fd7a3ca656b5e063edeb45'
auth_token = '6638bd03af33a3b6d223cd7a549c7a36'
client = Client(account_sid, auth_token)
def send_msg(to_phone_number, message):
    message = client.messages.create(
            body=message,
            from_='+15407387218',
            to=to_phone_number
        )
def send_email(to_email, subject, html_content):
    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }

    payload = {
        "sender": {
            "name": SENDER_NAME,
            "email": SENDER_EMAIL
        },
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:LiWTXGZPopMlSrUIEldyHGUeRUlmeeqD@yamabiko.proxy.rlwy.net:34102/railway'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
class profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    place = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    diabetes = db.Column(db.Boolean, nullable=False)
    blood_pressure = db.Column(db.Boolean, nullable=False)
    other_disease = db.Column(db.String(100))
    notify = db.Column(db.String(3), nullable=False)
    address = db.Column(db.Text, nullable=False)
# models.py
class DailyRoutine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.String(5), nullable=False)
    event = db.Column(db.String(100))  # Change column name from medicine to event
    email = db.Column(db.String(120), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = password
# ...
class PregnancyFormData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    overall_feeling = db.Column(db.String(20))
    morning_sickness = db.Column(db.String(20))
    weight_changes = db.Column(db.String(20))
    appetite = db.Column(db.String(20))
    swelling = db.Column(db.String(20))
    fatigue = db.Column(db.String(20))
    sleep_quality = db.Column(db.String(20))
    hydration = db.Column(db.String(20))
    mood_changes = db.Column(db.String(20))
    prenatal_checkups = db.Column(db.String(20))


@app.before_request
def protect_internal_route():
    if request.path == "/internal/run-mail-jobs":
        token = request.headers.get("X-CRON-KEY")
        if token != os.environ.get("CRON_SECRET"):
            abort(401)

@app.route("/internal/run-mail-jobs", methods=["POST"])
def run_mail_jobs():
    now = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%H:%M")

    # EXACT daily time
    if now == "06:00":
        send_email_at_6()
        send_msg_at_6()

    # other reminder logic can also live here
    check_and_send_emails()
    check_and_send_msgs()

    return {"status": "Mail job executed"}

@app.before_request
def check_launch_time():
    now = datetime.now(timezone(timedelta(hours=5, minutes=30)))

    if now < LAUNCH_TIME:
        # Allow admin / health routes if needed
        if request.path.startswith("/health"):
            return None
        return render_template("coming_soon.html"), 503


@app.route('/', methods=['GET', 'POST'])
def index():
    # Check if the user is not logged in
    if 'loggedin' not in session or not session['loggedin']:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))
    user = session['username']
    # Your existing code for the index page goes here
    return render_template('index.html',username=user)

@app.route('/form', methods=['GET'])
def show_form():
    return render_template('form.html')
@app.route('/submit', methods=['POST'])
def submit_form():
    data = PregnancyFormData(
        overall_feeling=request.form['overall_feeling'],
        morning_sickness=request.form['morning_sickness'],
        weight_changes=request.form['weight_changes'],
        appetite=request.form['appetite'],
        swelling=request.form['swelling'],
        fatigue=request.form['fatigue'],
        sleep_quality=request.form['sleep_quality'],
        hydration=request.form['hydration'],
        mood_changes=request.form['mood_changes'],
        prenatal_checkups=request.form['prenatal_checkups']
    )
    db.session.add(data)
    db.session.commit()
    flash('Form submitted successfully!', 'success')  # Flash a success message
    return redirect(url_for('show_form'))
@app.route('/about')
def about():
    user = session['username']
    return render_template('about.html',username=user)

@app.route('/services')
def services():
    user = session['username']
    return render_template('services.html',username=user)

@app.route('/resources')
def resources():
    user = session['username']
    return render_template('resources.html',username=user)
@app.route('/chatbot.html')
def chatbot():
    user = session['username']
    return render_template('index.html',username=user)

@app.route('/contact')
def contact():
    user = session['username']
    # Render your contact page template here
    return render_template('contact.html',username=user)

@app.route('/sendmessage', methods=['POST'])
def send_message():
    user = session['username']
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        # Create a new Contact object
        new_contact = Contact(name=name, email=email, message=message)

        # Add the new contact to the database
        db.session.add(new_contact)
        db.session.commit()

        # Send email
        try:
            subject='New message from PREGBOT'
            recipient='pregbotapp@gmail.com'  # Admin's email
            body = f"Name: {name}\nEmail: {email}\nMessage: {message}"
            send_email(recipient,subject,body)
            flash('Mail sent successfully.', 'success')
            return redirect('/contact?status=success')
        except Exception as e:
            flash('Error sending mail','error')
            return redirect('/contact?status=failure')

@app.route('/healthprofile')
def health_profile():
    username = session.get('username')

    if username:
        # Query the database to retrieve user information based on the username
        user = User.query.filter_by(username=username).first()

        if user:
            # Query the profile table based on the user's email
            pro= profile.query.filter_by(email=user.email).first()

            # Pass user and profile data to the template
            return render_template('healthprofile.html', user=user, profile=pro)
        else:
            # Handle the case where the user is not found
            return render_template('error.html', error_message='User not found')

    # Handle the case where there is no username in the session
    return render_template('error.html', error_message='No username in session')
@app.route('/dailyroutine', methods=['GET'])
def show_daily_routines():
    if 'email' not in session:
        return "Error: User not logged in"
    user=session['username']
    email = session['email']
    routines = DailyRoutine.query.filter_by(email=email).all()

    return render_template('dailyroutine.html', routines=routines,username=user,email=email)
@app.route('/dailyroutine', methods=['POST'])
def save_daily_routine():
    if request.method == 'POST':
        username = session['username']
        user = User.query.filter_by(username=username).first()
        time = request.form['time']
        event = request.form['event']  # Change from 'medicine' to 'event'
        email = request.form['email']
        mobile = user.mobile

        new_routine = DailyRoutine(time=time, event=event, email=email, mobile=mobile)
        db.session.add(new_routine)
        db.session.commit()

        return "Data saved successfully."
@app.route('/dailyroutine/delete/<int:routine_id>', methods=['POST'])
def delete_daily_routine(routine_id):
    if 'email' not in session:
        return "Error: User not logged in"

    email = session['email']
    routine_to_delete = DailyRoutine.query.get(routine_id)

    if routine_to_delete and routine_to_delete.email == email:
        db.session.delete(routine_to_delete)
        db.session.commit()

    return redirect(url_for('index'))

@app.route('/translate', methods=['POST'])
def translate_text():
    try:
        text = request.form.get('text', '')
        target_language = request.form.get('target_language', 'en')

        translated_text = GoogleTranslator(
            source='auto',
            target=target_language
        ).translate(text)

        return jsonify({'translated_text': translated_text}), 200

    except Exception as e:
        app.logger.error(f"Translate error: {e}")
        return jsonify({'translated_text': text}), 200


@app.route('/find')
def find_hospitals():
    user = session['username']
    return render_template('find.html',username=user)



@app.route('/chat', methods=['POST'])
def chat():
    
    try:
        message = request.form.get('message', '').strip()

        if not message:
            return jsonify({'response': 'Please enter a message.'}), 200

        if message.lower() == 'quit':
            return jsonify({'response': 'Goodbye!'}), 200
        
        
        ints = predict_intent_remote(message)
        resp = get_response(ints, intents)
        return jsonify({"response": resp})


    except Exception as e:
        app.logger.error(f"Chat error: {e}")
        return jsonify({'response': 'Sorry, something went wrong.'}), 200


@app.route('/healthprofile', methods=['GET', 'POST'])# update the data
def chatbot_submit():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        mobile = request.form['mobile']
        place = request.form['place']
        age = int(request.form['age'])
        height = int(request.form['height'])
        weight = int(request.form['weight'])
        month = int(request.form['month'])

        # Handle checkbox values
        diabetes = int('diabetes' in request.form)
        blood_pressure = int('Blood pressure' in request.form)
        disease_description = request.form['disesase']
        notify = request.form['notify']
        address = request.form['address']
        
        # Check if a profile with the given email already exists
        existing_profile = profile.query.filter_by(email=email).first()

        if existing_profile:
            # Update the existing profile
            existing_profile.name = fullname
            existing_profile.mobile = mobile
            existing_profile.place = place
            existing_profile.age = age
            existing_profile.height = height
            existing_profile.weight = weight
            existing_profile.month = month
            existing_profile.diabetes = diabetes
            existing_profile.blood_pressure = blood_pressure
            existing_profile.other_disease = disease_description
            existing_profile.notify = notify
            existing_profile.address = address
        else:
            # Create a new profile
            new_profile = profile(
                name=fullname,
                email=email,
                mobile=mobile,
                place=place,
                age=age,
                height=height,
                weight=weight,
                month=month,
                diabetes=diabetes,
                blood_pressure=blood_pressure,
                other_disease=disease_description,
                notify=notify,
                address=address
            )
            db.session.add(new_profile)

        db.session.commit()

        return redirect(url_for('index'))

    username = session.get('username')
    user = User.query.filter_by(username=username).first()

    if user:
        return render_template('healthprofile.html', user=user)

    return render_template('error.html', error_message='User not found')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and password and user.password_hash==password:
            session['loggedin'] = True
            session['username'] = username
            session['email'] = user.email
            flash('Logged in successfully.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your username and password.', 'error')

    return render_template('login.html')
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        fullname = request.form['fullname']
        username = request.form['username']
        email = request.form['email']
        mobile = request.form['mobile']
        password = request.form['password']
        cpassword = request.form['cpassword']

        # Check if the user already exists
        existing_user = User.query.filter_by(email=email).first()
        existing_username = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Email already taken. Choose a different one.', 'error')
        if existing_username:
            flash('User name already taken. Choose a different one.', 'error')
        digit=False                          
        upper=False
        lower=False                          
        cond1=len(password)>=8 and not(password.isalnum())          
        for i in password:
            if i.isupper():
                upper=True                                         
                break                                             
        for i in password:
            if i.islower():                                                                           
                lower=True                                        
                break
        for i in password:
            if i.isdigit():                                        
                digit=True                                        
                break
        if cond1 and upper and lower and digit and password==cpassword:                   
            new_user = User(fullname=fullname, username=username, email=email, mobile=mobile)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            subject='NEW USER REGISTERED IN PREGBOT'
            recipient='pregbotapp@gmail.com'  # Admin's email
            body = f"Name: {new_user.username}\nEmail: {new_user.email}\nMobile No: {new_user.mobile}"
            send_email(recipient,subject,body)
            subject1='PREGBOT USER REGISTRATION SUCCESSFUL'
            recipient1=str(new_user.email)
            body1 = f"Name: {new_user.fullname}\nUsername: {new_user.username}\nEmail: {new_user.email}\nMobile No: {new_user.mobile}"
            send_email(recipient1,subject1,body1)
            flash('Account created successfully. You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            if len(password)<8:
                flash('Password must contain atleast 8 characters', 'error')
            if(password.isalnum()):
                flash('Password must contain atleast one special character', 'error')
            if(digit==False):
                flash('Password must contain atleast one digit', 'error')
            if(upper==False and lower==False):
                flash('Password must contain alphabet', 'error')
            else:
                if(upper==False):
                    flash('Password must contain atleast one uppercase letter', 'error')
                if(lower==False):
                    flash('Password must contain atleast one lowercase letter', 'error')
    return render_template('signup.html')

@app.route('/forgotpwd', methods=['GET','POST'])
def forgotpwd():
    if request.method == 'POST':
        username = request.form['username']
        npassword = request.form['npassword']
        cpassword = request.form['cpassword']

        user = User.query.filter_by(username=username).first()
        digit=False                          
        upper=False
        lower=False                          
        cond1=len(npassword)>=8 and not(npassword.isalnum())          
        for i in npassword:
            if i.isupper():
                upper=True                                         
                break                                             
        for i in npassword:
            if i.islower():                                                                           
                lower=True                                        
                break
        for i in npassword:
            if i.isdigit():                                        
                digit=True                                        
                break
        if cond1 and upper and lower and digit and user and npassword and cpassword and npassword==cpassword:
            user.set_password(cpassword)
            db.session.commit()
            flash('Password changed successfully.', 'success')
            return redirect(url_for('login'))
        else:
            if npassword!=cpassword:
                flash('Passwords should match', 'error')
            if not user:
                flash('Username not found', 'error')
            if len(npassword)<8:
                flash('Password must contain atleast 8 characters', 'error')
            if(npassword.isalnum()):
                flash('Password must contain atleast one special character', 'error')
            if(digit==False):
                flash('Password must contain atleast one digit', 'error')
            if(upper==False and lower==False):
                flash('Password must contain alphabet', 'error')
            else:
                if(upper==False):
                    flash('Password must contain atleast one uppercase letter', 'error')
                if(lower==False):
                    flash('Password must contain atleast one lowercase letter', 'error')
    return render_template('forgotpwd.html')

@app.route('/logout')
def logout():
    # Clear the session to log the user out
    session.clear()

    # Redirect to the login page
    return redirect(url_for('login'))

def get_response(intents_list, intents_json):
    tag = intents_list[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if i['tag'] == tag:
            result = random.choice(i['responses'])
            break
    return result

def send_email_at_6():
    with app.app_context():
        users = User.query.all()
        subject = "Daily Link Reminder"
        body = "Here is the link you requested: https://pregbot-app.onrender.com/form"
        for user in users:
            send_email(user.email, subject, body)

def check_and_send_emails():
    with app.app_context():
        try:
            current_time = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%H:%M")
            print(f"Current Time: {current_time}")

            # Query the database for routines with matching time
            routines = DailyRoutine.query.filter_by(time=current_time).all()

            for routine in routines:
                recipient = routine.email
                event = routine.event

                # Translate event message into multiple languages
                translated_messages = {}
                for language in ['te', 'en', 'ta', 'kn', 'hi']:  # Telugu, English, Tamil, Kannada, Hindi
                    translated_event = translate_message(event, language)
                    translated_messages[language] = translated_event

                # Prepare email body with content in all languages
                email_body = ""
                for language, translated_event in translated_messages.items():
                    email_body += f"{language.upper()}: {translated_event}\n"

                # Send email
                subject = "Your Daily Routine Reminder"
                try:
                    send_email(recipient, subject, email_body)
                    print(f"Email sent successfully to {recipient}")
                except Exception as e:
                    print(f"Error sending email to {recipient}: {e}")

                # Print values to console
                print(f"Routine ID: {routine.id}, Time: {routine.time}, Event: {event}, Email: {recipient}")

            print(f"Checked and sent emails at {current_time}")

            # Commit changes to the database
            db.session.commit()

        except Exception as e:
            # Rollback in case of an error
            db.session.rollback()
            print(f"An error occurred: {e}")

def check_and_send_msgs():
    with app.app_context():
        try:
            current_time = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%H:%M")
            print(f"Current Time: {current_time}")

            # Query the database for routines with matching time
            routines = DailyRoutine.query.filter_by(time=current_time).all()

            for routine in routines:
                to_phone_number = '+91'+str(routine.mobile)
                event = routine.event

                # Translate event message into multiple languages
                translated_messages = {}
                for language in ['te', 'en', 'ta', 'kn', 'hi']:  # Telugu, English, Tamil, Kannada, Hindi
                    translated_event = translate_message(event, language)
                    translated_messages[language] = translated_event

                # Prepare email body with content in all languages
                msg_body = "Your Daily Remainder"
                for language, translated_event in translated_messages.items():
                    msg_body += f"{language.upper()}: {translated_event}\n"

                try:
                    send_msg(to_phone_number, msg_body)
                    print(f"Message sent successfully to {to_phone_number}")
                except Exception as e:
                    print(f"Error sending message to {to_phone_number}: {e}")

                # Print values to console
                print(f"Routine ID: {routine.id}, Time: {routine.time}, Event: {event}, Mobile: {to_phone_number}")

            print(f"Checked and sent messages at {current_time}")

            # Commit changes to the database
            db.session.commit()

        except Exception as e:
            # Rollback in case of an error
            db.session.rollback()
            print(f"An error occurred: {e}")

def send_msg_at_6():
    with app.app_context():
        users = User.query.all()
        body = "NEW MESSAGE FROM PREGBOT!!! Here is the link you requested: https://pregbot-app.onrender.com/form"
        for user in users:
            send_msg('+91'+str(user.mobile), body)

if __name__ == "__main__":
  # Replace with your actual secret key
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0",debug=False,port=port)
