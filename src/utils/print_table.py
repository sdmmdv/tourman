#!/usr/bin/env python3
import psycopg2
import argparse
import sys
import os
import pandas as pd

from common.db_utils import get_connection_string


def print_standings(conn):
    cur = conn.cursor()
    query = """
    SELECT
      ROW_NUMBER() OVER (ORDER BY points DESC, tiebreaker_A DESC, tiebreaker_B DESC, tiebreaker_C DESC) AS rank,
      name, matches, tiebreaker_B AS t2, tiebreaker_A as t1, points
    FROM
      Standings
    WHERE
      is_active = 'true'
    ORDER BY
      points DESC, tiebreaker_A DESC, tiebreaker_B DESC, tiebreaker_C DESC;
    """
    
    cur.execute(query)
    standings = cur.fetchall()

    # Print the results in PostgreSQL format
    print(" rank |         name              | matches |  t2  |  t1  | points")
    print("------+---------------------------+---------+------+------+--------")
    for row in standings:
        print("{:5d} | {:25s} | {:7d} | {:.2f} | {:.2f} | {:6.1f}".format(row[0], row[1], row[2], row[3], row[4], row[5]))
    
    cur.close()

    # Convert the query results to a pandas DataFrame
    df = pd.DataFrame(standings, columns=['rank', 'name', 'matches', 't2', 't1', 'points'])
    df.to_excel('output.xlsx', index=False)

def print_players(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, name, email FROM players")
    rows = cur.fetchall()
    print("{:<7} | {:<21} | {:<30}".format("id", "name", "email"))
    print("-" * 70)
    for row in rows:
        print("{:<7} | {:<21} | {:<30}".format(row[0], row[1], row[2]))
    print()

def print_results(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT round_id, player1_name, player1_score, player2_score, player2_name
        FROM results
        ORDER BY round_id;
    """)
    rows = cur.fetchall()
    print("{:<9} | {:<21} | {:<13} | {:<13} | {:<21}".format(
        "round_id", "player1_name", "player1_score", "player2_score", "player2_name"))
    print("-" * 100)
    for row in rows:
        safe_row = tuple("" if value is None else value for value in row)
        print("{:<9} | {:<21} | {:<13} | {:<13} | {:<21}".format(*safe_row))
    print()


if __name__ == '__main__':
    conn_string = get_connection_string()

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--conn', 
                        help='PostgreSQL connection string',
                        default=conn_string)
    parser.add_argument("-t",
                        "--table",
                        choices=['standings', 'results', 'players'],
                        required=True,
                        help="a PostgreSQL table")
    args = parser.parse_args()

    # Connect to the database
    conn = psycopg2.connect(args.conn)

    function_name = f"print_{args.table}"
    function = getattr(sys.modules[__name__], function_name)
    function(conn)

    # Close database connection
    conn.close()