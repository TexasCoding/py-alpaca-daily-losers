import pytest
import logging
import pandas as pd
from unittest.mock import MagicMock, patch
from alpaca_daily_losers.close_positions import ClosePositions# assuming the refactored class is in close_positions.py

@pytest.fixture
def mock_trading_client():
    mock = MagicMock()
    return mock

@pytest.fixture
def mock_stock_client():
    mock = MagicMock()
    return mock

@pytest.fixture
def mock_logger():
    return logging.getLogger("test_logger")

@pytest.fixture
def close_positions(mock_trading_client, mock_stock_client, mock_logger):
    return ClosePositions(trading_client=mock_trading_client, stock_client=mock_stock_client, py_logger=mock_logger)

def test_sell_positions_from_criteria_no_sell_opportunities(close_positions, mock_trading_client):
    close_positions.get_stocks_to_sell = MagicMock(return_value=[])
    with patch('src.alpaca_daily_losers.global_functions.send_message') as mock_send_message:
        close_positions.sell_positions_from_criteria()
        mock_send_message == "No sell opportunities found."

def test_sell_positions_from_criteria_with_sell_opportunities(close_positions, mock_trading_client):
    # Mock get_stocks_to_sell to return some stocks
    stocks_to_sell = ["AAPL", "MSFT"]
    close_positions.get_stocks_to_sell = MagicMock(return_value=stocks_to_sell)
    # Mock trade positions return value
    mock_positions_df = pd.DataFrame({
        "symbol": ["AAPL", "MSFT", "Cash"],
        "qty": [10, 20, 0]
    })
    mock_trading_client.positions.get_all = MagicMock(return_value=mock_positions_df)
    
    with patch('alpaca_daily_losers.global_functions.send_position_messages') as mock_send_position_messages:
        close_positions.sell_positions_from_criteria()
        sold_positions = [
            {"symbol": "AAPL", "qty": 10},
            {"symbol": "MSFT", "qty": 20},
        ]
        mock_send_position_messages == sold_positions

@patch('alpaca_daily_losers.close_positions.get_ticker_data')
def test_get_stocks_to_sell(mock_get_ticker_data, close_positions, mock_trading_client):
    mock_positions_df = pd.DataFrame({
        "symbol": ["AAPL", "MSFT"],
        "profit_pct": [15.0, -10.0]
    })
    mock_trading_client.positions.get_all = MagicMock(return_value=mock_positions_df)

    mock_asset_history_df = pd.DataFrame({
        "symbol": ["AAPL", "MSFT"],
        "rsi14": [72, 65],
        "rsi30": [69, 60],
        "rsi50": [75, 64],
        "rsi200": [71, 63],
        "bbhi14": [1, 0],
        "bbhi30": [0, 0],
        "bbhi50": [1, 0],
        "bbhi200": [0, 0],
    })
    mock_get_ticker_data.return_value = mock_asset_history_df

    expected_stocks_to_sell = ["AAPL"]
    
    result = close_positions.get_stocks_to_sell()
    assert set(result) == set(expected_stocks_to_sell)

def test_sell_stocks_with_sell_list(close_positions, mock_trading_client):
    stocks_to_sell = ['AAPL', 'MSFT']
    
    mock_positions_df = pd.DataFrame({
        "symbol": ["AAPL", "MSFT", "Cash"],
        "qty": [10, 20, 0]
    })
    mock_trading_client.positions.get_all = MagicMock(return_value=mock_positions_df)
    mock_trading_client.positions.close = MagicMock()

    result = close_positions._sell_positions(stocks_to_sell, mock_positions_df)
    
    expected_result = [
        {"symbol": "AAPL", "qty": 10},
        {"symbol": "MSFT", "qty": 20}
    ]
    
    assert result == expected_result
    assert mock_trading_client.positions.close.call_count == 2
    mock_trading_client.positions.close.assert_any_call(symbol_or_id="AAPL", qty=10)
    mock_trading_client.positions.close.assert_any_call(symbol_or_id="MSFT", qty=20)

def test_sell_stocks_with_empty_list(close_positions, mock_trading_client):
    stocks_to_sell = []
    
    mock_positions_df = pd.DataFrame({
        "symbol": ["AAPL", "MSFT", "Cash"],
        "qty": [10, 20, 0]
    })
    
    result = close_positions._sell_positions(stocks_to_sell, mock_positions_df)
    
    expected_result = []
    
    assert result == expected_result
    assert mock_trading_client.positions.close.call_count == 0

@patch('alpaca_daily_losers.close_positions.get_ticker_data')
def test_get_stocks_to_sell_no_sell_criteria(mock_get_ticker_data, close_positions, mock_trading_client):
    mock_positions_df = pd.DataFrame({
        "symbol": ["AAPL", "MSFT"],
        "profit_pct": [5.0, 2.0]
    })
    mock_trading_client.positions.get_all = MagicMock(return_value=mock_positions_df)

    mock_asset_history_df = pd.DataFrame({
        "symbol": ["AAPL", "MSFT"],
        "rsi14": [50, 50],
        "rsi30": [50, 50],
        "rsi50": [50, 50],
        "rsi200": [50, 50],
        "bbhi14": [0, 0],
        "bbhi30": [0, 0],
        "bbhi50": [0, 0],
        "bbhi200": [0, 0],
    })
    mock_get_ticker_data.return_value = mock_asset_history_df

    result = close_positions.get_stocks_to_sell()
    assert result == []