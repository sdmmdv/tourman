"""
test_cli.py — functional tests for the tourman CLI
Place at: src/tests/test_cli.py

Run:
    pytest src/tests/test_cli.py -v --tb=short --timeout=30
"""

import os
import csv
import pytest
import psycopg2

DATA = os.path.join(os.getcwd(), "data")


def _conn():
    from common.db_utils import get_connection_string
    return psycopg2.connect(get_connection_string())


def _scalar(sql, params=None):
    conn = _conn()
    with conn.cursor() as cur:
        cur.execute(sql, params or ())
        val = cur.fetchone()[0]
    conn.close()
    return val


def _csv(filename):
    with open(os.path.join(DATA, filename), newline="") as f:
        return list(csv.DictReader(f))


@pytest.fixture(scope="session", autouse=True)
def session_setup(fresh_database, num_players):
    from core.generate_players import main as gen_players
    from core.register_players import main as reg_players
    from core.register_standings import main as reg_standings
    gen_players(num_players)
    reg_players()
    reg_standings()


# ─────────────────────────────────────────────────────────────────────────────
# 1. init-db
# ─────────────────────────────────────────────────────────────────────────────

class TestInitDb:

    @pytest.mark.parametrize("table", ["players", "results", "standings"])
    def test_table_exists(self, session_setup, table):
        exists = _scalar(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s);",
            (table,),
        )
        assert exists, f"Table '{table}' was not created"

    def test_players_registered(self, session_setup, num_players):
        assert _scalar("SELECT COUNT(*) FROM players;") == num_players

    def test_standings_registered(self, session_setup, num_players):
        assert _scalar("SELECT COUNT(*) FROM standings;") == num_players

    def test_results_empty(self, session_setup):
        assert _scalar("SELECT COUNT(*) FROM results;") == 0


# ─────────────────────────────────────────────────────────────────────────────
# 2. generate-players
# ─────────────────────────────────────────────────────────────────────────────

class TestGeneratePlayers:

    def test_players_csv_created(self, session_setup):
        assert os.path.exists(os.path.join(DATA, "players.csv"))

    def test_correct_number_of_rows(self, session_setup, num_players):
        assert len(_csv("players.csv")) == num_players

    def test_required_columns_present(self, session_setup):
        assert {"id", "name", "email"} <= _csv("players.csv")[0].keys()

    def test_no_blank_fields(self, session_setup):
        for row in _csv("players.csv"):
            for col in ("id", "name", "email"):
                assert row[col].strip(), f"Blank '{col}' in row: {row}"

    def test_all_ids_unique(self, session_setup):
        ids = [r["id"] for r in _csv("players.csv")]
        assert len(ids) == len(set(ids)), "Duplicate player IDs found"


# ─────────────────────────────────────────────────────────────────────────────
# 3. register-players
# ─────────────────────────────────────────────────────────────────────────────

class TestRegisterPlayers:

    def test_all_players_inserted(self, session_setup, num_players):
        assert _scalar("SELECT COUNT(*) FROM players;") == num_players


# ─────────────────────────────────────────────────────────────────────────────
# 4. register-standings
# ─────────────────────────────────────────────────────────────────────────────

class TestRegisterStandings:

    def test_one_standing_row_per_player(self, session_setup, num_players):
        assert _scalar("SELECT COUNT(*) FROM standings;") == num_players

    def test_initial_points_all_zero(self, session_setup):
        assert float(_scalar("SELECT SUM(points) FROM standings;")) == 0.0

    def test_initial_matches_all_zero(self, session_setup):
        assert _scalar("SELECT COUNT(*) FROM standings WHERE matches != 0;") == 0

    def test_all_players_active(self, session_setup, num_players):
        assert _scalar("SELECT COUNT(*) FROM standings WHERE is_active = TRUE;") == num_players

    def test_all_bye_flags_false(self, session_setup, num_players):
        assert _scalar("SELECT COUNT(*) FROM standings WHERE is_bye = FALSE;") == num_players


# ─────────────────────────────────────────────────────────────────────────────
# 5. generate-swiss-pairings (round 1)
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateSwissPairings:
    ROUND = 1

    @pytest.fixture(scope="class", autouse=True)
    @classmethod
    def run(cls, session_setup):
        from core.generate_swiss_pairings import main as gen
        gen(cls.ROUND)

    def test_pairings_csv_created(self):
        assert os.path.exists(os.path.join(DATA, f"pairings_r{self.ROUND}.csv"))

    def test_correct_pairing_count(self, num_players):
        assert len(_csv(f"pairings_r{self.ROUND}.csv")) == num_players // 2

    def test_no_player_appears_twice(self):
        seen = set()
        for row in _csv(f"pairings_r{self.ROUND}.csv"):
            p1, p2 = row["player1_id"], row["player2_id"]
            assert p1 not in seen, f"{p1} appears twice"
            seen.add(p1)
            if p2:
                assert p2 not in seen, f"{p2} appears twice"
                seen.add(p2)

    def test_no_self_pairing(self):
        for row in _csv(f"pairings_r{self.ROUND}.csv"):
            if row["player2_id"]:
                assert row["player1_id"] != row["player2_id"]

    def test_score_placeholders_are_question_marks(self):
        for row in _csv(f"pairings_r{self.ROUND}.csv"):
            if row["player1_score"] != "BYE":
                assert row["player1_score"] == "?"
                assert row["player2_score"] == "?"


# ─────────────────────────────────────────────────────────────────────────────
# 6. populate-results
# ─────────────────────────────────────────────────────────────────────────────

class TestPopulateResults:
    ROUND = 1

    @pytest.fixture(scope="class", autouse=True)
    @classmethod
    def run(cls, session_setup):
        from utils.populate_results import main as populate
        populate(os.path.join(DATA, f"pairings_r{cls.ROUND}.csv"))

    def test_results_csv_created(self):
        assert os.path.exists(os.path.join(DATA, f"results_r{self.ROUND}.csv"))

    def test_no_question_marks_remain(self):
        for row in _csv(f"results_r{self.ROUND}.csv"):
            assert row["player1_score"] != "?"
            assert row["player2_score"] != "?"

    def test_scores_are_valid_values(self):
        valid = {"0.0", "0.5", "1.0", "BYE"}
        for row in _csv(f"results_r{self.ROUND}.csv"):
            assert row["player1_score"] in valid
            if row["player1_score"] != "BYE":
                assert row["player2_score"] in valid

    def test_scores_sum_to_one(self):
        for row in _csv(f"results_r{self.ROUND}.csv"):
            if row["player1_score"] == "BYE":
                continue
            total = float(row["player1_score"]) + float(row["player2_score"])
            assert total == 1.0, f"Scores don't sum to 1.0: {row}"

    def test_round_id_correct(self):
        for row in _csv(f"results_r{self.ROUND}.csv"):
            assert int(row["round_id"]) == self.ROUND


# ─────────────────────────────────────────────────────────────────────────────
# 7. print-table
# ─────────────────────────────────────────────────────────────────────────────

class TestPrintTable:

    @pytest.mark.parametrize("table", ["standings", "results", "players"])
    def test_print_does_not_raise(self, session_setup, table):
        from utils.print_table import main as print_table
        try:
            print_table(table, None)
        except SystemExit as e:
            pytest.fail(f"print-table '{table}' called sys.exit({e.code})")