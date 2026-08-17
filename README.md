# plane-alert

Texts you whenever an aircraft flies within a configurable radius of your
house, or an earthquake happens nearby, using ADS-B Exchange and the USGS
Earthquake API for data and Signal for messaging. Flags military aircraft
(via ADS-B Exchange's `dbFlags` bit) and helicopters (via its `category`
field) in the message text.

Twilio SMS is mothballed (see [Mothballed: Twilio SMS](#mothballed-twilio-sms))
after its A2P 10DLC campaign registration was rejected — Signal has no
equivalent carrier-vetting process.

## How it works

`plane_alert/main.py` runs two independent checks on one loop:

- **Aircraft**: polls ADS-B Exchange every `POLL_INTERVAL_SECONDS`, filters
  returned aircraft to those within `RADIUS_MILES` of `HOME_LAT`/`HOME_LON`
  (haversine distance, computed locally — not left to the API's own radius
  filter), and alerts on any aircraft it hasn't already alerted on in the
  last `COOLDOWN_MINUTES`.
- **Earthquakes**: polls the free, keyless [USGS Earthquake API](https://earthquake.usgs.gov/fdsnws/event/1/)
  every `EARTHQUAKE_POLL_INTERVAL_SECONDS` (much less frequently than
  aircraft — quakes don't move miles in 15 seconds) for events within
  `EARTHQUAKE_RADIUS_MILES` and above `EARTHQUAKE_MIN_MAGNITUDE`, and alerts
  once per USGS event id (dedup'd the same way as aircraft, just with an
  effectively-permanent cooldown — see config table).

Both share one SQLite dedup table (`DB_PATH`) keyed by an opaque entity id
(ICAO hex for aircraft, USGS event id for earthquakes).

## Setup

1. Subscribe to the [ADS-B Exchange API on RapidAPI](https://rapidapi.com/adsbx/api/adsbexchange-com1)
   and grab your API key. **Before deploying**, hit the endpoint once by hand
   (RapidAPI's console lets you do this) and confirm the response still has
   `hex`, `flight`, `r`, `t`, `lat`, `lon`, `alt_baro`, `gs`, and `dbFlags` on
   each object in `ac` — ADS-B Exchange has been migrating v2 → v3 and field
   names can shift.
2. Run [signal-cli-rest-api](https://github.com/bbernhard/signal-cli-rest-api)
   locally to register the sending identity:
   ```sh
   docker compose up -d signal-api
   ```
   Then open `http://localhost:8080/v1/qrcodelink?device_name=plane-alert`
   and scan the QR code from your phone's Signal app (Settings → Linked
   devices → +). This links the container as a secondary device on your own
   Signal account — no separate phone number needed. The `-v` mount persists
   the linked session across container restarts; keep it, or you'll have to
   re-scan.
3. Copy `.env.example` to `.env` and fill in your coordinates, ADS-B Exchange
   key, and `SIGNAL_FROM_NUMBER`/`SIGNAL_TO_NUMBER` (both are your own Signal
   number in E.164 format — you're sending yourself alerts from your own
   linked account). No signup needed for earthquakes — the USGS API requires
   no key.

## Run locally

```sh
cd plane-alert
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export $(grep -v '^#' .env | xargs)   # or use python-dotenv / direnv
python -m plane_alert.main
```

## Deploy to a DigitalOcean Droplet

A Droplet gives both containers a real persistent disk, which also solves
the Signal linked-device persistence problem App Platform couldn't
(ephemeral disks there would force a QR re-scan on every restart).

`docker-compose.yml` runs two services:
- `signal-api` — `signal-cli-rest-api`, bound to `127.0.0.1:8080` only (it
  has no built-in auth — anyone who could reach the port could send as your
  linked Signal number, so don't expose it publicly)
- `poller` — this app, built from the local `Dockerfile`

Both have `restart: always`. That's what makes this survive a reboot: Docker
restarts any `restart: always` container whenever the Docker daemon starts,
and the Docker daemon itself is a systemd service that starts on boot by
default (on DO's "Docker on Ubuntu" Marketplace image, or after `apt install
docker.io` + `systemctl enable docker` on a plain Ubuntu Droplet). So a
Droplet reboot — planned or from a crash — brings Docker back up, which
brings both containers back up, with no manual step. `restart: always` also
covers the app crashing on its own (e.g. an unhandled exception, though
`main.py`'s poll loop already catches and logs those rather than dying) or
someone doing `docker stop` and the daemon restarting later.

1. Create a Droplet — the **"Docker on Ubuntu" Marketplace image** is the
   easy path (Docker pre-installed and pre-enabled on boot). Otherwise, on a
   plain Ubuntu image: `apt install docker.io docker-compose-plugin && systemctl enable --now docker`.
2. Copy this repo to the Droplet (`git clone`, or `scp` if you'd rather not
   push secrets-adjacent files anywhere) and create `.env` from
   `.env.example` with your real values.
3. Start it:
   ```sh
   docker compose up -d --build
   ```
4. Link Signal (first run only): the `signal-api` port is bound to
   localhost for security, so reach it through an SSH tunnel:
   ```sh
   ssh -L 8080:localhost:8080 you@your-droplet-ip
   ```
   then open `http://localhost:8080/v1/qrcodelink?device_name=plane-alert`
   in your local browser and scan it from your phone's Signal app. This
   session persists in `./data/signal-cli` on the Droplet's disk.
5. Verify both containers are set to survive a reboot:
   ```sh
   docker inspect -f '{{.Name}} {{.HostConfig.RestartPolicy.Name}}' $(docker compose ps -q)
   ```
   should print `always` for both. Watch logs with `docker compose logs -f poller`.

To actually test the reboot behavior rather than take it on faith:
`sudo reboot`, wait for the Droplet to come back, then `docker compose ps`
should show both containers `Up` without you touching anything.

## Mothballed: Twilio SMS

`plane_alert/notifier.py` (Twilio) is left in place but unused — `main.py`
currently imports `signal_notifier` instead. The A2P 10DLC campaign
registration required to send SMS was rejected; Signal has no equivalent
carrier-vetting process, hence the switch. To revert: swap the import in
`main.py` back to `.notifier`, and fill in the `TWILIO_*` vars in `.env`
(they're optional/unused while mothballed).

### Legal pages for A2P 10DLC registration (only relevant if you revisit Twilio)

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
| `EARTHQUAKE_RADIUS_MILES` | Earthquake alert radius | `50.0` |
| `EARTHQUAKE_MIN_MAGNITUDE` | Minimum magnitude to alert on | `2.0` |
| `EARTHQUAKE_LOOKBACK_HOURS` | How far back each USGS query looks | `24` |
| `EARTHQUAKE_POLL_INTERVAL_SECONDS` | USGS poll frequency | `300` |
| `EARTHQUAKE_COOLDOWN_MINUTES` | Effectively "once per quake" (dedup is by USGS event id already) | `10080` (1 week) |
| `SIGNAL_REST_API_URL` | Base URL of your `signal-cli-rest-api` instance | `http://localhost:8080` |
| `SIGNAL_FROM_NUMBER` / `SIGNAL_TO_NUMBER` | Your Signal number (E.164) — both are you | required |
| `TWILIO_*` | Twilio account SID / auth token / from / to numbers | mothballed, unused |
| `DB_PATH` | SQLite file for cooldown state | `/data/plane_alert.db` |

## Changing configuration after deploy

Every tunable (radii, magnitude threshold, poll intervals, cooldowns) lives
in `.env`, not in code — see the table above for what each one does.

**Local dev**: edit `.env`, then just re-run `python -m plane_alert.main` —
env vars are read fresh on every start.

**Droplet**:
```sh
ssh -i <your-key> root@<droplet-ip>
cd /opt/plane-alert
nano .env            # or vim, or scp a new .env over from your Mac
docker compose up -d
```
Use `up -d`, not `restart` — `restart` just restarts the existing container
process with whatever env it already has baked in; it does **not** re-read
`.env`. `up -d` recreates whichever service's resolved config (including
`.env` values) changed since it was last started — verified live: editing
an `EARTHQUAKE_*` value and running `up -d` recreated only `poller`,
`signal-api` stayed running untouched. Even if `signal-api` does get
recreated (e.g. after a compose/image change), that's harmless — its Signal
session lives in the `./data/signal-cli` volume mount, not the container, so
it survives recreation. No `--build` needed here since you're only touching
config, not code.

## Caveats

- Military aircraft not transmitting ADS-B won't show up at all — this is a
  transponder-level limitation, not something the app or API can work around.
- ADS-B Exchange's lat/lon/dist endpoint is deprecated in favor of v3; this
  still targets v2 for simplicity but the field-name caveat above applies.
- `signal-cli-rest-api` is an unofficial, reverse-engineered Signal client —
  not sanctioned by Signal for automation, though this pattern (personal,
  single-recipient, low-volume) is common and low-risk. It could break on a
  future Signal protocol change.
- USGS revises earthquake magnitude/location for a while after an event as
  more seismic data comes in. Since dedup is keyed by USGS event id with a
  ~1-week cooldown, you'll only ever get the first alert for a given quake,
  not a corrected one — a M4.9 initially reported and later revised to M5.3
  still only texts you once, with whatever numbers were live at poll time.
