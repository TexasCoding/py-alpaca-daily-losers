import os

import pytest

from src.alpaca_daily_losers.global_functions import send_position_messages

production = os.environ.get("PRODUCTION", False)


def test_send_position_messages_sell(capsys):
    positions = [
        {"symbol": "AAPL", "qty": 10},
        {"symbol": "GOOGL", "qty": 5},
    ]
    pos_type = "sell"
    result = send_position_messages(positions, pos_type)
    printed_message = capsys.readouterr().out
    if not production:
        assert (
            printed_message
            == """Message: Successfully sold the following positions:
sold 10 shares of AAPL
sold 5 shares of GOOGL\n\n"""
        )
    assert True if result else False


def test_send_position_messages_buy(capsys):
    positions = [
        {"symbol": "AAPL", "notional": 1000},
        {"symbol": "GOOGL", "notional": 500},
    ]
    pos_type = "buy"
    result = send_position_messages(positions, pos_type)
    printed_message = capsys.readouterr().out
    if not production:
        assert (
            printed_message
            == """Message: Successfully bought the following positions:
$1000 of AAPL bought
$500 of GOOGL bought\n\n"""
        )
    assert True if result else False


def test_send_position_messages_liquidate(capsys):
    positions = [
        {"symbol": "AAPL", "notional": 10},
        {"symbol": "GOOGL", "notional": 5},
    ]
    pos_type = "liquidate"
    result = send_position_messages(positions, pos_type)
    printed_message = capsys.readouterr().out
    if not production:
        assert (
            printed_message
            == """Message: Successfully liquidated the following positions:
$10 of AAPL liquidated
$5 of GOOGL liquidated\n\n"""
        )
    assert True if result else False


def test_send_position_messages_invalid_type():
    positions = [
        {"symbol": "AAPL", "qty": 10},
        {"symbol": "GOOGL", "qty": 5},
    ]
    pos_type = "invalid"
    with pytest.raises(ValueError):
        send_position_messages(positions, pos_type)


def test_send_position_messages_no_positions():
    positions = []
    pos_type = "sell"
    result = send_position_messages(positions, pos_type)
    assert True if result else False
