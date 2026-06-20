# tourman

A command-line tournament management tool built in Python. Supports **Swiss** and **Round-Robin** pairing systems with a PostgreSQL-backed standings table, automatic Buchholz tiebreaker calculation, and Docker Compose support for easy deployment.

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
  - [Local (venv)](#local-venv)
  - [Docker Compose](#docker-compose)
- [Configuration](#configuration)
- [Database Schema](#database-schema)
- [Commands](#commands)
- [Tournament Workflows](#tournament-workflows)
  - [Swiss Tournament](#swiss-tournament)
  - [Round-Robin Tournament](#round-robin-tournament)
- [Scoring](#scoring)
- [Tiebreakers](#tiebreakers)
- [Project Structure](#project-structure)

---

## Requirements

- Python 3.11+
- PostgreSQL 15+
- pip
- Docker + Docker Compose (optional, for containerised setup)

---

## Installation

### Local (venv)

```bash
git clone https://github.com/sdmmdv/tourman.git
cd tourman

python3 -m venv .venv
source .venv/bin/activate

pip install .
```

For development — changes to source files take effect immediately without reinstalling:

```bash
pip install -e .
```

---

### Docker Compose

The repository ships with a `docker-compose.yml` that starts a PostgreSQL 15 database and a `tourman` application container.

**1. Start the services:**

```bash
docker compose up -d
```

This will:
- Start `tourman_db` — PostgreSQL 15 on port `5432`
- Start `tourman_app` — Python 3.11 container with `tourman` installed

**2. Open a shell in the app container:**

```bash
docker exec -it tourman_app bash
```

**3. Run commands inside the container:**

```bash
tourman init-db
tourman generate-players
tourman register-players
tourman register-standings
```

**4. Stop services:**

```bash
docker compose down
```

To also remove the database volume (⚠️ destroys all data):

```bash
docker compose down -v
```

---

## Configuration

`tourman` connects to PostgreSQL using environment variables. Set them in your shell or in a `.env` file:

```bash
export DB_NAME=tournament
export DB_USER=app_admin
export DB_PASS=admin_secure_pass
export DB_HOST=localhost       # default: localhost
export DB_PORT=5432            # default: 5432
```

When using Docker Compose, these variables are already set in the `app` service definition inside `docker-compose.yml`.

You can also override the connection string per-command with `--conn`:

```bash
tourman generate-swiss-pairings -r 1 --conn "postgresql://app_admin:admin_secure_pass@localhost:5432/tournament"
```

---

## Database Schema

Three tables are used:

### `Players`

| Column | Type | Description |
|--------|------|-------------|
| `id` | VARCHAR(25) PK | Unique player identifier |
| `name` | VARCHAR(255) | Full name |
| `email` | VARCHAR(255) | Email address |

### `Standings`

| Column | Type | Description |
|--------|------|-------------|
| `id` | VARCHAR(25) FK | References Players |
| `name` | VARCHAR(255) | Player name |
| `is_active` | BOOLEAN | Whether the player is active |
| `is_bye` | BOOLEAN | Whether the player received a BYE |
| `matches` | INTEGER | Number of matches played |
| `points` | DECIMAL(4,1) | Total score |
| `tiebreaker_A` | DECIMAL(8,2) | Buchholz score |
| `tiebreaker_B` | DECIMAL(8,2) | Reserved |
| `tiebreaker_C` | DECIMAL(8,2) | Reserved |

### `Results`

| Column | Type | Description |
|--------|------|-------------|
| `round_id` | INTEGER | Round number |
| `player1_id` | VARCHAR(25) FK | References Players |
| `player1_name` | VARCHAR(255) | Player 1 name |
| `player1_score` | DECIMAL(2,1) | Score: 0.0, 0.5, or 1.0 |
| `player2_score` | DECIMAL(2,1) | Score: 0.0, 0.5, or 1.0 |
| `player2_name` | VARCHAR(255) | Player 2 name (NULL for BYE) |
| `player2_id` | VARCHAR(25) FK | References Players (NULL for BYE) |

---

## Commands

### Setup Commands

| Command | Description |
|---------|-------------|
| `tourman init-db` | Create database tables and roles |
| `tourman generate-players [-n N]` | Generate `N` fake players (default: 10) |
| `tourman register-players` | Insert generated players into the DB |
| `tourman register-standings` | Initialise standings rows for all players |

### Tournament Commands

| Command | Description |
|---------|-------------|
| `tourman generate-swiss-pairings -r <N>` | Generate Swiss pairings for round N |
| `tourman generate-roundrobin-pairings` | Generate all Round-Robin pairings at once |
| `tourman populate-results -f <file>` | Fill a pairings CSV with random scores (testing) |
| `tourman register-results -f <file>` | Validate and insert a results CSV into the DB |
| `tourman apply-results -r <N>` | Apply round N results to the standings table |

### Utility Commands

| Command | Description |
|---------|-------------|
| `tourman print-table -t <table>` | Print `standings`, `results`, or `players` |
| `tourman convert-excel-to-csv` | Convert an Excel file to CSV |
| `tourman convert-table-to-excel` | Export DB tables to Excel |

### Global Flags

| Flag | Description |
|------|-------------|
| `-v`, `--verbose` | Enable DEBUG-level logging |
| `--conn <string>` | Override PostgreSQL connection string |

---

## Tournament Workflows

### Swiss Tournament

Swiss pairing matches players of similar scores each round. The number of recommended rounds is `ceil(log2(N))` where N is the player count.

**Full setup from scratch:**

```bash
tourman init-db
tourman generate-players -n 16
tourman register-players
tourman register-standings
```

**Run a single round manually:**

```bash
tourman generate-swiss-pairings -r 1
# Edit data/pairings_r1.csv with real scores, then:
tourman register-results -f data/results_r1.csv
tourman apply-results -r 1
tourman print-table -t standings
```

**Run 5 rounds automatically (with random scores for testing):**

```bash
for r in $(seq 1 5); do
    echo "=== Round $r ==="
    tourman generate-swiss-pairings -r $r &&
    tourman populate-results -f data/pairings_r$r.csv &&
    tourman register-results -f data/results_r$r.csv &&
    tourman apply-results -r $r
    tourman print-table -t standings
done
```

Or use the provided script:

```bash
bash runscript.sh
```

---

### Round-Robin Tournament

Every player faces every other player exactly once. For N players: N-1 rounds (even N) or N rounds (odd N, with rotating BYE).

**Full setup from scratch:**

```bash
tourman init-db
tourman generate-players -n 10
tourman register-players
tourman register-standings
```

**Generate all pairings at once:**

```bash
tourman generate-roundrobin-pairings
# Creates data/pairings_r1.csv through data/pairings_r9.csv (for 10 players)
```

**Run all rounds:**

```bash
for r in $(seq 1 9); do
    echo "=== Round $r ==="
    tourman populate-results -f data/pairings_r$r.csv &&
    tourman register-results -f data/results_r$r.csv &&
    tourman apply-results -r $r
    tourman print-table -t standings
done
```

> **Note:** Unlike Swiss, `generate-roundrobin-pairings` generates all rounds upfront. Do not re-run it between rounds.

---

## Scoring

| Outcome | player1_score | player2_score |
|---------|--------------|--------------|
| Player 1 wins | 1.0 | 0.0 |
| Draw | 0.5 | 0.5 |
| Player 2 wins | 0.0 | 1.0 |
| BYE (player 1 rests) | 1.0 | — |

Scores in the results CSV must sum to exactly `1.0`. Invalid scores are rejected by `register-results`.

---

## Tiebreakers

When players are equal on points, standings are ordered by:

1. **Points** — total accumulated score
2. **Tiebreaker A (Buchholz)** — sum of all opponents' total points; rewards playing stronger competition
3. **Tiebreaker B** — reserved for future use
4. **Tiebreaker C** — reserved for future use

Buchholz is recalculated automatically after every `apply-results` call.

---

## Project Structure

```
tourman/
├── src/
│   ├── main.py                              # CLI entry point — all commands routed here
│   ├── core/
│   │   ├── init_db.py                       # Database initialisation
│   │   ├── generate_players.py              # Fake player generation (Faker)
│   │   ├── register_players.py              # Insert players into DB
│   │   ├── register_standings.py            # Initialise standings rows
│   │   ├── generate_swiss_pairings.py       # Swiss pairing algorithm (O(n²))
│   │   ├── generate_roundrobin_pairings.py  # Circle-method round-robin
│   │   ├── register_results.py              # Validate and insert results CSV
│   │   └── apply_results_to_standings.py    # Update standings + Buchholz
│   ├── utils/
│   │   ├── populate_results.py              # Random score generator (testing)
│   │   ├── print_table.py                   # Console table printer
│   │   ├── convert_excel_to_csv.py
│   │   └── convert_table_to_excel.py
│   ├── common/
│   │   ├── db_utils.py                      # Connection string from env vars
│   │   ├── logger.py                        # Structured logging
│   │   └── common.py
│   └── db/
│       ├── tables.sql                       # CREATE TABLE statements
│       ├── roles.sql                        # DB roles and permissions
│       ├── schema_permissions.sql
│       └── table_permissions.sql
├── data/                                    # Runtime output — CSV pairings and results
├── docker-compose.yml                       # PostgreSQL + app services
├── tourman.Dockerfile
├── runscript.sh                             # End-to-end Swiss demo script
├── setup.py
├── pyproject.toml
└── README.md
```

---

## License

MIT — see [LICENSE](LICENSE).
