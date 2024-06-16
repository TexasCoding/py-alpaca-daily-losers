import pandas as pd

import alpaca_daily_losers
from alpaca_daily_losers.close_positions import ClosePositions


class TestSellPositionsFromCriteria:
    def test_sell_positions_from_criteria_no_positions(self, mocker):
        mocker.patch("alpaca_daily_losers.close_positions.send_message")
        trade_mock = mocker.Mock()
        stock_client_mock = mocker.Mock()
        py_logger_mock = mocker.Mock()
        trade_mock.positions.get_all.return_value = []
        instance = ClosePositions(
            trade_mock, stock_client=stock_client_mock, py_logger=py_logger_mock
        )
        instance.get_stocks_to_sell = mocker.Mock(return_value=[])

        instance.sell_positions_from_criteria()

        send_message_mock = alpaca_daily_losers.close_positions.send_message
        send_message_mock.assert_called_once_with("No sell opportunities found.")

    def test_sell_positions_from_criteria_success(self, mocker):
        trade_mock = mocker.Mock()
        stock_client_mock = mocker.Mock()
        py_logger_mock = mocker.Mock()
        positions_mock = [mocker.Mock(), mocker.Mock()]
        trade_mock.positions.get_all.return_value = positions_mock
        instance = ClosePositions(
            trade_mock, stock_client=stock_client_mock, py_logger=py_logger_mock
        )
        stocks_to_sell_mock = [mocker.Mock(), mocker.Mock()]
        instance.get_stocks_to_sell = mocker.Mock(return_value=stocks_to_sell_mock)
        instance._sell_positions = mocker.Mock(return_value=positions_mock)
        send_position_messages_mock = mocker.patch(
            "alpaca_daily_losers.close_positions.send_position_messages"
        )

        instance.sell_positions_from_criteria()

        instance._sell_positions.assert_called_once_with(stocks_to_sell_mock, positions_mock)
        send_position_messages_mock.assert_called_once_with(positions_mock, "sell")


class TestGetStocksToSell:
    def test_get_stocks_to_sell_no_positions(self, mocker):
        trade_mock = mocker.Mock()
        stock_client_mock = mocker.Mock()
        py_logger_mock = mocker.Mock()
        trade_mock.positions.get_all.return_value = pd.DataFrame({"symbol": []})
        instance = ClosePositions(
            trade_mock, stock_client=stock_client_mock, py_logger=py_logger_mock
        )

        result = instance.get_stocks_to_sell()

        assert result == []

    def test_get_stocks_to_sell_only_cash_position(self, mocker):
        trade_mock = mocker.Mock()
        stock_client_mock = mocker.Mock()
        py_logger_mock = mocker.Mock()
        trade_mock.positions.get_all.return_value = pd.DataFrame({"symbol": ["Cash"]})
        instance = ClosePositions(
            trade_mock, stock_client=stock_client_mock, py_logger=py_logger_mock
        )

        result = instance.get_stocks_to_sell()

        assert result == []

    def test_get_stocks_to_sell_rsi_and_bbhi_criteria(self, mocker):
        trade_mock = mocker.Mock()
        stock_client_mock = mocker.Mock()
        py_logger_mock = mocker.Mock()
        positions_df = pd.DataFrame({"symbol": ["AAPL", "GOOG"], "profit_pct": [5.0, -3.0]})
        trade_mock.positions.get_all.return_value = positions_df
        rsi_df = pd.DataFrame(
            {
                "symbol": ["AAPL", "GOOG"],
                "rsi14": [75, 60],
                "rsi30": [80, 65],
                "rsi50": [70, 55],
                "rsi200": [65, 50],
                "bbhi14": [0, 1],
                "bbhi30": [0, 0],
                "bbhi50": [1, 0],
                "bbhi200": [0, 0],
            }
        )
        mocker.patch("alpaca_daily_losers.close_positions.get_ticker_data", return_value=rsi_df)
        instance = ClosePositions(
            trade_mock, stock_client=stock_client_mock, py_logger=py_logger_mock
        )

        result = instance.get_stocks_to_sell()

        assert set(result) == set(["AAPL", "GOOG"])
