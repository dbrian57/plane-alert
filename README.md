# plane-alert

Texts you whenever an aircraft flies within a configurable radius of your
house, using ADS-B Exchange for positions and Twilio for SMS. Flags military
aircraft (via ADS-B Exchange's `dbFlags` bit) in the message text.

## How it works

`plane_alert/main.py` polls ADS-B Exchange every `POLL_INTERVAL_SECONDS`,
filters returned aircraft to those within `RADIUS_MILES` of `HOME_LAT`/`HOME_LON`
(haversine distance, computed locally — not left to the API's own radius
filter), and texts you about any aircraft it hasn't already alerted on in the
last `COOLDOWN_MINUTES`. Cooldown state lives in a SQLite file at `DB_PATH`.

## Setup

1. Subscribe to the [ADS-B Exchange API on RapidAPI](https://rapidapi.com/adsbx/api/adsbexchange-com1)
   and grab your API key. **Before deploying**, hit the endpoint once by hand
   (RapidAPI's console lets you do this) and confirm the response still has
   `hex`, `flight`, `r`, `t`, `lat`, `lon`, `alt_baro`, `gs`, and `dbFlags` on
   each object in `ac` — ADS-B Exchange has been migrating v2 → v3 and field
   names can shift.
2. In Twilio, buy/confirm a phone number capable of sending SMS.
3. Copy `.env.example` to `.env` and fill in your coordinates, ADS-B Exchange
   key, and Twilio credentials.

## Run locally

```sh
cd plane-alert
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export $(grep -v '^#' .env | xargs)   # or use python-dotenv / direnv
python -m plane_alert.main
```

## Deploy to DigitalOcean App Platform

1. Push this directory to a GitHub repo (App Platform deploys from git or a
   registry image — the `dockerfile_path` in `app.yaml` assumes git).
2. Edit `app.yaml`: replace every `REPLACE_ME`, and set the `SECRET` envs
   (`ADSBX_API_KEY`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`) via
   `doctl apps create --spec app.yaml` — doctl will prompt for secret values
   rather than storing them in the file, or you can set them after creation
   in the App Platform dashboard instead of committing them.
3. Create the app:
   ```sh
   doctl apps create --spec app.yaml
   ```
4. Watch logs:
   ```sh
   doctl apps logs <app-id> poller --follow
   ```

**Note on state persistence**: App Platform workers have ephemeral disks — a
redeploy or restart wipes `DB_PATH`, so you may get one duplicate text per
aircraft still overhead right after a restart. Not worth solving for a
single-house hobby app; if it bugs you, point `DB_PATH` at a mounted DO
Volume or swap SQLite for a tiny managed DB.

## Legal pages for A2P 10DLC registration

Twilio's A2P 10DLC campaign registration requires a hosted privacy policy and
terms of service URL. `docs/privacy.html`, `docs/terms.html`, and
`docs/index.html` cover the minimum required disclosures (no sharing of
phone numbers, message frequency, "message and data rates may apply",
STOP/HELP opt-out). Before publishing:

1. Replace `[YOUR CONTACT EMAIL HERE]` in both `privacy.html` and
   `terms.html` with an email address you're fine making public.
2. Push this repo to GitHub, then enable **GitHub Pages** under
   Settings → Pages → set source to the `docs/` folder on your default
   branch.
3. GitHub will publish at `https://<username>.github.io/<repo>/` — use
   `.../privacy.html` and `.../terms.html` as the URLs in Twilio's campaign
   registration form.

## Config reference

| Env var | Purpose | Default |
|---|---|---|
| `HOME_LAT` / `HOME_LON` | Your coordinates | required |
| `RADIUS_MILES` | Alert radius | `1.0` |
| `POLL_INTERVAL_SECONDS` | ADS-B Exchange poll frequency | `15` |
| `COOLDOWN_MINUTES` | Minimum time between repeat alerts for the same aircraft | `20` |
| `ADSBX_API_KEY` | RapidAPI key for ADS-B Exchange | required |
| `TWILIO_*` | Twilio account SID / auth token / from / to numbers | required |
| `DB_PATH` | SQLite file for cooldown state | `/data/plane_alert.db` |

## Caveats

- Military aircraft not transmitting ADS-B won't show up at all — this is a
  transponder-level limitation, not something the app or API can work around.
- ADS-B Exchange's lat/lon/dist endpoint is deprecated in favor of v3; this
  still targets v2 for simplicity but the field-name caveat above applies.
