import pytest

from src.alpaca_daily_losers import openai


def test_chat_single_message():
    api = openai.OpenAIAPI()
    msgs = [{"role": "system", "content": "You are a helpful assistant."}]
    response = api.chat(msgs)
    assert isinstance(response, object), "Response is not dictionary"
    # assert "choices" in response, "No choices in response"
    assert len(response.choices) > 0, "No content in response"


def test_chat_multi_message():
    api = openai.OpenAIAPI()
    msgs = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What's the weather outside?"},
    ]
    response = api.chat(msgs)
    assert isinstance(response, object), "Response is not dictionary"
    # assert "choices" in response, "No choices in response"
    assert len(response.choices) > 0, "No content in response"


def test_chat_empty_message():
    api = openai.OpenAIAPI()
    msgs = []
    with pytest.raises(Exception):
        api.chat(msgs)


def test_chat_non_list_message():
    api = openai.OpenAIAPI()
    msgs = "You are a helpful assistant."
    with pytest.raises(Exception):
        api.chat(msgs)
