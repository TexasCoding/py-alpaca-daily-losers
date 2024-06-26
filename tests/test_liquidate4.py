from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.alpaca_daily_losers.liquidate import Liquidate


class TestLiquidate:
    def setup_method(self):
        self.mock_trading_client = Mock()
        self.mock_logger = Mock()
        self.liquidator = Liquidate(self.mock_trading_client, self.mock_logger)

    @staticmethod
    @pytest.fixture()
    def current_positions():
        return pd.DataFrame(
            [
                {"symbol": "GOOG", "market_value": 13245.0},
                {"symbol": "AAPL", "market_value": 11245.7},
                {"symbol": "Cash", "market_value": 2000.0},
            ]
        )

    @staticmethod
    @pytest.fixture()
    def top_performers():
        return pd.DataFrame(
            [
                {"symbol": "GOOG", "market_value": 13245.0},
            ]
        )

    @patch.object(Liquidate, "get_top_performers")
    @patch.object(Liquidate, "calculate_cash_needed")
    def test_liquidate_positions(
        self, mock_cash_needed, mock_top_performers, current_positions, top_performers
    ):
        mock_cash_needed.return_value = 3000.0
        mock_top_performers.return_value = top_performers
        self.mock_trading_client.positions.get_all.return_value = current_positions
        self.liquidator.liquidate_positions()
        assert self.mock_trading_client.orders.market.call_count == 1
        assert self.mock_logger.warning.call_count == 0

    @patch.object(Liquidate, "get_top_performers")
    @patch.object(Liquidate, "calculate_cash_needed")
    def test_liquidate_positions_with_exception(
        self, mock_cash_needed, mock_top_performers, current_positions, top_performers
    ):
        mock_cash_needed.return_value = 3000.0
        mock_top_performers.return_value = top_performers
        self.mock_trading_client.positions.get_all.return_value = current_positions
        self.mock_trading_client.orders.market.side_effect = Exception()
        self.liquidator.liquidate_positions()
        assert self.mock_trading_client.orders.market.call_count == 1
        assert self.mock_logger.warning.call_count == 1

    def test_calculate_cash_needed(self):
        total_holdings = 13245.0
        cash_row = pd.DataFrame([{"symbol": "Cash", "market_value": 0}])
        cash_needed = self.liquidator.calculate_cash_needed(total_holdings, cash_row)
        assert cash_needed == 1324.5

    def test_get_top_performers(self):
        current_positions = pd.DataFrame(
            [
                {"symbol": "GOOG", "market_value": 13245.0, "profit_pct": 10},
                {"symbol": "AAPL", "market_value": 11245.7, "profit_pct": -1.32},
            ]
        )
        top_performers = self.liquidator.get_top_performers(current_positions)
        assert top_performers.equals(pd.DataFrame([current_positions.iloc[0]]))
