import logging

from py_alpaca_api.trading.account import Account


class Statistics:
    def __init__(self, account: Account, py_logger: logging.Logger) -> None:
        self.account = account
        self.py_logger = py_logger
