from twilio.rest import Client

from .adsb_client import Aircraft
from .config import Config


def _describe(ac: Aircraft) -> str:
    label = ac.flight or ac.registration or ac.icao24
    kind = f" ({ac.aircraft_type})" if ac.aircraft_type else ""
    altitude = f" at {ac.altitude_ft:,.0f} ft" if isinstance(ac.altitude_ft, (int, float)) else ""
    tag = "\U0001F396️ Military aircraft " if ac.is_military else "✈️ "
    return f"{tag}{label}{kind}{altitude}, {ac.distance_miles:.2f} mi from home"


def send_alert(config: Config, ac: Aircraft) -> None:
    client = Client(config.twilio_account_sid, config.twilio_auth_token)
    client.messages.create(
        body=_describe(ac),
        from_=config.twilio_from_number,
        to=config.twilio_to_number,
    )
