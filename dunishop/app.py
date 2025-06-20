from flask import Flask, render_template, url_for, abort, request, session, redirect, flash
import psycopg2
from psycopg2 import sql
import psycopg2.extras  # <-- IMPORTANT: Keep this import
import os
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename  # For securing uploaded filenames
from functools import wraps  # Import wraps for decorators

app = Flask(__name__)

# --- Configuration ---
app.config['SECRET_KEY'] = 'your_super_secret_key_here_replace_me'
app.config['SESSION_COOKIE_NAME'] = 'my_shop_session'
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Define your upload folder
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max upload size: 16MB (for images)

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Allowed image file extensions


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


DB_HOST = 'localhost'
DB_NAME = 'dunishop_db'
DB_USER = 'postgres'
DB_PASSWORD = '1234'
DB_PORT = '5432'  # Default PostgreSQL port


# --- Helper function to establish a database connection ---
def get_new_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None


# --- User-related Functions and Decorators ---

# This simulates Flask-Login's current_user.
def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        conn = get_new_db_connection()
        if conn is None:
            return None
        # Use DictCursor here
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            cur.execute("SELECT id, username, email, is_admin FROM users WHERE id = %s;", (user_id,))
            user = cur.fetchone()
            return user
        except Exception as e:
            print(f"Error fetching user: {e}")
            return None
        finally:
            cur.close()
            conn.close()
    return None


# Custom decorator for routes that require login
def login_required(f):
    @wraps(f)  # Ensures decorator metadata is preserved
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


# Custom decorator for routes that require admin privileges
def admin_required(f):
    @wraps(f)  # Ensures decorator metadata is preserved
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or not user['is_admin']:
            flash('You do not have administrative access.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_function


# --- Database Initialization / Seeding Functions (Run once at app startup) ---
def init_db_and_seed_data():
    conn = None
    try:
        conn = get_new_db_connection()
        if conn is None:
            print("Failed to get database connection for initialization.")
            return

        cur = conn.cursor()  # Default cursor is fine for DDL operations

        # Create tables
        cur.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                price NUMERIC(10, 2) NOT NULL,
                image_url VARCHAR(255),
                category_id INTEGER REFERENCES categories(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(900) NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cart_items (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                UNIQUE(user_id, product_id) 
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL, -- Keep order history even if user is deleted
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_amount NUMERIC(10, 2) NOT NULL,
                shipping_address TEXT NOT NULL,
                status VARCHAR(50) DEFAULT 'Pending', -- e.g., 'Pending', 'Shipped', 'Delivered', 'Cancelled'
                payment_method VARCHAR(50) DEFAULT 'Not Specified'
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
                product_id INTEGER REFERENCES products(id) ON DELETE SET NULL, -- Keep item info even if product deleted
                product_name VARCHAR(100) NOT NULL, -- Store name in case product is deleted
                price_at_purchase NUMERIC(10, 2) NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0)
            );
        """)
        # NEW: Table for Homepage Slider Images
        cur.execute("""
            CREATE TABLE IF NOT EXISTS slider_images (
                id SERIAL PRIMARY KEY,
                image_url VARCHAR(255) NOT NULL,
                title VARCHAR(255),
                description TEXT,
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        print("Database tables created (if not existing).")

        # Seed categories if empty
        cur.execute("SELECT COUNT(*) FROM categories;")
        if cur.fetchone()[0] == 0:
            categories_data = [
                ('Electronics',), ('Laptops',), ('Office Accessories',),
                ('Books',)
            ]
            cur.executemany("INSERT INTO categories (name) VALUES (%s);", categories_data)
            conn.commit()
            print("Dummy categories added.")

        # Seed products if empty
        cur.execute("SELECT COUNT(*) FROM products;")
        if cur.fetchone()[0] == 0:
            cur.execute("SELECT id, name FROM categories;")
            categories_map = {name: id for id, name in cur.fetchall()}

            products_data = [
                ('Wireless Bluetooth Headphones', 'High-quality audio with noise cancellation.', 59.99,
                 'https://th.bing.com/th/id/OIP.RZjRvaO9IfDAwpD20I7e5wHaHa?w=193&h=193&c=7&r=0&o=7&dpr=2&pid=1.7&rm=3',
                 categories_map.get('Electronics')),
                ('Gaming Laptop GX-Pro', 'Powerful gaming laptop with RTX 4080.', 1899.99,
                 'https://th.bing.com/th/id/OIP.25YohRvDBjIh8yujK5p1bQHaEK?w=270&h=180&c=7&r=0&o=7&dpr=2&pid=1.7&rm=3',
                 categories_map.get('Laptops')),
                ('Ergonomic Office Chair', 'Comfortable chair for long working hours.', 249.00,
                 'https://th.bing.com/th/id/OIP.av_xPm-Zbmw4zM5a0IpSmAHaHZ?w=193&h=192&c=7&r=0&o=7&dpr=2&pid=1.7&rm=3',
                 categories_map.get('Office Accessories')),
                ('The Hitchhiker\'s Guide to the Galaxy', 'A comedic science fiction series.', 12.50,
                 'https://th.bing.com/th/id/OIP.R7Jfa87zyviic5e3xlyvbgHaJo?w=186&h=242&c=7&r=0&o=7&dpr=2&pid=1.7&rm=3',
                 categories_map.get('Books')),
                ('Smartwatch X-Fit', 'Track your fitness and receive notifications.', 129.99,
                 'https://th.bing.com/th/id/OIP.CMTapD76baYK5Fay5SL7LwHaHa?w=212&h=212&c=7&r=0&o=7&dpr=2&pid=1.7&rm=3',
                 categories_map.get('Electronics')),
                ('USB-C Hub 7-in-1', 'Expand your laptop\'s connectivity.', 35.00,
                 'https://th.bing.com/th/id/OIP.PNjIHUp_mw1CKpFLxJgbdQHaHa?w=208&h=208&c=7&r=0&o=7&dpr=2&pid=1.7&rm=3',
                 categories_map.get('Electronics')),
                ('Mechanical Keyboard RGB', 'Durable mechanical keyboard with customizable RGB lighting.', 85.00,
                 'https://th.bing.com/th/id/OIP.AYJQSVIB5GTjinDmYnJSNAHaF7?w=193&h=180&c=7&r=0&o=7&dpr=2&pid=1.7&rm=3',
                 categories_map.get('Office Accessories')),
                ('Portable External SSD 1TB', 'High-speed external storage for all your files.', 99.99,
                 'https://th.bing.com/th/id/OIP.NcO_kE5viX0gcy_PZjydFAHaEK?w=257&h=180&c=7&r=0&o=7&dpr=2&pid=1.7&rm=3',
                 categories_map.get('Electronics')),
                ('E-Reader PaperView 2', 'Read comfortably with an anti-glare screen.', 110.00,
                 'https://th.bing.com/th/id/OIP._XE3N9t6tk2lGRiVc1No0QHaHa?w=148&h=180&c=7&r=0&o=7&dpr=2&pid=1.7&rm=3',
                 categories_map.get('Electronics')),
                ('Monitor 27-inch 4K', 'Stunning visuals for work and play.', 349.99,
                 'https://th.bing.com/th/id/OIP.SGC-lyFW9ZqH2NWvqRtKDgHaEK?w=301&h=180&c=7&r=0&o=7&dpr=2&pid=1.7&rm=3',
                 categories_map.get('Electronics'))
            ]
            cur.executemany("""
                INSERT INTO products (name, description, price, image_url, category_id)
                VALUES (%s, %s, %s, %s, %s);
            """, products_data)
            conn.commit()
            print("Dummy products added.")

        # Seed an admin user if no users exist (for easy testing)
        cur.execute("SELECT COUNT(*) FROM users;")
        if cur.fetchone()[0] == 0:
            admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'adminpass')  # CHANGE THIS FOR PRODUCTION!
            hashed_password = generate_password_hash(admin_password)

            cur.execute("""
                INSERT INTO users (username, email, password_hash, is_admin)
                VALUES (%s, %s, %s, TRUE);
            """, (admin_username, admin_email, hashed_password))
            conn.commit()
            print(f"Default admin user '{admin_username}' created with password '{admin_password}'. CHANGE THIS!")

        # NEW: Seed slider images if empty
        cur.execute("SELECT COUNT(*) FROM slider_images;")
        if cur.fetchone()[0] == 0:
            slider_data = [
                ('https://th.bing.com/th/id/OIP.RZjRvaO9IfDAwpD20I7e5wHaHa?w=193&h=193&c=7&r=0&o=7&dpr=2&pid=1.7&rm=3',
                 'Discover Our Latest Arrivals', 'Fresh styles and innovative products just for you.', 1),
                ('https://th.bing.com/th/id/OIP.CMTapD76baYK5Fay5SL7LwHaHa?w=212&h=212&c=7&r=0&o=7&dpr=2&pid=1.7&rm=3',
                 'Limited Time Offers!', 'Don\'t miss out on incredible savings across all categories.', 2),
                ('https://th.bing.com/th/id/OIP.SGC-lyFW9ZqH2NWvqRtKDgHaEK?w=301&h=180&c=7&r=0&o=7&dpr=2&pid=1.7&rm=3',
                 'Quality You Can Trust', 'Hand-picked products, built to last and satisfy.', 3)
            ]
            cur.executemany("""
                INSERT INTO slider_images (image_url, title, description, display_order)
                VALUES (%s, %s, %s, %s);
            """, slider_data)
            conn.commit()
            print("Dummy slider images added.")

        cur.close()
        print("Database initialization and seeding complete.")

    except Exception as e:
        print(f"Database initialization failed: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


# --- Functions to manage cart items (session and DB) ---

def get_cart_items():
    user = get_current_user()
    print(f"DEBUG: Current user in get_cart_items: {user}")
    if user:
        print(f"DEBUG: User ID: {user['id']}")

    conn = get_new_db_connection()
    if conn is None:
        print("DEBUG: Database connection failed in get_cart_items. Returning empty.")
        return []

    cart_data = []
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # Ensure DictCursor is used here
        if user:
            cur.execute("""
                SELECT ci.product_id, p.name, p.price, p.image_url, ci.quantity
                FROM cart_items ci JOIN products p ON ci.product_id = p.id
                WHERE ci.user_id = %s;
            """, (user['id'],))
            db_rows = cur.fetchall()
            print(f"DEBUG: Fetched DB cart rows for user {user['id']}: {db_rows}")

            for row in db_rows:
                # Access by key since using DictCursor
                item_data = {
                    'product_id': row['product_id'],
                    'name': row['name'],
                    'price': float(row['price']),
                    'image_url': row['image_url'],
                    'quantity': row['quantity']
                }
                print(f"DEBUG: Processing DB item: {item_data}")
                cart_data.append(item_data)
        else:
            session_cart = session.get('cart', {})
            if session_cart:
                product_ids = [int(pid) for pid in session_cart.keys()]
                if product_ids:
                    query = sql.SQL("""
                        SELECT id, name, price, image_url FROM products WHERE id IN ({});
                    """).format(sql.SQL(', ').join(map(sql.Literal, product_ids)))
                    cur.execute(query)
                    products_in_cart = {p['id']: p for p in cur.fetchall()}  # Already DictCursor rows

                    for product_id_str, quantity in session_cart.items():
                        product_id = int(product_id_str)
                        if product_id in products_in_cart:
                            product_info = products_in_cart[product_id]
                            item_data = {
                                'product_id': product_id,
                                'name': product_info['name'],
                                'price': float(product_info['price']),
                                'image_url': product_info['image_url'],
                                'quantity': quantity
                            }
                            print(f"DEBUG: Processing Session item: {item_data}")
                            cart_data.append(item_data)
            print(f"DEBUG: Fetched Session cart for anonymous user: {cart_data}")

    except Exception as e:
        print(f"Error getting cart items: {e}")
    finally:
        if cur: cur.close()
        if conn: conn.close()

    print(f"DEBUG: Final cart_data being returned: {cart_data}")
    return cart_data


def add_to_cart_db(user_id, product_id, quantity):
    conn = get_new_db_connection()
    if conn is None: return False
    cur = conn.cursor()  # Default cursor is fine for simple INSERT/UPDATE/DELETE
    try:
        cur.execute("""
            INSERT INTO cart_items (user_id, product_id, quantity)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, product_id) DO UPDATE
            SET quantity = cart_items.quantity + EXCLUDED.quantity;
        """, (user_id, product_id, quantity))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding to DB cart: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def remove_from_cart_db(user_id, product_id):
    conn = get_new_db_connection()
    if conn is None: return False
    cur = conn.cursor()  # Default cursor is fine for simple DELETE
    try:
        cur.execute("DELETE FROM cart_items WHERE user_id = %s AND product_id = %s;", (user_id, product_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error removing from DB cart: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def update_cart_quantity_db(user_id, product_id, quantity):
    conn = get_new_db_connection()
    if conn is None: return False
    cur = conn.cursor()  # Default cursor is fine for simple UPDATE
    try:
        if quantity <= 0:
            cur.execute("DELETE FROM cart_items WHERE user_id = %s AND product_id = %s;", (user_id, product_id))
        else:
            cur.execute("""
                UPDATE cart_items
                SET quantity = %s
                WHERE user_id = %s AND product_id = %s;
            """, (quantity, user_id, product_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating DB cart quantity: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def merge_session_cart_to_db(user_id):
    conn = get_new_db_connection()
    if conn is None: return
    cur = conn.cursor()  # Default cursor is fine
    try:
        if 'cart' in session:
            for product_id_str, quantity in session['cart'].items():
                product_id = int(product_id_str)
                cur.execute("""
                    INSERT INTO cart_items (user_id, product_id, quantity)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, product_id) DO UPDATE
                    SET quantity = cart_items.quantity + EXCLUDED.quantity;
                """, (user_id, product_id, quantity))
            conn.commit()
            session.pop('cart', None)
            flash('Your previous cart items have been added to your account.', 'info')
    except Exception as e:
        print(f"Error merging session cart: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


# --- Routes ---

# Function to fetch categories (used across routes)
def fetch_categories():
    conn = None
    try:
        conn = get_new_db_connection()
        if conn is None: return []
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # Use DictCursor here
        cur.execute("SELECT id, name FROM categories ORDER BY name;")
        categories = [{'id': row['id'], 'name': row['name']} for row in cur.fetchall()]
        cur.close()
        return categories
    except Exception as e:
        print(f"Error fetching categories: {e}")
        return []
    finally:
        if conn:
            conn.close()


# Context processor to make current_user and categories available globally
@app.context_processor
def inject_global_data():
    return {
        'current_user': get_current_user(),
        'categories': fetch_categories(),
        'search_query': request.args.get('query', ''),
        'get_cart_items': get_cart_items,
        'now': datetime.now()
    }


@app.route('/')
def index():
    conn = None
    products = []
    # Initialize an empty list for slider images to ensure it always exists
    slider_images_dicts = []  # Renamed to clearly indicate it will be a list of dicts

    try:
        conn = get_new_db_connection()
        if conn is None:
            # If connection fails, ensure both lists are empty and correct type
            return render_template('index.html', products=[], slider_images=[])

        # Use DictCursor for products, as it appears to be working correctly for them
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Fetch products for the main section (should already be dicts)
        cur.execute("""
            SELECT p.id, p.name, p.description, p.price, p.image_url, c.name as category_name
            FROM products p JOIN categories c ON p.category_id = c.id
            ORDER BY p.created_at DESC LIMIT 8;
        """)
        products = cur.fetchall()

        # Fetch slider images for the homepage slider
        cur.execute("""
            SELECT id, image_url, title, description, display_order
            FROM slider_images
            ORDER BY display_order ASC, created_at ASC;
        """)
        # Fetch raw data (which you observed as lists/tuples)
        raw_slider_images = cur.fetchall()

        # --- START MANUAL CONVERSION ---
        # Convert the list of lists/tuples into a list of dictionaries
        for row in raw_slider_images:
            # Assuming the order of columns in your SELECT statement matches the order
            # in your printed output: id, image_url, title, description, display_order
            slider_images_dicts.append({
                'id': row[0],
                'image_url': row[1],
                'title': row[2],
                'description': row[3],
                'display_order': row[4]
            })
        # --- END MANUAL CONVERSION ---

        # Print the *converted* list to verify its structure now
        print(f"Converted slider_images (list of dicts): {slider_images_dicts}")
        print(f"Number of slider images: {len(slider_images_dicts)}")

        cur.close()

    except Exception as e:
        print(f"Error fetching index data (products/slider_images): {e}")
        # In case of an error, ensure empty lists are passed to prevent template errors
        return render_template('index.html', products=[], slider_images=[])
    finally:
        if conn:
            conn.close()

    # Pass the correctly structured list of dictionaries to the template
    return render_template('index.html', products=products, slider_images=slider_images_dicts)


@app.route('/products')
def products():
    conn = None
    all_products = []
    search_query = request.args.get('query', '').strip()
    category_id = request.args.get('category_id', type=int)

    current_category = None

    try:
        conn = get_new_db_connection()
        if conn is None:
            return render_template('products.html', products=[], search_query=search_query,
                                   current_category=current_category)

        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        base_sql = """
            SELECT p.id, p.name, p.description, p.price, p.image_url, c.name as category_name, c.id as category_id
            FROM products p JOIN categories c ON p.category_id = c.id
        """
        where_clauses = []
        params = []

        if search_query:
            where_clauses.append("(p.name ILIKE %s OR p.description ILIKE %s)")
            params.extend([f"%{search_query}%", f"%{search_query}%"])

        if category_id is not None:
            where_clauses.append("p.category_id = %s")
            params.append(category_id)
            cur.execute("SELECT id, name FROM categories WHERE id = %s;", (category_id,))
            cat_data = cur.fetchone()
            if cat_data:
                current_category = {'id': cat_data['id'], 'name': cat_data['name']}

        if where_clauses:
            base_sql += " WHERE " + " AND ".join(where_clauses)

        base_sql += " ORDER BY p.name;"

        cur.execute(sql.SQL(base_sql), tuple(params))

        for row in cur.fetchall():
            all_products.append({
                'id': row['id'],
                'name': row['name'],
                'description': row['description'],
                'price': float(row['price']),
                'image_url': row['image_url'],
                'category_name': row['category_name'],
                'category_id': row['category_id']
            })
        cur.close()
    except Exception as e:
        print(f"Error fetching all products (with search/category): {e}")
    finally:
        if conn:
            conn.close()

    return render_template('products.html', products=all_products, search_query=search_query,
                           current_category=current_category)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = None
    product = None
    try:
        conn = get_new_db_connection()
        if conn is None: abort(500)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute(sql.SQL("""
            SELECT p.id, p.name, p.description, p.price, p.image_url, c.id as category_id, c.name as category_name
            FROM products p JOIN categories c ON p.category_id = c.id
            WHERE p.id = %s;
        """), (product_id,))

        product_data = cur.fetchone()
        cur.close()
        if product_data is None:
            abort(404)

        product = {
            'id': product_data['id'],
            'name': product_data['name'],
            'description': product_data['description'],
            'price': float(product_data['price']),
            'image_url': product_data['image_url'],
            'category': {'id': product_data['category_id'], 'name': product_data['category_name']}
        }
    except Exception as e:
        print(f"Error fetching product detail (ID: {product_id}): {e}")
        abort(500)
    finally:
        if conn:
            conn.close()

    return render_template('indiv_products.html', product=product)


@app.route('/category/<int:category_id>')
def category_products(category_id):
    conn = None
    category = None
    products = []
    search_query = request.args.get('query', '').strip()

    try:
        conn = get_new_db_connection()
        if conn is None: abort(500)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute(sql.SQL("""
            SELECT id, name FROM categories WHERE id = %s;
        """), (category_id,))
        category_data = cur.fetchone()
        if category_data is None:
            abort(404)
        category = {'id': category_data['id'], 'name': category_data['name']}

        base_sql = """
            SELECT p.id, p.name, p.description, p.price, p.image_url
            FROM products p
            WHERE p.category_id = %s
        """
        params = [category_id]

        if search_query:
            base_sql += " AND (p.name ILIKE %s OR p.description ILIKE %s)"
            params.extend([f"%{search_query}%", f"%{search_query}%"])

        base_sql += " ORDER BY p.name;"

        cur.execute(sql.SQL(base_sql), tuple(params))

        for row in cur.fetchall():
            products.append({
                'id': row['id'],
                'name': row['name'],
                'description': row['description'],
                'price': float(row['price']),
                'image_url': row['image_url']
            })
        cur.close()
    except Exception as e:
        print(f"Error fetching category products (ID: {category_id}): {e}")
    finally:
        if conn:
            conn.close()

    return render_template('products.html', category=category, products=products, current_category=category)


@app.route('/cart')
def cart():
    cart_items = get_cart_items()
    total_amount = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total_amount=total_amount)


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', type=int, default=1)

    if not product_id or quantity <= 0:
        flash('Invalid product or quantity.', 'danger')
        return redirect(request.referrer or url_for('index'))

    user = get_current_user()
    conn = get_new_db_connection()
    if conn is None:
        flash('Database error.', 'danger')
        return redirect(request.referrer or url_for('index'))

    try:
        cur = conn.cursor()
        if user:
            cur.execute("""
                INSERT INTO cart_items (user_id, product_id, quantity)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, product_id) DO UPDATE
                SET quantity = cart_items.quantity + EXCLUDED.quantity;
            """, (user['id'], product_id, quantity))
            conn.commit()
        else:
            cart = session.get('cart', {})
            product_id_str = str(product_id)
            cart[product_id_str] = cart.get(product_id_str, 0) + quantity
            session['cart'] = cart
            session.modified = True
        flash(f'Product added to cart!', 'success')
    except Exception as e:
        conn.rollback()
        print(f"Error adding to cart: {e}")
        flash('There was an error adding the product to your cart.', 'danger')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('cart'))


@app.route('/update_cart', methods=['POST'])
def update_cart():
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', type=int)

    if not product_id or quantity is None:
        flash('Invalid cart update request.', 'danger')
        return redirect(url_for('cart'))

    user = get_current_user()
    if user:
        if update_cart_quantity_db(user['id'], product_id, quantity):
            flash('Cart updated.', 'success')
        else:
            flash('Could not update cart.', 'danger')
    else:
        session_cart = session.get('cart', {})
        if quantity <= 0:
            session_cart.pop(str(product_id), None)
        else:
            session_cart[str(product_id)] = quantity
        session['cart'] = session_cart
        flash('Session cart updated.', 'success')
    return redirect(url_for('cart'))


@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    product_id = request.form.get('product_id', type=int)

    if not product_id:
        flash('Invalid product to remove.', 'danger')
        return redirect(url_for('cart'))

    user = get_current_user()
    conn = get_new_db_connection()
    if conn is None:
        flash('Database error.', 'danger')
        return redirect(url_for('cart'))

    cur = conn.cursor()
    try:
        if user:
            cur.execute("DELETE FROM cart_items WHERE user_id = %s AND product_id = %s;", (user['id'], product_id))
            conn.commit()
        else:
            cart = session.get('cart', {})
            product_id_str = str(product_id)
            if product_id_str in cart:
                del cart[product_id_str]
            session['cart'] = cart
            session.modified = True
        flash('Product removed from cart.', 'info')
    except Exception as e:
        conn.rollback()
        print(f"Error removing from cart: {e}")
        flash('Error removing product from cart.', 'danger')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    user = get_current_user()
    if not user:
        flash('Please log in to checkout.', 'warning')
        return redirect(url_for('login', next=url_for('checkout')))

    conn = get_new_db_connection()
    if conn is None:
        flash('Database error.', 'danger')
        # Ensure cart_items is passed as an empty list if DB connection fails
        return render_template('checkout.html', cart_items=[], total_amount=0)

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cart_items = []
    total_amount = 0

    try:
        cur.execute("""
            SELECT ci.product_id, p.name, p.price, p.image_url, ci.quantity
            FROM cart_items ci JOIN products p ON ci.product_id = p.id
            WHERE ci.user_id = %s;
        """, (user['id'],))
        cart_items = cur.fetchall()

        if not cart_items:
            flash('Your cart is empty. Please add items before checking out.', 'warning')
            return redirect(url_for('index'))

        for item in cart_items:
            total_amount += float(item['price']) * item['quantity']

        if request.method == 'POST':
            # --- START DEBUGGING PRINTS ---
            print("\n--- DEBUG: Checkout POST Request Data ---")
            print("request.form:", request.form)
            print("Cart Items (before order placement):", cart_items)
            print("Total Amount:", total_amount)
            # --- END DEBUGGING PRINTS ---

            # Extract new shipping fields from the form
            # Using .get() with a default value to prevent KeyError if field is somehow missing
            # (though HTML 'required' should prevent this in most browsers)
            full_name = request.form.get('fullName')
            address = request.form.get('address')
            city = request.form.get('city')
            zip_code = request.form.get('zipCode')
            country = request.form.get('country')
            whatsapp_phone = request.form.get('whatsapp_phone')

            # Basic validation for essential fields from the form
            if not all([full_name, address, city, zip_code, country, whatsapp_phone]):
                flash('Please fill in all required shipping and contact details.', 'danger')
                # Re-render the checkout page with current cart data if validation fails
                return render_template('checkout.html', cart_items=cart_items, total_amount=total_amount)


            # Combine address parts into a single string for 'shipping_address'
            shipping_address_combined = f"{full_name}, {address}, {city}, {zip_code}, {country} | WhatsApp: {whatsapp_phone}"

            # Set payment_method to indicate WhatsApp contact
            payment_method_status = "WhatsApp Contact"

            print("DEBUG: Combined Shipping Address:", shipping_address_combined)
            print("DEBUG: Payment Method Status:", payment_method_status)

            cur.execute("""
                INSERT INTO orders (user_id, order_date, total_amount, shipping_address, payment_method, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (user['id'], datetime.now(), total_amount, shipping_address_combined, payment_method_status,
                  'Pending'))  # Updated fields
            order_id = cur.fetchone()['id']
            print("DEBUG: Order ID created:", order_id)

            for item in cart_items:
                print(f"DEBUG: Inserting order item: {item['name']}, Qty: {item['quantity']}, Price: {item['price']}")
                cur.execute("""
                    INSERT INTO order_items (order_id, product_id, product_name, quantity, price_at_purchase)
                    VALUES (%s, %s, %s, %s, %s);
                """, (order_id, item['product_id'], item['name'], item['quantity'], item['price']))

            cur.execute("DELETE FROM cart_items WHERE user_id = %s;", (user['id'],))
            conn.commit()
            flash('Order placed successfully! We will contact you via WhatsApp to confirm details.',
                  'success')
            return redirect(url_for('order_confirmation', order_id=order_id))

    except Exception as e:
        conn.rollback()
        # --- IMPORTANT: Print the actual exception for debugging! ---
        print(f"Error during checkout: {e}")
        # Pass cart_items and total_amount back to the template on error
        flash(f'There was an error processing your order. Details: {e}', 'danger') # Display error to user
    finally:
        cur.close()
        conn.close()

    # This return is for the GET request, or if initial checks fail before POST handling
    return render_template('checkout.html', cart_items=cart_items, total_amount=total_amount)


@app.route('/order_confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    conn = get_new_db_connection()
    if conn is None:
        flash('Database error.', 'danger')
        return redirect(url_for('profile'))

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    order = None
    order_items = []

    try:
        cur.execute("SELECT * FROM orders WHERE id = %s AND user_id = %s;", (order_id, user['id']))
        order = cur.fetchone()

        if not order:
            flash('Order not found or you do not have permission to view it.', 'danger')
            return redirect(url_for('profile'))

        cur.execute("""
            SELECT oi.quantity, oi.price_at_purchase, oi.product_name, p.image_url
            FROM order_items oi
            LEFT JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s;
        """, (order_id,))
        order_items = cur.fetchall()

    except Exception as e:
        print(f"Error fetching order confirmation: {e}")
        flash('Error loading order details.', 'danger')
        return redirect(url_for('profile'))
    finally:
        cur.close()
        conn.close()

    return render_template('order_confirmation.html', order=order, order_items=order_items)


@app.route('/profile')
@login_required
def profile():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    conn = get_new_db_connection()
    if conn is None:
        flash('Database error.', 'danger')
        # Ensure all expected variables are passed, even if empty
        return render_template('profile.html', current_cart_items=[], orders=[], current_cart_total=0,
                               admin_uploaded_products=[])

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    current_cart_items = []
    orders = []
    current_cart_total = 0
    admin_uploaded_products = []  # Initialize for all cases

    try:
        if not user['is_admin']:
            # Fetch cart items for regular users
            cur.execute("""
                SELECT ci.product_id, p.name, p.price, ci.quantity
                FROM cart_items ci JOIN products p ON ci.product_id = p.id
                WHERE ci.user_id = %s;
            """, (user['id'],))
            current_cart_items = cur.fetchall()
            current_cart_total = sum(float(item['price']) * item['quantity'] for item in current_cart_items)

            # Fetch order history for regular users
            cur.execute("""
                SELECT id, order_date, total_amount, shipping_address, status
                FROM orders
                WHERE user_id = %s
                ORDER BY order_date DESC;
            """, (user['id'],))
            orders_raw = cur.fetchall()

            for order_row in orders_raw:
                order_id = order_row['id']
                cur.execute("""
                    SELECT quantity, price_at_purchase, product_name
                    FROM order_items
                    WHERE order_id = %s;
                """, (order_id,))
                order_items = cur.fetchall()
                orders.append({
                    'id': order_row['id'],
                    'order_date': order_row['order_date'],
                    'total_amount': float(order_row['total_amount']),
                    'shipping_address': order_row['shipping_address'],
                    'status': order_row['status'],
                    'items': order_items
                })
        else:  # user['is_admin'] is True
            # Fetch all products for admin to show as "Uploaded Products History"
            # NOTE: If your 'products' table had an 'uploaded_by_user_id' column
            # (which it currently doesn't based on your schema), you would filter
            # by that ID here (e.g., WHERE p.uploaded_by_user_id = %s).
            # For now, this will display ALL products in the system to the admin.
            cur.execute("""
                SELECT p.id, p.name, p.description, p.price, p.image_url, c.name as category_name, p.created_at as upload_date
                FROM products p
                JOIN categories c ON p.category_id = c.id
                ORDER BY p.created_at DESC;
            """)
            admin_uploaded_products = cur.fetchall()  # This will be a list of dicts because of DictCursor

    except Exception as e:
        print(f"Error fetching profile data: {e}")
        flash('Error loading profile data.', 'danger')
    finally:
        cur.close()
        conn.close()

    return render_template('profile.html',
                           user=user,
                           current_cart_items=current_cart_items,
                           current_cart_total=current_cart_total,
                           orders=orders,
                           admin_uploaded_products=admin_uploaded_products  # Pass the populated list
                           )


# Important: This init_db_and_seed_data() function should only be called once,
# e.g., when your application starts, to set up the database.
# In a production environment, you would use a proper migration tool.
# For development, you can uncomment the line below to run it when the app starts.
# if __name__ == '__main__':
#     with app.app_context():
#         init_db_and_seed_data()
#     app.run(debug=True)


# --- Admin Routes ---

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    # Example: Fetch some stats for the admin dashboard
    conn = get_new_db_connection()
    if conn is None:
        flash('Database connection error.', 'danger')
        return render_template('admin/dashboard.html', total_products=0, total_users=0, total_orders=0)

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    total_products = 0
    total_users = 0
    total_orders = 0

    try:
        cur.execute("SELECT COUNT(*) FROM products;")
        total_products = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM users;")
        total_users = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM orders;")
        total_orders = cur.fetchone()[0]

    except Exception as e:
        print(f"Error fetching admin dashboard stats: {e}")
        flash('Error loading dashboard data.', 'danger')
    finally:
        cur.close()
        conn.close()

    return render_template('admin/dashboard.html',
                           total_products=total_products,
                           total_users=total_users,
                           total_orders=total_orders)


@app.route('/admin/products', methods=['GET', 'POST'])
@admin_required
def admin_products():
    conn = get_new_db_connection()
    if conn is None:
        flash('Database connection error.', 'danger')
        return render_template('admin/products.html', products=[], categories=[])

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    products_list = []
    categories_list = []

    try:
        # Fetch products
        cur.execute("""
            SELECT p.id, p.name, p.description, p.price, p.image_url, c.name as category_name
            FROM products p JOIN categories c ON p.category_id = c.id
            ORDER BY p.created_at DESC;
        """)
        products_list = cur.fetchall()

        # Fetch categories for the form
        categories_list = fetch_categories()  # Reuse existing function

    except Exception as e:
        print(f"Error fetching products or categories for admin: {e}")
        flash('Error loading products/categories data.', 'danger')
    finally:
        cur.close()
        conn.close()

    return render_template('admin/product_list.html', products=products_list, categories=categories_list)


@app.route('/admin/add_product', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    conn = get_new_db_connection()
    if conn is None:
        flash('Database connection error.', 'danger')
        return redirect(url_for('admin_products'))

    categories = fetch_categories()  # Fetch categories for the dropdown

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        category_id = request.form['category_id']

        # Corrected: Get the file from 'image_file' input
        image_file = request.files.get('image_file')
        # Get the image URL from the 'image_url' input field
        image_url_from_form = request.form.get('image_url')

        final_image_url = None  # This will be the URL saved to the DB

        # Prioritize local file upload
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            unique_filename = str(uuid.uuid4()) + "_" + filename  # Generate unique filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            try:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                image_file.save(file_path)
                final_image_url = url_for('static', filename=f'uploads/{unique_filename}')
            except Exception as e:
                print(f"Error saving image file: {e}")
                flash('Error saving image file.', 'danger')
                # Do not return here; try to proceed without image if it fails
        elif image_url_from_form:  # Fallback to URL if no file uploaded
            final_image_url = image_url_from_form
        else:  # Neither file nor URL provided
            flash('No image provided or file type not allowed. Product will be added without an image.', 'warning')
            # final_image_url remains None, which is fine for the DB schema if image_url is nullable.

        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO products (name, description, price, image_url, category_id)
                VALUES (%s, %s, %s, %s, %s);
            """, (name, description, price, final_image_url, category_id))  # Use final_image_url
            conn.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('admin_products'))
        except Exception as e:
            conn.rollback()
            print(f"Error adding product: {e}")
            flash('Error adding product.', 'danger')
        finally:
            cur.close()
            conn.close()

    return render_template('admin/product_form.html', categories=categories)


@app.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    conn = get_new_db_connection()
    if conn is None:
        flash('Database connection error.', 'danger')
        return redirect(url_for('admin_products'))

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    product = None
    categories = fetch_categories()

    try:
        cur.execute("""
            SELECT p.id, p.name, p.description, p.price, p.image_url, p.category_id, c.name as category_name
            FROM products p JOIN categories c ON p.category_id = c.id
            WHERE p.id = %s;
        """, (product_id,))
        product = cur.fetchone()

        if product is None:
            flash('Product not found.', 'danger')
            return redirect(url_for('admin_products'))

        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']
            price = request.form['price']
            category_id = request.form['category_id']

            # Corrected: Get the file from 'image_file' input
            image_file = request.files.get('image_file')
            # Get the image URL from the 'image_url' input field
            image_url_from_form = request.form.get('image_url')

            # Start with the existing image URL from the database
            final_image_url = product['image_url']

            # Prioritize new local file upload
            if image_file and allowed_file(image_file.filename):
                # Delete old local image if it existed
                if final_image_url and final_image_url.startswith('/static/uploads/'):
                    old_filename = os.path.basename(final_image_url)
                    old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], old_filename)
                    if os.path.exists(old_file_path):
                        try:
                            os.remove(old_file_path)
                            print(f"Deleted old image file: {old_file_path}")
                        except Exception as e:
                            print(f"Error deleting old image file {old_file_path}: {e}")

                filename = secure_filename(image_file.filename)
                unique_filename = str(uuid.uuid4()) + "_" + filename  # Generate unique filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                try:
                    image_file.save(file_path)
                    final_image_url = url_for('static', filename=f'uploads/{unique_filename}')
                except Exception as e:
                    print(f"Error saving new image file: {e}")
                    flash('Error saving new image file. Product update might be incomplete.', 'danger')

            # If no new file, and a URL was provided in the form, use that URL
            elif image_url_from_form:
                final_image_url = image_url_from_form
                # If the previous image was a local file, delete it
                if product['image_url'] and product['image_url'].startswith('/static/uploads/'):
                    old_filename = os.path.basename(product['image_url'])
                    old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], old_filename)
                    if os.path.exists(old_file_path):
                        try:
                            os.remove(old_file_path)
                            print(f"Deleted old local image file when new URL provided: {old_file_path}")
                        except Exception as e:
                            print(f"Error deleting old local image file: {e}")

            # If neither new file nor new URL, and existing was a local file, but image_url_from_form is empty
            elif not image_file and not image_url_from_form and final_image_url and final_image_url.startswith(
                    '/static/uploads/'):
                # This handles cases where a user might explicitly clear both inputs, intending to remove the image.
                # If you want to allow removal, set final_image_url to None.
                # If you want to keep the existing image if nothing new is provided, this block won't be entered.
                # Current logic keeps existing unless new file/url is present.
                pass  # final_image_url already holds the existing one, or will become None if product['image_url'] was None

            cur.execute("""
                UPDATE products
                SET name = %s, description = %s, price = %s, image_url = %s, category_id = %s
                WHERE id = %s;
            """, (name, description, price, final_image_url, category_id, product_id))
            conn.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin_products'))

    except Exception as e:
        conn.rollback()
        print(f"Error editing product (ID: {product_id}): {e}")
        flash('Error editing product.', 'danger')
    finally:
        cur.close()
        conn.close()

    return render_template('admin/product_form.html', product=product, categories=categories)


@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    conn = get_new_db_connection()
    if conn is None:
        flash('Database connection error.', 'danger')
        return redirect(url_for('admin_products'))

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # Use DictCursor to fetch image_url
    try:
        # First, retrieve the image_url to delete the file
        cur.execute("SELECT image_url FROM products WHERE id = %s;", (product_id,))
        product = cur.fetchone()

        if product and product['image_url'] and product['image_url'].startswith('/static/uploads/'):
            filename_to_delete = os.path.basename(product['image_url'])
            file_path_to_delete = os.path.join(app.config['UPLOAD_FOLDER'], filename_to_delete)
            if os.path.exists(file_path_to_delete):
                try:
                    os.remove(file_path_to_delete)
                    print(f"Deleted image file: {file_path_to_delete}")
                except Exception as e:
                    print(f"Error deleting image file {file_path_to_delete}: {e}")

        cur_delete = conn.cursor()
        cur_delete.execute("DELETE FROM products WHERE id = %s;", (product_id,))
        conn.commit()
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()
        print(f"Error deleting product (ID: {product_id}): {e}")
        flash('Error deleting product.', 'danger')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('admin_products'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    user = get_current_user()
    if user:
        flash('You are already logged in.', 'info')
        return redirect(url_for('profile'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not all([username, email, password, confirm_password]):
            flash('All fields are required!', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')

        hashed_password = generate_password_hash(password)

        conn = get_new_db_connection()
        if conn is None:
            flash('Database connection error.', 'danger')
            return render_template('register.html')

        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id;",
                        (username, email, hashed_password))
            user_id = cur.fetchone()[0]
            conn.commit()
            session['user_id'] = user_id
            merge_session_cart_to_db(user_id)
            flash('Registration successful! You are now logged in.', 'success')
            return redirect(url_for('profile'))
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash('Username or Email already exists.', 'danger')
        except Exception as e:
            conn.rollback()
            print(f"Registration error: {e}")
            flash('An error occurred during registration.', 'danger')
        finally:
            cur.close()
            conn.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    user = get_current_user()
    if user:
        flash('You are already logged in.', 'info')
        return redirect(url_for('profile'))

    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email')
        password = request.form.get('password')

        conn = get_new_db_connection()
        if conn is None:
            flash('Database connection error.', 'danger')
            return render_template('login.html')

        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        user_data = None
        try:
            cur.execute("SELECT id, username, password_hash, is_admin FROM users WHERE username = %s OR email = %s;",
                        (username_or_email, username_or_email))
            user_data = cur.fetchone()
        except Exception as e:
            print(f"Login query error: {e}")
        finally:
            cur.close()
            conn.close()

        if user_data and check_password_hash(user_data['password_hash'], password):
            session['user_id'] = user_data['id']
            merge_session_cart_to_db(user_data['id'])
            flash('Login successful!', 'success')
            next_url = request.args.get('next')
            return redirect(next_url or url_for('profile'))
        else:
            flash('Invalid username/email or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# Admin Routes for Slider Images (DO NOT CHANGE THESE AS PER USER REQUEST)
@app.route('/admin/slider-images')
@admin_required
def admin_slider_images():
    conn = get_new_db_connection()
    slider_images = []
    if conn:
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT id, image_url, title, description FROM slider_images ORDER BY id;")
            slider_images = cur.fetchall()
            cur.close()
        except Exception as e:
            flash(f"Error fetching slider images: {e}", 'danger')
        finally:
            conn.close()
    return render_template('admin/slider_list.html', slider_images=slider_images)


@app.route('/admin/slider-images/add', methods=('GET', 'POST'))
@admin_required
def admin_add_slider_image():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        # Handle image upload
        if 'image_file' not in request.files:
            flash('No image file part', 'danger')
            return redirect(request.url)
        file = request.files['image_file']
        if file.filename == '':
            flash('No selected image file', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_url = url_for('static', filename=f'uploads/{filename}')

            conn = get_new_db_connection()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO slider_images (image_url, title, description) VALUES (%s, %s, %s);",
                        (image_url, title, description)
                    )
                    conn.commit()
                    cur.close()
                    flash('Slider image added successfully!', 'success')
                    return redirect(url_for('admin_slider_images'))
                except Exception as e:
                    flash(f"Error adding slider image: {e}", 'danger')
                    conn.rollback()
                finally:
                    conn.close()
        else:
            flash('Invalid file type for image.', 'danger')
    return render_template('admin/slider_form.html')


@app.route('/admin/slider-images/edit/<int:image_id>', methods=('GET', 'POST'))
@admin_required
def admin_edit_slider_image(image_id):
    conn = get_new_db_connection()
    slider_image = None
    if conn:
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT id, image_url, title, description FROM slider_images WHERE id = %s;", (image_id,))
            slider_image = cur.fetchone()
            cur.close()
        except Exception as e:
            flash(f"Error fetching slider image for edit: {e}", 'danger')
        finally:
            conn.close()

    if slider_image is None:
        flash('Slider image not found.', 'danger')
        return redirect(url_for('admin_slider_images'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        new_image_url = slider_image['image_url']  # Keep existing if not new file

        if 'image_file' in request.files and request.files['image_file'].filename != '':
            file = request.files['image_file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                new_image_url = url_for('static', filename=f'uploads/{filename}')
            else:
                flash('Invalid file type for new image.', 'danger')
                return redirect(request.url)

        conn = get_new_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE slider_images SET image_url = %s, title = %s, description = %s WHERE id = %s;",
                    (new_image_url, title, description, image_id)
                )
                conn.commit()
                cur.close()
                flash('Slider image updated successfully!', 'success')
                return redirect(url_for('admin_slider_images'))
            except Exception as e:
                flash(f"Error updating slider image: {e}", 'danger')
                conn.rollback()
            finally:
                conn.close()

    return render_template('admin/slider_form.html', slider_image=slider_image)


@app.route('/admin/slider-images/delete/<int:image_id>', methods=('POST',))
@admin_required
def admin_delete_slider_image(image_id):
    conn = get_new_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM slider_images WHERE id = %s;", (image_id,))
            conn.commit()
            cur.close()
            flash('Slider image deleted successfully!', 'success')
        except Exception as e:
            flash(f"Error deleting slider image: {e}", 'danger')
            conn.rollback()
        finally:
            conn.close()
    return redirect(url_for('admin_slider_images'))


# --- NEW ADMIN ROUTES FOR USER MANAGEMENT ---

@app.route('/admin/users')
@admin_required
def admin_users():
    conn = get_new_db_connection()
    users = []
    if conn:
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT id, username, email, is_admin FROM users ORDER BY id;")
            users = cur.fetchall()
            cur.close()
        except Exception as e:
            flash(f"Error fetching users: {e}", 'danger')
            print(f"Error fetching users: {e}")  # Debug print
        finally:
            conn.close()
    return render_template('admin/user_list.html', users=users)


@app.route('/admin/users/add', methods=['GET', 'POST'])
@admin_required
def admin_add_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']  # New field for adding user
        is_admin = 'is_admin' in request.form

        # Basic validation
        if not username or not email or not password:
            flash('Username, Email, and Password are required to add a new user.', 'danger')
            return render_template('admin/user_form.html')  # Stay on form

        hashed_password = generate_password_hash(password)

        conn = get_new_db_connection()
        if conn is None:
            flash('Database connection error.', 'danger')
            return redirect(url_for('admin_users'))

        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO users (username, email, password_hash, is_admin)
                VALUES (%s, %s, %s, %s);
            """, (username, email, hashed_password, is_admin))
            conn.commit()
            flash('User added successfully!', 'success')
            return redirect(url_for('admin_users'))
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash('Username or Email already exists.', 'danger')
        except Exception as e:
            conn.rollback()
            print(f"Error adding user: {e}")
            flash('Error adding user.', 'danger')
        finally:
            cur.close()
            conn.close()
    return render_template('admin/user_form.html')  # For GET request


@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(user_id):
    conn = get_new_db_connection()
    if conn is None:
        flash('Database connection error.', 'danger')
        return redirect(url_for('admin_users'))

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    user_to_edit = None

    try:
        cur.execute("SELECT id, username, email, is_admin FROM users WHERE id = %s;", (user_id,))
        user_to_edit = cur.fetchone()

        if user_to_edit is None:
            flash('User not found.', 'danger')
            return redirect(url_for('admin_users'))

        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            is_admin = 'is_admin' in request.form
            new_password = request.form.get('new_password')
            confirm_new_password = request.form.get('confirm_new_password')

            update_sql = "UPDATE users SET username = %s, email = %s, is_admin = %s"
            update_params = [username, email, is_admin]

            # Handle password update only if new_password is provided
            if new_password:
                if new_password != confirm_new_password:
                    flash('New passwords do not match!', 'danger')
                    # Re-render the form with existing data and error
                    return render_template('admin/user_form.html', user=user_to_edit)
                hashed_password = generate_password_hash(new_password)
                update_sql += ", password_hash = %s"
                update_params.append(hashed_password)

            update_sql += " WHERE id = %s;"
            update_params.append(user_id)

            cur.execute(update_sql, tuple(update_params))
            conn.commit()
            flash('User updated successfully!', 'success')
            return redirect(url_for('admin_users'))

    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        flash('Username or Email already exists for another user.', 'danger')
    except Exception as e:
        conn.rollback()
        print(f"Error editing user (ID: {user_id}): {e}")
        flash('Error editing user.', 'danger')
    finally:
        cur.close()
        conn.close()

    return render_template('admin/user_form.html', user=user_to_edit)


@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    # Prevent admin from deleting themselves if they are the only admin
    current_admin = get_current_user()
    if current_admin and current_admin['id'] == user_id:
        conn = get_new_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users WHERE is_admin = TRUE;")
            admin_count = cur.fetchone()[0]
            cur.close()
            conn.close()
            if admin_count == 1:
                flash('Cannot delete the last admin user.', 'danger')
                return redirect(url_for('admin_users'))

    conn = get_new_db_connection()
    if conn is None:
        flash('Database connection error.', 'danger')
        return redirect(url_for('admin_users'))

    cur = conn.cursor()
    try:
        # Note: ON DELETE CASCADE on cart_items means cart entries will be deleted.
        # ON DELETE SET NULL on orders means orders will remain but user_id will be null.
        cur.execute("DELETE FROM users WHERE id = %s;", (user_id,))
        conn.commit()
        flash('User deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()
        print(f"Error deleting user (ID: {user_id}): {e}")
        flash('Error deleting user.', 'danger')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('admin_users'))


# --- NEW ADMIN ROUTES FOR ORDER MANAGEMENT ---

@app.route('/admin/orders')
@admin_required
def admin_orders():
    conn = get_new_db_connection()
    orders = []
    if conn:
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            # Fetch orders with the username of the associated user
            cur.execute("""
                SELECT o.id, o.order_date, o.total_amount, o.shipping_address, o.status, o.payment_method,
                       u.username AS user_username, u.email AS user_email
                FROM orders o
                LEFT JOIN users u ON o.user_id = u.id
                ORDER BY o.order_date DESC;
            """)
            orders = cur.fetchall()
            cur.close()
        except Exception as e:
            flash(f"Error fetching orders: {e}", 'danger')
            print(f"Error fetching orders: {e}")
        finally:
            conn.close()
    return render_template('admin/order_list.html', orders=orders)


@app.route('/admin/orders/edit_status/<int:order_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_order_status(order_id):
    conn = get_new_db_connection()
    if conn is None:
        flash('Database connection error.', 'danger')
        return redirect(url_for('admin_orders'))

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    order = None

    try:
        cur.execute("SELECT id, status FROM orders WHERE id = %s;", (order_id,))
        order = cur.fetchone()

        if order is None:
            flash('Order not found.', 'danger')
            return redirect(url_for('admin_orders'))

        if request.method == 'POST':
            new_status = request.form['status']
            valid_statuses = ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']

            if new_status not in valid_statuses:
                flash('Invalid status provided.', 'danger')
                return redirect(url_for('admin_edit_order_status', order_id=order_id))

            cur.execute("""
                UPDATE orders
                SET status = %s
                WHERE id = %s;
            """, (new_status, order_id))
            conn.commit()
            flash(f'Order {order_id} status updated to {new_status}!', 'success')
            return redirect(url_for('admin_orders'))

    except Exception as e:
        conn.rollback()
        print(f"Error editing order status (ID: {order_id}): {e}")
        flash('Error updating order status.', 'danger')
    finally:
        cur.close()
        conn.close()

    # Define possible statuses to pass to the template
    statuses = ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']
    return render_template('admin/order_status_form.html', order=order, statuses=statuses)


@app.route('/admin/orders/view_details/<int:order_id>')
@admin_required
def admin_view_order_details(order_id):
    conn = get_new_db_connection()
    if conn is None:
        flash('Database connection error.', 'danger')
        return redirect(url_for('admin_orders'))

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    order = None
    order_items = []

    try:
        cur.execute("""
            SELECT o.id, o.order_date, o.total_amount, o.shipping_address, o.status, o.payment_method,
                   u.username AS user_username, u.email AS user_email
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            WHERE o.id = %s;
        """, (order_id,))
        order = cur.fetchone()

        if order is None:
            flash('Order not found.', 'danger')
            return redirect(url_for('admin_orders'))

        cur.execute("""
            SELECT oi.product_name, oi.quantity, oi.price_at_purchase, p.image_url
            FROM order_items oi
            LEFT JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s;
        """, (order_id,))
        order_items = cur.fetchall()

    except Exception as e:
        print(f"Error fetching order details (ID: {order_id}): {e}")
        flash('Error fetching order details.', 'danger')
    finally:
        cur.close()
        conn.close()

    return render_template('admin/order_details.html', order=order, order_items=order_items)

@app.route('/cancel_order/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    user = get_current_user()
    if not user:
        flash('Please log in to cancel an order.', 'warning')
        return redirect(url_for('login'))

    conn = get_new_db_connection()
    if conn is None:
        flash('Database error.', 'danger')
        return redirect(url_for('profile'))

    cur = conn.cursor()
    try:
        # Verify the order belongs to the current user and is in a cancellable status
        cur.execute("SELECT user_id, status FROM orders WHERE id = %s;", (order_id,))
        order_info = cur.fetchone()

        if not order_info:
            flash('Order not found.', 'danger')
            return redirect(url_for('profile'))

        order_user_id, current_status = order_info

        if order_user_id != user['id']:
            flash('You do not have permission to cancel this order.', 'danger')
            return redirect(url_for('profile'))

        # Only allow cancellation if status is Pending or Processing
        if current_status not in ['Pending', 'Processing']:
            flash(f'Order cannot be cancelled because its current status is "{current_status}".', 'warning')
            return redirect(url_for('profile'))

        cur.execute("""
            UPDATE orders
            SET status = 'Cancelled'
            WHERE id = %s;
        """, (order_id,))
        conn.commit()
        flash(f'Order #{order_id} has been successfully cancelled.', 'success')
    except Exception as e:
        conn.rollback()
        print(f"Error cancelling order (ID: {order_id}): {e}")
        flash(f'Error cancelling order. Details: {e}', 'danger')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('profile'))


if __name__ == '__main__':
    with app.app_context():
        init_db_and_seed_data()
    app.run(debug=True)

