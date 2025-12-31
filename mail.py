import logging
import signal
import sys
# from flask_mail import Message
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# from flask_mail import Mail
from datetime import datetime
import time
from googletrans import Translator
import schedule  # Import schedule library
import os
import requests

app = Flask(__name__)

# Configure Flask-Mail
# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 587  # Use the appropriate port
# app.config['MAIL_USE_TLS'] = True  # Or MAIL_USE_SSL=True for SSL
# app.config['MAIL_USERNAME'] = 'mypregbot@gmail.com'
# app.config['MAIL_PASSWORD'] = 'ijaefbyibmwtmobf'
# app.config['MAIL_DEFAULT_SENDER'] = 'mypregbot@gmail.com'

# mail = Mail(app)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://freedb_pregbot:#Da!C*5t39JWnUv@sql.freedb.tech:3306/freedb_Pregbot'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 3600,  # Set a reasonable pool_recycle time in seconds
}
db = SQLAlchemy(app)

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

def translate_message(message, target_language):
    translator = Translator()
    translated_message = translator.translate(message, dest=target_language).text
    return translated_message

def check_and_send_emails():
    with app.app_context():
        try:
            current_time = datetime.now().strftime("%H:%M")
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
                    logging.info(f"Email sent successfully to {recipient}")
                except Exception as e:
                    logging.error(f"Error sending email to {recipient}: {e}")

                # Print values to console
                print(f"Routine ID: {routine.id}, Time: {routine.time}, Event: {event}, Email: {recipient}")

            logging.info(f"Checked and sent emails at {current_time}")

            # Commit changes to the database
            db.session.commit()

        except Exception as e:
            # Rollback in case of an error
            db.session.rollback()
            logging.error(f"An error occurred: {e}")

def send_email_at_6():
    with app.app_context():
        users = User.query.all()
        subject = "Daily Link Reminder"
        body = "Here is the link you requested: http://finally-merry-tadpole.ngrok-free.app/form"
        for user in users:
            send_email(user.email, subject, body)

def signal_handler(signal, frame):
    logging.info("Shutting down gracefully...")
    sys.exit(0)

if __name__ == "__main__":
    logging.basicConfig(filename='email_scheduler.log', level=logging.INFO)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Schedule sending the email at 6:00 every day
    schedule.every().day.at("10:26").do(send_email_at_6)
    
    while True:
        schedule.run_pending()
        check_and_send_emails()
        # Wait for a certain interval before checking again
        time.sleep(60)  # Wait for 60 seconds (1 minute) before checking again
