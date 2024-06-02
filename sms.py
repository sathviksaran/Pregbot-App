import logging
import signal
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import time
from googletrans import Translator
from twilio.rest import Client
import schedule  # Import schedule library

# Twilio account credentials
account_sid = 'AC4923a8ee90fd7a3ca656b5e063edeb45'
auth_token = '9530ba9aa237e3cfbc9d20ffdedb2546'

# Initialize Twilio client
client = Client(account_sid, auth_token)

app = Flask(__name__)

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

def send_msg(to_phone_number, message):
    message = client.messages.create(
            body=message,
            from_='+15075568490',
            to=to_phone_number
        )

def translate_message(message, target_language):
    translator = Translator()
    translated_message = translator.translate(message, dest=target_language).text
    return translated_message

def check_and_send_msgs():
    with app.app_context():
        try:
            current_time = datetime.now().strftime("%H:%M")
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
                    logging.info(f"Message sent successfully to {to_phone_number}")
                except Exception as e:
                    logging.error(f"Error sending message to {to_phone_number}: {e}")

                # Print values to console
                print(f"Routine ID: {routine.id}, Time: {routine.time}, Event: {event}, Mobile: {to_phone_number}")

            logging.info(f"Checked and sent messages at {current_time}")

            # Commit changes to the database
            db.session.commit()

        except Exception as e:
            # Rollback in case of an error
            db.session.rollback()
            logging.error(f"An error occurred: {e}")

def send_msg_at_6():
    with app.app_context():
        users = User.query.all()
        body = "NEW MESSAGE FROM PREGBOT!!! Here is the link you requested: http://finally-merry-tadpole.ngrok-free.app/form"
        for user in users:
            send_msg('+91'+str(user.mobile), body)

def signal_handler(signal, frame):
    logging.info("Shutting down gracefully...")
    sys.exit(0)

if __name__ == "__main__":
    logging.basicConfig(filename='message_scheduler.log', level=logging.INFO)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Schedule sending the email at 6:00 every day
    schedule.every().day.at("10:26").do(send_msg_at_6)
    
    while True:
        schedule.run_pending()
        check_and_send_msgs()
        # Wait for a certain interval before checking again
        time.sleep(60)  # Wait for 60 seconds (1 minute) before checking again
