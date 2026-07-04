# Employee Management System (v2 — MySQL + Login Authentication)

A full-stack CRUD web application built with **Flask**, **MySQL**, and **SHA-256 password hashing** for admin login.

## Features
- 🔐 Admin login/logout with SHA-256 hashed passwords, protected via Flask sessions
- All employee routes require login (`@login_required` decorator)
- Add, View, Edit, Delete employees
- Search employees by name, department, or position
- Bootstrap 5 UI with flash messages

## Tech Stack
- **Backend:** Python 3, Flask
- **Database:** MySQL 8.0
- **Auth:** Session-based login, SHA-256 password hashing (`hashlib`)
- **Frontend:** HTML5, Jinja2, Bootstrap 5, CSS

## Project Structure
```
employee_management_system_v2/
├── app.py                  # Flask app: routes, auth, MySQL logic
├── config.py                # MySQL connection settings (edit this!)
├── schema.sql                # Creates database + employees + admin_users tables
├── requirements.txt
├── templates/
│   ├── base.html             # Navbar with logout + username
│   ├── login.html            # Login page
│   ├── index.html
│   ├── add_employee.html
│   ├── edit_employee.html
│   └── view_employee.html
└── static/
    └── style.css
```

## Setup Instructions

### 1. Create the MySQL database
Make sure MySQL Server is installed and running, then run:
```bash
mysql -u root -p < schema.sql
```
This creates the `employee_management_db` database with two tables:
- `employees` — stores employee records
- `admin_users` — stores login credentials (SHA-256 hashed passwords)

It also inserts a **default admin account**:
```
Username: admin
Password: admin123
```

### 2. Configure your database credentials
Open `config.py` and set your MySQL username/password:
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_mysql_password',
    'database': 'employee_management_db'
}
```

### 3. Install Python dependencies
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run the app
```bash
python app.py
```
Visit `http://127.0.0.1:5000` — you'll be redirected to the login page.

## How the Authentication Works
1. User submits username + password on `/login`.
2. The password is hashed using SHA-256 (`hashlib.sha256(...).hexdigest()`).
3. The hash is compared against the stored `password_hash` in `admin_users`.
4. On match, `session['admin_id']` and `session['username']` are set.
5. Every employee-related route is wrapped with a `@login_required` decorator that checks `session['admin_id']` — if missing, the user is redirected to `/login`.
6. `/logout` clears the session.

**Note:** SHA-256 alone is fine for an academic project demo, but for production systems you'd normally use a salted algorithm like `bcrypt` or `werkzeug.security.generate_password_hash`, since plain SHA-256 is vulnerable to rainbow-table attacks.

## Adding More Admin Users
To add another admin from the MySQL shell:
```sql
-- Example: create user "yashoda" with password "guide2026"
-- First compute the SHA-256 hash in Python:
-- python3 -c "import hashlib; print(hashlib.sha256('guide2026'.encode()).hexdigest())"

INSERT INTO admin_users (username, password_hash)
VALUES ('yashoda', '<paste_the_hash_here>');
```

## Database Schema

**employees**
| Column          | Type          | Notes            |
|-----------------|---------------|------------------|
| id              | INT, PK, AI   |                  |
| name            | VARCHAR(150)  | Required         |
| email           | VARCHAR(150)  | Required, unique |
| phone           | VARCHAR(20)   | Optional         |
| department      | VARCHAR(100)  | Required         |
| position        | VARCHAR(100)  | Required         |
| salary          | DECIMAL(10,2) | Required         |
| date_of_joining | DATE          | Optional         |

**admin_users**
| Column        | Type         | Notes                    |
|---------------|--------------|--------------------------|
| id            | INT, PK, AI  |                          |
| username      | VARCHAR(50)  | Unique                   |
| password_hash | CHAR(64)     | SHA-256 hex digest       |

## Possible Extensions
- Add a "Change Password" page for admins
- Add role-based access (admin vs. viewer)
- Add pagination for large employee lists
- Export employee list to PDF/Excel
- Add department-wise dashboard with charts
