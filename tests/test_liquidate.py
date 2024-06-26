import pandas as pd

from src.alpaca_daily_losers.liquidate import Liquidate


def test_calculate_cash_needed():
    cash_row = pd.DataFrame({"market_value": [200.0]})

    # Test with a total_holdings value that would result in a positive cash direction after fee
    assert Liquidate.calculate_cash_needed(3000.0, cash_row) == 100.0

    # Test with a negative cash direction in cash_row and total_holdings being 2000.0
    negative_cash_row = pd.DataFrame({"market_value": [-200.0]})
    assert Liquidate.calculate_cash_needed(2000.0, negative_cash_row) == 400.00
    assert Liquidate.calculate_cash_needed(0.0, cash_row) == -200.00


def test_liquidates_positions_when_cash_less_than_10_percent_with_sold_positions_with_empty(
    mocker,
):
    # Mocking dependencies
    mock_trade = mocker.Mock()
    mock_logger = mocker.Mock()
    # mock_send_message = mocker.patch('alpaca_daily_losers.global_functions.send_message')
    mock_send_position_messages = mocker.patch(
        "alpaca_daily_losers.global_functions.send_position_messages"
    )

    # Mocking current positions
    current_positions = pd.DataFrame(
        {
            "symbol": ["AAPL", "GOOGL", "Cash"],
            "market_value": [5000, 3000, 500],
            "profit_pct": [2.0, 0.4, 0],
        }
    )
    mock_trade.positions.get_all.return_value = current_positions

    liquidate = Liquidate(trading_client=mock_trade, py_logger=mock_logger)
    liquidate.liquidate_positions()

    # Assertions
    assert mock_trade.orders.market.call_count == 1
    assert (
        mock_send_position_messages.call_args is None
        or mock_send_position_messages.call_args[0][0] == []
    )
