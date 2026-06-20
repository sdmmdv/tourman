#!/usr/bin/env bash

set -e
 
pip install --force-reinstall . --break-system-packages

tourman init-db
tourman generate-players
tourman register-players
tourman register-standings

# tourman generate-swiss-pairings -r 1
# tourman populate-results -f data/pairings_r1.csv
# tourman register-results -f data/results_r1.csv
# tourman apply-results -r 1

# Swiss pairing tournament
for r in $(seq 1 5); do
    echo "=== Round $r ==="
    tourman generate-swiss-pairings -r $r &&
    tourman populate-results -f data/pairings_r$r.csv &&
    tourman register-results -f data/results_r$r.csv &&
    tourman apply-results -r $r
    tourman print-table -t standings
done

# Round Robin tournament
# tourman generate-roundrobin-pairings
# for r in $(seq 1 9); do
#     echo "=== Round $r ==="
#     tourman populate-results -f data/pairings_r$r.csv &&
#     tourman register-results -f data/results_r$r.csv &&
#     tourman apply-results -r $r
#     tourman print-table -t standings
# done