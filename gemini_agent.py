import os
from google import genai
from google.genai import types
from functions import FinancialFunctions
import json
from dotenv import load_dotenv
import datetime
import logging
import sys
from collections import deque

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("gemini_agent.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

load_dotenv()


class GeminiAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.0-flash"
        self.functions = FinancialFunctions()
        self.chat_history = deque(maxlen=5)  # Store last 5 messages
        logger.info(f"Initialized GeminiAgent with model: {self.model}")

        # Define function declarations for Gemini
        self.log_expense_func = types.FunctionDeclaration(
            name="log_expense",
            description="Log or record an expense (money spent) with a specified amount and category (e.g., 'food', 'transport', 'rent'), optionally including the date (defaults to today).",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "The amount of the expense.",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category of the expense (e.g., food, transport, utilities).",
                    },
                    "date": {
                        "type": "string",
                        "description": "Date of the expense in YYYY-MM-DD format (optional; defaults to today).",
                    },
                },
                "required": ["amount", "category"],
            },
        )

        self.log_income_func = types.FunctionDeclaration(
            name="log_income",
            description="Log or record an income (earning) with a specified amount and source (e.g., 'salary', 'freelancing', 'investment'), optionally including the date (defaults to today).",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "The amount of the income.",
                    },
                    "source": {
                        "type": "string",
                        "description": "Source of the income (e.g., salary, freelancing, investment).",
                    },
                    "date": {
                        "type": "string",
                        "description": "Date of the income in YYYY-MM-DD format (optional; defaults to today).",
                    },
                },
                "required": ["amount", "source"],
            },
        )

        self.get_monthly_summary_func = types.FunctionDeclaration(
            name="get_monthly_summary",
            description="Retrieve a summary of expenses and income for a specific month and year, including total spending, total earnings, and net balance. Useful for viewing a monthly financial report.",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "month": {
                        "type": "integer",
                        "description": "Month number (1-12) for the summary. the default is this month ",
                    },
                    "year": {
                        "type": "integer",
                        "description": "Year (e.g., 2024) for the summary.the default is this year",
                    },
                },
            },
        )

        self.get_exchange_rate_func = types.FunctionDeclaration(
            name="get_exchange_rate",
            description="Retrieve the exchange (conversion) rate from one currency to another for a given date. Provide source and target currency codes (e.g., USD, ETB) and an optional date (defaults to today).",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "from_currency": {
                        "type": "string",
                        "description": "Source currency code (e.g., USD).",
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "Target currency code (e.g., ETB).",
                    },
                },
                "required": ["from_currency", "to_currency"],
            },
        )

        self.tools = types.Tool(
            function_declarations=[
                self.log_expense_func,
                self.log_income_func,
                self.get_monthly_summary_func,
                self.get_exchange_rate_func,
            ]
        )
        logger.info("Function declarations and tools configured")

    def _format_chat_history(self):
        """Format chat history for the model context"""
        formatted_history = []
        for msg in self.chat_history:
            formatted_history.append(
                types.Content(
                    role=msg["role"],
                    parts=[types.Part.from_text(text=msg["content"])],
                )
            )
        return formatted_history

    def process_message(self, message):
        """
        Process a user message and handle function calling

        Args:
            message (str): The user's message

        Returns:
            str: The response to the user
        """
        try:
            logger.info(f"Processing message: {message}")

            # Add user message to chat history
            self.chat_history.append({"role": "user", "content": message})

            # Get formatted chat history
            contents = self._format_chat_history()

            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(tools=[self.tools], temperature=0),
            )

            if not hasattr(response, "candidates") or not response.candidates:
                logger.warning("Empty response received from model")
                return "I received an empty response from the model. Please try again."

            candidate = response.candidates[0]
            logger.debug(f"Candidate type: {type(candidate)}")
            logger.debug(f"Candidate attributes: {dir(candidate)}")

            if not hasattr(candidate, "content") or not candidate.content:
                logger.warning("No content in candidate response")
                return "I couldn't process the model's response. Please try again."

            content = candidate.content
            logger.debug(f"Content type: {type(content)}")
            logger.debug(f"Content attributes: {dir(content)}")

            if not hasattr(content, "parts") or not content.parts:
                logger.warning("No parts in content response")
                return "The response format was unexpected. Please try again."

            for part in content.parts:
                logger.debug(f"Part type: {type(part)}")
                logger.debug(f"Part attributes: {dir(part)}")

                if hasattr(part, "function_call") and part.function_call is not None:
                    function_call = part.function_call
                    logger.debug(f"Function call type: {type(function_call)}")
                    logger.debug(f"Function call attributes: {dir(function_call)}")

                    function_name = function_call.name
                    args = function_call.args

                    logger.info(f"Function name: {function_name}")
                    logger.info(f"Function args: {args}")

                    if not isinstance(args, dict):
                        try:
                            args = dict(args)
                        except Exception:
                            if isinstance(args, str) and args.strip():
                                try:
                                    args = json.loads(args)
                                except Exception:
                                    args = {}
                            else:
                                args = {}

                    # If get_monthly_summary and year/month missing, use current year/month
                    if function_name == "get_monthly_summary":
                        now = datetime.datetime.now()
                        if "year" not in args or not args["year"]:
                            args["year"] = now.year
                        if "month" not in args or not args["month"]:
                            args["month"] = now.month

                    # Call the appropriate function
                    if function_name == "log_expense":
                        result = self.functions.log_expense(**args)
                    elif function_name == "log_income":
                        result = self.functions.log_income(**args)
                    elif function_name == "get_monthly_summary":
                        result = self.functions.get_monthly_summary(**args)
                    elif function_name == "get_exchange_rate":
                        result = self.functions.get_exchange_rate(**args)
                    else:
                        logger.warning(f"Unknown function called: {function_name}")
                        return "I'm sorry, I don't know how to handle that function."

                    # Generate a natural language response based on the function result
                    if result.get("success"):
                        if function_name in ["log_expense", "log_income"]:
                            response = f"Successfully logged the transaction. {result['message']}"
                        elif function_name == "get_monthly_summary":
                            summary = result["summary"]
                            response = f"Here's your monthly summary:\nIncome: ${summary['income']:.2f}\nExpenses: ${summary['expenses']:.2f}\nBalance: ${summary['balance']:.2f}\nTotal transactions: {summary['transactions']}"
                        elif function_name == "get_exchange_rate":
                            rate = result["rate"]
                            response = f"The exchange rate from {rate['from']} to {rate['to']} on {rate['date']} is {rate['rate']:.4f}"
                        logger.info(f"Function {function_name} executed successfully")

                        # Add assistant response to chat history
                        self.chat_history.append(
                            {"role": "assistant", "content": response}
                        )

                        return response
                    else:
                        error_msg = f"I encountered an error: {result.get('error', 'Unknown error')}"
                        logger.error(f"Function {function_name} failed: {error_msg}")
                        return error_msg

            # If no function call was made, return the model's response
            logger.info("No function call detected, returning model's response")

            # Add assistant response to chat history
            self.chat_history.append({"role": "assistant", "content": response.text})

            return response.text

        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            logger.error(f"Error processing message: {str(e)}\n{error_details}")
            return f"I encountered an error: {str(e)}\nError details: {error_details}"


if __name__ == "__main__":
    agent = GeminiAgent()
    test_messages = [
        "I spend 1000 birr on food",
        "I earn 5000 birr from my job",
        "can i get my monthly summary for this month?",
        "insert 2000 usd income as salary today",
    ]

    for message in test_messages:
        logger.info(f"\nProcessing test message: {message}")
        response = agent.process_message(message)
        logger.info(f"Response: {response}\n")
