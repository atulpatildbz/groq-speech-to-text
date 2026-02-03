#!/usr/bin/env python3
"""
Optional scheduler for periodic Google Drive sync
Runs gdrive_sync.py at specified intervals (minimum 2 hours)
"""
import schedule
import time
import subprocess
from datetime import datetime

# Configuration
SYNC_INTERVAL_HOURS = 2  # Minimum 2 hours, adjust as needed


def run_sync():
    """Run the sync script"""
    print(f"\n{'='*60}")
    print(f"Scheduled sync triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    try:
        # Run gdrive_sync.py as a subprocess
        result = subprocess.run(['python', 'gdrive_sync.py'], capture_output=False, text=True)

        if result.returncode == 0:
            print("\n✓ Sync completed successfully")
        else:
            print(f"\n✗ Sync failed with exit code {result.returncode}")

    except Exception as e:
        print(f"\n✗ Error running sync: {str(e)}")


def main():
    """Main scheduler loop"""
    if SYNC_INTERVAL_HOURS < 2:
        print("Error: SYNC_INTERVAL_HOURS must be at least 2 hours")
        return

    print(f"{'='*60}")
    print(f"Google Drive Sync Scheduler Started")
    print(f"Interval: Every {SYNC_INTERVAL_HOURS} hour(s)")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    print("Press Ctrl+C to stop\n")

    # Schedule the job
    schedule.every(SYNC_INTERVAL_HOURS).hours.do(run_sync)

    # Run once immediately on startup
    print("Running initial sync...")
    run_sync()

    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\nScheduler stopped by user")


if __name__ == "__main__":
    main()
