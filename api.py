import requests
from datetime import datetime


class ExchangeRateAPI:
    def __init__(self):
        self.base_url = "https://api.exchangerate.host"

    def get_exchange_rate(self, from_currency, to_currency, date=None):
        """
        Fetch exchange rate between two currencies for a specific date
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        url = f"{self.base_url}/convert"
        params = {"from": from_currency, "to": to_currency, "amount": 1, "date": date}

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return {
                "rate": data["result"],
                "date": data["date"],
                "from": from_currency,
                "to": to_currency,
            }
        except requests.RequestException as e:
            return {"error": str(e)}

    def get_available_currencies(self):
        """
        Fetch list of available currencies
        """
        url = f"{self.base_url}/symbols"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return data["symbols"]
        except requests.RequestException as e:
            return {"error": str(e)}
