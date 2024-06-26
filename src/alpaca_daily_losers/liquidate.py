import logging

import pandas as pd
from py_alpaca_api.trading import Trading

from alpaca_daily_losers.global_functions import send_message, send_position_messages

LIQUIDATE_PERCENTAGE = 1.0


class Liquidate:

    def __init__(self, trading_client: Trading, py_logger: logging.Logger):
        self.trade = trading_client
        self.py_logger = py_logger

    @staticmethod
    def calculate_cash_needed(total_holdings: float, cash_row: pd.DataFrame) -> float:
        """
        Calculate the amount of cash needed to liquidate a portion of holdings.

        Parameters:
            total_holdings (float): The total value of the holdings to be liquidated.
            cash_row (pd.DataFrame): A DataFrame containing the cash information.

        Returns:
            float: The amount of cash needed for liquidation, including a fixed fee of $5.00.
        """
        return total_holdings * 0.1 - cash_row["market_value"].iloc[0]

    @staticmethod
    def get_top_performers(current_positions: pd.DataFrame) -> pd.DataFrame:
        """
        Returns the top performers from the given current positions DataFrame.

        Parameters:
            current_positions (pd.DataFrame): DataFrame containing the current positions.

        Returns:
            pd.DataFrame: DataFrame containing the top performers.
        """
        non_cash_positions = current_positions[current_positions["symbol"] != "Cash"]
        non_cash_positions = non_cash_positions[
            non_cash_positions["profit_pct"] > LIQUIDATE_PERCENTAGE
        ].sort_values(by="profit_pct", ascending=False)

        return non_cash_positions.iloc[: len(non_cash_positions)]

    def liquidate_positions(self) -> None:
        """
        Liquidates positions to make cash 10% of the portfolio.

        This method sells positions in order to meet the requirement of having cash
        equal to 10% of the portfolio's total value. It identifies the top performers
        in the current positions and calculates the amount of cash needed to meet the
        requirement. It then sells the necessary amount of shares for each top performer.

        Returns:
            None
        """
        current_positions = self.trade.positions.get_all()

        if current_positions[current_positions["symbol"] != "Cash"].empty:
            self._send_liquidation_message("No positions available to liquidate for capital")
            return

        cash_row = current_positions[current_positions["symbol"] == "Cash"]
        total_holdings = current_positions["market_value"].sum()

        # Check if cash is less than 10% of total holdings
        if cash_row["market_value"].iloc[0] / total_holdings < 0.1:
            top_performers = self.get_top_performers(current_positions)
            if top_performers.empty:
                self._send_liquidation_message("No top performers found to liquidate for capital")
                return
            top_performers_market_value = top_performers["market_value"].sum()
            cash_needed = self.calculate_cash_needed(total_holdings, cash_row)
            sold_positions = self._sell_top_performers(
                top_performers, top_performers_market_value, cash_needed
            )
            send_position_messages(sold_positions, "liquidate")

    def _sell_top_performers(
        self, top_performers: pd.DataFrame, top_performers_market_value: float, cash_needed: float
    ) -> list:
        """
        Sells positions of top performers to liquidate the required cash.

        Parameters:
            top_performers (pd.DataFrame): DataFrame containing top performer positions.
            top_performers_market_value (float): The total market value of top performers.
            cash_needed (float): The amount of cash needed to be liquidated.

        Returns:
            list: List of sold positions with their details.
        """
        sold_positions = []
        for _, row in top_performers.iterrows():
            amount_to_sell = int((row["market_value"] / top_performers_market_value) * cash_needed)
            if amount_to_sell == 0:
                continue

            try:
                self.trade.orders.market(symbol=row["symbol"], notional=amount_to_sell, side="sell")
                sold_positions.append(
                    {"symbol": row["symbol"], "notional": round(amount_to_sell, 2)}
                )
            except Exception as e:
                self.py_logger.warning(f"Error liquidating position {row['symbol']}. Error: {e}")
                self._send_liquidation_message(f"Error selling {row['symbol']}: {e}")

        return sold_positions

    @staticmethod
    def _send_liquidation_message(message: str):
        """
        Send a liquidation message using the global `send_message` function.

        Parameters:
            message (str): The message to be sent.
        """
        send_message(message)
