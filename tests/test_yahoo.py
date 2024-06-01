import pytest
import yfinance as yf

from alpaca_daily_losers.yahoo import Yahoo


@pytest.fixture
def yahoo():
    return Yahoo()


def test_returns_ticker_object_for_valid_symbol(yahoo):
    ticker_symbol = "AAPL"
    ticker_object = yahoo.get_ticker(ticker_symbol)
    assert isinstance(ticker_object, yf.Ticker)


def test_handles_empty_string_as_ticker_symbol(yahoo):
    ticker_symbol = ""
    ticker_object = yahoo.get_ticker(ticker_symbol)
    assert isinstance(ticker_object, yf.Ticker)


def test_create_news_dict_correct_extraction_from_valid_input(yahoo):
    url_dict = {"title": "Breaking News", "link": "https://example.com"}
    news_dict = yahoo.create_news_dict(url_dict)
    assert news_dict == {"title": "Breaking News", "url": "https://example.com"}


def test_create_news_dict_missing_title_key(yahoo):
    url_dict = {"link": "https://example.com"}
    with pytest.raises(KeyError):
        yahoo.create_news_dict(url_dict)


def test_retrieves_news_data_for_valid_ticker(yahoo):
    news_data = yahoo.get_news_data("AAPL")
    assert isinstance(news_data, list)
    assert len(news_data) > 0
    assert "title" in news_data[0]
    assert "url" in news_data[0]


def test_retrieves_news_data_for_invalid_ticker(yahoo):
    news_data = yahoo.get_news_data("FAKE_TICKER")
    assert isinstance(news_data, list)
    assert len(news_data) > 0
    assert "title" in news_data[0]
    assert "url" in news_data[0]


def test_get_articles_returns_list(yahoo):
    articles = yahoo.get_articles("AAPL")
    assert isinstance(articles, list)


def test_get_articles_returns_limit_number_of_articles(yahoo):
    articles = yahoo.get_articles("AAPL", limit=3)
    assert len(articles) == 3


def test_get_articles_contains_required_keys(yahoo):
    articles = yahoo.get_articles("AAPL")
    for article in articles:
        assert "symbol" in article
        assert "title" in article
        assert "content" in article


def test_get_articles_content_is_truncated(yahoo):
    articles = yahoo.get_articles("AAPL")
    for article in articles:
        assert len(article["content"]) <= 9000


def test_get_articles_content_length_limit(yahoo):
    articles = yahoo.get_articles("AAPL")
    for article in articles:
        assert len(article["content"]) <= 10000
