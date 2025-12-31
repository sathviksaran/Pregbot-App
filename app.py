from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import nltk
import random
import numpy as np
import json
import pickle
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.models import load_model # type: ignore
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from googletrans import Translator
from flask_mail import Message,Mail
from twilio.rest import Client
import os


nltk.download('wordnet')
nltk.download('punkt')
nltk.download('omw-1.4')

lemmatizer = WordNetLemmatizer()
with open('bot.json') as json_file:
    intents = json.load(json_file)

words = pickle.load(open('words.pkl', 'rb'))
classes = pickle.load(open('classes.pkl', 'rb'))
model = load_model('chatbotmodel.h5')


app = Flask(__name__)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587  # Use the appropriate port
app.config['MAIL_USE_TLS'] = True  # Or MAIL_USE_SSL=True for SSL
app.config['MAIL_USERNAME'] = 'mypregbot@gmail.com'
app.config['MAIL_PASSWORD'] = 'ijaefbyibmwtmobf'
app.config['MAIL_DEFAULT_SENDER'] = 'mypregbot@gmail.com'

mail = Mail(app)

# Twilio account credentials
account_sid = 'AC4923a8ee90fd7a3ca656b5e063edeb45'
auth_token = '9530ba9aa237e3cfbc9d20ffdedb2546'
client = Client(account_sid, auth_token)
def send_msg(to_phone_number, message):
    message = client.messages.create(
            body=message,
            from_='+15075568490',
            to=to_phone_number
        )

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://freedb_pregbot:#Da!C*5t39JWnUv@sql.freedb.tech:3306/freedb_Pregbot'
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
            msg = Message(subject='New message from PREGBOT',
                        recipients=['mypregbot@gmail.com'])  # Admin's email
            msg.body = f"Name: {name}\nEmail: {email}\nMessage: {message}"
            mail.send(msg)
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
    text = request.form['text']
    target_language = request.form['target_language']
    
    translator = Translator()
    
    try:
        translated_text = translator.translate(text, dest=target_language).text
        return jsonify({'translated_text': translated_text}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/find')
def find_hospitals():
    user = session['username']
    return render_template('find.html',username=user)

@app.route('/chat', methods=['POST'])
def chat():
    if request.method == 'POST':
        message = request.form['message']

        if message.lower() == 'quit':
            return jsonify({'response': 'Goodbye!'})

        ints = predict_class(message)
        resp = get_response(ints, intents)

        return jsonify({'response': resp})

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
            msg = Message(subject='NEW USER REGISTERED IN PREGBOT',
                    recipients=['mypregbot@gmail.com'])  # Admin's email
            msg.body = f"Name: {new_user.username}\nEmail: {new_user.email}\nMobile No: {new_user.mobile}"
            mail.send(msg)
            msg1 = Message(subject='PREGBOT USER REGISTRATION SUCCESSFUL',
                           recipients=[str(new_user.email)])
            msg1.body = f"Name: {new_user.fullname}\nUsername: {new_user.username}\nEmail: {new_user.email}\nMobile No: {new_user.mobile}"
            mail.send(msg1)
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

def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word) for word in sentence_words]
    return sentence_words

def bag_of_words(sentence):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for w in sentence_words:
        for i, word in enumerate(words):
            if word == w:
                bag[i] = 1
    return np.array(bag)

def predict_class(sentence):
    bow = bag_of_words(sentence)
    res = model.predict(np.array([bow]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]

    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({'intent': classes[r[0]], 'probability': str(r[1])})
    return return_list

def get_response(intents_list, intents_json):
    tag = intents_list[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if i['tag'] == tag:
            result = random.choice(i['responses'])
            break
    return result

if __name__ == "__main__":
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev-fallback-key")
  # Replace with your actual secret key
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0",debug=False,port=port)
