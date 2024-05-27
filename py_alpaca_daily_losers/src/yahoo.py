import yfinance as yf
import time
import logging

logger = logging.getLogger('yfinance')
logger.disabled = True
logger.propagate = False


class Yahoo:
    def __init__(self):
        pass

    @staticmethod
    def get_ticker(ticker):
        return yf.Ticker(ticker)

    def get_recommendations(self, ticker):
        return self.get_ticker(ticker).recommendations

    def get_sentiment(self, ticker):
        time.sleep(1)
        recommendations = self.get_ticker(ticker).recommendations
        if recommendations.empty:
            return "NEUTRAL"
        buy = (
            recommendations["strongBuy"].sum()
            + recommendations["buy"].sum()
        )
        sell = (
            recommendations["strongSell"].sum()
            + recommendations["sell"].sum()
            + recommendations["hold"].sum()
        )
        return 'BULLISH' if (buy / (buy + sell)) > 0.7 else 'BEARISH'
