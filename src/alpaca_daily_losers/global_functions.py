import logging
import os
from datetime import datetime, timedelta

import pandas as pd
from py_alpaca_api import Stock
from pytz import timezone
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

from alpaca_daily_losers.slack import Slack

# Constants
tz = timezone("US/Eastern")
ctime = datetime.now(tz)
today = ctime.strftime("%Y-%m-%d")
previous_day = (ctime - timedelta(days=1)).strftime("%Y-%m-%d")
year_ago = (ctime - timedelta(days=365)).strftime("%Y-%m-%d")

# Environment Variables
production = os.environ.get("PRODUCTION")
slack_username = os.environ.get("SLACK_USERNAME")

# Initialize logger
logger = logging.getLogger(__name__)


def calculate_indicators(history: pd.DataFrame, window: int) -> pd.DataFrame:
    """
    Calculate RSI and Bollinger Bands for a given history and window.

    Args:
        history (pd.DataFrame): Historical stock data.
        window (int): Window period for RSI and Bollinger Bands.

    Returns:
        df (pd.DataFrame): DataFrame with RSI and Bollinger Band indicators.
    """
    rsi = RSIIndicator(close=history["close"], window=window).rsi()
    bb = BollingerBands(close=history["close"], window=window, window_dev=2)
    history[f"rsi{window}"] = rsi
    history[f"bbhi{window}"] = bb.bollinger_hband_indicator()
    history[f"bblo{window}"] = bb.bollinger_lband_indicator()
    return history


def get_historical_data(
    stock_client: Stock, ticker: str, start_date: str, end_date: str
) -> pd.DataFrame:
    """
    Retrieve historical data for a given ticker.

    Args:
        stock_client (Stock): Stock client for retrieving historical data.
        ticker (str): Stock ticker symbol.
        start_date (str): Start date for historical data.
        end_date (str): End date for historical data.

    Returns:
        history (pd.DataFrame): Historical stock data.
    """
    try:
        history = stock_client.history.get_stock_data(symbol=ticker, start=start_date, end=end_date)
        return history
    except Exception as e:
        logger.warning(f"Error getting historical data for {ticker}. Error: {e}")
        return pd.DataFrame()


def get_ticker_data(tickers, stock_client: Stock, py_logger=None) -> pd.DataFrame:
    """
    Retrieve historical data for given tickers and compute technical indicators.

    Args:
        tickers (list): List of stock ticker symbols.
        stock_client (Stock): Stock client for retrieving historical data.
        py_logger (logging.Logger, optional): Logger for logging warnings and errors.

    Returns:
        df_tech (pd.DataFrame): DataFrame with the latest technical indicators for each ticker.
    """
    df_tech = []

    for ticker in tickers:

        try:
            history = get_historical_data(stock_client, ticker, year_ago, previous_day)
            if history.empty:
                continue
            for window in [14, 30, 50, 200]:
                history = calculate_indicators(history, window)

            df_tech_temp = history.tail(1)
            df_tech.append(df_tech_temp)
        except KeyError as ke:
            logger.warning(f"KeyError processing indicators for {ticker}. Error: {ke}")
        except Exception as e:
            logger.error(f"Unhandled exception processing {ticker}. Error: {e}")
            continue

    if df_tech:
        df_tech = pd.concat([x for x in df_tech if not x.empty], axis=0)
    else:
        df_tech = pd.DataFrame()

    return df_tech


def send_position_messages(positions: list, pos_type: str):
    """
    Sends position messages based on the type of position.

    Args:
        positions (list): List of position dictionaries.
        pos_type (str): Type of position ("buy", "sell", or "liquidate").

    Returns:
        bool: True if message was sent successfully, False otherwise.
    """
    position_names = {
        "sell": "sold",
        "buy": "bought",
        "liquidate": "liquidated",
    }

    if pos_type not in position_names:
        raise ValueError('Invalid type. Must be "sell", "buy", or "liquidate".')

    position_name = position_names[pos_type]

    if not positions:
        position_message = f"No positions to {pos_type}"
    else:
        position_message = f"Successfully {position_name} the following positions:\n"
        for position in positions:
            qty_key = "notional" if position_name in ["liquidated", "bought"] else "qty"
            qty = position[qty_key]
            symbol = position["symbol"]
            if position_name in ["liquidated", "bought"]:
                position_message += f"${qty} of {symbol} {position_name}\n"
            else:
                position_message += f"{position_name} {qty} shares of {symbol}\n"

    return send_message(position_message)


def send_message(message: str):
    """
    Send a message to Slack.

    Args:
        message (str): Message to send.
    """
    slack = Slack()
    try:
        if production == "False":
            print(f"Message: {message}")
        else:
            slack.send_message(channel="#app-development", text=message, username=slack_username)
    except Exception as e:
        print(f"Error sending message: {e}")
        return False
    return True
