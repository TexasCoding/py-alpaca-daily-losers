import os
import pandas as pd
from py_alpaca_api.alpaca import PyAlpacaApi

from .src.marketaux import MarketAux
from .src.article_extractor import ArticleExtractor
from .src.openai import OpenAIAPI
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
    """
    This code initializes an instance of the PyAlpacaApi class with the provided API key and API secret.
    It sets the api_paper parameter to True, indicating that the API should be used in a paper trading environment.

    The value of the production variable is derived from the environment variable "PRODUCTION".
    If the value of "PRODUCTION" is "True", the production variable is set to True.
    Otherwise, it is set to False.

    This code is used to configure and set up the PyAlpacaApi for interacting with the Alpaca API in a Python
    application.
    """

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
        This piece of code is a method called 'run' that belongs to a class. The method performs several actions in a
        specific sequence.

        The first action is to sell positions based on a sell criteria. It is unclear what exactly these criteria is as
        it is not mentioned in the code.

        The second action is to liquidate the positions in order to make cash amount to be 10% of the portfolio.
        Again, it is not mentioned how the positions are chosen to be liquidated.

        The third action is to check for buy opportunities. It is not specified how these opportunities are determined.

        This method assumes that there are corresponding functions or methods elsewhere in the codebase for each of
        these actions: 'sell_positions_from_criteria()', 'liquidate_positions_for_capital()', and
        'check_for_buy_opportunities()'. The method simply calls these functions in a predetermined order.

        It is important to note that without the implementation of these functions, the code will not execute correctly.
        It is recommended to review the codebase to find and examine the definitions of these functions in order to
        understand the complete logic of this 'run' method.
        """
        # Sell the positions based on the sell criteria
        self.sell_positions_from_criteria()
        # Liquidate the positions to make cash 10% of the portfolio
        self.liquidate_positions_for_capital()
        # Check for buy opportunities
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
        # Get the sell opportunities
        sell_opportunities = self.get_sell_opportunities()
        # Get the current positions
        current_positions = self.alpaca.position.get_all()
        sold_positions = []
        # Iterate through the sell opportunities and sell the stocks
        for symbol in sell_opportunities:
            # Try to sell the stock
            try:
                # Get the quantity of the stock to sell
                qty = current_positions[current_positions["symbol"] == symbol][
                    "qty"
                ].values[0]
                if self.alpaca.market.clock().is_open:
                    self.alpaca.position.close(
                        symbol_or_id=symbol, percentage=100
                    )
            # If there is an error, print or send a Slack message
            except Exception as e:
                send_message(f"Error selling {symbol}: {e}")
                continue
            # If the order was successful, append the sold position to the sold_positions list
            else:
                sold_positions.append({"symbol": symbol, "qty": qty})

        # Print or send Slack messages of the sold positions
        self._send_position_messages(sold_positions, "sell")

    ########################################################
    # Define the get_sell_opportunities function
    ########################################################
    def get_sell_opportunities(self) -> list:
        """

        This method, `get_sell_opportunities`, returns a list of symbols that are potential sell opportunities.

        The method first retrieves the current positions from the Alpaca API. If there are no positions other than
        "Cash", an empty list is returned.

        Next, the method gets the symbols from the current positions that are not cash.

        Then, it retrieves the assets history from the Yahoo API using the `get_ticker_data` method. The symbols
        retrieved earlier are used to fetch the asset's history.

        The sell criteria are then defined. It checks if any of the RSI values (14, 30, 50, 200) are greater than or
        equal to 70, or if any of the Bollinger Bands HI values (14, 30, 50, 200) are equal to 1.

        The positions that meet the sell criteria are filtered using the assets history.

        A list of symbols is created from the filtered positions.

        Next, the method checks for symbols with a profit percentage greater than 0.1. If those symbols are not already
        in the sell list, they are added.

        Finally, the sell list is returned.

        Example usage:
        ```python
        sell_opportunities = get_sell_opportunities()
        print(sell_opportunities)
        ```
        ```python
        Output:
        ["AAPL", "GOOG", "MSFT"]
        ```
        """
        # Get the current positions from the Alpaca API
        current_positions = self.alpaca.position.get_all()
        if current_positions[current_positions["symbol"] != "Cash"].empty:
            return []
        # Get the symbols from the current positions that are not cash
        current_positions_symbols = current_positions[
            current_positions["symbol"] != "Cash"
        ]["symbol"].tolist()
        # Get the assets history from the Yahoo API
        assets_history = self.get_ticker_data(current_positions_symbols)
        # Get the sell criteria
        sell_criteria = (
            (assets_history[["rsi14", "rsi30", "rsi50", "rsi200"]] >= 70).any(
                axis=1
            )
        ) | (
            (
                assets_history[["bbhi14", "bbhi30", "bbhi50", "bbhi200"]] == 1
            ).any(axis=1)
        )

        # Get the filtered positions based on the sell criteria
        sell_filtered_df = assets_history[sell_criteria]
        sell_list = sell_filtered_df["symbol"].tolist()

        percentage_change_list = current_positions[
            current_positions["profit_pct"] > 0.1
        ]["symbol"].tolist()

        for symbol in percentage_change_list:
            if symbol not in sell_list:
                sell_list.append(symbol)

        # Get the symbol list from the filtered positions
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
        # Get the current positions from the Alpaca API
        current_positions = self.alpaca.position.get_all()
        if current_positions.empty:
            sold_message = "No positions available to liquidate for capital"
            send_message(sold_message)
            return
        # Get the cash available from the Alpaca API
        # cash_available = float(self.alpaca.get_account().cash)
        cash_row = current_positions[current_positions["symbol"] == "Cash"]

        # Get the total holdings from the current positions and cash available
        total_holdings = current_positions["market_value"].sum()

        sold_positions = []
        # If the cash is less than 10% of the total holdings, liquidate the top 25% of performing stocks to make cash
        # 10% of the portfolio
        if cash_row["market_value"][0] / total_holdings < 0.1:
            # Sort the positions by profit percentage
            current_positions = current_positions[
                current_positions["symbol"] != "Cash"
            ].sort_values(by="profit_pct", ascending=False)
            # Sell the top 25% of performing stocks evenly to make cash 10% of total portfolio
            top_performers = current_positions.iloc[
                : int(len(current_positions) // 2)
            ]
            top_performers_market_value = top_performers["market_value"].sum()
            cash_needed = (
                total_holdings * 0.1 - cash_row["market_value"][0]
            ) + 5.00

            # Sell the top performers to make cash 10% of the portfolio
            for index, row in top_performers.iterrows():
                print(
                    f"Selling {row['symbol']} to make cash 10% portfolio cash requirement"
                )
                # Calculate the quantity to sell from the top performers
                # amount_to_sell = float((row['market_value'] / top_performers_market_value) * cash_needed)
                amount_to_sell = int(
                    (row["market_value"] / top_performers_market_value)
                    * cash_needed
                )
                # If the amount to sell is 0, continue to the next stock
                if amount_to_sell == 0:
                    continue

                # Market sell the stock
                try:
                    # Market sell the stock if the market is open
                    if self.alpaca.market.clock().is_open:
                        self.alpaca.order.market(
                            symbol=row["symbol"],
                            notional=amount_to_sell,
                            side="sell",
                        )
                # If there is an error, print or send a Slack message
                except Exception as e:
                    send_message(f"Error selling {row['symbol']}: {e}")
                    continue
                # If the order was successful, append the sold position to the sold_positions list
                else:
                    sold_positions.append(
                        {
                            "symbol": row["symbol"],
                            "notional": round(amount_to_sell, 2),
                        }
                    )
        # Print or send Slack messages of the sold positions
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
        ticker_data = self.get_ticker_data(losers)
        filter_tickers = self.buy_criteria(ticker_data)
        self.filter_tickers_with_news(filter_tickers)
        self.open_positions()

    ########################################################
    # Define the open_positions function
    ########################################################
    def open_positions(self, ticker_limit=8):
        """
        This method is used to open positions by buying stocks based on buy opportunities and sentiment analysis using
        OpenAI. By default, it limits to 8 stocks to buy.

        Parameters:
        - ticker_limit: Maximum number of stocks to buy (default = 8)

        Returns:
        None

        Example usage:
        open_positions(10)

        """
        print(
            "Buying orders based on buy opportunities and openai sentiment. Limit to 8 stocks by default"
        )
        # Get the tickers from the get_ticker_info function and convert symbols to a list
        tickers = self.alpaca.watchlist.get_assets(
            watchlist_name="DailyLosers"
        )

        # Get the available cash from the Alpaca API
        available_cash = self.alpaca.account.get().cash

        # This is the amount to buy for each stock
        if len(tickers) == 0:
            notional = 0
        else:
            notional = (available_cash / len(tickers[:ticker_limit])) - 1

        bought_positions = []
        # Iterate through the tickers and buy the stocks
        for ticker in tickers[:ticker_limit]:
            # Market buy the stock
            try:
                if self.alpaca.market.clock().is_open:
                    # print(f"Buying {ticker} with notional amount of {notional}")
                    self.alpaca.order.market(symbol=ticker, notional=notional)
            # If there is an error, print or send a Slack message
            except Exception as e:
                send_message(f"Error buying {ticker}: {e}")
                continue
            else:
                bought_positions.append(
                    {"symbol": ticker, "notional": round(notional, 2)}
                )
        # Print or send Slack messages of the bought positions
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
        This method retrieves the list of daily losers from the Alpaca screener, creates or updates a watchlist named
        "DailyLosers" with these symbols, and returns the assets in the watchlist.

        Parameters:
            - self: The instance of the class that calls this method.

        Returns:
            - A list of assets in the "DailyLosers" watchlist.

        Example usage:
            instance = ClassName()
            daily_losers = instance.get_daily_losers()

        Note: Make sure you have the necessary credentials and modules imported before using this method.
        """
        losers = self.alpaca.screener.losers()["symbol"].to_list()
        try:
            watchlist = self.alpaca.watchlist.get(watchlist_name="DailyLosers")
        except ValueError:
            self.alpaca.watchlist.create(
                name="DailyLosers", symbols=",".join(losers)
            )
        else:
            if watchlist.updated_at.strftime("%Y-%m-%d") != today:
                self.alpaca.watchlist.update(
                    watchlist_name="DailyLosers", symbols=",".join(losers)
                )
            else:
                print(f"Watchlist already updated today: {today}")

        return self.alpaca.watchlist.get_assets(watchlist_name="DailyLosers")

    ########################################################
    # Define the buy_criteria function
    ########################################################
    def buy_criteria(self, data) -> list:
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
        # Filter the DataFrame based on the buy criteria
        buy_criteria = (
            (data[["bblo14", "bblo30", "bblo50", "bblo200"]] == 1).any(axis=1)
        ) | ((data[["rsi14", "rsi30", "rsi50", "rsi200"]] <= 30).any(axis=1))
        # Get the filtered data based on the buy criteria
        buy_filtered_data = data[buy_criteria]

        filtered_data = list(buy_filtered_data["symbol"])

        if len(filtered_data) == 0:
            print("No tickers meet the buy criteria")
            return []

        try:
            self.alpaca.watchlist.update(
                watchlist_name="DailyLosers", symbols=",".join(filtered_data)
            )
        except ValueError:
            self.alpaca.watchlist.create(
                name="DailyLosers", symbols=",".join(filtered_data)
            )

        tickers = self.alpaca.watchlist.get_assets(
            watchlist_name="DailyLosers"
        )
        # Return the list of tickers that meet the buy criteria
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
        # Get the daily stock data, RSI, and Bollinger Bands for the stock
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
                    # Initialize RSI Indicator
                    history["rsi" + str(n)] = RSIIndicator(
                        close=history["close"], window=n
                    ).rsi()
                    # Initialize Hi BB Indicator
                    history["bbhi" + str(n)] = BollingerBands(
                        close=history["close"], window=n, window_dev=2
                    ).bollinger_hband_indicator()
                    # Initialize Lo BB Indicator
                    history["bblo" + str(n)] = BollingerBands(
                        close=history["close"], window=n, window_dev=2
                    ).bollinger_lband_indicator()
                # Get the last 16 days of data
                df_tech_temp = history.tail(1)
                # Append the DataFrame to the list
                df_tech.append(df_tech_temp)
            except KeyError:
                pass

        # If the list is not empty, concatenate the DataFrames
        if df_tech:
            df_tech = [x for x in df_tech if not x.empty]
            df_tech = pd.concat(df_tech)
        # If the list is empty, create an empty DataFrame
        else:
            df_tech = pd.DataFrame()
        # Return the DataFrame
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

        # Print or send Slack messages of the sold positions
        if not positions:
            # If no positions were sold, create the message
            position_message = "No positions to {}".format(pos_type)
        else:
            # If positions were sold, create the message
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
        # Print or send the message
        return send_message(position_message)
