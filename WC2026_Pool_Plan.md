# World Cup 2026 Pool — Master Plan

Last updated: May 21, 2026 (ESPN API results pipeline complete; group + KO scoring documented)

---

## Overview

Two pools running in parallel on the same codebase:
- **Swiftly** — company pool
- **FandF** — friends & family pool

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

## Repo File Inventory (current state)

```
wc26/
├── WC2026_Pool_Group_Picks.html               ← group pick page (shared by both pools)
├── WC2026_Pool_Knockout_Picks.html            ← knockout pick page (shared by both pools)
├── WC2026_Pool_Leaderboard_Swiftly.html       ← leaderboard + knockout bracket (Swiftly)
├── WC2026_Pool_Leaderboard_FandF.html         ← leaderboard + knockout bracket (F&F)
├── bracket.js                                 ← shared bracket rendering primitives (all variants)
├── test_bracket.py                             ← bracket end-to-end test (495 combos verified)
├── picks/
│   ├── group/
│   │   ├── swiftly/                            ← participant CSVs (uploaded manually by Ritesh)
│   │   └── fandf/
│   └── knockout/
│       ├── swiftly/                            ← empty until Jun 27
│       └── fandf/
├── data/
│   ├── knockout_bracket.json                   ← R32 matchups (auto-generated, live)
│   ├── group_swiftly_picks.json                ← aggregated group picks
│   └── group_fandf_picks.json
├── results/
│   ├── group_results.csv                       ← match results (auto-updated from ESPN API)
│   └── knockout_results.csv                    ← KO results (simulation data now; real data Jun 28+ via parse_results.py)
└── .github/
    ├── workflows/
    │   ├── update.yml                           ← every 15 min, Jun 11–Jul 19
    │   ├── simulate.yml                         ← generates test data
    │   └── clear_simulation.yml                 ← wipes simulation data
    └── scripts/
        ├── parse_results.py                     ← ESPN API → results CSV + knockout_bracket.json (two fetches: group M1–72, KO M73–104)
        ├── aggregate_picks.py                   ← pick CSVs → picks JSON
        └── simulate.py                          ← generates simulated picks + results
```

---

## Pick Submission Flow

1. Participant opens their pool's pick page (shared link)
2. Enters name, makes picks for all 72 matches
3. Clicks **"Happy with your picks?"** → **"Submit"** → CSV downloads
4. Participant emails CSV to Ritesh
5. Ritesh uploads CSV to `picks/group/swiftly/` or `picks/group/fandf/` on GitHub

### Pick CSV format

**Group:** `wc26_group_john-smith.csv`
```
match,result
1,"Mexico v South Africa",Mexico win
2,"South Korea v Czech Republic",Draw
...
72,"DR Congo v Uzbekistan",DR Congo win
```

**Knockout:** `wc26_knockout_john-smith.csv`
```
match,winner
73,Netherlands
74,Spain
...
104,Brazil
```

Ritesh routes the CSV to the correct pool folder on upload (`picks/group/swiftly/` or `picks/group/fandf/` etc.).

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
4. If `data/knockout_bracket.json` exists, calls `fetch_espn_ko_events()` (Jun 28–Jul 20 date range). ESPN returns `competitor.winner = true` on the winning team — no score parsing needed. Results are resolved by walking the bracket topology (R32 → R16 → QF → SF → 3rd/Final), propagating actual team names through `W73`-style references as rounds complete. Writes `results/knockout_results.csv`.

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
match,winner
73,Netherlands
89,Spain
```
One row per completed KO match. Winner is the team's display name (as used in picks CSVs).

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

**Dev workflow flags** (remove before Jun 11/28):
- `USE_LOCAL_DATA = true` — uses embedded sim data; shows KO games played input
- `knockoutMode = true` — forces KO layout regardless of date (set to date expression for production)

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
- `KO_SCHEDULE` — match dates M73–M104
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
- Match results table: score + outcome pill
- Qualification status: blue (top 2), green (3rd qualified), yellow (3rd pending), red (eliminated)
- Progress bar in sticky bar: "GROUP STAGE" · fill bar · "X / 72 matches played" · last updated
- Collapsible sections
- **Live knockout bracket** (collapsible section at bottom) — see below

### Knockout bracket (leaderboard pages — Variant 1)
- 5-column horizontal layout: R32 → R16 → QF → SF → Final/3rd
- Shows **Provisional** badge (orange) while group stage is in progress; **Confirmed ✓** badge (green) once `knockout_bracket.json` has `"confirmed": true`
- `confirmed: true` is set by `parse_results.py` only when BOTH conditions are met: (1) all 72 group results present, AND (2) computed R32 bracket has been cross-checked against the Wikipedia knockout bracket page via MediaWiki API
- Leaderboard fetches `data/knockout_bracket.json` in `init()` alongside picks + results; falls back gracefully (stays Provisional) if the file doesn't exist yet (404)
- All **495/495** third-place combinations encoded in 3 files
- `test_bracket.py` — end-to-end test, all 495 combos verified passing
- Uses `bracket.js` for all rendering primitives; page only defines `slotTeams()` + `mkCard()` + calls `buildBracketHtml(mkCard, { podiumHtml })`

**Bracket design (all variants — updated May 20):**
- ESPN-style cards: flag (`.bk-fl`) + name+rank (`.bk-tn`) — flag rendered separately, not via `teamHtml()` (avoids double-flag)
- Match header bar: `[Round] · M# · Date` (e.g. `R32 · M74 · Jun 29`, `QF · M97 · Jul 9`)
- **Sticky round header strip** (`.bk-header-strip`) sits above `.bk-wrap`, auto-pins below `.sticky-bar` using measured height. `position: sticky` works because leaderboard `.section-body` uses `overflow: clip` (not `hidden`), which clips without creating a scroll container
- Round headers with blue intensity progression: lightest R32 → darkest Final; strip injected via `bracket.js` CSS tag
- Matches in Wikipedia bracket order: [74,77,73,75,83,84,81,82,76,78,79,80,86,88,85,87]
- R32 uses uniform 16px gap between all 16 matches
- R16/QF/SF/Final cards absolutely positioned by JS to align team-dividing line with midpoint of feeders
- SVG `]` bracket connectors drawn after positioning
- Final column label: `🏆 Final (and 3rd place)`
- Podium section (🥇/🥈/🥉) in Final column, top aligned with M89

### Knockout pick page (`WC2026_Pool_Knockout_Picks.html`) — Variant 2 ✅
- Fetches `knockout_bracket.json` on load; shows "not yet available" if file missing (pre-Jun 27)
- R32 teams populated from `bracketData.round_of_32`; R16+ slots cascade from user picks
- Click any team row to pick winner — both teams must be known before either row is clickable
- Winner cascades into the next round's slot; downstream picks cleared if they become invalid
- Picks state: `picks = { matchNum: winnerName }` — 32 picks total
- **No re-render on pick**: `updateCards()` replaces each `.bk-card` outerHTML in-place, preserving `style.top` on absolutely-positioned cards — eliminates flash/jitter
- Full `renderBracket()` only called once on initial load
- Podium updates live as Final and 3rd place picks are made
- Shortcuts: 🎲 Pick randomly · 💪 Pick higher-ranked · ✕ Reset — all use `updateCards()`
- Progress bar: `X / 32 matches picked`

### GitHub Actions
- `update.yml` — runs every 15 min, Jun 11–Jul 19
- `simulate.yml` — generates test picks + results
- `clear_simulation.yml` — wipes simulation data

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

## Bracket Design — Three Variants

Same ESPN-style card DNA across all three: flag emoji + team name + score, winner row highlighted blue, loser row muted, TBD rows in grey italic, round headers with blue intensity progression (lightest R32 → darkest Final).

### Variant 1 — Provisional bracket (leaderboard, group stage live)
**File:** embedded in `WC2026_Pool_Leaderboard_Swiftly.html` + FandF  
**When shown:** once all 12 groups have each played ≥1 match (Provisional badge), updated to Confirmed ✓ after all 72 group matches  
**Interaction:** read-only  
**States:**
- Confirmed 1st/2nd slots → real team name + flag
- Unconfirmed slots (3rd-place TBD, groups not finished) → greyed italic "3rd place TBD" or "1F TBD"
- Later rounds (R16, QF, etc.) → "W73"-style placeholders until knockout matches complete
- Match header bar: match number + date, no score column

### Variant 2 — Pick bracket (knockout picks page, after Jun 27)
**Files:** `WC2026_Pool_Knockout_Picks_Swiftly.html` + FandF (new pages, not yet built)  
**When shown:** after Jun 27 once all group games done and R32 bracket is confirmed  
**Interaction:** tap a team row to pick them as winner  
**States:**
- Picked team → blue highlight + ✓ checkmark, auto-populates into next round slot
- Unpicked teams in unlocked cards → normal, tappable
- Cards in future rounds where feeder picks not yet made → greyed out "Pick M__ first"
- Picks cascade round-by-round (R32 → R16 → QF → SF → Final)
- Submit / download flow (same pattern as group pick pages)

### Variant 3 — Results bracket (leaderboard, knockout in progress)
**File:** embedded in leaderboard pages (replaces/extends Variant 1 after Jun 28)  
**When shown:** as knockout matches complete (Jun 28 – Jul 19)  
**Interaction:** read-only  
**States:**
- Completed match → scores shown in .sc column; winner row blue + bold; loser row muted + flag faded
- Penalty shootout → small italic note below card ("Netherlands win 5–3 on pens")
- Confirmed upcoming matchup (teams known, match not played) → teams shown, no score, normal weight
- Future slot not yet determined → grey italic "TBD" or "Winner M73"
- Match header: "M73 · Jun 28 · FT" or "M74 · Jul 1 · upcoming"

---

## Still To Build

### Pre-tournament (before Jun 11)
- [x] ~~Iterate on visual design of knockout bracket~~ — ESPN-style design finalised
- [x] ~~Rebuild bracket with new design~~ — Variant 1 complete in both leaderboard pages
- [x] ~~Font size consistency~~ — `0.78rem` body / `0.68rem` headers across all 4 pages
- [x] ~~Pick form polish~~ — shortcuts, name field, progress bar, reset, qualification logic, flag emojis, header consistency
- [ ] **Remove `USE_LOCAL_DATA = true` and `knockoutMode = true` from both leaderboard pages** (set to date expression) before Jun 11
- [ ] Clear simulation data (`Actions → Clear simulation data`) before Jun 11
- [ ] Share pick page links with participants, collect CSVs
- [ ] Upload real participant CSVs to `picks/group/swiftly/` and `picks/group/fandf/`

### After Jun 27 (bracket confirmed — build before Jun 28)
- [x] ~~`bracket.js` shared template~~ — all rendering primitives extracted; both leaderboards updated
- [x] ~~Podium section~~ — `buildPodiumHtml()` in template, positioned at M89, updates live from picks
- [x] ~~Interactive bracket (Variant 2)~~ — `WC2026_Pool_Knockout_Picks.html` fully wired; click-to-pick, cascade, surgical update, shortcuts
- [x] ~~Wire CSV download + submission flow~~ — same pattern as group picks; downloads `wc26_knockout_[name].csv`
- [x] ~~Update `aggregate_picks.py`~~ — aggregates knockout CSVs → `data/knockout_swiftly_picks.json` + `data/knockout_fandf_picks.json`
- [x] ~~Single picks page~~ — one page for both pools (same as group picks); leaderboards are the only pool-specific pages
- [ ] Share knockout pick page link, collect and upload CSVs before Jun 28

### After Jun 28 (knockout results start)
- [x] ~~Build Variant 3 leaderboard~~ — **complete and merged to main**
  - Combined table: Group pts · KO pts · Total · Max pts · squares (group + KO, with dividers)
  - Cascading tournament scoring — eliminated teams score 0 in all downstream rounds
  - Group section flat in KO mode (no toggle); KO teaser below bracket in group mode
  - Variant 3 results bracket: ESPN cards fill progressively from `knockout_results.csv`
- [x] ~~**Extend `parse_results.py`** to fetch knockout scores~~ — complete; uses ESPN KO API (Jun 28–Jul 20) → `results/knockout_results.csv` (existing `update.yml` picks it up automatically)
- [ ] **Duplicate Variant 3 changes to `WC2026_Pool_Leaderboard_FandF.html`**

---

## Knockout Stage Design

### Two-stage pool structure
1. **Group stage** (before Jun 12): participants submit 72 picks. Points lock after Jun 27.
2. **Knockout stage** (Jun 27–28): participants submit 32 bracket picks. Points accumulate as rounds complete Jun 28 – Jul 19.
3. **Final leaderboard**: group pts + knockout pts, one combined ranking.

### Knockout pick page (Variant 2)

**File:** `WC2026_Pool_Knockout_Picks.html` — shared by both pools (same as group picks page pattern)

**Source data:** `data/knockout_bracket.json` (confirmed after all 72 group matches)

**UX — cascading bracket fill:**
- Shows the full confirmed bracket (all 32 matches)
- User clicks a team in R32 to pick them → that team auto-populates into the correct R16 slot
- User picks R16 winners → auto-populates QF slots
- User picks QF winners → auto-populates SF slots
- User picks SF winners → winners auto-populate Final, losers auto-populate 3rd place match
- User picks winner of Final AND winner of 3rd place match
- **32 picks total** — all must be filled before submission
- Same submission flow as group picks: CSV download → email to Ritesh → upload to `picks/knockout/swiftly/` or `picks/knockout/fandf/`

**CSV format (`wc26_knockout_john-smith.csv`):**
```
match,winner
73,Netherlands
74,Spain
75,France
...
103,Argentina
104,Brazil
```

### Scoring

Points per correct pick (Scheme A):

| Round | Matches | Pts per correct pick | Max pts |
|---|---|---|---|
| Group stage | 72 | 2 | 144 |
| Round of 32 | 16 | 4 | 64 |
| Round of 16 | 8 | 8 | 64 |
| Quarterfinals | 4 | 12 | 48 |
| Semifinals | 2 | 16 | 32 |
| 3rd place | 1 | 12 | 12 |
| Final | 1 | 24 | 24 |
| **Total** | **104** | | **388** |

**Scoring model (75% favourite wins, path-dependent):**
- A player who always picks the favourite expects ~12/16 correct in R32, ~4/8 in R16, ~2/4 in QF, ~1/2 in SF, and the Final/3rd are binary (0 or full points)
- Expected total for favourite-picking strategy: ~192–228 pts (50–59% of 388 max)

**A pick is correct if the team you picked to win that match actually won.** If a team you picked didn't reach a round (because they were eliminated earlier), all their remaining picks score 0.

### Data pipeline

```
ESPN API (dates=20260628-20260720)
  → parse_results.py → results/knockout_results.csv
picks/knockout/swiftly/*.csv → aggregate_picks.py → data/knockout_swiftly_picks.json
picks/knockout/fandf/*.csv  → aggregate_picks.py → data/knockout_fandf_picks.json
```

`update.yml` already runs every 15 min Jun 11–Jul 19 and commits `results/` and `data/` — no workflow changes needed.

### Tiebreaker

If two or more players finish with the same total points, tiebreakers are applied in order:

1. **Correct champion** — who correctly picked the winner of the Final (M104). Players who got the champion right win over those who didn't.
2. **Most matches correct** — total number of individual matches correctly picked across all 104 matches (72 group + 32 knockout). The player who predicted the most individual matches correctly wins.

- Both tiebreakers are derived automatically from picks vs results — no extra input required
- Leaderboard sort order: total pts (desc) → correct champion (desc) → total correct picks (desc) → name (alpha)

### Leaderboard update (Variant 3)

#### Page layout — two modes

**Group stage (before Jun 28):**
```
[GROUP STAGE] section          ← flat, no toggles
  └─ standings table
  └─ group tables + match results (side by side)
  └─ provisional bracket (Variant 1)
  └─ KO teaser card ("picks open Jun 27…")
```

**Knockout stage (Jun 28+):**
```
[KNOCKOUT STANDINGS] section   ← primary view; combined table
  └─ Rank · Name · Group pts · KO pts · Total · Max pts · squares (group + KO)
[KNOCKOUT BRACKET] section     ← Variant 3 live results bracket
── section divider ──
[GROUP STAGE] section          ← flat (no toggle); provisional bracket hidden
  └─ group-only standings (locked)
  └─ group tables + match results
```

**Section notes:**
- All sub-toggles removed — everything is flat with plain section labels
- No accordion anywhere in KO mode
- Provisional bracket hidden in KO mode (superseded by Variant 3 KO bracket above)

#### Mode detection
Date-gated:
```javascript
const knockoutMode = new Date() >= new Date('2026-06-28T00:00:00Z');
```
`knockoutMode` controls section visibility, accordion default state, and sort/scoring logic on page load.

#### New data sources (added to parallel fetch in `init()`)
- `data/knockout_{pool}_picks.json` — each participant's 32 KO picks
- `results/knockout_results.csv` — completed KO match results (`match,winner` format)

Both fetched with `.catch(() => null)` fallback. Page degrades gracefully if files missing.

#### Combined standings table (knockout mode)

Columns: **Rank · Name · Group pts · KO pts · Total pts · squares**

Sort order: Total pts ↓ → correct champion (M104) ↓ → total correct picks (group + KO) ↓ → name A-Z

Mini squares: 72 group squares + visual divider + 32 KO squares in the same row.
- Group squares: existing correct/wrong/pending colours
- KO squares: same colour scheme; pending (grey) until match is played
- Square sizing TBD once initial design is reviewed

No individual participant drill-down — points columns tell the story.

#### KO scoring

| Round | Matches | Pts per correct pick |
|---|---|---|
| Round of 32 | M73–88 | 4 |
| Round of 16 | M89–96 | 8 |
| Quarterfinals | M97–100 | 12 |
| Semifinals | M101–102 | 16 |
| 3rd place | M103 | 12 |
| Final | M104 | 24 |

**Cascading scoring:** if a team loses in round R, all downstream picks for that team in rounds R+1+ score 0 and are marked `cascaded` (red, italic strikethrough). This is enforced in `computeCombinedStandings()` via `eliminatedInRound` map + `cascadeThreshold(m)`. See Variant 3 section above for full logic.

#### Knockout bracket (Variant 3)

Same ESPN-style cards as Variant 1. `mkCard` reads from `koResults`:
- **Match played**: winner row `.w` (blue), loser row `.l` (muted), score shown
- **Not yet played**: both rows neutral; teams shown from bracket JSON or derived from prior results

Results fill in progressively round by round as `knockout_results.csv` grows.

#### Sticky bar (knockout mode)
Switches from `X / 72 group matches played` to `X / 32 knockout matches played`.

#### `parse_results.py` KO fetch ✅
Fetches knockout match results from ESPN API (`dates=20260628-20260720`). ESPN returns `competitor.winner = true` on the winning team — no score parsing needed. Results are resolved by walking the bracket topology in order (R32 → R16 → QF → SF → 3rd/Final), propagating actual team names through `W73`-style references in `knockout_bracket.json` as rounds complete. Writes `results/knockout_results.csv` (`match,winner` format, confirmed matches only). Existing `update.yml` already runs every 15 min — no workflow changes needed.

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

**Pick buttons (W1/Draw/W2):** Same as secondary. Selected state: `--swiftly-blue` bg, white text. Always include `overflow: hidden; text-overflow: ellipsis; min-width: 0` to prevent long team names expanding the row.

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

Both leaderboard pages have a `USE_LOCAL_DATA` flag near the top of the `<script>` block:
- `USE_LOCAL_DATA = true` → uses embedded simulation data (no network, works as `file://`)
- `USE_LOCAL_DATA = false` → fetches live data from GitHub (production default)

**Workflow:**
1. Set `USE_LOCAL_DATA = true` in `WC2026_Pool_Leaderboard_Swiftly.html`
2. Open file in Chrome directly (`file://` URL)
3. Edit CSS/JS in editor → save → ⌘R in browser (instant feedback, no push needed)
4. When done: set `USE_LOCAL_DATA = false`, copy changes to FandF file, push via GitHub Desktop

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
- **KO_SCHEDULE**: knockout match dates encoded in JS object for M73–M104. Times not yet available from FIFA.

---

## Notes

- GitHub Actions free tier: well within limits (date-gated, only runs Jun 11–Jul 19)
- ESPN API updates within ~5 min of match end; leaderboard reflects within ~15 min (next Actions run)
- Pick submission is download-only — Ritesh uploads CSVs manually to GitHub
- Every participant's picks exist as individual CSV in `picks/` — fully auditable
- Leaderboard URLs use exact filenames: `WC2026_Pool_Leaderboard_Swiftly.html` (not `WC2026_Leaderboard_Swiftly.html`)
