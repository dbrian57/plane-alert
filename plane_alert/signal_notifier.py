import requests

from .config import Config


def send_alert(config: Config, message: str) -> None:
    resp = requests.post(
        f"{config.signal_rest_api_url}/v2/send",
        json={
            "message": message,
            "number": config.signal_from_number,
            "recipients": [config.signal_to_number],
        },
        timeout=10,
    )
    resp.raise_for_status()
