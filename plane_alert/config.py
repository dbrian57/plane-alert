import os


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"missing required env var: {name}")
    return value


def _float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    return float(raw) if raw else default


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    return int(raw) if raw else default


class Config:
    def __init__(self) -> None:
        self.home_lat = float(_require("HOME_LAT"))
        self.home_lon = float(_require("HOME_LON"))
        self.radius_miles = _float("RADIUS_MILES", 1.0)
        self.poll_interval_seconds = _int("POLL_INTERVAL_SECONDS", 15)
        self.cooldown_minutes = _int("COOLDOWN_MINUTES", 20)

        self.adsbx_api_key = _require("ADSBX_API_KEY")
        self.adsbx_host = os.environ.get("ADSBX_HOST", "adsbexchange-com1.p.rapidapi.com")

        self.twilio_account_sid = _require("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = _require("TWILIO_AUTH_TOKEN")
        self.twilio_from_number = _require("TWILIO_FROM_NUMBER")
        self.twilio_to_number = _require("TWILIO_TO_NUMBER")

        self.db_path = os.environ.get("DB_PATH", "/data/plane_alert.db")
