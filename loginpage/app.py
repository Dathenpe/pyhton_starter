import psycopg2
from flask import Flask, render_template, request
from psycopg2.extras import DictCursor

app = Flask(__name__)

def get_db_connection():
    try:
        conn = psycopg2.connect(
            database="demodb",
            user="postgres",
            password="1234",
            host="localhost",
            port="5432"
        )
        cur = conn.cursor()

        # It's still highly recommended to remove this CREATE TABLE from here.
        # It runs on every single database connection. Run it manually in psql once.
        cur.execute("""
                   CREATE TABLE IF NOT EXISTS login_details (
                       id SERIAL PRIMARY KEY,
                       username VARCHAR(255) UNIQUE NOT NULL,
                       email VARCHAR(255) UNIQUE NOT NULL,
                       password VARCHAR(255) NOT NULL
                   );
               """)
        conn.commit()
        print("Table 'login_details' ensured to exist. (Consider moving this out of get_db_connection)")
        cur.close() # Close the cursor used for DDL
        return conn

    except psycopg2.Error as e:
        print(f"Error connecting to the database: {e}")
        return None

@app.route("/")
def index():
    conn = None
    cur = None
    # Renamed for clarity, as we'll be fetching login details
    login_users_from_db = []

    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            # CHANGE THIS LINE: Select from 'login_details' table
            # IMPORTANT: Do NOT select 'password' in real applications for display!
            # For this example, we'll include it as you asked, but be cautious.
            cur.execute("SELECT id, username, email FROM login_details")
            login_users_from_db = cur.fetchall()
    except psycopg2.Error as e:
        print(f"Database error fetching users for index page: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    # Pass the renamed variable to the template
    return render_template("index.html", users=login_users_from_db)

@app.route("/create_account", methods=["GET", "POST"])
def create_account():
    message = None

    if request.method == "POST":
        conn = None
        cur = None
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                username = request.form["username"]
                email = request.form["email"]
                password = request.form["password"]

                cur.execute("SELECT id FROM login_details WHERE username = %s OR email = %s", (username, email))
                if cur.fetchone():
                    message = "Username or Email already exists. Please choose another."
                    conn.rollback()
                else:
                    cur.execute("INSERT INTO login_details (username, email, password) VALUES (%s, %s, %s)",
                                (username, email, password))
                    conn.commit()
                    message = "Account created successfully! You can now log in."
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            print(f"Database error during account creation: {e}")
            message = f"Error creating account: {e}. Please try again."
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
    return render_template("create_account.html", message=message)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = None
        cur = None
        message = None

        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor(cursor_factory=DictCursor)
                cur.execute("SELECT * FROM login_details WHERE username = %s AND password = %s",
                            (username, password))
                user_record = cur.fetchone()

                if user_record:
                    message = f"Welcome, {user_record['username']}! Login successful."
                    return render_template("login.html", message=message, login_success=True)
                else:
                    message = "Invalid username or password."
                    return render_template("login.html", message=message)

        except psycopg2.Error as e:
            print(f"Database error during login: {e}")
            message = "An error occurred during login. Please try again."
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
    return render_template("login.html")

@app.route("/response", methods=["POST","GET"])
def response():
    message = None
    conn = None
    cur = None

    if request.method == "POST":
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()

                name = request.form["name"]
                email = request.form.get("email")
                phone_number = request.form["number"]

                cur.execute("INSERT INTO users (name, email, phone_number) VALUES (%s, %s, %s)",
                            (name, email, phone_number))
                conn.commit()
                message = f"User {name} added successfully!"

        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            print(f"Database error during insertion in response: {e}")
            message = f"Error adding user: {e}. Please try again."
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    return render_template("response.html", message=message)

@app.route("/features")
def features():
    return render_template("features.html")

@app.route("/testimonials")
def testimonials():
    return render_template("testimonials.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)