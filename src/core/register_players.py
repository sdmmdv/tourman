#!/usr/bin/env python3

import csv
import psycopg2
from pathlib import Path
import argparse
import subprocess
import os

from common.db_utils import get_connection_string
from common.logger import get_logger
from common.common import root_dir

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

if __name__ == '__main__':
    conn_string = get_connection_string()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--conn',
                        help='PostgreSQL connection string',
                        default=conn_string)
    parser.add_argument('--csv-file',
                        help='CSV file containing player data',
                        default=os.path.join(root_dir(__file__), 'data/players.csv'))
    args = parser.parse_args()

    # Connect to the database
    conn = psycopg2.connect(args.conn)

    # Register players from CSV file
    register_players(conn, args.csv_file)

    # Close database connection
    conn.close()