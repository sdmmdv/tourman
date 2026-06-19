#!/usr/bin/env python3
import os
import psycopg2
from importlib.resources import files

from common.db_utils import get_connection_string
from common.logger import get_logger

logger = get_logger(__name__)


def execute_sql_file(conn, sql_text, label):
    with conn.cursor() as cur:
        cur.execute(sql_text)
        if conn.notices:
            for notice in conn.notices:
                logger.info(notice.strip())
            conn.notices.clear()
    conn.commit()
    logger.info(f"{label} executed.")


def main():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "tournament"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        logger.info("Connection to the database was successful.")
    except Exception as err:
        logger.error(f"Failed to connect to the database: {err}")
        exit(1)

    try:
        # Load SQL files from the installed 'db' package — path-independent
        execute_sql_file(conn, files("db").joinpath("schema_permissions.sql").read_text(), "schema_permissions.sql")
        execute_sql_file(conn, files("db").joinpath("tables.sql").read_text(),             "tables.sql")
        execute_sql_file(conn, files("db").joinpath("table_permissions.sql").read_text(),  "table_permissions.sql")
    finally:
        conn.close()


if __name__ == "__main__":
    main()