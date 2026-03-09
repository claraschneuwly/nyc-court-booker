#!/bin/bash

# NYC Court Booker — Cron Job Setup Script
# Reads job definitions from jobs.yaml and installs / removes / views cron entries.
#
# Usage:
#   ./setup_cron.sh install   — Install cron jobs from jobs.yaml
#   ./setup_cron.sh remove    — Remove all project cron jobs
#   ./setup_cron.sh view      — Show current project cron jobs
#   ./setup_cron.sh status    — Full configuration overview

# Don't exit on error for crontab commands (they return non-zero when no crontab exists)
set +e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
CONFIG_FILE="$PROJECT_DIR/jobs.yaml"
CRON_LOG="$PROJECT_DIR/cron.log"
CRON_ERROR_LOG="$PROJECT_DIR/cron_error.log"

# Find Python virtual environment
if [ -d "$PROJECT_DIR/venv" ]; then
    VENV_DIR="$PROJECT_DIR/venv"
elif [ -d "$PROJECT_DIR/.venv" ]; then
    VENV_DIR="$PROJECT_DIR/.venv"
elif [ -d "$PROJECT_DIR/venvclean" ]; then
    VENV_DIR="$PROJECT_DIR/venvclean"
else
    echo -e "${RED}Error: No virtual environment found. Create one first:${NC}"
    echo "  python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

PYTHON_BIN="$VENV_DIR/bin/python"

# ── Pre-flight checks ───────────────────────────────────────────────────────
for f in "$PYTHON_BIN" "$CONFIG_FILE"; do
    if [ ! -f "$f" ]; then
        echo -e "${RED}Error: Required file not found: $f${NC}"
        exit 1
    fi
done

# Parse jobs from jobs.yaml using Python
# Returns lines like: job_name|cron_schedule
parse_jobs() {
    "$PYTHON_BIN" -c "
import yaml, sys
with open('$CONFIG_FILE') as f:
    config = yaml.safe_load(f)
if not config or 'jobs' not in config:
    sys.exit(1)
for name, job in config['jobs'].items():
    print(f\"{name}|{job['cron_schedule']}\")
"
}

# Build the cron entries that should be installed
# Uses `python -m court_booker <job>` instead of calling a script directly
build_cron_entries() {
    local entries=""
    while IFS='|' read -r job_name cron_schedule; do
        local cmd="cd $PROJECT_DIR && $PYTHON_BIN -m court_booker $job_name >> $CRON_LOG 2>> $CRON_ERROR_LOG"
        if [ -n "$entries" ]; then
            entries="$entries"$'\n'
        fi
        entries="${entries}${cron_schedule} ${cmd}"
    done < <(parse_jobs)
    echo "$entries"
}

# Function to check if any cron jobs for this project exist
cron_jobs_exist() {
    crontab -l 2>/dev/null | grep -F "court_booker" > /dev/null
}

# Function to install cron jobs from YAML config
install_cron() {
    if cron_jobs_exist; then
        echo -e "${YELLOW}Warning: Cron jobs for this project already exist.${NC}"
        echo "Use 'remove' first, then 'install' to refresh."
        return 1
    fi

    NEW_ENTRIES=$(build_cron_entries)
    if [ -z "$NEW_ENTRIES" ]; then
        echo -e "${RED}Error: No jobs found in $CONFIG_FILE${NC}"
        return 1
    fi

    NUM_JOBS=$(echo "$NEW_ENTRIES" | wc -l | tr -d ' ')
    CURRENT_CRONTAB=$(crontab -l 2>/dev/null)
    CRON_EXIT_CODE=$?

    if [ $CRON_EXIT_CODE -eq 0 ] && [ -n "$CURRENT_CRONTAB" ]; then
        (echo "$CURRENT_CRONTAB"; echo "$NEW_ENTRIES") | crontab -
    else
        echo "$NEW_ENTRIES" | crontab -
    fi

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}${NUM_JOBS} cron job(s) installed successfully!${NC}"
        echo ""
        echo "Jobs installed:"
        while IFS='|' read -r job_name cron_schedule; do
            echo "  - $job_name (schedule: $cron_schedule)"
        done < <(parse_jobs)
        echo ""
        echo "Logs: $CRON_LOG (stdout) and $CRON_ERROR_LOG (stderr)"
        echo "To view your cron jobs, run: crontab -l"
        return 0
    else
        echo -e "${RED}Error: Failed to install cron jobs.${NC}"
        return 1
    fi
}

# Function to remove all cron jobs for this project
remove_cron() {
    if ! cron_jobs_exist; then
        echo -e "${YELLOW}No cron jobs found for this project.${NC}"
        return 1
    fi

    CURRENT_CRONTAB=$(crontab -l 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$CURRENT_CRONTAB" ]; then
        FILTERED=$(echo "$CURRENT_CRONTAB" | grep -vF "court_booker")
        if [ -n "$FILTERED" ]; then
            echo "$FILTERED" | crontab -
        else
            crontab -r 2>/dev/null
        fi
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}All cron jobs for this project removed.${NC}"
            return 0
        else
            echo -e "${RED}Error: Failed to remove cron jobs.${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}No crontab found.${NC}"
        return 1
    fi
}

# Function to view cron jobs
view_cron() {
    echo "Current cron jobs for this project:"
    echo "------------------------------------"
    if cron_jobs_exist; then
        crontab -l 2>/dev/null | grep -F "court_booker"
    else
        echo "(none)"
    fi
    echo ""
    echo "All cron jobs:"
    echo "--------------"
    crontab -l 2>/dev/null || echo "(no crontab configured)"
}

# Function to show status
show_status() {
    echo "Project directory : $PROJECT_DIR"
    echo "Virtual environment: $VENV_DIR"
    echo "Python binary      : $PYTHON_BIN"
    echo "Config file        : $CONFIG_FILE"
    echo "Cron log (stdout)  : $CRON_LOG"
    echo "Cron log (stderr)  : $CRON_ERROR_LOG"
    echo ""

    echo "Jobs defined in jobs.yaml:"
    while IFS='|' read -r job_name cron_schedule; do
        echo "  - $job_name (schedule: $cron_schedule)"
    done < <(parse_jobs)
    echo ""

    if cron_jobs_exist; then
        NUM_INSTALLED=$(crontab -l 2>/dev/null | grep -cF "court_booker")
        echo -e "${GREEN}Status: ${NUM_INSTALLED} cron job(s) installed${NC}"
        echo ""
        view_cron
    else
        echo -e "${YELLOW}Status: No cron jobs installed${NC}"
    fi
}

# Main script logic
case "${1:-}" in
    install) install_cron ;;
    remove)  remove_cron  ;;
    view)    view_cron    ;;
    status)  show_status  ;;
    *)
        echo "NYC Court Booker — Cron Job Setup"
        echo "================================="
        echo ""
        echo "Usage: $0 {install|remove|view|status}"
        echo ""
        echo "Commands:"
        echo "  install  - Install cron jobs defined in jobs.yaml"
        echo "  remove   - Remove all cron jobs for this project"
        echo "  view     - View current cron jobs for this project"
        echo "  status   - Show setup status and configuration"
        echo ""
        echo "Jobs are defined in: $CONFIG_FILE"
        exit 1
        ;;
esac
