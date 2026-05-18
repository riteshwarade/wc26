"""
parse_results.py
Fetches the 2026 FIFA World Cup Wikipedia page via the MediaWiki API,
parses group stage match results, and writes results/group_results.csv.
"""

import csv
import os
import re
import requests

# ── FIFA ↔ Wikipedia name mapping (for reference) ────────────────────────────
# FIFA official name   → Wikipedia name (used throughout this system)
# "Korea Republic"     → "South Korea"
# "Türkiye"            → "Turkey"
# "Côte d'Ivoire"      → "Ivory Coast"
# "Cabo Verde"         → "Cape Verde"
# "IR Iran"            → "Iran"
# "Congo DR"           → "DR Congo"
# "Czech Republic"            → "Czech Republic"  (same on both)
# ─────────────────────────────────────────────────────────────────────────────

# ── Wikipedia country code → team name ───────────────────────────────────────
TEAM_CODES = {
    'MEX': 'Mexico',          'RSA': 'South Africa',      'KOR': 'South Korea',
    'CZE': 'Czech Republic',         'CAN': 'Canada',            'BIH': 'Bosnia and Herzegovina',
    'USA': 'United States',   'PAR': 'Paraguay',          'HAI': 'Haiti',
    'SCO': 'Scotland',        'AUS': 'Australia',         'TUR': 'Turkey',
    'BRA': 'Brazil',          'MAR': 'Morocco',           'QAT': 'Qatar',
    'SUI': 'Switzerland',     'CIV': 'Ivory Coast',       'ECU': 'Ecuador',
    'GER': 'Germany',         'CUW': 'Curaçao',           'NED': 'Netherlands',
    'JPN': 'Japan',           'SWE': 'Sweden',            'TUN': 'Tunisia',
    'KSA': 'Saudi Arabia',    'URU': 'Uruguay',           'ESP': 'Spain',
    'CPV': 'Cape Verde',      'IRN': 'Iran',              'NZL': 'New Zealand',
    'BEL': 'Belgium',         'EGY': 'Egypt',             'FRA': 'France',
    'SEN': 'Senegal',         'IRQ': 'Iraq',              'NOR': 'Norway',
    'ARG': 'Argentina',       'ALG': 'Algeria',           'AUT': 'Austria',
    'JOR': 'Jordan',          'GHA': 'Ghana',             'PAN': 'Panama',
    'ENG': 'England',         'CRO': 'Croatia',           'POR': 'Portugal',
    'COD': 'DR Congo',        'UZB': 'Uzbekistan',        'COL': 'Colombia',
}

# ── Match list: (team1, team2) → match number ─────────────────────────────────
MATCH_LOOKUP = {
    ('Mexico', 'South Africa'): 1,          ('South Korea', 'Czech Republic'): 2,
    ('Canada', 'Bosnia and Herzegovina'): 3, ('United States', 'Paraguay'): 4,
    ('Haiti', 'Scotland'): 5,               ('Australia', 'Turkey'): 6,
    ('Brazil', 'Morocco'): 7,              ('Qatar', 'Switzerland'): 8,
    ('Ivory Coast', 'Ecuador'): 9,          ('Germany', 'Curaçao'): 10,
    ('Netherlands', 'Japan'): 11,           ('Sweden', 'Tunisia'): 12,
    ('Saudi Arabia', 'Uruguay'): 13,        ('Spain', 'Cape Verde'): 14,
    ('Iran', 'New Zealand'): 15,            ('Belgium', 'Egypt'): 16,
    ('France', 'Senegal'): 17,             ('Iraq', 'Norway'): 18,
    ('Argentina', 'Algeria'): 19,           ('Austria', 'Jordan'): 20,
    ('Ghana', 'Panama'): 21,               ('England', 'Croatia'): 22,
    ('Portugal', 'DR Congo'): 23,           ('Uzbekistan', 'Colombia'): 24,
    ('Czech Republic', 'South Africa'): 25,        ('Switzerland', 'Bosnia and Herzegovina'): 26,
    ('Canada', 'Qatar'): 27,               ('Mexico', 'South Korea'): 28,
    ('Brazil', 'Haiti'): 29,               ('Scotland', 'Morocco'): 30,
    ('Turkey', 'Paraguay'): 31,             ('United States', 'Australia'): 32,
    ('Germany', 'Ivory Coast'): 33,         ('Ecuador', 'Curaçao'): 34,
    ('Netherlands', 'Sweden'): 35,          ('Tunisia', 'Japan'): 36,
    ('Uruguay', 'Cape Verde'): 37,          ('Spain', 'Saudi Arabia'): 38,
    ('Belgium', 'Iran'): 39,               ('New Zealand', 'Egypt'): 40,
    ('Norway', 'Senegal'): 41,             ('France', 'Iraq'): 42,
    ('Argentina', 'Austria'): 43,           ('Jordan', 'Algeria'): 44,
    ('England', 'Ghana'): 45,              ('Panama', 'Croatia'): 46,
    ('Portugal', 'Uzbekistan'): 47,         ('Colombia', 'DR Congo'): 48,
    ('Scotland', 'Brazil'): 49,             ('Morocco', 'Haiti'): 50,
    ('Switzerland', 'Canada'): 51,          ('Bosnia and Herzegovina', 'Qatar'): 52,
    ('Czech Republic', 'Mexico'): 53,              ('South Africa', 'South Korea'): 54,
    ('Curaçao', 'Ivory Coast'): 55,         ('Ecuador', 'Germany'): 56,
    ('Japan', 'Sweden'): 57,               ('Tunisia', 'Netherlands'): 58,
    ('Turkey', 'United States'): 59,        ('Paraguay', 'Australia'): 60,
    ('Norway', 'France'): 61,              ('Senegal', 'Iraq'): 62,
    ('Egypt', 'Iran'): 63,                 ('New Zealand', 'Belgium'): 64,
    ('Cape Verde', 'Saudi Arabia'): 65,     ('Uruguay', 'Spain'): 66,
    ('Panama', 'England'): 67,             ('Croatia', 'Ghana'): 68,
    ('Algeria', 'Austria'): 69,             ('Jordan', 'Argentina'): 70,
    ('Colombia', 'Portugal'): 71,           ('DR Congo', 'Uzbekistan'): 72,
}


def fetch_wikitext():
    """Fetch the raw wikitext of the 2026 FIFA World Cup Wikipedia article."""
    resp = requests.get(
        'https://en.wikipedia.org/w/api.php',
        params={
            'action': 'parse',
            'page': '2026_FIFA_World_Cup',
            'prop': 'wikitext',
            'format': 'json',
        },
        timeout=30,
        headers={'User-Agent': 'wc26-pool-bot/1.0 (github.com/riteshwarade/wc26)'},
    )
    resp.raise_for_status()
    return resp.json()['parse']['wikitext']['*']


def extract_team(raw):
    """Extract team name from a wikitext field containing {{fb|CODE}} or similar."""
    m = re.search(r'\{\{fb[a-z]*\|([A-Z]{2,3})', raw)
    if m:
        return TEAM_CODES.get(m.group(1))
    return None


def extract_score(raw):
    """Parse a score string like '2–1' or '0–0'. Returns (home, away) or None."""
    raw = raw.strip()
    m = re.match(r'^(\d+)\s*[–\-]\s*(\d+)$', raw)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def parse_results(wikitext):
    """Extract all completed group stage match results from the wikitext."""
    results = {}

    # Split on each Football box template
    blocks = re.split(r'\{\{[Ff]ootball[ _]box', wikitext)

    for block in blocks[1:]:
        # Extract relevant fields
        t1_m     = re.search(r'\|\s*team1\s*=\s*([^\n|]+)', block)
        t2_m     = re.search(r'\|\s*team2\s*=\s*([^\n|]+)', block)
        score_m  = re.search(r'\|\s*score\s*=\s*([^\n|]+)', block)

        if not (t1_m and t2_m and score_m):
            continue

        team1      = extract_team(t1_m.group(1))
        team2      = extract_team(t2_m.group(1))
        score_pair = extract_score(score_m.group(1))

        if not (team1 and team2 and score_pair):
            continue  # unplayed match or unknown teams

        home, away = score_pair

        if home > away:
            outcome = 'W1'
        elif home < away:
            outcome = 'W2'
        else:
            outcome = 'Draw'

        match_num = MATCH_LOOKUP.get((team1, team2))
        if match_num:
            results[match_num] = (home, away, outcome)
        else:
            print(f'  Warning: no match found for {team1} vs {team2}')

    return results


def write_csv(results):
    os.makedirs('results', exist_ok=True)
    path = 'results/group_results.csv'
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['match', 'home_score', 'away_score', 'outcome'])
        for num in sorted(results):
            home, away, outcome = results[num]
            w.writerow([num, home, away, outcome])
    print(f'Wrote {len(results)} results → {path}')


if __name__ == '__main__':
    print('Fetching Wikipedia wikitext...')
    wikitext = fetch_wikitext()
    print('Parsing match results...')
    results = parse_results(wikitext)
    print(f'Found {len(results)} completed matches')
    write_csv(results)
