import os
from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()


class OpenAIAPI:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")

    ########################################################
    # Define the OpenAi chat function
    ########################################################
    def chat(self, msgs):
        """
        Chat with the OpenAI API
        :param msgs: List of messages
        return: OpenAI response
        """
        openai = OpenAI(api_key=self.api_key)
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo", messages=msgs
        )
        message = response
        return message

    ########################################################
    # Define the get_market_sentiment function
    ########################################################
    def get_sentiment_analysis(self, title, symbol, article):
        """
        get_sentiment_analysis(self, title, symbol, article)

        This method is used to get the sentiment analysis for financial news. It takes in the title, symbol,
        and article as parameters.

        Parameters:
            - title (str): The title of the news.
            - symbol (str): The stock symbol associated with the news.
            - article (str): The content of the news article.

        Returns:
            - signal (str): The sentiment analysis result as either "BEARISH", "BULLISH", or "NEUTRAL".

        """
        message_history = []
        sentiments = []
        # Send the system message to the OpenAI API
        system_message = "You will work as a Sentiment Analysis for Financial news. \
            I will share news headline, stock symbol and article. \
                You will only answer as:\n\n BEARISH,BULLISH,NEUTRAL. No further explanation. \n Got it?"

        message_history.append({"content": system_message, "role": "user"})
        self.chat(message_history)

        # Send the article to the OpenAI API
        user_message = "{}\n{}\n{}".format(title, symbol, article)

        message_history.append({"content": user_message, "role": "user"})
        response = self.chat(message_history)
        sentiments.append(
            {
                "title": title,
                "symbol": symbol,
                "article": article,
                "signal": response.choices[0].message.content,
            }
        )
        message_history.pop()
        # Return the sentiment
        return sentiments[0]["signal"]
