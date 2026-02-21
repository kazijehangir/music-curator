import sys
import argparse
import logging
from pathlib import Path

# Configure basic logging to stdout for the CLI
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stdout
)

def run_discover():
    from src.services.discover import run_discovery
    result = run_discovery()
    print(f"RESULT: {result}")

def run_analyze():
    from src.services.analyze import run_analysis
    result = run_analysis()
    print(f"RESULT: {result}")

def main():
    parser = argparse.ArgumentParser(description="Music Curator CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("discover", help="Run file discovery")
    subparsers.add_parser("analyze", help="Run audio analysis")
    # Future commands: tag, symlink, etc.

    args = parser.parse_args()

    if args.command == "discover":
        run_discover()
    elif args.command == "analyze":
        run_analyze()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
