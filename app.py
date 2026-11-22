import sqlite3
from database import init_sqlite_db, get_mongo_collection
import os
from flask import Flask, render_template, render_template_string, request, redirect, flash, session, url_for
import pandas as pd
import pymongo
import bcrypt
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env', override=True)  # Load environment variables from .env file

# Initialize Flask app
import secrets

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # Limit file upload size to 5MB
app.secret_key = os.environ["FLASK_SECRET_KEY"]  # Use secret key from environment variable

# MongoDB connection setup

collection = get_mongo_collection()


# SQLite connection setup

init_sqlite_db()

# Route for home page
@app.route('/')
def home():
    return render_template('home.html')

# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        customer_id = request.form['customer_id']
        gender = request.form['gender']
        age = request.form['age']
        password = request.form['password']
        
        # Hash the password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Store user information in SQLite
        try:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, customer_id, gender, age, password_hash) VALUES (?, ?, ?, ?, ?)",
                           (username, customer_id, gender, age, password_hash))
            conn.commit()
            conn.close()
            flash("User registered successfully!", "success")
            return redirect('/view_users')
        except sqlite3.IntegrityError:
            flash("Customer ID already exists. Please choose a unique ID.", "danger")

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, password_hash FROM users WHERE username = ?",
            (username,)
        )
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.checkpw(
            password.encode('utf-8'), user[1]
        ):
            session.clear()
            session['user_id'] = user[0]
            return redirect(url_for('home'))

        flash('Invalid username or password', 'danger')

    return render_template_string('''
        <h2>Login</h2>

        {% for category, message in get_flashed_messages(with_categories=true) %}
    <p style="color: red;">{{ message }}</p>
{% endfor %}

        <form method="POST">
            <input name="username" placeholder="Username" required>
            <input name="password" type="password"
                   placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    ''')
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Route to display user registration data (without showing password)
@app.route('/view_users')
def view_users():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, customer_id, gender, age FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template('view_users.html', users=users)

# Route to load CSV file into MongoDB
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            df = pd.read_csv(file)
            records = df.to_dict(orient='records')
            collection.insert_many(records)
            flash("Data has been successfully stored!", "success")
            return redirect('/view')  # Redirect to view page after uploading

    return render_template('upload.html')

# Route to view all data from MongoDB
@app.route('/view')
def view():
    if 'user_id' not in session:
        return redirect(url_for('login'))
       
    data = list(collection.find())
    return render_template('view.html', data=data)

# Route to search and display shopping info for a specific Customer ID
@app.route('/user_shopping', methods=['GET', 'POST'])
def user_shopping():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        
        # Fetch user details from SQLite
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE customer_id = ?", (customer_id,))
        user = cursor.fetchone()
        conn.close()

        if user:
            # Fetch shopping data from MongoDB based on Customer ID
            shopping_data = list(collection.find({"customer_id": customer_id}))
            return render_template('user_shopping.html', username=user[0], shopping_data=shopping_data)
        else:
            flash("Customer ID not found.", "danger")
    
    return render_template('search_shopping.html')

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)  # Set use_reloader=False to avoid double execution in some environments