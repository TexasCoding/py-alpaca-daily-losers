from alpaca_daily_losers.openai import OpenAIAPI


def test_chat_returns_response():
    api = OpenAIAPI()
    msgs = [{"content": "Hello", "role": "user"}]
    response = api.chat(msgs)
    assert response is not None
