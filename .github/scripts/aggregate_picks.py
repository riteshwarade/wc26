"""
aggregate_picks.py
Reads all individual pick CSVs from picks/group/swiftly/ and picks/group/fandf/,
combines them into data/group_swiftly_picks.json and data/group_fandf_picks.json
for use by the leaderboard pages.
"""

import csv
import glob
import json
import os

# Match number → (team1, team2)
MATCH_TEAMS = {
    1: ('Mexico', 'South Africa'),          2: ('South Korea', 'Czech Republic'),
    3: ('Canada', 'Bosnia and Herzegovina'), 4: ('United States', 'Paraguay'),
    5: ('Haiti', 'Scotland'),               6: ('Australia', 'Turkey'),
    7: ('Brazil', 'Morocco'),               8: ('Qatar', 'Switzerland'),
    9: ('Ivory Coast', 'Ecuador'),          10: ('Germany', 'Curaçao'),
    11: ('Netherlands', 'Japan'),           12: ('Sweden', 'Tunisia'),
    13: ('Saudi Arabia', 'Uruguay'),        14: ('Spain', 'Cape Verde'),
    15: ('Iran', 'New Zealand'),            16: ('Belgium', 'Egypt'),
    17: ('France', 'Senegal'),              18: ('Iraq', 'Norway'),
    19: ('Argentina', 'Algeria'),           20: ('Austria', 'Jordan'),
    21: ('Ghana', 'Panama'),                22: ('England', 'Croatia'),
    23: ('Portugal', 'DR Congo'),           24: ('Uzbekistan', 'Colombia'),
    25: ('Czech Republic', 'South Africa'),        26: ('Switzerland', 'Bosnia and Herzegovina'),
    27: ('Canada', 'Qatar'),                28: ('Mexico', 'South Korea'),
    29: ('Brazil', 'Haiti'),                30: ('Scotland', 'Morocco'),
    31: ('Turkey', 'Paraguay'),             32: ('United States', 'Australia'),
    33: ('Germany', 'Ivory Coast'),         34: ('Ecuador', 'Curaçao'),
    35: ('Netherlands', 'Sweden'),          36: ('Tunisia', 'Japan'),
    37: ('Uruguay', 'Cape Verde'),          38: ('Spain', 'Saudi Arabia'),
    39: ('Belgium', 'Iran'),                40: ('New Zealand', 'Egypt'),
    41: ('Norway', 'Senegal'),              42: ('France', 'Iraq'),
    43: ('Argentina', 'Austria'),           44: ('Jordan', 'Algeria'),
    45: ('England', 'Ghana'),               46: ('Panama', 'Croatia'),
    47: ('Portugal', 'Uzbekistan'),         48: ('Colombia', 'DR Congo'),
    49: ('Scotland', 'Brazil'),             50: ('Morocco', 'Haiti'),
    51: ('Switzerland', 'Canada'),          52: ('Bosnia and Herzegovina', 'Qatar'),
    53: ('Czech Republic', 'Mexico'),              54: ('South Africa', 'South Korea'),
    55: ('Curaçao', 'Ivory Coast'),         56: ('Ecuador', 'Germany'),
    57: ('Japan', 'Sweden'),                58: ('Tunisia', 'Netherlands'),
    59: ('Turkey', 'United States'),        60: ('Paraguay', 'Australia'),
    61: ('Norway', 'France'),               62: ('Senegal', 'Iraq'),
    63: ('Egypt', 'Iran'),                  64: ('New Zealand', 'Belgium'),
    65: ('Cape Verde', 'Saudi Arabia'),     66: ('Uruguay', 'Spain'),
    67: ('Panama', 'England'),              68: ('Croatia', 'Ghana'),
    69: ('Algeria', 'Austria'),             70: ('Jordan', 'Argentina'),
    71: ('Colombia', 'Portugal'),           72: ('DR Congo', 'Uzbekistan'),
}


def name_from_filename(filename, pool_id):
    base = os.path.basename(filename)
    prefix = f'wc26group_{pool_id}_'
    name_part = base.replace(prefix, '').replace('.csv', '')
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
                elif label == f'{t1} win':
                    outcome = 'W1'
                elif label == f'{t2} win':
                    outcome = 'W2'
                else:
                    continue
                picks[match_num] = outcome
            except (ValueError, IndexError):
                continue
    return picks


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
