from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from transformers import pipeline
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection, authenticate_user
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app, origins="*", supports_credentials=True)
sentiment_pipeline = pipeline("sentiment-analysis")

@app.route('/')
def home():
    return jsonify({"message": "Sentiment Analysis API is running!"})

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    text = data.get('text', '')

    result = sentiment_pipeline(text)[0]
    sentiment = result['label'].capitalize()
    confidence = result['score']

    return jsonify({
        'text': text,
        'sentiment': sentiment,
        'confidence': confidence
    })

@app.route('/save', methods=['POST'])
def save_sentiment():
    data = request.json
    username = data.get('username')
    text_input = data.get('text_input')
    sentiment = data.get('sentiment')
    emoji = data.get('emoji')
    confidence = data.get('confidence')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        user_id = user['id']

        if not text_input or not sentiment:
            return jsonify({"error": "Missing text or sentiment"}), 400

        cursor.execute(
            "INSERT INTO user_history (user_id, text_input, sentiment, emoji, confidence) VALUES (%s, %s, %s, %s, %s)",
            (user_id, text_input, sentiment, emoji, confidence)
        )
        conn.commit()
        return jsonify({"message": "Sentiment saved successfully"}), 200

    except mysql.connector.Error as e:
        print("[ERROR] Failed to save sentiment:", e)
        return jsonify({"error": "Failed to save sentiment"}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/history', methods=['GET'])
def history():
    username = request.args.get('username')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT uh.text_input AS text, uh.sentiment, uh.emoji, uh.confidence, uh.timestamp 
        FROM user_history uh
        JOIN users u ON uh.user_id = u.id
        WHERE u.username = %s
        ORDER BY uh.timestamp DESC
    """, (username,))

    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(result)

@app.route('/clear-history', methods=['POST'])
def clear_history():
    data = request.json
    username = data.get('username')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        user_id = user[0]
        cursor.execute("DELETE FROM user_history WHERE user_id = %s", (user_id,))
        conn.commit()
        return jsonify({'message': 'History cleared successfully'})

    except mysql.connector.Error as err:
        print("Clear History Error:", err)
        return jsonify({'error': 'Failed to clear history'}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            return jsonify({'error': 'Username already exists'}), 409

        hashed = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed))
        conn.commit()
        return jsonify({'message': 'User registered successfully'}), 200

    except mysql.connector.Error as err:
        print("Registration Error:", err)
        return jsonify({'error': 'Registration failed'}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if authenticate_user(username, password):
        return jsonify({'message': 'Login successful', 'username': username})
    else:
        return jsonify({'error': 'Invalid username or password'}), 401



if __name__ == '__main__':
    app.run(debug=True, port=5000)
