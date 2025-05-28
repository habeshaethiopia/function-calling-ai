from flask import Flask, render_template, request, jsonify
from gemini_agent import GeminiAgent
from db import Database
from config import USER_CONFIG
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

    if not message:
        return jsonify({"error": "No message provided"}), 400

    response = agent.process_message(message)
    return jsonify({"response": response})


if __name__ == "__main__":
    app.run(debug=True)
