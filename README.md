# NYC Tennis Court Booking Bot

This project is a Python automation bot using Selenium to book tennis courts on the [NYC Parks Tennis Reservation website](https://www.nycgovparks.org/tennisreservation). It automatically attempts to book courts the moment they are released to the public each week, based on your personal preferences and location priorities (Central Park, Sutton East, Riverside Park, and McCarren).


## Project Structure
```
.
├── app.py # Core booking logic and Selenium flows
├── weekly_court_scheduler.py # Scheduler script (runs every Tuesday at midnight)
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

- Run the weekly scheduler

```bash
python weekly_court_scheduler.py
```

This will: 

- Run every Monday at midnight (i.e., 12:00 AM on Tuesday)

- Attempt bookings in order:

    1. Sutton East at 8 PM
    2. Sutton East at 7 PM
    3. Riverside Park at 7 PM

- Always attempt Central Park 29 days out if that day is a Saturday:

    1. First try 4 PM

    2. If unavailable, try 11 AM

## Debbugging and Deployment

- Screenshots  of booking attempts are saved as `*.png` for debugging 
- Logs are saved to `scheduler.log` for review
- To run this as a persistent job, consider setting up as a cron job or using a process manager (e.g. pm2, systemd) if running on a server


## Relevant info about the courts

- Central Park = 12 : Six Outdoor Har-Thru courts, 1 month is advance, last slot @ 7pm, res open @ 6am ?
- Sutton East = 13: Two Inside Clay courts, 1 week in advance, last slot @ 8pm, res open @ midnight ?
- Riverside Park (119 Street) = 2 : Two Outdoor Hard courts (recently resurfaced), 1 week in advance, last slot @ 7pm, res open @ midnight ?
- MCCarren = 11: Two Outdoor Hard courts, 1 week in advance, last slot @ 6pm, , res open @ midnight ?


## References: [court_booker](https://github.com/danroche10/court_booker.git) 
