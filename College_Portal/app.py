from flask import Flask, render_template, request, redirect, url_for, flash, session, g
import os
from datetime import datetime
import psycopg2 # Import psycopg2 for PostgreSQL
from werkzeug.security import generate_password_hash, check_password_hash # For password hashing (future proofing)

app = Flask(__name__)
# Set a strong secret key for session management
# It's highly recommended to set this as an environment variable in production.
# For local development, this fallback is fine, but change it to a random string.
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'a_very_secret_and_random_key_for_your_app')

# Database configuration
DB_HOST = 'localhost'
DB_NAME = 'college_portal_db' # Changed database name
DB_USER = 'postgres'
DB_PASSWORD = '1234'
DB_PORT = '5432'

# --- Database Connection Management ---
def get_db():
    """Establishes a new database connection if one doesn't exist for the current request."""
    if 'db' not in g:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                port=DB_PORT
            )
            g.db = conn
        except psycopg2.Error as e:
            flash(f"Database connection error: {e}", 'danger')
            g.db = None # Ensure g.db is None if connection fails
            print(f"Database connection failed: {e}") # Log the error
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    """Closes the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

# --- Context Processor ---
# This makes `current_user` and `now` available in all templates
@app.before_request
def load_logged_in_user():
    """Load the current user before each request if user_id is in session."""
    user_id = session.get('user_id')
    g.user = None # Initialize g.user to None

    if user_id is not None:
        conn = get_db()
        if conn:
            cur = conn.cursor()
            try:
                cur.execute("SELECT username, role, name FROM users WHERE username = %s", (user_id,))
                user_data = cur.fetchone()
                if user_data:
                    g.user = {
                        "username": user_data[0],
                        "role": user_data[1],
                        "name": user_data[2]
                    }
            except psycopg2.Error as e:
                flash(f"Error fetching user data: {e}", 'danger')
                print(f"Error fetching user data: {e}")
            finally:
                cur.close()

@app.context_processor
def inject_user():
    """Injects the global user object and current datetime into all templates."""
    return dict(current_user=g.user, now=datetime.now())

# --- Decorators ---
def login_required(view):
    """Decorator to protect routes that require authentication."""
    from functools import wraps
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login', next=request.url))
        return view(*args, **kwargs)
    return wrapped_view

def role_required(role_name):
    """Decorator to protect routes that require a specific role."""
    def decorator(view):
        from functools import wraps
        @wraps(view)
        @login_required # Ensure user is logged in first
        def wrapped_view(*args, **kwargs):
            if g.user and g.user.get('role') == role_name:
                return view(*args, **kwargs)
            else:
                flash(f'You do not have permission to access this page. Required role: {role_name.capitalize()}', 'danger')
                return redirect(url_for('dashboard')) # Redirect to dashboard or home
        return wrapped_view
    return decorator

# --- Routes ---

@app.route('/')
def index():
    """Homepage of the college portal."""
    # Dummy upcoming events - in a real app, these would come from a database
    upcoming_events = [
        {"title": "Fall Semester Registration Opens", "date": "July 15, 2025", "description": "Get ready to enroll in your fall courses!"},
        {"title": "Welcome Back Picnic", "date": "August 20, 2025", "description": "Join us for food, games, and fun to kick off the new academic year."},
        {"title": "Career Fair 2025", "date": "September 10, 2025", "description": "Connect with top employers and explore job opportunities."}
    ]
    return render_template('index.html', upcoming_events=upcoming_events)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route."""
    if g.user:
        flash('You are already logged in.', 'info')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        next_url = request.args.get('next')

        conn = get_db()
        if not conn:
            flash("Could not connect to the database. Please try again later.", "danger")
            return render_template('login.html')

        cur = conn.cursor()
        user_data = None
        try:
            cur.execute("SELECT username, password, role, name FROM users WHERE username = %s", (username,))
            user_data = cur.fetchone()
        except psycopg2.Error as e:
            flash(f"Error during login query: {e}", 'danger')
            print(f"Error during login query: {e}")
        finally:
            cur.close()

        if user_data:
            # In a real app, use check_password_hash(user_data[1], password)
            if password == user_data[1]: # Simple password check for demonstration
                session['user_id'] = user_data[0]
                flash('Login successful!', 'success')
                return redirect(next_url or url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'danger')
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout route."""
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard accessible after login."""
    return render_template('dashboard.html')

@app.route('/admin')
@role_required('admin')
def admin_panel():
    """Admin panel - only accessible by users with 'admin' role."""
    return render_template('admin_panel.html', message="Welcome to the Admin Panel!")

@app.route('/student')
@role_required('student')
def student_portal():
    """Student portal - only accessible by users with 'student' role."""
    return render_template('student_portal.html', message="Welcome to the Student Portal!")

@app.route('/faculty')
@role_required('faculty')
def faculty_portal():
    """Faculty portal - only accessible by users with 'faculty' role."""
    return render_template('faculty_portal.html', message="Welcome to the Faculty Portal!")

if __name__ == '__main__':
    app.run(debug=True)