# search.py (Make sure this file is correct and saved)

import psycopg2

DB_NAME = "books_hub"
DB_USER = "postgres"
DB_PASS = "1234"
DB_HOST = "localhost"
DB_PORT = "5432"

def get_db_connection(db_to_connect_to="postgres"):
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            database=db_to_connect_to,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database '{db_to_connect_to}': {e}")
        return None


try:
    initial_conn = get_db_connection("postgres")
    if initial_conn is None:
        print("Failed to connect to the 'postgres' database. Ensure PostgreSQL is running and credentials are correct.")
        # Do not exit here if this is part of a Flask app that needs to run
        # Consider raising an exception or returning None and handling in app.py
    else:
        initial_conn.autocommit = True
        cursor = initial_conn.cursor()
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}'")
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            print(f"Database '{DB_NAME}' created successfully.")
        else:
            print(f"Database '{DB_NAME}' already exists.")
        cursor.close()
        initial_conn.close()

    conn = get_db_connection(DB_NAME)
    if conn is None:
        print(f"Failed to connect to '{DB_NAME}' database after creation/check.")
    else:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                author VARCHAR(255) NOT NULL,
                publisher VARCHAR(255) NOT NULL,
                price DECIMAL(10, 2)
            );
        """)
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM books")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute("""
                INSERT INTO books (name, author, publisher, price) VALUES
                ('To Kill a Mockingbird', 'Harper Lee', 'J. B. Lippincott & Co.', 12.99),
                ('1984', 'George Orwell', 'Secker & Warburg', 9.99),
                ('The Great Gatsby', 'F. Scott Fitzgerald', 'Charles Scribner''s Sons', 10.99),
                ('The Catcher in the Rye', 'J.D. Salinger', 'Little, Brown and Company', 8.99),
                ('Moby-Dick', 'Herman Melville', 'Harper & Brothers', 8.99),
                ('Pride and Prejudice', 'Jane Austen', 'T. Egerton, Whitehall', 6.75),
                ('The Hobbit', 'J.R.R. Tolkien', 'George Allen & Unwin', 12.50),
                ('Fahrenheit 451', 'Ray Bradbury', 'Ballantine Books', 9.99),
                ('Jane Eyre', 'Charlotte Brontë', 'Smith, Elder & Co.', 7.50),
                ('The Lord of the Rings', 'J.R.R. Tolkien', 'George Allen & Unwin', 25.00);
            """)
            conn.commit()
            print("Initial books inserted successfully.")
        else:
            print("Books already exist in the 'books' table.")
        cursor.close()
        conn.close()
except psycopg2.Error as e:
    print(f"A database error occurred during setup: {e}")
# --- End of Database Initialization ---

def get_books():
    connb = get_db_connection(DB_NAME)
    if connb is None:
        return []
    cursor = connb.cursor()
    cursor.execute("SELECT name, author, publisher, price FROM books WHERE name IS NOT NULL")
    results = cursor.fetchall()
    cursor.close()
    connb.close() # Close the connection here
    # Ensure all prices are floats for JSON serialization
    books = [{"name": row[0], "author": row[1], "publisher": row[2], "price": float(row[3])} for row in results]
    return books

def search_books(query):
  try:
    connb = get_db_connection(DB_NAME)
    if connb is None:
        return []
    cursor = connb.cursor()
    # Using ILIKE for case-insensitive search
    cursor.execute("SELECT name, author, publisher, price FROM books WHERE name ILIKE %s OR author ILIKE %s", (f"%{query}%", f"%{query}%"))
    raw_results = cursor.fetchall()
    # Convert tuples to dictionaries for consistency with get_books
    results_as_dicts = [{"name": row[0], "author": row[1], "publisher": row[2], "price": float(row[3])} for row in raw_results]
    return results_as_dicts
  except psycopg2.Error as e:
        print(f"A database error occurred during search: {e}")
        return [] # Return empty list on error
  finally:
       if 'connb' in locals() and connb:
        cursor.close()
        connb.close()