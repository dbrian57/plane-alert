from .adsb_client import Aircraft
from .earthquake_client import Earthquake


def describe_aircraft(ac: Aircraft) -> str:
    label = ac.flight or ac.registration or ac.icao24
    kind = f" ({ac.aircraft_type})" if ac.aircraft_type else ""
    altitude = f" at {ac.altitude_ft:,.0f} ft" if isinstance(ac.altitude_ft, (int, float)) else ""
    speed = f", {ac.ground_speed_kt:.0f} kt" if isinstance(ac.ground_speed_kt, (int, float)) else ""
    craft_word = "helicopter" if ac.is_helicopter else "aircraft"
    if ac.is_military:
        tag = f"\U0001F396️ Military {craft_word} "
    else:
        tag = "\U0001F681 " if ac.is_helicopter else "✈️ "
    emergency = f"\U0001F6A8 EMERGENCY ({ac.emergency}) — " if ac.emergency != "none" else ""
    return f"{emergency}{tag}{label}{kind}{altitude}{speed}, {ac.distance_miles:.2f} mi from home"


def describe_earthquake(eq: Earthquake) -> str:
    when = eq.time_utc.strftime("%H:%M UTC") if eq.time_utc else "unknown time"
    body = (
        f"\U0001F30E M{eq.magnitude:.1f} earthquake, {eq.depth_km:.0f} km deep, "
        f"{eq.distance_miles:.2f} mi from home — {eq.place} ({when})"
    )
    return f"{body}\n{eq.url}" if eq.url else body
