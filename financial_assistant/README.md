# Financial Assistant

A personalized financial assistant that uses Google's Gemini AI to help manage your finances. The assistant can log income and expenses, provide monthly summaries, and fetch currency exchange rates.

## Features

- Log income and expenses with categories
- Get monthly financial summaries
- Fetch currency exchange rates
- Natural language interaction using Gemini AI
- SQLite database for persistent storage
- Simple web interface

## Prerequisites

- Python 3.8 or higher
- Google Gemini API key

## Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd financial_assistant
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your Gemini API key:

```
GEMINI_API_KEY=your_api_key_here
```

## Running the Application

1. Start the Flask server:

```bash
python app.py
```

2. Open your web browser and navigate to `http://localhost:5000`

## Usage

1. Enter your name to create a user profile
2. Start interacting with the assistant using natural language. Here are some example commands:
   - "Log an expense of $50 for groceries"
   - "I received $1000 salary today"
   - "Show me my monthly summary for March 2024"
   - "What's the exchange rate from USD to EUR?"

## Project Structure

- `app.py`: Flask web application
- `gemini_agent.py`: Gemini AI integration and function calling
- `functions.py`: Financial operations and business logic
- `db.py`: Database models and operations
- `api.py`: External API integration for currency exchange rates
- `templates/`: HTML templates for the web interface

## Contributing

Feel free to submit issues and enhancement requests!
