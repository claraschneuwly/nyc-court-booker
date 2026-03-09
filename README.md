# NYC Tennis Court Booking Bot

Automated booking of tennis courts on the [NYC Parks Tennis Reservation website](https://www.nycgovparks.org/tennisreservation) using Selenium. The bot attempts to reserve courts the moment they are released each week, based on your personal preferences and location priorities (Central Park, Sutton East, Riverside Park, and McCarren).

## Project Structure

```
.
├── court_booker/                # Python package
│   ├── __init__.py
│   ├── __main__.py              # Entry point (python -m court_booker)
│   ├── booking.py               # Core Selenium booking flow
│   ├── config.py                # Constants, location metadata, env loading
│   ├── logging_config.py        # Centralised logging setup
│   ├── notifier.py              # Telegram push notifications
│   └── scheduler.py             # Job runner (reads jobs.yaml)
├── jobs.yaml                    # Job configuration (locations, hours, schedules)
├── setup_cron.sh                # Install / remove cron jobs
├── .env                         # Environment variables (not tracked)
├── .env.example                 # Template for .env
├── .gitignore
├── requirements.txt
├── chromedriver                 # ChromeDriver binary (match your Chrome version)
└── screenshots/                 # Runtime screenshots (auto-created, not tracked)
```

## Quick Start

```bash
git clone https://github.com/claraschneuwly/nyc-court-booker.git
cd nyc-court-booker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your real values
```

## 1. Environment Variables

Create a `.env` file in the project root (see `.env.example` for all keys):

```ini
full-name=Your Full Name
email=your@email.com
address-line-one=123 Main St
city=New York
postcode=10000
phone-number=1234567890
permit-number=XXXXXX          # Only required for Central Park

card-number=4111111111111111
expiry-month=12
expiry-year=2025
cvv=123

# Optional — see Section Phone Notifications
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

> **Note:** Never commit your `.env` to version control.


## 2. Install dependencies

### Download the Matching ChromeDriver
Ensure `chromedriver` matches the major version of your installed Google Chrome browser. Otherwise, Selenium will fail with a `session 
not created error`.
```bash
# On macOS:
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version
```

You’ll see something like: `Google Chrome 114.0.5735.198`
In this case, your Chrome major version is 114.

1. Go to the official [Chrome for Testing download page](https://googlechromelabs.github.io/chrome-for-testing/)

2. Look for a version that matches your Chrome major version (ex: 114.0.x.x).

3. Download the correct platform version:

- mac-x64 : Intel Macs

- mac-arm64 : Apple Silicon (M1, M2, M3)

- linux-x64 : Linux

- win32 : Windows

4. Unzip it and move the binary in the project root:
```bash
unzip chromedriver-mac-arm64.zip
mv chromedriver-mac-arm64/chromedriver ./chromedriver
chmod +x ./chromedriver
```

## 3. Run the Bot

### One-off manual booking

```bash
python -m court_booker sutton
python -m court_booker central-park-sat
python -m court_booker central-park-sun
```

### Configure jobs

All booking jobs are defined in `jobs.yaml`. Edit this file to change locations, hours, lead time, or cron schedules — no code changes needed.

```yaml
jobs:
  sutton:
    cron_schedule: "0 0 * * 4"  # Wed midnight (Thu 00:00)
    days_ahead: 7
    attempts:
      - location: 13   # Sutton East
        hour: 20        # 8PM
      - location: 13
        hour: 19        # 7PM (fallback)

  central-park-sat:
    cron_schedule: "0 0 * * 6"  # Fri midnight (Sat 00:00)
    days_ahead: 29
    attempts:
      - location: 12   # Central Park
        hour: 16        # 4PM

  central-park-sun:
    cron_schedule: "0 0 * * 0"  # Sat midnight (Sun 00:00)
    days_ahead: 29
    attempts:
      - location: 12   # Central Park
        hour: 17        # 5PM
```

To add a new job, add another entry under `jobs:` and re-run `./setup_cron.sh install`.

## 4. Cron Jobs

The setup script reads `jobs.yaml` and installs a cron entry for each job. No continuously running process is needed.

### Option A: Using the setup script (recommended)

```bash
./setup_cron.sh install   # Install from jobs.yaml
./setup_cron.sh view      # View current cron jobs
./setup_cron.sh status    # Full status overview
./setup_cron.sh remove    # Remove all project cron jobs
```

After editing `jobs.yaml`, run `./setup_cron.sh remove` then `./setup_cron.sh install` to apply changes.

### Option B: Manual cron setup
Open your crontab with `crontab -e` and add entries matching your `jobs.yaml` (adjust paths as needed):

Add entries like:

```
0 0 * * 4 cd /path/to/nyc-court-booker && /path/to/venv/bin/python -m court_booker sutton >> cron.log 2>> cron_error.log
```

## 5. Keep Your Mac Awake for Cron

Cron jobs only run while your computer is awake. If your Mac is asleep or shut down at the scheduled time, the job is silently skipped.
To ensure your Mac wakes up before the cron jobs fire at midnight, schedule a daily wake at 23:55 so the machine is ready for midnight jobs. Run this once:

```bash
sudo pmset repeat wakeorpoweron MTWRFSU 23:55:00
```

This tells macOS to wake (or power on) your Mac at 23:55 every night, giving it 5 minutes to reconnect to WiFi before the midnight cron jobs run.

**Requirements:**
- Mac must be **plugged into power**
- Lid can be closed (sleep is fine)
- Do **not** shut down the Mac — sleep mode is required

```bash
pmset -g sched       # Verify schedule
sudo pmset repeat cancel  # Cancel
```

## 6. Phone Notifications (Telegram)

The bot sends real-time notifications to your phone via Telegram after every cron run.

| Event | Example message |
|---|---|
| Court booked | ✅ **Court booked!** Sutton East, 8:00 PM on 2026-03-11 |
| All attempts failed | ❌ **Booking failed** — All 2 attempt(s) failed for 2026-03-11 |
| Bot crash | ⚠️ **Bot error** — Job `sutton` crashed: TimeoutException… |

### Setup

1. Open Telegram and message [@BotFather](https://t.me/BotFather). Send `/newbot` and follow the prompts to create a bot. Save the **bot token**.
2. Find your new bot by its username and send it any message (e.g. `hello`).
3. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser. Find your **chat ID** at `result[0].message.chat.id`.
4. Add both values to `.env`:

```ini
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=987654321
```

If the Telegram API is unreachable, the bot logs a warning and continues — notifications never interfere with bookings.

## Debugging

- **Screenshots** — saved to `screenshots/` as `*.png` after each step for post-mortem debugging.
- **Application log** — `court_booking.log` (all levels).
- **Cron output** — `cron.log` (stdout) and `cron_error.log` (stderr).
- To test a job manually: `python -m court_booker sutton`.
- To verify cron is installed: `crontab -l`.

## Relevant court info

- Central Park = 12 : Six Outdoor Har-Thru courts, 1 month is advance, last slot @ 7pm, res open @ 6am ?
- Sutton East = 13: Two Inside Clay courts, 1 week in advance, last slot @ 8pm, res open @ midnight ?
- Riverside Park (119 Street) = 2 : Two Outdoor Hard courts (recently resurfaced), 1 week in advance, last slot @ 7pm, res open @ midnight ?
- MCCarren = 11: Two Outdoor Hard courts, 1 week in advance, last slot @ 6pm, , res open @ midnight ?

## References: [court_booker](https://github.com/danroche10/court_booker.git) 
