import psycopg2
from MySQLdb import connect
from flask import Flask, render_template, request, redirect, url_for, session, flash, current_app
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import MySQLdb.cursors
import os
import uuid  # Import for generating unique filenames

app = Flask(__name__)
app.secret_key = 'ijijijijiskolmdo2nmdnoqind@9-r1324r1=pe3or240t2492o3-921jg-13k'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'login_system'  # Use MYSQL_DB for the database name

mysql = MySQL(app)

app.config['UPLOAD_FOLDER'] = 'static/uploads'
# Updated ALLOWED_EXTENSIONS to include video formats
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov'}
# Updated MAX_FILE_SIZE to 10MB as indicated in your HTML
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/test_db')
def test_db():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT DATABASE();")
        db_name = cursor.fetchone()
        return f"Connected to database: {db_name[0]}"  # Access the first element of the tuple
    except Exception as e:
        return f"Database connection error: {e}"


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]
        phone = request.form["phone"]
        email = request.form["email"]

        if not all([username, password, email, phone]):
            flash('Please fill out all fields!', 'alert-danger')
            return render_template('register.html')

        hashed_password = generate_password_hash(password)

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()

        if account:
            flash('Username already exists!', 'alert-danger')
            return render_template('register.html')

        try:
            cursor.execute('INSERT INTO users (username, password, email, phone_number) VALUES (%s, %s, %s, %s)',
                           (username, hashed_password, email, phone))
            mysql.connection.commit()
            flash('Registration successful! You can now log in.', 'alert-success')
            return redirect(url_for('login'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'An error occurred during registration: {e}', 'alert-danger')
            # For debugging, you might want to print the actual error:
            # print(f"Registration error: {e}")
            return render_template('register.html')
        finally:
            cursor.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username_input = request.form["username"]
        password = request.form["password"]

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s OR phone_number = %s OR email = %s',
                       (username_input, username_input, username_input))
        account = cursor.fetchone()
        cursor.close()

        if account and check_password_hash(account['password'], password):
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            flash('Logged in successfully!', 'alert-success')
            return redirect(url_for('home'))
        else:
            flash('Incorrect username/email/phone number or password!', 'alert-danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'alert-info')
    return redirect(url_for('login'))


@app.route('/home')
def home():
    if 'loggedin' in session:
        return render_template('home.html', username=session['username'])
    flash('Please log in to access this page.', 'alert-warning')
    return redirect(url_for('login'))


@app.route('/profile')
def profile():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT id, username, email, phone_number FROM users WHERE id = %s', (session['id'],))
        account = cursor.fetchone()

        # Fetch uploaded media files for the user
        # This assumes you have a 'user_media' table or similar
        # For simplicity, if you're only allowing ONE profile image/video stored in 'users.image'
        # you would fetch 'image' from the 'users' table directly.
        # Let's adjust this assuming we are now storing a single 'profile_media' filename in the 'users' table
        # For a more robust solution, you'd create a separate 'user_media' table.

        # Adjusted to fetch 'image' from users table, assuming it stores the path to the current profile media
        cursor.execute('SELECT image FROM users WHERE id = %s', (session['id'],))
        profile_media = cursor.fetchone()
        current_profile_image = profile_media['image'] if profile_media and 'image' in profile_media else None

        cursor.close()

        if account:
            # Pass the current profile image filename to the template
            return render_template('profile.html', account=account, current_profile_image=current_profile_image)
        else:
            flash('Account not found.', 'alert-danger')
            return redirect(url_for('home'))
    flash('Please log in to view your profile.', 'alert-warning')
    return redirect(url_for('login'))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/assessments')
def assessments():
    flash('Access to assessments is restricted.', 'alert-warning')
    return render_template('assessments.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'loggedin' not in session:
        flash('Please log in to upload files.', 'alert-warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No file part in the request.', 'alert-danger')
            return redirect(request.url)

        uploaded_file = request.files['image']

        if uploaded_file.filename == '':
            flash('No selected file.', 'alert-danger')
            return redirect(request.url)

        if uploaded_file and allowed_file(uploaded_file.filename):
            uploaded_file.seek(0, os.SEEK_END)
            file_size = uploaded_file.tell()
            uploaded_file.seek(0)

            if file_size > MAX_FILE_SIZE:
                flash(f'File size exceeds limit ({MAX_FILE_SIZE / (1024 * 1024):.0f}MB).', 'alert-danger')
                return redirect(request.url)

            unique_filename = str(uuid.uuid4()) + os.path.splitext(uploaded_file.filename)[1]
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

            cursor = None
            try:
                uploaded_file.save(filepath)

                cursor = mysql.connection.cursor()

                cursor.execute("UPDATE users SET image = %s WHERE id = %s",
                               (unique_filename, session['id']))
                mysql.connection.commit()
                flash('File uploaded and profile updated successfully!', 'alert-success')
                return redirect(url_for('profile'))
            except Exception as e:
                mysql.connection.rollback()
                flash(f'An error occurred during upload or database update: {e}', 'alert-danger')
                current_app.logger.error(f"Upload error: {e}")  # Use current_app.logger for better logging
                if os.path.exists(filepath):
                    os.remove(filepath)  # Clean up partially uploaded file
            finally:
                if cursor:
                    cursor.close()
        else:
            flash('Invalid file type. Allowed: PNG, JPG, JPEG, GIF, MP4, AVI, MOV.', 'alert-danger')

    return redirect(url_for('profile'))


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)