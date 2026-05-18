"""
aggregate_picks.py
Reads all individual pick CSVs from picks/swiftly/ and picks/fandf/,
combines them into data/swiftly_picks.json and data/fandf_picks.json
for use by the leaderboard pages.
"""

import csv
import glob
import json
import os


def name_from_filename(filename, pool_id):
    """
    Convert filename to display name.
    e.g. wc26group_swiftly_john-smith.csv → John Smith
    """
    base = os.path.basename(filename)
    prefix = f'wc26group_{pool_id}_'
    name_part = base.replace(prefix, '').replace('.csv', '')
    return name_part.replace('-', ' ').title()


def load_picks_csv(filepath):
    """
    Load a picks CSV file and return a dict of {match_num: outcome}.
    Outcome is 'W1', 'Draw', or 'W2'.
    """
    picks = {}
    with open(filepath, newline='', encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) < 5:
                continue
            try:
                match_num = int(row[0])
                w1   = int(row[2])
                draw = int(row[3])
                w2   = int(row[4])
                if w1 == 1:
                    outcome = 'W1'
                elif draw == 1:
                    outcome = 'Draw'
                else:
                    outcome = 'W2'
                picks[match_num] = outcome
            except (ValueError, IndexError):
                continue
    return picks


def aggregate_pool(pool_id):
    """Aggregate all CSV picks for a pool into a single dict."""
    picks_dir = f'picks/{pool_id}'
    if not os.path.exists(picks_dir):
        print(f'  No picks directory: {picks_dir}')
        return {}

    all_picks = {}
    files = [f for f in glob.glob(f'{picks_dir}/*.csv')
             if not os.path.basename(f).startswith('.')]

    for filepath in sorted(files):
        name = name_from_filename(filepath, pool_id)
        picks = load_picks_csv(filepath)
        if picks:
            all_picks[name] = picks
            print(f'  Loaded {len(picks)} picks for {name}')

    return all_picks


def write_json(pool_id, all_picks):
    os.makedirs('data', exist_ok=True)
    path = f'data/{pool_id}_picks.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(all_picks, f, indent=2)
    print(f'Wrote {len(all_picks)} participants → {path}')


if __name__ == '__main__':
    for pool_id in ['swiftly', 'fandf']:
        print(f'\nAggregating {pool_id} picks...')
        picks = aggregate_pool(pool_id)
        write_json(pool_id, picks)
