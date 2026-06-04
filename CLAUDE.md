# WC2026 Pool — Claude Context

Full design doc: `WC2026_Pool_Plan.md`

---

## Hard rules

**Never edit `WC2026_Pool_Leaderboard_FandF.html` directly.**
Always edit `WC2026_Pool_Leaderboard_Swiftly.html`, then run:
```
python3 make_fandf.py
```
The two files are identical except 3 lines (title, header, POOL_ID). POOL_NAME was removed as it was never referenced.

**Git pushes must be done from Mac** — the sandbox can't push via SSH:
```
cd ~/Documents/GitHub/wc26 && git add -A && git commit -m "..." && git push
```
If `index.lock` error: `rm ~/Documents/GitHub/wc26/.git/index.lock` first.

---

## Key files

| File | Role |
|---|---|
| `bracket.js` | Shared bracket primitives — loaded by all pages |
| `scoring.js` | MATCHES array (72 group games), KO topology, scoring functions |
| `sim_core.js` | Seeded PRNG + KO generators for Node sim/test scripts |
| `WC2026_Pool_Leaderboard_Swiftly.html` | Main leaderboard — edit this, never FandF |
| `WC2026_Pool_Leaderboard_FandF.html` | Auto-generated from Swiftly via `make_fandf.py` |
| `WC2026_Pool_Knockout_Picks.html` | KO picks entry page |
| `WC2026_Pool_Group_Picks.html` | Group stage picks entry page |
| `make_fandf.py` | Regenerates FandF from Swiftly (3 substitutions: title, header, POOL_ID) |
| `data/rankings.json` | **Canonical** FIFA rankings — single source of truth for all scripts |
| `WC2026_Intro.pptx` | Swiftly-branded intro deck (13 slides, incl. host cities map as slide 6) — share with pool participants before Jun 11 |
| `test_aggregate_picks.py` | Python unit tests for aggregate_picks.py: CSV parsing + filename extraction (28 tests) |
| `test_parse_results.py` | Python unit tests for parse_results.py (84 tests) |
| `test_e2e.js` | JS end-to-end: 10-user full-tournament + 105 invariant checks |
| `test_bracket.py` | Bracket + standings end-to-end (all 495 3rd-place combos) |
| `.github/workflows/ci.yml` | CI: runs all four test suites on every push/PR |

---

## UTC time storage + local-TZ display

All kick-off times are stored as UTC ISO 8601 and converted at render time. Never hardcode ET/EDT.

**Group games** — in `scoring.js` and pick/leaderboard pages:
```js
// MATCHES format: [num, group, dateStr, utcKickoff, home, away]
// dateStr = human-readable local date; utcKickoff = '2026-06-11T19:00:00Z'

const _tzAbbr = new Date().toLocaleTimeString('en-US', { timeZoneName: 'short' }).split(' ').pop();
// → 'EDT', 'PDT', 'BST' etc., computed once at page load

function localMatchTime(utcStr) {
  const dt = new Date(utcStr);
  const t = dt.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  return `${t}<span class="cell-tz"> ${_tzAbbr}</span>`;
}
```
- Column header: `Time (${_tzAbbr})`
- `.cell-tz { display: none }` on desktop; `display: inline` on mobile (`max-width: 640px`)

**KO games** — in `bracket.js`:
```js
// KO_SCHEDULE: { matchNum: '2026-06-28T19:00Z', ... } for M73–M104
// koDisplay(num) → 'Sat, Jun 28 · 3:00 PM' (day of week included, TZ abbreviation omitted)
// Used in matchCard() and all mobile card renderers
```

---

## Bracket

### JS primitives (`bracket.js`)

- Exports: `KO_SCHEDULE`, `koDisplay()`, `R16`, `QF`, `SF`, `R32_SLOTS`, `FLAGS`, `RANKINGS`, `roundLabel()`, `matchCard()`, `buildBracketHtml()`, `positionAndConnectBracket()`, `drawBracketConnectors()`
- Match numbers: R32=73–88, R16=89–96, QF=97–100, SF=101–102, 3rd=103, Final=104
- R32 display order follows Wikipedia bracket (not M73–M88 numeric): `[74,77,73,75,83,84,81,82,76,78,79,80,86,88,85,87]`
- `bkTeamRow` renders flag in `.bk-fl` and name+rank in `.bk-tn` separately — do NOT call `teamHtml()` inside bracket cards (double-flag bug)
- R16/QF/SF/Final cards are `position: absolute` inside `.bk-float` — absolutely positioned cards have no intrinsic width, so column sizing is driven by R32 content only
- `roundLabel(103)` returns `'3rd'` (not `'3rd Place'`)

### Desktop card styling

Applies to both `WC2026_Pool_Knockout_Picks.html` and `WC2026_Pool_Leaderboard_Swiftly.html`.

**Spacing:** Uniform 16px gap at all four hierarchy levels keeps R32 evenly distributed and R16/QF/SF/Final midpoints mathematically aligned:
```css
.bk-matches, .bk-half, .bk-quarter, .bk-pair { gap: 16px; }
```

**Team row (flush bordered pill):**
```css
.bk-team {
  padding: 5px 9px;     /* height-neutral: larger font offset by smaller padding */
  font-size: 0.92rem;
  font-weight: 400;
  margin: 0 4px;
  border-radius: 5px;
  border: 1.5px solid #cce8f4;
}
.bk-mnum + .bk-team { margin-top: 4px; }
.bk-team + .bk-team  { margin-top: 4px; }
.bk-team:last-child   { margin-bottom: 4px; }
```
No `border-top` divider — row separation comes from `margin-top` only.

**Match header:** `.bk-mnum` is `display: flex; justify-content: space-between` on the leaderboard (label in `.bk-mnum-label`, correctness pill right-aligned). Plain block on the KO picks page — no flex, no pill.

**States:**
| Class | Background | Border | Text |
|---|---|---|---|
| (default) | white | `#cce8f4` | `var(--neutral-darkest)`, weight 400 |
| `.w` (winner) | `var(--swiftly-blue)` solid | same | white, weight 700; rank + score at 75% opacity |
| `.l` (loser) | transparent | transparent | `var(--neutral-medium)`; flag 35% opacity |
| `:hover` (unset) | `var(--blue-lightest)` | `var(--swiftly-blue)` | — |
| `.w:hover` | `var(--swiftly-blue)` + `brightness(0.92)` | same | — |
| `.l:hover` | `var(--blue-lightest)` | `var(--swiftly-blue)` | restored to normal |

**Gotchas:**
- `.bk-team[data-match].w:hover` must re-assert `background: var(--swiftly-blue)` — the less-specific `:hover` rule otherwise wins and reverts the row to light blue
- `.team-rank` has its own `color: var(--neutral-dark)` rule; losers need explicit `.bk-team.l .team-rank { color: var(--neutral-medium); }` to override it
- Do NOT add `font-weight` to loser hover — font-weight changes cause text reflow even with `white-space: nowrap`
- `matchCard()` always puts `data-match="${num}"` on the outer `.bk-card` div. The click handler uses `closest('[data-match]')`, which will bubble up to `.bk-card` if the click lands outside a team row. `.bk-card` has no `data-team`, so `pickTeam` receives `undefined` — guard with `if (!team) return` at the top of `pickTeam`

### Mobile auto-advance (KO picks page only)

- `maybeAdvanceTab()` is called after every `pickTeam()` — not after shortcuts (which call `updateCards()` directly)
- Condition: `MOB_ROUNDS[roundIdx].matches.every(m => !!picks[m])` — all matches in the active tab are picked
- On match: shows a fixed centered toast (`position: fixed; top: 50%; left: 50%; transform: translate(-50%,-50%)`) counting down 3→2→1, then calls `switchBracketTab` + `scrollIntoView`
- Toast stores a `_cancel` function on the element — call `existing._cancel?.()` before removing if you need to abort in-flight countdown
- `ROUND_FULL_LABELS` maps tab ids (`r32`, `r16`, `qf`, `sf`, `3rd`, `fin`) to display strings

---

## Group picks page

- **Pick button padding (desktop):** `padding: 6px 8px` — middle ground between too tight (4px) and too tall (8px) across 72 rows
- **`SHORT_NAMES`** applies on **all screen sizes** (not just mobile). Provides shortened display names inside pick buttons to avoid overflow: `'Bosnia and Herzegovina' → 'Bosnia…'`, `'Czech Republic' → 'Czech…'`
- **JS content flash fix:** `.container` has `visibility: hidden` in CSS; set to `visible` synchronously after `buildForm()` + `renderPickGroupTables()` — page paints once with content already in place

---

## Page load flash fixes (all pages)

- **Google Fonts:** all pages use `display=block` (not `display=swap`) — prevents font-swap flash at the cost of a brief invisible-text period on first load. Do not revert to `display=swap`.
- **Group picks:** `visibility: hidden` on `.container`, revealed after sync JS build (see above)
- **Knockout picks:** `bracketContainer` has a static "Loading bracket…" placeholder in HTML — shown while async fetch is in flight
- **Leaderboard — header + sticky bar:** `visibility: hidden` in CSS; revealed by `document.fonts.ready.then(_revealChrome)`. A `setTimeout(_revealChrome, 3000)` fallback fires if fonts never load (e.g. offline).
- **Leaderboard — section labels + card bodies:** `.section-label` and `.section-body` have `visibility: hidden` in CSS; revealed by `_revealSections()` called at the end of `init()` (both success and error paths).
- **Leaderboard — static loading placeholders:** static `⏳ Loading…` text uses class `.state-msg--loading` which has `visibility: hidden`. When `init()` replaces card `innerHTML`, the new content renders normally. Error (`⚠️`) and empty (`📭`) states use plain `.state-msg` (visible).
- **`_updateTimestamp()`** — called inside `init()` after `_lastUpdated = new Date()`. Populates `#updatedAt` with "Updated HH:MM".

---

## Group match results table

- Column order: `#` · `Grp` · `Date` · `Time (TZ)` · `Result` · `Score`
- Mobile (`max-width: 680px`): Time column hidden; `#` and `Grp` also hidden
- Group picks CSS grid: `grid-template-columns: 30px 28px 88px 72px auto`; mobile breakpoint `max-width: 640px`

### Group table pre-tournament state

Group tables render immediately (before Jun 11). Before any matches in a group have played:
- Teams are shown in `GROUP_ORDER` (Wikipedia order), same as the group picks page
- No qualified/eliminated row highlighting — all rows unstyled
- All stats show 0

Once the first match in a group kicks off, `sortedStandings()` takes over and row highlighting activates.

### Group stage tiebreaker chain (FIFA official, source: Wikipedia)

Applied when two or more teams are level on points. Criteria in order:

- **a.** H2H points (among tied teams only)
- **b.** H2H goal difference (among tied teams only)
- **c.** H2H goals scored (among tied teams only)
- *(if still tied: re-apply a–c exclusively among the still-level subset)*
- **d.** Overall goal difference
- **e.** Overall goals scored
- **f.** Fair play score — yellow: −1, indirect red: −3, direct red: −4, yellow+direct red: −5 *(not implemented — no card data)*
- **g.** FIFA ranking (most recent) *(implemented)*
- **h.** Progressively older FIFA rankings *(not implemented — single ranking only)*

Two sorting functions implement this chain:

- **`sortedStandings(grp)`** — used by group tables in `renderGroupTables`. Full chain a–e, g implemented via pairwise sort. `h2hStats(teamA, teamB, grpMatches, results)` is a module-scope helper used here.
- **`computeGroupStandings(results)`** — used by the bracket display and 3rd-place ranking. Same chain. Uses the same `h2hStats` module-scope helper.

Both functions must stay in sync. The group picks page uses a simplified chain (no GD/GF since users don't pick scores) — this is intentional.

### Correctness pill

Shows `N/total` for completed matches. Locations: appended to `td-score` cell (group table, `margin-left: 8px` via `.td-score .cp-pill`); right-aligned in `.bk-mnum` header (KO desktop); inline in `.bk-mob-meta` (KO mobile). `bracket.js` is not modified — injected entirely in the leaderboard.

**Color classes** (% of participants correct):
- ≥ 67%: `.cp-hi` — `#d4f0fb` bg / `#00628a` text
- 33–66%: `.cp-mid` — `#fff0d0` bg / `#a05800` text
- < 33%: `.cp-lo` — `#fce0e7` bg / `#b3003d` text

---

## ESPN API

Results and time verification both use:
```
https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates=YYYYMMDD
```
No API key required. Returns events with UTC `date` field and team `displayName`.

ESPN name mapping (5 teams differ from internal names):
`Czechia→Czech Republic`, `Türkiye→Turkey`, `Bosnia-Herzegovina→Bosnia and Herzegovina`, `Congo DR→DR Congo`, `Curacao→Curaçao`

**Home/away ordering** — ESPN's `homeAway` field on each competitor matches our internal MATCHES ordering exactly for all 72 group games. `parse_group_results_espn()` handles the rare case where ESPN reverses home/away: it tries `MATCH_LOOKUP[(home, away)]` first, then falls back to `MATCH_LOOKUP[(away, home)]` and swaps scores. Same logic in `parse_ko_results_espn()`: if `espn_home != bracket_home`, scores are swapped so the CSV always stores scores from the bracket's home team's perspective.

**Unknown team detection** — `KNOWN_TEAMS = set(TEAM_CODES.values())` is defined in `parse_results.py`. `espn_team_name()` prints a warning if a resolved name is not in `KNOWN_TEAMS`, which surfaces any new ESPN name variants that need an `ESPN_TEAM_MAP` entry.

---

## Local dev / testing

```bash
# Generate sim data and serve
python .github/scripts/simulate.py --participants 10 --stage all [--seed N]
python .github/scripts/aggregate_picks.py
python -m http.server 8000
# open http://localhost:8000/WC2026_Pool_Leaderboard_Swiftly.html?games=88

# Run all tests (same commands CI uses)
python3 test_parse_results.py   # 84 Python unit tests
python3 test_aggregate_picks.py # 28 Python unit tests (aggregate_picks.py CSV parsing)
node test_e2e.js                # 105 JS invariant checks
python3 test_bracket.py         # bracket + standings (self-contained, no CSV needed)
```

**`--seed N`** — makes simulate.py output reproducible. Without it, results are random each run.

**URL params:**
- `?games=N` — simulate tournament at match N (0–72 group, 73–104 KO); e.g. `?games=88` = R32 complete
- `?ko=1` — force knockout mode without specifying a game count

## GitHub Actions workflows

| Workflow | Trigger | What it does |
|---|---|---|
| **Simulate picks and results** | Manual — set `participants` (default 5) and `stage` (group/knockout/all) | Installs `requests`, runs `simulate.py` + `aggregate_picks.py`, commits + pushes sim data |
| **Clear simulation data** | Manual | Deletes `*simulation*` pick CSVs, writes `{}` to all picks/bracket JSONs, clears both results CSVs, commits + pushes |
| **Auto-clear simulation data** | Automatic at 1pm ET Jun 11 + manual | Same as above — fires automatically 2hrs before first match |
| **CI** | Every push/PR | Runs all 4 test suites |
| **update** | Push to `picks/**` (always) · Every 15 min Jun 11–Jul 20 (schedule) · Manual | Push trigger: aggregates picks immediately. Schedule: aggregates picks + fetches ESPN results. |

**To simulate N users for github.io testing:**
GitHub → Actions → "Simulate picks and results" → Run workflow → participants=N, stage=all

**To clear simulation data:**
GitHub → Actions → "Clear simulation data" → Run workflow
- Only deletes files matching `*simulation*` — real picks are never touched
- Clears both `group_results.csv` and `knockout_results.csv`
- Also fires automatically at 1pm ET on June 11
- No CDN purge needed — leaderboard uses `raw.githubusercontent.com` directly

## Leaderboard data fetching

All data files are fetched from `raw.githubusercontent.com` with `cache: 'no-store'` and a `?t=${Date.now()}` cache-buster appended inside `init()` on every call — bypasses both browser cache and the Fastly CDN (which caches raw.githubusercontent.com responses for 5 minutes). No cache purging ever needed.

```js
const _RAW = 'https://raw.githubusercontent.com/riteshwarade/wc26/main';
const PICKS_URL      = `${_RAW}/data/group_${POOL_ID}_picks.json`;
const RESULTS_URL    = `${_RAW}/results/group_results.csv`;
const BRACKET_URL    = `${_RAW}/data/knockout_bracket.json`;
const KO_PICKS_URL   = `${_RAW}/data/knockout_${POOL_ID}_picks.json`;
const KO_RESULTS_URL = `${_RAW}/results/knockout_results.csv`;
```

**Git push conflicts** — GitHub Actions workflows commit to main, which causes local push rejections. Fix:
```bash
git pull --rebase && git push
```
Set once to avoid the prompt: `git config --global pull.rebase true`

---

## Canonical data sources

Each piece of shared data has exactly one canonical source. All other copies must stay in sync:

| Data | Canonical source | Copies (must match) |
|---|---|---|
| FIFA rankings | `data/rankings.json` | `bracket.js` `const RANKINGS` (comment points here); `parse_results.py` loads from JSON |
| KO bracket topology (R16/QF/SF) | `bracket.js` `R16`/`QF`/`SF` | `scoring.js` `_R16`/`_QF`/`_SF` (+ runtime assertion); `sim_core.js` `R16`/`QF`/`SF`; `simulate.py` `R16_FEEDS` etc. |
| Group match list | `parse_results.py` `GROUP_MATCHES` | `simulate.py` and `aggregate_picks.py` import it; `test_bracket.py` imports it |
| ESPN name mapping | `parse_results.py` `ESPN_TEAM_MAP` | `CLAUDE.md` table above |

**Rankings update process:** edit `data/rankings.json` first, then update `bracket.js` `const RANKINGS` to match.

**Topology update process:** edit `bracket.js` `R16`/`QF`/`SF` first, then mirror changes to `scoring.js`, `sim_core.js`, and `simulate.py`. The `scoring.js` runtime assertion (`_assertEq`) will log a `console.error` in the browser if the copies drift.

## Pick status values

Group `pickResults[num].status`: `correct` · `wrong` · `pending` (result not yet in) · `empty` (no pick made)

KO `koPickResults[num].status`: same four + `cascaded` (team already eliminated, pick voids)
