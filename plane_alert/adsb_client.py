import math
from dataclasses import dataclass

import requests

from .config import Config

EARTH_RADIUS_MILES = 3958.8
MILES_TO_NM = 0.868976
MILITARY_DB_FLAG = 1


@dataclass
class Aircraft:
    icao24: str
    flight: str
    registration: str
    aircraft_type: str
    lat: float
    lon: float
    altitude_ft: float | None
    ground_speed_kt: float | None
    is_military: bool
    distance_miles: float


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(a))


def fetch_nearby_aircraft(config: Config) -> list[Aircraft]:
    # Query the API for a wider radius than we care about (API's dist unit
    # has been reported as both sm and nm across API versions), then do the
    # real distance filtering ourselves with haversine below.
    query_radius_nm = math.ceil(config.radius_miles * MILES_TO_NM) + 5
    url = (
        f"https://{config.adsbx_host}/v2/lat/{config.home_lat}/lon/{config.home_lon}"
        f"/dist/{query_radius_nm}/"
    )
    headers = {
        "X-RapidAPI-Key": config.adsbx_api_key,
        "X-RapidAPI-Host": config.adsbx_host,
    }
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    payload = resp.json()

    aircraft: list[Aircraft] = []
    for ac in payload.get("ac", []):
        lat, lon = ac.get("lat"), ac.get("lon")
        if lat is None or lon is None:
            continue
        distance = _haversine_miles(config.home_lat, config.home_lon, lat, lon)
        if distance > config.radius_miles:
            continue
        db_flags = ac.get("dbFlags", 0) or 0
        aircraft.append(
            Aircraft(
                icao24=ac.get("hex", "unknown"),
                flight=(ac.get("flight") or "").strip(),
                registration=ac.get("r", ""),
                aircraft_type=ac.get("t", ""),
                lat=lat,
                lon=lon,
                altitude_ft=ac.get("alt_baro"),
                ground_speed_kt=ac.get("gs"),
                is_military=bool(db_flags & MILITARY_DB_FLAG),
                distance_miles=distance,
            )
        )
    return aircraft
