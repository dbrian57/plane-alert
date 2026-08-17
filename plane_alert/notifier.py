from twilio.rest import Client

from .config import Config

# Mothballed: A2P 10DLC campaign registration was rejected. Kept working in
# case it's worth revisiting later; main.py currently wires up
# signal_notifier instead.


def send_alert(config: Config, message: str) -> None:
    client = Client(config.twilio_account_sid, config.twilio_auth_token)
    client.messages.create(
        body=message,
        from_=config.twilio_from_number,
        to=config.twilio_to_number,
    )
