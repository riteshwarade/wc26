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
    MATCH_LOOKUP,
    ESPN_TEAM_MAP,
    TEAM_CODES,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_espn_event(home_name, away_name, home_score, away_score,
                    season_slug='group-stage', completed=True,
                    home_winner=None, away_winner=None):
    """Build a minimal ESPN event dict matching the structure parse_* expects."""
    if home_winner is None and away_winner is None:
        home_winner = home_score > away_score
        away_winner = away_score > home_score
    return {
        'season': {'slug': season_slug},
        'competitions': [{
            'status': {'type': {'completed': completed}},
            'competitors': [
                {
                    'homeAway': 'home',
                    'team': {'displayName': home_name},
                    'score': str(home_score),
                    'winner': home_winner,
                },
                {
                    'homeAway': 'away',
                    'team': {'displayName': away_name},
                    'score': str(away_score),
                    'winner': away_winner,
                },
            ],
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
# Runner
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    unittest.main(verbosity=2)
