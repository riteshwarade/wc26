"""
simulate.py
Generates simulated pick CSVs (all 72 matches) and match results for
end-to-end testing before the tournament begins.

Pick files are named simulation_1, simulation_2, etc. so they are easy
to identify and remove with clear_simulation.yml when testing is done.
You can also create your own test picks manually using the same naming pattern.

Usage:
  python simulate.py --participants 5
"""

import argparse
import csv
import os
import random

# ── Match data ────────────────────────────────────────────────────────────────
MATCHES = [
    (1,  'Mexico',                'South Africa'),
    (2,  'South Korea',           'Czech Republic'),
    (3,  'Canada',                'Bosnia and Herzegovina'),
    (4,  'United States',         'Paraguay'),
    (5,  'Haiti',                 'Scotland'),
    (6,  'Australia',             'Turkey'),
    (7,  'Brazil',                'Morocco'),
    (8,  'Qatar',                 'Switzerland'),
    (9,  'Ivory Coast',           'Ecuador'),
    (10, 'Germany',               'Curaçao'),
    (11, 'Netherlands',           'Japan'),
    (12, 'Sweden',                'Tunisia'),
    (13, 'Saudi Arabia',          'Uruguay'),
    (14, 'Spain',                 'Cape Verde'),
    (15, 'Iran',                  'New Zealand'),
    (16, 'Belgium',               'Egypt'),
    (17, 'France',                'Senegal'),
    (18, 'Iraq',                  'Norway'),
    (19, 'Argentina',             'Algeria'),
    (20, 'Austria',               'Jordan'),
    (21, 'Ghana',                 'Panama'),
    (22, 'England',               'Croatia'),
    (23, 'Portugal',              'DR Congo'),
    (24, 'Uzbekistan',            'Colombia'),
    (25, 'Czech Republic',               'South Africa'),
    (26, 'Switzerland',           'Bosnia and Herzegovina'),
    (27, 'Canada',                'Qatar'),
    (28, 'Mexico',                'South Korea'),
    (29, 'Brazil',                'Haiti'),
    (30, 'Scotland',              'Morocco'),
    (31, 'Turkey',                'Paraguay'),
    (32, 'United States',         'Australia'),
    (33, 'Germany',               'Ivory Coast'),
    (34, 'Ecuador',               'Curaçao'),
    (35, 'Netherlands',           'Sweden'),
    (36, 'Tunisia',               'Japan'),
    (37, 'Uruguay',               'Cape Verde'),
    (38, 'Spain',                 'Saudi Arabia'),
    (39, 'Belgium',               'Iran'),
    (40, 'New Zealand',           'Egypt'),
    (41, 'Norway',                'Senegal'),
    (42, 'France',                'Iraq'),
    (43, 'Argentina',             'Austria'),
    (44, 'Jordan',                'Algeria'),
    (45, 'England',               'Ghana'),
    (46, 'Panama',                'Croatia'),
    (47, 'Portugal',              'Uzbekistan'),
    (48, 'Colombia',              'DR Congo'),
    (49, 'Scotland',              'Brazil'),
    (50, 'Morocco',               'Haiti'),
    (51, 'Switzerland',           'Canada'),
    (52, 'Bosnia and Herzegovina','Qatar'),
    (53, 'Czech Republic',               'Mexico'),
    (54, 'South Africa',          'South Korea'),
    (55, 'Curaçao',               'Ivory Coast'),
    (56, 'Ecuador',               'Germany'),
    (57, 'Japan',                 'Sweden'),
    (58, 'Tunisia',               'Netherlands'),
    (59, 'Turkey',                'United States'),
    (60, 'Paraguay',              'Australia'),
    (61, 'Norway',                'France'),
    (62, 'Senegal',               'Iraq'),
    (63, 'Egypt',                 'Iran'),
    (64, 'New Zealand',           'Belgium'),
    (65, 'Cape Verde',            'Saudi Arabia'),
    (66, 'Uruguay',               'Spain'),
    (67, 'Panama',                'England'),
    (68, 'Croatia',               'Ghana'),
    (69, 'Algeria',               'Austria'),
    (70, 'Jordan',                'Argentina'),
    (71, 'Colombia',              'Portugal'),
    (72, 'DR Congo',              'Uzbekistan'),
]


def random_outcome():
    return random.choice(['W1', 'Draw', 'W2'])


def outcome_label(outcome, t1, t2):
    if outcome == 'W1':   return f'{t1} win'
    if outcome == 'Draw': return 'Draw'
    return f'{t2} win'


def random_score(outcome):
    if outcome == 'W1':
        h = random.randint(1, 4)
        a = random.randint(0, h - 1)
    elif outcome == 'W2':
        a = random.randint(1, 4)
        h = random.randint(0, a - 1)
    else:
        s = random.randint(0, 2)
        h = a = s
    return h, a


def generate_picks(pool_id, participant_num):
    folder = f'picks/group/{pool_id}'
    os.makedirs(folder, exist_ok=True)
    filename = f'{folder}/wc26group_{pool_id}_simulation-{participant_num}.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for num, t1, t2 in MATCHES:
            outcome = random_outcome()
            label   = outcome_label(outcome, t1, t2)
            writer.writerow([num, f'{t1} v {t2}', label])
    print(f'  Generated: {filename}')


def generate_results():
    os.makedirs('results', exist_ok=True)
    path = 'results/group_results.csv'
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['match', 'home_score', 'away_score', 'outcome'])
        for num, t1, t2 in MATCHES:
            outcome    = random_outcome()
            home, away = random_score(outcome)
            writer.writerow([num, home, away, outcome])
    print(f'Generated results for all 72 matches → {path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--participants', type=int, default=5)
    args = parser.parse_args()

    print(f'\nGenerating {args.participants} participants × 2 pools (all 72 matches)...')
    for pool_id in ['swiftly', 'fandf']:
        print(f'\n  Pool: {pool_id}')
        for n in range(1, args.participants + 1):
            generate_picks(pool_id, n)

    print('\nGenerating results for all 72 matches...')
    generate_results()
    print('\nDone. Run aggregate_picks.py next to update the leaderboard data.')
