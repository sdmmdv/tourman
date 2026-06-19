#!/usr/bin/env python3
import csv
from faker import Faker
from pathlib import Path
import argparse
import os

from common.logger import get_logger

logger = get_logger(__name__)
fake = Faker()


def generate_fake_players(num_players):
    players = []
    used_ids = set()
    logger.debug(f"Starting generation of {num_players} players...")
    while len(players) < num_players:
        player_id = fake.numerify(text='#####')
        if player_id in used_ids:
            continue
        used_ids.add(player_id)
        players.append((player_id, fake.name(), fake.email()))
    logger.debug(f"Generated {len(players)} players successfully.")
    return players


def write_players_to_csv(players, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['id', 'name', 'email'])
        writer.writerows(players)
    logger.info(f"Successfully wrote {len(players)} players to {output_path}")


def main(num_players=10):          # ← accepts argument directly
    logger.info(f"Generating {num_players} players...")
    players = generate_fake_players(num_players)

    # Use CWD/data/ — works correctly after installation
    output_file = Path(os.getcwd()) / 'data' / 'players.csv'
    write_players_to_csv(players, output_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--num-players', type=int, default=10)
    args = parser.parse_args()
    main(args.num_players)