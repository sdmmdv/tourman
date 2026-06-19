#!/usr/bin/env python3

from pathlib import Path
import argparse
import psycopg2
import csv
import os
import sys

from common.db_utils import get_connection_string
from common.logger import get_logger
from common.common import root_dir

logger = get_logger(__name__)


def get_max_round_id(conn) -> int:
    """Return the maximum round_id from results table (0 if empty)."""
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(MAX(round_id), 0) FROM results;")
        return cur.fetchone()[0]

def check_inputs(conn, round_id, player1_id, player1_name, player2_name, player2_id, max_round_id):
    with conn.cursor() as cur:
        # --- Guard 2: Check player identities ---
        cur.execute("SELECT 1 FROM standings WHERE id = %s AND name = %s;",
                    (player1_id, player1_name))
        if not cur.fetchone():
            raise ValueError(f"Player mismatch: {player1_id} - {player1_name} not found in standings.")

        # If the player1 was set to bye, naturally bypass empty player2 attributes
        if not (player2_name == None and player2_id == None):
            cur.execute("SELECT 1 FROM standings WHERE id = %s AND name = %s;",
                        (player2_id, player2_name))
            if not cur.fetchone():
                raise ValueError(f"Player mismatch: {player2_id} - {player2_name} not found in standings.")

        if round_id != max_round_id + 1:
            raise ValueError(
                f"Invalid round {round_id}: next allowed round is {max_round_id + 1}."
            )    

def store_results(input_file, conn):
    max_round_id = get_max_round_id(conn)
    cur = None
    try:
        cur = conn.cursor()
        with open(input_file, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                round_id = int(row['round_id'])
                player1_id = row['player1_id']
                player1_name = row['player1_name']
                player1_score = row['player1_score']
                player2_score = row['player2_score']
                player2_name = row['player2_name']
                player2_id = row['player2_id']
                
                # A player score set to BYE means that he\she has having a resting round.
                # As there are no matches he gets auto Win a.k.a 1.0 points
                if player1_score == 'BYE':
                    player1_score = 1.0
                    player2_score, player2_name, player2_id = '0.0', None, None
                else:
                    row_output = ','.join([str(round_id), player1_id, player1_name, player1_score, player2_score, player2_name, player2_id])
                    try:
                        player1_score = float(player1_score)
                        if player1_score not in [0.5, 0.0, 1.0]:
                            raise ValueError('Invalid player1_score')
                    except ValueError:
                        logger.error(f'Invalid player2_score: {player1_score}\n{row_output}')                       
                        conn.rollback()
                        sys.exit(1)

                    try:
                        player2_score = float(player2_score)
                        if player2_score not in [0.5, 0.0, 1.0]:
                            raise ValueError('Invalid player2_score')
                    except ValueError:
                        logger.error(f'Invalid player2_score: {player2_score}\n{row_output}')
                        conn.rollback()
                        sys.exit(1)

                    try:
                        if player1_score + player2_score != 1.0:
                            msg = 'Sum of player scores must be 1.0'
                            raise ValueError(msg)
                    except ValueError:
                        logger.error(f'Invalid sum of players! {msg}\n{row_output}')
                        conn.rollback()
                        sys.exit(1)
                
                check_inputs(conn, round_id, player1_id, player1_name, player2_name, player2_id, max_round_id)

                cur.execute("INSERT INTO results (round_id, player1_id, player1_name, player1_score, player2_score, player2_name, player2_id) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (round_id, player1_id, player1_name, player1_score, player2_score, player2_name, player2_id))

        logger.info("Results stored successfully.")
        conn.commit()
    except (psycopg2.Error, FileNotFoundError) as e:
        if conn is not None:
            conn.rollback()
        logger.error(f"Error: {str(e)}")
    finally:
        if cur is not None:
            cur.close()


def main():
    conn_string = get_connection_string()

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--conn', 
                        help='PostgreSQL connection string',
                        default=conn_string)
    parser.add_argument('-f',
                        '--input-file',
                        required=True,
                        help=f'Results csv input file (default: %(default)s)')
    args = parser.parse_args()

    # Connect to the database
    conn = psycopg2.connect(args.conn)


    store_results(args.input_file, conn)

    # Close database connection
    conn.close()

if __name__ == '__main__':
    main()