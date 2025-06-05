# app.py
from flask import Flask, render_template, request, jsonify
import psycopg2 # Make sure you have this installed: pip install psycopg2-binary

app = Flask(__name__)

# --- Database Connection Details ---
# IMPORTANT: Replace with your actual PostgreSQL credentials
DB_HOST = "localhost"
DB_NAME = "blog_database" # Updated to your renamed database
DB_USER = "postgres" # Example, use your actual username
DB_PASSWORD = "your_db_password" # Use your actual password

def get_db_connection():
    """Establishes and returns a database connection."""
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

@app.route('/')
def index():
    """Renders the main search page."""
    return render_template('index.html')

@app.route('/js-search')
def js_search():
    query = request.args.get('query', '')
    results = []
    conn = None
    cur = None

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        search_sql = """
        SELECT
            p.post_id,
            u.username AS author_name,
            p.content,
            p.user_id
        FROM
            posts AS p
        JOIN
            users AS u ON p.user_id = u.user_id
        WHERE
            p.content ILIKE %s OR u.username ILIKE %s
        ORDER BY p.post_id;
        """
        cur.execute(search_sql, (f'%{query}%', f'%{query}%'))
        raw_results = cur.fetchall()

        for row in raw_results:
            results.append({
                'id': row[0],
                'author': row[1], # author_name from the join
                'content': row[2],
                'user_id': row[3]
            })

    except Exception as e:
        print(f"Database error during search: {e}")

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True) # `debug=True` helps with development (auto-reloads)