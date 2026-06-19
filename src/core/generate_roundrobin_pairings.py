#!/usr/bin/env python3

import psycopg2
import argparse
from pathlib import Path
import csv
import subprocess
import os
import math

from player import Player
from common.db_utils import get_connection_string
from common.logger import get_logger
from common.common import root_dir

logger = get_logger(__name__)


def round_robin_pairing(players):
    """
    Generate all round-robin pairings for a list of active player objects.

    Each player faces every other player exactly once.
    If there is an odd number of players, one receives a BYE each round.

    Args:
        players (list): List of player objects with at least attributes:
                        - id
                        - name
                        - rank (optional, used for sorting/logging)

    Returns:
        list[list[tuple]]: A list of rounds,
                           where each round is a list of (playerA, playerB) tuples.
                           A BYE is represented as (player, 'BYE').

    Algorithm:
        - Implements the "circle method" for round-robin scheduling.
        - Ensures each player plays every other exactly once.
        - BYE pairings appear only if the player count is odd.

    Complexity:
        Time  : O(n²)
        Space : O(n²)
    """

    players = players[:]  # Copy list to avoid mutation
    n = len(players)
    has_bye = False

    # Handle odd number of players
    if n % 2 == 1:
        has_bye = True
        n += 1

    rounds = []
    for round_index in range(n - 1):
        round_pairs = []

        for i in range(n // 2):
            if has_bye and (i == 0 and round_index % n < len(players)):
                # Give BYE to one player each round in rotation
                bye_player = players[(round_index + i) % len(players)]
                round_pairs.append((bye_player, 'BYE'))
                continue

            # Determine real matchups
            p1_index = (round_index + i) % len(players)
            p2_index = (round_index + n - 1 - i) % len(players)

            if p1_index == p2_index:
                continue  # skip self-match in odd count

            p1 = players[p1_index]
            p2 = players[p2_index]
            if p1 != p2:
                round_pairs.append((p1, p2))

        rounds.append(round_pairs)

    return rounds


# Get eligible list of players in order of rankings to pair for the next round
def get_active_players(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, name, is_bye
            FROM Standings
            WHERE is_active = true
            ORDER BY points DESC, tiebreaker_A DESC, tiebreaker_B DESC, tiebreaker_C DESC;
        """)
        player_data = cur.fetchall()
    players = [Player(rank + 1, *data) for rank, data in enumerate(player_data)]
    return players

def roundrobin_round_count(num_players: int) -> int:
    """
    Return number of rounds required for a round-robin tournament
    given num_players.

    - Even n -> n - 1 rounds
    - Odd  n -> n rounds (one BYE slot included)
    """
    if num_players < 2:
        raise ValueError("Need at least 2 players for a tournament")
    return num_players if (num_players % 2 == 1) else (num_players - 1)


def generate_pairings_csv(sorted_pairs, round_id):
    filename = os.path.join(root_dir(__file__), 'data', f'pairings_r{round_id}.csv')
    filename_display = os.path.join(root_dir(__file__), 'data', 'pairings-display.txt')

    os.makedirs(os.path.dirname(filename), exist_ok=True)  # ensure data/ dir exists

    with open(filename, 'w', newline='') as file, open(filename_display, 'w') as f:
        writer = csv.writer(file)
        writer.writerow(["round_id", "player1_id", "player1_name", "player1_score", "player2_score", "player2_name", "player2_id"])

        for pair in sorted_pairs:
            player1 = pair[0]
            player2 = pair[1]

            if player2 == "BYE":
                row = [round_id, player1.id, player1.name, "BYE", "_", "_", "_"]
                row_display = f"{player1.name} has a BYE\n"
            else:
                row = [round_id, player1.id, player1.name, "?", "?", player2.name, player2.id]
                row_display = f'{player1.name} ?  -  ? {player2.name}\n'

            writer.writerow(row)
            f.write(row_display)

    logger.info(f"Pairings CSV file generated successfully: {filename}")

if __name__ == '__main__':
    conn_string = get_connection_string()

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--conn',
                        help='PostgreSQL connection string',
                        default=conn_string)
    args = parser.parse_args()

    # Connect to the database
    conn = psycopg2.connect(args.conn)

    active_players = get_active_players(conn)

    max_rounds = roundrobin_round_count(len(active_players))
    
    all_rounds = round_robin_pairing(active_players)
    
    for r, matches in enumerate(all_rounds, 1):
        generate_pairings_csv(matches, r)

    # Close database connection
    conn.close()