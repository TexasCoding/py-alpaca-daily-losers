import logging
import os
from typing import List

import pandas as pd
from py_alpaca_api import PyAlpacaAPI

from alpaca_daily_losers.close_positions import ClosePositions
from alpaca_daily_losers.global_functions import (
    get_ticker_data,
    send_message,
    send_position_messages,
)
from alpaca_daily_losers.liquidate import Liquidate
from alpaca_daily_losers.openai import OpenAIAPI
from alpaca_daily_losers.statistics import Statistics

# Constants
WATCHLIST_NAME = "DailyLosers"
DEFAULT_BUY_LIMIT = 4
DEFAULT_ARTICLE_LIMIT = 4
DEFAULT_STOP_LOSS_PERCENTAGE = 10.0
DEFAULT_TAKE_PROFIT_PERCENTAGE = 10.0
DEFAULT_FUTURE_DAYS = 4

# Load environment configuration
PRODUCTION = os.environ.get("PRODUCTION") == "True"
API_KEY = os.environ.get("ALPACA_API_KEY")
API_SECRET = os.environ.get("ALPACA_SECRET_KEY")
API_PAPER = os.environ.get("ALPACA_PAPER") == "True"

# Configure logging
logging.basicConfig(
    level=logging.WARNING if PRODUCTION else logging.INFO,
    format="%(name)s %(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


class DailyLosers:
    def __init__(self):
        self.alpaca = PyAlpacaAPI(api_key=API_KEY, api_secret=API_SECRET, api_paper=API_PAPER)
        self.liquidate = Liquidate(trading_client=self.alpaca.trading, py_logger=logger)
        self.close = ClosePositions(
            trading_client=self.alpaca.trading, stock_client=self.alpaca.stock, py_logger=logger
        )
        self.statistics = Statistics(account=self.alpaca.trading.account, py_logger=logger)
        self.openai = OpenAIAPI()

    def run(
        self,
        buy_limit=DEFAULT_BUY_LIMIT,
        article_limit=DEFAULT_ARTICLE_LIMIT,
        stop_loss_percentage=DEFAULT_STOP_LOSS_PERCENTAGE,
        take_profit_percentage=DEFAULT_TAKE_PROFIT_PERCENTAGE,
        future_days=DEFAULT_FUTURE_DAYS,
    ):
        """
        Executes the main logic of the program, orchestrating the various components.
        """

        try:
            self.close.sell_positions_from_criteria(stop_loss_percentage, take_profit_percentage)
        except Exception as e:
            logger.error(f"Error selling positions from criteria: {e}")

        try:
            self.liquidate.liquidate_positions()
        except Exception as e:
            logger.error(f"Error liquidating positions for capital: {e}")

        try:
            current_positions = self.alpaca.trading.positions.get_all()

            cash_row = current_positions[current_positions["symbol"] == "Cash"]
            total_holdings = current_positions["market_value"].sum()

            # Check if cash is less than 10% of total holdings
            if cash_row["market_value"].iloc[0] / total_holdings < 0.1:
                print(
                    "Cash is less than 10% of total holdings. Can't open any new positions today."
                )
                logger.info(
                    "Cash is less than 10% of total holdings. \
                    Can't open any new positions today."
                )
                return

            self.check_for_buy_opportunities(buy_limit, article_limit, future_days)
        except Exception as e:
            logger.error(f"Error entering new positions: {e}")

    def check_for_buy_opportunities(
        self,
        buy_limit=DEFAULT_BUY_LIMIT,
        article_limit=DEFAULT_ARTICLE_LIMIT,
        future_days=DEFAULT_FUTURE_DAYS,
    ):
        """
        Checks for buy opportunities based on daily losers and news sentiment.
        """
        try:
            losers = self.get_daily_losers(future_days)
            if not losers:
                print("No buy opportunities found.")
                logger.info("No buy opportunities found.")
                return

            tickers = self.filter_tickers_with_news(losers, article_limit, buy_limit)
            if tickers:
                logger.info(f"Found {len(tickers)} buy opportunities.")
                self.open_positions(tickers=tickers, ticker_limit=buy_limit)
            else:
                print("No buy opportunities found.")
                logger.info("No buy opportunities found.")
        except Exception as e:
            logger.error(f"Error checking for buy opportunities: {e}")

    def open_positions(self, tickers: List[str], ticker_limit=DEFAULT_BUY_LIMIT):
        """
        Opens buying orders based on buy opportunities and OpenAI sentiment.
        """
        try:
            available_cash = self.alpaca.trading.account.get().cash
            if not tickers:
                send_message("No tickers to buy.")
                return

            notional = (available_cash / len(tickers[:ticker_limit])) - 1
            bought_positions = []

            for ticker in tickers[:ticker_limit]:
                try:
                    self.alpaca.trading.orders.market(symbol=ticker, notional=notional)
                    bought_positions.append({"symbol": ticker, "notional": round(notional, 2)})
                except Exception as e:
                    logger.warning(f"Error entering new position for {ticker}: {e}")
                    send_message(f"Error buying {ticker}: {e}")
                    continue

            send_position_messages(positions=bought_positions, pos_type="buy")
        except Exception as e:
            logger.error(f"Error opening positions: {e}")

    def update_or_create_watchlist(self, name: str, symbols: List[str]):
        """
        Updates an existing watchlist or creates a new one.
        """
        try:
            self.alpaca.trading.watchlists.update(watchlist_name=name, symbols=symbols)
        except Exception as e:
            logger.info(f"Watchlist could not be updated, attempting to create new watchlist: {e}")
            try:
                self.alpaca.trading.watchlists.create(name=name, symbols=symbols)
            except Exception as e:
                logger.error(f"Could not create or update the watchlist {name}: {e}")

    def filter_tickers_with_news(
        self,
        tickers: List[str],
        article_limit=DEFAULT_ARTICLE_LIMIT,
        filter_ticker_limit=DEFAULT_BUY_LIMIT,
    ):
        """
        Filters tickers based on news sentiment.
        """
        try:
            filtered_tickers = []
            for ticker in tickers:
                if len(filtered_tickers) >= filter_ticker_limit:
                    break

                articles = self.alpaca.trading.news.get_news(
                    symbol=ticker, limit=article_limit, content_length=4000
                )
                if len(articles) >= article_limit:
                    bullish_count = sum(
                        1
                        for article in articles
                        if self.openai.get_sentiment_analysis(
                            title=article["title"],
                            symbol=article["symbol"],
                            article=article["content"],
                        )
                        == "BULLISH"
                    )

                    if bullish_count > len(articles) // 2:
                        filtered_tickers.append(ticker)

            self.update_or_create_watchlist(name=WATCHLIST_NAME, symbols=filtered_tickers)
            return self.alpaca.trading.watchlists.get_assets(watchlist_name=WATCHLIST_NAME)
        except Exception as e:
            logger.warning(f"Error filtering tickers with news: {e}")
            return []

    def get_daily_losers(self, future_days=DEFAULT_FUTURE_DAYS):
        """
        Get daily losers based on the criteria and predictions.
        """
        try:
            losers = self.alpaca.stock.predictor.get_losers_to_gainers(future_periods=future_days)
            losers_data = get_ticker_data(
                tickers=losers, stock_client=self.alpaca.stock, py_logger=logger
            )
            return self.buy_criteria(losers_data)
        except Exception as e:
            logger.error(f"Error fetching daily losers: {e}")
            return []

    def buy_criteria(self, data: pd.DataFrame):
        """
        Apply buy criteria to the given DataFrame and return symbols that meet the criteria.
        """
        RSI_COLUMNS = ["rsi14", "rsi30", "rsi50", "rsi200"]
        BBLO_COLUMNS = ["bblo14", "bblo30", "bblo50", "bblo200"]

        criteria = data[RSI_COLUMNS].le(30).any(axis=1) | data[BBLO_COLUMNS].eq(1).any(axis=1)
        filtered_data = data[criteria]
        filtered_symbols = list(filtered_data["symbol"])

        if not filtered_symbols:
            logger.info("No tickers meet the buy criteria")
            return []

        logger.info(f"Found {len(filtered_symbols)} tickers that meet the buy criteria.")
        self.update_or_create_watchlist(name=WATCHLIST_NAME, symbols=filtered_symbols)
        return filtered_symbols
