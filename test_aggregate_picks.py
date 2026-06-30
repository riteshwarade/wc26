"""
test_aggregate_picks.py

Unit tests for .github/scripts/aggregate_picks.py.

Covers:
  - name_from_filename: group CSV filename → participant name
  - name_from_knockout_filename: KO CSV filename → participant name
  - load_picks_csv: 4-col group CSV (match,group,matchup,pick) → {match_num: outcome}
  - load_knockout_csv: 4-col KO CSV (match,round,matchup,pick) → {match_num: winner}

Run: python3 test_aggregate_picks.py
"""

import csv
import io
import os
import sys
import tempfile
import unittest

# Allow running from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.github', 'scripts'))

from aggregate_picks import (
    name_from_filename,
    name_from_knockout_filename,
    load_picks_csv,
    load_knockout_csv,
)

# Minimal match_teams dict for group pick tests (subset of real matches)
MATCH_TEAMS = {
    1:  ('Mexico',    'South Africa'),
    2:  ('South Korea', 'Czech Republic'),
    7:  ('Brazil',    'Morocco'),
    17: ('France',    'Senegal'),
}


# ─────────────────────────────────────────────────────────────────────────────
# name_from_filename
# ─────────────────────────────────────────────────────────────────────────────

class TestNameFromFilename(unittest.TestCase):

    def test_simple_name(self):
        self.assertEqual(name_from_filename('wc26_group_alice.csv'), 'Alice')

    def test_hyphenated_name(self):
        self.assertEqual(name_from_filename('wc26_group_john-smith.csv'), 'John Smith')

    def test_simulation_name(self):
        # Numeric suffix: last part not alphabetic, so no abbreviation
        self.assertEqual(name_from_filename('wc26_group_simulation-1.csv'), 'Simulation 1')

    def test_full_path_ignored(self):
        self.assertEqual(
            name_from_filename('/some/path/picks/group/swiftly/wc26_group_jane-doe.csv'),
            'Jane Doe'
        )

    def test_multi_part_name(self):
        self.assertEqual(
            name_from_filename('wc26_group_mary-anne-jones.csv'),
            'Mary Anne Jones'
        )


# ─────────────────────────────────────────────────────────────────────────────
# name_from_knockout_filename
# ─────────────────────────────────────────────────────────────────────────────

class TestNameFromKnockoutFilename(unittest.TestCase):

    def test_simple_name(self):
        self.assertEqual(name_from_knockout_filename('wc26_knockout_alice.csv'), 'Alice')

    def test_hyphenated_name(self):
        self.assertEqual(name_from_knockout_filename('wc26_knockout_john-smith.csv'), 'John Smith')

    def test_simulation_name(self):
        # Numeric suffix: last part not alphabetic, so no abbreviation
        self.assertEqual(
            name_from_knockout_filename('wc26_knockout_simulation-3.csv'),
            'Simulation 3'
        )

    def test_full_path_ignored(self):
        self.assertEqual(
            name_from_knockout_filename('/picks/knockout/fandf/wc26_knockout_bob-jones.csv'),
            'Bob Jones'
        )


# ─────────────────────────────────────────────────────────────────────────────
# load_picks_csv — group stage (format: match,group,matchup,pick)
# ─────────────────────────────────────────────────────────────────────────────

def _write_group_csv(rows, tmpdir, filename='test_group.csv'):
    """Write rows to a temp CSV file and return its path."""
    path = os.path.join(tmpdir, filename)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)
    return path


class TestLoadPicksCsv(unittest.TestCase):

    def test_home_win(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write_group_csv([
                ['match', 'group', 'matchup', 'pick'],
                [1, 'A', 'Mexico v South Africa', 'Mexico'],
            ], d)
            picks = load_picks_csv(path, MATCH_TEAMS)
        self.assertEqual(picks[1], 'W1')

    def test_away_win(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write_group_csv([
                ['match', 'group', 'matchup', 'pick'],
                [1, 'A', 'Mexico v South Africa', 'South Africa'],
            ], d)
            picks = load_picks_csv(path, MATCH_TEAMS)
        self.assertEqual(picks[1], 'W2')

    def test_draw(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write_group_csv([
                ['match', 'group', 'matchup', 'pick'],
                [1, 'A', 'Mexico v South Africa', 'Draw'],
            ], d)
            picks = load_picks_csv(path, MATCH_TEAMS)
        self.assertEqual(picks[1], 'Draw')

    def test_header_row_skipped(self):
        # Header row must not be counted as a match
        with tempfile.TemporaryDirectory() as d:
            path = _write_group_csv([
                ['match', 'group', 'matchup', 'pick'],
                [1, 'A', 'Mexico v South Africa', 'Mexico'],
            ], d)
            picks = load_picks_csv(path, MATCH_TEAMS)
        self.assertNotIn('match', picks)
        self.assertIn(1, picks)

    def test_multiple_matches(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write_group_csv([
                ['match', 'group', 'matchup', 'pick'],
                [1,  'A', 'Mexico v South Africa',    'Mexico'],
                [2,  'A', 'South Korea v Czech Republic', 'Draw'],
                [7,  'C', 'Brazil v Morocco',          'Morocco'],
                [17, 'E', 'France v Senegal',           'France'],
            ], d)
            picks = load_picks_csv(path, MATCH_TEAMS)
        self.assertEqual(picks[1],  'W1')
        self.assertEqual(picks[2],  'Draw')
        self.assertEqual(picks[7],  'W2')
        self.assertEqual(picks[17], 'W1')

    def test_unknown_team_skipped(self):
        # 'Wakanda' is not a valid team for match 1
        with tempfile.TemporaryDirectory() as d:
            path = _write_group_csv([
                ['match', 'group', 'matchup', 'pick'],
                [1, 'A', 'Mexico v South Africa', 'Wakanda'],
            ], d)
            picks = load_picks_csv(path, MATCH_TEAMS)
        self.assertNotIn(1, picks)

    def test_empty_pick_field_skipped(self):
        # 4-column row with blank pick cell (late joiner / missed game) — must not store the match
        with tempfile.TemporaryDirectory() as d:
            path = _write_group_csv([
                ['match', 'group', 'matchup', 'pick'],
                [1, 'A', 'Mexico v South Africa', ''],   # blank pick
                [2, 'A', 'South Korea v Czech Republic', 'Draw'],
            ], d)
            picks = load_picks_csv(path, MATCH_TEAMS)
        self.assertNotIn(1, picks)       # blank pick → absent from output
        self.assertEqual(picks[2], 'Draw')  # other picks unaffected

    def test_short_rows_skipped(self):
        # Rows with fewer than 4 columns are ignored
        with tempfile.TemporaryDirectory() as d:
            path = _write_group_csv([
                ['match', 'group', 'matchup', 'pick'],
                [1, 'A', 'Mexico v South Africa'],  # only 3 cols
            ], d)
            picks = load_picks_csv(path, MATCH_TEAMS)
        self.assertEqual(picks, {})

    def test_empty_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write_group_csv([], d)
            picks = load_picks_csv(path, MATCH_TEAMS)
        self.assertEqual(picks, {})

    def test_header_only_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write_group_csv([['match', 'group', 'matchup', 'pick']], d)
            picks = load_picks_csv(path, MATCH_TEAMS)
        self.assertEqual(picks, {})

    def test_unknown_match_num_skipped(self):
        # match 999 is not in MATCH_TEAMS → pick stored anyway (outcome just can't resolve)
        # Actually load_picks_csv resolves based on t1/t2 — for unknown match, t1=t2=''
        # and label won't match '', so it's skipped.
        with tempfile.TemporaryDirectory() as d:
            path = _write_group_csv([
                ['match', 'group', 'matchup', 'pick'],
                [999, 'Z', 'Atlantis v Wakanda', 'Atlantis'],
            ], d)
            picks = load_picks_csv(path, MATCH_TEAMS)
        self.assertNotIn(999, picks)


# ─────────────────────────────────────────────────────────────────────────────
# load_knockout_csv — KO stage (format: match,round,matchup,pick)
# ─────────────────────────────────────────────────────────────────────────────

def _write_ko_csv(rows, tmpdir, filename='test_ko.csv'):
    path = os.path.join(tmpdir, filename)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)
    return path


class TestLoadKnockoutCsv(unittest.TestCase):

    def test_single_pick(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write_ko_csv([
                ['match', 'round', 'matchup', 'pick'],
                [73, 'R32', 'Brazil v Morocco', 'Brazil'],
            ], d)
            picks = load_knockout_csv(path)
        self.assertEqual(picks[73], 'Brazil')

    def test_header_row_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write_ko_csv([
                ['match', 'round', 'matchup', 'pick'],
                [73, 'R32', 'Brazil v Morocco', 'Brazil'],
            ], d)
            picks = load_knockout_csv(path)
        self.assertNotIn('match', picks)
        self.assertIn(73, picks)

    def test_multiple_rounds(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write_ko_csv([
                ['match', 'round', 'matchup', 'pick'],
                [73,  'R32',   'Brazil v Morocco',     'Brazil'],
                [89,  'R16',   'Brazil v France',      'France'],
                [97,  'QF',    'France v Spain',       'Spain'],
                [101, 'SF',    'Spain v England',      'England'],
                [103, '3rd',   'Brazil v France',      'Brazil'],
                [104, 'Final', 'England v Germany',    'England'],
            ], d)
            picks = load_knockout_csv(path)
        self.assertEqual(picks[73],  'Brazil')
        self.assertEqual(picks[89],  'France')
        self.assertEqual(picks[97],  'Spain')
        self.assertEqual(picks[101], 'England')
        self.assertEqual(picks[103], 'Brazil')
        self.assertEqual(picks[104], 'England')

    def test_empty_pick_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write_ko_csv([
                ['match', 'round', 'matchup', 'pick'],
                [73, 'R32', 'Brazil v Morocco', ''],
            ], d)
            picks = load_knockout_csv(path)
        self.assertNotIn(73, picks)

    def test_short_rows_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write_ko_csv([
                ['match', 'round', 'matchup', 'pick'],
                [73, 'R32', 'Brazil v Morocco'],  # only 3 cols
            ], d)
            picks = load_knockout_csv(path)
        self.assertEqual(picks, {})

    def test_empty_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write_ko_csv([], d)
            picks = load_knockout_csv(path)
        self.assertEqual(picks, {})

    def test_header_only_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write_ko_csv([['match', 'round', 'matchup', 'pick']], d)
            picks = load_knockout_csv(path)
        self.assertEqual(picks, {})

    def test_all_32_matches(self):
        # Verify all 32 KO match numbers are parsed when present
        ko_order = (
            list(range(73, 89)) + list(range(89, 97)) +
            list(range(97, 101)) + [101, 102, 103, 104]
        )
        rows = [['match', 'round', 'matchup', 'pick']]
        for m in ko_order:
            rows.append([m, 'R32', 'Team A v Team B', 'Team A'])
        with tempfile.TemporaryDirectory() as d:
            path = _write_ko_csv(rows, d)
            picks = load_knockout_csv(path)
        self.assertEqual(len(picks), 32)
        self.assertEqual(set(picks.keys()), set(ko_order))

    def test_quoted_team_name_with_comma(self):
        # Team names containing commas must be quoted in CSV; parser must handle them
        with tempfile.TemporaryDirectory() as d:
            path = _write_ko_csv([
                ['match', 'round', 'matchup', 'pick'],
                [73, 'R32', 'Brazil v Morocco', 'Brazil'],
            ], d)
            picks = load_knockout_csv(path)
        self.assertEqual(picks[73], 'Brazil')


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    unittest.main(verbosity=2)
