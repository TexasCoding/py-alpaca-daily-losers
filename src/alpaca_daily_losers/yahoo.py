import logging
import textwrap
import time
from typing import Union

import pandas as pd
import yfinance as yf
from bs4 import BeautifulSoup as bs

from .requests import Requests

logger = logging.getLogger("yfinance")
logger.disabled = True
logger.propagate = False


class Yahoo:
    def __init__(self) -> None:
        pass

    ########################################################
    # ///////////  static get_ticker method  //////////////#
    ########################################################
    @staticmethod
    def get_ticker(ticker: str) -> Union[yf.Ticker, None]:
        """
        Get the Yahoo Finance ticker object for the given ticker symbol.

        Args:
            ticker (str): The ticker symbol.

        Returns:
            Union[yf.Ticker, None]: The Yahoo Finance ticker object if the ticker symbol is valid,
            otherwise None.
        """
        return yf.Ticker(ticker)

    ########################################################
    # ////////  static create_news_dict method  ///////////#
    ########################################################
    @staticmethod
    def create_news_dict(url: dict) -> dict:
        """
        Create a dictionary containing the title and URL of a news article.

        Args:
            url (dict): A dictionary containing the title and link of the news article.

        Returns:
            dict: A dictionary with the title and URL of the news article.
        """
        return {
            "title": url["title"],
            "url": url["link"],
        }

    ########################################################
    # /////////////  _get_news_data method  ///////////////#
    ########################################################
    def get_news_data(self, ticker: str) -> list[dict]:
        """
        Retrieves the news data for a given ticker.

        Args:
            ticker (str): The ticker symbol of the stock.

        Returns:
            dict: The news data for the given ticker.
        """
        news = self.get_ticker(ticker).news
        return [self.create_news_dict(url) for url in news]

    ########################################################
    # //////////  static _scrape_article method  //////////#
    ########################################################
    @staticmethod
    def scrape_article(url: str) -> str:
        """
        Scrapes the article text from the given URL.

        Args:
            url (str): The URL of the article.

        Returns:
            str: The text content of the article, or None if the article body is not found.
        """
        time.sleep(1)
        request = Requests().get(url)
        soup = bs(request.text, "html.parser")
        return soup.find(class_="caas-body").text if soup.find(class_="caas-body") else None

    ########################################################
    # ////////////  static _truncate method  //////////////#
    ########################################################
    @staticmethod
    def truncate(text: str, length: int) -> str:
        """
        Truncates a given text to a specified length.

        Args:
            text (str): The text to be truncated.
            length (int): The maximum length of the truncated text.

        Returns:
            str: The truncated text.
        """
        return textwrap.shorten(text, length, placeholder="") if len(text) > length else text

    ########################################################
    # ///////////  _create_article_dict method  ///////////#
    ########################################################
    def create_article_dict(self, ticker: str, article: dict, article_content: str) -> dict:
        """
        Create a dictionary representing an article.

        Args:
            ticker (str): The symbol of the stock.
            article (dict): The dictionary containing article information.
            article_content (str): The content of the article.

        Returns:
            dict: A dictionary representing the article with the following keys:
                - symbol: The symbol of the stock.
                - title: The title of the article.
                - content: The truncated content of the article.
        """
        return {
            "symbol": ticker,
            "title": article["title"],
            "content": self.truncate(article_content, 9000),
        }

    ########################################################
    # //////////////  get_articles method  ////////////////#
    ########################################################
    def get_articles(self, ticker: str, limit: int = 5) -> Union[list, None]:
        """
        Retrieves news articles related to a given ticker.

        Args:
            ticker (str): The ticker symbol for the stock.
            limit (int, optional): The maximum number of articles to retrieve. Defaults to 5.

        Returns:
            Union[list, None]: A list of dictionaries representing the articles, or None if an
            error occurs.
        """
        articles = []
        try:
            for article in self.get_news_data(ticker)[:limit]:
                content = self.scrape_article(article["url"])
                if content:
                    articles.append(
                        self.create_article_dict(
                            ticker=ticker, article=article, article_content=content
                        )
                    )
        except Exception:
            return None
        return articles

    ########################################################
    # ////////////  _get_recommendations method ///////////#
    ########################################################
    def get_recommendations(self, ticker: str) -> Union[dict, pd.DataFrame]:
        """
        Retrieves the recommendations for a given ticker.

        Args:
            ticker (str): The ticker symbol of the stock.

        Returns:
            Union[dict, pd.DataFrame]: The recommendations for the given ticker.
        """
        return self.get_ticker(ticker).recommendations

    ########################################################
    # //////////////  get_sentiment method  ///////////////#
    ########################################################
    def get_sentiment(self, ticker: str) -> str:
        """
        Retrieves the sentiment of a given ticker symbol.

        Args:
            ticker (str): The ticker symbol of the stock.

        Returns:
            str: The sentiment of the stock, which can be "BULLISH", "BEARISH", or "NEUTRAL".
        """
        time.sleep(1)
        recommendations = self.get_recommendations(ticker)
        if recommendations.empty:
            return "NEUTRAL"
        buy = recommendations["strongBuy"].sum() + recommendations["buy"].sum()
        sell = (
            recommendations["strongSell"].sum()
            + recommendations["sell"].sum()
            + recommendations["hold"].sum()
        )
        return "BULLISH" if (buy / (buy + sell)) > 0.7 else "BEARISH"
