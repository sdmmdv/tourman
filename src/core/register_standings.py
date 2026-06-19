#!/usr/bin/env python3

import psycopg2
import argparse
import random
import time
import os

from common.db_utils import get_connection_string
from common.logger import get_logger

logger = get_logger(__name__)

# Populate standings table based on players list and default values.
def fill_standings_table(conn):
    with conn.cursor() as cur:
        # Select all the id and name values from the Players table
        cur.execute("SELECT id, name FROM Players")
        # Insert each row into the Standings table with the default values
        for row in cur.fetchall():
            # dn1 = generate_decimal_number()
            # dn2 = generate_decimal_number()
            # dn3 = generate_decimal_number()
            # p = generate_decimal_number()
            # print(dn1,dn2,dn3,p)
            if row[0] != '_':
                cur.execute("""
                    INSERT INTO Standings (id, name, is_active, is_bye, matches, tiebreaker_C, tiebreaker_B, tiebreaker_A, points)
                    VALUES (%s, %s, true, false, %s, %s, %s, %s, %s)
                """, (row[0], row[1], 0, 0.00, 0.00, 0.00, 0.0))

        conn.commit()
        logger.info("Standings table filled successfully")


def generate_decimal_number():
    random.seed(time.time())
    decimal_number = round(random.uniform(0.0, 10.0), 1)
    while decimal_number % 0.5 != 0:
        decimal_number = round(random.uniform(0.0, 10.0), 1)
    return decimal_number

def main():
    dbname=os.getenv("DB_NAME")
    user=os.getenv("DB_USER")
    password=os.getenv("DB_PASS")
    host=os.getenv("DB_HOST", "localhost")
    port=os.getenv("DB_PORT", "5432")
    
    required_vars = [dbname, user, password, host, port]
    if not all(required_vars):
        raise ValueError("One or more required environment variables are missing.")

    conn_string = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    
    conn = psycopg2.connect(conn_string)

    # Fill the tables
    fill_standings_table(conn)

if __name__ == '__main__':
    main()
