from flask import Flask, render_template, request, redirect, url_for, flash, session, g
import os
from datetime import datetime
import psycopg2
from psycopg2 import errors as pg_errors
from werkzeug.security import generate_password_hash, check_password_hash
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'a_very_secret_and_random_key_for_your_app')

# Define a global college name
COLLEGE_NAME = "Evergreen University"

# Database configuration
DB_HOST = 'localhost'
DB_NAME = 'college_portal_db'
DB_USER = 'postgres'
DB_PASSWORD = '1234'
DB_PORT = '5432'


# --- Database Connection Management ---
def get_db():
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
            print(f"Database connection error: {e}")
            g.db = None
            raise RuntimeError(f"Failed to connect to database: {e}") from e
    return g.db


@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


# --- Logging Function ---
def log_action(user_id, action_type, description):
    """Logs an administrative or user action to the database."""
    conn = get_db()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO logs (user_id, action_type, description) VALUES (%s, %s, %s)",
                (user_id, action_type, description)
            )
            conn.commit()
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Error logging action: {e}")
        finally:
            cur.close()


# --- Database Initialization ---
def init_db():
    conn = None
    cur = None
    try:
        conn = get_db()
        if conn is None:
            print("Cannot initialize database: Connection failed (get_db returned None).")
            return

        cur = conn.cursor()
        print("Attempting to initialize database tables...")

        # Create Users table (modified to include status, department, and matric_number columns)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'faculty', 'admin')),
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'expelled')),
                department VARCHAR(100),
                matric_number VARCHAR(20) UNIQUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        print("Users table checked/created/updated with status, department, and matric_number columns.")

        # Create Courses table
        cur.execute("""
           CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    course_code VARCHAR(10) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    credits NUMERIC(3, 1) NOT NULL CHECK (credits > 0),
    faculty_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    department VARCHAR(100), -- New: Department for courses
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
        """)
        conn.commit()
        print("Courses table checked/created.")

        # Create Enrollments table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS enrollments (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
                enrollment_date DATE DEFAULT CURRENT_DATE,
                UNIQUE (user_id, course_id)
            );
        """)

        conn.commit()
        print("Enrollments table checked/created.")

        # Create Grades table (without score/grade_value initially, then alter)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS grades (
                id SERIAL PRIMARY KEY,
                enrollment_id INTEGER REFERENCES enrollments(id) ON DELETE CASCADE UNIQUE NOT NULL,
                graded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                grade_date DATE DEFAULT CURRENT_DATE
            );
        """)
        conn.commit()
        print("Grades table checked/created.")

        # Add 'grade_value' column if it doesn't exist (robustly)
        try:
            cur.execute("""
                DO $$ BEGIN
                    ALTER TABLE grades ADD COLUMN grade_value VARCHAR(5);
                EXCEPTION
                    WHEN duplicate_column THEN RAISE NOTICE 'column grade_value already exists in grades.';
                END $$;
            """)
            conn.commit()
            print("Ensured 'grade_value' column exists in grades table.")
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Error ensuring 'grade_value' column: {e}")

        # Add 'score' column if it doesn't exist (robustly)
        try:
            cur.execute("""
                DO $$ BEGIN
                    ALTER TABLE grades ADD COLUMN score NUMERIC(5, 2);
                EXCEPTION
                    WHEN duplicate_column THEN RAISE NOTICE 'column score already exists in grades.';
                END $$;
            """)
            conn.commit()
            print("Ensured 'score' column exists in grades table.")
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Error ensuring 'score' column: {e}")

        # Create Announcements table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                posted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                posted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        print("Announcements table checked/created.")

        # Create Housing Applications table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS housing_applications (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                student_id VARCHAR(50) NOT NULL,
                full_name VARCHAR(255) NOT NULL,
                email VARCHAR(120) NOT NULL,
                preferred_hall VARCHAR(50),
                semester VARCHAR(50) NOT NULL,
                notes TEXT,
                application_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected'))
            );
        """)
        conn.commit()
        print("Housing Applications table checked/created.")

        # New: Create Logs table for system activities
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                action_type VARCHAR(100) NOT NULL,
                description TEXT
            );
        """)
        conn.commit()
        print("Logs table checked/created.")

        # Create Indexes (use IF NOT EXISTS as well for safety)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_courses_code ON courses (course_code);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_enrollments_user_course ON enrollments (user_id, course_id);")
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_housing_applications_student_id ON housing_applications (student_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs (timestamp);")
        conn.commit()
        print("Database indexes checked/created.")

        print("Database tables and indexes initialization complete.")

        # Optional: Insert initial dummy data if users table is empty
        cur.execute("SELECT COUNT(*) FROM users;")
        if cur.fetchone()[0] == 0:
            print("Inserting initial dummy users...")
            try:
                # Initial users
                users_to_insert = [
                    ('student1', generate_password_hash('password123'), 'student1@college.edu', 'student', 'Alice',
                     'Smith', 'active', 'Computer Science', '2023-CS-001'), # Added department and matric_number
                    ('admin1', generate_password_hash('adminpass'), 'admin1@college.edu', 'admin', 'Bob', 'Johnson',
                     'active', None, None), # Admin has no department or matric number
                ]

                # Adding 10 more detailed dummy faculty members
                faculty_data = [
                    ('faculty1', 'faculty123', 'faculty1@college.edu', 'Dr. Carol', 'White', 'Computer Science',
                     'Professor',
                     'Dr. Carol White is a leading expert in Artificial Intelligence and Machine Learning. Her research focuses on natural language processing and robotics, with numerous publications in top-tier journals. She is passionate about mentoring students in cutting-edge AI projects.',
                     ["Artificial Intelligence", "Machine Learning", "Natural Language Processing"],
                     ["Foundations of AI (2023)", "Robotics and Advanced Automation (2022)"]),
                    ('faculty2', 'faculty2pass', 'faculty2@college.edu', 'Prof. David', 'Miller', 'English Literature',
                     'Associate Professor',
                     'Professor David Miller specializes in modern and contemporary American literature. His work explores themes of identity and societal change, and he is known for his engaging lectures on literary theory and creative writing workshops.',
                     ["Modern American Literature", "Literary Criticism", "Creative Writing"],
                     ["Narratives of the American Dream (2024)", "The Poetics of the City (2021)"]),
                    ('faculty3', 'faculty3pass', 'faculty3@college.edu', 'Dr. Emily', 'Davis', 'Biology',
                     'Assistant Professor',
                     'Dr. Emily Davis is a molecular biologist with a keen interest in genetic engineering and bioinformatics. Her current research investigates gene editing techniques for disease prevention. She leads a vibrant lab and encourages undergraduate participation in research.',
                     ["Molecular Biology", "Genetics", "Bioinformatics"],
                     ["CRISPR Technologies (2023)", "Computational Biology Approaches (2022)"]),
                    ('faculty4', 'faculty4pass', 'faculty4@college.edu', 'Prof. Frank', 'Wilson',
                     'Business Administration', 'Professor',
                     'Professor Frank Wilson is an accomplished financial strategist with decades of experience in global markets. He teaches courses on corporate finance and investment strategies, bringing real-world case studies into the classroom.',
                     ["Corporate Finance", "Investment Banking", "Global Markets"],
                     ["Fundamentals of Financial Strategy (2023)", "Navigating Volatile Markets (2011)"]),
                    ('faculty5', 'faculty5pass', 'faculty5@college.edu', 'Dr. Grace', 'Taylor', 'Physics',
                     'Associate Professor',
                     'Dr. Grace Taylor\'s expertise lies in quantum mechanics and astrophysics. She is known for making complex scientific concepts accessible to students and is actively involved in projects related to dark matter research.',
                     ["Quantum Mechanics", "Astrophysics", "Cosmology"],
                     ["Introduction to Quantum Field Theory (2023)", "Exploring the Dark Universe (2020)"]),
                    ('faculty6', 'faculty6pass', 'faculty6@college.edu', 'Prof. Henry', 'Brown', 'History', 'Professor',
                     'Professor Henry Brown is a renowned historian specializing in ancient civilizations and classical studies. His lectures are celebrated for their depth and storytelling, bringing historical events to life.',
                     ["Ancient Civilizations", "Classical Studies", "Archaeology"],
                     ["The Rise and Fall of Empires (2024)", "Daily Life in Ancient Rome (2022)"]),
                    ('faculty7', 'faculty7pass', 'faculty7@college.edu', 'Dr. Ivy', 'Clark', 'Environmental Science',
                     'Assistant Professor',
                     'Dr. Ivy Clark is passionate about sustainable development and climate change mitigation. Her research focuses on renewable energy sources and environmental policy.',
                     ["Sustainable Development", "Climate Change", "Renewable Energy"],
                     ["Policy for a Greener Tomorrow (2023)", "Harnessing Solar Power (2021)"]),
                    ('faculty8', 'faculty8pass', 'faculty8@college.edu', 'Prof. Jack', 'Lewis', 'Mathematics',
                     'Professor',
                     'Professor Jack Lewis is an expert in pure mathematics, particularly in algebraic topology and number theory. He is committed to fostering a love for abstract thinking and problem-solving in his students.',
                     ["Algebraic Topology", "Number Theory", "Mathematical Logic"],
                     ["Abstract Algebra Reimagined (2024)", "The Beauty of Numbers (2022)"]),
                    ('faculty9', 'faculty9pass', 'faculty9@college.edu', 'Dr. Karen', 'Hall', 'Psychology',
                     'Associate Professor',
                     'Dr. Karen Hall specializes in cognitive psychology and behavioral neuroscience. Her research explores how the brain processes information and influences human behavior.',
                     ["Cognitive Psychology", "Neuroscience", "Behavioral Analysis"],
                     ["Understanding the Human Mind (2023)", "Neural Pathways of Learning (2021)"]),
                    ('faculty10', 'faculty10pass', 'faculty10@college.edu', 'Prof. Liam', 'Young', 'Chemistry',
                     'Professor',
                     'Professor Liam Young is a leading researcher in organic chemistry and drug discovery. His lab is at the forefront of developing new therapeutic compounds.',
                     ["Organic Chemistry", "Medicinal Chemistry", "Drug Discovery"],
                     ["Synthesis of Novel Compounds (2024)", "Targeted Drug Delivery Systems (2023)"]),
                ]

                for data in faculty_data:
                    users_to_insert.append((
                        data[0], generate_password_hash(data[1]), data[2], 'faculty', data[3], data[4], 'active', None, None
                    ))

                # Add some more dummy students
                for i in range(2, 6):  # student2 to student5
                    users_to_insert.append((
                        f'student{i}',
                        generate_password_hash(f'student{i}pass'),
                        f'student{i}@college.edu',
                        'student',
                        f'StudentFN{i}',
                        f'StudentLN{i}',
                        'active',
                        random.choice(['Computer Science', 'Engineering', 'Medicine', 'Arts']), # Assign random department
                        f'2023-ST-{i:03d}' # Dummy matric number
                    ))

                cur.executemany(
                    "INSERT INTO users (username, password_hash, email, role, first_name, last_name, status, department, matric_number) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    users_to_insert
                )
                conn.commit()
                print("Initial dummy users and additional faculty inserted successfully.")
            except pg_errors.UniqueViolation:
                conn.rollback()
                print("Dummy users already exist (unique violation). Skipping insertion.")
            except Exception as e:
                conn.rollback()
                print(f"Error inserting dummy users: {e}")
        else:
            print("Users table is not empty. Skipping dummy user insertion.")

        # Optional: Insert some dummy announcements if the table is empty
        cur.execute("SELECT COUNT(*) FROM announcements;")
        if cur.fetchone()[0] == 0:
            print("Inserting initial dummy announcements...")
            try:
                cur.execute("""
                    INSERT INTO announcements (title, content, posted_by) VALUES
                    ('Campus Closed for Holiday', 'The campus will be closed on July 4th for Independence Day. Classes will resume on July 5th.', (SELECT id FROM users WHERE username = 'admin1')),
                    ('New Course Registration Open', 'Registration for Fall 2025 semester courses is now open. Log in to your dashboard to register.', (SELECT id FROM users WHERE username = 'admin1')),
                    ('Student Orientation Day', 'New student orientation will be held on August 25th in the Main Auditorium. All new students must attend.', (SELECT id FROM users WHERE username = 'admin1'))
                    ON CONFLICT DO NOTHING;
                """)
                conn.commit()
                print("Initial dummy announcements inserted successfully.")
            except Exception as e:
                conn.rollback()
                print(f"Error inserting dummy announcements: {e}")
        else:
            print("Announcements table is not empty. Skipping dummy announcement insertion.")

        # Optional: Insert dummy courses if the table is empty
        cur.execute("SELECT COUNT(*) FROM courses;")
        if cur.fetchone()[0] == 0:
            print("Inserting initial dummy courses...")
            try:
                # Helper to get faculty ID reliably
                def get_faculty_id(username):
                    cur.execute("SELECT id FROM users WHERE username = %s AND role = 'faculty'", (username,))
                    result = cur.fetchone()
                    return result[0] if result else None

                courses_to_insert = [
                    ('COMP101', 'Introduction to Programming',
                     'Foundational course in programming concepts using Python.', 3.0, get_faculty_id('faculty1')),
                    ('MATH201', 'Calculus I', 'First course in differential and integral calculus.', 4.0,
                     get_faculty_id('faculty8')),
                    ('ENG101', 'English Composition', 'Develops essential writing and critical thinking skills.', 3.0,
                     get_faculty_id('faculty2')),
                    ('PHYS101', 'General Physics I', 'Introduction to mechanics, heat, and waves.', 4.0,
                     get_faculty_id('faculty5')),
                    ('BIO205', 'Cell Biology', 'Study of cell structure, function, and molecular processes.', 3.0,
                     get_faculty_id('faculty3')),
                    ('HIST301', 'World History Since 1500',
                     'Exploration of global events and trends from the Renaissance to present.', 3.0,
                     get_faculty_id('faculty6')),
                    ('BUS310', 'Principles of Management',
                     'Overview of management theories and organizational practices.', 3.0, get_faculty_id('faculty4')),
                    ('CHEM105', 'General Chemistry I', 'Fundamental principles of chemistry and chemical reactions.',
                     4.0, get_faculty_id('faculty10')),
                    ('PSYCH101', 'Introduction to Psychology',
                     'Survey of major concepts, theories, and research methods in psychology.', 3.0,
                     get_faculty_id('faculty9')),
                    ('ENV201', 'Environmental Science Basics',
                     'An introduction to environmental issues and sustainable solutions.', 3.0,
                     get_faculty_id('faculty7')),
                ]

                for course_code, title, description, credits, faculty_id in courses_to_insert:
                    cur.execute(
                        "INSERT INTO courses (course_code, title, description, credits, faculty_id) VALUES (%s, %s, %s, %s, %s)",
                        (course_code, title, description, credits, faculty_id if faculty_id else None)
                    )
                conn.commit()
                print("Initial dummy courses inserted successfully.")
            except pg_errors.UniqueViolation:
                conn.rollback()
                print("Dummy courses already exist (unique violation). Skipping insertion.")
            except Exception as e:
                conn.rollback()
                print(f"Error inserting dummy courses: {e}")
        else:
            print("Courses table is not empty. Skipping dummy course insertion.")

        # Optional: Insert dummy enrollments if the table is empty
        cur.execute("SELECT COUNT(*) FROM enrollments;")
        if cur.fetchone()[0] == 0:
            print("Inserting initial dummy enrollments...")
            try:
                # Get some student and course IDs
                cur.execute("SELECT id FROM users WHERE role = 'student' LIMIT 2;")
                student_ids = [row[0] for row in cur.fetchall()]
                cur.execute("SELECT id FROM courses ORDER BY id LIMIT 3;")
                course_ids = [row[0] for row in cur.fetchall()]

                if student_ids and course_ids:
                    enrollments_to_insert = []
                    # Enroll student1 in COMP101 and MATH201
                    if len(student_ids) >= 1 and len(course_ids) >= 2:
                        enrollments_to_insert.append((student_ids[0], course_ids[0]))
                        enrollments_to_insert.append((student_ids[0], course_ids[1]))
                    # Enroll student2 in ENG101
                    if len(student_ids) >= 2 and len(course_ids) >= 3:
                        enrollments_to_insert.append((student_ids[1], course_ids[2]))

                    for user_id, course_id in enrollments_to_insert:
                        try:
                            cur.execute(
                                "INSERT INTO enrollments (user_id, course_id) VALUES (%s, %s) ON CONFLICT (user_id, course_id) DO NOTHING;",
                                (user_id, course_id)
                            )
                        except Exception as e:
                            print(f"Skipping enrollment for user {user_id} in course {course_id} due to error: {e}")

                    conn.commit()
                    print("Initial dummy enrollments inserted successfully.")
                else:
                    print("Not enough dummy students or courses to insert enrollments.")
            except Exception as e:
                conn.rollback()
                print(f"Error inserting dummy enrollments: {e}")
        else:
            print("Enrollments table is not empty. Skipping dummy enrollment insertion.")


    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print(f"An error occurred during database initialization: {e}")
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"An unexpected error occurred: {e}")
    finally:
        if cur:
            cur.close()


# --- Context Processor ---
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    g.user = None

    if user_id is not None:
        conn = get_db()
        if conn:
            cur = conn.cursor()
            try:
                # Fetch status, department, and matric_number along with other user details
                cur.execute(
                    "SELECT id, username, password_hash, email, role, first_name, last_name, status, department, matric_number FROM users WHERE username = %s",
                    (user_id,))
                user_data = cur.fetchone()
                if user_data:
                    g.user = {
                        "id": user_data[0],
                        "username": user_data[1],
                        "password_hash": user_data[2],
                        "email": user_data[3],
                        "role": user_data[4],
                        "first_name": user_data[5],
                        "last_name": user_data[6],
                        "status": user_data[7],
                        "department": user_data[8], # Added department
                        "matric_number": user_data[9], # Added matric_number
                        "name": f"{user_data[5]} {user_data[6]}"
                    }
                    if g.user['status'] in ['suspended', 'expelled']:
                        flash('Your account is currently suspended or expelled. Please contact administration.',
                              'danger')
                        session.pop('user_id', None)
                        g.user = None
            except psycopg2.Error as e:
                flash(f"Error fetching user data: {e}", 'danger')
                print(f"Error fetching user data: {e}")
            finally:
                cur.close()


@app.context_processor
def inject_user():
    return dict(current_user=g.user, now=datetime.now(), college_name=COLLEGE_NAME)


# --- Decorators ---
def login_required(view):
    from functools import wraps
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login', next=request.url))
        if g.user and g.user.get('status') in ['suspended', 'expelled']:
            flash('Your account is suspended or expelled. Access denied.', 'danger')
            session.pop('user_id', None)
            return redirect(url_for('login'))
        return view(*args, **kwargs)

    return wrapped_view


def role_required(role_name):
    def decorator(view):
        from functools import wraps
        @wraps(view)
        @login_required
        def wrapped_view(*args, **kwargs):
            if g.user and g.user.get('role') == role_name and g.user.get('status') == 'active':
                return view(*args, **kwargs)
            else:
                flash(f'You do not have permission to access this page. Required role: {role_name.capitalize()}',
                      'danger')
                return redirect(url_for('dashboard'))

        return wrapped_view

    return decorator


# --- Routes ---

@app.route('/')
def index():
    upcoming_events = []
    conn = get_db()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, title, content, posted_at FROM announcements ORDER BY posted_at DESC LIMIT 5;")
            raw_events = cur.fetchall()
            for event in raw_events:
                upcoming_events.append({
                    "id": event[0],
                    "title": event[1],
                    "description": event[2],
                    "date": event[3].strftime('%B %d, %Y')
                })
        except psycopg2.Error as e:
            flash(f"Error fetching announcements: {e}", 'danger')
            print(f"Error fetching announcements: {e}")
        finally:
            cur.close()

    return render_template('index.html', upcoming_events=upcoming_events)


@app.route('/login', methods=['GET', 'POST'])
def login():
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
            cur.execute(
                "SELECT username, password_hash, role, first_name, last_name, status FROM users WHERE username = %s",
                (username,))
            user_data = cur.fetchone()
        except psycopg2.Error as e:
            flash(f"Error during login query: {e}", 'danger')
            print(f"Error during login query: {e}")
        finally:
            cur.close()

        if user_data:
            if check_password_hash(user_data[1], password):
                user_status = user_data[5]
                if user_status in ['suspended', 'expelled']:
                    flash('Your account is currently suspended or expelled. Please contact administration.', 'danger')
                    return render_template('login.html', username=username)
                else:
                    session['user_id'] = user_data[0]
                    flash('Login successful!', 'success')
                    return redirect(next_url or url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'danger')
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if g.user:
        flash('You are already logged in. Please log out to register a new account.', 'info')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        email = request.form['email'].strip()
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        role = request.form['role'].strip()
        department = request.form.get('department') # Get department from form

        if not username or not password or not email or not first_name or not last_name or not role:
            flash('All fields are required.', 'danger')
            return render_template('register.html',
                                   username=username, email=email,
                                   first_name=first_name, last_name=last_name,
                                   selected_role=role, selected_department=department) # Pass selected_department

        if role not in ['student', 'faculty', 'admin']:
            flash('Invalid role selected.', 'danger')
            return render_template('register.html',
                                   username=username, email=email,
                                   first_name=first_name, last_name=last_name,
                                   selected_role=role, selected_department=department)

        if role == 'student' and not department:
            flash('Department is required for student registration.', 'danger')
            return render_template('register.html',
                                   username=username, email=email,
                                   first_name=first_name, last_name=last_name,
                                   selected_role=role, selected_department=department)

        conn = get_db()
        if not conn:
            flash("Could not connect to the database. Please try again later.", "danger")
            return render_template('register.html')

        cur = conn.cursor()
        try:
            cur.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
            if cur.fetchone():
                flash('Username or Email already exists. Please choose a different one.', 'danger')
                return render_template('register.html',
                                       username=username, email=email,
                                       first_name=first_name, last_name=last_name,
                                       selected_role=role, selected_department=department)

            hashed_password = generate_password_hash(password)
            matric_number = None

            if role == 'student':
                # Generate a simple matriculation number:YYYY-DEPT-XXXX (e.g., 2023-CS-001)
                year = datetime.now().year
                dept_code = department[:3].upper() # Take first 3 letters of department for code
                # Find the next available sequence number for the department and year
                cur.execute("SELECT COUNT(*) FROM users WHERE role = 'student' AND department = %s AND matric_number LIKE %s",
                            (department, f'{year}-{dept_code}-%'))
                count = cur.fetchone()[0]
                matric_number = f"{year}-{dept_code}-{count + 1:03d}"

            # Insert new user with default 'active' status, department, and matric_number
            cur.execute(
                "INSERT INTO users (username, password_hash, email, role, first_name, last_name, status, department, matric_number) VALUES (%s, %s, %s, %s, %s, %s, 'active', %s, %s) RETURNING id",
                (username, hashed_password, email, role, first_name, last_name, department, matric_number)
            )
            new_user_id = cur.fetchone()[0]
            conn.commit()

            log_action(new_user_id, 'user_registration', f"New {role} account registered: {username} (Matric: {matric_number if matric_number else 'N/A'})")

            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except psycopg2.Error as e:
            conn.rollback()
            flash(f"An error occurred during registration: {e}", 'danger')
            print(f"Registration error: {e}")
        finally:
            cur.close()

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    announcements = []
    conn = get_db()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT title, content, posted_at FROM announcements ORDER BY posted_at DESC LIMIT 3;")
            raw_announcements = cur.fetchall()
            for ann in raw_announcements:
                announcements.append({
                    "title": ann[0],
                    "content": ann[1],
                    "date": ann[2].strftime('%B %d, %Y')
                })
        except psycopg2.Error as e:
            flash(f"Error fetching announcements for dashboard: {e}", 'danger')
            print(f"Error fetching announcements for dashboard: {e}")
        finally:
            cur.close()
    return render_template('dashboard.html', announcements=announcements)


@app.route('/admin')
@role_required('admin')
def admin_panel():
    total_users = 0
    total_courses = 0
    pending_housing_applications = 0
    recent_activities = []

    conn = get_db()
    if conn:
        cur = conn.cursor()
        try:
            total_users = 0
            cur.execute("SELECT COUNT(*) FROM users;")
            total_users = cur.fetchone()[0]

            total_courses = 0
            cur.execute("SELECT COUNT(*) FROM courses;")
            total_courses = cur.fetchone()[0]

            pending_housing_applications = 0
            cur.execute("SELECT COUNT(*) FROM housing_applications WHERE status = 'pending';")
            pending_housing_applications = cur.fetchone()[0]

            cur.execute("""
                SELECT
                    l.timestamp,
                    u.first_name,
                    u.last_name,
                    l.action_type,
                    l.description
                FROM
                    logs l
                LEFT JOIN
                    users u ON l.user_id = u.id
                ORDER BY
                    l.timestamp DESC
                LIMIT 10;
            """)
            raw_activities = cur.fetchall()
            for activity in raw_activities:
                posted_by_name = f"{activity[1]} {activity[2]}" if activity[1] and activity[2] else "System"
                recent_activities.append({
                    "type": activity[3].replace('_', ' ').title(),
                    "description": activity[4],
                    "posted_by": posted_by_name,
                    "timestamp": activity[0].strftime('%Y-%m-%d %H:%M')
                })

        except psycopg2.Error as e:
            flash(f"Error fetching admin panel data: {e}", 'danger')
            print(f"Error fetching admin panel data: {e}")
        finally:
            cur.close()

    return render_template('admin_panel.html',
                           total_users=total_users,
                           total_courses=total_courses,
                           pending_housing_applications=pending_housing_applications,
                           recent_activities=recent_activities,
                           message="Welcome to the Admin Panel!")


@app.route('/student')
@role_required('student')
def student_portal():
    enrolled_courses = []
    message = "Welcome to the Student Portal!"
    matric_number = None
    department = None

    conn = get_db()

    if conn and g.user:
        cur = conn.cursor()
        try:
            matric_number = g.user.get('matric_number')
            department = g.user.get('department')

            cur.execute("""
                SELECT
                    c.course_code,
                    c.title,
                    c.description,
                    c.credits,
                    u_faculty.first_name,
                    u_faculty.last_name,
                    g.grade_value,
                    g.score
                FROM
                    enrollments e
                JOIN
                    courses c ON e.course_id = c.id
                LEFT JOIN
                    users u_faculty ON c.faculty_id = u_faculty.id
                LEFT JOIN
                    grades g ON e.id = g.enrollment_id
                WHERE
                    e.user_id = %s
                ORDER BY
                    c.course_code;
            """, (g.user['id'],))
            raw_courses = cur.fetchall()
            for course in raw_courses:
                faculty_name = f"{course[4]} {course[5]}" if course[4] and course[5] else "N/A"
                enrolled_courses.append({
                    "course_code": course[0],
                    "title": course[1],
                    "description": course[2],
                    "credits": course[3],
                    "faculty_name": faculty_name,
                    "grade_value": course[6] if course[6] else "N/A",
                    "score": course[7] if course[7] is not None else "N/A"
                })

            if not enrolled_courses:
                message = "You are not currently enrolled in any courses. Explore the course catalog!"

        except psycopg2.Error as e:
            flash(f"Error fetching your courses: {e}", 'danger')
            print(f"Error fetching student courses: {e}")
            message = "Error loading your courses."
        finally:
            cur.close()

    return render_template('student_portal.html', message=message, enrolled_courses=enrolled_courses,
                           matric_number=matric_number, department=department)


@app.route('/faculty')
@role_required('faculty')
def faculty_portal():
    return render_template('faculty_portal.html', message="Welcome to the Faculty Portal!")


@app.route('/manage_events', methods=['GET', 'POST'])
@role_required('admin')
def manage_events():
    conn = get_db()
    if not conn:
        flash("Could not connect to the database. Please try again later.", "danger")
        return redirect(url_for('admin_panel'))

    edit_event = None

    if request.method == 'POST':
        action = request.form.get('action')
        event_id = request.form.get('event_id')
        title = request.form.get('title')
        content = request.form.get('content')

        cur = conn.cursor()
        try:
            if action == 'add':
                if title and content:
                    cur.execute(
                        "INSERT INTO announcements (title, content, posted_by) VALUES (%s, %s, %s)",
                        (title, content, g.user['id'])
                    )
                    conn.commit()
                    log_action(g.user['id'], 'announcement_add', f"Added announcement: '{title}'")
                    flash('Event added successfully!', 'success')
                else:
                    flash('Title and content are required to add an event.', 'danger')
            elif action == 'update':
                if event_id and title and content:
                    cur.execute(
                        "UPDATE announcements SET title = %s, content = %s WHERE id = %s",
                        (title, content, event_id)
                    )
                    conn.commit()
                    log_action(g.user['id'], 'announcement_update', f"Updated announcement ID {event_id}: '{title}'")
                    flash('Event updated successfully!', 'success')
                else:
                    flash('Event ID, title, and content are required to update an event.', 'danger')
            elif action == 'delete':
                if event_id:
                    cur.execute("SELECT title FROM announcements WHERE id = %s", (event_id,))
                    deleted_title = cur.fetchone()
                    cur.execute("DELETE FROM announcements WHERE id = %s", (event_id,))
                    conn.commit()
                    log_action(g.user['id'], 'announcement_delete',
                               f"Deleted announcement ID {event_id}: '{deleted_title[0] if deleted_title else 'Unknown'}'")
                    flash('Event deleted successfully!', 'success')
                else:
                    flash('Event ID is required to delete an event.', 'danger')
        except psycopg2.Error as e:
            conn.rollback()
            flash(f"Database error: {e}", 'danger')
            print(f"Manage events error: {e}")
        finally:
            cur.close()
        return redirect(url_for('manage_events'))

    events = []
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, title, content, posted_at FROM announcements ORDER BY posted_at DESC;")
        raw_events = cur.fetchall()
        for event in raw_events:
            events.append({
                "id": event[0],
                "title": event[1],
                "content": event[2],
                "posted_at": event[3].strftime('%Y-%m-%d %H:%M:%S')
            })

        edit_id = request.args.get('edit_id', type=int)
        if edit_id:
            cur.execute("SELECT id, title, content FROM announcements WHERE id = %s", (edit_id,))
            fetched_event = cur.fetchone()
            if fetched_event:
                edit_event = {
                    "id": fetched_event[0],
                    "title": fetched_event[1],
                    "content": fetched_event[2]
                }
            else:
                flash(f"Event with ID {edit_id} not found.", 'warning')

    except psycopg2.Error as e:
        flash(f"Error fetching events: {e}", 'danger')
        print(f"Error fetching events: {e}")
    finally:
        cur.close()
    return render_template('manage_events.html', events=events, edit_event=edit_event)


# New Admin Routes

@app.route('/admin/manage_courses', methods=['GET', 'POST'])
@role_required('admin')
def manage_courses():
    conn = get_db()
    if not conn:
        flash("Could not connect to the database. Please try again later.", "danger")
        return redirect(url_for('admin_panel'))

    edit_course = None
    faculty_members = []
    courses = []
    # Define a list of possible departments. This could also be fetched from the database if departments were dynamic.
    departments = ["Computer Science", "Engineering", "Medicine", "Arts", "Mathematics", "Physics", "Biology", "English Literature", "Business Administration", "History", "Environmental Science", "Psychology", "Chemistry", "Art & Design"]


    cur = conn.cursor()
    try:
        # Fetch all faculty members for dropdown
        cur.execute(
            "SELECT id, first_name, last_name FROM users WHERE role = 'faculty' ORDER BY last_name, first_name;")
        raw_faculty = cur.fetchall()
        faculty_members = [{"id": f[0], "name": f"{f[1]} {f[2]}"} for f in raw_faculty]

        # Handle POST requests
        if request.method == 'POST':
            action = request.form.get('action')
            course_id = request.form.get('course_id')
            course_code = request.form.get('course_code')
            title = request.form.get('title')
            description = request.form.get('description')
            credits = request.form.get('credits')
            faculty_id = request.form.get('faculty_id')
            department = request.form.get('department') # Get department from form

            # Convert credits to float
            try:
                credits = float(credits)
            except (ValueError, TypeError):
                credits = None

            if action == 'add':
                if course_code and title and credits is not None and credits > 0 and department:
                    try:
                        cur.execute(
                            "INSERT INTO courses (course_code, title, description, credits, faculty_id, department) VALUES (%s, %s, %s, %s, %s, %s)",
                            (course_code, title, description, credits, faculty_id if faculty_id else None, department)
                        )
                        conn.commit()
                        log_action(g.user['id'], 'course_add', f"Added new course: {course_code} - {title} ({department})")
                        flash('Course added successfully!', 'success')
                    except pg_errors.UniqueViolation:
                        conn.rollback()
                        flash('Course code already exists. Please use a different one.', 'danger')
                    except Exception as e:
                        conn.rollback()
                        flash(f"Error adding course: {e}", 'danger')
                        print(f"Error adding course: {e}")
                else:
                    flash('Course Code, Title, valid Credits, and Department are required to add a course.', 'danger')
            elif action == 'update':
                if course_id and course_code and title and credits is not None and credits > 0 and department:
                    try:
                        cur.execute(
                            "UPDATE courses SET course_code = %s, title = %s, description = %s, credits = %s, faculty_id = %s, department = %s WHERE id = %s",
                            (course_code, title, description, credits, faculty_id if faculty_id else None, department, course_id)
                        )
                        conn.commit()
                        log_action(g.user['id'], 'course_update',
                                   f"Updated course ID {course_id}: {course_code} - {title} ({department})")
                        flash('Course updated successfully!', 'success')
                    except pg_errors.UniqueViolation:
                        conn.rollback()
                        flash('Course code already exists. Please use a different one.', 'danger')
                    except Exception as e:
                        conn.rollback()
                        flash(f"Error updating course: {e}", 'danger')
                        print(f"Error updating course: {e}")
                else:
                    flash('Course ID, Code, Title, valid Credits, and Department are required to update a course.', 'danger')
            elif action == 'delete':
                if course_id:
                    try:
                        cur.execute("SELECT course_code, title FROM courses WHERE id = %s", (course_id,))
                        deleted_course = cur.fetchone()
                        cur.execute("DELETE FROM courses WHERE id = %s", (course_id,))
                        conn.commit()
                        log_action(g.user['id'], 'course_delete',
                                   f"Deleted course ID {course_id}: {deleted_course[0]} - {deleted_course[1]}")
                        flash('Course deleted successfully!', 'success')
                    except Exception as e:
                        conn.rollback()
                        flash(f"Error deleting course: {e}", 'danger')
                        print(f"Error deleting course: {e}")
                else:
                    flash('Course ID is required to delete a course.', 'danger')
            return redirect(url_for('manage_courses'))

        cur.execute("""
            SELECT
                c.id, c.course_code, c.title, c.description, c.credits, u.first_name, u.last_name, u.id as faculty_user_id, c.department
            FROM
                courses c
            LEFT JOIN
                users u ON c.faculty_id = u.id
            ORDER BY
                c.course_code;
        """)
        raw_courses = cur.fetchall()
        for course in raw_courses:
            faculty_name = f"{course[5]} {course[6]}" if course[5] and course[6] else "Unassigned"
            courses.append({
                "id": course[0],
                "course_code": course[1],
                "title": course[2],
                "description": course[3],
                "credits": course[4],
                "faculty_name": faculty_name,
                "faculty_id": course[7],
                "department": course[8] # Fetch the department
            })

        edit_id = request.args.get('edit_id', type=int)
        if edit_id:
            cur.execute("""
                SELECT
                    id, course_code, title, description, credits, faculty_id, department
                FROM
                    courses
                WHERE id = %s
            """, (edit_id,))
            fetched_course = cur.fetchone()
            if fetched_course:
                edit_course = {
                    "id": fetched_course[0],
                    "course_code": fetched_course[1],
                    "title": fetched_course[2],
                    "description": fetched_course[3],
                    "credits": fetched_course[4],
                    "faculty_id": fetched_course[5],
                    "department": fetched_course[6] # Fetch the department for editing
                }
            else:
                flash(f"Course with ID {edit_id} not found.", 'warning')

    except psycopg2.Error as e:
        flash(f"Error managing courses: {e}", 'danger')
        print(f"Error managing courses: {e}")
    finally:
        cur.close()
    return render_template('manage_courses.html', courses=courses, faculty_members=faculty_members,
                           edit_course=edit_course, departments=departments)



@app.route('/admin/view_students', methods=['GET', 'POST'])
@role_required('admin')
def view_students():
    conn = get_db()
    if not conn:
        flash("Could not connect to the database. Please try again later.", "danger")
        return redirect(url_for('admin_panel'))

    students = []
    cur = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id', type=int)

        if not user_id:
            flash("User ID is required for this action.", 'danger')
            return redirect(url_for('view_students'))

        try:
            cur.execute("SELECT first_name, last_name, username, status FROM users WHERE id = %s", (user_id,))
            student_info = cur.fetchone()
            student_name = f"{student_info[0]} {student_info[1]}" if student_info else "Unknown Student"
            old_status = student_info[3] if student_info else "N/A"

            if action == 'suspend':
                cur.execute("UPDATE users SET status = 'suspended' WHERE id = %s AND role = 'student'", (user_id,))
                conn.commit()
                log_action(g.user['id'], 'student_status_change',
                           f"Suspended student: {student_name} (ID: {user_id}). Old status: {old_status.upper()}")
                flash('Student account suspended.', 'success')
            elif action == 'expel':
                cur.execute("UPDATE users SET status = 'expelled' WHERE id = %s AND role = 'student'", (user_id,))
                conn.commit()
                log_action(g.user['id'], 'student_status_change',
                           f"Expelled student: {student_name} (ID: {user_id}). Old status: {old_status.upper()}")
                flash('Student account expelled.', 'success')
            elif action == 'activate':
                cur.execute("UPDATE users SET status = 'active' WHERE id = %s AND role = 'student'", (user_id,))
                conn.commit()
                log_action(g.user['id'], 'student_status_change',
                           f"Activated student: {student_name} (ID: {user_id}). Old status: {old_status.upper()}")
                flash('Student account activated.', 'success')
            elif action == 'delete':
                cur.execute("DELETE FROM users WHERE id = %s AND role = 'student'", (user_id,))
                conn.commit()
                log_action(g.user['id'], 'student_account_delete',
                           f"Permanently deleted student account: {student_name} (ID: {user_id}).")
                flash('Student account deleted permanently.', 'success')
            else:
                flash('Invalid action.', 'danger')
        except psycopg2.Error as e:
            conn.rollback()
            flash(f"Database error: {e}", 'danger')
            print(f"Student management error: {e}")
        finally:
            cur.close()
        return redirect(url_for('view_students'))

    try:
        cur.execute(
            "SELECT id, username, first_name, last_name, email, status, department, matric_number FROM users WHERE role = 'student' ORDER BY last_name, first_name;")
        raw_students = cur.fetchall()
        for student in raw_students:
            students.append({
                "id": student[0],
                "username": student[1],
                "first_name": student[2],
                "last_name": student[3],
                "email": student[4],
                "status": student[5],
                "department": student[6],
                "matric_number": student[7]
            })
    except psycopg2.Error as e:
        flash(f"Error fetching student data: {e}", 'danger')
        print(f"Error fetching student data: {e}")
    finally:
        cur.close()
    return render_template('view_students.html', students=students)


@app.route('/admin/manage_student_courses', methods=['GET', 'POST'])
@role_required('admin')
def manage_student_courses():
    conn = get_db()
    if not conn:
        flash("Could not connect to the database. Please try again later.", "danger")
        return redirect(url_for('admin_panel'))

    students = []
    courses = [] # This will hold all courses or filtered courses
    student_enrollments = []
    selected_student_id = request.args.get('student_id', type=int)
    selected_student_department = None # To store the department of the selected student

    cur = conn.cursor()

    try:
        # Fetch all active students, including department and matric_number
        cur.execute(
            "SELECT id, first_name, last_name, department, matric_number FROM users WHERE role = 'student' AND status = 'active' ORDER BY last_name, first_name;")
        raw_students = cur.fetchall()
        students = [{"id": s[0], "name": f"{s[1]} {s[2]}", "department": s[3], "matric_number": s[4]} for s in raw_students]

        # Determine the department of the selected student
        if selected_student_id:
            for student in students:
                if student['id'] == selected_student_id:
                    selected_student_department = student['department']
                    break

        # Fetch courses based on the selected student's department if available
        if selected_student_department:
            cur.execute("SELECT id, course_code, title FROM courses WHERE department = %s ORDER BY course_code;", (selected_student_department,))
        else:
            # If no student is selected or department is null, fetch all courses
            cur.execute("SELECT id, course_code, title FROM courses ORDER BY course_code;")

        raw_courses = cur.fetchall()
        courses = [{"id": c[0], "code": c[1], "title": c[2]} for c in raw_courses]


        # Handle POST requests
        if request.method == 'POST':
            action = request.form.get('action')
            student_id = request.form.get('student_id', type=int)
            course_id = request.form.get('course_id', type=int)

            if not student_id or not course_id:
                flash("Student and Course must be selected for this action.", 'danger')
                return redirect(url_for('manage_student_courses', student_id=selected_student_id))

            cur.execute("SELECT first_name, last_name FROM users WHERE id = %s", (student_id,))
            student_info = cur.fetchone()
            student_name = f"{student_info[0]} {student_info[1]}" if student_info else "Unknown Student"
            cur.execute("SELECT course_code, title FROM courses WHERE id = %s", (course_id,))
            course_info = cur.fetchone()
            course_details = f"{course_info[0]} - {course_info[1]}" if course_info else "Unknown Course"

            if action == 'enroll':
                try:
                    cur.execute("INSERT INTO enrollments (user_id, course_id) VALUES (%s, %s)", (student_id, course_id))
                    conn.commit()
                    log_action(g.user['id'], 'student_enrollment',
                               f"Enrolled student {student_name} (ID: {student_id}) in course: {course_details}")
                    flash('Student enrolled in course successfully!', 'success')
                except pg_errors.UniqueViolation:
                    conn.rollback()
                    flash('Student is already enrolled in this course.', 'warning')
                except Exception as e:
                    conn.rollback()
                    flash(f"Error enrolling student: {e}", 'danger')
                    print(f"Error enrolling student: {e}")
            elif action == 'unenroll':
                try:
                    cur.execute("DELETE FROM enrollments WHERE user_id = %s AND course_id = %s",
                                (student_id, course_id))
                    conn.commit()
                    log_action(g.user['id'], 'student_unenrollment',
                               f"Unenrolled student {student_name} (ID: {student_id}) from course: {course_details}")
                    flash('Student unenrolled from course successfully!', 'success')
                except Exception as e:
                    conn.rollback()
                    flash(f"Error unenrolling student: {e}", 'danger')
                    print(f"Error unenrolling student: {e}")
            else:
                flash('Invalid action.', 'danger')

            return redirect(url_for('manage_student_courses', student_id=student_id))

        if selected_student_id:
            cur.execute("""
                SELECT
                    e.id as enrollment_id,
                    c.id as course_id,
                    c.course_code,
                    c.title,
                    u_faculty.first_name,
                    u_faculty.last_name,
                    g.grade_value,
                    g.score
                FROM
                    enrollments e
                JOIN
                    courses c ON e.course_id = c.id
                LEFT JOIN
                    users u_faculty ON c.faculty_id = u_faculty.id
                LEFT JOIN
                    grades g ON e.id = g.enrollment_id
                WHERE
                    e.user_id = %s
                ORDER BY
                    c.course_code;
            """, (selected_student_id,))
            raw_enrollments = cur.fetchall()
            for enrollment in raw_enrollments:
                faculty_name = f"{enrollment[4]} {enrollment[5]}" if enrollment[4] and enrollment[5] else "N/A"
                student_enrollments.append({
                    "enrollment_id": enrollment[0],
                    "course_id": enrollment[1],
                    "course_code": enrollment[2],
                    "title": enrollment[3],
                    "faculty_name": faculty_name,
                    "grade_value": enrollment[6] if enrollment[6] else "N/A",
                    "score": enrollment[7] if enrollment[7] is not None else "N/A"
                })
    except psycopg2.Error as e:
        flash(f"Error fetching data for student course management: {e}", 'danger')
        print(f"Error fetching data for student course management: {e}")
    finally:
        cur.close()

    return render_template('manage_student_courses.html',
                           students=students,
                           courses=courses,
                           student_enrollments=student_enrollments,
                           selected_student_id=selected_student_id)


@app.route('/admin/assign_grades', methods=['GET', 'POST'])
@role_required('admin')
def assign_grades():
    conn = get_db()
    if not conn:
        flash("Could not connect to the database. Please try again later.", "danger")
        return redirect(url_for('admin_panel'))

    students = []
    student_enrollments_for_grading = []
    selected_student_id = request.args.get('student_id', type=int)

    cur = conn.cursor()

    try:
        # Fetch all active students, including department and matric_number
        cur.execute(
            "SELECT id, first_name, last_name, department, matric_number FROM users WHERE role = 'student' AND status = 'active' ORDER BY last_name, first_name;")
        raw_students = cur.fetchall()
        students = [{"id": s[0], "name": f"{s[1]} {s[2]}", "department": s[3], "matric_number": s[4]} for s in raw_students]

        if request.method == 'POST':
            student_id = request.form.get('student_id', type=int)
            enrollment_id = request.form.get('enrollment_id', type=int)
            grade_value = request.form.get('grade_value')
            score_str = request.form.get('score')

            score = None
            if score_str:
                try:
                    score = float(score_str)
                    if not (0 <= score <= 100):
                        flash('Score must be between 0 and 100.', 'danger')
                        return redirect(url_for('assign_grades', student_id=student_id))
                except ValueError:
                    flash('Invalid score value. Please enter a number.', 'danger')
                    return redirect(url_for('assign_grades', student_id=student_id))

            if not student_id or not enrollment_id:
                flash("Student and Enrollment must be selected to assign a grade.", 'danger')
                return redirect(url_for('assign_grades', student_id=selected_student_id))

            cur.execute("""
                SELECT
                    u.first_name, u.last_name, c.course_code, c.title
                FROM
                    enrollments e
                JOIN users u ON e.user_id = u.id
                JOIN courses c ON e.course_id = c.id
                WHERE e.id = %s
            """, (enrollment_id,))
            enroll_info = cur.fetchone()
            student_name_for_log = f"{enroll_info[0]} {enroll_info[1]}" if enroll_info else "Unknown Student"
            course_name_for_log = f"{enroll_info[2]} - {enroll_info[3]}" if enroll_info else "Unknown Course"

            cur.execute("SELECT id FROM grades WHERE enrollment_id = %s", (enrollment_id,))
            existing_grade = cur.fetchone()

            if existing_grade:
                cur.execute(
                    "UPDATE grades SET grade_value = %s, score = %s, graded_by = %s, grade_date = CURRENT_DATE WHERE enrollment_id = %s",
                    (grade_value, score, g.user['id'], enrollment_id)
                )
                conn.commit()
                log_action(g.user['id'], 'grade_update',
                           f"Updated grade for {student_name_for_log} in {course_name_for_log} to: {grade_value} ({score})")
                flash('Grade updated successfully!', 'success')
            else:
                cur.execute(
                    "INSERT INTO grades (enrollment_id, grade_value, score, graded_by) VALUES (%s, %s, %s, %s)",
                    (enrollment_id, grade_value, score, g.user['id'])
                )
                conn.commit()
                log_action(g.user['id'], 'grade_assign',
                           f"Assigned grade for {student_name_for_log} in {course_name_for_log}: {grade_value} ({score})")
                flash('Grade assigned successfully!', 'success')

            return redirect(url_for('assign_grades', student_id=student_id))

        if selected_student_id:
            cur.execute("""
                SELECT
                    e.id as enrollment_id,
                    c.course_code,
                    c.title,
                    u_faculty.first_name,
                    u_faculty.last_name,
                    g.grade_value,
                    g.score
                FROM
                    enrollments e
                JOIN
                    courses c ON e.course_id = c.id
                LEFT JOIN
                    users u_faculty ON c.faculty_id = u_faculty.id
                LEFT JOIN
                    grades g ON e.id = g.enrollment_id
                WHERE
                    e.user_id = %s
                ORDER BY
                    c.course_code;
            """, (selected_student_id,))
            raw_enrollments = cur.fetchall()
            for enrollment in raw_enrollments:
                faculty_name = f"{enrollment[4]} {enrollment[5]}" if enrollment[4] and enrollment[5] else "N/A"
                student_enrollments_for_grading.append({
                    "enrollment_id": enrollment[0],
                    "course_code": enrollment[1],
                    "title": enrollment[2],
                    "faculty_name": faculty_name,
                    "current_grade_value": enrollment[5] if enrollment[5] else "",
                    "current_score": enrollment[6] if enrollment[6] is not None else ""
                })
    except psycopg2.Error as e:
        flash(f"Error fetching data for grade assignment: {e}", 'danger')
        print(f"Error fetching data for grade assignment: {e}")
    finally:
        cur.close()

    return render_template('assign_grades.html',
                           students=students,
                           student_enrollments_for_grading=student_enrollments_for_grading,
                           selected_student_id=selected_student_id)


@app.route('/admissions')
def admissions():
    return render_template('admissions.html')


@app.route('/academics')
def academics():
    return render_template('academics.html')


@app.route('/campus_life')
def campus_life():
    return render_template('campus_life.html')


@app.route('/financial_aid')
def financial_aid():
    return render_template('financial_aid.html')


@app.route('/faculty_directory')
def faculty_directory():
    faculty_members = []
    conn = get_db()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT id, first_name, last_name, email FROM users WHERE role = 'faculty' ORDER BY last_name, first_name;")
            raw_faculty = cur.fetchall()
            detailed_faculty_data = {
                'faculty1@college.edu': {
                    "department": "Computer Science", "position": "Professor",
                    "specialization": "Artificial Intelligence",
                    "bio": "Dr. Carol White is a leading expert in Artificial Intelligence and Machine Learning. Her research focuses on natural language processing and robotics, with numerous publications in top-tier journals. She is passionate about mentoring students in cutting-edge AI projects.",
                    "office_hours": "Mon/Wed 10:00 AM - 12:00 PM, Tue 2:00 PM - 4:00 PM",
                    "research_interests": ["Artificial Intelligence", "Machine Learning",
                                           "Natural Language Processing"],
                    "publications": ["Foundations of AI (2023)", "Robotics and Advanced Automation (2022)"]
                },
                'faculty2@college.edu': {
                    "department": "English Literature", "position": "Associate Professor",
                    "specialization": "Modern American Literature",
                    "bio": "Professor David Miller specializes in modern and contemporary American literature. His work explores themes of identity and societal change, and he is known for his engaging lectures on literary theory and creative writing workshops.",
                    "office_hours": "Tue/Thu 11:00 AM - 1:00 PM",
                    "research_interests": ["Modern American Literature", "Literary Criticism", "Creative Writing"],
                    "publications": ["Narratives of the American Dream (2024)", "The Poetics of the City (2021)"]
                },
                'faculty3@college.edu': {
                    "department": "Biology", "position": "Assistant Professor", "specialization": "Molecular Biology",
                    "bio": "Dr. Emily Davis is a molecular biologist with a keen interest in genetic engineering and bioinformatics. Her current research investigates gene editing techniques for disease prevention. She leads a vibrant lab and encourages undergraduate participation in research.",
                    "office_hours": "Mon/Wed/Fri 9:00 AM - 10:00 AM",
                    "research_interests": ["Molecular Biology", "Genetics", "Bioinformatics"],
                    "publications": ["CRISPR Technologies (2023)", "Computational Biology Approaches (2022)"]
                },
                'faculty4@college.edu': {
                    "department": "Business Administration", "position": "Professor",
                    "specialization": "Financial Management",
                    "bio": "Professor Frank Wilson is an accomplished financial strategist with decades of experience in global markets. He teaches courses on corporate finance and investment strategies, bringing real-world case studies into the classroom.",
                    "office_hours": "Mon 1:00 PM - 3:00 PM",
                    "research_interests": ["Corporate Finance", "Investment Banking", "Global Markets"],
                    "publications": ["Fundamentals of Financial Strategy (2023)", "Navigating Volatile Markets (2011)"]
                },
                'faculty5@college.edu': {
                    "department": "Physics", "position": "Associate Professor", "specialization": "Quantum Mechanics",
                    "bio": "Dr. Grace Taylor's expertise lies in quantum mechanics and astrophysics. She is known for making complex scientific concepts accessible to students and is actively involved in projects related to dark matter research.",
                    "office_hours": "Thu 10:00 AM - 12:00 PM",
                    "research_interests": ["Quantum Mechanics", "Astrophysics", "Cosmology"],
                    "publications": ["Introduction to Quantum Field Theory (2023)",
                                     "Exploring the Dark Universe (2020)"]
                },
                'faculty6@college.edu': {
                    "department": "History", "position": "Professor", "specialization": "Ancient Civilizations",
                    "bio": "Professor Henry Brown is a renowned historian specializing in ancient civilizations and classical studies. His lectures are celebrated for their depth and storytelling, bringing historical events to life.",
                    "office_hours": "Tue/Thu 2:00 PM - 3:00 PM",
                    "research_interests": ["Ancient Civilizations", "Classical Studies", "Archaeology"],
                    "publications": ["The Rise and Fall of Empires (2024)", "Daily Life in Ancient Rome (2022)"]
                },
                'faculty7@college.edu': {
                    "department": "Environmental Science", "position": "Assistant Professor",
                    "specialization": "Sustainable Development",
                    "bio": "Dr. Ivy Clark is passionate about sustainable development and climate change mitigation. Her research focuses on renewable energy sources and environmental policy.",
                    "office_hours": "Wed 11:00 AM - 1:00 PM",
                    "research_interests": ["Sustainable Development", "Climate Change", "Renewable Energy"],
                    "publications": ["Policy for a Greener Tomorrow (2023)", "Harnessing Solar Power (2021)"]
                },
                'faculty8@college.edu': {
                    "department": "Mathematics", "position": "Professor", "specialization": "Algebraic Topology",
                    "bio": "Professor Jack Lewis is an expert in pure mathematics, particularly in algebraic topology and number theory. He is committed to fostering a love for abstract thinking and problem-solving in his students.",
                    "office_hours": "Mon/Fri 3:00 PM - 4:00 PM",
                    "research_interests": ["Algebraic Topology", "Number Theory", "Mathematical Logic"],
                    "publications": ["Abstract Algebra Reimagined (2024)", "The Beauty of Numbers (2022)"]
                },
                'faculty9@college.edu': {
                    "department": "Psychology", "position": "Associate Professor",
                    "specialization": "Cognitive Psychology",
                    "bio": "Dr. Karen Hall specializes in cognitive psychology and behavioral neuroscience. Her research explores how the brain processes information and influences human behavior.",
                    "office_hours": "Tue 9:00 AM - 11:00 AM",
                    "research_interests": ["Cognitive Psychology", "Neuroscience", "Behavioral Analysis"],
                    "publications": ["Understanding the Human Mind (2023)", "Neural Pathways of Learning (2021)"]
                },
                'faculty10@college.edu': {
                    "department": "Chemistry", "position": "Professor", "specialization": "Organic Chemistry",
                    "bio": "Professor Liam Young is a leading researcher in organic chemistry and drug discovery. His lab is at the forefront of developing new therapeutic compounds.",
                    "office_hours": "Wed/Fri 1:00 PM - 2:00 PM",
                    "research_interests": ["Organic Chemistry", "Medicinal Chemistry", "Drug Discovery"],
                    "publications": ["Synthesis of Novel Compounds (2024)", "Targeted Drug Delivery Systems (2023)"]
                },
                'faculty11@college.edu': {
                    "department": "Art & Design", "position": "Assistant Professor", "specialization": "Digital Art",
                    "bio": "Professor Mia Chen is an innovative artist specializing in digital mediums and interactive installations. Her courses challenge students to explore new creative frontiers and integrate technology into their artistic practice.",
                    "office_hours": "Mon 1:00 PM - 2:00 PM, Thu 10:00 AM - 11:00 AM",
                    "research_interests": ["Digital Art", "Interactive Media", "Generative Design"],
                    "publications": ["The Art of Code (2023)", "Digital Sculpting Techniques (2022)"]
                }
            }

            for member in raw_faculty:
                member_email = member[3]
                details = detailed_faculty_data.get(member_email, {
                    "department": "Various",
                    "position": "Faculty Member",
                    "specialization": "General",
                    "bio": f"A dedicated faculty member in the college, committed to excellence in teaching and research.",
                    "office_hours": "By appointment",
                    "research_interests": [],
                    "publications": []
                })
                faculty_members.append({
                    "id": member[0],
                    "first_name": member[1],
                    "last_name": member[2],
                    "full_name": f"{member[1]} {member[2]}",
                    "email": member[3],
                    "department": details["department"],
                    "position": details["position"],
                    "specialization": details["specialization"],
                })
        except psycopg2.Error as e:
            flash(f"Error fetching faculty data: {e}", 'danger')
            print(f"Error fetching faculty data: {e}")
        finally:
            cur.close()
    return render_template('faculty_directory.html', faculty_members=faculty_members)


@app.route('/faculty_profile/<int:user_id>')
def faculty_profile(user_id):
    faculty_member = None
    conn = get_db()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT id, first_name, last_name, email, username FROM users WHERE id = %s AND role = 'faculty';",
                (user_id,)
            )
            raw_member = cur.fetchone()
            if raw_member:
                member_email = raw_member[3]
                detailed_faculty_data = {
                    'faculty1@college.edu': {
                        "department": "Computer Science", "position": "Professor",
                        "specialization": "Artificial Intelligence",
                        "bio": "Dr. Carol White is a leading expert in Artificial Intelligence and Machine Learning. Her research focuses on natural language processing and robotics, with numerous publications in top-tier journals. She is passionate about mentoring students in cutting-edge AI projects.",
                        "office_hours": "Mon/Wed 10:00 AM - 12:00 PM, Tue 2:00 PM - 4:00 PM",
                        "research_interests": ["Artificial Intelligence", "Machine Learning",
                                               "Natural Language Processing"],
                        "publications": ["Foundations of AI (2023)", "Robotics and Advanced Automation (2022)"]
                    },
                    'faculty2@college.edu': {
                        "department": "English Literature", "position": "Associate Professor",
                        "specialization": "Modern American Literature",
                        "bio": "Professor David Miller specializes in modern and contemporary American literature. His work explores themes of identity and societal change, and he is known for his engaging lectures on literary theory and creative writing workshops.",
                        "office_hours": "Tue/Thu 11:00 AM - 1:00 PM",
                        "research_interests": ["Modern American Literature", "Literary Criticism", "Creative Writing"],
                        "publications": ["Narratives of the American Dream (2024)", "The Poetics of the City (2021)"]
                    },
                    'faculty3@college.edu': {
                        "department": "Biology", "position": "Assistant Professor",
                        "specialization": "Molecular Biology",
                        "bio": "Dr. Emily Davis is a molecular biologist with a keen interest in genetic engineering and bioinformatics. Her current research investigates gene editing techniques for disease prevention. She leads a vibrant lab and encourages undergraduate participation in research.",
                        "office_hours": "Mon/Wed/Fri 9:00 AM - 10:00 AM",
                        "research_interests": ["Molecular Biology", "Genetics", "Bioinformatics"],
                        "publications": ["CRISPR Technologies (2023)", "Computational Biology Approaches (2022)"]
                    },
                    'faculty4@college.edu': {
                        "department": "Business Administration", "position": "Professor",
                        "specialization": "Financial Management",
                        "bio": "Professor Frank Wilson is an accomplished financial strategist with decades of experience in global markets. He teaches courses on corporate finance and investment strategies, bringing real-world case studies into the classroom.",
                        "office_hours": "Mon 1:00 PM - 3:00 PM",
                        "research_interests": ["Corporate Finance", "Investment Banking", "Global Markets"],
                        "publications": ["Fundamentals of Financial Strategy (2023)",
                                         "Navigating Volatile Markets (2011)"]
                    },
                    'faculty5@college.edu': {
                        "department": "Physics", "position": "Associate Professor",
                        "specialization": "Quantum Mechanics",
                        "bio": "Dr. Grace Taylor's expertise lies in quantum mechanics and astrophysics. She is known for making complex scientific concepts accessible to students and is actively involved in projects related to dark matter research.",
                        "office_hours": "Thu 10:00 AM - 12:00 PM",
                        "research_interests": ["Quantum Mechanics", "Astrophysics", "Cosmology"],
                        "publications": ["Introduction to Quantum Field Theory (2023)",
                                         "Exploring the Dark Universe (2020)"]
                    },
                    'faculty6@college.edu': {
                        "department": "History", "position": "Professor", "specialization": "Ancient Civilizations",
                        "bio": "Professor Henry Brown is a renowned historian specializing in ancient civilizations and classical studies. His lectures are celebrated for their depth and storytelling, bringing historical events to life.",
                        "office_hours": "Tue/Thu 2:00 PM - 3:00 PM",
                        "research_interests": ["Ancient Civilizations", "Classical Studies", "Archaeology"],
                        "publications": ["The Rise and Fall of Empires (2024)", "Daily Life in Ancient Rome (2022)"]
                    },
                    'faculty7@college.edu': {
                        "department": "Environmental Science", "position": "Assistant Professor",
                        "specialization": "Sustainable Development",
                        "bio": "Dr. Ivy Clark is passionate about sustainable development and climate change mitigation. Her research focuses on renewable energy sources and environmental policy.",
                        "office_hours": "Wed 11:00 AM - 1:00 PM",
                        "research_interests": ["Sustainable Development", "Climate Change", "Renewable Energy"],
                        "publications": ["Policy for a Greener Tomorrow (2023)", "Harnessing Solar Power (2021)"]
                    },
                    'faculty8@college.edu': {
                        "department": "Mathematics", "position": "Professor", "specialization": "Algebraic Topology",
                        "bio": "Professor Jack Lewis is an expert in pure mathematics, particularly in algebraic topology and number theory. He is committed to fostering a love for abstract thinking and problem-solving in his students.",
                        "office_hours": "Mon/Fri 3:00 PM - 4:00 PM",
                        "research_interests": ["Algebraic Topology", "Number Theory", "Mathematical Logic"],
                        "publications": ["Abstract Algebra Reimagined (2024)", "The Beauty of Numbers (2022)"]
                    },
                    'faculty9@college.edu': {
                        "department": "Psychology", "position": "Associate Professor",
                        "specialization": "Cognitive Psychology",
                        "bio": "Dr. Karen Hall specializes in cognitive psychology and behavioral neuroscience. Her research explores how the brain processes information and influences human behavior.",
                        "office_hours": "Tue 9:00 AM - 11:00 AM",
                        "research_interests": ["Cognitive Psychology", "Neuroscience", "Behavioral Analysis"],
                        "publications": ["Understanding the Human Mind (2023)", "Neural Pathways of Learning (2021)"]
                    },
                    'faculty10@college.edu': {
                        "department": "Chemistry", "position": "Professor", "specialization": "Organic Chemistry",
                        "bio": "Professor Liam Young is a leading researcher in organic chemistry and drug discovery. His lab is at the forefront of developing new therapeutic compounds.",
                        "office_hours": "Wed/Fri 1:00 PM - 2:00 PM",
                        "research_interests": ["Organic Chemistry", "Medicinal Chemistry", "Drug Discovery"],
                        "publications": ["Synthesis of Novel Compounds (2024)", "Targeted Drug Delivery Systems (2023)"]
                    },
                    'faculty11@college.edu': {
                        "department": "Art & Design", "position": "Assistant Professor", "specialization": "Digital Art",
                        "bio": "Professor Mia Chen is an innovative artist specializing in digital mediums and interactive installations. Her courses challenge students to explore new creative frontiers and integrate technology into their artistic practice.",
                        "office_hours": "Mon 1:00 PM - 2:00 PM, Thu 10:00 AM - 11:00 AM",
                        "research_interests": ["Digital Art", "Interactive Media", "Generative Design"],
                        "publications": ["The Art of Code (2023)", "Digital Sculpting Techniques (2022)"]
                    }
                }

                details = detailed_faculty_data.get(member_email, {})

                faculty_member = {
                    "id": raw_member[0],
                    "first_name": raw_member[1],
                    "last_name": raw_member[2],
                    "full_name": f"{raw_member[1]} {raw_member[2]}",
                    "email": raw_member[3],
                    "username": raw_member[4],
                    "department": details.get("department", "Various Department"),
                    "position": details.get("position", "Faculty Member"),
                    "specialization": details.get("specialization", "Various Disciplines"),
                    "bio": details.get("bio", f"Dr. {raw_member[2]} is a dedicated faculty member in the college."),
                    "office_hours": details.get("office_hours", "By appointment"),
                    "research_interests": details.get("research_interests", []),
                    "publications": details.get("publications", [])
                }
        except psycopg2.Error as e:
            flash(f"Error fetching faculty profile: {e}", 'danger')
            print(f"Error fetching faculty profile: {e}")
        finally:
            cur.close()

    if not faculty_member:
        flash("Faculty member not found or you don't have access.", 'danger')
        return redirect(url_for('faculty_directory'))

    return render_template('faculty_profile.html', faculty_member=faculty_member)


@app.route('/student_organizations')
def student_organizations():
    return render_template('student_organizations.html')


@app.route('/housing_options')
def housing_options():
    return render_template('housing_options.html')


@app.route('/housing_application', methods=['GET', 'POST'])
def housing_application():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        preferred_hall = request.form.get('preferred_hall')
        semester = request.form.get('semester')
        notes = request.form.get('notes')

        if not all([student_id, full_name, email, semester]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('housing_application.html',
                                   student_id=student_id, full_name=full_name,
                                   email=email, preferred_hall=preferred_hall,
                                   semester=semester, notes=notes)

        conn = get_db()
        if not conn:
            flash("Could not connect to the database. Please try again later.", "danger")
            return render_template('housing_application.html')

        cur = conn.cursor()
        try:
            user_id = g.user['id'] if g.user else None

            cur.execute(
                """INSERT INTO housing_applications
                   (user_id, student_id, full_name, email, preferred_hall, semester, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (user_id, student_id, full_name, email, preferred_hall, semester, notes)
            )
            conn.commit()
            log_action(user_id, 'housing_application_submit',
                       f"New housing application submitted by {full_name} (Student ID: {student_id})")
            flash('Your housing application has been submitted successfully!', 'success')
            return redirect(url_for('housing_options'))
        except psycopg2.Error as e:
            conn.rollback()
            flash(f"An error occurred during application submission: {e}", 'danger')
            print(f"Housing application error: {e}")
        finally:
            cur.close()

    initial_data = {}
    if g.user:
        initial_data['full_name'] = f"{g.user.get('first_name', '')} {g.user.get('last_name', '')}".strip()
        initial_data['email'] = g.user.get('email', '')
        initial_data['student_id'] = "" # Student ID is not automatically filled as it's a separate field from user ID

    return render_template('housing_application.html', **initial_data)


@app.route('/about_us')
def about_us():
    return render_template('about_us.html')


@app.route('/course_catalog')
def course_catalog():
    courses_data = []
    conn = get_db()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    c.course_code,
                    c.title,
                    c.description,
                    c.credits,
                    u.first_name,
                    u.last_name
                FROM
                    courses c
                LEFT JOIN
                    users u ON c.faculty_id = u.id
                ORDER BY
                    c.course_code;
            """)
            raw_courses = cur.fetchall()
            for course in raw_courses:
                faculty_name = f"{course[4]} {course[5]}" if course[4] and course[5] else "N/A"
                courses_data.append({
                    "course_code": course[0],
                    "title": course[1],
                    "description": course[2],
                    "credits": course[3],
                    "faculty_name": faculty_name
                })
        except psycopg2.Error as e:
            flash(f"Error fetching course data: {e}", 'danger')
            print(f"Error fetching course data: {e}")
        finally:
            cur.close()
    return render_template('course_catalog.html', courses=courses_data)


if __name__ == '__main__':
    with app.app_context():
        init_db()

    app.run(debug=True)
