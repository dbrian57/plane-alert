import logging
import time

from .adsb_client import fetch_nearby_aircraft
from .config import Config
from .earthquake_client import fetch_recent_earthquakes
from .message import describe_aircraft, describe_earthquake
from .signal_notifier import send_alert
from .state import NotificationState

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("plane_alert")


def run() -> None:
    config = Config()
    state = NotificationState(config.db_path)
    log.info(
        "watching %.4f,%.4f: aircraft within %.2f mi (poll %ss), earthquakes within %.0f mi M%.1f+ (poll %ss)",
        config.home_lat, config.home_lon,
        config.radius_miles, config.poll_interval_seconds,
        config.earthquake_radius_miles, config.earthquake_min_magnitude, config.earthquake_poll_interval_seconds,
    )

    next_earthquake_poll = 0.0

    while True:
        try:
            aircraft = fetch_nearby_aircraft(config)
            for ac in aircraft:
                if not state.should_notify(ac.icao24, config.cooldown_minutes):
                    continue
                log.info("alerting on %s (%s), %.2f mi", ac.icao24, ac.flight, ac.distance_miles)
                send_alert(config, describe_aircraft(ac))
                state.record_notified(ac.icao24)

            now = time.monotonic()
            if now >= next_earthquake_poll:
                for eq in fetch_recent_earthquakes(config):
                    if not state.should_notify(eq.event_id, config.earthquake_cooldown_minutes):
                        continue
                    log.info("alerting on earthquake %s M%.1f, %.2f mi", eq.event_id, eq.magnitude, eq.distance_miles)
                    send_alert(config, describe_earthquake(eq))
                    state.record_notified(eq.event_id)
                next_earthquake_poll = now + config.earthquake_poll_interval_seconds
        except Exception:
            log.exception("poll cycle failed")

        time.sleep(config.poll_interval_seconds)


if __name__ == "__main__":
    run()
