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

        self.earthquake_radius_miles = _float("EARTHQUAKE_RADIUS_MILES", 50.0)
        self.earthquake_min_magnitude = _float("EARTHQUAKE_MIN_MAGNITUDE", 2.0)
        self.earthquake_lookback_hours = _int("EARTHQUAKE_LOOKBACK_HOURS", 24)
        self.earthquake_poll_interval_seconds = _int("EARTHQUAKE_POLL_INTERVAL_SECONDS", 300)
        # Effectively "notify once per quake" — dedup is keyed by USGS event
        # id, so this just guards against reprocessing the same id sooner
        # than a magnitude revision would plausibly land.
        self.earthquake_cooldown_minutes = _int("EARTHQUAKE_COOLDOWN_MINUTES", 10080)

        self.signal_rest_api_url = os.environ.get("SIGNAL_REST_API_URL", "http://localhost:8080")
        self.signal_from_number = _require("SIGNAL_FROM_NUMBER")
        self.signal_to_number = _require("SIGNAL_TO_NUMBER")

        # Mothballed alongside notifier.py — not required unless you switch
        # main.py back to Twilio.
        self.twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        self.twilio_from_number = os.environ.get("TWILIO_FROM_NUMBER")
        self.twilio_to_number = os.environ.get("TWILIO_TO_NUMBER")

        self.db_path = os.environ.get("DB_PATH", "/data/plane_alert.db")
