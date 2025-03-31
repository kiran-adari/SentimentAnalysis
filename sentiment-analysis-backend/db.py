import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

# Establishing MySQL connection
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="StrongPassword123",
            database="sentiment_app"
        )
        return conn
    except Error as e:
        print("Error while connecting to MySQL:", e)
        return None

# Create new user with hashed password
def create_user(username, password):
    conn = get_db_connection()
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
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        return check_password_hash(user['password'], password)
    return False
