"""Command-line interface for Overmind."""

import argparse
import sys
from pathlib import Path

from overmind import __version__
from overmind.config.settings import Settings


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Overmind - Solar water temperature regulation system"
    )
    parser.add_argument(
        "--version", action="version", version=f"overmind {__version__}"
    )
    parser.add_argument(
        "-c", "--config",
        type=str,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Validate configuration and exit",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run the temperature controller")
    run_parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Control loop interval in seconds (default: 60)",
    )

    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor temperatures")
    monitor_parser.add_argument(
        "--interval",
        type=int,
        default=10,
        help="Monitoring interval in seconds (default: 10)",
    )

    args = parser.parse_args()

    # Load settings
    try:
        settings = Settings(args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.check_config:
        print(f"Configuration loaded successfully from: {settings.config_path}")
        print(f"Location: {settings.location_name} (ID: {settings.location_id})")
        print(f"Wattrouter URL: {settings.wattrouter_url}")
        return 0

    if args.command == "run":
        from overmind.controllers.temperature import TemperatureController
        from overmind.sensors.wattrouter import WattrouterClient

        print("Starting Overmind temperature controller...")
        print(f"Configuration: {settings.config_path}")
        print(f"Control interval: {args.interval}s")
        # TODO: Implement main control loop
        return 0

    elif args.command == "monitor":
        from overmind.sensors.wattrouter import WattrouterClient

        print("Starting temperature monitoring...")
        print(f"Monitoring interval: {args.interval}s")
        # TODO: Implement monitoring loop
        return 0

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
