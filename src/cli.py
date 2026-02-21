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

def run_cleanup_releases():
    from src.services.analyze import cleanup_orphaned_releases
    result = cleanup_orphaned_releases()
    print(f"RESULT: {result}")

def run_repair_metadata():
    from src.services.discover import repair_file_metadata
    result = repair_file_metadata()
    print(f"RESULT: {result}")

def run_reanalyze_quality():
    from src.services.analyze import reanalyze_quality
    result = reanalyze_quality()
    print(f"RESULT: {result}")

def run_symlink():
    from src.services.symlink import run_symlink
    result = run_symlink()
    print(f"RESULT: {result}")

def main():
    parser = argparse.ArgumentParser(description="Music Curator CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("discover", help="Run file discovery")
    subparsers.add_parser("analyze", help="Run audio analysis")
    subparsers.add_parser("cleanup-releases", help="Delete orphaned music_release rows with no linked files")
    subparsers.add_parser("repair-metadata", help="Re-extract tags for files stored with empty metadata (' |  | ')")
    subparsers.add_parser("reanalyze-quality", help="Re-run spectral ceiling + quality scoring for all files (use after algorithm changes)")
    subparsers.add_parser("symlink", help="Create/update symlinks for primary files; remove stale ones")

    args = parser.parse_args()

    if args.command == "discover":
        run_discover()
    elif args.command == "analyze":
        run_analyze()
    elif args.command == "cleanup-releases":
        run_cleanup_releases()
    elif args.command == "repair-metadata":
        run_repair_metadata()
    elif args.command == "reanalyze-quality":
        run_reanalyze_quality()
    elif args.command == "symlink":
        run_symlink()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
