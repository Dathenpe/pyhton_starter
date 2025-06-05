
from flask import Flask, jsonify, request, render_template

from pyhton_starter.book_search.search import get_db_connection, DB_NAME
from search import get_books, search_books # Assuming these are in search.py

app = Flask(__name__)

@app.route('/')
def index():

    books = get_books()
    return render_template('index.html', books=books, results=[]) # Pass results as an empty list for initial load

@app.route('/search')
def search():
    query = request.args.get('query')

    results = search_books(query)

    return jsonify(results)
@app.route('/js-search', methods=['GET'])
def js_searches():
    query = request.args.get('query')
    conn = get_db_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
          SELECT name, author, publisher, price
          FROM books
          WHERE name ILIKE %s
          OR author ILIKE %s
          OR publisher ILIKE %s
          OR CAST(price AS TEXT) ILIKE %s 
      """, (f"%{query or ''}%", f"%{query or ''}%", f"%{query or ''}%", f"%{query or ''}%"))
    results = cursor.fetchall()
    books = [{"name": row[0], "author": row[1], "publisher": row[2], "price": float(row[3])} for row in results]
    return jsonify(books)
@app.route('/search2')
def search_post():
    return render_template('search.html',)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)