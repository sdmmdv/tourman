#!/usr/bin/env python3

import csv
import random
import argparse
import os

from common.logger import get_logger

logger = get_logger(__name__)

# Possible results
RESULTS = [
    ("1.0", "0.0"),  # player1 wins
    ("0.5", "0.5"),  # draw
    ("0.0", "1.0")   # player2 wins
]

def replace_results(filename: str) -> None:
    # Create new filename by replacing 'pairings' with 'results'
    dirname, basename = os.path.split(filename)
    if "pairings" in basename:
        new_basename = basename.replace("pairings", "results", 1)
    else:
        new_basename = f"results_{basename}"
    output_file = os.path.join(dirname, new_basename)

    # Read all rows
    with open(filename, newline="", encoding="utf-8") as infile:
        reader = csv.reader(infile)
        rows = list(reader)

    # Replace results
    for row in rows[1:]:  # skip header
        if row[3] == "?" and row[4] == "?":
            row[3], row[4] = random.choice(RESULTS)

    # Write to the new results file
    with open(output_file, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        writer.writerows(rows)

    logger.info(f"Results written to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Replace ? with random chess/game results in pairings CSV."
    )
    parser.add_argument("-f",
                        "--file",
                        type=str,
                        required=True,
                        help="Path to the pairings file to be updated")

    args = parser.parse_args()
    replace_results(args.file)


if __name__ == "__main__":
    main()
