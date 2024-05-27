import os
import pandas as pd
from py_alpaca_api.alpaca import PyAlpacaApi

from .src.marketaux import MarketAux
from .src.article_extractor import ArticleExtractor
from .src.openai import OpenAIAPI
from .src.yahoo import Yahoo
from .src.global_fuctions import send_message

from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator

from tqdm import tqdm
from dotenv import load_dotenv
from datetime import datetime
from datetime import timedelta
from pytz import timezone

tz = timezone("US/Eastern")
ctime = datetime.now(tz)
today = ctime.strftime("%Y-%m-%d")
previous_day = (ctime - timedelta(days=1)).strftime("%Y-%m-%d")
year_ago = (ctime - timedelta(days=365)).strftime("%Y-%m-%d")

load_dotenv()

api_key = str(os.getenv("API_KEY"))
api_secret = str(os.getenv("API_SECRET"))
api_paper = True if os.getenv("API_PAPER") == "True" else False


class DailyLosers:
    def __init__(self):
        """
        This code initializes an instance of the PyAlpacaApi class with the provided API key and API secret.
        It sets the api_paper parameter to True, indicating that the API should be used in a paper trading environment.

        The value of the production variable is derived from the environment variable "PRODUCTION".
        If the value of "PRODUCTION" is "True", the production variable is set to True.
        Otherwise, it is set to False.

        This code is used to configure and set up the PyAlpacaApi for interacting with the Alpaca API in a Python
        application.
        """
        self.alpaca = PyAlpacaApi(
            api_key=api_key, api_secret=api_secret, api_paper=True
        )
        self.production = True if os.getenv("PRODUCTION") == "True" else False

    def run(self):
        """
        Executes the main logic of the program.

        This method performs the following steps:
        1. Sells the positions based on the sell criteria.
        2. Liquidates the positions to make cash 10% of the portfolio.
        3. Checks for buy opportunities.
        """

        self.sell_positions_from_criteria()
        self.liquidate_positions_for_capital()
        self.check_for_buy_opportunities()

    ########################################################
    # Define the sell_positions_from_criteria function
    ########################################################
    def sell_positions_from_criteria(self):
        """
        Sell Positions from Criteria

        This method is used to sell positions based on sell criteria. It retrieves sell opportunities, current
        positions, and then iterates through the sell opportunities to sell the stocks.

        Parameters:
            - None

        Returns:
            - None

        """
        print("Selling positions based on sell criteria")

        sell_opportunities = self.get_sell_opportunities()

        current_positions = self.alpaca.position.get_all()
        sold_positions = []

        for symbol in sell_opportunities:
            try:
                qty = current_positions[current_positions["symbol"] == symbol][
                    "qty"
                ].values[0]
                if self.alpaca.market.clock().is_open:
                    self.alpaca.position.close(
                        symbol_or_id=symbol, percentage=100
                    )
            except Exception as e:
                send_message(f"Error selling {symbol}: {e}")
                continue
            else:
                sold_positions.append({"symbol": symbol, "qty": qty})

        self._send_position_messages(sold_positions, "sell")

    ########################################################
    # Define the get_sell_opportunities function
    ########################################################
    def get_sell_opportunities(self) -> list:
        """
        Retrieves a list of symbols representing potential sell opportunities based on specified criteria.

        Returns:
            sell_list (list): A list of symbols representing potential sell opportunities.
        """
        current_positions = self.alpaca.position.get_all()
        if current_positions[current_positions["symbol"] != "Cash"].empty:
            return []

        current_positions_symbols = current_positions[
            current_positions["symbol"] != "Cash"
        ]["symbol"].tolist()

        assets_history = self.get_ticker_data(current_positions_symbols)

        sell_criteria = (
            (assets_history[["rsi14", "rsi30", "rsi50", "rsi200"]] >= 70).any(
                axis=1
            )
        ) | (
            (
                assets_history[["bbhi14", "bbhi30", "bbhi50", "bbhi200"]] == 1
            ).any(axis=1)
        )

        sell_filtered_df = assets_history[sell_criteria]
        sell_list = sell_filtered_df["symbol"].tolist()

        percentage_change_list = current_positions[
            current_positions["profit_pct"] > 0.1
        ]["symbol"].tolist()

        for symbol in percentage_change_list:
            if symbol not in sell_list:
                sell_list.append(symbol)

        return sell_list

    ########################################################
    # Define the liquidate_positions_for_capital function
    ########################################################
    def liquidate_positions_for_capital(self):
        """
        Liquidates positions to ensure cash is 10% of the portfolio.

        This method calculates the current cash available and compares it to the total holdings in the portfolio.
        If the cash is less than 10% of the total holdings, it sells the top 25% performing stocks to make cash
        10% of the portfolio.

        Returns:
            None
        """
        print(
            "Liquidating positions for capital to make cash 10% of the portfolio"
        )

        current_positions = self.alpaca.position.get_all()
        if current_positions.empty:
            sold_message = "No positions available to liquidate for capital"
            send_message(sold_message)
            return

        cash_row = current_positions[current_positions["symbol"] == "Cash"]

        total_holdings = current_positions["market_value"].sum()
        sold_positions = []

        if cash_row["market_value"][0] / total_holdings < 0.1:
            current_positions = current_positions[
                current_positions["symbol"] != "Cash"
            ].sort_values(by="profit_pct", ascending=False)

            top_performers = current_positions.iloc[
                : int(len(current_positions) // 2)
            ]
            top_performers_market_value = top_performers["market_value"].sum()
            cash_needed = (
                total_holdings * 0.1 - cash_row["market_value"][0]
            ) + 5.00

            for index, row in top_performers.iterrows():
                print(
                    f"Selling {row['symbol']} to make cash 10% portfolio cash requirement"
                )

                amount_to_sell = int(
                    (row["market_value"] / top_performers_market_value)
                    * cash_needed
                )

                if amount_to_sell == 0:
                    continue

                try:
                    if self.alpaca.market.clock().is_open:
                        self.alpaca.order.market(
                            symbol=row["symbol"],
                            notional=amount_to_sell,
                            side="sell",
                        )
                except Exception as e:
                    send_message(f"Error selling {row['symbol']}: {e}")
                    continue
                else:
                    sold_positions.append(
                        {
                            "symbol": row["symbol"],
                            "notional": round(amount_to_sell, 2),
                        }
                    )

        self._send_position_messages(sold_positions, "liquidate")

    ########################################################
    # Define the check_for_buy_opportunities function
    ########################################################
    def check_for_buy_opportunities(self):
        """
        The following code is a method definition that checks for buy opportunities. It performs the following steps:

        1. Calls the `get_daily_losers()` method to get the list of tickers that have performed poorly on a given day.
        2. Calls the `get_ticker_data(losers)` method, passing in the list of losers, to get detailed data for each
        ticker.
        3. Applies buy criteria to the ticker data by calling the `buy_criteria(ticker_data)` method, which returns a
        filtered list of tickers that meet the buy criteria.
        4. Filters the list of tickers with news by calling the `filter_tickers_with_news(filter_tickers)` method.
        5. Opens positions for the filtered tickers by calling the `open_positions()` method.

        This method assumes that the necessary data and methods required for each step are available within the current
        class or its dependencies.

        """
        losers = self.get_daily_losers()
        buy_opportunities = self.filter_tickers_with_news(losers)

        if len(buy_opportunities) > 0:
            print(
                f"{len(buy_opportunities)} buy opportunities found. Opening positions..."
            )
            self.open_positions()
        else:
            print("No buy opportunities found")

    ########################################################
    # Define the open_positions function
    ########################################################
    def open_positions(self, ticker_limit=8):
        """
        Opens positions by buying stocks based on buy opportunities and openai sentiment.

        Args:
            ticker_limit (int): The maximum number of stocks to buy. Defaults to 8.

        Returns:
            None
        """
        print(
            "Buying orders based on buy opportunities and openai sentiment. Limit to 8 stocks by default"
        )

        tickers = self.alpaca.watchlist.get_assets(
            watchlist_name="DailyLosers"
        )

        available_cash = self.alpaca.account.get().cash

        if len(tickers) == 0:
            notional = 0
        else:
            notional = (available_cash / len(tickers[:ticker_limit])) - 1

        bought_positions = []

        for ticker in tickers[:ticker_limit]:
            try:
                if self.alpaca.market.clock().is_open:
                    self.alpaca.order.market(symbol=ticker, notional=notional)
            except Exception as e:
                send_message(f"Error buying {ticker}: {e}")
                continue
            else:
                bought_positions.append(
                    {"symbol": ticker, "notional": round(notional, 2)}
                )

        self._send_position_messages(bought_positions, "buy")

    ########################################################
    # Define the filter_tickers_with_news function
    ########################################################
    def filter_tickers_with_news(self, tickers) -> list:
        """
        Filter tickers with news using OpenAI and MarketAux.

        This method takes a list of tickers as input and filters out the tickers that have news articles associated
        with them. It uses the MarketAux API to retrieve news for each ticker and the ArticleExtractor to extract
        articles from the news. It also utilizes the OpenAI API to perform sentiment analysis on the articles and
        determine if they are bullish or bearish.

        Parameters:
        - tickers (list): A list of tickers to filter.

        Returns:
        - list: A list of tickers that have news articles associated with them.

        Note:
        - If no tickers with news are found, an empty list is returned.

        """
        news = MarketAux()
        article = ArticleExtractor()
        openai = OpenAIAPI()
        filtered_tickers = []

        for i, ticker in tqdm(
            enumerate(tickers),
            desc=f"• Analizing news for {len(tickers)} tickers, using OpenAI & MarketAux: ",
        ):
            m_news = news.get_symbol_news(symbol=ticker)
            articles = article.extract_articles(m_news)

            if len(articles) > 0:
                bullish = 0
                bearish = 0
                for art in articles:
                    sentiment = openai.get_sentiment_analysis(
                        title=art["title"],
                        symbol=ticker,
                        article=art["content"],
                    )
                    if sentiment == "BULLISH":
                        bullish += 1
                    else:
                        bearish += 1

                if bullish > bearish:
                    filtered_tickers.append(ticker)

        if len(filtered_tickers) == 0:
            print("No tickers with news found")
            return []

        try:
            self.alpaca.watchlist.update(
                watchlist_name="DailyLosers",
                symbols=",".join(filtered_tickers),
            )
        except ValueError:
            self.alpaca.watchlist.create(
                name="DailyLosers", symbols=",".join(filtered_tickers)
            )

        tickers = self.alpaca.watchlist.get_assets(
            watchlist_name="DailyLosers"
        )

        return tickers

    ########################################################
    # Define the get_daily_losers function
    ########################################################
    def get_daily_losers(self) -> list:
        """
        Retrieves the daily losers from Alpaca, filters them based on certain criteria,
        and updates the 'DailyLosers' watchlist in Alpaca.

        Returns:
            A list of assets in the 'DailyLosers' watchlist.
        """
        filtered_losers = []
        yahoo = Yahoo()
        losers = self.alpaca.screener.losers(total_losers_returned=130)[
            "symbol"
        ].to_list()

        losers = self.get_ticker_data(losers)
        losers = self.buy_criteria(losers)

        for i, ticker in tqdm(
            enumerate(losers),
            desc=f"• Getting recommendations for {len(losers)} tickers, from Yahoo Finance: ",
        ):
            sentiment = yahoo.get_sentiment(ticker)
            if sentiment == "NEUTRAL" or sentiment == "BEARISH":
                losers.remove(ticker)
        try:
            self.alpaca.watchlist.get(watchlist_name="DailyLosers")
        except Exception:
            self.alpaca.watchlist.create(
                name="DailyLosers", symbols=",".join(losers)
            )
        else:
            self.alpaca.watchlist.update(
                watchlist_name="DailyLosers", symbols=",".join(losers)
            )

        return self.alpaca.watchlist.get_assets(watchlist_name="DailyLosers")

    ########################################################
    # Define the buy_criteria function
    ########################################################
    def buy_criteria(self, data: pd.DataFrame) -> list:
        """
        Filter the DataFrame based on the buy criteria and update the DailyLosers watchlist.

        Args:
            self (object): The current object.
            data (DataFrame): The input DataFrame containing stock data.

        Returns:
            list: The list of tickers that meet the buy criteria.

        Raises:
            ValueError: If there is an error updating or creating the DailyLosers watchlist.

        """

        buy_criteria = (
            (data[["bblo14", "bblo30", "bblo50", "bblo200"]] == 1).any(axis=1)
        ) | ((data[["rsi14", "rsi30", "rsi50", "rsi200"]] <= 30).any(axis=1))

        buy_filtered_data = data[buy_criteria]

        filtered_data = list(buy_filtered_data["symbol"])

        if len(filtered_data) == 0:
            print("No tickers meet the buy criteria")
            return []

        try:
            self.alpaca.watchlist.update(
                watchlist_name="DailyLosers", symbols=",".join(filtered_data)
            )
        except Exception:
            self.alpaca.watchlist.create(
                name="DailyLosers", symbols=",".join(filtered_data)
            )

        tickers = self.alpaca.watchlist.get_assets(
            watchlist_name="DailyLosers"
        )

        return tickers

    ########################################################
    # Define the get_ticker_data function
    ########################################################
    def get_ticker_data(self, tickers) -> pd.DataFrame:
        """
        Gets ticker data for multiple stocks from the Alpaca API.

        Parameters:
        - `tickers` (list): A list of ticker symbols for the stocks.

        Returns:
        - `df_tech` (pd.DataFrame): A DataFrame containing the ticker data, RSI, and Bollinger Bands for each stock.

        Example usage:
        ```python
        tickers = ['AAPL', 'MSFT', 'GOOGL']
        data = get_ticker_data(tickers)
        ```
        """
        df_tech = []

        for i, ticker in tqdm(
            enumerate(tickers),
            desc="• Analizing ticker data for "
            + str(len(tickers))
            + " symbols from Alpaca API",
        ):
            try:
                history = self.alpaca.history.get_stock_data(
                    symbol=ticker, start=year_ago, end=previous_day
                )
            except ValueError:
                continue

            try:
                for n in [14, 30, 50, 200]:
                    history["rsi" + str(n)] = RSIIndicator(
                        close=history["close"], window=n
                    ).rsi()
                    history["bbhi" + str(n)] = BollingerBands(
                        close=history["close"], window=n, window_dev=2
                    ).bollinger_hband_indicator()
                    history["bblo" + str(n)] = BollingerBands(
                        close=history["close"], window=n, window_dev=2
                    ).bollinger_lband_indicator()
                df_tech_temp = history.tail(1)
                df_tech.append(df_tech_temp)
            except KeyError:
                pass

        if df_tech:
            df_tech = [x for x in df_tech if not x.empty]
            df_tech = pd.concat(df_tech)
        else:
            df_tech = pd.DataFrame()

        return df_tech

    ########################################################
    # Define the _send_position_messages function
    ########################################################
    def _send_position_messages(self, positions: list, pos_type: str):
        """
        Sends position messages based on the type of position.

        Args:
            positions (list): List of position dictionaries.
            pos_type (str): Type of position ("buy", "sell", or "liquidate").

        Returns:
            bool: True if message was sent successfully, False otherwise.
        """
        if pos_type == "sell":
            position_name = "sold"
        elif pos_type == "buy":
            position_name = "bought"
        elif pos_type == "liquidate":
            position_name = "liquidated"
        else:
            raise ValueError(
                'Invalid type. Must be "sell", "buy", or "liquidate".'
            )

        if not positions:
            position_message = "No positions to {}".format(pos_type)
        else:
            position_message = (
                "Successfully{} {} the following positions:\n".format(
                    (
                        " pretend"
                        if not self.alpaca.market.clock().is_open
                        else ""
                    ),
                    position_name,
                )
            )
            for position in positions:
                if position_name == "liquidated":
                    position_message += "{qty} shares of {symbol}\n".format(
                        qty=position["notional"], symbol=position["symbol"]
                    )

                elif position_name == "sold":
                    position_message += "{qty} shares of {symbol}\n".format(
                        qty=position["qty"], symbol=position["symbol"]
                    )
                else:
                    position_message += "${qty} of {symbol}\n".format(
                        qty=position["notional"], symbol=position["symbol"]
                    )

        return send_message(position_message)
