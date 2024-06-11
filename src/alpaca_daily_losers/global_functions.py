import os
from datetime import datetime, timedelta

import pandas as pd
from dotenv import load_dotenv
from py_alpaca_api import Stock
from pytz import timezone
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from tqdm import tqdm

from .slack import Slack

load_dotenv()

tz = timezone("US/Eastern")
ctime = datetime.now(tz)
today = ctime.strftime("%Y-%m-%d")
previous_day = (ctime - timedelta(days=1)).strftime("%Y-%m-%d")
year_ago = (ctime - timedelta(days=365)).strftime("%Y-%m-%d")

production = os.getenv("PRODUCTION")
slack_username = os.getenv("SLACK_USERNAME")


########################################################
# Define the get_ticker_data method
########################################################
def get_ticker_data(tickers, stock_client: Stock, py_logger) -> pd.DataFrame:

    df_tech = []

    for i, ticker in tqdm(
        enumerate(tickers),
        desc="• Analyzing ticker data for " + str(len(tickers)) + " symbols from Alpaca API",
    ):
        try:
            history = stock_client.history.get_stock_data(
                symbol=ticker, start=year_ago, end=previous_day
            )
        except Exception as e:
            py_logger.warning(f"Error get historical data for {ticker}. Error: {e}")
            continue

        try:
            for n in [14, 30, 50, 200]:
                history["rsi" + str(n)] = RSIIndicator(close=history["close"], window=n).rsi()
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
# Define the _send_position_messages method
########################################################
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

    try:
        position_name = position_names[pos_type]
    except KeyError:
        raise ValueError('Invalid type. Must be "sell", "buy", or "liquidate".')

    if not positions:
        position_message = f"No positions to {pos_type}"
    else:
        position_message = f"Successfully {position_name} the following positions:\n"

        for position in positions:
            if position_name == "liquidated":
                qty_key = "notional"
            elif position_name == "sold":
                qty_key = "qty"
            else:
                qty_key = "notional"

            qty = position[qty_key]
            symbol = position["symbol"]

            position_message += f"{qty} shares of {symbol}\n"
    return send_message(position_message)


def send_message(message):
    """
    Send a message to Slack
    :param message: str: message to send
    """
    slack = Slack()
    if production == "False":
        print(message)
    else:
        slack.send_message(channel="#app-development", message=message, username=slack_username)
