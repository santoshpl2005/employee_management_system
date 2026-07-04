"""
Employee Management System (v2)
--------------------------------
Flask + MySQL + SHA-256 login authentication.

Before running:
  1. Run schema.sql in MySQL to create the database and tables:
       mysql -u root -p < schema.sql
  2. Edit config.py with your MySQL username/password.
  3. pip install -r requirements.txt
  4. python app.py

Default login: username = admin, password = admin123
"""

import hashlib
import sqlite3
from functools import wraps

import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, flash, session

from config import DB_CONFIG

app = Flask(__name__)
app.secret_key = "change_this_secret_key"   # needed for sessions + flash messages


# ---------------------------------------------------------
# DATABASE HELPERS
# ---------------------------------------------------------
def is_sqlite():
    """Return True when SQLite should be used instead of MySQL."""
    return DB_CONFIG.get('type', 'sqlite').lower() == 'sqlite'


def db_sql(sql):
    """Convert MySQL-style %s placeholders to SQLite-style ? placeholders."""
    return sql.replace('%s', '?') if is_sqlite() else sql


def get_db_cursor(conn):
    """Create a cursor that works for both MySQL and SQLite."""
    if is_sqlite():
        conn.row_factory = sqlite3.Row
        return conn.cursor()
    return conn.cursor(dictionary=True)


def get_db_connection():
    """Create and return a new database connection."""
    if is_sqlite():
        return sqlite3.connect(DB_CONFIG.get('database_path', 'employee_management.db'))

    mysql_config = {k: v for k, v in DB_CONFIG.items() if k not in {'type', 'database_path'}}
    return mysql.connector.connect(**mysql_config)


def hash_password(password):
    """Return the SHA-256 hex digest of a plain-text password."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def init_db():
    """Create the SQLite database and seed the default admin account if needed."""
    if not is_sqlite():
        return

    conn = sqlite3.connect(DB_CONFIG.get('database_path', 'employee_management.db'))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            department TEXT NOT NULL,
            position TEXT NOT NULL,
            salary REAL NOT NULL,
            date_of_joining TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute(
        "INSERT OR IGNORE INTO admin_users (username, password_hash) VALUES (?, ?)",
        ('admin', hash_password('admin123'))
    )
    conn.commit()
    conn.close()


init_db()


# ---------------------------------------------------------
# AUTH DECORATOR
# ---------------------------------------------------------
def login_required(f):
    """Redirect to login page if the user is not logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ---------------------------------------------------------
# AUTH ROUTES
# ---------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return redirect(url_for('login'))

        password_hash = hash_password(password)

        conn = get_db_connection()
        cursor = get_db_cursor(conn)
        cursor.execute(
            db_sql("SELECT * FROM admin_users WHERE username = %s AND password_hash = %s"),
            (username, password_hash)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['admin_id'] = user['id']
            session['username'] = user['username']
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


# ---------------------------------------------------------
# EMPLOYEE ROUTES (all protected by login_required)
# ---------------------------------------------------------
@app.route('/')
@login_required
def index():
    search_term = request.args.get('q', '').strip()
    conn = get_db_connection()
    cursor = get_db_cursor(conn)

    if search_term:
        like_term = f"%{search_term}%"
        cursor.execute(db_sql("""
            SELECT * FROM employees
            WHERE name LIKE %s OR department LIKE %s OR position LIKE %s
            ORDER BY id DESC
        """), (like_term, like_term, like_term))
    else:
        cursor.execute(db_sql("SELECT * FROM employees ORDER BY id DESC"))

    employees = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) AS total FROM employees")
    total_employees = cursor.fetchone()['total']

    cursor.close()
    conn.close()

    return render_template('index.html',
                            employees=employees,
                            search_term=search_term,
                            total_employees=total_employees)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        phone = request.form['phone'].strip()
        department = request.form['department'].strip()
        position = request.form['position'].strip()
        salary = request.form['salary'].strip()
        date_of_joining = request.form['date_of_joining'].strip() or None

        if not name or not email or not department or not position or not salary:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for('add_employee'))

        try:
            salary_val = float(salary)
        except ValueError:
            flash("Salary must be a valid number.", "danger")
            return redirect(url_for('add_employee'))

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(db_sql("""
                INSERT INTO employees (name, email, phone, department, position, salary, date_of_joining)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """), (name, email, phone, department, position, salary_val, date_of_joining))
            conn.commit()
            flash(f"Employee '{name}' added successfully!", "success")
        except Exception as e:
            if getattr(e, 'errno', None) == 1062 or isinstance(e, sqlite3.IntegrityError):
                flash("An employee with this email already exists.", "danger")
            else:
                flash(f"Database error: {e}", "danger")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('index'))

    return render_template('add_employee.html')


@app.route('/edit/<int:emp_id>', methods=['GET', 'POST'])
@login_required
def edit_employee(emp_id):
    conn = get_db_connection()
    cursor = get_db_cursor(conn)
    cursor.execute(db_sql("SELECT * FROM employees WHERE id = %s"), (emp_id,))
    employee = cursor.fetchone()

    if employee is None:
        cursor.close()
        conn.close()
        flash("Employee not found.", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        phone = request.form['phone'].strip()
        department = request.form['department'].strip()
        position = request.form['position'].strip()
        salary = request.form['salary'].strip()
        date_of_joining = request.form['date_of_joining'].strip() or None

        try:
            salary_val = float(salary)
        except ValueError:
            flash("Salary must be a valid number.", "danger")
            cursor.close()
            conn.close()
            return redirect(url_for('edit_employee', emp_id=emp_id))

        try:
            cursor.execute(db_sql("""
                UPDATE employees
                SET name=%s, email=%s, phone=%s, department=%s, position=%s, salary=%s, date_of_joining=%s
                WHERE id=%s
            """), (name, email, phone, department, position, salary_val, date_of_joining, emp_id))
            conn.commit()
            flash(f"Employee '{name}' updated successfully!", "success")
        except Exception as e:
            if getattr(e, 'errno', None) == 1062 or isinstance(e, sqlite3.IntegrityError):
                flash("Another employee with this email already exists.", "danger")
            else:
                flash(f"Database error: {e}", "danger")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('index'))

    cursor.close()
    conn.close()
    return render_template('edit_employee.html', employee=employee)


@app.route('/view/<int:emp_id>')
@login_required
def view_employee(emp_id):
    conn = get_db_connection()
    cursor = get_db_cursor(conn)
    cursor.execute(db_sql("SELECT * FROM employees WHERE id = %s"), (emp_id,))
    employee = cursor.fetchone()
    cursor.close()
    conn.close()

    if employee is None:
        flash("Employee not found.", "danger")
        return redirect(url_for('index'))

    return render_template('view_employee.html', employee=employee)


@app.route('/delete/<int:emp_id>', methods=['POST'])
@login_required
def delete_employee(emp_id):
    conn = get_db_connection()
    cursor = get_db_cursor(conn)
    cursor.execute(db_sql("SELECT * FROM employees WHERE id = %s"), (emp_id,))
    employee = cursor.fetchone()

    if employee is None:
        cursor.close()
        conn.close()
        flash("Employee not found.", "danger")
        return redirect(url_for('index'))

    cursor.execute(db_sql("DELETE FROM employees WHERE id = %s"), (emp_id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash(f"Employee '{employee['name']}' deleted.", "info")
    return redirect(url_for('index'))


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
