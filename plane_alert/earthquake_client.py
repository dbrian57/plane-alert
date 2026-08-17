from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import requests

from .config import Config
from .geo import haversine_miles

USGS_QUERY_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
KM_TO_MILES = 0.621371


@dataclass
class Earthquake:
    event_id: str
    magnitude: float
    place: str
    depth_km: float
    time_utc: datetime | None
    lat: float
    lon: float
    url: str
    distance_miles: float


def fetch_recent_earthquakes(config: Config) -> list[Earthquake]:
    starttime = datetime.now(timezone.utc) - timedelta(hours=config.earthquake_lookback_hours)
    resp = requests.get(
        USGS_QUERY_URL,
        params={
            "format": "geojson",
            "latitude": config.home_lat,
            "longitude": config.home_lon,
            "maxradiuskm": config.earthquake_radius_miles / KM_TO_MILES,
            "minmagnitude": config.earthquake_min_magnitude,
            "starttime": starttime.strftime("%Y-%m-%dT%H:%M:%S"),
        },
        timeout=10,
    )
    resp.raise_for_status()
    payload = resp.json()

    earthquakes: list[Earthquake] = []
    for feature in payload.get("features", []):
        props = feature.get("properties", {})
        coords = feature.get("geometry", {}).get("coordinates")
        if not coords or len(coords) < 3:
            continue
        lon, lat, depth_km = coords[0], coords[1], coords[2]
        distance = haversine_miles(config.home_lat, config.home_lon, lat, lon)
        if distance > config.earthquake_radius_miles:
            continue
        time_ms = props.get("time")
        earthquakes.append(
            Earthquake(
                event_id=feature.get("id", "unknown"),
                magnitude=props.get("mag") or 0.0,
                place=props.get("place") or "unknown location",
                depth_km=depth_km,
                time_utc=datetime.fromtimestamp(time_ms / 1000, tz=timezone.utc) if time_ms else None,
                lat=lat,
                lon=lon,
                url=props.get("url", ""),
                distance_miles=distance,
            )
        )
    return earthquakes
