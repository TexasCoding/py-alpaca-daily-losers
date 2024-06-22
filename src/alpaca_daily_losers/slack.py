import os

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class Slack:
    """
    A class to send messages to a Slack channel.

    Attributes:
        slack_token (str): Token for authenticating with the Slack API.
        client (WebClient): Slack WebClient instance for making API calls.
    """

    def __init__(self, slack_token: str = None):
        """
        Initializes the Slack class with a Slack token.

        Args:
            slack_token (str, optional): Token for Slack API. Loads from
            environment variable if not provided.
        """
        self.slack_token = slack_token or os.environ.get("SLACK_ACCESS_TOKEN")
        self.client = WebClient(token=self.slack_token) if self.slack_token else None

    def send_message(self, channel: str, text: str, username: str = None):
        """
        Sends a message to the specified Slack channel.

        Args:
            channel (str): Slack channel ID or name.
            text (str): Message text to send.
            username (str, optional): Username to send the message as. Defaults to None.

        Returns:
            dict: Response from the Slack API.

        Raises:
            ValueError: If the Slack token is not set or if the message fails to send.
        """
        if not self.slack_token:
            print(f"Slack token is not provided. Message: {text}")
            return {"ok": False, "error": "Slack token is not provided"}

        if not self.client:
            raise ValueError("Slack client is not initialized.")

        try:
            response = self.client.chat_postMessage(channel=channel, text=text, username=username)
            return response

        except SlackApiError as e:
            print(f"Error sending message: {e.response['error']}")
            return {"ok": False, "error": e.response["error"]}
