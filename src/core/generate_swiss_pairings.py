#!/usr/bin/env python3

import psycopg2
import argparse
import csv
import os
import math

from core.player import Player
from common.db_utils import get_connection_string
from common.logger import get_logger

logger = get_logger(__name__)


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


def validate_new_round(conn, max_round_count, round_id: int):
    if max_round_count == 0:
        raise ValueError(
            f"No players are registered in the standings table. "
            f"Cannot start or validate round {round_id} for swiss tournament."
        )
    if round_id > max_round_count:
        raise ValueError(
            f"Invalid round {round_id}! swiss tournament is limited to maximum {max_round_count} rounds."
        )
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(MAX(round_id), 0) FROM results;")
        max_round_id = cur.fetchone()[0]
    if round_id <= max_round_id:
        raise ValueError(
            f"Invalid round {round_id}: must be greater than last applied round {max_round_id}."
        )
    if round_id != max_round_id + 1:
        raise ValueError(
            f"Invalid round {round_id}: Last round was {max_round_id}, next round must be {max_round_id + 1}!"
        )
    logger.info(f"Round {round_id} is valid (previous max round = {max_round_id})")
    return True


def fetch_played_opponents(conn, player_id):
    opponents = set()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT player1_id, player2_id
            FROM results
            WHERE player1_id = %s OR player2_id = %s
        """, (player_id, player_id))
        for row in cur.fetchall():
            opponent1_id, opponent2_id = row
            if opponent1_id and opponent1_id != player_id:
                opponents.add(opponent1_id)
            if opponent2_id and opponent2_id != player_id:
                opponents.add(opponent2_id)
    return opponents


def create_head_to_head_map(conn):
    map_of_opponents = {}
    with conn.cursor() as cur:
        cur.execute("SELECT player1_id, player2_id FROM results")
        for row in cur.fetchall():
            opponent1_id, opponent2_id = row
            if opponent1_id:
                if opponent1_id not in map_of_opponents:
                    map_of_opponents[opponent1_id] = set()
                map_of_opponents[opponent1_id].add(opponent2_id)
            if opponent2_id:
                if opponent2_id not in map_of_opponents:
                    map_of_opponents[opponent2_id] = set()
                map_of_opponents[opponent2_id].add(opponent1_id)
    return map_of_opponents


def have_played_before(head_to_head_map, player1_id, player2_id):
    return player1_id in head_to_head_map and player2_id in head_to_head_map[player1_id]


def swiss_pairing(conn, players):
    head_to_head_map = create_head_to_head_map(conn)
    paired_players = set()
    pairings = []

    for i in range(len(players) - 1, -1, -1):
        player = players[i]
        if player.is_bye and player.id not in paired_players:
            left_player = player
            paired_players.add(player.id)
            for j in range(i - 1, -1, -1):
                opponent = players[j]
                if not opponent.is_bye and opponent.id not in paired_players and \
                   not have_played_before(head_to_head_map, left_player.id, opponent.id):
                    pairings.append((left_player, opponent))
                    paired_players.add(opponent.id)
                    logger.debug(f"{left_player.id} {left_player.name} - {opponent.name} {opponent.id}")
                    break
            else:
                for j in range(i, len(players)):
                    opponent = players[j]
                    if not opponent.is_bye and opponent.id not in paired_players and \
                       not have_played_before(head_to_head_map, left_player.id, opponent.id):
                        pairings.append((left_player, opponent))
                        paired_players.add(opponent.id)
                        logger.debug(f"{left_player.id} {left_player.name} - {opponent.name} {opponent.id}")
                        break

    for i, left_player in enumerate(players):
        if left_player.id in paired_players:
            continue
        paired_players.add(left_player.id)
        paired = False

        for j, right_player in enumerate(players[i:], start=i):
            if right_player.id in paired_players:
                continue
            if not have_played_before(head_to_head_map, left_player.id, right_player.id):
                pairings.append((left_player, right_player))
                paired_players.add(right_player.id)
                paired = True
                logger.debug(f"{left_player.id} {left_player.name} - {right_player.name} {right_player.id}")
                break
            if j == len(players) - 1:
                for k in range(len(pairings) - 1, -1, -1):
                    player1, player2 = pairings[k]
                    id1, id2 = player1.id, player2.id
                    if not have_played_before(head_to_head_map, left_player.id, id2) and \
                       not have_played_before(head_to_head_map, id1, right_player.id):
                        pairings[k] = (player1, right_player)
                        pairings.append((left_player, player2))
                        paired_players.add(right_player.id)
                        paired = True
                        logger.debug(f"Swap pairing: {id1}-{right_player.id}, {left_player.id}-{player2.id}")
                        break
                    elif not have_played_before(head_to_head_map, left_player.id, id1) and \
                         not have_played_before(head_to_head_map, right_player.id, id2):
                        pairings[k] = (player1, left_player)
                        pairings.append((right_player, player2))
                        paired_players.add(right_player.id)
                        paired = True
                        logger.debug(f"Swap pairing: {id1}-{left_player.id}, {right_player.id}-{player2.id}")
                        break
        if not paired:
            if left_player.is_bye:
                raise ValueError(f"Player {left_player.name} (ID {left_player.id}) has already received a BYE before!")
            pairings.append((left_player, 'BYE'))
            logger.debug(f"{left_player.id} {left_player.name} - BYE")

    return pairings


def round_robin_pairing(players):
    players = players[:]
    n = len(players)
    has_bye = False
    if n % 2 == 1:
        has_bye = True
        n += 1
    rounds = []
    for round_index in range(n - 1):
        round_pairs = []
        for i in range(n // 2):
            if has_bye and (i == 0 and round_index % n < len(players)):
                bye_player = players[(round_index + i) % len(players)]
                round_pairs.append((bye_player, 'BYE'))
                continue
            p1_index = (round_index + i) % len(players)
            p2_index = (round_index + n - 1 - i) % len(players)
            if p1_index == p2_index:
                continue
            p1 = players[p1_index]
            p2 = players[p2_index]
            if p1 != p2:
                round_pairs.append((p1, p2))
        rounds.append(round_pairs)
    return rounds


def generate_pairings_csv(sorted_pairs, round_id):
    data_dir = os.path.join(os.getcwd(), 'data')           # ← fixed: use CWD
    filename = os.path.join(data_dir, f'pairings_r{round_id}.csv')
    filename_display = os.path.join(data_dir, 'pairings-display.txt')
    os.makedirs(data_dir, exist_ok=True)

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


def get_player_count(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(id) FROM standings;")
        num_players = cur.fetchone()[0] or 0
    return num_players


def swiss_round_count(num_players: int, round_id: int) -> int:
    if num_players < 2:
        raise ValueError("Need at least 2 players for a tournament")
    recommended = math.ceil(math.log2(num_players))
    max_rounds = num_players // 2 if num_players % 2 == 0 else (num_players - 1) // 2
    if round_id > recommended:
        logger.warning(
            f"[Swiss pairing] Recommended rounds ≈ {recommended} "
            f"(based on log2({num_players})), but using up to {max_rounds} is acceptable."
        )
    return max_rounds


def main(round_id, conn_string=None):                      # ← new main()
    if conn_string is None:
        conn_string = get_connection_string()

    conn = psycopg2.connect(conn_string)

    active_players = get_active_players(conn)
    max_rounds = swiss_round_count(len(active_players), round_id)
    validate_new_round(conn, max_rounds, round_id)

    raw_pairs = swiss_pairing(conn, active_players)
    sorted_pairs = sorted(raw_pairs, key=lambda pair: pair[0].rank)
    generate_pairings_csv(sorted_pairs, round_id)

    conn.close()


if __name__ == '__main__':
    conn_string = get_connection_string()
    parser = argparse.ArgumentParser()
    parser.add_argument('--conn', default=conn_string)
    parser.add_argument("-r", "--round-id", type=int, required=True)
    args = parser.parse_args()
    main(args.round_id, args.conn)