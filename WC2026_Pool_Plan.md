# World Cup 2026 Pool — Master Plan

## Changelog

| Date | Change |
|---|---|
| Jun 12, 2026 | **Leaderboard audit 4 fixes.** Bridge/live tooltip: tooltip `data-result` now shows the live score (`1–0 (Mexico) · live`) when ESPN has a score but CSV is not yet confirmed — was showing "Not played yet" while the square pulsed live-correct/live-wrong. KO mob-recent column fallback: when no KO results exist, column now shows empty set (consistent with group-mode behavior) instead of the last-5 match numbers (M100–M104 Finals area), which was showing a confusing column of all-empty final squares. |
| Jun 12, 2026 | **Minor leaderboard fixes (audit 3 remainder).** Added `.tt-status.empty { color: var(--neutral-medium) }` CSS rule so empty-pick tooltip status text renders in muted gray. Moved `let _lastUpdated = null` from the auto-refresh block (post-DOMContentLoaded) to the module-level live-scores state block — prevents a TDZ window where `_updateTimestamp()` could reference an undeclared variable. KO mob recent column now shows last-5 *played* matches (filters `KO_MATCH_ORDER` by `koResults[m]`) instead of last-5 by match number — during R32 the column was showing all-empty M100–M104 squares. Fixed typo `liveLoseer` → `liveLoser` in results table renderer. |
| Jun 12, 2026 | **Leaderboard audit fixes (critical — allGroupsStarted + thirdPlaceTeams).** `allGroupsStarted` (which gates 3rd-place qualification highlighting) was using `isGroupStarted` (any match played) instead of `isGroupDone` (all 6 played) — fixed. `thirdPlaceTeams` was including groups with 0 games played (ghost 3rd-place entries with P=0), corrupting the cross-group ranking — fixed with a `st.P === 0` filter. `_pendingResults` seeding capped at 24h to prevent old finished matches from re-entering the bridge on stale reloads. |
| Jun 12, 2026 | **Fix `computeGroupStandings` H2H tiebreaker.** `grpMatches` was built as 4-element arrays `[num,grp,t1,t2]` but `h2hStats` destructures as `[num,,,,t1,t2]` (6-element MATCHES format). H2H criteria a/b/c were silently skipped, falling straight to overall GD/GF for bracket seeding. Fix: push `[num,grp,null,null,t1,t2]`. Group table sorting (`sortedStandings`) was unaffected — it passes full MATCHES arrays directly. |
| Jun 12, 2026 | **Leaderboard audit fixes (critical + minor).** Critical: `init()` now has `if (_inInit) return` entry guard preventing concurrent races; `_buildAbbrevMap` moved into each mode branch so KO-only participants are included before collision resolution; KO tooltip `data-match` no longer double-prefixes "Match M73". Minor: live score in results table now reorders to winner-first (consistent with FT display); trailing divider after M103 removed; `err.message` injected via `createTextNode` (no XSS risk); `KO_ROUND_BREAKS` hoisted above `forEach` loop. |
| Jun 12, 2026 | **Late joiner support + empty square fixes.** To handle participants who join after games are played, blank their picks in the CSV for already-played matches. `aggregate_picks.py` skips empty fields → key absent from JSON → `computeStandings` assigns `empty` status (0 pts, no scoring). `.sq-empty` now shows a faint outlined square (was fully invisible — no border). Tooltip hides "Your pick" line and shows "— No pick". `pickResults[num].result` now populated for empty picks so tooltip shows actual score for played matches. |
| Jun 12, 2026 | **Bridge pulsing fix.** During the bridge period (`_pendingResults.size > 0`), polling interval is no longer stopped when `anyIn = false`. Previously, `stopLivePolling()` fired immediately when a game ended, creating a gap before the bridge restarted polling — causing squares to show solid during that window. Fix: keep interval running; only `stopLivePolling()` when `_pendingResults` is empty. `init()` is still called each cycle to re-fetch the CSV. |
| Jun 12, 2026 | **Mobile recent-squares column (leaderboard).** Added `.td-mob-sq` / `.th-mob-sq` column (hidden on desktop, shown at ≤640px) showing the last 5 squares for the current stage only. Group mode: last 5 of M1–M72 with live-correct/live-wrong pulsing. KO mode: last 5 of KO_MATCH_ORDER (M100–M104). No carryover between stages. |
| Jun 12, 2026 | **SHORT_NAMES in leaderboard group tables.** Added `_GRP_SHORT_NAMES` map to leaderboard and optional `display` param to `teamHtml()` in `bracket.js`. Fixes "Bosnia and Herzegovina" and "Czech Republic" overflowing the team name cell on iPad (`.side-left` is fixed 380px, leaving ~120px for the team column). Mirrors existing picks page `SHORT_NAMES` pattern. |
| Jun 12, 2026 | **Live scores end-to-end testing + diagnostics.** Verified full pulsing lifecycle on Canada vs Bosnia (M3): kickoff → pulsing → FT bridge → CSV snap-to-solid. Added `live_scores_test_plan.md` with phase-by-phase checklist + console simulation commands. Added diagnostic commands + known-behavior notes to `CLAUDE.md`. Known transient: on `in → post` transition, squares may briefly flash solid before bridge re-injects (~one poll cycle, ≤60s). |
| Jun 12, 2026 | **FT bridge + cron reliability fixes.** Live scores: added `_pendingResults` Set to track matches where ESPN said game ended but CSV not yet confirmed — persists even after ESPN drops the post-game event (which it does within minutes of FT). Time-based seeding: on every `fetchLiveScores` call, any match past kickoff+110min with no CSV result is added to `_pendingResults`, covering page reloads after ESPN has already dropped the event. Bridge polling: while `_pendingResults` is non-empty, polling calls `init()` (not just `fetchLiveScores`) so CSV is re-fetched every 60s until GitHub Actions pushes the result. `_inInit` guard prevents recursive `init()` calls. Cron reliability: GitHub native cron reduced to `*/10` (fallback only); primary trigger is cron-job.org every 5 min via `workflow_dispatch` API. GitHub PAT `wc26-cron-trigger` expires 2026-08-11. |
| Jun 11, 2026 | **Live scores bug fixes + results table polish.** ESPN live scores fix: ESPN indexes matches by ET date, not UTC — fetching yesterday+today UTC instead of today+tomorrow catches all live matches including late ET games (e.g. 10 PM ET = 2 AM UTC next day). Correctness pill moved to its own "Correct" column in results table (was appended inline to Score). Score column now center-aligned. Correct pill pulses during live matches (consistent with score + minute). |
| Jun 11, 2026 | **Live scores (group stage).** Client-side ESPN fetch (`site.api.espn.com`) polls every 60s when games are in-progress. New square statuses `live-correct` / `live-wrong` pulse in full color (blue/red) while a match is live; snap to solid on FT. Results table shows pulsing minute in Time cell + pulsing live score in Score cell (default text color). Standings frozen during live. `LIVE_SCORES_ENABLED` const toggle at top of leaderboard JS. KO live scores planned for later — same architecture. |
| Jun 11, 2026 | **Mobile landscape fixes.** Leaderboard: added `@media (max-width: 896px) and (orientation: landscape)` query — stacks group tables and match results vertically (same order as portrait) and makes the standings card horizontally scrollable (`overflow-x: auto`). The existing portrait breakpoint (`max-width: 640px`) was missed by landscape phones (~667–896px wide). |
| Jun 11, 2026 | **Tournament day fixes.** `update.yml`: schedule changed from 15-min to 5-min polling. `test_bracket.py`: fixed crash when `group_results.csv` exists but is empty — `load_results()` now falls back to deterministic results when file is empty, not only when missing. KO picks timeline documented in `CLAUDE.md` and `WC2026_Pool_Plan.md`: picks submitted after final group stage game, deadline before M73 (Jun 28, 3:00 PM ET / 19:00 UTC). **Collision-aware name abbreviation:** `_abbrevName()` replaced with `_buildAbbrevMap()` + `_abbrevMap` lookup — detects collisions on first+last-initial (e.g. two "Arnav J"s) and expands last name chars until unique (Arnav Jha → "Arnav Jh", Arnav Juneja → "Arnav Ju"). Called once after `standings` is computed in `init()`. **Auto-clear workflow bug fix:** both clear workflows were writing `{}` to all picks JSONs, wiping real participant data. Fixed to only clear results CSVs and `knockout_bracket.json`, then re-run `aggregate_picks.py` to rebuild picks JSONs from real CSVs. |
| Jun 10, 2026 | **Upset pick visual.** Correct picks where the lower-ranked team won are promoted to `correct-upset` status via `_isUpsetResult()`. Displayed as a Swiftly Blue square with a white ✦ star (U+2726) instead of the plain blue correct square. Tooltip shows `✓ Correct ✦ Upset`. Participant name display: UI-only abbreviation to "First L" format via `_abbrevName()` in leaderboard JS — full names stored in picks JSON. Standings section: participant count pill added to Standings and Knockout Standings section labels. |
| Jun 3–4, 2026 | **Pre-tournament bug fixes and polish.** Leaderboard: CDN cache-buster (`?t=${Date.now()}`) added to all five `init()` fetch URLs — fixes stale data on auto-refresh (Fastly CDN caches raw.githubusercontent.com for 5 min; `cache: 'no-store'` only bypasses browser cache, not CDN). Page-load flash fixes: `<header>` and `.sticky-bar` start `visibility:hidden`, revealed by `document.fonts.ready` + 3s fallback; `.section-label` and `.section-body` start hidden, revealed by `_revealSections()` after `init()` completes; static loading placeholders use `.state-msg--loading` (hidden). `_updateTimestamp()` now actually called — "Updated HH:MM" now displays. `white-space: nowrap` on `.td-name` (desktop only). Group stage tiebreaker fix: `computeGroupStandings()` (used by bracket display) now uses full H2H chain (a, b, c) matching `sortedStandings()` — bracket and group tables were previously showing different team orderings on points ties. `h2hStats()` extracted to module scope. `GRP_SAMPLE` corrected for groups C, E, G, H, L (was using a later match instead of the group's first kickoff — bracket could appear up to 3hrs late per affected group). KO standings mobile: Grp/KO pts columns hidden, Total pts remains. Tooltip XSS: `_esc()` helper added; all data-attribute values and `p.name` now escaped. `POOL_NAME` variable removed (unused); `make_fandf.py` now 3 substitutions. Dead code removed: `grpSquares`, `finalist1/2`, `skipBracket`, `completedNums`, `results` param in `computeBracket`, `koSectionDivider`, `groupAccordionHeader`, `allGroupsDone`, `GRP_ROUND_BREAKS` hoisted. `bracketLabel` querySelector fixed — confirmation badge now actually appended to `#bracketSectionLabel`. `renderResults`/`renderGroupTables`/`renderBracket` now skip in KO mode (were running on every refresh unnecessarily). Group picks page: dead modal (CSS + HTML + JS `showSummary`/`closeModal`/`copyToClipboard` + event listener) removed; dead CSS (`.name-card label`, `.confirm-note`, duplicate `.group-tables-grid`) removed. Favicons (⚽ SVG emoji) added to all four pages. `koDisplay()` comment in `bracket.js` corrected. `WC2026_Intro.pptx`: host cities map slide added as slide 6 (Lambert Conformal Conic projection, USA=Swiftly Blue, Canada=red, Mexico=green, all 16 host cities labeled). |
| May 31, 2026 | **Pre-tournament leaderboard improvements.** `update.yml` restructured: push trigger on `picks/**` aggregates picks immediately whenever new CSVs land; 15-min schedule gated to Jun 11–Jul 20 (fetches ESPN results + aggregates picks); `aggregate_picks` now runs before `parse_results`. Group tables now render pre-tournament: all 12 groups shown immediately with 0-stat rows in `GROUP_ORDER` (Wikipedia order, matching the group picks page); qualified/eliminated highlighting only activates once a group's first match kicks off. |
| May 27, 2026 | **Picks CSV format improvements.** Group CSV: added header (`match,group,matchup,pick`), added `group` column, renamed pick column from unlabeled to `pick`. KO CSV: added `round` and `matchup` columns, renamed `winner` → `pick`. Both formats now consistent. Group filename: `wc26group_{pool_id}_name.csv` → `wc26_group_name.csv` (pool from folder, not filename). `aggregate_picks.py` updated for new column positions; `name_from_filename` no longer requires `pool_id`. KO `downloadCSV()` uses `getTeams(m)` to populate matchup; added `koRoundLabel()`. New `test_aggregate_picks.py` (28 tests) covers all parsing and filename functions; added to `ci.yml`. |
| May 27, 2026 | **Data model robustness + CI.** Canonical data sources: `data/rankings.json` created; `parse_results.py` loads RANKINGS from JSON; `GROUP_MATCHES` moved to top of `parse_results.py`; `MATCH_LOOKUP` auto-derived (no more 72-line hardcoded dict); `simulate.py` and `aggregate_picks.py` import `GROUP_MATCHES` instead of their own hardcoded copies; `test_bracket.py` imports from `parse_results.py`. ESPN robustness: home/away reversal handled in both group and KO parsing (fallback + score swap); `KNOWN_TEAMS` validation added to `espn_team_name()`. KO topology: `scoring.js` runtime assertion catches drift vs `bracket.js`; comments on all copies name `bracket.js` as canonical. `simulate.py` `--seed` flag for reproducible runs. 84 Python tests (up from 67): 4 new test classes cover ESPN reversal (group + KO), KNOWN_TEAMS warning, and `compute_group_standings`. `test_bracket.py` self-contained (deterministic fallback results, no CSV required). **`ci.yml` — runs all three test suites on every push/PR.** |
| May 26, 2026 | Correctness pill — group results table + KO bracket desktop/mobile |
| May 24, 2026 | UTC kick-off times for all group + KO matches; local-TZ display; KO schedule verified against ESPN API; bracket card title nowrap; column reorder; `koDisplay` day-of-week + no TZ; group picks reset highlight bug fix |
| Earlier | KO leaderboard (Variant 3) + combined standings; cascade scoring; `parse_results.py` KO fetch; test suite (80 + 105 + 84 + 67 tests); bracket shared template (`bracket.js`); KO picks page (Variant 2); mobile tab view + auto-advance; penalty shootout scores; podium section |

---

## Overview

Two pools running in parallel on the same codebase:
- **Swiftly** — company pool
- **FandF** — friends & family pool

**Note:** Ritesh Warade (ritesh@goswift.ly) participates in both pools with separate pick CSVs. When running cross-pool analytics, deduplicate or suffix his name (e.g. `Ritesh Warade (F&F)`) to avoid key collision in merged data.

Pick pages, leaderboard, and automation all live in a single GitHub repo (`riteshwarade/wc26`) served via GitHub Pages.

---

## Phases

| Phase | Matches | Dates | Status |
|---|---|---|---|
| Group stage | 72 matches (M1–M72) | Jun 12–27, 2026 | System complete ✅ |
| Knockout stage | 32 matches (M73–M104) | Jun 28–Jul 19, 2026 | Combined leaderboard live ✅ · picks page built ✅ · `parse_results.py` ESPN KO fetch complete ✅ |

---

## GitHub Pages URLs

| Page | URL | Notes |
|---|---|---|
| Group picks | `https://riteshwarade.github.io/wc26/WC2026_Pool_Group_Picks.html` | One page, both pools |
| Knockout picks | `https://riteshwarade.github.io/wc26/WC2026_Pool_Knockout_Picks.html` | One page, both pools |
| Swiftly leaderboard | `https://riteshwarade.github.io/wc26/WC2026_Pool_Leaderboard_Swiftly.html` | Pool-specific |
| FandF leaderboard | `https://riteshwarade.github.io/wc26/WC2026_Pool_Leaderboard_FandF.html` | Pool-specific |

---

## Development workflow

**Always edit `WC2026_Pool_Leaderboard_Swiftly.html`, then run `python3 make_fandf.py` to regenerate `WC2026_Pool_Leaderboard_FandF.html`. Never edit FandF directly.**

Git pushes must be done from Mac (sandbox lacks SSH access to GitHub):
```
cd ~/Documents/GitHub/wc26 && git add -A && git commit -m "..." && git push
```
If you get `index.lock` error: `rm ~/Documents/GitHub/wc26/.git/index.lock` first.

---

## Repo File Inventory (current state)

```
wc26/
├── WC2026_Pool_Group_Picks.html               ← group pick page (shared by both pools)
├── WC2026_Pool_Knockout_Picks.html            ← knockout pick page (shared by both pools)
├── WC2026_Pool_Leaderboard_Swiftly.html       ← leaderboard + knockout bracket (Swiftly)
├── WC2026_Pool_Leaderboard_FandF.html         ← leaderboard + knockout bracket (F&F)
├── bracket.js                                 ← shared bracket rendering primitives; canonical R16/QF/SF topology + RANKINGS
├── scoring.js                                 ← shared scoring module (browser + Node); MATCHES, KO_POINTS, scoring fns; mirrors bracket.js topology with runtime assertion
├── sim_core.js                                ← seeded PRNG + KO generators for Node sim/test; mirrors bracket.js topology
├── make_fandf.py                              ← regenerate FandF from Swiftly (3 substitutions: title, header, POOL_ID); never edit FandF directly
├── WC2026_Pool_Intro.md                       ← pool announcement text (3 versions: Original FandF, WhatsApp FandF, Slack Swiftly)
├── WC2026_Pool_Plan.md                        ← this document
├── test_bracket.py                             ← bracket end-to-end test (all 495 3rd-place combos); self-contained — runs without CSV
├── test_leaderboard.js                        ← unit tests: group scoring, KO scoring, cascade rules, tiebreakers (80 tests)
├── test_e2e.js                                ← 10-user full-tournament simulation + 105 structural invariant checks
├── test_partial.js                            ← mid-tournament state tests: pending/cascaded picks, maxPts at each phase (84 tests)
├── test_aggregate_picks.py                    ← Python unit tests for aggregate_picks.py: CSV parsing (group + KO 4-col format), filename → name extraction (28 tests)
├── test_parse_results.py                      ← Python unit tests for parse_results.py: ESPN + wikitext parsers, home/away reversal, KNOWN_TEAMS, standings (84 tests)
├── picks/
│   ├── group/
│   │   ├── swiftly/                            ← participant CSVs (uploaded manually by Ritesh)
│   │   └── fandf/
│   └── knockout/
│       ├── swiftly/                            ← empty until Jun 27
│       └── fandf/
├── data/
│   ├── rankings.json                           ← CANONICAL FIFA rankings (single source of truth; bracket.js + parse_results.py load from here)
│   ├── knockout_bracket.json                   ← R32 matchups (auto-generated, live)
│   ├── group_swiftly_picks.json                ← aggregated group picks
│   └── group_fandf_picks.json
├── results/
│   ├── group_results.csv                       ← match results (auto-updated from ESPN API)
│   └── knockout_results.csv                    ← KO results (simulation data now; real data Jun 28+ via parse_results.py)
└── .github/
    ├── workflows/
    │   ├── ci.yml                               ← runs on every push/PR: test_parse_results.py + test_bracket.py + test_e2e.js
    │   ├── update.yml                           ← every 15 min, Jun 11–Jul 19
    │   ├── simulate.yml                         ← generates test data (supports --seed for reproducibility)
    │   └── clear_simulation.yml                 ← wipes simulation data
    └── scripts/
        ├── parse_results.py                     ← ESPN API → results CSV + knockout_bracket.json; GROUP_MATCHES canonical list; RANKINGS from data/rankings.json; KNOWN_TEAMS guard on ESPN names
        ├── aggregate_picks.py                   ← pick CSVs → picks JSON; imports GROUP_MATCHES from parse_results.py; parses 4-col format (match,group,matchup,pick) for group and (match,round,matchup,pick) for KO
        └── simulate.py                          ← generates simulated picks + results; imports GROUP_MATCHES from parse_results.py; --seed flag; outputs 4-col format with headers
```

---

## Pick Submission Flow

1. Participant opens their pool's pick page (shared link)
2. Enters name, makes picks for all 72 matches
3. Clicks **"Happy with your picks?"** → **"Submit"** → CSV downloads
4. Participant emails CSV to Ritesh
5. Ritesh uploads CSV to `picks/group/swiftly/` or `picks/group/fandf/` on GitHub

### Pick CSV format

Filenames carry no pool identifier — pool is determined by which folder Ritesh places the file in.

**Group:** `wc26_group_john-smith.csv`
```
match,group,matchup,pick
1,A,Mexico v South Africa,Mexico
2,A,South Korea v Czech Republic,Draw
...
72,L,DR Congo v Uzbekistan,DR Congo
```

**Knockout:** `wc26_knockout_john-smith.csv`
```
match,round,matchup,pick
73,R32,Brazil v Morocco,Brazil
74,R32,France v Norway,France
...
89,R16,Brazil v France,France
...
104,Final,England v Germany,England
```
- `round` values: `R32` · `R16` · `QF` · `SF` · `3rd` · `Final`
- `matchup` for R16+ is filled from the user's own prior picks (i.e. the teams they expect to advance)
- `pick` for group stage: team name or `Draw`; for KO: team name only

Ritesh routes the CSV to the correct pool folder on upload (`picks/group/swiftly/` or `picks/group/fandf/` etc.).

### Name display format

Participant names are shown as **"First L"** (last name abbreviated to initial, no period). Abbreviation is **UI-only** via `_abbrevName()` in the leaderboard JS — full names are stored in the picks JSON and used by analytics scripts. Examples: stored as `Cole Mccarren`, displayed as `Cole M`. Numeric suffixes are not abbreviated (`Simulation 1` stays as-is). This sidesteps `.title()` mangling since the mangled last name is never visible.

Benefits: avoids `.title()` mangling of names like McCarren → Mccarren; keeps the leaderboard name column narrow; provides light privacy on last names.

Long-term fix (Option B): embed the display name inside the CSV itself so filenames don't matter.

---

## Results Automation (GitHub Actions)

**Source:** ESPN hidden scoreboard API (no API key required)
```
https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard
```

Two separate fetches, called on every run, because ESPN caps responses at 100 events:
- **Group stage:** `?dates=20260611-20260627` — returns all 72 M1–M72 events
- **KO stage:** `?dates=20260628-20260720` — returns all 32 M73–M104 events

**Schedule:** Every 15 minutes (`*/15 * * * *`), Jun 11–Jul 19 only (date-gated in workflow).

**`update.yml` steps:**
1. `parse_results.py` — fetches ESPN → writes `results/group_results.csv` + `data/knockout_bracket.json` (group stage) + `results/knockout_results.csv` (KO stage, once `data/knockout_bracket.json` exists)
2. `aggregate_picks.py` — combines pick CSVs → `data/group_swiftly_picks.json` + `data/group_fandf_picks.json`
3. Commits all changes to `results/` and `data/`

**How `parse_results.py` works:**
1. Calls `fetch_espn_group_events()` (Jun 11–27 date range). For each completed group-stage event, reads home/away team `displayName`, looks up the match number via `MATCH_LOOKUP`, determines outcome (`W1`/`Draw`/`W2`) from scores, and writes `results/group_results.csv`.
2. From group results, computes which teams qualified top-2/3rd by group and builds the R32 bracket. Writes `data/knockout_bracket.json`.
3. Calls `verify_r32_against_wikipedia()` as a cross-check on the R32 bracket once all 72 group matches are complete. Sets `"confirmed": true` in `knockout_bracket.json` only when the Wikipedia bracket matches.
4. If `data/knockout_bracket.json` exists, calls `fetch_espn_ko_events()` (Jun 28–Jul 20 date range). ESPN returns `competitor.winner = true` on the winning team. Scores are read from `competitor.score`; penalty shootout scores from `competitor.shootoutScore` (present only when a match goes to penalties). Results are resolved by walking the bracket topology (R32 → R16 → QF → SF → 3rd/Final), propagating actual team names through `W73`-style references as rounds complete. Writes `results/knockout_results.csv` (6-column with pen columns when any match had penalties).

### Results CSV formats

**`results/group_results.csv`:**
```
match,home_score,away_score,outcome
1,2,1,W1
5,1,1,Draw
7,3,0,W1
```
Only completed matches included. Outcome: `W1` / `Draw` / `W2`.

**`results/knockout_results.csv`:**
```
match,winner,home_score,away_score,home_pen,away_pen
73,Netherlands,0,2,,
89,Spain,1,1,4,2
```
One row per completed KO match. `home_pen`/`away_pen` are only present if the match went to a penalty shootout; otherwise those columns are empty. `parse_results.py` writes 6-column format whenever any match in the file has penalty data; otherwise falls back to 4-column. `parseKoScores()` in `scoring.js` reads `home_pen`/`away_pen` and returns `{ home, away, homePen, awayPen }` when present. On the leaderboard bracket, penalty scores render as `1 (4)` / `1 (2)` per team row.

### ESPN → internal team name mapping

ESPN uses slightly different names for five teams. `parse_results.py` maps them via `ESPN_TEAM_MAP` before any lookup:

| ESPN `displayName` | Internal name (used in picks + leaderboard) |
|---|---|
| Czechia | Czech Republic |
| Türkiye | Turkey |
| Bosnia-Herzegovina | Bosnia and Herzegovina |
| Congo DR | DR Congo |
| Curacao | Curaçao |

---

## Scoring

### Group stage
- **2 points** per correct result pick (W1 / Draw / W2)
- Group stage max: 72 × 2 = **144 points**
- Stateless — each match scored independently; no dependency on other results
- Computed in JavaScript on the leaderboard page from `results/group_results.csv`

### Knockout stage
Points per correct pick (Scheme A):

| Round | Matches | Pts per correct pick | Max pts |
|---|---|---|---|
| Round of 32 | M73–88 | 4 | 64 |
| Round of 16 | M89–96 | 8 | 64 |
| Quarterfinals | M97–100 | 12 | 48 |
| Semifinals | M101–102 | 16 | 32 |
| 3rd place | M103 | 12 | 12 |
| Final | M104 | 24 | 24 |
| **KO total** | **32** | | **244** |
| **Grand total** | **104** | | **388** |

**Cascading scoring:** if a team loses in round R, all downstream picks for that team score 0 and are shown as `cascaded` (red square, italic strikethrough). Example: if you picked Spain to win M73 (R32), M89 (R16), M97 (QF), and Spain loses M73, then M89 and M97 both score 0 regardless of who actually wins those matches.

Cascade thresholds per round (the earliest elimination round that voids a pick):
- R32 (M73–88): never cascaded (threshold 0)
- R16 (M89–96): cascaded if team was out in R32 (threshold 2)
- QF (M97–100): cascaded if out before R16 (threshold 3)
- SF (M101–102): cascaded if out before QF (threshold 4)
- 3rd place (M103): cascaded if out before SF — SF losers are valid picks (threshold 4)
- Final (M104): cascaded if team didn't win their SF (threshold 5)

Implemented in `computeCombinedStandings()` via `eliminatedInRound` map + `cascadeThreshold(m)`.

**Max pts** column on leaderboard = current total + sum of `KO_POINTS[m]` for all `pending` picks (i.e. best-case remaining score assuming all pending picks turn out correct).

### Tiebreaker

When two or more players share the same total points, tiebreakers apply in order:

1. **Correct champion** — correctly picked the winner of M104
2. **Most correct picks** — total individual matches correctly predicted across all 104 matches

Both are derived automatically from picks vs results. Sort order: total pts ↓ → correct champion ↓ → total correct picks ↓ → name A–Z.

---

## What's Built ✅

### Variant 3 — Combined KO+group leaderboard (`WC2026_Pool_Leaderboard_Swiftly.html`) ✅

**Mode detection** (date-gated, automatic):
```javascript
const knockoutMode = new Date() >= new Date('2026-06-28T00:00:00Z');
```

**Group mode layout (before Jun 28):**
- Group standings, group tables, match results, provisional bracket (Variant 1) — all flat
- KO teaser card ("picks open Jun 27…") rendered below the bracket

**Knockout mode layout (from Jun 28):**
- Combined standings table (primary, top of page)
- Live KO bracket (Variant 3) below standings
- Thin section divider
- Group stage section flat below (no toggle, no accordion) — provisional bracket hidden (superseded by KO bracket)

**Combined standings table columns:** Rank · Name · Group pts · Knockout pts · Total · Max pts · Squares

**Squares:**
- Group stage: 72 small squares (9px) with dividers after matchday 1 (M24) and matchday 2 (M48); `flex-wrap: nowrap`
- KO stage: 32 larger squares (12px) with round dividers after R32/R16/QF/SF/3rd; champion pick label inline after Final square
- Colors: blue = correct, red (`#ee0e51`) = wrong or cascaded void, empty = pending

**Cascading tournament scoring** (`computeCombinedStandings(groupStandings, koPicksData, koResults, bracketData)`):
- Builds `eliminatedInRound[team]` map from actual results (which round each team was knocked out)
- `cascadeThreshold(m)` — per-match minimum elimination round that voids a pick:
  - R32 (M73–88): threshold 0 (never cascaded)
  - R16 (M89–96): threshold 2 (cascaded if out in R32)
  - QF (M97–100): threshold 3
  - SF (M101–102): threshold 4
  - 3rd (M103): threshold 4 (SF losers ARE valid; cascaded if out before SF)
  - Final (M104): threshold 5 (cascaded if out before winning SF)
- Status values: `correct` / `wrong` / `cascaded` / `pending` / `empty`
- `cascaded` = team was eliminated before reaching this match → 0 pts, red square, italic strikethrough label
- `wrong` = team was in the match but lost → 0 pts, red square
- Max pts = current total + sum of `KO_POINTS[m]` for all `pending` picks

**URL testing params** (no code changes needed, no cleanup required):
- `?games=N` — simulates leaderboard at match N (0–72 = group stage, 73–104 = knockout stage); slices results CSVs client-side
- `?ko=1` — shortcut to force knockout mode without specifying a game count

---

### Shared templates (across all pages)

**`teamHtml(name, showRank=true)`** — reusable team display function in every page:
- Returns: `🇩🇪 Germany <span class="team-rank">(10)</span>`
- `showRank=false` suppresses the rank where it would be redundant
- `.team-rank` CSS: `0.68rem`, `neutral-dark`, weight 400

**`renderGroupTableCard(grp, teams, stats, opts)`** — reusable group table renderer:
- `opts.showGD`: include GF/GA/GD columns (leaderboard: true, pick form: false)
- `opts.rowClassFn(team, index)`: returns CSS class per row (qualification colours)
- Wraps output in `.group-tables-grid` for consistent 10px spacing

### `bracket.js` — shared bracket rendering primitives

Loaded by all pages that render a bracket: `<script src="bracket.js"></script>`.  
Each page provides its own `renderBracket()` that calls the shared functions below.

**Shared data:**
- `FLAGS` — flag emoji lookup for all 48 teams
- `RANKINGS` — FIFA rankings (canonical name; was `LB_RANKINGS` in leaderboard before extraction)
- `KO_SCHEDULE` — UTC ISO kick-off times for M73–M104 (verified against ESPN `fifa.world` scoreboard API; R32 confirmed by matching ESPN team-slot descriptions to `R32_SLOTS`)
- `koDisplay(num)` — formats `KO_SCHEDULE[num]` into local-timezone string e.g. `Sat, Jun 28 · 3:00 PM` (day of week included, timezone abbreviation omitted); used in `matchCard()` and all mobile card renderers
- `R16`, `QF`, `SF` — bracket topology (feeder match pairs for each round)

**Shared rendering primitives:**
- `teamHtml(name, showRank=true)` — flag + name + rank (same as group table template)
- `isTbd(name)` — returns true for null/TBD/W73-style/1A-style/3Mxx-style slots
- `bkTeamRow(name, stateCls, score, extraAttrs='')` — one team row inside a bracket card; renders flag in `.bk-fl` + name+rank in `.bk-tn` separately (flag is NOT passed through `teamHtml` to avoid duplication); `extraAttrs` injects arbitrary HTML attributes for Variant 2 click targets
- `matchCard(num, home, away, label, homeScore, awayScore, homeCls, awayCls, homeAttrs='', awayAttrs='')` — full bracket card with match header + two team rows

**Shared bracket structure:**
- `buildBracketHtml(mkCard, opts={})` — builds the complete bracket HTML; `mkCard(matchNum)` is injected per-variant (resolves teams + state); `opts.podiumHtml` injects the podium section below the Final column's float  
- Bracket layout matches Wikipedia visual order: top half [74,77,73,75,83,84,81,82] → bottom half [76,78,79,80,86,88,85,87]

**Podium section:**
- `buildPodiumHtml(champion, runnerUp, thirdPlace)` — renders a 3-row card (🥇/🥈/🥉) at the top of the Final column, absolutely positioned in line with M89 (top of Round of 16). Pass `null` for any unknown slot → shows "TBD". No ranking shown in podium rows.
- Intended for **Variant 2** (user's picks) and **Variant 3** (live results) only. Currently passed with all-null in Variant 1 for preview; will be removed from Variant 1 once Variants 2/3 are built.
- CSS (`.bk-podium`, `.bk-podium-hdr`, `.bk-podium-row`, `.bk-podium-team`) lives in each page's `<style>` block (not in `bracket.js`).

**Shared DOM / positioning:**
- `positionAndConnectBracket()` — sizes all `.bk-float` containers to R32 height; positions R16/QF/SF/Final cards at feeder midpoints (cascading); positions M103 aligned with M99; positions podium top at M89 top
- `drawBracketConnectors()` — draws SVG `]` connector paths after positioning

### UTC kick-off time storage and local-TZ display

All match times are stored as UTC ISO 8601 strings and converted to the viewer's local timezone at render time. Never store or display ET/EDT times directly.

**Group stage (`scoring.js` + pick/leaderboard pages):**
- `MATCHES` array format: `[num, group, dateStr, utcKickoff, home, away]` — `dateStr` is a human-readable local date for display (e.g. `'Thu, Jun 11'`); `utcKickoff` is ISO 8601 UTC (e.g. `'2026-06-11T19:00:00Z'`)
- 3 midnight games (M6, M20, M36) have `utcKickoff` on the calendar-next day (e.g. M6 is `'2026-06-14T04:00:00Z'`); `dateStr` shows the local viewing date
- All 72 times verified against ESPN scoreboard API
- **Pattern used in leaderboard and group picks pages:**
  ```js
  const _tzAbbr = new Date().toLocaleTimeString('en-US', { timeZoneName: 'short' }).split(' ').pop();
  // → 'EDT', 'PDT', 'BST', etc. — computed once at page load

  function localMatchTime(utcStr) {
    const dt = new Date(utcStr);
    const t = dt.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
    return `${t}<span class="cell-tz"> ${_tzAbbr}</span>`;
  }
  ```
- Column header: `Time (${_tzAbbr})` — shows timezone once per table
- `.cell-tz { display: none }` on desktop (header shows TZ); `display: inline` on mobile via `@media (max-width: 640px)` (no column header visible)
- Group picks CSS grid: `grid-template-columns: 30px 28px 88px 72px auto` (`#` · `Grp` · `Date` · `Time` · picks); mobile breakpoint `max-width: 640px`

**KO stage (`bracket.js`):**
- `KO_SCHEDULE` stores UTC ISO strings for M73–M104; R32 times verified by cross-referencing ESPN team-slot descriptions against `R32_SLOTS`; R16/QF/SF/Final assigned chronologically within each local date
- `koDisplay(num)` converts to e.g. `Mon, Jun 28 · 3:00 PM` (weekday included, TZ abbreviation omitted); used in `matchCard()` and all mobile card renderers in leaderboard + KO picks pages

### Group stage pick page (`WC2026_Pool_Group_Picks.html`)
- Single shared page for all pools (no Swiftly/FandF split — Ritesh sorts CSVs manually)
- 72 matches, W1/Draw/W2 picks
- Live group tables (left sidebar, no sticky/scroll) via `renderGroupTableCard` template
  - Qualification colours only appear once all 4 teams in the group have ≥1 match picked
  - Team names: flag + name + rank via `teamHtml()` — consistent with leaderboard
  - Columns: Team (with flag+rank) · P · W · D · L · Pts
  - 10px gap between tables — matches leaderboard spacing
- Full 2026 WC tiebreaker chain
- Shortcuts bar (above picks table): Pick randomly · Pick higher-ranked team · Pick all draws · Reset all picks
- Name field: prominent blue-bordered card, 1.1rem bold input
- Validation error if name missing on submit
- Progress bar in sticky bar
- Pick buttons clip long team names (ellipsis)
- CSV download → `wc26_group_[name].csv`

### Leaderboard pages (Swiftly + FandF)
- Standings table with 72 mini squares (9px, `sq-sm`); blue = correct, red (`#ee0e51`) = wrong
- Matchday dividers after M24 and M48; `nowrap` layout
- Tooltip on hover: match, your pick, result, correct/wrong
- Group tables via `renderGroupTableCard` template (with GF/GA/GD): flag + name + rank, tighter padding on numeric columns
- Match results table: all 72 matches shown (completed + upcoming); see below for format
- Qualification status: blue (top 2), green (3rd qualified), yellow (3rd pending), red (eliminated)
- Progress bar in sticky bar: "GROUP STAGE" · fill bar · "X / 72 matches played" · last updated
- Collapsible sections
- **Live knockout bracket** (collapsible section at bottom) — see below

#### Match results table (group stage)
- Columns: `#` · `Grp` · `Date` · `Time (TZ)` · `Result` · `Score` — Group moved immediately after # so it scans fast; TZ abbreviation in column header reflects viewer's local timezone
- On mobile (`max-width: 680px`): Time column hidden entirely; `#` and `Grp` also hidden; result + score remain
- **Completed matches:** `[Winner bold] beat [loser muted] · score` or `[A muted] drew [B muted] · score`; winner's score always listed first (score flipped for away wins so winner's goals appear on the left)
- **Upcoming matches:** team names shown as `A v B` with slight opacity (0.45) — muted but readable
- Team names use `teamHtml()`: flag + name + (rank); `white-space: nowrap` prevents name/rank from splitting across lines
- On mobile the result cell wraps between the verb and the second team when names are long; score column stays pinned right
- **Correctness pill** — appended to the Score cell for completed matches; shows `N/total` with a color-tinted pill (blue ≥67% correct, orange 33–66%, red <33%). Separated from the score text by `margin-left: 8px`. Pill also appears right-aligned in the `.bk-mnum` header of KO desktop bracket cards and inline in `.bk-mob-meta` on mobile. See CLAUDE.md for full implementation details.

### Knockout bracket (leaderboard pages — Variant 1)
- 5-column horizontal layout: R32 → R16 → QF → SF → Final/3rd
- Shows **Provisional** badge (orange) while group stage is in progress; **Confirmed ✓** badge (green) once `knockout_bracket.json` has `"confirmed": true`
- `confirmed: true` is set by `parse_results.py` only when BOTH conditions are met: (1) all 72 group results present, AND (2) computed R32 bracket has been cross-checked against the Wikipedia knockout bracket page via MediaWiki API
- Leaderboard fetches `data/knockout_bracket.json` in `init()` alongside picks + results; falls back gracefully (stays Provisional) if the file doesn't exist yet (404)
- All **495/495** third-place combinations encoded in 3 files
- `test_bracket.py` — end-to-end test, all 495 combos verified passing
- Uses `bracket.js` for all rendering primitives; page only defines `slotTeams()` + `mkCard()` + calls `buildBracketHtml(mkCard, { podiumHtml })`

**Bracket design (all variants):**
- ESPN-style cards: flag (`.bk-fl`) + name+rank (`.bk-tn`) — flag rendered separately, not via `teamHtml()` (avoids double-flag)
- Match header bar (`.bk-mnum`): `[Round] · M# · Day, Date · Time` (e.g. `R32 · M74 · Sat, Jun 28 · 1:00 PM`); timezone abbreviation omitted; `roundLabel(103)` returns `'3rd'`
- All `.bk-col` use `flex: 1` (equal width); no per-round flex overrides
- **Sticky round header strip** (`.bk-header-strip`) sits above `.bk-wrap`, auto-pins below `.sticky-bar` using measured height. `position: sticky` works because leaderboard `.section-body` uses `overflow: clip` (not `hidden`), which clips without creating a scroll container
- Round headers with blue intensity progression: lightest R32 → darkest Final; strip injected via `bracket.js` CSS tag
- Matches in Wikipedia bracket order: [74,77,73,75,83,84,81,82,76,78,79,80,86,88,85,87]
- Uniform 16px gap at all hierarchy levels — R32 rows evenly distributed; R16/QF/SF/Final midpoints mathematically symmetric
- R16/QF/SF/Final cards absolutely positioned by JS to align team-dividing line with midpoint of feeders
- SVG `]` bracket connectors drawn after positioning
- Final column label: `🏆 Final (and 3rd place)`
- Podium section (🥇/🥈/🥉) in Final column, top aligned with M89
- Desktop team rows: flush bordered pill style (0.92rem, 5px/9px padding, 1.5px `#cce8f4` border, solid blue winner fill). Full CSS + gotchas in `CLAUDE.md`.

### Knockout pick page (`WC2026_Pool_Knockout_Picks.html`) — Variant 2 ✅
- Fetches `knockout_bracket.json` on load; shows "not yet available" if file missing (pre-Jun 27)
- R32 teams populated from `bracketData.round_of_32`; R16+ slots cascade from user picks
- Click any team row to pick winner — both teams must be known before either row is clickable
- Winner cascades into the next round's slot; downstream picks cleared if they become invalid
- Picks state: `picks = { matchNum: winnerName }` — 32 picks total
- **No re-render on pick**: `updateCards()` replaces each `.bk-card` outerHTML in-place on desktop (preserves `style.top`); replaces `#mob-card-${m}` outerHTML on mobile (preserves active tab state)
- Full `renderBracket()` only called once on initial load
- Podium updates live as Final and 3rd place picks are made
- Shortcuts: 🎲 Pick randomly · 💪 Pick higher-ranked · ✕ Reset — all use `updateCards()`
- Progress bar: `X / 32 matches picked` — counts `Object.keys(picks).length`

**Mobile tab view (≤ 640px):**
- Desktop bracket hidden; `.bk-mobile-tabs` shown
- Round tabs: R32 · R16 · QF · SF · 3rd · Final; auto-opens first round with any unpicked matches
- `MOB_ROUNDS` match order mirrors desktop bracket column order
- `PAIR_NEXT` maps each pair of matches in a round to their next-round match (e.g. [M74,M77]→M89)
- Each pair wrapped in `.bk-mob-pair-group` (blue-light border, 12px radius) — visually groups the two feeders
- Floating blue pill (`.bk-mob-pair-pill`) between the two matches in each group: "winners meet in R16 · M89"
- Team rows use group-picks button style: white bg + `1.5px solid var(--blue-light)` unselected; solid `var(--swiftly-blue)` fill + white text when picked; borderless muted when loser
- `.team-rank` inherits white at 75% opacity on picked/winner rows (matching group picks behaviour)
- All data fetched from `raw.githubusercontent.com` with `cache: 'no-store'` — no CDN, always fresh
- **Auto-advance:** when all matches in the current tab are picked, a centered toast appears — "Moving to Round of 16 in 3s…" — counts down 3→2→1, then switches tab and scrolls to top. Only triggers on manual picks (`pickTeam`), not shortcuts.

### GitHub Actions
- `ci.yml` — runs on every push and PR: `test_parse_results.py -v` → `test_aggregate_picks.py -v` → `test_bracket.py` → `node test_e2e.js`. No simulate.py required — test_bracket.py generates its own fallback data.
- `update.yml` — runs every 15 min, Jun 11–Jul 19
- `simulate.yml` — generates test picks + results (supports `--seed N` for reproducibility); installs `requests` before running
- `clear_simulation.yml` — wipes simulation data: deletes `*simulation*` CSVs, clears both results CSVs, writes `{}` to all picks/bracket JSONs; no CDN purge needed
- `auto_clear_simulation.yml` — same as above, fires automatically at 1pm ET Jun 11 (2hrs before kickoff)

### `data/knockout_bracket.json` format
```json
{
  "status": "provisional" | "confirmed",
  "confirmed": false | true,
  "qualifying_groups": ["A","B",...,"L"],
  "third_place_groups": ["E","F","G","H","I","J","K","L"],
  "combo_key": "EFGHIJKL",
  "matches": {
    "73": {"home": "2A", "away": "2B"},
    ...
    "104": {"home": "W101", "away": "W102"}
  }
}
```
`confirmed: true` requires all 72 group results + Wikipedia R32 cross-check passing (set by `parse_results.py`).  
Leaderboard pages fetch this file and use `bracketData.confirmed` for the Confirmed ✓ / Provisional badge — they do NOT compute confirmation locally.

---

## Knockout Stage Structure (reference)

### Round of 32 (M73–M88)
| Match | Home | Away | Type |
|---|---|---|---|
| 73 | 2A | 2B | Fixed |
| 74 | 1E | 3rd(A/B/C/D/F) | 3rd slot |
| 75 | 1F | 2C | Fixed |
| 76 | 1C | 2F | Fixed |
| 77 | 1I | 3rd(C/D/F/G/H) | 3rd slot |
| 78 | 2E | 2I | Fixed |
| 79 | 1A | 3rd(C/E/F/H/I) | 3rd slot |
| 80 | 1L | 3rd(E/H/I/J/K) | 3rd slot |
| 81 | 1D | 3rd(B/E/F/I/J) | 3rd slot |
| 82 | 1G | 3rd(A/E/H/I/J) | 3rd slot |
| 83 | 2K | 2L | Fixed |
| 84 | 1H | 2J | Fixed |
| 85 | 1B | 3rd(E/F/G/I/J) | 3rd slot |
| 86 | 1J | 2H | Fixed |
| 87 | 1K | 3rd(D/E/I/J/L) | 3rd slot |
| 88 | 2D | 2G | Fixed |

Note: M84 (1H vs 2J) and M86 (1J vs 2H) are intentional cross-matches. Same for M75/M76.

### Round of 16 (M89–M96)
| Match | Home | Away |
|---|---|---|
| 89 | W74 | W77 |
| 90 | W73 | W75 |
| 91 | W76 | W78 |
| 92 | W79 | W80 |
| 93 | W83 | W84 |
| 94 | W81 | W82 |
| 95 | W86 | W88 |
| 96 | W85 | W87 |

### Quarterfinals (M97–M100)
| Match | Home | Away |
|---|---|---|
| 97 | W89 | W90 |
| 98 | W93 | W94 |
| 99 | W91 | W92 |
| 100 | W95 | W96 |

### Semifinals, 3rd Place, Final (M101–M104)
| Match | Home | Away |
|---|---|---|
| 101 | W97 | W98 |
| 102 | W99 | W100 |
| 103 | L101 | L102 (3rd place) |
| 104 | W101 | W102 (Final) |

### 3rd Place Slot Assignment
The 8 qualifying third-place teams fill these specific slots:
| Slot match | Opponent |
|---|---|
| M79 | 1A's opponent |
| M85 | 1B's opponent |
| M81 | 1D's opponent |
| M74 | 1E's opponent |
| M82 | 1G's opponent |
| M77 | 1I's opponent |
| M87 | 1K's opponent |
| M80 | 1L's opponent |

Lookup key = sorted string of the 8 qualifying groups (e.g. `"EFGHIJKL"`). All 495 combinations encoded. Source: https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_knockout_stage

---

## Bracket Implementation

All three variants share ESPN-style card DNA: flag emoji + team name + score, winner row solid blue, loser row muted, TBD rows grey italic, round header strip with blue intensity progression (lightest R32 → darkest Final). All rendering primitives live in `bracket.js`; each page supplies its own `mkCard()`.

### Variant 1 — Provisional bracket (leaderboard, group stage)
Embedded in both leaderboard pages. Read-only. Real team names fill in as groups confirm; greyed italic for unresolved 3rd-place and future rounds. Shows **Provisional** badge (orange) until `knockout_bracket.json` has `confirmed: true`, then **Confirmed ✓** (green).

### Variant 2 — Pick bracket (`WC2026_Pool_Knockout_Picks.html`)
Shared by both pools. Click any team row to pick winner — cascades into next-round slot; downstream picks clear if invalidated. 32 picks total. CSV download → `wc26_knockout_[name].csv`. Desktop: `updateCards()` replaces cards in-place. Mobile: tab view with auto-advance toast (3s countdown when a full round is picked). Shortcuts: 🎲 random · 💪 higher-ranked · ✕ reset.

### Variant 3 — Results bracket (leaderboard, knockout stage)
Same cards as Variant 1. `mkCard` reads from `koResults`: completed matches show winner (solid blue) + loser (muted) + score; penalty shootouts render as `1 (4)` / `1 (2)`. Unplayed matches show known teams in neutral style. Correctness pill right-aligned in `.bk-mnum` for completed matches.

---

## Still To Do

- [x] Clear simulation data (`Actions → Clear simulation data`) before Jun 11 — or auto-clear fires at 1pm ET Jun 11
- [ ] Share group pick page links with participants, collect and upload CSVs to `picks/group/swiftly/` and `picks/group/fandf/`
- [ ] Share knockout pick page link **after final group stage game (Jun 27)** — KO picks are submitted once group stage is complete; deadline is **before M73 (Jun 28, 3:00 PM ET / 19:00 UTC)**. Collect and upload CSVs to `picks/knockout/swiftly/` and `picks/knockout/fandf/`

---

## Testing

### Unit tests — `test_leaderboard.js`

Run: `node test_leaderboard.js`

80 tests across 8 sections, exercising scoring functions imported from `scoring.js`:

- **Group stage scoring** — 2 pts per correct pick, 0 for wrong/empty, pending when result not yet available, alphabetical sort on equal pts
- **CSV parsing** (`parseKoResults`) — normal, empty, header-only, trailing blank lines
- **Bracket resolution** (`getKoTeams`) — R32 from bracketData, R16/QF/SF chained forward, M103 computes SF losers, M104 computes SF winners, null bracketData → TBD
- **KO scoring** — all 32 correct = 244 pts, individual round point values (4/8/12/16/12/24), all statuses correct
- **Cascade rules** — R32 loser: pick is `wrong` (not cascaded); R16 loser: downstream picks cascade; M103 special: SF losers (round 4) are valid picks (4 < 4 = false); M104: SF loser cascades
- **Max pts** — pending picks add full KO_POINTS value; cascaded picks add nothing
- **Tiebreakers** — total pts → correct champion → total correct picks → alphabetical
- **KO-only participants + sanity** — player with no group picks, KO_POINTS sums to 244, grand total 388

**Important fixture constraint documented in tests:** bracket team names must be internally consistent. A team appearing in two R32 slots will be double-registered in `eliminatedInRound` (once as loser, at round 1). Tests use team names that appear in only one R32 slot.

### End-to-end simulation — `test_e2e.js`

Run: `node test_e2e.js`

Generates a full 104-match tournament (seeded, reproducible — same result every run) with 10 participants (Alice–Jack) plus 3 sentinel participants whose expected scores are computed exactly from the results. Runs the real scoring pipeline and checks **152 invariants** (105 structural + 47 exact-score).

**Structural invariants (105):**
- All 13 participants present, group pts 0–144, KO pts 0–244
- totalPts = groupPts + koPts for all participants
- No pending picks when all 104 results provided; maxPts = totalPts
- All 72 group pick results resolved per participant
- Sort order satisfies the full 4-tier tiebreaker chain for each consecutive pair
- koPts = sum of `correct` KO pick points (proves cascaded picks score exactly 0)
- correctChampion flag consistent with M104 pick status
- Aggregate point bounds and coverage sanity

**Exact-score invariants (47) — sentinel participants:**
- `__Perfect__` (picks every match correctly) → **388 pts** (144 + 244); all 72 group picks correct; all 32 KO picks correct; correctChampion = true
- `__Zero__` (picks every match wrong) → **0 pts**; no correct group picks; no correct KO picks; correctChampion = false
- `__CascadeR32__` (correct group + correct R32, then all R16+ picks cascade) → **208 pts** (144 + 64); all 16 R32 picks correct; all 16 R16+ picks cascaded

Simulated tournament result (seed 20260611): **Belgium wins**, beats Canada in Final, England wins 3rd place.

### Mid-tournament state tests — `test_partial.js`

Run: `node test_partial.js`

84 tests across 5 tournament phases verifying correct behaviour when only some results are in:

- **Phase 0** — no results yet: all picks pending/empty, 0 pts, participants sorted alphabetically
- **Phase 1** — partial group results (M1–M3 only): correct/wrong/pending/empty status per pick, partial groupPts accumulate correctly
- **Phase 2** — all 72 group results, no KO bracket yet: maxPts includes pending KO upside; koPts = 0 (no bracket → no KO scoring)
- **Phase 3** — R32 in progress (M73 played, Spain eliminated): **cascade fires immediately** — all of Spain's downstream picks (R16, QF, SF, Final) flip to 'cascaded' even before those matches are played; maxPts drops to 0 for picks that are already eliminated
- **Phase 4** — R16 in progress: cascade continues, maxPts = groupPts + koPts + pendingKoPts at every step

Key insight documented: cascade is not gated on the downstream match being played. A team eliminated in R32 immediately voids all downstream picks, even unplayed ones.

### Python unit tests — `test_parse_results.py`

Run: `python3 test_parse_results.py`

**84 tests** across 13 classes covering every testable function in `.github/scripts/parse_results.py`:

- `TestEspnTeamName` (9) — ESPN display-name normalisation: Czechia→Czech Republic, Türkiye→Turkey, Curaçao, Bosnia, passthrough, missing field
- `TestEspnTeamNameValidation` (4) — **new:** unknown name triggers KNOWN_TEAMS warning; valid name is silent; all TEAM_CODES in KNOWN_TEAMS; all ESPN_TEAM_MAP values in KNOWN_TEAMS
- `TestParseGroupResultsEspn` (10) — home win, away win, draw, incomplete skip, non-group-stage skip, ESPN name mapping, multiple matches, unknown matchup skip, empty events, match lookup coverage
- `TestGroupEspnHomeAwayReversal` (4) — **new:** ESPN reversed home/away detected and scores swapped; draw stays draw; home-team-wins case; normal order unaffected
- `TestParseKoResultsEspn` (13) — single R32, away win, R16 resolves after R32, R16 not resolved without R32, incomplete skip, non-KO slug skip, empty, multiple rounds, penalty home wins, penalty away wins, no-shootout is 2-tuple
- `TestKoEspnHomeAwayReversal` (3) — **new:** KO ESPN reversal detected, scores swapped; penalty scores swapped correctly; normal order unaffected
- `TestWriteCsv` (2) — output format (sorted by match number, correct columns), empty results
- `TestWriteKoResultsCsv` (4) — output format, no scores, with penalties (6-col), mixed no-pen uses 4 cols
- `TestExtractTeam` (10) — `{{fb|...}}`, `{{fb-rt|...}}`, `{{#invoke:flag|fb|...}}`, `{{#invoke:flagg|...}}`, wiki-link fallback, unknown code, empty, all 48 TEAM_CODES parseable
- `TestExtractScore` (9) — dash, en-dash, 0-0, high score, whitespace, text, empty, partial
- `TestParseResultsWikitext` (10) — home win, away win, draw, unplayed (no score field), placeholder score, multiple blocks, lowercase `{{football box}}`, unknown team, empty wikitext, `{{#invoke:flag|...}}` format
- `TestMatchLookupIntegrity` (3) — exactly 72 entries, all numbers 1–72 present, all team names in TEAM_CODES
- `TestComputeGroupStandings` (6) — **new:** all 12 groups present; winner tops group; 4 teams per group; empty results OK; points accumulate correctly; draw gives 1pt each

### Python unit tests — `test_aggregate_picks.py`

Run: `python3 test_aggregate_picks.py`

**28 tests** across 4 classes covering every function in `.github/scripts/aggregate_picks.py`:

- `TestNameFromFilename` (5) — `wc26_group_` prefix stripped; hyphens → spaces → title case; full paths handled; simulation names; multi-part names
- `TestNameFromKnockoutFilename` (4) — `wc26_knockout_` prefix stripped; same name normalization
- `TestLoadPicksCsv` (10) — home win → `W1`, away win → `W2`, draw → `Draw`; header skipped; multiple matches; unknown team skipped; short rows skipped; empty file; header-only file; unknown match number skipped
- `TestLoadKnockoutCsv` (9) — single pick; header skipped; multiple rounds; empty pick skipped; short rows skipped; empty file; header-only file; all 32 match numbers; quoted team name with comma

### Simulation data for local testing — `simulate.py`

Run: `python .github/scripts/simulate.py --participants 10 --stage all [--seed N] && python .github/scripts/aggregate_picks.py`

`--seed N` makes all random choices deterministic and reproducible (default: random). Generates realistic picks CSVs for N simulated participants in both pools, plus group and KO results, plus the confirmed bracket JSON. The leaderboard fetches these files via HTTP — serve with `python -m http.server 8000`. This is the canonical local dev workflow; see the Local Dev Workflow section above.

---

## Style Guide

### Color Tokens (`:root` on every page)

| Token | Value | Used for |
|---|---|---|
| `--swiftly-blue` | `#009edf` | Primary brand, links, active states, headers, correct picks |
| `--swiftly-orange` | `#ff9e16` | Warnings, validation errors |
| `--swiftly-red` | `#ee0e51` | Wrong picks, cascaded void picks (leaderboard pages) |
| `--neutral-lightest` | `#f7f7f7` | Page background, alternating table rows |
| `--neutral-light` | `#ebebeb` | Borders, dividers, progress bar track |
| `--neutral-medium` | `#c4c4c4` | Placeholder text, muted labels |
| `--neutral-dark` | `#525f66` | Secondary text, column headers |
| `--neutral-darkest` | `#131e27` | Body text |
| `--blue-lightest` | `#ebf9ff` | Hover backgrounds, qualified-row tint |
| `--blue-light` | `#ccecf9` | Header subtitle text |
| `--radius` | `10px` | Default card border radius |

Never hardcode hex values except: `#ffffff` (white), `#22863a` (confirmed badge), `#e6f9ef`/`#fff8e6`/`#fdf0f0` (qualification row tints), and the bracket header blue scale (`#B5D4F4` → `#85B7EB` → `#378ADD` → `#185FA5` → `#0C447C` → `#042C53`).

Additional semantic tokens on leaderboard pages:
- `--correct-green: #5ce65c` — legacy; still defined but superseded by `--swiftly-blue` for correct pick indicators
- `--wrong-red: #ff6b6b` — legacy; still defined but superseded by `--swiftly-red` (`#ee0e51`) for wrong/cascaded indicators

### Typography

Fonts: **Inter** (400, 700) for all body/UI text; **Poppins** (600) for page titles, group table headers, name card label.

| Role | Size | Weight | Used for |
|---|---|---|---|
| Page title | `1.5rem` | 600 Poppins | `.header-title` |
| Page subtitle | `0.875rem` | 400 Inter | `.header-subtitle` |
| Body / data | `0.78rem` | 400–700 Inter | Table rows, bracket cards, buttons, match info |
| Column headers | `0.68rem` | 700 Inter | Uppercase letter-spaced labels (TEAM, PTS, etc.) |
| Small labels | `0.65rem` | 700 Inter | Chevrons, bracket separators |
| Name input | `1.1rem` | 700 Inter | Pick form name field only |

### Mobile breakpoints

All 4 pages are mobile-friendly. Two breakpoints:

- **Portrait** — `@media (max-width: 640px)`
- **Landscape** — `@media (max-width: 896px) and (orientation: landscape)` — stacks group tables/results vertically; standings card scrollable horizontally

| Element | Mobile behaviour |
|---|---|
| `.header-title` | `font-size: clamp(0.82rem, 3.6vw, 1.2rem); white-space: nowrap` — fits on one line |
| Group picks match rows | 2-row CSS grid: meta (# date time grp) on row 1, pick buttons on row 2 spanning full width |
| Pick buttons | `padding: 7px 6px; min-height: 38px`; long team names use `SHORT_NAMES` map (e.g. Bosnia → Bosnia…) — applies on all screen sizes, not just mobile |
| Leaderboard: squares column | Hidden (`display: none`) |
| Leaderboard: max pts column | Hidden |
| Leaderboard: group tables | Appear below match results (CSS `order` swap on `.side-left`/`.side-right`) |
| Leaderboard: results table | # column hidden; Date/Time hidden; result + score remain; score pinned right |
| KO bracket (desktop) | Flush bordered pill rows: `font-size: 0.92rem; padding: 5px 9px; border-radius: 5px; border: 1.5px solid #cce8f4; margin: 0 4px`. Uniform 16px gap at all hierarchy levels. Winner: solid `var(--swiftly-blue)` fill. Loser: transparent. |
| KO bracket mobile | Desktop `.bk-outer` hidden; `.bk-mobile-tabs` shown. Round tabs + pair-grouped match cards. |
| KO mobile team row | `0.90rem`, `padding: 7px 9px`, `border-radius: 6px`. Unselected: white bg + `1.5px solid var(--blue-light)`. Selected/winner: solid `var(--swiftly-blue)` fill + white text. Loser: borderless + muted. |
| KO mobile pair group | `.bk-mob-pair-group`: `border: 1px solid var(--blue-light); border-radius: 12px; padding: 8px`. Wraps two match cards + pill connector. |
| KO mobile pill | `.bk-mob-pair-pill span`: `10px`, `#185FA5`, `var(--blue-lightest)` bg, `1px solid var(--blue-light)` border, `border-radius: 20px`. |

**FandF rule:** `make_fandf.py` regenerates FandF from Swiftly — all mobile CSS propagates automatically. Never edit FandF directly.

---

### Live scores (group stage)

> Built Jun 11, 2026. Full spec in CLAUDE.md.

- **Toggle:** `const LIVE_SCORES_ENABLED` in leaderboard JS (internal flag, not URL param)
- **Data:** Client-side ESPN fetch, polling every ~60s while games are in-progress
- **Squares:** New `live-correct` / `live-wrong` statuses — pulse in full color (blue/red) while game is live; snap to solid once final
- **Results table:** In-progress rows show current minute in time cell + live score — both pulse in default text color; `FT` shown once final
- **Standings:** Frozen during live — only squares change
- **Scope:** Group stage only; KO live scores planned for later (same architecture)

---

### Layout

All pages: `<header>` → `<div.sticky-bar>` → `<div.container>` (max-width 1200px, padding 24px 16px 64px). Picks form uses a two-column layout inside container: sidebar 380px fixed + main `flex: 1`.

### Cards

```
background: #ffffff
border: 1px solid --neutral-light
border-radius: --radius (10px)
box-shadow: 0 1px 5px rgba(0,0,0,0.04)
```

Prominent card (name field): `border: 2px solid --swiftly-blue`, `box-shadow: 0 2px 10px rgba(0,158,223,0.12)`.

### Tables

- Body: `0.78rem`
- Header row: `background: --neutral-lightest`, `border-bottom: 2px solid --neutral-light`
- Header cells: `0.68rem`, 700, uppercase, `letter-spacing: 0.5px`, `color: --neutral-dark`
- Row border: `1px solid --neutral-light`; even rows `--neutral-lightest`; hover `--blue-lightest`
- Cell padding: `5px 8px` (compact) or `8px 12px` (standard)

### Group Table Qualification Colours

Only appear once all 4 teams in the group have ≥1 result/pick.

| State | Class | Background |
|---|---|---|
| Top 2 | `qualified` | `--blue-lightest` |
| 3rd — confirmed | `third-qual` | `#e6f9ef` |
| 3rd — pending | `third-pending` | `#fff8e6` |
| Eliminated | `eliminated` | `#fdf0f0` |

### Buttons

**Primary:** Poppins 600, `0.78rem`, `--swiftly-blue` bg, white text, `padding: 15px 48px`, `border-radius: 8px`.

**Secondary / shortcut:** Inter 700, `0.78rem`, white bg, `border: 1.5px solid --neutral-light`, `border-radius: 5px`, `padding: 4px 12px`. Hover: blue border + blue text + `--blue-lightest` bg.

**Pick buttons (W1/Draw/W2):** Same as secondary but `padding: 6px 8px` (desktop). Selected state: `--swiftly-blue` bg, white text. Always include `overflow: hidden; text-overflow: ellipsis; min-width: 0` to prevent long team names expanding the row.

### Progress Bar

Label (`0.68rem`, uppercase) → fill bar (6px tall, `--swiftly-blue` fill, `--neutral-light` track) → count (`0.78rem`, `--swiftly-blue`, bold). Used in the sticky bar of all pages.

### Flags

All 48 teams have flag emojis in the `FLAGS` JS object on every page. Render as `FLAGS[team] + ' ' + team`. No fallback character — show name only if flag missing.

### Team Name Mapping (Wikipedia → display)

| Display | FIFA |
|---|---|
| Turkey | Türkiye |
| Ivory Coast | Côte d'Ivoire |
| Cape Verde | Cabo Verde |
| DR Congo | Congo DR |
| South Korea | Korea Republic |

---

## Local Dev Workflow (rapid design iteration)

The leaderboard always fetches live data from GitHub — there is no embedded sim data or `USE_LOCAL_DATA` flag. For local testing, use `simulate.py` to populate the CSV files, then serve the repo with a local HTTP server:

**Workflow:**
1. `python .github/scripts/simulate.py --participants 10 --stage all` — writes picks + results CSVs
2. `python .github/scripts/aggregate_picks.py` — builds the aggregated JSON files the leaderboard fetches
3. `python -m http.server 8000` from the repo root
4. Open `http://localhost:8000/WC2026_Pool_Leaderboard_Swiftly.html` in Chrome
5. Append `?games=N` to the URL to simulate any point in the tournament (e.g. `?games=88` = R32 complete)
6. Edit CSS/JS in editor → save → ⌘R in browser
7. When done: regenerate FandF from Swiftly (`python3 make_fandf.py`), push via GitHub Desktop

**Or without touching your machine:** trigger **Actions → Simulate picks and results** (participants=10, stage=all) on GitHub, then browse the live GitHub Pages URL with `?games=N`.

**FandF sync rule:** never edit `WC2026_Pool_Leaderboard_FandF.html` directly. Always edit Swiftly, then regenerate FandF. The two files are intentionally identical except 3 lines: `<title>`, header text, `POOL_ID`.

---

## Bracket Technical Notes

- **`bracket.js`**: all shared rendering primitives live here. Pages load it via `<script src="bracket.js">`, then define a `renderBracket()` that calls `buildBracketHtml(mkCard, opts)` with a page-specific `mkCard` function.
- **Match ordering** in R32 column follows Wikipedia bracket visual order (not M73–M88 numerical): [74,77,73,75,83,84,81,82,76,78,79,80,86,88,85,87]
- **Team name template in bracket cards**: `bkTeamRow` renders flag in `.bk-fl` and name+rank in `.bk-tn` *separately*. It does NOT call `teamHtml()` for the label — that would double the flag. The rank is pulled from `RANKINGS` inline.
- **Connector anchor point**: team-dividing line (bottom of home row / top of away row), NOT card center — computed via `getBoundingClientRect` on `.bk-team` rows
- **Float positioning**: R16/QF/SF/Final cards are `position: absolute` inside `.bk-float` divs. JS sets their `top` to align the team-dividing line at the midpoint of their two feeders. Cascades R32→R16→QF→SF→Final in sequence so each level uses updated positions from previous level.
- **Podium positioning**: `#bk-podium-results` is inside the `.bk-float` of the `fin` column (also `position: absolute`). Its `top` is set to align with M89's top edge (top of Round of 16).
- **SVG connectors**: drawn after all cards positioned. `]` shape for each pair: horizontal stub right → vertical bar → horizontal stub right → midpoint horizontal to next card's left edge. Color `#B5D4F4` (light blue), 1.5px stroke.
- **Variant 2 hook**: `bkTeamRow` accepts `extraAttrs` (4th param) for injecting `data-match`/`data-team` attributes on click targets. `matchCard` accepts `homeAttrs`/`awayAttrs` (9th/10th params) that forward to `bkTeamRow`.
- **Variant 3 readiness**: `matchCard()` already accepts `homeScore`, `awayScore`, `homeCls`, `awayCls` params. When knockout results exist, pass them in. Connectors and positioning will still work.
- **Podium in Variant 1**: currently passes `buildPodiumHtml(null, null, null)` — shows TBD. Remove this call from Variant 1's `renderBracket` once Variants 2/3 are built.
- **KO_SCHEDULE**: stores UTC ISO strings (e.g. `'2026-06-28T19:00Z'`) for all 32 KO matches (M73–M104), verified via ESPN API. Displayed via `koDisplay(num)` → `Sat, Jun 28 · 1:00 PM` (viewer's local timezone, day of week prepended, TZ abbreviation dropped). `roundLabel(103)` returns `'3rd'` (not `'3rd Place'`) to fit within the card width.
- **`.bk-mnum` on leaderboard**: `display: flex; justify-content: space-between` with label in `.bk-mnum-label` (overflow hidden, ellipsis) and correctness pill right-aligned. On the KO picks page `.bk-mnum` remains plain block — no flex, no pill. `bracket.js` is not modified; the pill is injected in the leaderboard via string-replace in `mkCard()`.

---

## Notes

- GitHub Actions free tier: well within limits (date-gated, only runs Jun 11–Jul 19)
- ESPN API updates within ~5 min of match end; leaderboard reflects within ~5 min (next Actions run + leaderboard auto-refreshes every 5 min)
- Pick submission is download-only — Ritesh uploads CSVs manually to GitHub
- Every participant's picks exist as individual CSV in `picks/` — fully auditable
- Leaderboard URLs use exact filenames: `WC2026_Pool_Leaderboard_Swiftly.html` (not `WC2026_Leaderboard_Swiftly.html`)
