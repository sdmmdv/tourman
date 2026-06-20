#!/usr/bin/env python3

import psycopg2
import argparse
import sys
import os

from common.db_utils import get_connection_string
from common.logger import get_logger

logger = get_logger(__name__)

def apply_scores_to_standings(conn, round_id):
    try:
        with conn.cursor() as cur:
            # Fetch all the results from the results table
            cur.execute("SELECT * FROM results WHERE round_id = %s", (round_id,))
            results = cur.fetchall()
            if not results:
                raise ValueError(f"Round ID {round_id} does not exist in the table")

            #Make sure to not apply duplicate rounds
            cur.execute("SELECT MAX(matches) FROM standings;")
            max_matches = cur.fetchone()[0] or 0
            if not (round_id > max_matches):
                raise ValueError(f"Round {round_id} already applied (matches = {max_matches})")


            # Apply the scores to the standings table
            for result in results:
                round_id = result[0]
                player1_id = result[1]
                player1_score = result[3]
                player2_score = result[4]
                player2_id = result[6]

                # Update number of matches played
                cur.execute("UPDATE standings SET matches = matches + 1 WHERE id IN (%s, %s)", (player1_id, player2_id))

                # Update player1's score in standings table
                cur.execute("UPDATE standings SET points = points + %s WHERE id = %s", (player1_score, player1_id))

                # Check if player2_id are empty
                if player2_id != None:
                    # Update player2's score in standings table
                    cur.execute("UPDATE standings SET points = points + %s WHERE id = %s", (player2_score, player2_id))
                else:
                    # Store is_bye to standings
                    cur.execute(f"UPDATE standings SET is_bye = 'true' WHERE id = '{player1_id}'")

            # Commit the changes to the database
            conn.commit()
            logger.info("Record applied successfully")

    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


def apply_buchholz_tiebreak(conn):
    """
    Calculate and apply Buchholz tie-breaker (sum of opponents' total points).
    Excludes BYE matches and ensures no duplicates.
    """
    try:
        with conn.cursor() as cur:
            # Get all players
            cur.execute("SELECT id, name FROM standings")
            players = cur.fetchall()

            for player_id, player_name in players:
                # Get valid opponents (exclude BYE)
                cur.execute("""
                    SELECT DISTINCT
                        CASE
                            WHEN player1_id = %s THEN player2_id
                            WHEN player2_id = %s THEN player1_id
                        END AS opponent_id
                    FROM results
                    WHERE (player1_id = %s OR player2_id = %s)
                      AND (player1_id IS NOT NULL AND player2_id IS NOT NULL)
                      AND (
                        CASE
                            WHEN player1_id = %s THEN player2_id
                            WHEN player2_id = %s THEN player1_id
                        END
                      ) IS NOT NULL;
                """, [player_id] * 6)

                opponent_ids = [row[0] for row in cur.fetchall() if row[0] is not None]

                if not opponent_ids:
                    buchholz_score_sum = 0
                else:
                    cur.execute("""
                        SELECT COALESCE(SUM(points), 0)
                        FROM standings
                        WHERE id = ANY(%s);
                    """, (opponent_ids,))
                    buchholz_score_sum = cur.fetchone()[0]

                cur.execute("""
                    UPDATE standings
                    SET tiebreaker_a = %s
                    WHERE id = %s;
                """, (buchholz_score_sum, player_id))

                logger.debug(f"Buchholz updated: {player_name} ({player_id}) = {buchholz_score_sum}")

            conn.commit()
            logger.info("Buchholz tie-breaker recalculated successfully.")

    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Error in Buchholz computation: {e}")
        raise


def main(round_id: int, conn_string=None):
    if conn_string is None:
        conn_string = get_connection_string()

    conn = psycopg2.connect(conn_string)
    apply_scores_to_standings(conn, round_id)
    apply_buchholz_tiebreak(conn)
    conn.close()


if __name__ == '__main__':
    conn_string = get_connection_string()
    parser = argparse.ArgumentParser()
    parser.add_argument('--conn', default=conn_string)
    parser.add_argument("-r", "--round-id", type=int, required=True)
    args = parser.parse_args()
    main(args.round_id, args.conn)
