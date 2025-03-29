import os
from flask import Flask, render_template, request, redirect, url_for, make_response
import firebase_admin
from firebase_admin import credentials, auth, firestore
import jwt             # pip install PyJWT
import datetime
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['FIREBASE_API_KEY'] = os.getenv('FIREBASE_API_KEY')
app.config['FIREBASE_AUTH_DOMAIN'] = os.getenv('FIREBASE_AUTH_DOMAIN')
app.config['FIREBASE_DATABASE_URL'] = os.getenv('FIREBASE_DATABASE_URL')
app.config['FIREBASE_PROJECT_ID'] = os.getenv('FIREBASE_PROJECT_ID')
app.config['FIREBASE_STORAGE_BUCKET'] = os.getenv('FIREBASE_STORAGE_BUCKET')
app.config['FIREBASE_MESSAGING_SENDER_ID'] = os.getenv('FIREBASE_MESSAGING_SENDER_ID')
app.config['FIREBASE_APP_ID'] = os.getenv('FIREBASE_APP_ID')
# Initialize Firebase Admin SDK
cred = credentials.Certificate("firebase.json")  # Use the path to your service account key file
firebase_admin.initialize_app(cred)
db = firestore.client()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        email = request.form['email']
        mobile = request.form['mobile']
        password = request.form['password']

        try:
            # Create user in Firebase Authentication
            user = auth.create_user(
                email=email,
                password=password,
                display_name=name,
            )

            # Store additional user data in Firestore
            doc_ref = db.collection("users").document(user.uid)
            doc_ref.set({
                "uid": user.uid,
                "name": name,
                "age": int(age),
                "gender": gender,
                "email": email,
                "mobile": mobile
            })

            return redirect(url_for('login'))

        except Exception as e:
            return f"An error occurred: {e}"

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']  # Note: Firebase Admin SDK cannot validate passwords

        try:
            # Get user by email (assumes that the user exists and the password is correct)
            user = auth.get_user_by_email(email)
            # In a real app, authenticate the password using an alternate method

            # Generate a JWT token containing the user's uid and email 
            token = jwt.encode({
                'uid': user.uid,
                'email': user.email,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
            }, app.config['SECRET_KEY'], algorithm='HS256')

            # Create a response with token cookie set
            resp = make_response(redirect(url_for('dashboard')))
            resp.set_cookie('jwt_token', token)
            return resp

        except Exception as e:
            return f"An error occurred: {e}"

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    token = request.cookies.get('jwt_token')
    if not token:
        return redirect(url_for('login'))
    try:
        # Validate token
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return render_template('dashboard.html')
    except Exception as e:
        return redirect(url_for('login'))

@app.route('/alerts')
def alerts():
    token = request.cookies.get('jwt_token')
    if not token:
        return redirect(url_for('login'))
    try:
        # Validate token
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return render_template('alerts.html', config=app.config)
    except Exception as e:
        return redirect(url_for('login'))
    
@app.route('/profile')
def profile():
    token = request.cookies.get('jwt_token')
    if not token:
        return redirect(url_for('login'))
    try:
        # Validate token
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return render_template('profile.html', config=app.config)
    except Exception as e:
        return redirect(url_for('login'))
if __name__ == '__main__':
    app.run(debug=True)