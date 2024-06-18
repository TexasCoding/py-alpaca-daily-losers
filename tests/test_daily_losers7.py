# from alpaca_daily_losers.daily_losers import DailyLosers


# class MockAPI:
#     def __init__(self, response):
#         self.response = response

#     def get_sentiment_analysis(self, title, symbol, article):
#         return self.response


# def test_filter_tickers_with_news_negative_sentiment():
#     # Setup
#     api_response = "BEARISH"
#     mock_openai = MockAPI(api_response)
#     mock_alpaca = MockAPI(["Article 1", "Article 2", "Article 3"])
#     tickers = ["abc", "def", "ghi"]
#     dl = DailyLosers()
#     dl.openai = mock_openai
#     dl.alpaca = mock_alpaca

#     # Run
#     result = dl.filter_tickers_with_news(tickers, article_limit=3, filter_ticker_limit=3)

#     # Assert
#     assert len(result) == 0


# def test_filter_tickers_with_news_empty_articles():
#     # Setup
#     mock_alpaca = MockAPI([])
#     api_response = "BULLISH"
#     mock_openai = MockAPI(api_response)
#     tickers = ["abc", "def", "ghi"]
#     dl = DailyLosers()
#     dl.openai = mock_openai
#     dl.alpaca = mock_alpaca

#     # Run
#     result = dl.filter_tickers_with_news(tickers)

#     # Assert
#     assert len(result) == 0
