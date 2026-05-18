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


# ── Knockout bracket generation ───────────────────────────────────────────────
# Only runs once all 72 group stage matches have results.

GROUP_ORDER = {
    'A': ['Mexico','South Africa','South Korea','Czech Republic'],
    'B': ['Canada','Bosnia and Herzegovina','Qatar','Switzerland'],
    'C': ['Brazil','Morocco','Haiti','Scotland'],
    'D': ['United States','Paraguay','Australia','Turkey'],
    'E': ['Germany','Curaçao','Ivory Coast','Ecuador'],
    'F': ['Netherlands','Japan','Sweden','Tunisia'],
    'G': ['Belgium','Egypt','Iran','New Zealand'],
    'H': ['Spain','Cape Verde','Saudi Arabia','Uruguay'],
    'I': ['France','Senegal','Iraq','Norway'],
    'J': ['Argentina','Algeria','Austria','Jordan'],
    'K': ['Portugal','DR Congo','Uzbekistan','Colombia'],
    'L': ['England','Croatia','Ghana','Panama'],
}

RANKINGS = {
    'Mexico':15,'South Africa':60,'South Korea':25,'Czech Republic':41,
    'Canada':30,'Bosnia and Herzegovina':65,'Qatar':55,'Switzerland':19,
    'Brazil':6,'Morocco':8,'Haiti':83,'Scotland':43,
    'United States':16,'Paraguay':40,'Australia':27,'Turkey':22,
    'Germany':10,'Curaçao':82,'Ivory Coast':34,'Ecuador':23,
    'Netherlands':7,'Japan':18,'Sweden':38,'Tunisia':44,
    'Belgium':9,'Egypt':29,'Iran':21,'New Zealand':85,
    'Spain':2,'Cape Verde':69,'Saudi Arabia':61,'Uruguay':17,
    'France':1,'Senegal':14,'Iraq':57,'Norway':31,
    'Argentina':3,'Algeria':28,'Austria':24,'Jordan':63,
    'Portugal':5,'DR Congo':46,'Uzbekistan':50,'Colombia':13,
    'England':4,'Croatia':11,'Ghana':74,'Panama':33,
}

# 495-combination table: key = sorted 8 qualifying group letters
# value = [1A-opp, 1B-opp, 1D-opp, 1E-opp, 1G-opp, 1I-opp, 1K-opp, 1L-opp]
# → maps to matches [M79, M85, M81, M74, M82, M77, M87, M80]
THIRD_COMBOS = {}
_RAW = """EFGHIJKL:E J I F H G L K
DFGHIJKL:H G I D J F L K
DEGHIJKL:E J I D H G L K
DEFHIJKL:E J I D H F L K
DEFGIJKL:E G I D J F L K
DEFGHJKL:E G J D H F L K
DEFGHIKL:E G I D H F L K
DEFGHIJL:E G J D H F L I
DEFGHIJK:E G J D H F I K
CFGHIJKL:H G I C J F L K
CEGHIJKL:E J I C H G L K
CEFHIJKL:E J I C H F L K
CEFGIJKL:E G I C J F L K
CEFGHJKL:E G J C H F L K
CEFGHIKL:E G I C H F L K
CEFGHIJL:E G J C H F L I
CEFGHIJK:E G J C H F I K
CDGHIJKL:H G I C J D L K
CDFHIJKL:C J I D H F L K
CDFGIJKL:C G I D J F L K
CDFGHJKL:C G J D H F L K
CDFGHIKL:C G I D H F L K
CDFGHIJL:C G J D H F L I
CDFGHIJK:C G J D H F I K
CDEHIJKL:E J I C H D L K
CDEGIJKL:E G I C J D L K
CDEGHJKL:E G J C H D L K
CDEGHIKL:E G I C H D L K
CDEGHIJL:E G J C H D L I
CDEGHIJK:E G J C H D I K
CDEFIJKL:C J E D I F L K
CDEFHJKL:C J E D H F L K
CDEFHIKL:C E I D H F L K
CDEFHIJL:C J E D H F L I
CDEFHIJK:C J E D H F I K
CDEFGJKL:C G E D J F L K
CDEFGIKL:C G E D I F L K
CDEFGIJL:C G E D J F L I
CDEFGIJK:C G E D J F I K
CDEFGHKL:C G E D H F L K
CDEFGHJL:C G J D H F L E
CDEFGHJK:C G J D H F E K
CDEFGHIL:C G E D H F L I
CDEFGHIK:C G E D H F I K
CDEFGHIJ:C G J D H F E I
BFGHIJKL:H J B F I G L K
BEGHIJKL:E J I B H G L K
BEFHIJKL:E J B F I H L K
BEFGIJKL:E J B F I G L K
BEFGHJKL:E J B F H G L K
BEFGHIKL:E G B F I H L K
BEFGHIJL:E J B F H G L I
BEFGHIJK:E J B F H G I K
BDGHIJKL:H J B D I G L K
BDFHIJKL:H J B D I F L K
BDFGIJKL:I G B D J F L K
BDFGHJKL:H G B D J F L K
BDFGHIKL:H G B D I F L K
BDFGHIJL:H G B D J F L I
BDFGHIJK:H G B D J F I K
BDEHIJKL:E J B D I H L K
BDEGIJKL:E J B D I G L K
BDEGHJKL:E J B D H G L K
BDEGHIKL:E G B D I H L K
BDEGHIJL:E J B D H G L I
BDEGHIJK:E J B D H G I K
BDEFIJKL:E J B D I F L K
BDEFHJKL:E J B D H F L K
BDEFHIKL:E I B D H F L K
BDEFHIJL:E J B D H F L I
BDEFHIJK:E J B D H F I K
BDEFGJKL:E G B D J F L K
BDEFGIKL:E G B D I F L K
BDEFGIJL:E G B D J F L I
BDEFGIJK:E G B D J F I K
BDEFGHKL:E G B D H F L K
BDEFGHJL:H G B D J F L E
BDEFGHJK:H G B D J F E K
BDEFGHIL:E G B D H F L I
BDEFGHIK:E G B D H F I K
BDEFGHIJ:H G B D J F E I
BCGHIJKL:H J B C I G L K
BCFHIJKL:H J B C I F L K
BCFGIJKL:I G B C J F L K
BCFGHJKL:H G B C J F L K
BCFGHIKL:H G B C I F L K
BCFGHIJL:H G B C J F L I
BCFGHIJK:H G B C J F I K
BCEHIJKL:E J B C I H L K
BCEGIJKL:E J B C I G L K
BCEGHJKL:E J B C H G L K
BCEGHIKL:E G B C I H L K
BCEGHIJL:E J B C H G L I
BCEGHIJK:E J B C H G I K
BCEFIJKL:E J B C I F L K
BCEFHJKL:E J B C H F L K
BCEFHIKL:E I B C H F L K
BCEFHIJL:E J B C H F L I
BCEFHIJK:E J B C H F I K
BCEFGJKL:E G B C J F L K
BCEFGIKL:E G B C I F L K
BCEFGIJL:E G B C J F L I
BCEFGIJK:E G B C J F I K
BCEFGHKL:E G B C H F L K
BCEFGHJL:H G B C J F L E
BCEFGHJK:H G B C J F E K
BCEFGHIL:E G B C H F L I
BCEFGHIK:E G B C H F I K
BCEFGHIJ:H G B C J F E I
BCDGHIJL:H J B C I D L K
BCDFGIJKL:I G B C J F L K
BCDFGHJKL:H G B C J F L K
BCDFGHIKL:H G B C I F L K
BCDFGHIJL:H G B C J F L I
BCDFGHIJK:H G B C J F I K
BCDFIJKL:C J B D I F L K
BCDFHJKL:C J B D H F L K
BCDFHIKL:C I B D H F L K
BCDFHIJL:C J B D H F L I
BCDFHIJK:C J B D H F I K
BCDFGJKL:C G B D J F L K
BCDFGIKL:C G B D I F L K
BCDFGIJL:C G B D J F L I
BCDFGIJK:C G B D J F I K
BCDFGHKL:C G B D H F L K
BCDFGHJL:C G B D H F L J
BCDFGHJK:H G B C J F D K
BCDFGHIL:C G B D H F L I
BCDFGHIK:C G B D H F I K
BCDFGHIJ:H G B C J F D I
BCDEHIJL:E J B C I D L K
BCDEHJKL:E J B C H D L K
BCDEHIKL:E I B C H D L K
BCDEHIJL:E J B C H D L I
BCDEHIJK:E J B C H D I K
BCDEGJKL:E G B C J D L K
BCDEGIKL:E G B C I D L K
BCDEGIJL:E G B C J D L I
BCDEGIJK:E G B C J D I K
BCDEGHKL:E G B C H D L K
BCDEGHIJL:H G B C J D L E
BCDEGHIJK:H G B C J D E K
BCDEGHIL:E G B C H D L I
BCDEGHIK:E G B C H D I K
BCDEGHIJ:H G B C J D E I
BCDEFIJL:C J B D E F L K
BCDEFIKL:C E B D I F L K
BCDEFIJL:C J B D E F L I
BCDEFIJK:C J B D E F I K
BCDEFHKL:C E B D H F L K
BCDEFHJL:C J B D H F L E
BCDEFHJK:C J B D H F E K
BCDEFHIL:C E B D H F L I
BCDEFHIK:C E B D H F I K
BCDEFHIJ:C J B D H F E I
BCDEFGKL:C E B D E F L K
BCDEFGJL:C J B D J F L E
BCDEFGJK:C J B D J F E K
BCDEFGIL:C E B D E F L I
BCDEFGIK:C E B D E F I K
BCDEFGIJ:C E B D J F E I
BCDEFGHL:C G B D H F L E
BCDEFGHK:H G B C H F D K
BCDEFGHJ:H G B C J F D E
BCDEFGHI:C G B D H F E I
AFGHIJKL:H J I F A G L K
AEGHIJKL:E J I A H G L K
AEFHIJKL:E J I F A H L K
AEFGIJKL:E J I F A G L K
AEFGHJKL:E G J F A H L K
AEFGHIKL:E G I F A H L K
AEFGHIJL:E G J F A H L I
AEFGHIJK:E G J F A H I K
ADGHIJKL:H J I D A G L K
ADFHIJKL:H J I D A F L K
ADFGIJKL:I G J D A F L K
ADFGHJKL:H G J D A F L K
ADFGHIKL:H G I D A F L K
ADFGHIJL:H G J D A F L I
ADFGHIJK:H G J D A F I K
ADEHIJKL:E J I D A H L K
ADEGIJKL:E J I D A G L K
ADEGHJKL:E G J D A H L K
ADEGHIKL:E G I D A H L K
ADEGHIJL:E G J D A H L I
ADEGHIJK:E G J D A H I K
ADEFIJKL:E J I D A F L K
ADEFHJKL:H J E D A F L K
ADEFHIKL:H E I D A F L K
ADEFHIJL:H J E D A F L I
ADEFHIJK:H J E D A F I K
ADEFGJKL:E G J D A F L K
ADEFGIKL:E G I D A F L K
ADEFGIJL:E G J D A F L I
ADEFGIJK:E G J D A F I K
ADEFGHKL:H G E D A F L K
ADEFGHJL:H G J D A F L E
ADEFGHJK:H G J D A F E K
ADEFGHIL:H G E D A F L I
ADEFGHIK:H G E D A F I K
ADEFGHIJ:H G J D A F E I
ACGHIJKL:H J I C A G L K
ACFHIJKL:H J I C A F L K
ACFGIJKL:I G J C A F L K
ACFGHJKL:H G J C A F L K
ACFGHIKL:H G I C A F L K
ACFGHIJL:H G J C A F L I
ACFGHIJK:H G J C A F I K
ACEHIJKL:E J I C A H L K
ACEGIJKL:E J I C A G L K
ACEGHJKL:E G J C A H L K
ACEGHIKL:E G I C A H L K
ACEGHIJL:E G J C A H L I
ACEGHIJK:E G J C A H I K
ACEFIJKL:E J I C A F L K
ACEFHJKL:H J E C A F L K
ACEFHIKL:H E I C A F L K
ACEFHIJL:H J E C A F L I
ACEFHIJK:H J E C A F I K
ACEFGJKL:E G J C A F L K
ACEFGIKL:E G I C A F L K
ACEFGIJL:E G J C A F L I
ACEFGIJK:E G J C A F I K
ACEFGHKL:H G E C A F L K
ACEFGHJL:H G J C A F L E
ACEFGHJK:H G J C A F E K
ACEFGHIL:H G E C A F L I
ACEFGHIK:H G E C A F I K
ACEFGHIJ:H G J C A F E I
ACDGHIJL:H J I C A D L K
ACDGIJKL:I G J C A D L K
ACDGHJKL:H G J C A D L K
ACDGHIKL:H G I C A D L K
ACDGHIJL:H G J C A D L I
ACDGHIJK:H G J C A D I K
ACDFIJKL:C J I D A F L K
ACDFHJKL:H J F C A D L K
ACDFHIKL:H F I C A D L K
ACDFHIJL:H J F C A D L I
ACDFHIJK:H J F C A D I K
ACDFGJKL:C G J D A F L K
ACDFGIKL:C G I D A F L K
ACDFGIJL:C G J D A F L I
ACDFGIJK:C G J D A F I K
ACDFGHKL:H G F C A D L K
ACDFGHJL:C G J D A F L H
ACDFGHJK:H G J C A F D K
ACDFGHIL:H G F C A D L I
ACDFGHIK:H G F C A D I K
ACDFGHIJ:H G J C A F D I
ACDEHIJL:E J I C A D L K
ACDEHJKL:H J E C A D L K
ACDEHIKL:H E I C A D L K
ACDEHIJL:H J E C A D L I
ACDEHIJK:H J E C A D I K
ACDEGJKL:E G J C A D L K
ACDEGIKL:E G I C A D L K
ACDEGIJL:E G J C A D L I
ACDEGIJK:E G J C A D I K
ACDEGHKL:H G E C A D L K
ACDEGHIJL:H G J C A D L E
ACDEGHIJK:H G J C A D E K
ACDEGHIL:H G E C A D L I
ACDEGHIK:H G E C A D I K
ACDEGHIJ:H G J C A D E I
ACDEFIJL:C J E D A F L K
ACDEFIKL:C E I D A F L K
ACDEFIJL:C J E D A F L I
ACDEFIJK:C J E D A F I K
ACDEFHKL:H E F C A D L K
ACDEFHJL:H J F C A D L E
ACDEFHJK:H J E C A F D K
ACDEFHIL:H E F C A D L I
ACDEFHIK:H E F C A D I K
ACDEFHIJ:H J E C A F D I
ACDEFGKL:C G E D A F L K
ACDEFGJL:C G J D A F L E
ACDEFGJK:C G J D A F E K
ACDEFGIL:C G E D A F L I
ACDEFGIK:C G E D A F I K
ACDEFGIJ:C G J D A F E I
ACDEFGHL:H G F C A D L E
ACDEFGHK:H G E C A F D K
ACDEFGHJ:H G J C A F D E
ACDEFGHI:H G E C A F D I
ABGHIJKL:H J B A I G L K
ABFHIJKL:H J B A I F L K
ABFGIJKL:I J B F A G L K
ABFGHJKL:H J B F A G L K
ABFGHIKL:H G B A I F L K
ABFGHIJL:H J B F A G L I
ABFGHIJK:H J B F A G I K
ABEHIJKL:E J B A I H L K
ABEGIJKL:E J B A I G L K
ABEGHJKL:E J B A H G L K
ABEGHIKL:E G B A I H L K
ABEGHIJL:E J B A H G L I
ABEGHIJK:E J B A H G I K
ABEFIJKL:E J B A I F L K
ABEFHJKL:E J B F A H L K
ABEFHIKL:E I B F A H L K
ABEFHIJL:E J B F A H L I
ABEFHIJK:E J B F A H I K
ABEFGJKL:E J B F A G L K
ABEFGIKL:E G B A I F L K
ABEFGIJL:E J B F A G L I
ABEFGIJK:E J B F A G I K
ABEFGHKL:E G B F A H L K
ABEFGHJL:H J B F A G L E
ABEFGHJK:H J B F A G E K
ABEFGHIL:E G B F A H L I
ABEFGHIK:E G B F A H I K
ABEFGHIJ:H J B F A G E I
ABDGHIJL:I J B D A H L K
ABDGIJKL:I J B D A G L K
ABDGHJKL:H J B D A G L K
ABDGHIKL:I G B D A H L K
ABDGHIJL:H J B D A G L I
ABDGHIJK:H J B D A G I K
ABDFIJKL:I J B D A F L K
ABDFHJKL:H J B D A F L K
ABDFHIKL:H I B D A F L K
ABDFHIJL:H J B D A F L I
ABDFHIJK:H J B D A F I K
ABDFGJKL:F J B D A G L K
ABDFGIKL:I G B D A F L K
ABDFGIJL:F J B D A G L I
ABDFGIJK:F J B D A G I K
ABDFGHKL:H G B D A F L K
ABDFGHJL:H G B D A F L J
ABDFGHJK:H G B D A F J K
ABDFGHIL:H G B D A F L I
ABDFGHIK:H G B D A F I K
ABDFGHIJ:H G B D A F I J
ABDEHIJL:E J B A I D L K
ABDEHJKL:E J B D A H L K
ABDEHIKL:E I B D A H L K
ABDEHIJL:E J B D A H L I
ABDEHIJK:E J B D A H I K
ABDEGJKL:E J B D A G L K
ABDEGIKL:E G B A I D L K
ABDEGIJL:E J B D A G L I
ABDEGIJK:E J B D A G I K
ABDEGHKL:E G B D A H L K
ABDEGHIJL:H J B D A G L E
ABDEGHIJK:H J B D A G E K
ABDEGHIL:E G B D A H L I
ABDEGHIK:E G B D A H I K
ABDEGHIJ:H J B D A G E I
ABDEFIJL:E J B D A F L K
ABDEFIKL:E I B D A F L K
ABDEFIJL:E J B D A F L I
ABDEFIJK:E J B D A F I K
ABDEFHKL:H E B D A F L K
ABDEFHJL:H J B D A F L E
ABDEFHJK:H J B D A F E K
ABDEFHIL:H E B D A F L I
ABDEFHIK:H E B D A F I K
ABDEFHIJ:H J B D A F E I
ABDEFGKL:E G B D A F L K
ABDEFGJL:E G B D A F L J
ABDEFGJK:E G B D A F J K
ABDEFGIL:E G B D A F L I
ABDEFGIK:E G B D A F I K
ABDEFGIJ:E G B D A F I J
ABDEFGHL:H G B D A F L E
ABDEFGHK:H G B D A F E K
ABDEFGHJ:H G B D A F E J
ABDEFGHI:H G B D A F E I
ABCGHIJL:I J B C A H L K
ABCGIJKL:I J B C A G L K
ABCGHJKL:H J B C A G L K
ABCGHIKL:I G B C A H L K
ABCGHIJL:H J B C A G L I
ABCGHIJK:H J B C A G I K
ABCFIJKL:I J B C A F L K
ABCFHJKL:H J B C A F L K
ABCFHIKL:H I B C A F L K
ABCFHIJL:H J B C A F L I
ABCFHIJK:H J B C A F I K
ABCFGJKL:C J B F A G L K
ABCFGIKL:I G B C A F L K
ABCFGIJL:C J B F A G L I
ABCFGIJK:C J B F A G I K
ABCFGHKL:H G B C A F L K
ABCFGHJL:H G B C A F L J
ABCFGHJK:H G B C A F J K
ABCFGHIL:H G B C A F L I
ABCFGHIK:H G B C A F I K
ABCFGHIJ:H G B C A F I J
ABCEIJKL:E J B A I C L K
ABCEHJKL:E J B C A H L K
ABCEHIKL:E I B C A H L K
ABCEHIJL:E J B C A H L I
ABCEHIJK:E J B C A H I K
ABCEGJKL:E J B C A G L K
ABCEGIKL:E G B A I C L K
ABCEGIJL:E J B C A G L I
ABCEGIJK:E J B C A G I K
ABCEGHKL:E G B C A H L K
ABCEGHIJL:H J B C A G L E
ABCEGHIJK:H J B C A G E K
ABCEGHIL:E G B C A H L I
ABCEGHIK:E G B C A H I K
ABCEGHIJ:H J B C A G E I
ABCEFIJL:E J B C A F L K
ABCEFIKL:E I B C A F L K
ABCEFIJL:E J B C A F L I
ABCEFIJK:E J B C A F I K
ABCEFHKL:H E B C A F L K
ABCEFHJL:H J B C A F L E
ABCEFHJK:H J B C A F E K
ABCEFHIL:H E B C A F L I
ABCEFHIK:H E B C A F I K
ABCEFHIJ:H J B C A F E I
ABCEFGKL:E G B C A F L K
ABCEFGJL:E G B C A F L J
ABCEFGJK:E G B C A F J K
ABCEFGIL:E G B C A F L I
ABCEFGIK:E G B C A F I K
ABCEFGIJ:E G B C A F I J
ABCEFGHL:H G B C A F L E
ABCEFGHK:H G B C A F E K
ABCEFGHJ:H G B C A F E J
ABCEFGHI:H G B C A F E I
ABCDHIJL:I J B C A D L K
ABCDGIJKL:I J B C A D L K
ABCDGHJKL:H J B C A D L K
ABCDGHIKL:H I B C A D L K
ABCDGHIJL:H J B C A D L I
ABCDGHIJK:H J B C A D I K
ABCDFIJKL:C J B D A F L K
ABCDFIKL:C I B D A F L K
ABCDFIJL:C J B D A F L I
ABCDFIJK:C J B D A F I K
ABCDFHKL:H F B C A D L K
ABCDFHJL:C J B D A F L H
ABCDFHJK:H J B C A F D K
ABCDFHIL:H F B C A D L I
ABCDFHIK:H F B C A D I K
ABCDFHIJ:H J B C A F D I
ABCDEHIJL:E J B C A D L K
ABCDEIKL:E I B C A D L K
ABCDEHIJL:E J B C A D L I
ABCDEHIJK:E J B C A D I K
ABCDEHKL:H E B C A D L K
ABCDEHJL:H J B C A D L E
ABCDEHJK:H J B C A D E K
ABCDEHIL:H E B C A D L I
ABCDEHIK:H E B C A D I K
ABCDEHIJ:H J B C A D E I
ABCDEGKL:E G B C A D L K
ABCDEGJL:E G B C A D L J
ABCDEGJK:E G B C A D J K
ABCDEGIL:E G B C A D L I
ABCDEGIK:E G B C A D I K
ABCDEGIJ:E G B C A D I J
ABCDEGHIJL:H G B C A D L E
ABCDEGHIJK:H G B C A D E K
ABCDEGHIJ:H G B C A D E J
ABCDEGHI:H G B C A D E I
ABCDEFKL:C E B D A F L K
ABCDEFJL:C J B D A F L E
ABCDEFJK:C J B D A F E K
ABCDEFIL:C E B D A F L I
ABCDEFIK:C E B D A F I K
ABCDEFIJ:C J B D A F E I
ABCDEFHL:H F B C A D L E
ABCDEFHK:H E B C A F D K
ABCDEFHJ:H J B C A F D E
ABCDEFHI:H E B C A F D I
ABCDEFGL:C G B D A F L E
ABCDEFGK:C G B D A F E K
ABCDEFGJ:C G B D A F E J
ABCDEFGI:C G B D A F E I
ABCDEFGH:H G B C A F D E"""

for _line in _RAW.strip().split('\n'):
    _k, _v = _line.split(':')
    _key = ''.join(sorted(_k.strip().split()))
    if len(_key) == 8:
        THIRD_COMBOS[_key] = _v.strip().split()


GROUP_MATCHES = [
    (1,'A','Mexico','South Africa'),(2,'A','South Korea','Czech Republic'),
    (3,'B','Canada','Bosnia and Herzegovina'),(4,'D','United States','Paraguay'),
    (5,'C','Haiti','Scotland'),(6,'D','Australia','Turkey'),
    (7,'C','Brazil','Morocco'),(8,'B','Qatar','Switzerland'),
    (9,'E','Ivory Coast','Ecuador'),(10,'E','Germany','Curaçao'),
    (11,'F','Netherlands','Japan'),(12,'F','Sweden','Tunisia'),
    (13,'H','Saudi Arabia','Uruguay'),(14,'H','Spain','Cape Verde'),
    (15,'G','Iran','New Zealand'),(16,'G','Belgium','Egypt'),
    (17,'I','France','Senegal'),(18,'I','Iraq','Norway'),
    (19,'J','Argentina','Algeria'),(20,'J','Austria','Jordan'),
    (21,'L','Ghana','Panama'),(22,'L','England','Croatia'),
    (23,'K','Portugal','DR Congo'),(24,'K','Uzbekistan','Colombia'),
    (25,'A','Czech Republic','South Africa'),(26,'B','Switzerland','Bosnia and Herzegovina'),
    (27,'B','Canada','Qatar'),(28,'A','Mexico','South Korea'),
    (29,'C','Brazil','Haiti'),(30,'C','Scotland','Morocco'),
    (31,'D','Turkey','Paraguay'),(32,'D','United States','Australia'),
    (33,'E','Germany','Ivory Coast'),(34,'E','Ecuador','Curaçao'),
    (35,'F','Netherlands','Sweden'),(36,'F','Tunisia','Japan'),
    (37,'H','Uruguay','Cape Verde'),(38,'H','Spain','Saudi Arabia'),
    (39,'G','Belgium','Iran'),(40,'G','New Zealand','Egypt'),
    (41,'I','Norway','Senegal'),(42,'I','France','Iraq'),
    (43,'J','Argentina','Austria'),(44,'J','Jordan','Algeria'),
    (45,'L','England','Ghana'),(46,'L','Panama','Croatia'),
    (47,'K','Portugal','Uzbekistan'),(48,'K','Colombia','DR Congo'),
    (49,'C','Scotland','Brazil'),(50,'C','Morocco','Haiti'),
    (51,'B','Switzerland','Canada'),(52,'B','Bosnia and Herzegovina','Qatar'),
    (53,'A','Czech Republic','Mexico'),(54,'A','South Africa','South Korea'),
    (55,'E','Curaçao','Ivory Coast'),(56,'E','Ecuador','Germany'),
    (57,'F','Japan','Sweden'),(58,'F','Tunisia','Netherlands'),
    (59,'D','Turkey','United States'),(60,'D','Paraguay','Australia'),
    (61,'I','Norway','France'),(62,'I','Senegal','Iraq'),
    (63,'G','Egypt','Iran'),(64,'G','New Zealand','Belgium'),
    (65,'H','Cape Verde','Saudi Arabia'),(66,'H','Uruguay','Spain'),
    (67,'L','Panama','England'),(68,'L','Croatia','Ghana'),
    (69,'J','Algeria','Austria'),(70,'J','Jordan','Argentina'),
    (71,'K','Colombia','Portugal'),(72,'K','DR Congo','Uzbekistan'),
]


def compute_group_standings(results):
    """Compute group standings from results dict."""
    stats = {}
    all_matches = GROUP_MATCHES

    stats = {}
    for num, grp, t1, t2 in all_matches:
        for t in [t1, t2]:
            if t not in stats:
                stats[t] = {'P':0,'W':0,'D':0,'L':0,'GF':0,'GA':0,'Pts':0,'grp':grp}
        r = results.get(num)
        if not r: continue
        home, away, outcome = r
        stats[t1]['P'] += 1; stats[t2]['P'] += 1
        stats[t1]['GF'] += home; stats[t1]['GA'] += away
        stats[t2]['GF'] += away; stats[t2]['GA'] += home
        if outcome == 'W1':
            stats[t1]['W'] += 1; stats[t1]['Pts'] += 3; stats[t2]['L'] += 1
        elif outcome == 'W2':
            stats[t2]['W'] += 1; stats[t2]['Pts'] += 3; stats[t1]['L'] += 1
        else:
            stats[t1]['D'] += 1; stats[t1]['Pts'] += 1
            stats[t2]['D'] += 1; stats[t2]['Pts'] += 1

    grp_standings = {}
    for grp, teams in GROUP_ORDER.items():
        sorted_teams = sorted(teams, key=lambda t: (
            -stats.get(t, {}).get('Pts', 0),
            -(stats.get(t, {}).get('GF', 0) - stats.get(t, {}).get('GA', 0)),
            -stats.get(t, {}).get('GF', 0),
            RANKINGS.get(t, 999)
        ))
        grp_standings[grp] = [(t, stats.get(t, {})) for t in sorted_teams]

    return grp_standings, stats


def write_bracket_json(results):
    """Compute and write knockout_bracket.json when all 72 matches are done."""
    if len(results) < 72:
        print(f'Group stage incomplete ({len(results)}/72) — bracket not yet generated')
        return

    grp_standings, _ = compute_group_standings(results)

    # Build position lookup
    pos = {}
    for grp, teams in grp_standings.items():
        if len(teams) > 0: pos[f'1{grp}'] = teams[0][0]
        if len(teams) > 1: pos[f'2{grp}'] = teams[1][0]
        if len(teams) > 2: pos[f'3{grp}'] = teams[2][0]

    # Best 8 third-place teams
    thirds = sorted(
        [(grp, teams[2][0], teams[2][1]) for grp, teams in grp_standings.items() if len(teams) >= 3],
        key=lambda x: (-x[2].get('Pts',0), -(x[2].get('GF',0)-x[2].get('GA',0)),
                       -x[2].get('GF',0), RANKINGS.get(x[1], 999))
    )[:8]

    qual_groups = ''.join(sorted(g for g,_,_ in thirds))
    combo = THIRD_COMBOS.get(qual_groups)

    # 3rd place slot assignments: [M79,M85,M81,M74,M82,M77,M87,M80]
    third_slot = {}
    if combo:
        for match, grp_letter in zip([79,85,81,74,82,77,87,80], combo):
            third_slot[match] = pos.get(f'3{grp_letter}', f'3{grp_letter}')
    else:
        print(f'Warning: combination key "{qual_groups}" not found — using placeholders')
        for m in [79,85,81,74,82,77,87,80]:
            third_slot[m] = 'TBD'

    # Round of 32 matchups
    r32 = {
        73: (pos.get('2A'), pos.get('2B')),
        74: (pos.get('1E'), third_slot.get(74)),
        75: (pos.get('1F'), pos.get('2C')),
        76: (pos.get('1C'), pos.get('2F')),
        77: (pos.get('1I'), third_slot.get(77)),
        78: (pos.get('2E'), pos.get('2I')),
        79: (pos.get('1A'), third_slot.get(79)),
        80: (pos.get('1L'), third_slot.get(80)),
        81: (pos.get('1D'), third_slot.get(81)),
        82: (pos.get('1G'), third_slot.get(82)),
        83: (pos.get('2K'), pos.get('2L')),
        84: (pos.get('1H'), pos.get('2J')),
        85: (pos.get('1B'), third_slot.get(85)),
        86: (pos.get('1J'), pos.get('2H')),
        87: (pos.get('1K'), third_slot.get(87)),
        88: (pos.get('2D'), pos.get('2G')),
    }

    import json, datetime
    bracket = {
        'generated_at': datetime.datetime.utcnow().isoformat() + 'Z',
        'confirmed': True,
        'combination_key': qual_groups,
        'combination_found': combo is not None,
        'groups': {
            grp: {
                'first':  teams[0][0] if len(teams) > 0 else None,
                'second': teams[1][0] if len(teams) > 1 else None,
                'third':  teams[2][0] if len(teams) > 2 else None,
                'fourth': teams[3][0] if len(teams) > 3 else None,
            }
            for grp, teams in grp_standings.items()
        },
        'qualified_thirds': [
            {'group': g, 'team': t, 'pts': s.get('Pts',0),
             'gd': s.get('GF',0)-s.get('GA',0), 'gf': s.get('GF',0)}
            for g, t, s in thirds
        ],
        'round_of_32': {
            str(m): {'home': home, 'away': away}
            for m, (home, away) in r32.items()
        },
        'round_of_16': {
            '89': {'home': 'W74', 'away': 'W77'}, '90': {'home': 'W73', 'away': 'W75'},
            '91': {'home': 'W76', 'away': 'W78'}, '92': {'home': 'W79', 'away': 'W80'},
            '93': {'home': 'W83', 'away': 'W84'}, '94': {'home': 'W81', 'away': 'W82'},
            '95': {'home': 'W86', 'away': 'W88'}, '96': {'home': 'W85', 'away': 'W87'},
        },
        'quarterfinals': {
            '97': {'home': 'W89', 'away': 'W90'}, '98': {'home': 'W93', 'away': 'W94'},
            '99': {'home': 'W91', 'away': 'W92'}, '100': {'home': 'W95', 'away': 'W96'},
        },
        'semifinals': {
            '101': {'home': 'W97', 'away': 'W98'},
            '102': {'home': 'W99', 'away': 'W100'},
        },
        'third_place': {'103': {'home': 'L101', 'away': 'L102'}},
        'final':       {'104': {'home': 'W101', 'away': 'W102'}},
    }

    os.makedirs('data', exist_ok=True)
    path = 'data/knockout_bracket.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(bracket, f, indent=2)
    print(f'Knockout bracket written → {path}')
    for m, (h, a) in r32.items():
        print(f'  M{m}: {h} vs {a}')


if __name__ == '__main__':
    print('Fetching Wikipedia wikitext...')
    wikitext = fetch_wikitext()
    print('Parsing match results...')
    results = parse_results(wikitext)
    print(f'Found {len(results)} completed matches')
    write_csv(results)
    write_bracket_json(results)
