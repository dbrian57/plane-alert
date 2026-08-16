import logging
import time

from .adsb_client import fetch_nearby_aircraft
from .config import Config
from .notifier import send_alert
from .state import NotificationState

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("plane_alert")


def run() -> None:
    config = Config()
    state = NotificationState(config.db_path)
    log.info(
        "watching %.4f,%.4f within %.2f mi, polling every %ss",
        config.home_lat, config.home_lon, config.radius_miles, config.poll_interval_seconds,
    )

    while True:
        try:
            aircraft = fetch_nearby_aircraft(config)
            for ac in aircraft:
                if not state.should_notify(ac.icao24, config.cooldown_minutes):
                    continue
                log.info("alerting on %s (%s), %.2f mi", ac.icao24, ac.flight, ac.distance_miles)
                send_alert(config, ac)
                state.record_notified(ac.icao24)
        except Exception:
            log.exception("poll cycle failed")

        time.sleep(config.poll_interval_seconds)


if __name__ == "__main__":
    run()
