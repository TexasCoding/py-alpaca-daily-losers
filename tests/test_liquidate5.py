import logging
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from alpaca_daily_losers.liquidate import (
    Liquidate,  # assuming the module name is liquidate.py
)


@pytest.fixture
def mock_trading_client():
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_logger():
    return logging.getLogger("test_logger")


@pytest.fixture
def liquidate(mock_trading_client, mock_logger):
    return Liquidate(trading_client=mock_trading_client, py_logger=mock_logger)


def test_calculate_cash_needed():
    total_holdings = 10000.0
    cash_row = pd.DataFrame({"market_value": [500.0]})
    result = Liquidate.calculate_cash_needed(total_holdings, cash_row)
    assert result == 500.0


def test_get_top_performers():
    current_positions = pd.DataFrame(
        {"symbol": ["AAPL", "MSFT", "GOOGL", "Cash"], "profit_pct": [0.2, 20, 30, 0]}
    )
    result = Liquidate.get_top_performers(current_positions)
    expected = pd.DataFrame({"symbol": ["GOOGL", "MSFT"], "profit_pct": [30, 20]})
    assert (
        result["symbol"].tolist()
        == expected["symbol"]
        .iloc[: len(current_positions[current_positions["symbol"] != "Cash"])]
        .tolist()
    )


def test_liquidate_positions_sufficient_cash(liquidate, mock_trading_client):
    current_positions = pd.DataFrame(
        {"symbol": ["AAPL", "MSFT", "Cash"], "market_value": [700.0, 800.0, 2000.0]}
    )

    mock_trading_client.positions.get_all.return_value = current_positions

    liquidate.liquidate_positions()
    liquidate._send_liquidation_message == "No positions available to liquidate for capital"


def test_liquidate_positions_insufficient_cash(liquidate, mock_trading_client):
    current_positions = pd.DataFrame(
        {
            "symbol": ["AAPL", "MSFT", "GOOGL", "Cash"],
            "market_value": [4000.0, 3000.0, 3000.0, 100.0],
            "profit_pct": [10, 15, 20, 0],
        }
    )

    mock_trading_client.positions.get_all.return_value = current_positions

    liquidate.calculate_cash_needed = MagicMock(return_value=505.0)
    liquidate.get_top_performers = MagicMock(
        return_value=current_positions[current_positions["symbol"] != "Cash"]
    )
    liquidate._sell_top_performers = MagicMock(
        return_value=[{"symbol": "AAPL", "notional": round(134.0, 2)}]
    )

    with patch(
        "src.alpaca_daily_losers.global_functions.send_position_messages"
    ) as mock_send_position_messages:
        liquidate.liquidate_positions()
        mock_send_position_messages == [{"symbol": "AAPL", "notional": 134.0}]


def test_sell_top_performers(liquidate, mock_trading_client):
    top_performers = pd.DataFrame({"symbol": ["AAPL", "MSFT"], "market_value": [500.0, 1000.0]})

    result = liquidate._sell_top_performers(
        top_performers, top_performers["market_value"].sum(), 150.0
    )
    expected_result = [{"symbol": "AAPL", "notional": 50}, {"symbol": "MSFT", "notional": 100}]
    assert result == expected_result


def test_sell_top_performers_with_zero_to_sell(liquidate, mock_trading_client):
    top_performers = pd.DataFrame({"symbol": ["AAPL", "MSFT"], "market_value": [500.0, 1000.0]})

    liquidate.trade.orders.market = MagicMock()

    result = liquidate._sell_top_performers(
        top_performers, top_performers["market_value"].sum(), 1.0
    )
    assert not result
    assert liquidate.trade.orders.market.call_count == 0


def test_send_liquidation_message():
    with patch("src.alpaca_daily_losers.global_functions.send_message") as mock_send_message:
        Liquidate._send_liquidation_message("Test Message")
        mock_send_message == "Test Message"
