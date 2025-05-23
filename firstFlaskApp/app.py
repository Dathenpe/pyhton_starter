import psycopg2
from flask import Flask, render_template
app = Flask(__name__)
try:
    conn = psycopg2.connect(
        database="demodb",
        user="postgres",
        password="1234",
        host="localhost",
        port="5432"
    )
    print("Connected to the database")
    cur = conn.cursor()
    # cur.execute()
except psycopg2.Error as e:
    print("Error connecting to the database:", e)

@app.route("/")
def index():
   return render_template("index.html")

@app.route("/about")
def about():
    return
@app.route("/contact")
def contact():
    return
@app.route("/response")
def response():
    return render_template("response.html")
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)