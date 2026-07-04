-- Employee Management System - MySQL Schema
-- Run this file first: mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS employee_management_db;
USE employee_management_db;

-- Table: employees
CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    phone VARCHAR(20),
    department VARCHAR(100) NOT NULL,
    position VARCHAR(100) NOT NULL,
    salary DECIMAL(10, 2) NOT NULL,
    date_of_joining DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: admin_users (for login authentication)
CREATE TABLE IF NOT EXISTS admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash CHAR(64) NOT NULL,   -- SHA-256 hash is always 64 hex characters
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Default admin login: username = admin, password = admin123
-- SHA-256 hash of "admin123" is inserted below.
INSERT INTO admin_users (username, password_hash)
VALUES ('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9')
ON DUPLICATE KEY UPDATE username = username;
