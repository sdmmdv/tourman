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

    print(" rank |         name              | matches |  t2  |  t1  | points")
    print("------+---------------------------+---------+------+------+--------")
    for row in standings:
        print("{:5d} | {:25s} | {:7d} | {:.2f} | {:.2f} | {:6.1f}".format(
            row[0], row[1], row[2], row[3], row[4], row[5]))

    cur.close()

    df = pd.DataFrame(standings, columns=['rank', 'name', 'matches', 't2', 't1', 'points'])
    output_file = os.path.join(os.getcwd(), 'output.xlsx')
    df.to_excel(output_file, index=False)


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


def main(table=None, conn_string=None):       # ← new main()
    if conn_string is None:
        conn_string = get_connection_string()

    conn = psycopg2.connect(conn_string)

    function = globals().get(f"print_{table}")
    if function is None:
        raise ValueError(f"Unknown table: {table}")
    function(conn)

    conn.close()


if __name__ == '__main__':
    conn_string = get_connection_string()
    parser = argparse.ArgumentParser()
    parser.add_argument('--conn', default=conn_string)
    parser.add_argument("-t", "--table",
                        choices=['standings', 'results', 'players'],
                        required=True)
    args = parser.parse_args()
    main(args.table, args.conn)