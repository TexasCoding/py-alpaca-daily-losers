import os
from .slack import Slack

from dotenv import load_dotenv

load_dotenv()

production = os.getenv("PRODUCTION")
slack_username = os.getenv("SLACK_USERNAME")


def send_message(message):
    """
    Send a message to Slack
    :param message: str: message to send
    """
    slack = Slack()
    if production == "False":
        print(message)
    else:
        slack.send_message(
            channel="#app-development", message=message, username=slack_username
        )
