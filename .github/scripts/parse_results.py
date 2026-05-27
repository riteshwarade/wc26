"""
parse_results.py
Fetches the 2026 FIFA World Cup Wikipedia page via the MediaWiki API,
parses group stage match results, and writes results/group_results.csv.
"""

import csv
import json
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


# ── ESPN API (primary data source) ───────────────────────────────────────────
# ESPN's hidden scoreboard API returns clean JSON for all 104 WC2026 matches.
# No API key required.  Full tournament: group stage + all KO rounds.

ESPN_SCOREBOARD_URL = (
    'https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard'
)
# ESPN caps results at 100 events per request.  Group stage (72) and KO stage
# (32) are fetched separately so each request stays well within the cap.
ESPN_GROUP_DATES = '20260611-20260627'   # M1–M72  (Jun 11 – Jun 27)
ESPN_KO_DATES    = '20260628-20260720'   # M73–M104 (Jun 28 – Jul 20)

# ESPN uses a handful of team names that differ from our TEAM_CODES values.
ESPN_TEAM_MAP = {
    'Czechia':            'Czech Republic',
    'Türkiye':            'Turkey',
    'Bosnia-Herzegovina': 'Bosnia and Herzegovina',
    'Congo DR':           'DR Congo',
    'Curacao':            'Curaçao',
}


def _fetch_events(date_range):
    """Fetch ESPN scoreboard events for one date range."""
    resp = requests.get(
        ESPN_SCOREBOARD_URL,
        params={'dates': date_range},
        timeout=30,
        headers={'User-Agent': 'wc26-pool-bot/1.0 (github.com/riteshwarade/wc26)'},
    )
    resp.raise_for_status()
    return resp.json().get('events', [])


def fetch_espn_group_events():
    """Fetch the 72 group-stage match events (Jun 11–27)."""
    return _fetch_events(ESPN_GROUP_DATES)


def fetch_espn_ko_events():
    """Fetch the 32 knockout-stage match events (Jun 28–Jul 20)."""
    return _fetch_events(ESPN_KO_DATES)


def espn_team_name(team_dict):
    """Normalise an ESPN team object's displayName to our internal team name."""
    raw = team_dict.get('displayName', '')
    return ESPN_TEAM_MAP.get(raw, raw)


def parse_group_results_espn(events):
    """
    Extract completed group-stage results from ESPN event list.
    Returns dict {match_num: (home_score, away_score, outcome)}.
    """
    results = {}
    for evt in events:
        if evt.get('season', {}).get('slug') != 'group-stage':
            continue
        comp = evt['competitions'][0]
        if not comp['status']['type'].get('completed'):
            continue
        competitors = comp.get('competitors', [])
        home_c = next((c for c in competitors if c['homeAway'] == 'home'), None)
        away_c = next((c for c in competitors if c['homeAway'] == 'away'), None)
        if not (home_c and away_c):
            continue
        home_name  = espn_team_name(home_c.get('team', {}))
        away_name  = espn_team_name(away_c.get('team', {}))
        espn_home_score = int(home_c.get('score', 0))
        espn_away_score = int(away_c.get('score', 0))
        # Look up by ESPN's home/away order first; fall back to reversed order in
        # case ESPN swaps home/away on a neutral-site fixture.
        match_num = MATCH_LOOKUP.get((home_name, away_name))
        if match_num:
            home_score, away_score = espn_home_score, espn_away_score
        else:
            match_num = MATCH_LOOKUP.get((away_name, home_name))
            if match_num:
                # ESPN labelled them reversed — swap scores to match our fixture order
                home_score, away_score = espn_away_score, espn_home_score
                print(f'  Note: ESPN home/away reversed for M{match_num} '
                      f'({home_name} vs {away_name}) — scores swapped')
            else:
                print(f'  Warning: no group match found for {home_name} vs {away_name}')
                continue
        if home_score > away_score:
            outcome = 'W1'
        elif away_score > home_score:
            outcome = 'W2'
        else:
            outcome = 'Draw'
        results[match_num] = (home_score, away_score, outcome)
    return results


def parse_ko_results_espn(events, bracket_data):
    """
    Extract completed KO match results from ESPN event list.

    Uses the same bracket-walking logic as parse_ko_results(): iterates
    sections in order (R32 → R16 → QF → SF → 3rd/Final), resolving
    'W73'/'L101'-style references as earlier winners become known.

    Returns dict {match_num (int): winner_name (str)}.
    """
    KO_SLUGS = {
        'round-of-32', 'round-of-16', 'quarterfinals',
        'semifinals', '3rd-place-match', 'final',
    }

    # Build {frozenset(team1, team2): winner} from completed KO events.
    # ESPN sets competitor.winner=True for the winning side.
    pair_to_winner = {}
    pair_to_scores = {}
    for evt in events:
        if evt.get('season', {}).get('slug') not in KO_SLUGS:
            continue
        comp = evt['competitions'][0]
        if not comp['status']['type'].get('completed'):
            continue
        competitors = comp.get('competitors', [])
        teams  = [espn_team_name(c.get('team', {})) for c in competitors]
        winner = next(
            (espn_team_name(c.get('team', {})) for c in competitors if c.get('winner')),
            None,
        )
        if winner and len(teams) == 2:
            pair_to_winner[frozenset(teams)] = winner
            home_c = next((c for c in competitors if c.get('homeAway') == 'home'), None)
            away_c = next((c for c in competitors if c.get('homeAway') == 'away'), None)
            if home_c and away_c:
                h_score = int(home_c.get('score', 0) or 0)
                a_score = int(away_c.get('score', 0) or 0)
                h_pen   = home_c.get('shootoutScore')
                a_pen   = away_c.get('shootoutScore')
                entry   = (h_score, a_score)
                if h_pen is not None and a_pen is not None:
                    try:
                        entry = (h_score, a_score, int(h_pen), int(a_pen))
                    except (TypeError, ValueError):
                        pass
                pair_to_scores[frozenset(teams)] = entry

    # Walk bracket sections in order to assign our match numbers.
    results       = {}
    scores        = {}
    match_winners = {}
    match_losers  = {}

    def resolve(ref):
        if not ref:             return None
        if ref.startswith('W'): return match_winners.get(int(ref[1:]))
        if ref.startswith('L'): return match_losers.get(int(ref[1:]))
        return ref

    for section in [
        bracket_data.get('round_of_32',   {}),
        bracket_data.get('round_of_16',   {}),
        bracket_data.get('quarterfinals', {}),
        bracket_data.get('semifinals',    {}),
        bracket_data.get('third_place',   {}),
        bracket_data.get('final',         {}),
    ]:
        for m_str, info in sorted(section.items(), key=lambda x: int(x[0])):
            m    = int(m_str)
            home = resolve(info.get('home'))
            away = resolve(info.get('away'))
            if not (home and away):
                continue
            winner = pair_to_winner.get(frozenset([home, away]))
            if winner:
                results[m]       = winner
                match_winners[m] = winner
                match_losers[m]  = away if winner == home else home
                sc = pair_to_scores.get(frozenset([home, away]))
                if sc:
                    scores[m] = sc

    return results, scores


# ── Wikipedia fetch helpers (kept for verify_r32_against_wikipedia) ───────────

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


def fetch_ko_wikitext():
    """Fetch the raw wikitext of the 2026 FIFA World Cup knockout stage Wikipedia article."""
    resp = requests.get(
        'https://en.wikipedia.org/w/api.php',
        params={
            'action': 'parse',
            'page': '2026_FIFA_World_Cup_knockout_stage',
            'prop': 'wikitext',
            'format': 'json',
        },
        timeout=30,
        headers={'User-Agent': 'wc26-pool-bot/1.0 (github.com/riteshwarade/wc26)'},
    )
    resp.raise_for_status()
    return resp.json()['parse']['wikitext']['*']


def extract_team(raw):
    """
    Extract team name from a wikitext field.  Handles several formats:
      {{fb|ESP}}, {{fb-rt|ESP}}                   (group stage / Copa style)
      {{#invoke:flag|fb|ESP}}, {{#invoke:flag|fb-rt|ESP}}  (2026 WC KO style)
      {{#invoke:flagg|main|...|ESP}}               (2022 WC style)
      [[Spain national football team|Spain]]       (wiki link)
    Returns the TEAM_CODES display name, or None if not found.
    """
    for pat in [
        r'\{\{fb[a-z\-]*\|([A-Z]{2,3})',                              # {{fb|ESP}}, {{fb-rt|ESP}}
        r'\{\{#invoke:flag\|fb[a-z\-]*\|([A-Z]{2,3})',               # {{#invoke:flag|fb-rt|ESP}}
        r'\{\{#invoke:flagg\|[^|]*\|[^|]*\|(?:[^|]*\|)?([A-Z]{2,3})',  # {{#invoke:flagg|main|...|ESP}}
    ]:
        m = re.search(pat, raw)
        if m:
            result = TEAM_CODES.get(m.group(1))
            if result:
                return result
    # Fallback: wiki link text  [[...|Spain]]
    m = re.search(r'\[\[[^\]|]*\|([^\]]+)\]\]', raw)
    if m:
        candidate = m.group(1).strip()
        if candidate in TEAM_CODES.values():
            return candidate
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
        t1_m     = re.search(r'\|\s*team1\s*=\s*([^\n]+)', block)
        t2_m     = re.search(r'\|\s*team2\s*=\s*([^\n]+)', block)
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


def parse_ko_results(wikitext, bracket_data):
    """
    Parse KO match results from the knockout stage wikitext.

    The 2026 WC KO page uses {{#invoke:football box|main ...}} blocks with
    scores embedded as {{score link|...|2-1}}.  Older pages (2022 WC, Copa)
    use {{Football box with plain scores.  Both formats are handled.

    Uses bracket_data (loaded from data/knockout_bracket.json) to map each
    block's team pair to the correct match number.  Works in bracket order
    (R32 → R16 → QF → SF → 3rd/Final) so placeholder references like "W73"
    or "L101" resolve correctly as earlier results become available.

    Returns a dict {match_num (int): winner_name (str)}.
    """
    # ── Step 1: split on the correct template name ────────────────────────────
    pair_to_winner = {}

    # Try the 2026-style Lua module call first; fall back to classic template.
    blocks = []
    for pat in (
        r'\{\{#invoke:football[ _]box\|main',   # 2026 WC KO format
        r'\{\{[Ff]ootball[ _]box',              # 2022 WC / Copa style
    ):
        parts = re.split(pat, wikitext)
        if len(parts) > 1:
            blocks = parts[1:]
            break

    for block in blocks:
        # Grab the full line for each field — team values may contain '|'
        # inside nested templates, so we consume the entire line.
        t1_m    = re.search(r'\|\s*team1\s*=\s*([^\n]+)', block)
        t2_m    = re.search(r'\|\s*team2\s*=\s*([^\n]+)', block)
        score_m = re.search(r'\|\s*score\s*=\s*([^\n]+)', block)

        if not (t1_m and t2_m and score_m):
            continue

        team1 = extract_team(t1_m.group(1))
        team2 = extract_team(t2_m.group(1))
        if not (team1 and team2):
            continue

        # Score may be:
        #   {{score link|...|2-1}}          → played, score is 2nd param
        #   {{score link|...|Match 73}}     → not yet played, skip
        #   2-1  (plain text, older format) → played
        raw_score = score_m.group(1).strip()
        sl_m = re.search(r'\{\{score[ _]link\|[^|]+\|([^}|]+)\}\}', raw_score)
        if sl_m:
            inner = sl_m.group(1).strip()
            if re.match(r'^Match\s+\d+$', inner, re.I):
                continue  # match not yet played
            actual_score = inner
        else:
            actual_score = raw_score

        sm = re.match(r'^(\d+)\s*[–\-]\s*(\d+)', actual_score)
        if not sm:
            continue
        home_g, away_g = int(sm.group(1)), int(sm.group(2))

        if home_g > away_g:
            winner = team1
        elif away_g > home_g:
            winner = team2
        else:
            # Draw after 90/120 min — check penalty shootout field.
            # Wikipedia uses various field names across templates.
            pen_m = re.search(
                r'\|\s*(?:penaltyscores?|pen1)\s*=\s*([^\n|]+)', block
            )
            if not pen_m:
                continue  # winner not yet determined
            pm = re.match(r'^(\d+)\s*[–\-]\s*(\d+)', pen_m.group(1).strip())
            if not pm or int(pm.group(1)) == int(pm.group(2)):
                continue  # still undetermined
            winner = team1 if int(pm.group(1)) > int(pm.group(2)) else team2

        pair_to_winner[frozenset([team1, team2])] = winner

    # ── Step 2: walk bracket sections in order; resolve references & record ──
    results       = {}
    match_winners = {}   # match_num → winner name
    match_losers  = {}   # match_num → loser name

    def resolve(ref):
        """'W73' → winner of M73, 'L101' → loser of M101, else literal team name."""
        if not ref:
            return None
        if ref.startswith('W'):
            return match_winners.get(int(ref[1:]))
        if ref.startswith('L'):
            return match_losers.get(int(ref[1:]))
        return ref

    sections_in_order = [
        bracket_data.get('round_of_32',   {}),
        bracket_data.get('round_of_16',   {}),
        bracket_data.get('quarterfinals', {}),
        bracket_data.get('semifinals',    {}),
        bracket_data.get('third_place',   {}),
        bracket_data.get('final',         {}),
    ]

    for section in sections_in_order:
        for m_str, info in sorted(section.items(), key=lambda x: int(x[0])):
            m    = int(m_str)
            home = resolve(info.get('home'))
            away = resolve(info.get('away'))

            if not (home and away):
                continue  # teams not yet determined (bracket not settled)

            winner = pair_to_winner.get(frozenset([home, away]))
            if winner:
                results[m]        = winner
                match_winners[m]  = winner
                match_losers[m]   = away if winner == home else home

    return results


def write_ko_results_csv(results, scores=None):
    """Write results/knockout_results.csv.

    scores dict values are tuples:
      (home_score, away_score)              — normal win
      (home_score, away_score, home_pen, away_pen) — penalty shootout
    Writes a 6-column CSV when any entry has pen data, otherwise 4-column.
    """
    os.makedirs('results', exist_ok=True)
    path = 'results/knockout_results.csv'
    has_pen = scores and any(len(sc) == 4 for sc in scores.values())
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if scores:
            if has_pen:
                w.writerow(['match', 'winner', 'home_score', 'away_score', 'home_pen', 'away_pen'])
                for num in sorted(results):
                    sc = scores.get(num)
                    if sc and len(sc) == 4:
                        w.writerow([num, results[num], sc[0], sc[1], sc[2], sc[3]])
                    elif sc:
                        w.writerow([num, results[num], sc[0], sc[1], '', ''])
                    else:
                        w.writerow([num, results[num], '', '', '', ''])
            else:
                w.writerow(['match', 'winner', 'home_score', 'away_score'])
                for num in sorted(results):
                    sc = scores.get(num, ('', ''))
                    w.writerow([num, results[num], sc[0], sc[1]])
        else:
            w.writerow(['match', 'winner'])
            for num in sorted(results):
                w.writerow([num, results[num]])
    print(f'Wrote {len(results)} KO results → {path}')


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
_RAW = """
A B C D E F G H:H G B C A F D E
A B C D E F G I:C G B D A F E I
A B C D E F G J:C G B D A F E J
A B C D E F G K:C G B D A F E K
A B C D E F G L:C G B D A F L E
A B C D E F H I:H E B C A F D I
A B C D E F H J:H J B C A F D E
A B C D E F H K:H E B C A F D K
A B C D E F H L:H F B C A D L E
A B C D E F I J:C J B D A F E I
A B C D E F I K:C E B D A F I K
A B C D E F I L:C E B D A F L I
A B C D E F J K:C J B D A F E K
A B C D E F J L:C J B D A F L E
A B C D E F K L:C E B D A F L K
A B C D E G H I:H G B C A D E I
A B C D E G H J:H G B C A D E J
A B C D E G H K:H G B C A D E K
A B C D E G H L:H G B C A D L E
A B C D E G I J:E G B C A D I J
A B C D E G I K:E G B C A D I K
A B C D E G I L:E G B C A D L I
A B C D E G J K:E G B C A D J K
A B C D E G J L:E G B C A D L J
A B C D E G K L:E G B C A D L K
A B C D E H I J:H J B C A D E I
A B C D E H I K:H E B C A D I K
A B C D E H I L:H E B C A D L I
A B C D E H J K:H J B C A D E K
A B C D E H J L:H J B C A D L E
A B C D E H K L:H E B C A D L K
A B C D E I J K:E J B C A D I K
A B C D E I J L:E J B C A D L I
A B C D E I K L:E I B C A D L K
A B C D E J K L:E J B C A D L K
A B C D F G H I:H G B C A F D I
A B C D F G H J:H G B C A F D J
A B C D F G H K:H G B C A F D K
A B C D F G H L:C G B D A F L H
A B C D F G I J:C G B D A F I J
A B C D F G I K:C G B D A F I K
A B C D F G I L:C G B D A F L I
A B C D F G J K:C G B D A F J K
A B C D F G J L:C G B D A F L J
A B C D F G K L:C G B D A F L K
A B C D F H I J:H J B C A F D I
A B C D F H I K:H F B C A D I K
A B C D F H I L:H F B C A D L I
A B C D F H J K:H J B C A F D K
A B C D F H J L:C J B D A F L H
A B C D F H K L:H F B C A D L K
A B C D F I J K:C J B D A F I K
A B C D F I J L:C J B D A F L I
A B C D F I K L:C I B D A F L K
A B C D F J K L:C J B D A F L K
A B C D G H I J:H G B C A D I J
A B C D G H I K:H G B C A D I K
A B C D G H I L:H G B C A D L I
A B C D G H J K:H G B C A D J K
A B C D G H J L:H G B C A D L J
A B C D G H K L:H G B C A D L K
A B C D G I J K:C J B D A G I K
A B C D G I J L:C J B D A G L I
A B C D G I K L:I G B C A D L K
A B C D G J K L:C J B D A G L K
A B C D H I J K:H J B C A D I K
A B C D H I J L:H J B C A D L I
A B C D H I K L:H I B C A D L K
A B C D H J K L:H J B C A D L K
A B C D I J K L:I J B C A D L K
A B C E F G H I:H G B C A F E I
A B C E F G H J:H G B C A F E J
A B C E F G H K:H G B C A F E K
A B C E F G H L:H G B C A F L E
A B C E F G I J:E G B C A F I J
A B C E F G I K:E G B C A F I K
A B C E F G I L:E G B C A F L I
A B C E F G J K:E G B C A F J K
A B C E F G J L:E G B C A F L J
A B C E F G K L:E G B C A F L K
A B C E F H I J:H J B C A F E I
A B C E F H I K:H E B C A F I K
A B C E F H I L:H E B C A F L I
A B C E F H J K:H J B C A F E K
A B C E F H J L:H J B C A F L E
A B C E F H K L:H E B C A F L K
A B C E F I J K:E J B C A F I K
A B C E F I J L:E J B C A F L I
A B C E F I K L:E I B C A F L K
A B C E F J K L:E J B C A F L K
A B C E G H I J:H J B C A G E I
A B C E G H I K:E G B C A H I K
A B C E G H I L:E G B C A H L I
A B C E G H J K:H J B C A G E K
A B C E G H J L:H J B C A G L E
A B C E G H K L:E G B C A H L K
A B C E G I J K:E J B C A G I K
A B C E G I J L:E J B C A G L I
A B C E G I K L:E G B A I C L K
A B C E G J K L:E J B C A G L K
A B C E H I J K:E J B C A H I K
A B C E H I J L:E J B C A H L I
A B C E H I K L:E I B C A H L K
A B C E H J K L:E J B C A H L K
A B C E I J K L:E J B A I C L K
A B C F G H I J:H G B C A F I J
A B C F G H I K:H G B C A F I K
A B C F G H I L:H G B C A F L I
A B C F G H J K:H G B C A F J K
A B C F G H J L:H G B C A F L J
A B C F G H K L:H G B C A F L K
A B C F G I J K:C J B F A G I K
A B C F G I J L:C J B F A G L I
A B C F G I K L:I G B C A F L K
A B C F G J K L:C J B F A G L K
A B C F H I J K:H J B C A F I K
A B C F H I J L:H J B C A F L I
A B C F H I K L:H I B C A F L K
A B C F H J K L:H J B C A F L K
A B C F I J K L:I J B C A F L K
A B C G H I J K:H J B C A G I K
A B C G H I J L:H J B C A G L I
A B C G H I K L:I G B C A H L K
A B C G H J K L:H J B C A G L K
A B C G I J K L:I J B C A G L K
A B C H I J K L:I J B C A H L K
A B D E F G H I:H G B D A F E I
A B D E F G H J:H G B D A F E J
A B D E F G H K:H G B D A F E K
A B D E F G H L:H G B D A F L E
A B D E F G I J:E G B D A F I J
A B D E F G I K:E G B D A F I K
A B D E F G I L:E G B D A F L I
A B D E F G J K:E G B D A F J K
A B D E F G J L:E G B D A F L J
A B D E F G K L:E G B D A F L K
A B D E F H I J:H J B D A F E I
A B D E F H I K:H E B D A F I K
A B D E F H I L:H E B D A F L I
A B D E F H J K:H J B D A F E K
A B D E F H J L:H J B D A F L E
A B D E F H K L:H E B D A F L K
A B D E F I J K:E J B D A F I K
A B D E F I J L:E J B D A F L I
A B D E F I K L:E I B D A F L K
A B D E F J K L:E J B D A F L K
A B D E G H I J:H J B D A G E I
A B D E G H I K:E G B D A H I K
A B D E G H I L:E G B D A H L I
A B D E G H J K:H J B D A G E K
A B D E G H J L:H J B D A G L E
A B D E G H K L:E G B D A H L K
A B D E G I J K:E J B D A G I K
A B D E G I J L:E J B D A G L I
A B D E G I K L:E G B A I D L K
A B D E G J K L:E J B D A G L K
A B D E H I J K:E J B D A H I K
A B D E H I J L:E J B D A H L I
A B D E H I K L:E I B D A H L K
A B D E H J K L:E J B D A H L K
A B D E I J K L:E J B A I D L K
A B D F G H I J:H G B D A F I J
A B D F G H I K:H G B D A F I K
A B D F G H I L:H G B D A F L I
A B D F G H J K:H G B D A F J K
A B D F G H J L:H G B D A F L J
A B D F G H K L:H G B D A F L K
A B D F G I J K:F J B D A G I K
A B D F G I J L:F J B D A G L I
A B D F G I K L:I G B D A F L K
A B D F G J K L:F J B D A G L K
A B D F H I J K:H J B D A F I K
A B D F H I J L:H J B D A F L I
A B D F H I K L:H I B D A F L K
A B D F H J K L:H J B D A F L K
A B D F I J K L:I J B D A F L K
A B D G H I J K:H J B D A G I K
A B D G H I J L:H J B D A G L I
A B D G H I K L:I G B D A H L K
A B D G H J K L:H J B D A G L K
A B D G I J K L:I J B D A G L K
A B D H I J K L:I J B D A H L K
A B E F G H I J:H J B F A G E I
A B E F G H I K:E G B F A H I K
A B E F G H I L:E G B F A H L I
A B E F G H J K:H J B F A G E K
A B E F G H J L:H J B F A G L E
A B E F G H K L:E G B F A H L K
A B E F G I J K:E J B F A G I K
A B E F G I J L:E J B F A G L I
A B E F G I K L:E G B A I F L K
A B E F G J K L:E J B F A G L K
A B E F H I J K:E J B F A H I K
A B E F H I J L:E J B F A H L I
A B E F H I K L:E I B F A H L K
A B E F H J K L:E J B F A H L K
A B E F I J K L:E J B A I F L K
A B E G H I J K:E J B A H G I K
A B E G H I J L:E J B A H G L I
A B E G H I K L:E G B A I H L K
A B E G H J K L:E J B A H G L K
A B E G I J K L:E J B A I G L K
A B E H I J K L:E J B A I H L K
A B F G H I J K:H J B F A G I K
A B F G H I J L:H J B F A G L I
A B F G H I K L:H G B A I F L K
A B F G H J K L:H J B F A G L K
A B F G I J K L:I J B F A G L K
A B F H I J K L:H J B A I F L K
A B G H I J K L:H J B A I G L K
A C D E F G H I:H G E C A F D I
A C D E F G H J:H G J C A F D E
A C D E F G H K:H G E C A F D K
A C D E F G H L:H G F C A D L E
A C D E F G I J:C G J D A F E I
A C D E F G I K:C G E D A F I K
A C D E F G I L:C G E D A F L I
A C D E F G J K:C G J D A F E K
A C D E F G J L:C G J D A F L E
A C D E F G K L:C G E D A F L K
A C D E F H I J:H J E C A F D I
A C D E F H I K:H E F C A D I K
A C D E F H I L:H E F C A D L I
A C D E F H J K:H J E C A F D K
A C D E F H J L:H J F C A D L E
A C D E F H K L:H E F C A D L K
A C D E F I J K:C J E D A F I K
A C D E F I J L:C J E D A F L I
A C D E F I K L:C E I D A F L K
A C D E F J K L:C J E D A F L K
A C D E G H I J:H G J C A D E I
A C D E G H I K:H G E C A D I K
A C D E G H I L:H G E C A D L I
A C D E G H J K:H G J C A D E K
A C D E G H J L:H G J C A D L E
A C D E G H K L:H G E C A D L K
A C D E G I J K:E G J C A D I K
A C D E G I J L:E G J C A D L I
A C D E G I K L:E G I C A D L K
A C D E G J K L:E G J C A D L K
A C D E H I J K:H J E C A D I K
A C D E H I J L:H J E C A D L I
A C D E H I K L:H E I C A D L K
A C D E H J K L:H J E C A D L K
A C D E I J K L:E J I C A D L K
A C D F G H I J:H G J C A F D I
A C D F G H I K:H G F C A D I K
A C D F G H I L:H G F C A D L I
A C D F G H J K:H G J C A F D K
A C D F G H J L:C G J D A F L H
A C D F G H K L:H G F C A D L K
A C D F G I J K:C G J D A F I K
A C D F G I J L:C G J D A F L I
A C D F G I K L:C G I D A F L K
A C D F G J K L:C G J D A F L K
A C D F H I J K:H J F C A D I K
A C D F H I J L:H J F C A D L I
A C D F H I K L:H F I C A D L K
A C D F H J K L:H J F C A D L K
A C D F I J K L:C J I D A F L K
A C D G H I J K:H G J C A D I K
A C D G H I J L:H G J C A D L I
A C D G H I K L:H G I C A D L K
A C D G H J K L:H G J C A D L K
A C D G I J K L:I G J C A D L K
A C D H I J K L:H J I C A D L K
A C E F G H I J:H G J C A F E I
A C E F G H I K:H G E C A F I K
A C E F G H I L:H G E C A F L I
A C E F G H J K:H G J C A F E K
A C E F G H J L:H G J C A F L E
A C E F G H K L:H G E C A F L K
A C E F G I J K:E G J C A F I K
A C E F G I J L:E G J C A F L I
A C E F G I K L:E G I C A F L K
A C E F G J K L:E G J C A F L K
A C E F H I J K:H J E C A F I K
A C E F H I J L:H J E C A F L I
A C E F H I K L:H E I C A F L K
A C E F H J K L:H J E C A F L K
A C E F I J K L:E J I C A F L K
A C E G H I J K:E G J C A H I K
A C E G H I J L:E G J C A H L I
A C E G H I K L:E G I C A H L K
A C E G H J K L:E G J C A H L K
A C E G I J K L:E J I C A G L K
A C E H I J K L:E J I C A H L K
A C F G H I J K:H G J C A F I K
A C F G H I J L:H G J C A F L I
A C F G H I K L:H G I C A F L K
A C F G H J K L:H G J C A F L K
A C F G I J K L:I G J C A F L K
A C F H I J K L:H J I C A F L K
A C G H I J K L:H J I C A G L K
A D E F G H I J:H G J D A F E I
A D E F G H I K:H G E D A F I K
A D E F G H I L:H G E D A F L I
A D E F G H J K:H G J D A F E K
A D E F G H J L:H G J D A F L E
A D E F G H K L:H G E D A F L K
A D E F G I J K:E G J D A F I K
A D E F G I J L:E G J D A F L I
A D E F G I K L:E G I D A F L K
A D E F G J K L:E G J D A F L K
A D E F H I J K:H J E D A F I K
A D E F H I J L:H J E D A F L I
A D E F H I K L:H E I D A F L K
A D E F H J K L:H J E D A F L K
A D E F I J K L:E J I D A F L K
A D E G H I J K:E G J D A H I K
A D E G H I J L:E G J D A H L I
A D E G H I K L:E G I D A H L K
A D E G H J K L:E G J D A H L K
A D E G I J K L:E J I D A G L K
A D E H I J K L:E J I D A H L K
A D F G H I J K:H G J D A F I K
A D F G H I J L:H G J D A F L I
A D F G H I K L:H G I D A F L K
A D F G H J K L:H G J D A F L K
A D F G I J K L:I G J D A F L K
A D F H I J K L:H J I D A F L K
A D G H I J K L:H J I D A G L K
A E F G H I J K:E G J F A H I K
A E F G H I J L:E G J F A H L I
A E F G H I K L:E G I F A H L K
A E F G H J K L:E G J F A H L K
A E F G I J K L:E J I F A G L K
A E F H I J K L:E J I F A H L K
A E G H I J K L:E J I A H G L K
A F G H I J K L:H J I F A G L K
B C D E F G H I:C G B D H F E I
B C D E F G H J:H G B C J F D E
B C D E F G H K:H G B C H F D K
B C D E F G H L:C G B D H F L E
B C D E F G I J:C E B D J F E I
B C D E F G I K:C E B D E F I K
B C D E F G I L:C E B D E F L I
B C D E F G J K:C J B D J F E K
B C D E F G J L:C J B D J F L E
B C D E F G K L:C E B D E F L K
B C D E F H I J:C J B D H F E I
B C D E F H I K:C E B D H F I K
B C D E F H I L:C E B D H F L I
B C D E F H J K:C J B D H F E K
B C D E F H J L:C J B D H F L E
B C D E F H K L:C E B D H F L K
B C D E F I J K:C J B D E F I K
B C D E F I J L:C J B D E F L I
B C D E F I K L:C E B D I F L K
B C D E F J K L:C J B D E F L K
B C D E G H I J:H G B C J D E I
B C D E G H I K:E G B C H D I K
B C D E G H I L:E G B C H D L I
B C D E G H J K:H G B C J D E K
B C D E G H J L:H G B C J D L E
B C D E G H K L:E G B C H D L K
B C D E G I J K:E G B C J D I K
B C D E G I J L:E G B C J D L I
B C D E G I K L:E G B C I D L K
B C D E G J K L:E G B C J D L K
B C D E H I J K:E J B C H D I K
B C D E H I J L:E J B C H D L I
B C D E H I K L:E I B C H D L K
B C D E H J K L:E J B C H D L K
B C D E I J K L:E J B C I D L K
B C D F G H I J:H G B C J F D I
B C D F G H I K:C G B D H F I K
B C D F G H I L:C G B D H F L I
B C D F G H J K:H G B C J F D K
B C D F G H J L:C G B D H F L J
B C D F G H K L:C G B D H F L K
B C D F G I J K:C G B D J F I K
B C D F G I J L:C G B D J F L I
B C D F G I K L:C G B D I F L K
B C D F G J K L:C G B D J F L K
B C D F H I J K:C J B D H F I K
B C D F H I J L:C J B D H F L I
B C D F H I K L:C I B D H F L K
B C D F H J K L:C J B D H F L K
B C D F I J K L:C J B D I F L K
B C D G H I J K:H G B C J D I K
B C D G H I J L:H G B C J D L I
B C D G H I K L:H G B C I D L K
B C D G H J K L:H G B C J D L K
B C D G I J K L:I G B C J D L K
B C D H I J K L:H J B C I D L K
B C E F G H I J:H G B C J F E I
B C E F G H I K:E G B C H F I K
B C E F G H I L:E G B C H F L I
B C E F G H J K:H G B C J F E K
B C E F G H J L:H G B C J F L E
B C E F G H K L:E G B C H F L K
B C E F G I J K:E G B C J F I K
B C E F G I J L:E G B C J F L I
B C E F G I K L:E G B C I F L K
B C E F G J K L:E G B C J F L K
B C E F H I J K:E J B C H F I K
B C E F H I J L:E J B C H F L I
B C E F H I K L:E I B C H F L K
B C E F H J K L:E J B C H F L K
B C E F I J K L:E J B C I F L K
B C E G H I J K:E J B C H G I K
B C E G H I J L:E J B C H G L I
B C E G H I K L:E G B C I H L K
B C E G H J K L:E J B C H G L K
B C E G I J K L:E J B C I G L K
B C E H I J K L:E J B C I H L K
B C F G H I J K:H G B C J F I K
B C F G H I J L:H G B C J F L I
B C F G H I K L:H G B C I F L K
B C F G H J K L:H G B C J F L K
B C F G I J K L:I G B C J F L K
B C F H I J K L:H J B C I F L K
B C G H I J K L:H J B C I G L K
B D E F G H I J:H G B D J F E I
B D E F G H I K:E G B D H F I K
B D E F G H I L:E G B D H F L I
B D E F G H J K:H G B D J F E K
B D E F G H J L:H G B D J F L E
B D E F G H K L:E G B D H F L K
B D E F G I J K:E G B D J F I K
B D E F G I J L:E G B D J F L I
B D E F G I K L:E G B D I F L K
B D E F G J K L:E G B D J F L K
B D E F H I J K:E J B D H F I K
B D E F H I J L:E J B D H F L I
B D E F H I K L:E I B D H F L K
B D E F H J K L:E J B D H F L K
B D E F I J K L:E J B D I F L K
B D E G H I J K:E J B D H G I K
B D E G H I J L:E J B D H G L I
B D E G H I K L:E G B D I H L K
B D E G H J K L:E J B D H G L K
B D E G I J K L:E J B D I G L K
B D E H I J K L:E J B D I H L K
B D F G H I J K:H G B D J F I K
B D F G H I J L:H G B D J F L I
B D F G H I K L:H G B D I F L K
B D F G H J K L:H G B D J F L K
B D F G I J K L:I G B D J F L K
B D F H I J K L:H J B D I F L K
B D G H I J K L:H J B D I G L K
B E F G H I J K:E J B F H G I K
B E F G H I J L:E J B F H G L I
B E F G H I K L:E G B F I H L K
B E F G H J K L:E J B F H G L K
B E F G I J K L:E J B F I G L K
B E F H I J K L:E J B F I H L K
B E G H I J K L:E J I B H G L K
B F G H I J K L:H J B F I G L K
C D E F G H I J:C G J D H F E I
C D E F G H I K:C G E D H F I K
C D E F G H I L:C G E D H F L I
C D E F G H J K:C G J D H F E K
C D E F G H J L:C G J D H F L E
C D E F G H K L:C G E D H F L K
C D E F G I J K:C G E D J F I K
C D E F G I J L:C G E D J F L I
C D E F G I K L:C G E D I F L K
C D E F G J K L:C G E D J F L K
C D E F H I J K:C J E D H F I K
C D E F H I J L:C J E D H F L I
C D E F H I K L:C E I D H F L K
C D E F H J K L:C J E D H F L K
C D E F I J K L:C J E D I F L K
C D E G H I J K:E G J C H D I K
C D E G H I J L:E G J C H D L I
C D E G H I K L:E G I C H D L K
C D E G H J K L:E G J C H D L K
C D E G I J K L:E G I C J D L K
C D E H I J K L:E J I C H D L K
C D F G H I J K:C G J D H F I K
C D F G H I J L:C G J D H F L I
C D F G H I K L:C G I D H F L K
C D F G H J K L:C G J D H F L K
C D F G I J K L:C G I D J F L K
C D F H I J K L:C J I D H F L K
C D G H I J K L:H G I C J D L K
C E F G H I J K:E G J C H F I K
C E F G H I J L:E G J C H F L I
C E F G H I K L:E G I C H F L K
C E F G H J K L:E G J C H F L K
C E F G I J K L:E G I C J F L K
C E F H I J K L:E J I C H F L K
C E G H I J K L:E J I C H G L K
C F G H I J K L:H G I C J F L K
D E F G H I J K:E G J D H F I K
D E F G H I J L:E G J D H F L I
D E F G H I K L:E G I D H F L K
D E F G H J K L:E G J D H F L K
D E F G I J K L:E G I D J F L K
D E F H I J K L:E J I D H F L K
D E G H I J K L:E J I D H G L K
D F G H I J K L:H G I D J F L K
E F G H I J K L:E J I F H G L K
"""

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


def verify_r32_against_wikipedia(computed_r32):
    """
    Fetch the WC2026 knockout stage Wikipedia page and compare R32 matchups
    against our computed bracket.

    Returns a dict:
      {
        'verified':    bool,      # True only if all 16 matches match
        'wiki_parsed': int,       # number of R32 matches successfully parsed
        'mismatches':  list,      # [{match, wikipedia, computed}]
        'error':       str|None,  # non-None if fetch/parse failed
      }
    """
    try:
        resp = requests.get(
            'https://en.wikipedia.org/w/api.php',
            params={
                'action':  'parse',
                'page':    '2026_FIFA_World_Cup_knockout_stage',
                'prop':    'wikitext',
                'format':  'json',
            },
            timeout=30,
            headers={'User-Agent': 'wc26-pool-bot/1.0 (github.com/riteshwarade/wc26)'},
        )
        resp.raise_for_status()
        wikitext = resp.json()['parse']['wikitext']['*']
    except Exception as e:
        return {'verified': False, 'wiki_parsed': 0, 'mismatches': [], 'error': str(e)}

    wiki_r32 = {}
    for m in range(73, 89):
        # Wikipedia bracket wikitext has patterns like:
        #   {{fb|MEX}}\n...\nMatch 73\n...\n{{fb|SUI}}
        # The fb template may be fbr, fbl, fbx etc.
        pattern = (
            r'\{\{fb[a-z]*\|([A-Z]{2,3})\}[^\n]*\n'   # team 1 line
            r'(?:[^\n]*\n){0,4}'                        # 0–4 lines between
            r'[^\n]*Match\s+' + str(m) + r'[^\n]*\n'   # match number line
            r'(?:[^\n]*\n){0,4}'                        # 0–4 lines between
            r'[^\n]*\{\{fb[a-z]*\|([A-Z]{2,3})\}'      # team 2
        )
        match = re.search(pattern, wikitext, re.IGNORECASE)
        if match:
            home = TEAM_CODES.get(match.group(1).upper())
            away = TEAM_CODES.get(match.group(2).upper())
            if home and away:
                wiki_r32[m] = (home, away)

    if len(wiki_r32) < 16:
        return {
            'verified':    False,
            'wiki_parsed': len(wiki_r32),
            'mismatches':  [],
            'error':       f'Wikipedia bracket not yet fully populated ({len(wiki_r32)}/16 R32 matches parsed)',
        }

    mismatches = []
    for m in range(73, 89):
        wiki_home, wiki_away   = wiki_r32[m]
        comp_home, comp_away   = computed_r32.get(m, (None, None))
        if {wiki_home, wiki_away} != {comp_home, comp_away}:
            mismatches.append({
                'match':     m,
                'wikipedia': f'{wiki_home} vs {wiki_away}',
                'computed':  f'{comp_home} vs {comp_away}',
            })

    return {
        'verified':    len(mismatches) == 0,
        'wiki_parsed': len(wiki_r32),
        'mismatches':  mismatches,
        'error':       None,
    }


def write_bracket_json(results):
    """
    Write knockout_bracket.json:
    - Provisional (confirmed=false): once all 12 groups have ≥1 result (after round 1)
    - Confirmed   (confirmed=true):  all 72 group results present AND
                                     Wikipedia knockout bracket matches our computed R32
    """
    # Check which groups have started
    groups_started = set()
    for num, grp, t1, t2 in GROUP_MATCHES:
        if num in results:
            groups_started.add(grp)

    if len(groups_started) < 12:
        print(f'Only {len(groups_started)}/12 groups have started — bracket not yet generated')
        return

    all_played = len(results) >= 72
    status     = 'provisional'
    wiki_check = None

    if all_played:
        print('All 72 group matches played — cross-checking R32 against Wikipedia...')

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

    # Cross-check R32 against Wikipedia once all 72 matches are played
    if all_played:
        wiki_check = verify_r32_against_wikipedia(r32)
        if wiki_check['error']:
            print(f'  Wikipedia check failed: {wiki_check["error"]}')
        elif wiki_check['verified']:
            status = 'confirmed'
            print(f'  ✓ Wikipedia verified — all {wiki_check["wiki_parsed"]} R32 matches match')
        else:
            print(f'  ✗ Wikipedia mismatch — {len(wiki_check["mismatches"])} discrepancies:')
            for mm in wiki_check['mismatches']:
                print(f'    M{mm["match"]}: computed={mm["computed"]} | wikipedia={mm["wikipedia"]}')
    else:
        print(f'Generating provisional bracket ({len(results)}/72 matches played)...')

    confirmed = (status == 'confirmed')

    import datetime
    bracket = {
        'generated_at': datetime.datetime.utcnow().isoformat() + 'Z',
        'confirmed': confirmed,
        'status': status,
        'matches_played': len(results),
        'source': 'Wikipedia (canonical)',
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
    # ── Group stage: results + bracket ────────────────────────────────────────
    print('Fetching ESPN group-stage events (M1–M72)...')
    group_events = fetch_espn_group_events()
    print(f'Got {len(group_events)} group events')

    print('Parsing group results...')
    results = parse_group_results_espn(group_events)
    print(f'Found {len(results)} completed group matches')
    write_csv(results)
    write_bracket_json(results)

    # ── Knockout stage: results ────────────────────────────────────────────────
    bracket_path = 'data/knockout_bracket.json'
    if os.path.exists(bracket_path):
        with open(bracket_path, encoding='utf-8') as _f:
            bracket_data = json.load(_f)
        print('\nFetching ESPN knockout-stage events (M73–M104)...')
        ko_events = fetch_espn_ko_events()
        print(f'Got {len(ko_events)} KO events')
        print('Parsing knockout results...')
        ko_results, ko_scores = parse_ko_results_espn(ko_events, bracket_data)
        print(f'Found {len(ko_results)} completed KO matches')
        for m in sorted(ko_results):
            print(f'  M{m}: {ko_results[m]}')
        write_ko_results_csv(ko_results, ko_scores)
    else:
        print('\nNo knockout_bracket.json yet — KO results will run once bracket is confirmed')
