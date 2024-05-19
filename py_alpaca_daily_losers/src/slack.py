import os

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from dotenv import load_dotenv

load_dotenv()

# Load environment variables
production = os.getenv("PRODUCTION")
slack_token = os.getenv("SLACK_ACCESS_TOKEN")


class Slack:
    """
    A class to send messages to a Slack channel
    attributes: slack_workspace_token
    """

    def __init__(self):
        self.slack_workspace_token = slack_token

    ########################################################
    # Define the send_message function
    ########################################################
    def send_message(self, channel, message, username):
        """
        Send a message to the Slack channel
        :param channel: Slack channel
        :param message: Message to send
        :param username: Username to send the message as
        If the slack_workspace_token is not set, print the message instead of sending it to Slack
        """
        # Create a WebClient object

        if not self.slack_workspace_token:
            print(message)
            return

        client = WebClient(token=self.slack_workspace_token)

        try:
            response = client.chat_postMessage(
                channel=channel, text=f"{message}", username=username
            )
            assert response["message"]["text"] == f"{message}"
        except SlackApiError as e:
            # You will get a SlackApiError if "ok" is False
            assert e.response["ok"] is False
            assert e.response[
                "error"
            ]  # str like 'invalid_auth', 'channel_not_found'
            print(f"Got an error: {e.response['error']}")
            # Also receive a corresponding status_code
            assert isinstance(e.response.status_code, int)
            print(f"Received a response status_code: {e.response.status_code}")
        # else:
        #     print(f"Message sent successfully to {channel}")
