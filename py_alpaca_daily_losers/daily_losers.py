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
    def __init__(self):
        self.alpaca = PyAlpacaApi(
            api_key=api_key, api_secret=api_secret, api_paper=api_paper
        )
        self.production = True if os.getenv("PRODUCTION") == "True" else False

    def run(self):
        """
        Run the daily losers strategy
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
        Sell the positions based on the criteria
        The strategy is to sell the stocks that are overbought based on RSI and Bollinger Bands, or based on the criteria
        return: True if the function is successful
        return: False if market is closed or there are no stocks to sell
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
                    self.alpaca.order.market(
                        symbol=symbol, qty=qty, side="sell"
                    )
            # If there is an error, print or send a slack message
            except Exception as e:
                send_message(f"Error selling {symbol}: {e}")
                continue
            # If the order was successful, append the sold position to the sold_positions list
            else:
                sold_positions.append({"symbol": symbol, "qty": qty})

        # Print or send slack messages of the sold positions
        if not sold_positions:
            # If no positions were sold, create the message
            sold_message = "No positions to sell"
        else:
            # If positions were sold, create the message
            sold_message = (
                "Successfully{} sold the following positions:\n".format(
                    " pretend"
                    if not self.alpaca.market.clock().is_open
                    else ""
                )
            )
            for position in sold_positions:
                sold_message += "{qty} shares of {symbol}\n".format(
                    qty=position["qty"], symbol=position["symbol"]
                )
        # Print or send the message
        send_message(sold_message)

    ########################################################
    # Define the get_sell_opportunities function
    ########################################################
    def get_sell_opportunities(self) -> list:
        """
        Get the sell assets opportunities based on the RSI and Bollinger Bands
        return: List of sell opportunities
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
        # Get the symbol list from the filtered positions
        return sell_filtered_df["symbol"].tolist()

    ########################################################
    # Define the liquidate_positions_for_capital function
    ########################################################
    def liquidate_positions_for_capital(self):
        """
        Liquidate the positions to make cash 10% of the portfolio
        The strategy is to sell the top 25% of performing stocks evenly to make cash 10% of total portfolio
        return: True if the function is successful
        return: False if the market is closed or there are no stocks to sell
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
        # If the cash is less than 10% of the total holdings, liquidate the top 25% of performing stocks to make cash 10% of the portfolio
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
            cash_needed = total_holdings * 0.1 - cash_row["market_value"][0]

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
                # If there is an error, print or send a slack message
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
        # Print or send slack messages of the sold positions
        if not sold_positions:
            # If no positions were sold, create the message
            sold_message = "No positions liquidated for capital"
        else:
            # If positions were sold, create the message
            # Pretend trades if the market is closed
            sold_message = (
                "Successfully{} liquidated the following positions:\n".format(
                    " pretend"
                    if not self.alpaca.market.clock().is_open
                    else ""
                )
            )
            for position in sold_positions:
                sold_message += "Sold ${qty} of {symbol}\n".format(
                    qty=position["notional"], symbol=position["symbol"]
                )
        # Print or send the message
        send_message(sold_message)

    ########################################################
    # Define the check_for_buy_opportunities function
    ########################################################
    def check_for_buy_opportunities(self):
        losers = self.get_daily_losers()
        ticker_data = self.get_ticker_data(losers)
        filter_tickers = self.buy_criteria(ticker_data)
        self.filter_tickers_with_news(filter_tickers)
        self.open_posistions()

    ########################################################
    # Define the open_posistions function
    ########################################################
    def open_posistions(self, ticker_limit=8):
        """
        Buy the stocks based on the buy opportunities, limit to 8 stocks by default
        Should only be run at market open
        Send a slack message with the bought positions, or print the bought positions
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
            # If there is an error, print or send a slack message
            except Exception as e:
                send_message(f"Error buying {ticker}: {e}")
                continue
            else:
                bought_positions.append(
                    {"symbol": ticker, "notional": round(notional, 2)}
                )
        # Print or send slack messages of the bought positions
        if not bought_positions:
            # If no positions were bought, create the message
            bought_message = "No positions bought"
        else:
            # If positions were bought, create the message
            bought_message = (
                "Successfully{} bought the following positions:\n".format(
                    " pretend"
                    if not self.alpaca.market.clock().is_open
                    else ""
                )
            )
            for position in bought_positions:
                bought_message += "${qty} of {symbol}\n".format(
                    qty=position["notional"], symbol=position["symbol"]
                )
        # Print or send the message
        send_message(bought_message)

    ########################################################
    # Define the filter_tickers_with_news function
    ########################################################
    def filter_tickers_with_news(self, tickers) -> list:
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
        except Exception:
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
        losers = self.alpaca.screener.losers()["symbol"].to_list()
        try:
            watchlist = self.alpaca.watchlist.get(watchlist_name="DailyLosers")
        except Exception:
            watchlist = self.alpaca.watchlist.create(
                name="DailyLosers", symbols=",".join(losers)
            )
        else:
            if watchlist.updated_at.strftime("%Y-%m-%d") != today:
                watchlist = self.alpaca.watchlist.update(
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
        Get the buy criteria for the stock
        :param data: DataFrame: stock data
        :return: list: tickers
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
        except Exception:
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
        Get the daily stock data, RSI, and Bollinger Bands
        this function is used for the daily stock data, RSI, and Bollinger Bands
        there is no need to add the sentiment of the news articles
        :return: DataFrame: stock data
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
            except Exception:
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
        if df_tech != []:
            df_tech = [x for x in df_tech if not x.empty]
            df_tech = pd.concat(df_tech)
        # If the list is empty, create an empty DataFrame
        else:
            df_tech = pd.DataFrame()
        # Return the DataFrame
        return df_tech
