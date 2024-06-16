from unittest.mock import MagicMock, patch

from alpaca_daily_losers.daily_losers import DailyLosers


def test_update_or_create_watchlist_update_success():
    with patch.object(DailyLosers, "__init__", lambda x: None):
        inst = DailyLosers()
        inst.alpaca = MagicMock()

        inst.update_or_create_watchlist("watchlist_1", ["AAPL", "GOOGL"])

        inst.alpaca.trading.watchlists.update.assert_called_once_with(
            watchlist_name="watchlist_1", symbols=["AAPL", "GOOGL"]
        )


def test_update_or_create_watchlist_update_fail_create_success():
    with patch.object(DailyLosers, "__init__", lambda x: None):
        inst = DailyLosers()
        inst.alpaca = MagicMock()
        inst.alpaca.trading.watchlists.update.side_effect = Exception("Update Exception")

        inst.update_or_create_watchlist("watchlist_2", ["AAPL", "MSFT"])

        inst.alpaca.trading.watchlists.update.assert_called_once_with(
            watchlist_name="watchlist_2", symbols=["AAPL", "MSFT"]
        )
        inst.alpaca.trading.watchlists.create.assert_called_once_with(
            name="watchlist_2", symbols=["AAPL", "MSFT"]
        )
