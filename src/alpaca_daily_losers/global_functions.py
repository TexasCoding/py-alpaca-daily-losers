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


def get_ticker_data(tickers, stock_client: Stock, py_logger) -> pd.DataFrame:
    """
    Retrieve historical data for given tickers and compute technical indicators.

    Args:
        tickers (list): List of stock ticker symbols.
        stock_client (Stock): Stock client for retrieving historical data.
        py_logger (logging.Logger): Logger for logging warnings and errors.

    Returns:
        df_tech (pd.DataFrame): DataFrame with the latest technical indicators for each ticker.
    """
    df_tech = []

    for ticker in tickers:
        try:
            history = stock_client.history.get_stock_data(
                symbol=ticker, start=year_ago, end=previous_day
            )
        except Exception as e:
            py_logger.warning(f"Error getting historical data for {ticker}. Error: {e}")
            continue

        try:
            for n in [14, 30, 50, 200]:
                history[f"rsi{n}"] = RSIIndicator(close=history["close"], window=n).rsi()
                bb = BollingerBands(close=history["close"], window=n, window_dev=2)
                history[f"bbhi{n}"] = bb.bollinger_hband_indicator()
                history[f"bblo{n}"] = bb.bollinger_lband_indicator()
            df_tech_temp = history.tail(1)
            df_tech.append(df_tech_temp)
        except KeyError as ke:
            py_logger.warning(f"KeyError processing indicators for {ticker}. Error: {ke}")

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
            qty_key = "notional" if position_name == "liquidated" else "qty"
            qty = position[qty_key]
            symbol = position["symbol"]
            position_message += f"{qty} shares of {symbol}\n"

    return send_message(position_message)


def send_message(message: str):
    """
    Send a message to Slack.

    Args:
        message (str): Message to send.
    """
    slack = Slack()
    if production == "False":
        print(f"Message: {message}")
    else:
        slack.send_message(channel="#app-development", message=message, username=slack_username)
