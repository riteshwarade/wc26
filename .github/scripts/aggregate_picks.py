"""
aggregate_picks.py
Reads all individual pick CSVs from:
  picks/group/swiftly/   → data/group_swiftly_picks.json
  picks/group/fandf/     → data/group_fandf_picks.json
  picks/knockout/swiftly/ → data/knockout_swiftly_picks.json
  picks/knockout/fandf/   → data/knockout_fandf_picks.json
"""

import csv
import glob
import json
import os
import sys

# parse_results.py is in the same directory — import canonical match data from it.
sys.path.insert(0, os.path.dirname(__file__))
from parse_results import GROUP_MATCHES

# Match number → (team1, team2) — auto-derived from canonical GROUP_MATCHES.
MATCH_TEAMS = {num: (t1, t2) for num, grp, t1, t2 in GROUP_MATCHES}


def name_from_filename(filename, pool_id):
    """Extract participant name from a group picks CSV filename."""
    base = os.path.basename(filename)
    prefix = f'wc26group_{pool_id}_'
    name_part = base.replace(prefix, '').replace('.csv', '')
    return name_part.replace('-', ' ').title()


def name_from_knockout_filename(filename):
    """Extract participant name from a knockout picks CSV filename.
    Expected pattern: wc26_knockout_firstname-lastname.csv
    """
    base = os.path.basename(filename)
    name_part = base.replace('wc26_knockout_', '').replace('.csv', '')
    return name_part.replace('-', ' ').title()


def load_picks_csv(filepath, match_teams):
    picks = {}
    with open(filepath, newline='', encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) < 3:
                continue
            try:
                match_num = int(row[0])
                label = row[2].strip()
                t1, t2 = match_teams.get(match_num, ('', ''))
                if label == 'Draw':
                    outcome = 'Draw'
                elif label == t1:
                    outcome = 'W1'
                elif label == t2:
                    outcome = 'W2'
                else:
                    continue
                picks[match_num] = outcome
            except (ValueError, IndexError):
                continue
    return picks


def load_knockout_csv(filepath):
    """Parse a knockout picks CSV (header: match,winner) into {match_num: winner_name}."""
    picks = {}
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i == 0 and len(row) >= 2 and row[0].strip().lower() == 'match':
                continue  # skip header row
            if len(row) < 2:
                continue
            try:
                match_num = int(row[0].strip())
                winner = row[1].strip()
                if winner:
                    picks[match_num] = winner
            except (ValueError, IndexError):
                continue
    return picks


def aggregate_knockout_pool(pool_id):
    """Aggregate all knockout pick CSVs for a given pool into a dict."""
    picks_dir = f'picks/knockout/{pool_id}'
    if not os.path.exists(picks_dir):
        print(f'  No picks directory: {picks_dir}')
        return {}

    all_picks = {}
    files = [f for f in glob.glob(f'{picks_dir}/*.csv')
             if not os.path.basename(f).startswith('.')]

    for filepath in sorted(files):
        name = name_from_knockout_filename(filepath)
        picks = load_knockout_csv(filepath)
        if picks:
            all_picks[name] = picks
            print(f'  Loaded {len(picks)} picks for {name}')

    return all_picks


def aggregate_pool(stage, pool_id):
    picks_dir = f'picks/{stage}/{pool_id}'
    if not os.path.exists(picks_dir):
        print(f'  No picks directory: {picks_dir}')
        return {}

    all_picks = {}
    files = [f for f in glob.glob(f'{picks_dir}/*.csv')
             if not os.path.basename(f).startswith('.')]

    for filepath in sorted(files):
        name = name_from_filename(filepath, pool_id)
        picks = load_picks_csv(filepath, MATCH_TEAMS)
        if picks:
            all_picks[name] = picks
            print(f'  Loaded {len(picks)} picks for {name}')

    return all_picks


def write_json(stage, pool_id, all_picks):
    os.makedirs('data', exist_ok=True)
    path = f'data/{stage}_{pool_id}_picks.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(all_picks, f, indent=2)
    print(f'Wrote {len(all_picks)} participants → {path}')


if __name__ == '__main__':
    for pool_id in ['swiftly', 'fandf']:
        print(f'\nAggregating group stage — {pool_id}...')
        picks = aggregate_pool('group', pool_id)
        write_json('group', pool_id, picks)

    for pool_id in ['swiftly', 'fandf']:
        print(f'\nAggregating knockout stage — {pool_id}...')
        picks = aggregate_knockout_pool(pool_id)
        write_json('knockout', pool_id, picks)
