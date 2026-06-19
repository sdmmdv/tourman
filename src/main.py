#!/usr/bin/env python3
"""
Tournament Manager Central CLI
-----------------------------------
Unified CLI for managing tournament operations.
"""

import argparse
import sys
import os

if "--verbose" in sys.argv or "-v" in sys.argv:
    os.environ["LOG_LEVEL"] = "DEBUG"
else:
    os.environ["LOG_LEVEL"] = "INFO"

from common.logger import get_logger
logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Swiss System Tournament Manager CLI")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db",              help="Initialize the tournament database")
    p = subparsers.add_parser("generate-players", help="Generate list of players")
    p.add_argument("-n", "--num-players", type=int, default=10, help="Number of players to generate")
    subparsers.add_parser("register-players",     help="Register players into the database")

    p = subparsers.add_parser("generate-swiss-pairings", help="Generate swiss match pairings")
    p.add_argument("-r", "--round-id", required=True, help="Round ID")

    subparsers.add_parser("generate-roundrobin-pairings", help="Generate round-robin match pairings")
    subparsers.add_parser("register-standings",   help="Register tournament standings")

    p = subparsers.add_parser("populate-results", help="Populate results from a file")
    p.add_argument("-f", "--file", required=True, help="CSV file with results")

    p = subparsers.add_parser("register-results", help="Register results into DB")
    p.add_argument("-f", "--input-file", required=True, help="Results input CSV file")
    p.add_argument("--conn", help="PostgreSQL connection string")

    p = subparsers.add_parser("print-table",      help="Print tournament tables")
    p.add_argument("-t", "--table", choices=["standings", "results", "players"], required=True)
    p.add_argument("--conn", help="PostgreSQL connection string")

    p = subparsers.add_parser("apply-results",    help="Apply results to standings for a given round")
    p.add_argument("-r", "--round-id", required=True)
    p.add_argument("--conn", help="PostgreSQL connection string")

    p = subparsers.add_parser("convert-excel-to-csv", help="Convert Excel file to CSV format")
    p.add_argument("--input",  default="data/input.xlsx", help="Path to input Excel file")
    p.add_argument("--output", default="data/output.csv",  help="Path to output CSV file")

    subparsers.add_parser("convert-table-to-excel", help="Convert DB tables to Excel format")

    test_parser = subparsers.add_parser("test", help="Run internal test scripts")
    test_parser.add_argument(
        "name",
        choices=["test_pairings", "test_player", "test_standings", "test_tournament"]
    )

    args = parser.parse_args()

    try:
        if args.command == "init-db":
            from core.init_db import main as run
            run()

        elif args.command == "generate-players":
            from core.generate_players import main as run
            run(args.num_players)

        elif args.command == "register-players":
            from core.register_players import main as run
            run()

        elif args.command == "generate-swiss-pairings":
            from core.generate_swiss_pairings import main as run
            run(args.round_id)

        elif args.command == "generate-roundrobin-pairings":
            from core.generate_roundrobin_pairings import main as run
            run()

        elif args.command == "register-standings":
            from core.register_standings import main as run
            run()

        elif args.command == "populate-results":
            from utils.populate_results import main as run
            run(args.file)

        elif args.command == "register-results":
            from core.register_results import main as run
            run(args.input_file, args.conn)

        elif args.command == "apply-results":
            from core.apply_results_to_standings import main as run
            run(args.round_id, args.conn)

        elif args.command == "print-table":
            from utils.print_table import main as run
            run(args.table, args.conn)

        elif args.command == "convert-excel-to-csv":
            from utils.convert_excel_to_csv import main as run
            run(args.input, args.output)

        elif args.command == "convert-table-to-excel":
            from utils.convert_table_to_excel import main as run
            run()

        elif args.command == "test":
            import importlib
            mod = importlib.import_module(f"test.{args.name}")
            mod.main()

    except ImportError as err:
        logger.error("Failed to import module: %s", err)
        sys.exit(1)
    except Exception as err:
        logger.error("Unexpected error occurred! %s", err)
        sys.exit(1)


if __name__ == "__main__":
    main()