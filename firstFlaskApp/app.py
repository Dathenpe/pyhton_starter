import psycopg2
from flask import Flask, render_template, request
from psycopg2.extras import DictCursor

app = Flask(__name__)
# Route for the Home page
@app.route("/")
def index():
    conn = psycopg2.connect(
        database="demodb",
        user="postgres",
        password="1234",
        host="localhost",
        port="5432"
    )
    #cur = conn.cursor(dictionary=True)
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT * FROM users ")
    users=cur.fetchall()
    return render_template("index.html",users=users)

# Route for the Features page
@app.route("/features")
def features():
    return render_template("features.html")

# Route for the Testimonials page
@app.route("/testimonials")
def testimonials():
    return render_template("testimonials.html")

# Route for the Contact page
@app.route("/contact")
def contact():
    # For the contact page, you might want a contact form here
    return render_template("contact.html")

@app.route("/response", methods=["POST","GET"])
def response():
    message = None
    if request.method == "POST":
        try:
            conn = psycopg2.connect(
                database="demodb",
                user="postgres",
                password="1234",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()

            name = request.form["name"]
            email = request.form.get("email")
            phone_number = request.form["number"]

            # Execute the INSERT statement
            cur.execute("INSERT INTO users (name, email, phone_number) VALUES (%s, %s, %s)",
                        (name, email, phone_number))

            # Commit the transaction to save changes
            conn.commit()
            message = f"User {name} added successfully!"

        except psycopg2.Error as e:
            # If an error occurs, rollback the transaction to clear the state
            if conn: # Check if connection was established before trying to rollback
                conn.rollback()
            print(f"Database error during insertion: {e}")
            message = f"Error adding user: {e}. Please try again."

        finally:
            # Always close the cursor and connection, regardless of success or failure
            if cur:
                cur.close()
            if conn:
                conn.close()

    # Make sure 'response.html' is in your 'templates' folder
    return render_template("response.html", message=message)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)