import textwrap

import requests
import yfinance as yf
import time
import logging
from bs4 import BeautifulSoup as bs

logger = logging.getLogger("yfinance")
logger.disabled = True
logger.propagate = False


class Yahoo:
    def __init__(self):
        pass

    @staticmethod
    def get_ticker(ticker: str):
        """
        This code defines a static method `get_ticker` that takes in a single parameter `ticker`. It uses the `yf`
        module to retrieve information for the given ticker.

        Parameters:
        - ticker (str): The ticker symbol for the desired stock.

        Returns:
        - Ticker: An object representing the stock with the given ticker symbol.
        """
        return yf.Ticker(ticker)

    def get_news_data(self, ticker: str):
        """
        Retrieves news data for a given ticker.

        Parameters:
        ticker (str): The ticker symbol of the stock.

        Returns:
        list: A list of dictionaries containing information about each news article.
              Each dictionary includes the URL of the article.

        Raises:
        None.
        """
        news = self.get_ticker(ticker).news
        return [self.create_news_dict(url) for url in news]

    @staticmethod
    def create_news_dict(url: dict):
        """
        This code is a static method called `create_news_dict` that takes in a `url` dictionary as a parameter and
        returns a new dictionary containing the `title` and `link` values from the `url` dictionary.
        """
        return {
            "title": url["title"],
            "url": url["link"],
        }

    def get_articles(self, ticker: str, limit: int = 5):
        """
        This function retrieves a specified number of articles related to a given ticker symbol.

        Parameters:
        - ticker: The ticker symbol for the desired articles.
        - limit: The maximum number of articles to retrieve. Defaults to 5 if not specified.

        Returns:
        - A list of dictionaries representing the articles. Each dictionary contains the following fields:
            - symbol: The ticker symbol.
            - title: The title of the article.
            - content: The content of the article.

        Exceptions:
        - If an error occurs during the retrieval or scraping process, an exception is thrown and the function returns
        None.
        """
        articles = []
        try:
            data = self.get_news_data(ticker)
            for article in data[:limit]:
                article_content = self.scrape_article(article["url"])
                if article_content is not None:
                    articles.append(
                        self._create_article_dict(
                            ticker, article, article_content
                        )
                    )
        except Exception:
            return None
        return articles

    def _create_article_dict(
        self, ticker: str, article: dict, article_content: str
    ):
        """
        Create an article dictionary.

        Parameters:
            ticker (str): The ticker symbol of the article.
            article (dict): The article information.
            article_content (str): The content of the article.

        Returns:
            dict: The created article dictionary with the following keys:
                - "symbol" (str): The ticker symbol.
                - "title" (str): The title of the article.
                - "content" (str): The truncated content of the article, limited to 10000 characters.
        """
        return {
            "symbol": ticker,
            "title": article["title"],
            "content": self.truncate("".join(article_content), 10000),
        }

    @staticmethod
    def scrape_article(url: str):
        """
        Scrape Article

        This static method is used to scrape the main content of an article from a given URL. It uses the requests
        library to make an HTTP GET request to the URL and then uses the bs4 library to parse the HTML response.

        Parameters:
            url (str): The URL of the article to scrape.

        Returns:
            str or None: The scraped article content as a string if scraping is successful, None otherwise.

        Raises:
            None

        Note:
            - The method includes a sleep of 1 second before making the HTTP request to be nice to the server.
            - If the HTTP response status code is not 200 (OK), the method returns None.
            - If the article content is not found in the parsed HTML, the method returns None.
        """
        time.sleep(1)  # Be nice to the server
        response = requests.get(url)
        if response.status_code != 200:
            return None
        soup = bs(response.text, "html.parser")
        if soup.find(class_="caas-body") is None:
            return None

        return soup.find(class_="caas-body").text

    @staticmethod
    def truncate(string: str, length: int):
        """
        Function: truncate

        Description: Truncates a given string to a specified length. If the length of the string
                     is less than or equal to the specified length, the original string is returned.
                     Otherwise, the string is truncated to the specified length using textwrap.shorten()
                     function from the 'textwrap' module, with an empty placeholder.

        Args:
            string (str): The input string to be truncated.
            length (int): The maximum length for the truncated string.

        Returns:
            str: The truncated string.

        Example:
            string = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
            length = 20
            truncated_string = truncate(string, length)
            print(truncated_string)  # Output: "Lorem ipsum dolor si..."

        Note:
            This function requires the 'textwrap' module to be imported.
        """
        if length >= len(string):
            return string
        else:
            return textwrap.shorten(string, width=length, placeholder="")

    def get_recommendations(self, ticker: str):
        """
        This method is a part of a class and is used to retrieve recommendations for a given ticker.

        Parameters:
        - ticker (str): The ticker symbol for which recommendations are to be retrieved.

        Returns:
        - recommendations (list): A list of recommendations for the given ticker symbol.
        """
        return self.get_ticker(ticker).recommendations

    def get_sentiment(self, ticker: str):
        """
        This method is used to determine the sentiment of a given ticker symbol.

        Parameters:
        - ticker (str): The ticker symbol of the stock.

        Returns:
        - sentiment (str): The sentiment of the stock, which can be one of the following:
            - "NEUTRAL": If there are no recommendations available for the given ticker symbol.
            - "BULLISH": If the ratio of strong buy and buy recommendations is greater than 0.7.
            - "BEARISH": If the ratio of strong sell, sell, and hold recommendations is less than or equal to 0.7.
        """
        time.sleep(1)  # Be nice to the server
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
