import logging
from typing import List

import pandas as pd
from py_alpaca_api import Stock, Trading

from alpaca_daily_losers.global_functions import (
    get_ticker_data,
    send_message,
    send_position_messages,
)


class ClosePositions:
    def __init__(self, trading_client: Trading, stock_client: Stock, py_logger: logging.Logger):
        self.trade = trading_client
        self.stock = stock_client
        self.py_logger = py_logger

    def sell_positions_from_criteria(
        self, stop_loss_percentage: float = 10.0, take_profit_percentage: float = 10.0
    ) -> None:
        """
        Sells positions based on the defined sell criteria, including RSI and
        Bollinger Band High Index (BBHI) thresholds, as well as take profit
        and stop loss conditions.

        This method first retrieves the current positions, filters out the
        cash position, and then uses the `get_stocks_to_sell()` method to
        determine which positions should be sold. It then calls
        the `_sell_positions()` method to execute the sell orders and
        sends messages to notify of the sold positions. If no positions meet the
        sell criteria, a message is sent indicating that no sell opportunities were found.
        Raises:
            Exception: If an error occurs while selling the positions.
        """
        try:
            stocks_to_sell = self.get_stocks_to_sell(
                stop_loss_percentage=stop_loss_percentage,
                take_profit_percentage=take_profit_percentage,
            )
            if not stocks_to_sell:
                send_message("No sell opportunities found.")
                return

            current_positions = self.trade.positions.get_all()
            sold_positions = self._sell_positions(stocks_to_sell, current_positions)
            send_position_messages(sold_positions, "sell")
        except Exception as e:
            self.py_logger.error(f"Error selling positions from criteria. Error: {e}")

    def _sell_positions(
        self, stocks_to_sell: List[str], current_positions: pd.DataFrame
    ) -> List[dict]:
        """
        Sell positions for the given stocks.

        Args:
            stocks_to_sell (list): List of symbols for the stocks to sell.
            current_positions (pandas.DataFrame): DataFrame containing the current positions.

        Returns:
            list: List of dictionaries representing the sold positions, each containing
            the symbol and quantity.
        """
        sold_positions = []

        for symbol in stocks_to_sell:
            try:
                qty = current_positions.loc[current_positions["symbol"] == symbol, "qty"].values[0]
                self.trade.positions.close(symbol_or_id=symbol, qty=qty)
                sold_positions.append({"symbol": symbol, "qty": qty})
            except Exception as e:
                self.py_logger.warning(f"Could not close {symbol}. Error: {e}")
                send_message(f"Error selling {symbol}: {e}")

        return sold_positions

    def get_stocks_to_sell(
        self, stop_loss_percentage: float = 10.0, take_profit_percentage: float = 10.0
    ) -> List[str]:
        """
        Retrieves a list of stocks to sell based on specific criteria.

        Args:
            stop_loss_percentage (float): The stop loss percentage criteria.
            take_profit_percentage (float): The take profit percentage criteria.

        Returns:
            list: A list of stocks to sell.
        """
        current_positions = self.trade.positions.get_all()
        non_cash_positions = current_positions[current_positions["symbol"] != "Cash"]

        if non_cash_positions.empty:
            return []

        current_positions_symbols = non_cash_positions["symbol"].tolist()
        assets_history = get_ticker_data(current_positions_symbols, self.stock, self.py_logger)

        RSI_COLUMNS = ["rsi14", "rsi30", "rsi50", "rsi200"]
        BBHI_COLUMNS = ["bbhi14", "bbhi30", "bbhi50", "bbhi200"]

        criterion1 = assets_history[RSI_COLUMNS] >= 70
        criterion2 = assets_history[BBHI_COLUMNS] == 1

        sell_criteria = criterion1.any(axis=1) | criterion2.any(axis=1)
        sell_filtered_df = assets_history[sell_criteria]

        stocks_to_sell = sell_filtered_df["symbol"].tolist()

        # Add stocks based on take profit and stop loss criteria
        stocks_to_sell = self._add_stocks_from_criteria(
            non_cash_positions, stocks_to_sell, stop_loss_percentage, take_profit_percentage
        )

        return stocks_to_sell

    def _add_stocks_from_criteria(
        self,
        non_cash_positions: pd.DataFrame,
        stocks_to_sell: List[str],
        stop_loss_percentage: float,
        take_profit_percentage: float,
    ) -> List[str]:
        """
        Adds stocks to the sell list based on stop loss and take profit criteria.

        Args:
            non_cash_positions (pd.DataFrame): DataFrame of non-cash positions.
            stocks_to_sell (list): Current list of stocks to sell.
            stop_loss_percentage (float): Stop loss percentage criteria.
            take_profit_percentage (float): Take profit percentage criteria.

        Returns:
            list: Updated list of stocks to sell.
        """
        take_profit_list = non_cash_positions[
            non_cash_positions["profit_pct"] > take_profit_percentage
        ]["symbol"].tolist()

        stop_loss_list = non_cash_positions[
            non_cash_positions["profit_pct"] < -stop_loss_percentage
        ]["symbol"].tolist()

        for stock in take_profit_list + stop_loss_list:
            if stock not in stocks_to_sell:
                stocks_to_sell.append(stock)

        return stocks_to_sell
