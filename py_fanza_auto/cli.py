from __future__ import annotations
import argparse
import os
from config import Settings
from engine import Engine
from apscheduler.schedulers.background import BackgroundScheduler
import time


def main() -> None:
    parser = argparse.ArgumentParser(description="FANZA Auto Plugin (Python)")
    parser.add_argument("run", nargs="?", default="once", choices=["once", "schedule", "test"], help="Run mode")
    args = parser.parse_args()

    settings = Settings.load()
    engine = Engine.from_settings(settings)

    if args.run == "once":
        ids = engine.run_once()
        print(f"Created posts: {ids}")
        return
    if args.run == "test":
        report = engine.run_test()
        print(report)
        return

    # schedule mode: read minute/hours from env if available
    minute = os.getenv("CRON_MINUTE", "0")
    hours = os.getenv("CRON_HOURS", "0")
    scheduler = BackgroundScheduler()
    for h in str(hours).split(","):
        try:
            hour = int(h)
        except Exception:
            continue
        scheduler.add_job(engine.run_once, "cron", minute=minute, hour=hour)
    scheduler.start()
    print("Scheduler started. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()


if __name__ == "__main__":
    main()
