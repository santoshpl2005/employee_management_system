"""
Database configuration for the employee management app.
By default this uses SQLite so the app runs immediately.
Set DB_TYPE=mysql and provide MySQL credentials if you want to use MySQL instead.
"""

import os

DB_CONFIG = {
    'type': os.getenv('DB_TYPE', 'sqlite'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'employee_management_db'),
    'database_path': os.getenv('DB_PATH', 'employee_management.db')
}
