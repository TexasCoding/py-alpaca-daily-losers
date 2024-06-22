from unittest.mock import MagicMock

import pytest
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from alpaca_daily_losers.slack import Slack


@pytest.fixture
def slack_instance():
    return Slack(slack_token="xoxb-fake-token")


def test_slack_initialization_with_token():
    slack = Slack(slack_token="xoxb-test-token")
    assert slack.slack_token == "xoxb-test-token"
    assert isinstance(slack.client, WebClient)


def test_slack_initialization_without_token(monkeypatch):
    monkeypatch.setenv("SLACK_ACCESS_TOKEN", "xoxb-env-token")
    slack = Slack()
    assert slack.slack_token == "xoxb-env-token"
    assert isinstance(slack.client, WebClient)


def test_send_message_success(slack_instance):
    response_data = {"ok": True, "message": {"text": "Hello world!"}}
    slack_instance.client.chat_postMessage = MagicMock(return_value=response_data)
    response = slack_instance.send_message(channel="#general", text="Hello world!")
    assert True if response["ok"] else False
    assert response["message"]["text"] == "Hello world!"


def test_send_message_no_token():
    slack = Slack(slack_token="asd")
    response = slack.send_message(channel="#general", text="Hello world!")
    assert True if not response["ok"] else False
    assert response["error"] == "invalid_auth"


def test_send_message_exception(slack_instance):
    slack_instance.client.chat_postMessage = MagicMock(
        side_effect=SlackApiError(message="error", response={"error": "invalid_auth"})
    )
    response = slack_instance.send_message(channel="#general", text="Hello world!")
    assert True if not response["ok"] else False
    assert response["error"] == "invalid_auth"
