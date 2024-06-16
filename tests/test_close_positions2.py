import logging
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.alpaca_daily_losers.close_positions import ClosePositions


@pytest.fixture
def trading_client():
    return Mock()


@pytest.fixture
def stock_client():
    return Mock()


@pytest.fixture
def py_logger():
    return logging.getLogger()


@pytest.fixture
def close_positions(trading_client, stock_client, py_logger):
    return ClosePositions(trading_client, stock_client, py_logger)


@pytest.fixture
def data_frame():
    return pd.DataFrame({"symbol": ["AAPL", "GOOG", "CASH"], "qty": [1, 2, 0]})


@pytest.fixture
def stocks_to_sell():
    return ["AAPL", "GOOG"]


def test_sell_positions_from_criteria_no_opportunities(close_positions):
    close_positions.get_stocks_to_sell = Mock(return_value=[])
    with patch("src.alpaca_daily_losers.close_positions.send_message") as mock_send_message:
        close_positions.sell_positions_from_criteria()
        mock_send_message.assert_called_once_with("No sell opportunities found.")


def test_sell_positions_from_criteria(close_positions, trading_client, data_frame, stocks_to_sell):
    close_positions.get_stocks_to_sell = Mock(return_value=stocks_to_sell)
    trading_client.positions.get_all = Mock(return_value=data_frame)
    with patch("src.alpaca_daily_losers.close_positions.send_message") as mock_send_message, patch(
        "src.alpaca_daily_losers.close_positions.send_position_messages"
    ) as mock_send_position_messages:
        close_positions.sell_positions_from_criteria()
        mock_send_message.assert_not_called()
        mock_send_position_messages.assert_called_once()


def test__sell_positions(close_positions, trading_client, data_frame, stocks_to_sell):
    trading_client.positions.close = Mock()
    close_positions._sell_positions(stocks_to_sell, data_frame)
    assert trading_client.positions.close.call_count == len(stocks_to_sell)
