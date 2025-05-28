import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class ExchangeRateAPI:
    def __init__(self):
        self.base_url = "https://api.fastforex.io"
        self.api_key = os.getenv("FASTFOREX_API_KEY")
        if not self.api_key:
            raise ValueError("FASTFOREX_API_KEY environment variable is not set")

    def get_exchange_rate(self, from_currency, to_currency, date=None):
        """
        Fetch exchange rate between two currencies using FastForex API
        """
        url = f"{self.base_url}/fetch-one"
        params = {"from": from_currency, "to": to_currency, "api_key": self.api_key}

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Extract the rate from the new response format
            rate = data["result"].get(to_currency)
            if rate is None:
                return {
                    "success": False,
                    "error": f"Exchange rate not found for {to_currency}",
                }

            return {
                "success": True,
                "rate": rate,
                "date": data["updated"],
                "from": from_currency,
                "to": to_currency,
            }
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    def get_available_currencies(self):
        """
        Fetch list of available currencies from FastForex API
        """
        url = f"{self.base_url}/currencies"
        params = {"api_key": self.api_key}

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return {"success": True, "symbols": data.get("currencies", {})}
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}
