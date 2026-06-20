#!/usr/bin/env python3

import csv
import psycopg2
from pathlib import Path
import argparse
import os

from common.db_utils import get_connection_string
from common.logger import get_logger

logger = get_logger(__name__)


def register_players(conn, csv_file):
    try:
        with conn.cursor() as cur:
            with open(csv_file, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    cur.execute("""
                        INSERT INTO players (id, name, email) 
                        VALUES (%s, %s, %s)
                    """, (row['id'], row['name'], row['email']))
        conn.commit()
        logger.info("All players registered successfully.")
    except Exception as err:
        conn.rollback()
        logger.error("An unexpected error occurred. Rolled back all changes.")
        logger.error(f"Reason: {err}")


def main(conn_string=None, csv_file=None):
    if conn_string is None:
        conn_string = get_connection_string()

    if csv_file is None:
        csv_file = os.path.join(os.getcwd(), 'data', 'players.csv')

    conn = psycopg2.connect(conn_string)
    register_players(conn, csv_file)
    conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--conn', default=get_connection_string())
    parser.add_argument('--csv-file', default=os.path.join(os.getcwd(), 'data', 'players.csv'))
    args = parser.parse_args()
    main(args.conn, args.csv_file)