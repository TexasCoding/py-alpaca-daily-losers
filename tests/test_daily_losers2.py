from unittest.mock import Mock, patch

import pytest

from alpaca_daily_losers.daily_losers import DailyLosers


@pytest.fixture
def daily_losers_instance():
    return DailyLosers()


def test_open_positions_no_tickers(daily_losers_instance):
    daily_losers_instance.alpaca = Mock()
    daily_losers_instance.alpaca.trading.account.get().cash = 1000

    with patch("alpaca_daily_losers.daily_losers.send_message") as mock_send_message:
        daily_losers_instance.open_positions([])

    mock_send_message.assert_called_once_with("No tickers to buy.")


def test_open_positions_buy_tickers(daily_losers_instance):
    tickers = ["AAPL", "GOOG", "MSFT"]

    cash = 1000
    daily_losers_instance.alpaca = Mock()
    daily_losers_instance.alpaca.trading.account.get().cash = cash

    with patch("alpaca_daily_losers.daily_losers.send_message") as mock_send_message:
        with patch(
            "alpaca_daily_losers.daily_losers.send_position_messages"
        ) as mock_send_position_messages:
            daily_losers_instance.open_positions(tickers)

    assert mock_send_message.call_count == 0
    mock_send_position_messages.assert_called_once()

    expected_positions = [
        {"symbol": "AAPL", "notional": round((cash / len(tickers)) - 1, 2)},
        {"symbol": "GOOG", "notional": round((cash / len(tickers)) - 1, 2)},
        {"symbol": "MSFT", "notional": round((cash / len(tickers)) - 1, 2)},
    ]

    mock_send_position_messages.assert_called_once_with(
        positions=expected_positions, pos_type="buy"
    )


def test_open_positions_buy_with_limit(daily_losers_instance):
    tickers = ["AAPL", "GOOG", "MSFT", "TSLA", "IBM", "ORCL", "SPOT", "UBER", "LYFT"]

    cash = 1000
    ticker_limit = 5

    daily_losers_instance.alpaca = Mock()
    daily_losers_instance.alpaca.trading.account.get().cash = cash

    with patch("alpaca_daily_losers.daily_losers.send_message") as mock_send_message:
        with patch(
            "alpaca_daily_losers.daily_losers.send_position_messages"
        ) as mock_send_position_messages:
            daily_losers_instance.open_positions(tickers, ticker_limit)

    assert mock_send_message.call_count == 0
    mock_send_position_messages.assert_called_once()

    expected_positions = [
        {"symbol": "AAPL", "notional": round((cash / ticker_limit) - 1, 2)},
        {"symbol": "GOOG", "notional": round((cash / ticker_limit) - 1, 2)},
        {"symbol": "MSFT", "notional": round((cash / ticker_limit) - 1, 2)},
        {"symbol": "TSLA", "notional": round((cash / ticker_limit) - 1, 2)},
        {"symbol": "IBM", "notional": round((cash / ticker_limit) - 1, 2)},
    ]

    mock_send_position_messages.assert_called_once_with(
        positions=expected_positions, pos_type="buy"
    )
