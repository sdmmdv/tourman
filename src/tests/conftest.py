"""
conftest.py — shared fixtures for tourman functional tests
Place at: src/tests/conftest.py
"""

import os
import csv
import pytest
import psycopg2


@pytest.fixture(autouse=True, scope="session")
def set_working_directory():
    """chdir to project root so data/ and db/ paths resolve correctly."""
    root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    os.chdir(root)
    os.makedirs(os.path.join(root, "data"), exist_ok=True)


def get_conn():
    from common.db_utils import get_connection_string
    return psycopg2.connect(get_connection_string())


@pytest.fixture
def count_rows():
    def _count(table: str) -> int:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {table};")
            result = cur.fetchone()[0]
        conn.close()
        return result
    return _count


@pytest.fixture
def scalar():
    def _scalar(sql: str, params=None):
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            val = cur.fetchone()[0]
        conn.close()
        return val
    return _scalar


@pytest.fixture
def read_csv():
    def _read(filename: str) -> list:
        path = os.path.join(os.getcwd(), "data", filename)
        with open(path, newline="") as f:
            return list(csv.DictReader(f))
    return _read


@pytest.fixture(scope="session")
def num_players():
    return 10


@pytest.fixture(scope="session")
def fresh_database(set_working_directory):
    """Wipe and recreate DB schema once before all tests. Drop on teardown."""
    from core.init_db import main as init_db
    init_db()
    yield
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS Results   CASCADE;")
        cur.execute("DROP TABLE IF EXISTS Standings CASCADE;")
        cur.execute("DROP TABLE IF EXISTS Players   CASCADE;")
    conn.commit()
    conn.close()