import logging

import pandas as pd
from py_alpaca_api.trading import Trading

from alpaca_daily_losers.global_functions import send_message, send_position_messages


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
        return (total_holdings * 0.1 - cash_row["market_value"].iloc[0]) + 5.00

    @staticmethod
    def get_top_performers(current_positions: pd.DataFrame) -> pd.DataFrame:
        """
        Returns the top performers from the given current positions DataFrame.

        Parameters:
        - current_positions (pd.DataFrame): DataFrame containing the current positions.

        Returns:
        - pd.DataFrame: DataFrame containing the top performers.
        """
        non_cash_positions = current_positions[current_positions["symbol"] != "Cash"].sort_values(
            by="profit_pct", ascending=False
        )
        return non_cash_positions.iloc[: int(len(non_cash_positions) // 2)]

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
        print("Liquidating positions to make cash 10% of the portfolio...")
        current_positions = self.trade.positions.get_all()
        if current_positions[current_positions["symbol"] != "Cash"].empty:
            self.send_liquidation_message("No positions available to liquidate for capital")
            return
        cash_row = current_positions[current_positions["symbol"] == "Cash"]
        total_holdings = current_positions["market_value"].sum()
        sold_positions = []
        if cash_row["market_value"].iloc[0] / total_holdings < 0.1:
            top_performers = self.get_top_performers(current_positions)
            top_performers_market_value = top_performers["market_value"].sum()
            cash_needed = self.calculate_cash_needed(total_holdings, cash_row)
            for index, row in top_performers.iterrows():
                print(f"Selling {row['symbol']} to make cash 10% portfolio cash requirement")
                amount_to_sell = int(
                    (row["market_value"] / top_performers_market_value) * cash_needed
                )
                if amount_to_sell == 0:
                    continue
                try:
                    self.trade.orders.market(
                        symbol=row["symbol"],
                        notional=amount_to_sell,
                        side="sell",
                    )
                except Exception as e:
                    self.py_logger.warning(
                        f"Error liquidating position {row['symbol']}. Error: {e}"
                    )
                    self.send_liquidation_message(f"Error selling {row['symbol']}: {e}")
                    continue
                else:
                    sold_positions.append(
                        {
                            "symbol": row["symbol"],
                            "notional": round(amount_to_sell, 2),
                        }
                    )
        send_position_messages(sold_positions, "liquidate")

    @staticmethod
    def send_liquidation_message(message: str):  # Renamed method to be more specific
        send_message(message)
