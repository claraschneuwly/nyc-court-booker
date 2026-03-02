# NYC Tennis Court Booking Bot

This project is a Python automation bot using Selenium to book tennis courts on the [NYC Parks Tennis Reservation website](https://www.nycgovparks.org/tennisreservation). It automatically attempts to book courts the moment they are released to the public each week, based on your personal preferences and location priorities (Central Park, Sutton East, Riverside Park, and McCarren).


## Project Structure
```
.
├── app.py # Core booking logic and Selenium flows
├── weekly_court_scheduler.py # Scheduler script (config-driven, runs via cron)
├── jobs.yaml # Job configuration (locations, hours, schedules)
├── setup_cron.sh # Script to install/remove cron jobs (reads jobs.yaml)
├── .env # Environment variables (not tracked in Git)
├── .gitignore # Ignores secrets, binaries, screenshots, logs
├── chromedriver # ChromeDriver binary (make sure it matches Chrome version)
├── requirements.txt # Python dependencies
```

## Usage

Clone this repo and adapt it to your needs.
```bash
git clone https://github.com/claraschneuwly/nyc-court-booker.git
cd nyc-tennis-booking-bot
```

## 1. Environment Variables

Create a `.env` file in the project root with the following:

```
full-name=Your Full Name
email=your@email.com
address-line-one=123 Main St
city=New York
postcode=10000
phone-number=1234567890
permit-number=XXXXXX # Only required for Central Park
card-number=4111111111111111
expiry-month=12
expiry-year=2025
cvv=123
```

Note: Never commit your `.env` to version control.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Ensure ChromeDriver Matches Your Chrome Version
To work correctly, `chromedriver` must match the major version of your installed Google Chrome browser. Otherwise, Selenium will fail with a `session not created error`.

#### How to Check Your Chrome Version

On MacOS: `/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version`

You’ll see something like: `Google Chrome 114.0.5735.198`
In this case, your Chrome major version is 114.

#### How to Download the Matching ChromeDriver

1. Go to the official [Chrome for Testing download page](https://googlechromelabs.github.io/chrome-for-testing/)

2. Look for a version that matches your Chrome major version (ex: 114.0.x.x).

3. Download the correct platform version:

- mac-x64 : Intel Macs

- mac-arm64 : Apple Silicon (M1, M2, M3)

- linux-x64 : Linux

- win32 : Windows

4. Unzip it and move the binary to your project folder:
```bash
unzip chromedriver-mac-arm64.zip
mv chromedriver-mac-arm64/chromedriver ./chromedriver
chmod +x ./chromedriver
```


### 4. Run the bot

- Run a one-time booking manually

```bash
python app.py
```

- Run individual jobs manually (for testing)

```bash
python weekly_court_scheduler.py sutton
python weekly_court_scheduler.py central-park-sat
python weekly_court_scheduler.py central-park-sun
```

### 5. Configure jobs

All booking jobs are defined in `jobs.yaml`. Edit this file to change locations, hours, days offset, or cron schedules — no Python code changes needed.

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

To add a new job, just add another entry under `jobs:` and re-run `./setup_cron.sh install`.

### 6. Set up the cron jobs

The setup script reads `jobs.yaml` and installs a cron entry for each job. No continuously running process is needed.

#### Option A: Using the setup script (Recommended)

```bash
# Install cron jobs (reads from jobs.yaml)
./setup_cron.sh install

# View current cron jobs
./setup_cron.sh view

# Check status
./setup_cron.sh status

# Remove all cron jobs
./setup_cron.sh remove
```

After editing `jobs.yaml`, run `./setup_cron.sh remove` then `./setup_cron.sh install` to apply changes.

#### Option B: Manual cron setup

Open your crontab with `crontab -e` and add entries matching your `jobs.yaml` (adjust paths as needed):

```bash
0 0 * * 4 cd /path/to/nyc-court-booker && /path/to/venv/bin/python weekly_court_scheduler.py sutton >> /path/to/nyc-court-booker/cron.log 2>> /path/to/nyc-court-booker/cron_error.log
0 0 * * 6 cd /path/to/nyc-court-booker && /path/to/venv/bin/python weekly_court_scheduler.py central-park-sat >> /path/to/nyc-court-booker/cron.log 2>> /path/to/nyc-court-booker/cron_error.log
0 0 * * 0 cd /path/to/nyc-court-booker && /path/to/venv/bin/python weekly_court_scheduler.py central-park-sun >> /path/to/nyc-court-booker/cron.log 2>> /path/to/nyc-court-booker/cron_error.log
```

### 7. Keep your Mac awake for cron jobs

Cron jobs only run if your computer is awake. If your Mac is asleep or shut down at the scheduled time, the job is silently skipped.
To ensure your Mac wakes up before the cron jobs fire at midnight, run this once:

```bash
sudo pmset repeat wakeorpoweron MTWRFSU 23:55:00
```

This tells macOS to wake (or power on) your Mac at 23:55 every night, giving it 5 minutes to reconnect to WiFi before the midnight cron jobs run.

**Requirements:**
- Your Mac must be **plugged into power**
- Lid can be closed (sleep is fine)
- Do **not** shut down the Mac — sleep mode is required

To verify the schedule is set:

```bash
pmset -g sched
```

To cancel it:

```bash
sudo pmset repeat cancel
```

## Debugging and Deployment

- Screenshots of booking attempts are saved as `*.png` for debugging 
- Application logs are saved to `scheduler.log` for review
- Cron job output is logged to `cron.log` (stdout) and `cron_error.log` (stderr)
- The script runs automatically via cron job - no need to keep it running continuously
- To verify the cron job is installed, run: `crontab -l`
- To test a job manually, run: `python weekly_court_scheduler.py sutton` (or `central-park-sat`, `central-park-sun`)


## Relevant info about the courts

- Central Park = 12 : Six Outdoor Har-Thru courts, 1 month is advance, last slot @ 7pm, res open @ 6am ?
- Sutton East = 13: Two Inside Clay courts, 1 week in advance, last slot @ 8pm, res open @ midnight ?
- Riverside Park (119 Street) = 2 : Two Outdoor Hard courts (recently resurfaced), 1 week in advance, last slot @ 7pm, res open @ midnight ?
- MCCarren = 11: Two Outdoor Hard courts, 1 week in advance, last slot @ 6pm, , res open @ midnight ?


## References: [court_booker](https://github.com/danroche10/court_booker.git) 
