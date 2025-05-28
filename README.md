# Financial Assistant

A modern web-based financial assistant that helps users manage their expenses, track income, and get real-time exchange rates using AI-powered conversations. you can access the hosted one [here](https://function-calling-ai.onrender.com)

## Features

- 💬 Natural language chat interface for financial queries
- 💰 Log expenses and income with categories
- 📊 View monthly financial summaries
- 💱 Get real-time exchange rates
- 🎯 Quick action buttons for common tasks
- 📱 Responsive design for all devices
- 🔒 Thread-safe database operations

## Tech Stack

- **Backend**: Python with Flask
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **Database**: SQLite with connection pooling
- **AI**: Google's Gemini Pro API
- **Exchange Rates**: FastForex API

## Prerequisites

- Python 3.8 or higher
- Google Cloud API key for Gemini
- FastForex API key

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/function-calling-ai.git
cd function-calling-ai
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_gemini_api_key
FASTFOREX_API_KEY=your_fastforex_api_key
```

## Usage

1. Start the Flask server:

```bash
python app.py
```

2. Open your browser and navigate to `http://localhost:5000`

3. Start chatting with the financial assistant! Try these example queries:
   - "Log an expense of 100 for food"
   - "Log income of 500 from salary"
   - "Show me the monthly summary"
   - "What is the exchange rate from USD to ETB?"

## Project Structure

```
function-calling-ai/
├── app.py              # Main Flask application
├── gemini_agent.py     # Gemini AI integration
├── functions.py        # Financial functions
├── db.py              # Database operations
├── api.py             # Exchange rate API
├── templates/         # HTML templates
│   └── index.html     # Main dashboard template
├── static/           # Static assets
├── requirements.txt   # Python dependencies
└── .env              # Environment variables
```

## Features in Detail

### Chat Interface

- Natural language processing for financial queries
- Real-time response generation
- Message history with timestamps
- Loading indicators for better UX

### Financial Management

- Log expenses with categories
- Track income sources
- View monthly summaries
- Calculate balances

### Exchange Rates

- Real-time currency conversion
- Support for multiple currencies
- Historical rate queries

### Database

- Thread-safe SQLite implementation
- Connection pooling for better performance
- Automatic table creation
- Transaction management

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Google Gemini API for AI capabilities
- FastForex for exchange rate data
- Tailwind CSS for the beautiful UI
- Font Awesome for icons
