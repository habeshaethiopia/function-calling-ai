from flask import Flask, render_template, request, jsonify, redirect, url_for
from functools import wraps
import json
from gemini_agent import GeminiAgent
from db import Database
import os
from dotenv import load_dotenv
import logging
import sys

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv(
    "SECRET_KEY", "your-secret-key-here"
)  # Use environment variable

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Initialize database
    db = Database()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {str(e)}")
    sys.exit(1)

try:
    # Initialize agent
    agent = GeminiAgent()
    logger.info("Agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize agent: {str(e)}")
    sys.exit(1)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = request.headers.get("X-Session-Token")
        if not session_token:
            return jsonify({"error": "Authentication required"}), 401

        user = db.get_user_by_token(session_token)
        if not user or not user.get("success"):
            return jsonify({"error": "Invalid session"}), 401

        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/api/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not all([username, email, password]):
            return jsonify({"error": "Missing required fields"}), 400

        # Create user and get session token
        session_token = db.create_user(username, email, password)
        if not session_token:
            return jsonify({"error": "Username or email already exists"}), 400

        return jsonify({"success": True, "session_token": session_token})
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"error": "Registration failed"}), 500


@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not all([username, password]):
            return jsonify({"error": "Missing required fields"}), 400

        # Authenticate user and get session token
        session_token = db.authenticate_user(username, password)
        if not session_token:
            return jsonify({"error": "Invalid credentials"}), 401

        return jsonify({"success": True, "session_token": session_token})
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": "Login failed"}), 500


@app.route("/api/chat", methods=["POST"])
@login_required
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "No message provided"}), 400

        # Get session token from request headers
        session_token = request.headers.get("X-Session-Token")
        if not session_token:
            return jsonify({"error": "No session token provided"}), 401

        # Verify user session
        user = db.get_user_by_token(session_token)
        if not user["success"]:
            return jsonify({"error": "Invalid or expired session"}), 401

        # Process message with user context
        response = agent.process_message(data["message"], user_id=user["user_id"])
        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(port=os.getenv("PORT", 5000))
