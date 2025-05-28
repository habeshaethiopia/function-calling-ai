from flask import Flask, render_template, request, jsonify
from gemini_agent import GeminiAgent
from db import Database
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
agent = GeminiAgent()
db = Database()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message")
    user_id = data.get("user_id", 1)  # Default to user 1 for simplicity

    if not message:
        return jsonify({"error": "No message provided"}), 400

    response = agent.process_message(message, user_id)
    return jsonify({"response": response})


@app.route("/api/create_user", methods=["POST"])
def create_user():
    data = request.json
    name = data.get("name")

    if not name:
        return jsonify({"error": "No name provided"}), 400

    user_id = db.add_user(name)
    return jsonify({"user_id": user_id, "name": name})


if __name__ == "__main__":
    app.run(debug=True)
