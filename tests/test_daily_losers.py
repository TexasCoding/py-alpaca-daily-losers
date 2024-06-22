import io
from unittest import mock

from alpaca_daily_losers.daily_losers import DailyLosers


class TestDailyLosers:

    def test_check_for_buy_opportunities_with_losers(self, mocker):
        mocker.patch.object(DailyLosers, "get_daily_losers", return_value=["AAPL", "GOOG"])
        mocker.patch.object(DailyLosers, "filter_tickers_with_news", return_value=["AAPL"])
        mocker.patch.object(DailyLosers, "open_positions")

        daily_losers = DailyLosers()
        daily_losers.check_for_buy_opportunities()

        daily_losers.open_positions.assert_called_once_with(tickers=["AAPL"], ticker_limit=4)

    def test_check_for_buy_opportunities_without_losers(self, mocker):
        mocker.patch.object(DailyLosers, "get_daily_losers", return_value=[])
        mocker.patch.object(DailyLosers, "filter_tickers_with_news", return_value=[])
        mocker.patch.object(DailyLosers, "open_positions")

        daily_losers = DailyLosers()
        with mock.patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            daily_losers.check_for_buy_opportunities()
            output = mock_stdout.getvalue().strip()

        assert output == "No buy opportunities found."
        daily_losers.open_positions.assert_not_called()

    def test_check_for_buy_opportunities_with_empty_tickers(self, mocker):
        mocker.patch.object(DailyLosers, "get_daily_losers", return_value=["AAPL", "GOOG"])
        mocker.patch.object(DailyLosers, "filter_tickers_with_news", return_value=[])
        mocker.patch.object(DailyLosers, "open_positions")

        daily_losers = DailyLosers()
        with mock.patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            daily_losers.check_for_buy_opportunities()
            output = mock_stdout.getvalue().strip()

        assert output == "No buy opportunities found."
