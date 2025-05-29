import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = 'ijijijijiskolmdo2nmdnoqind@9-r1324r1=pe3or240t2492o3-921jg-13k'
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']=''
# app.config['MYSQL_DATABASE']='login_system'
app.config['MYSQL_DB'] = 'login_system'

mysql = MySQL(app)

@app.route('/test_db')
def test_db():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT DATABASE();")
        db_name = cursor.fetchone()
        return f"Connected to database: {db_name}"
    except Exception as e:
        return str(e)

@app.route('/register', methods=['GET', 'POST'])
def register():
    flash = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form["username"]
        password = request.form["password"]
        phone  = request.form["phone"]
        email = request.form["email"]
        if username == "" or password == "" or email == "" or phone == "":
            flash("Make sure you fill in your username, password, and email and phone number", 'alert-danger')
            return render_template('register.html', msg=flash)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO users (username, password, email, phone_number) VALUES (%s, %s, %s, %s)', (username, password, email, phone))
        mysql.connection.commit()
        cursor.close()
        flash('You have successfully registered!', 'alert-success')
        return redirect(url_for('login'))
    elif request.method == 'GET':
        flash = 'please fill out the form'
    return render_template('register.html', msg=flash)

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == "POST" and "username" in request.form and "password" in request.form:
        username = request.form["username"]
        password = request.form["password"]
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            flash ('Logged in successfully!', 'alert-success')
            return redirect(url_for('home'))
        else:
            flash ('Incorrect username/password!', 'alert-danger')
    return render_template('login.html', msg=msg)
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))
@app.route('/home')
def home():
    if 'loggedin' in session:
        return render_template('home.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        return render_template('profile.html', account=account)
    return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/assessments')
def assessments():
    flash('Incorrect username/password!', 'alert-danger')
    return render_template('assessments.html')


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
