import os
import mysql.connector
from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash

# Establishing MySQL connection
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            database=os.environ.get('DB_NAME')
        )
        return conn
    except mysql.connector.Error as err:
        print(f"[DB ERROR] Failed to connect to database: {err}")
        return None

# Create new user with hashed password
def create_user(username, password):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    hashed_password = generate_password_hash(password)
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (%s, %s)",
        (username, hashed_password)
    )
    conn.commit()
    cursor.close()
    conn.close()

# Authenticate user by comparing hashed password
def authenticate_user(username, password):
    conn = get_db_connection()
    if not conn:    
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        return check_password_hash(user['password'], password)
    return False
