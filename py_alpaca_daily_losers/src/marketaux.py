import os
import requests
import json

from dotenv import load_dotenv

load_dotenv()


class MarketAux:
    def __init__(self):
        self.api_key = os.getenv("MARKETAUX_API_KEY")

    def get_symbol_news(self, symbol: str) -> list:
        url = "https://api.marketaux.com/v1/news/all"

        params = {
            "symbols": symbol,
            "filter_entities": True,
            "sentiment_gte": 0,
            "limit": 5,
            "language": "en",
            "api_token": self.api_key,
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            res_dict = json.loads(response.text)
            return_data = []
            for link in res_dict["data"]:
                return_data.append(link["url"]) if link["url"] != "" else None
            return return_data
        else:
            raise Exception(f"Error fetching data from MarketAux API: {response.text}")
