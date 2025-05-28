import google.generativeai as genai
from functions import FinancialFunctions
import json
import os
from dotenv import load_dotenv
import datetime

load_dotenv()


class GeminiAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        self.functions = FinancialFunctions()

        # Define function schemas for Gemini
        self.function_schemas = [
            {
                "name": "log_expense",
                "description": "Log an expense transaction",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The ID of the user",
                        },
                        "category": {
                            "type": "string",
                            "description": "The category of the expense",
                        },
                        "amount": {
                            "type": "number",
                            "description": "The amount of the expense",
                        },
                        "date": {
                            "type": "string",
                            "description": "The date of the expense in YYYY-MM-DD format (optional)",
                        },
                    },
                    "required": ["user_id", "category", "amount"],
                },
            },
            {
                "name": "log_income",
                "description": "Log an income transaction",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The ID of the user",
                        },
                        "category": {
                            "type": "string",
                            "description": "The category of the income",
                        },
                        "amount": {
                            "type": "number",
                            "description": "The amount of the income",
                        },
                        "date": {
                            "type": "string",
                            "description": "The date of the income in YYYY-MM-DD format (optional)",
                        },
                    },
                    "required": ["user_id", "category", "amount"],
                },
            },
            {
                "name": "get_monthly_summary",
                "description": "Get a summary of transactions for a specific month",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The ID of the user",
                        },
                        "year": {"type": "integer", "description": "The year"},
                        "month": {"type": "integer", "description": "The month (1-12)"},
                    },
                    "required": ["user_id", "year", "month"],
                },
            },
            {
                "name": "get_exchange_rate",
                "description": "Get the exchange rate between two currencies",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "from_currency": {
                            "type": "string",
                            "description": "The source currency code",
                        },
                        "to_currency": {
                            "type": "string",
                            "description": "The target currency code",
                        },
                        "date": {
                            "type": "string",
                            "description": "The date in YYYY-MM-DD format (optional)",
                        },
                    },
                    "required": ["from_currency", "to_currency"],
                },
            },
        ]

    def process_message(self, message, user_id):
        """
        Process a user message and handle function calling

        Args:
            message (str): The user's message
            user_id (int): The ID of the user

        Returns:
            str: The response to the user
        """
        try:
            # Add user context to the message
            context = f"User ID: {user_id}\nUser message: {message}"

            # Generate response with function calling
            response = self.model.generate_content(
                context,
                generation_config={"temperature": 0.7, "top_p": 0.8, "top_k": 40},
                tools=[{"function_declarations": self.function_schemas}],
            )

            # Check if the response includes a function call
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "content") and candidate.content:
                    content = candidate.content
                    if hasattr(content, "parts") and content.parts:
                        for part in content.parts:
                            if hasattr(part, "function_call"):
                                function_call = part.function_call
                                function_name = function_call.name
                                args = function_call.args
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
                                # Add user_id to function calls if not present
                                if "user_id" not in args and function_name in [
                                    "log_expense",
                                    "log_income",
                                    "get_monthly_summary",
                                ]:
                                    args["user_id"] = user_id
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
                                    return "I'm sorry, I don't know how to handle that function."

                                # Generate a natural language response based on the function result
                                if result.get("success"):
                                    if function_name in ["log_expense", "log_income"]:
                                        return f"Successfully logged the transaction. {result['message']}"
                                    elif function_name == "get_monthly_summary":
                                        summary = result["summary"]
                                        return f"Here's your monthly summary:\nIncome: ${summary['income']:.2f}\nExpenses: ${summary['expenses']:.2f}\nBalance: ${summary['balance']:.2f}\nTotal transactions: {summary['transactions']}"
                                    elif function_name == "get_exchange_rate":
                                        rate = result["rate"]
                                        return f"The exchange rate from {rate['from']} to {rate['to']} on {rate['date']} is {rate['rate']:.4f}"
                                else:
                                    return f"I encountered an error: {result.get('error', 'Unknown error')}"

            # If no function call was made, return the model's response
            return response.text

        except Exception as e:
            return f"I encountered an error: {str(e)}"
