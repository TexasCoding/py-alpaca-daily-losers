# File: tests_daily_losers.py
import pytest
from py_alpaca_api.src.position import Position

from src.alpaca_daily_losers.daily_losers import DailyLosers


class TestDailyLosers:
    @pytest.fixture
    def daily_losers_obj(self):
        return DailyLosers()

    def test_sell_positions_from_criteria_no_sell_opportunities(
        self, daily_losers_obj, capsys, mocker
    ):
        mocker.patch.object(DailyLosers, "get_sell_opportunities", return_value=[])
        daily_losers_obj.sell_positions_from_criteria()
        captured = capsys.readouterr()
        assert "No sell opportunities found." in captured.out

    def test_sell_positions_from_criteria_sell_opportunities_present(
        self, daily_losers_obj, mocker
    ):
        mocker.patch.object(DailyLosers, "get_sell_opportunities", return_value=["AAPL"])
        mocker.patch.object(Position, "get_all", return_value=["AAPL"])
        mocker.patch.object(DailyLosers, "_sell_positions", return_value=["AAPL"])
        mocker.patch.object(DailyLosers, "_send_position_messages")
        daily_losers_obj.sell_positions_from_criteria()
        DailyLosers._sell_positions.assert_called_with(["AAPL"], ["AAPL"])
        DailyLosers._send_position_messages.assert_called_with(["AAPL"], "sell")

    def test_sell_positions_from_criteria_no_current_positions(self, daily_losers_obj, mocker):
        mocker.patch.object(DailyLosers, "get_sell_opportunities", return_value=["AAPL"])
        mocker.patch.object(Position, "get_all", return_value=[])
        mocker.patch.object(DailyLosers, "_sell_positions", return_value=[])
        mocker.patch.object(DailyLosers, "_send_position_messages")
        daily_losers_obj.sell_positions_from_criteria()
        DailyLosers._sell_positions.assert_called_with(["AAPL"], [])
