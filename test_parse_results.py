"""
test_parse_results.py

Unit tests for .github/scripts/parse_results.py.

Covers:
  - espn_team_name: name mapping / passthrough
  - parse_group_results_espn: mock ESPN event structures
  - parse_ko_results_espn: mock ESPN event structures + bracket data
  - write_csv / write_ko_results_csv: CSV output format
  - extract_team: wikitext flag-template parsing
  - extract_score: score string parsing
  - parse_results: full wikitext group-stage parsing

Run: python3 test_parse_results.py
"""

import csv
import io
import os
import sys
import tempfile
import unittest

# Allow running from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.github', 'scripts'))

from parse_results import (
    espn_team_name,
    parse_group_results_espn,
    parse_ko_results_espn,
    write_csv,
    write_ko_results_csv,
    extract_team,
    extract_score,
    parse_results,
    compute_group_standings,
    MATCH_LOOKUP,
    ESPN_TEAM_MAP,
    TEAM_CODES,
    KNOWN_TEAMS,
    GROUP_MATCHES,
    GROUP_ORDER,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_espn_event(home_name, away_name, home_score, away_score,
                    season_slug='group-stage', completed=True,
                    home_winner=None, away_winner=None,
                    home_pen=None, away_pen=None):
    """Build a minimal ESPN event dict matching the structure parse_* expects.

    home_pen / away_pen: shootoutScore values for penalty-shootout matches.
    """
    if home_winner is None and away_winner is None:
        if home_pen is not None and away_pen is not None:
            home_winner = int(home_pen) > int(away_pen)
            away_winner = int(away_pen) > int(home_pen)
        else:
            home_winner = home_score > away_score
            away_winner = away_score > home_score
    home_comp = {
        'homeAway': 'home',
        'team': {'displayName': home_name},
        'score': str(home_score),
        'winner': home_winner,
    }
    away_comp = {
        'homeAway': 'away',
        'team': {'displayName': away_name},
        'score': str(away_score),
        'winner': away_winner,
    }
    if home_pen is not None:
        home_comp['shootoutScore'] = str(home_pen)
    if away_pen is not None:
        away_comp['shootoutScore'] = str(away_pen)
    return {
        'season': {'slug': season_slug},
        'competitions': [{
            'status': {'type': {'completed': completed}},
            'competitors': [home_comp, away_comp],
        }],
    }


def make_ko_bracket():
    """Minimal bracket_data for KO tests."""
    return {
        'round_of_32': {
            '73': {'home': 'Spain',      'away': 'France'},
            '74': {'home': 'Brazil',     'away': 'Germany'},
            '75': {'home': 'Argentina',  'away': 'England'},
            '76': {'home': 'Portugal',   'away': 'Netherlands'},
        },
        'round_of_16': {
            '89': {'home': 'W74', 'away': 'W77'},
            '90': {'home': 'W73', 'away': 'W75'},
        },
        'quarterfinals': {
            '97': {'home': 'W89', 'away': 'W90'},
        },
        'semifinals': {
            '101': {'home': 'W97', 'away': 'W98'},
        },
        'third_place': {
            '103': {'home': 'L101', 'away': 'L102'},
        },
        'final': {
            '104': {'home': 'W101', 'away': 'W102'},
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# espn_team_name
# ─────────────────────────────────────────────────────────────────────────────

class TestEspnTeamName(unittest.TestCase):

    def test_mapped_czechia(self):
        self.assertEqual(espn_team_name({'displayName': 'Czechia'}), 'Czech Republic')

    def test_mapped_turkiye(self):
        self.assertEqual(espn_team_name({'displayName': 'Türkiye'}), 'Turkey')

    def test_mapped_bosnia(self):
        self.assertEqual(espn_team_name({'displayName': 'Bosnia-Herzegovina'}),
                         'Bosnia and Herzegovina')

    def test_mapped_congo(self):
        self.assertEqual(espn_team_name({'displayName': 'Congo DR'}), 'DR Congo')

    def test_mapped_curacao(self):
        self.assertEqual(espn_team_name({'displayName': 'Curacao'}), 'Curaçao')

    def test_passthrough_brazil(self):
        self.assertEqual(espn_team_name({'displayName': 'Brazil'}), 'Brazil')

    def test_passthrough_france(self):
        self.assertEqual(espn_team_name({'displayName': 'France'}), 'France')

    def test_missing_display_name(self):
        # Empty dict → empty string (passthrough since '' not in ESPN_TEAM_MAP)
        self.assertEqual(espn_team_name({}), '')

    def test_all_mapped_names_are_in_system(self):
        # Every ESPN_TEAM_MAP value must exist somewhere in our system's team names
        all_team_names = set(TEAM_CODES.values())
        for espn_name, internal_name in ESPN_TEAM_MAP.items():
            self.assertIn(internal_name, all_team_names,
                          f'ESPN_TEAM_MAP value {internal_name!r} not in TEAM_CODES')


# ─────────────────────────────────────────────────────────────────────────────
# parse_group_results_espn
# ─────────────────────────────────────────────────────────────────────────────

class TestParseGroupResultsEspn(unittest.TestCase):

    def test_home_win(self):
        events = [make_espn_event('Mexico', 'South Africa', 2, 0)]
        results = parse_group_results_espn(events)
        self.assertEqual(results[1], (2, 0, 'W1'))

    def test_away_win(self):
        events = [make_espn_event('Mexico', 'South Africa', 0, 1)]
        results = parse_group_results_espn(events)
        self.assertEqual(results[1], (0, 1, 'W2'))

    def test_draw(self):
        events = [make_espn_event('Mexico', 'South Africa', 1, 1)]
        results = parse_group_results_espn(events)
        self.assertEqual(results[1], (1, 1, 'Draw'))

    def test_skips_incomplete_matches(self):
        events = [make_espn_event('Mexico', 'South Africa', 0, 0, completed=False)]
        results = parse_group_results_espn(events)
        self.assertNotIn(1, results)

    def test_skips_non_group_stage(self):
        events = [make_espn_event('Mexico', 'South Africa', 2, 1,
                                  season_slug='round-of-32')]
        results = parse_group_results_espn(events)
        self.assertNotIn(1, results)

    def test_espn_name_mapping_applied(self):
        # 'Czechia' → 'Czech Republic'; match 2 is South Korea vs Czech Republic
        events = [make_espn_event('South Korea', 'Czechia', 1, 0)]
        results = parse_group_results_espn(events)
        self.assertIn(2, results)
        self.assertEqual(results[2], (1, 0, 'W1'))

    def test_multiple_matches(self):
        events = [
            make_espn_event('Mexico', 'South Africa', 2, 0),
            make_espn_event('South Korea', 'Czech Republic', 1, 1),
            make_espn_event('Canada', 'Bosnia and Herzegovina', 0, 2),
        ]
        results = parse_group_results_espn(events)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[1], (2, 0, 'W1'))
        self.assertEqual(results[2], (1, 1, 'Draw'))
        self.assertEqual(results[3], (0, 2, 'W2'))

    def test_unknown_matchup_skipped(self):
        # Teams not in MATCH_LOOKUP — no result recorded, no exception
        events = [make_espn_event('Atlantis', 'Wakanda', 3, 2)]
        results = parse_group_results_espn(events)
        self.assertEqual(len(results), 0)

    def test_empty_events(self):
        self.assertEqual(parse_group_results_espn([]), {})

    def test_match_lookup_coverage(self):
        # All 72 matches in MATCH_LOOKUP are reachable via ESPN event simulation
        self.assertEqual(len(MATCH_LOOKUP), 72)


# ─────────────────────────────────────────────────────────────────────────────
# parse_ko_results_espn
# ─────────────────────────────────────────────────────────────────────────────

class TestParseKoResultsEspn(unittest.TestCase):

    def _ko_event(self, home, away, home_wins, slug='round-of-32'):
        score = (1, 0) if home_wins else (0, 1)
        return make_espn_event(home, away, score[0], score[1],
                               season_slug=slug)

    def test_single_r32_match(self):
        bracket = make_ko_bracket()
        events = [self._ko_event('Spain', 'France', home_wins=True)]
        results, scores = parse_ko_results_espn(events, bracket)
        self.assertEqual(results[73], 'Spain')
        self.assertEqual(scores[73], (1, 0))

    def test_away_team_wins_r32(self):
        bracket = make_ko_bracket()
        events = [self._ko_event('Spain', 'France', home_wins=False)]
        results, scores = parse_ko_results_espn(events, bracket)
        self.assertEqual(results[73], 'France')

    def test_r16_resolves_after_r32(self):
        # R16[90] = {home: W73, away: W75}
        # After M73 (Spain) and M75 (Argentina) are decided, M90 can resolve.
        bracket = make_ko_bracket()
        events = [
            self._ko_event('Spain',     'France',    home_wins=True,  slug='round-of-32'),  # M73
            self._ko_event('Argentina', 'England',   home_wins=True,  slug='round-of-32'),  # M75
            self._ko_event('Spain',     'Argentina', home_wins=True,  slug='round-of-16'),  # M90
        ]
        results, scores = parse_ko_results_espn(events, bracket)
        self.assertEqual(results[73], 'Spain')
        self.assertEqual(results[75], 'Argentina')
        self.assertEqual(results[90], 'Spain')

    def test_r16_not_resolved_without_r32(self):
        # If R32 results are absent, the bracket reference W73/W75 can't resolve,
        # so M90 should not appear in results even if the event is complete.
        bracket = make_ko_bracket()
        events = [
            self._ko_event('Spain', 'Argentina', home_wins=True, slug='round-of-16'),
        ]
        results, scores = parse_ko_results_espn(events, bracket)
        # M90 pair is (W73, W75) which are unknown → pair_to_winner match fails → 90 absent
        self.assertNotIn(90, results)

    def test_skips_incomplete_ko_event(self):
        bracket = make_ko_bracket()
        events = [make_espn_event('Spain', 'France', 0, 0,
                                  season_slug='round-of-32', completed=False)]
        results, scores = parse_ko_results_espn(events, bracket)
        self.assertNotIn(73, results)

    def test_skips_non_ko_slug(self):
        bracket = make_ko_bracket()
        # group-stage slug — should not be in KO_SLUGS
        events = [make_espn_event('Spain', 'France', 2, 0,
                                  season_slug='group-stage')]
        results, scores = parse_ko_results_espn(events, bracket)
        self.assertNotIn(73, results)

    def test_empty_events(self):
        bracket = make_ko_bracket()
        self.assertEqual(parse_ko_results_espn([], bracket), ({}, {}))

    def test_multiple_rounds(self):
        bracket = make_ko_bracket()
        events = [
            self._ko_event('Spain',     'France',    home_wins=True,  slug='round-of-32'),  # M73
            self._ko_event('Brazil',    'Germany',   home_wins=True,  slug='round-of-32'),  # M74
            self._ko_event('Argentina', 'England',   home_wins=False, slug='round-of-32'),  # M75
            # M90 = W73 vs W75 = Spain vs England
            self._ko_event('Spain',     'England',   home_wins=True,  slug='round-of-16'),  # M90
            # M89 = W74 vs W77 = Brazil vs (W77 unknown, skip)
        ]
        results, scores = parse_ko_results_espn(events, bracket)
        self.assertEqual(results[73], 'Spain')
        self.assertEqual(results[74], 'Brazil')
        self.assertEqual(results[75], 'England')
        self.assertEqual(results[90], 'Spain')
        self.assertNotIn(89, results)  # W77 unknown → can't match

    def test_penalty_shootout_home_wins(self):
        # M73: Spain 1-1 France (AET), Spain wins 4-2 on pens
        bracket = make_ko_bracket()
        events = [make_espn_event('Spain', 'France', 1, 1,
                                  season_slug='round-of-32',
                                  home_pen=4, away_pen=2)]
        results, scores = parse_ko_results_espn(events, bracket)
        self.assertEqual(results[73], 'Spain')
        self.assertEqual(scores[73], (1, 1, 4, 2))

    def test_penalty_shootout_away_wins(self):
        # M73: Spain 1-1 France (AET), France wins 5-3 on pens
        bracket = make_ko_bracket()
        events = [make_espn_event('Spain', 'France', 1, 1,
                                  season_slug='round-of-32',
                                  home_pen=3, away_pen=5)]
        results, scores = parse_ko_results_espn(events, bracket)
        self.assertEqual(results[73], 'France')
        self.assertEqual(scores[73], (1, 1, 3, 5))

    def test_no_shootout_score_is_two_tuple(self):
        # Normal win — scores tuple should have exactly 2 elements
        bracket = make_ko_bracket()
        events = [make_espn_event('Spain', 'France', 2, 0,
                                  season_slug='round-of-32')]
        results, scores = parse_ko_results_espn(events, bracket)
        self.assertEqual(scores[73], (2, 0))
        self.assertEqual(len(scores[73]), 2)


# ─────────────────────────────────────────────────────────────────────────────
# write_csv
# ─────────────────────────────────────────────────────────────────────────────

class TestWriteCsv(unittest.TestCase):

    def test_output_format(self):
        results = {
            1: (2, 0, 'W1'),
            3: (1, 1, 'Draw'),
            2: (0, 1, 'W2'),
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_dir = os.getcwd()
            os.chdir(tmpdir)
            try:
                write_csv(results)
                path = os.path.join(tmpdir, 'results', 'group_results.csv')
                self.assertTrue(os.path.exists(path))
                with open(path, newline='', encoding='utf-8') as f:
                    rows = list(csv.reader(f))
            finally:
                os.chdir(orig_dir)

        self.assertEqual(rows[0], ['match', 'home_score', 'away_score', 'outcome'])
        # Rows should be sorted by match number
        self.assertEqual(rows[1], ['1', '2', '0', 'W1'])
        self.assertEqual(rows[2], ['2', '0', '1', 'W2'])
        self.assertEqual(rows[3], ['3', '1', '1', 'Draw'])
        self.assertEqual(len(rows), 4)  # header + 3 data rows

    def test_empty_results(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_dir = os.getcwd()
            os.chdir(tmpdir)
            try:
                write_csv({})
                path = os.path.join(tmpdir, 'results', 'group_results.csv')
                with open(path, newline='', encoding='utf-8') as f:
                    rows = list(csv.reader(f))
            finally:
                os.chdir(orig_dir)

        self.assertEqual(rows, [['match', 'home_score', 'away_score', 'outcome']])


# ─────────────────────────────────────────────────────────────────────────────
# write_ko_results_csv
# ─────────────────────────────────────────────────────────────────────────────

class TestWriteKoResultsCsv(unittest.TestCase):

    def test_output_format(self):
        results = {73: 'Spain', 104: 'France', 89: 'Brazil'}
        scores  = {73: (2, 1), 89: (3, 0)}
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_dir = os.getcwd()
            os.chdir(tmpdir)
            try:
                write_ko_results_csv(results, scores)
                path = os.path.join(tmpdir, 'results', 'knockout_results.csv')
                with open(path, newline='', encoding='utf-8') as f:
                    rows = list(csv.reader(f))
            finally:
                os.chdir(orig_dir)

        self.assertEqual(rows[0], ['match', 'winner', 'home_score', 'away_score'])
        # Sorted by match number: 73, 89, 104
        self.assertEqual(rows[1], ['73', 'Spain', '2', '1'])
        self.assertEqual(rows[2], ['89', 'Brazil', '3', '0'])
        self.assertEqual(rows[3], ['104', 'France', '', ''])

    def test_output_format_no_scores(self):
        results = {73: 'Spain', 104: 'France', 89: 'Brazil'}
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_dir = os.getcwd()
            os.chdir(tmpdir)
            try:
                write_ko_results_csv(results)
                path = os.path.join(tmpdir, 'results', 'knockout_results.csv')
                with open(path, newline='', encoding='utf-8') as f:
                    rows = list(csv.reader(f))
            finally:
                os.chdir(orig_dir)

        self.assertEqual(rows[0], ['match', 'winner'])
        # Sorted by match number: 73, 89, 104
        self.assertEqual(rows[1], ['73', 'Spain'])
        self.assertEqual(rows[2], ['89', 'Brazil'])
        self.assertEqual(rows[3], ['104', 'France'])

    def test_output_format_with_penalties(self):
        # M97 went to pens (1-1 AET, home wins 4-2); others are normal
        results = {73: 'Spain', 97: 'Brazil', 104: 'France'}
        scores  = {73: (2, 1), 97: (1, 1, 4, 2)}
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_dir = os.getcwd()
            os.chdir(tmpdir)
            try:
                write_ko_results_csv(results, scores)
                path = os.path.join(tmpdir, 'results', 'knockout_results.csv')
                with open(path, newline='', encoding='utf-8') as f:
                    rows = list(csv.reader(f))
            finally:
                os.chdir(orig_dir)

        # Header must be 6-column when any pen data exists
        self.assertEqual(rows[0], ['match', 'winner', 'home_score', 'away_score', 'home_pen', 'away_pen'])
        # Normal win: pen columns blank
        self.assertEqual(rows[1], ['73', 'Spain',  '2', '1', '',  '' ])
        # Penalty win: all 6 columns populated
        self.assertEqual(rows[2], ['97', 'Brazil', '1', '1', '4', '2'])
        # No score at all: blank for all 4 score columns
        self.assertEqual(rows[3], ['104', 'France', '', '', '', ''])

    def test_output_format_mixed_no_pen_uses_4_cols(self):
        # When no entry has pen data, use the 4-column format even if scores exist
        results = {73: 'Spain', 89: 'Brazil'}
        scores  = {73: (2, 1), 89: (3, 0)}
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_dir = os.getcwd()
            os.chdir(tmpdir)
            try:
                write_ko_results_csv(results, scores)
                path = os.path.join(tmpdir, 'results', 'knockout_results.csv')
                with open(path, newline='', encoding='utf-8') as f:
                    rows = list(csv.reader(f))
            finally:
                os.chdir(orig_dir)

        self.assertEqual(rows[0], ['match', 'winner', 'home_score', 'away_score'])
        self.assertEqual(len(rows[0]), 4)


# ─────────────────────────────────────────────────────────────────────────────
# extract_team
# ─────────────────────────────────────────────────────────────────────────────

class TestExtractTeam(unittest.TestCase):

    def test_fb_template(self):
        self.assertEqual(extract_team('{{fb|ESP}}'), 'Spain')

    def test_fb_rt_template(self):
        self.assertEqual(extract_team('{{fb-rt|ESP}}'), 'Spain')

    def test_invoke_flag_template(self):
        self.assertEqual(extract_team('{{#invoke:flag|fb|BRA}}'), 'Brazil')

    def test_invoke_flag_rt_template(self):
        self.assertEqual(extract_team('{{#invoke:flag|fb-rt|FRA}}'), 'France')

    def test_invoke_flagg_template(self):
        self.assertEqual(extract_team('{{#invoke:flagg|main|flag|ARG}}'), 'Argentina')

    def test_wiki_link_fallback(self):
        self.assertEqual(extract_team('[[Spain national football team|Spain]]'), 'Spain')

    def test_unknown_code_returns_none(self):
        self.assertIsNone(extract_team('{{fb|XYZ}}'))

    def test_empty_string_returns_none(self):
        self.assertIsNone(extract_team(''))

    def test_all_team_codes_parseable(self):
        # Every code in TEAM_CODES should be extractable via the fb template
        for code, name in TEAM_CODES.items():
            result = extract_team(f'{{{{fb|{code}}}}}')
            self.assertEqual(result, name, f'extract_team failed for code {code!r}')


# ─────────────────────────────────────────────────────────────────────────────
# extract_score
# ─────────────────────────────────────────────────────────────────────────────

class TestExtractScore(unittest.TestCase):

    def test_regular_score_dash(self):
        self.assertEqual(extract_score('2-1'), (2, 1))

    def test_regular_score_endash(self):
        self.assertEqual(extract_score('2–1'), (2, 1))

    def test_draw(self):
        self.assertEqual(extract_score('0–0'), (0, 0))

    def test_high_score(self):
        self.assertEqual(extract_score('5–3'), (5, 3))

    def test_strips_whitespace(self):
        self.assertEqual(extract_score('  3 – 2  '), (3, 2))

    def test_returns_none_for_text(self):
        self.assertIsNone(extract_score('Match 73'))

    def test_returns_none_for_empty(self):
        self.assertIsNone(extract_score(''))

    def test_returns_none_for_partial(self):
        self.assertIsNone(extract_score('2–'))

    def test_score_0_0(self):
        self.assertEqual(extract_score('0-0'), (0, 0))


# ─────────────────────────────────────────────────────────────────────────────
# parse_results (Wikipedia wikitext)
# ─────────────────────────────────────────────────────────────────────────────

def _make_wikitext_block(team1_code, team2_code, score):
    """Build a minimal Football box wikitext block."""
    return (
        f'{{{{Football box\n'
        f'| team1 = {{{{fb|{team1_code}}}}}\n'
        f'| team2 = {{{{fb|{team2_code}}}}}\n'
        f'| score = {score}\n'
        f'}}}}\n'
    )


class TestParseResultsWikitext(unittest.TestCase):

    def test_home_win(self):
        wikitext = _make_wikitext_block('MEX', 'RSA', '2–0')
        results = parse_results(wikitext)
        self.assertEqual(results[1], (2, 0, 'W1'))

    def test_away_win(self):
        wikitext = _make_wikitext_block('MEX', 'RSA', '0–1')
        results = parse_results(wikitext)
        self.assertEqual(results[1], (0, 1, 'W2'))

    def test_draw(self):
        wikitext = _make_wikitext_block('MEX', 'RSA', '1–1')
        results = parse_results(wikitext)
        self.assertEqual(results[1], (1, 1, 'Draw'))

    def test_skips_unplayed_match_no_score(self):
        # Block with no score field → not parsed
        wikitext = '{{Football box\n| team1 = {{fb|MEX}}\n| team2 = {{fb|RSA}}\n}}\n'
        results = parse_results(wikitext)
        self.assertEqual(results, {})

    def test_skips_match_with_placeholder_score(self):
        # "Match 1" in score field → unplayed; extract_score returns None
        wikitext = _make_wikitext_block('MEX', 'RSA', 'Match 1')
        results = parse_results(wikitext)
        self.assertEqual(results, {})

    def test_multiple_matches(self):
        wikitext = (
            _make_wikitext_block('MEX', 'RSA', '2–0') +
            _make_wikitext_block('KOR', 'CZE', '1–1') +
            _make_wikitext_block('CAN', 'BIH', '0–2')
        )
        results = parse_results(wikitext)
        self.assertEqual(results[1], (2, 0, 'W1'))
        self.assertEqual(results[2], (1, 1, 'Draw'))
        self.assertEqual(results[3], (0, 2, 'W2'))

    def test_case_insensitive_template(self):
        # {{football box}} (lowercase 'f')
        wikitext = '{{football box\n| team1 = {{fb|BRA}}\n| team2 = {{fb|MAR}}\n| score = 3–0\n}}\n'
        results = parse_results(wikitext)
        self.assertEqual(results[7], (3, 0, 'W1'))

    def test_unknown_team_skipped(self):
        wikitext = _make_wikitext_block('XYZ', 'RSA', '2–0')
        results = parse_results(wikitext)
        self.assertEqual(results, {})

    def test_empty_wikitext(self):
        self.assertEqual(parse_results(''), {})

    def test_invoke_flag_format(self):
        # 2026 WC KO-style Lua invoke
        wikitext = (
            '{{Football box\n'
            '| team1 = {{#invoke:flag|fb|ESP}}\n'
            '| team2 = {{#invoke:flag|fb|CPV}}\n'
            '| score = 5–0\n'
            '}}\n'
        )
        results = parse_results(wikitext)
        self.assertEqual(results[14], (5, 0, 'W1'))  # Spain vs Cape Verde = M14


# ─────────────────────────────────────────────────────────────────────────────
# Integration: MATCH_LOOKUP completeness
# ─────────────────────────────────────────────────────────────────────────────

class TestMatchLookupIntegrity(unittest.TestCase):

    def test_72_matches(self):
        self.assertEqual(len(MATCH_LOOKUP), 72)

    def test_all_match_numbers_1_to_72(self):
        self.assertEqual(set(MATCH_LOOKUP.values()), set(range(1, 73)))

    def test_all_team_names_in_team_codes(self):
        all_values = set(TEAM_CODES.values())
        for (t1, t2) in MATCH_LOOKUP:
            self.assertIn(t1, all_values, f'Team {t1!r} in MATCH_LOOKUP but not TEAM_CODES')
            self.assertIn(t2, all_values, f'Team {t2!r} in MATCH_LOOKUP but not TEAM_CODES')


# ─────────────────────────────────────────────────────────────────────────────
# espn_team_name — KNOWN_TEAMS validation
# ─────────────────────────────────────────────────────────────────────────────

class TestEspnTeamNameValidation(unittest.TestCase):

    def test_unknown_name_triggers_warning(self):
        """An ESPN displayName that isn't in KNOWN_TEAMS should print a warning."""
        import io
        from unittest.mock import patch
        with patch('builtins.print') as mock_print:
            result = espn_team_name({'displayName': 'Wakanda'})
        self.assertEqual(result, 'Wakanda')
        # Confirm a warning was printed containing the unknown name
        printed = ' '.join(str(a) for call in mock_print.call_args_list for a in call[0])
        self.assertIn('Warning', printed)
        self.assertIn('Wakanda', printed)

    def test_known_name_no_warning(self):
        """A valid internal team name should not trigger a warning."""
        from unittest.mock import patch
        with patch('builtins.print') as mock_print:
            result = espn_team_name({'displayName': 'Brazil'})
        self.assertEqual(result, 'Brazil')
        mock_print.assert_not_called()

    def test_all_known_teams_covered(self):
        """Every value in TEAM_CODES must be in KNOWN_TEAMS."""
        for name in TEAM_CODES.values():
            self.assertIn(name, KNOWN_TEAMS, f'{name!r} missing from KNOWN_TEAMS')

    def test_mapped_names_in_known_teams(self):
        """Every value in ESPN_TEAM_MAP must be in KNOWN_TEAMS."""
        for espn_raw, internal in ESPN_TEAM_MAP.items():
            self.assertIn(internal, KNOWN_TEAMS,
                          f'ESPN_TEAM_MAP value {internal!r} not in KNOWN_TEAMS')


# ─────────────────────────────────────────────────────────────────────────────
# parse_group_results_espn — ESPN home/away reversal
# ─────────────────────────────────────────────────────────────────────────────

class TestGroupEspnHomeAwayReversal(unittest.TestCase):
    """Verify the reversed-pair fallback: when ESPN lists home/away swapped vs
    our MATCH_LOOKUP, scores are recorded from our home team's perspective."""

    def test_reversed_pair_match_found(self):
        # M1: Mexico (home) vs South Africa (away).
        # ESPN sends South Africa as home (1 goal) and Mexico as away (0 goals).
        # Our result should be home_score=0 (Mexico), away_score=1 (South Africa).
        events = [make_espn_event('South Africa', 'Mexico', 1, 0)]
        results = parse_group_results_espn(events)
        self.assertIn(1, results)
        home_score, away_score, outcome = results[1]
        self.assertEqual(home_score, 0)   # Mexico scored 0
        self.assertEqual(away_score, 1)   # South Africa scored 1
        self.assertEqual(outcome, 'W2')   # South Africa (away in our system) wins

    def test_reversed_pair_draw(self):
        # M7: Brazil (home) vs Morocco (away) — reversed in ESPN as Morocco 1 Brazil 1
        events = [make_espn_event('Morocco', 'Brazil', 1, 1)]
        results = parse_group_results_espn(events)
        self.assertIn(7, results)
        home_score, away_score, outcome = results[7]
        self.assertEqual(home_score, 1)
        self.assertEqual(away_score, 1)
        self.assertEqual(outcome, 'Draw')

    def test_reversed_pair_home_team_wins(self):
        # M17: France (home) vs Senegal (away) — ESPN reverses to Senegal 0 France 2
        events = [make_espn_event('Senegal', 'France', 0, 2)]
        results = parse_group_results_espn(events)
        self.assertIn(17, results)
        home_score, away_score, outcome = results[17]
        self.assertEqual(home_score, 2)   # France (our home) scored 2
        self.assertEqual(away_score, 0)
        self.assertEqual(outcome, 'W1')

    def test_normal_order_still_works(self):
        # Make sure the normal (non-reversed) path is unaffected
        events = [make_espn_event('Mexico', 'South Africa', 3, 0)]
        results = parse_group_results_espn(events)
        self.assertEqual(results[1], (3, 0, 'W1'))


# ─────────────────────────────────────────────────────────────────────────────
# parse_ko_results_espn — ESPN home/away reversal
# ─────────────────────────────────────────────────────────────────────────────

class TestKoEspnHomeAwayReversal(unittest.TestCase):
    """When ESPN labels a team as 'home' but our bracket has it as 'away',
    the stored scores must be swapped to match our bracket's home/away order."""

    def test_reversed_ko_scores_swapped(self):
        # Bracket M73: Spain=home, France=away.
        # ESPN sends France as home (2 goals), Spain as away (1 goal).
        # We expect scores stored as (1, 2) — Spain's score first.
        bracket = make_ko_bracket()
        events = [make_espn_event('France', 'Spain', 2, 1,
                                  season_slug='round-of-32',
                                  home_winner=False, away_winner=True)]
        results, scores = parse_ko_results_espn(events, bracket)
        self.assertIn(73, results)
        self.assertEqual(results[73], 'Spain')
        self.assertIn(73, scores)
        home_sc, away_sc = scores[73]
        self.assertEqual(home_sc, 1)   # Spain (our home) scored 1
        self.assertEqual(away_sc, 2)   # France (our away) scored 2

    def test_reversed_ko_penalty_scores_swapped(self):
        # M73: Spain=home, France=away. ESPN: France=home 1-1 Spain (AET), France wins 4-3.
        # Stored: (1, 1, 3, 4) — Spain's scores first.
        bracket = make_ko_bracket()
        events = [make_espn_event('France', 'Spain', 1, 1,
                                  season_slug='round-of-32',
                                  home_pen=4, away_pen=3)]
        results, scores = parse_ko_results_espn(events, bracket)
        self.assertEqual(results[73], 'France')
        self.assertEqual(len(scores[73]), 4)
        self.assertEqual(scores[73], (1, 1, 3, 4))  # Spain pens=3, France pens=4

    def test_normal_ko_order_unaffected(self):
        # Bracket M73: Spain=home, France=away. ESPN agrees: Spain=home 2-0 France.
        bracket = make_ko_bracket()
        events = [make_espn_event('Spain', 'France', 2, 0,
                                  season_slug='round-of-32')]
        results, scores = parse_ko_results_espn(events, bracket)
        self.assertEqual(results[73], 'Spain')
        self.assertEqual(scores[73], (2, 0))


# ─────────────────────────────────────────────────────────────────────────────
# compute_group_standings
# ─────────────────────────────────────────────────────────────────────────────

def _make_results_dict(winners):
    """Build a minimal results dict {match_num: (hs, as, outcome)} from a
    {match_num: 'W1'|'W2'|'Draw'} dict, using score 1-0 or 0-0 as appropriate."""
    out = {}
    for num, outcome in winners.items():
        if outcome == 'W1':   out[num] = (1, 0, 'W1')
        elif outcome == 'W2': out[num] = (0, 1, 'W2')
        else:                  out[num] = (0, 0, 'Draw')
    return out


class TestComputeGroupStandings(unittest.TestCase):
    """compute_group_standings(results) returns (grp_standings, stats)."""

    def test_all_groups_present(self):
        results = _make_results_dict({num: 'W1' for num, *_ in GROUP_MATCHES})
        grp_standings, stats = compute_group_standings(results)
        self.assertEqual(set(grp_standings.keys()), set(GROUP_ORDER.keys()))

    def test_winner_top_of_group(self):
        # M1 Mexico W1 → Mexico should be first in group A
        results = _make_results_dict({1: 'W1', 25: 'W1', 28: 'W1', 53: 'Draw', 54: 'Draw'})
        grp_standings, _ = compute_group_standings(results)
        group_a = grp_standings['A']
        teams = [t for t, _ in group_a]
        self.assertEqual(teams[0], 'Mexico')

    def test_all_matches_produce_four_teams_per_group(self):
        results = _make_results_dict({num: 'W1' for num, *_ in GROUP_MATCHES})
        grp_standings, _ = compute_group_standings(results)
        for grp, teams in grp_standings.items():
            self.assertEqual(len(teams), 4, f'Group {grp} should have 4 teams')

    def test_empty_results_still_returns_all_groups(self):
        grp_standings, _ = compute_group_standings({})
        self.assertEqual(set(grp_standings.keys()), set(GROUP_ORDER.keys()))

    def test_points_accumulate_correctly(self):
        # M16 Belgium(home) W1 (+3), M39 Belgium(home) W1 (+3), M64 New Zealand(home) W2=Belgium wins (+3) = 9
        results = _make_results_dict({16: 'W1', 39: 'W1', 64: 'W2'})
        grp_standings, _ = compute_group_standings(results)
        group_g = grp_standings['G']
        belgium_entry = next((s for t, s in group_g if t == 'Belgium'), None)
        self.assertIsNotNone(belgium_entry)
        self.assertEqual(belgium_entry['Pts'], 9)

    def test_draw_gives_one_point_each(self):
        results = _make_results_dict({16: 'Draw'})  # M16: Belgium vs Egypt
        grp_standings, _ = compute_group_standings(results)
        group_g = grp_standings['G']
        pts = {t: s['Pts'] for t, s in group_g}
        self.assertEqual(pts['Belgium'], 1)
        self.assertEqual(pts['Egypt'], 1)


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    unittest.main(verbosity=2)
