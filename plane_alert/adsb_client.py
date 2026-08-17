import math
from dataclasses import dataclass

import requests

from .config import Config
from .geo import haversine_miles

MILES_TO_NM = 0.868976
MILITARY_DB_FLAG = 1
ROTORCRAFT_CATEGORY = "A7"


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
    is_helicopter: bool
    emergency: str
    distance_miles: float


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
        distance = haversine_miles(config.home_lat, config.home_lon, lat, lon)
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
                is_helicopter=ac.get("category") == ROTORCRAFT_CATEGORY,
                emergency=ac.get("emergency") or "none",
                distance_miles=distance,
            )
        )
    return aircraft
