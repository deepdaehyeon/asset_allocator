import os

import slack_sdk


class Messenger:
    """Slack messenger class."""

    def __init__(self, acc_no: str):
        """initialize."""
        self.acc_no = acc_no

    def send_msg(self, msg: str, mention: bool = True) -> None:
        """Send message to slack."""
        client = slack_sdk.WebClient(token=os.getenv("SLACK_TOKEN"))
        user_id = "김대현"
        slack_msg = f'<@{user_id}> {msg} on {self.acc_no}' if mention else msg
        response = client.chat_postMessage(
            channel="C02SGLQV529",
            text=slack_msg,
        )
        print(response)
