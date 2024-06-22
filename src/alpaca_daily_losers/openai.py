import os
import re

from openai import OpenAI, OpenAIError
from tenacity import retry, stop_after_attempt, wait_random_exponential


class OpenAIAPI:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.model = "gpt-4o"

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
    def completion_with_backoff(self, **kwargs):
        """
        Makes a completion call to the OpenAI API with exponential backoff in case of failures.

        Returns:
            response (openai.Completion): The response object from the OpenAI API.
        """
        try:
            openai = OpenAI(api_key=self.api_key)
            return openai.chat.completions.create(**kwargs)
        except OpenAIError as e:
            print(f"OpenAI API error: {e}")
            raise

    def chat(self, msgs):
        """
        Chat with the OpenAI API.

        Args:
            msgs (list): List of messages.

        Returns:
            response (openai.ChatCompletion): The response from OpenAI.
        """
        response = self.completion_with_backoff(model=self.model, messages=msgs)
        return response

    def get_sentiment_analysis(self, title, symbol, article):
        """
        Get the sentiment analysis for financial news.

        Args:
            title (str): The title of the news.
            symbol (str): The stock symbol associated with the news.
            article (str): The content of the news article.

        Returns:
            signal (str): The sentiment analysis result - "BEARISH", "BULLISH", or "NEUTRAL".
        """
        try:
            system_message = (
                "You will work as a Sentiment Analysis for Financial news. "
                "I will share news headline, stock symbol and article. "
                "You will only answer as: BEARISH, BULLISH, NEUTRAL. "
                "No further explanation. Got it?"
            )

            message_history = [
                {"content": system_message, "role": "user"},
                {"content": f"{title}\n{symbol}\n{article}", "role": "user"},
            ]

            response = self.chat(message_history)

            sentiment = re.sub("[^a-zA-Z]", "", response.choices[0].message.content.strip().upper())

            if sentiment not in {"BEARISH", "BULLISH", "NEUTRAL"}:
                raise ValueError(f"Unexpected sentiment response: {sentiment}")

            return sentiment

        except (OpenAIError, ValueError) as e:
            print(f"Error in get_sentiment_analysis: {e}")
            return "NEUTRAL"
