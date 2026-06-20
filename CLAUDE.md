# WC2026 Pool — Claude Context

Full design doc: `WC2026_Pool_Plan.md`

---

## Pick submission timeline

- **Group picks** — submitted before the tournament starts (deadline: first group match, Jun 11)
- **KO picks** — submitted *after* the final group stage game; deadline is **before the first R32 game (M73, Jun 28 at 3:00 PM ET / 19:00 UTC)**. Nobody will have KO picks until late June — this is expected and correct.

---

## Hard rules

**After every design or technical change, update docs:**
- `CLAUDE.md` — update the relevant section (architecture, behavior, CSS rules, known gotchas, etc.)
- `WC2026_Pool_Plan.md` — prepend a row to the Changelog table with today's date and a concise summary of what changed and why

Do this at the end of every session where code, behavior, or architecture changed. Don't wait to be asked.

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
| `live_scores_test_plan.md` | Manual test plan for live scores + pulsing feature (phases 1–4 + console sim) |

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
- `.cell-tz { display: none }` always — the entire `.td-time` column is already hidden on mobile (`max-width: 640px`), so `.cell-tz` is never visible at any screen size

**KO games** — in `bracket.js`:
```js
// KO_SCHEDULE: { matchNum: '2026-06-28T19:00Z', ... } for M73–M104
// koDisplay(num) → 'Sat, Jun 28 · 3:00 PM' (day of week included, TZ abbreviation omitted)
// Used in matchCard() and all mobile card renderers
```

---

## Bracket

Three bracket variants — all share `bracket.js` primitives, each supplies its own `mkCard()`:
- **Variant 1** — Provisional bracket. Embedded in both leaderboard pages. Read-only; derived from group results. Shows Provisional (orange) / Confirmed ✓ (green) badge. `renderBracket()`.
- **Variant 2** — Pick bracket. `WC2026_Pool_Knockout_Picks.html`. Interactive; users click to pick winners. Uses `data-match`/`data-team` attrs via `bkTeamRow`'s `extraAttrs` param.
- **Variant 3** — Results bracket. Leaderboard, KO stage. Same cards as Variant 1 but `mkCard` reads `koResults`: winner solid blue, loser muted, scores + penalty rendering, correctness pill in `.bk-mnum`. `renderKoBracket()`.

### JS primitives (`bracket.js`)

- Exports: `KO_SCHEDULE`, `koDisplay()`, `R16`, `QF`, `SF`, `R32_SLOTS`, `FLAGS`, `RANKINGS`, `roundLabel()`, `matchCard()`, `buildBracketHtml()`, `positionAndConnectBracket()`, `drawBracketConnectors()`
- Match numbers: R32=73–88, R16=89–96, QF=97–100, SF=101–102, 3rd=103, Final=104
- R32 display order follows Wikipedia bracket (not M73–M88 numeric): `[74,77,73,75,83,84,81,82,76,78,79,80,86,88,85,87]`
- `bkTeamRow` renders flag in `.bk-fl` and name+rank in `.bk-tn` separately — do NOT call `teamHtml()` inside bracket cards (double-flag bug)
- R16/QF/SF/Final cards are `position: absolute` inside `.bk-float` — absolutely positioned cards have no intrinsic width, so column sizing is driven by R32 content only
- `roundLabel(103)` returns `'3rd'` (not `'3rd Place'`)

### Bracket display condition (leaderboard)

The bracket section shows "Bracket appears once every team has played." until `allTeamsPlayed` is true. This requires all 24 matchday-1 results to be in the CSV (M1–M24 = 2 matches per group × 12 groups). The check:
```js
const allTeamsPlayed = Array.from({length: 24}, (_, i) => i + 1).every(m => _lastResults[m]);
renderBracket(_lastResults, allTeamsPlayed, bracketConfirmed);
```
M24 (Uzbekistan vs Colombia, Group K) is the last matchday-1 game chronologically — Jun 18 02:00 UTC. Once it completes and the pipeline picks it up, the bracket unlocks.

`bracketConfirmed` is set by `parse_results.py` after all 72 group matches complete and it cross-checks the R32 against Wikipedia. Until then the badge reads "Provisional".

### Desktop card styling

Applies to both `WC2026_Pool_Knockout_Picks.html` and `WC2026_Pool_Leaderboard_Swiftly.html`.

**Spacing:** Uniform 16px gap at all four hierarchy levels keeps R32 evenly distributed and R16/QF/SF/Final midpoints mathematically aligned:
```css
.bk-matches, .bk-half, .bk-quarter, .bk-pair { gap: 16px; }
```

**Card container:** `.bk-card` is a transparent structural container — no background, border, or border-radius. All visual chrome lives on `.bk-team` rows only. `.bk-mnum` is also transparent (no background).

**Team row (flush bordered pill):**
```css
.bk-team {
  padding: 5px 9px;     /* height-neutral: larger font offset by smaller padding */
  font-size: 0.92rem;
  font-weight: 400;
  margin: 0 4px;
  border-radius: 5px;
  border: 1.5px solid #cce8f4;
  background: #ffffff;  /* white bg on team rows only, not the card container */
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

## Group table team name truncation (leaderboard)

`_GRP_SHORT_NAMES` in `WC2026_Pool_Leaderboard_Swiftly.html` mirrors the picks page `SHORT_NAMES`. Applied in `renderGroupTableCard` via the optional `display` parameter added to `teamHtml()` in `bracket.js`. Needed because `.side-left` is a fixed `380px` on iPad portrait, leaving only ~120px for the team name cell after stat columns. Entries: `'Bosnia and Herzegovina' → 'Bosnia…'`, `'Czech Republic' → 'Czech…'`.
- **JS content flash fix:** `.container` has `visibility: hidden` in CSS; set to `visible` synchronously after `buildForm()` + `renderPickGroupTables()` — page paints once with content already in place

---

## Mobile recent-squares column (leaderboard)

A `.td-mob-sq` / `.th-mob-sq` column is hidden on desktop and revealed at `max-width: 640px`. Shows the **last 5 squares** for the current stage only — no carryover between group and KO.

- **Group mode** (`renderStandings`): last 5 of played/live group matches **by kickoff time** (not match number — match numbers are not chronological). `_MATCHES_CHRONO` is a module-level constant: `[...MATCHES].sort((a,b) => a[3] < b[3] ? -1 : a[3] > b[3] ? 1 : a[0]-b[0])`. `mobMatchNums` filters `_MATCHES_CHRONO` to entries in `_lastResults` or `liveData`, then takes the last 5. Tiebreaker for simultaneous kickoffs: match number. `MOB_LAST = 5`. Squares are also **displayed** in chronological order: built in a `sqByNum` map during the main loop, then assembled via `_MATCHES_CHRONO.filter(...mobMatchNums...)` after.
- **KO mode** (`renderKoStandings`): last 5 of `KO_MATCH_ORDER` **by kickoff time** (same issue — KO match numbers are also not chronological). `koChronoOrder` sorts `KO_MATCH_ORDER` by `KO_SCHEDULE[m]` with match-number tiebreaker, computed inside `renderKoStandings`. `KO_MOB_LAST = 5`. No live override yet (KO live scores not built). Squares assembled from `koSqByNum` map in `koChronoOrder` order.
- Column header: `Recent`. Tooltip data attributes are present on every mob square — existing tooltip handler works automatically.

---

## Live scores (leaderboard — group stage)

> **Built.** Group stage only; KO live scores planned for later.

**Toggle:** `const LIVE_SCORES_ENABLED = true/false` at the top of the leaderboard JS. Off = no ESPN fetch, no live UI. This is an internal dev toggle, not a URL param.

**Data:** Client-side ESPN fetch (`https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates=YYYYMMDD`). Polls every ~60s while any match is in-progress (`status.type.state === 'in'`). Stops polling when all today's matches are `post`. Uses existing ESPN name mapping (`ESPN_TEAM_MAP`). **ESPN indexes matches by ET date, not UTC** — fetches yesterday + today UTC to catch late ET games (e.g. 10 PM ET = 2 AM UTC next day).

**Pick statuses (new):** `live-correct` and `live-wrong` — evaluated against current live score, same logic as `correct`/`wrong` but applied only while game is in progress. No `live-draw` — the current score implies exactly one of W1/Draw/W2; the pick either matches or doesn't. Squares pulse (opacity 1→0.3→1, 1.8s) in their full colors (blue for live-correct, red for live-wrong) — same animation as the results table time/score cells. Once final, squares snap to solid.

**Results table:** For in-progress matches (`state: 'in'`), the time cell shows the current minute (e.g. `67′`) and the score cell shows the live score — both pulsing (opacity 1→0.3→1, 1.8s) in default text color. During the bridge period (`state: 'post'`, CSV unconfirmed), the score and `FT` also pulse — same animation — so the results table stays consistent with the pulsing squares. `isBridge = lm.state === 'post'`; `pulse()` applies to both `isLive` and `isBridge`. Scheduled rows unchanged. Final rows (CSV confirmed) show `FT` + solid score. The Correct column also pulses during live and bridge; its count is computed on the fly from `_lastStandings` + current live score (not from `grpCounts`, which only tracks finalized `correct`/`wrong` statuses).

**Standings:** Points, rank, and all aggregate numbers stay frozen during live. Only squares change color. (May extend to preview standings in future.)

**Scope:** Group stage only for now. KO live scores to be added later — same architecture applies.

**Diagnostics (DevTools console):**
```js
document.querySelectorAll('.sq-live-correct, .sq-live-wrong').length  // should be > 0 while game is live
_liveData[matchNum]       // { homeScore, awayScore, state, minute }
_lastResults?.[matchNum]  // undefined = CSV not updated yet
_bridgeScores[matchNum]   // { homeScore, awayScore } — persists after ESPN drops event
_pendingResults.size      // > 0 = waiting for CSV confirmation
_livePoller               // null = stopped; number = interval ID (running)
renderStandings(_lastStandings, _liveData);  // force re-render if squares look wrong
```

**`_pendingResults` seeding — two paths:**
- **Score-based (primary):** if `_bridgeScores[mNum]` is set (we saw ESPN live data) and CSV hasn't confirmed, add to `_pendingResults` immediately on every `fetchLiveScores` call. Handles ESPN dropping the event without a `post` state transition (`in` → gone).
- **Time-based (page-reload fallback):** if elapsed > 95 min from kickoff and < 24 h, add to `_pendingResults`. Covers page reloads after ESPN has already dropped the event and `_bridgeScores` is empty. 95 min covers 90 min + normal stoppage; 24 h cap prevents indefinite polling.

**Known behavior (fixed):** Previously, `stopLivePolling()` was called immediately when a game ended, creating a gap before the bridge restarted polling. Fixed: during the bridge period (`_pendingResults.size > 0`), the polling interval is never stopped — it keeps running and `init()` is called each cycle to re-check the CSV. Polling only stops when `_pendingResults` is empty (all results CSV-confirmed). See `live_scores_test_plan.md` for the full manual test checklist.

**Stale-CSV regression fix:** After the bridge resolves, the 5-minute `setInterval` can call `init()` and Fastly CDN (up to 5-min cache on raw.githubusercontent.com) may serve a stale CSV that does NOT contain the just-confirmed result. Before this fix, `_lastResults` and `_lastStandings` would be overwritten with the stale data — squares stay solid (correct) but points revert to old values. Fix (in `init()`): guard the `_lastResults`/`_lastStandings`/`_lastGrpCounts` update with a regression check:
```js
const _newMatchCount = Object.keys(results).length;
const _oldMatchCount = _lastResults ? Object.keys(_lastResults).length : -1;
if (_newMatchCount >= _oldMatchCount) {
  _lastStandings = standings; _lastResults = results; _lastGrpCounts = grpCounts;
}
renderStandings(_lastStandings, _liveData);
```
All downstream renders (`renderResults`, `renderGroupTables`, `renderBracket`) and the sticky bar `played` count use `_lastResults`/`_lastGrpCounts` instead of local `results`/`grpCounts`, so match count and points always move in lockstep.

**Bridge-period flash fix:** During the bridge, `fetchLiveScores` calls `init()` (to re-check the CSV), and `init()` was calling `fetchLiveScores()` again unconditionally — creating a rapid loop (~200–500ms per iteration) that re-rendered `renderBracket` on each pass, causing the bracket to flash between positioned and unpositioned states every ~1s. Two fixes: (1) `renderGroupTables` and `renderBracket` in `init()` are now gated on `freshData || bracketChanged` — `freshData = currentMatchCount > _lastRenderedMatchCount` (only true when the CSV gains a confirmed result); `bracketChanged = bracketConfirmed !== _lastBracketConfirmed` (only true when Provisional flips to Confirmed). Tracked by module-scope `_lastRenderedMatchCount` (init: -1) and `_lastBracketConfirmed` (init: `undefined`). (2) The inner `fetchLiveScores()` call in `init()` is guarded with `&& !_livePoller` — only fires on initial page load before the 60s interval is started.

**`#provisional_bracket` deep link:** `_revealSections()` calls `bracketSectionLabel.scrollIntoView({ behavior: 'smooth' })` when `window.location.hash === '#provisional_bracket'`. Shareable URLs: `WC2026_Pool_Leaderboard_Swiftly.html#provisional_bracket` and `WC2026_Pool_Leaderboard_FandF.html#provisional_bracket`.

**TODO before KO stage (Jun 28):**
- **KO upset detection** — wire `_isUpsetResult` into `renderKoStandings` the same way group stage does it in `renderStandings`. CSS + tooltip already exist. ~5 lines.
- **KO live scores** — extend group stage ESPN polling to KO matches. Architecture is identical. See KO bracket live treatment spec below.

**KO bracket live treatment (planned):** During a live KO match, both team rows in the bracket card pulse (1→0.3→1, 1.8s). Currently winning team: pulsing solid blue (same as final winner style). Currently losing team: pulsing muted/transparent (same as final loser style). Minute shown pulsing in `.bk-mnum` alongside the match number. On FT, both rows snap to solid winner/loser state.

---

## Mobile breakpoints (leaderboard)

Two media queries govern mobile layout:

- **Portrait** — `@media (max-width: 640px)`: stacks group tables/results, hides squares + max-pts columns, hides date/time/# in results table, shows mobile bracket tabs. Also reveals `.th-mob-sq` / `.td-mob-sq` — the last-5 recent squares column (see below).
- **Landscape** — `@media (max-width: 896px) and (orientation: landscape)`: stacks group tables/results (same order as portrait); standings card is `overflow-x: auto` (horizontally scrollable); bracket switches to tab view (`.bk-outer` hidden, `.bk-mobile-tabs` shown — same as portrait). Landscape phones (~667–896px wide) miss the 640px portrait breakpoint entirely, hence the separate query. The KO Picks page has its own landscape block with just the bracket rules (no layout stacking needed there).

---

## Page load flash fixes (all pages)

- **Google Fonts:** all pages use `display=block` (not `display=swap`) — prevents font-swap flash at the cost of a brief invisible-text period on first load. Do not revert to `display=swap`.
- **Group picks:** `visibility: hidden` on `.container`, revealed after sync JS build (see above)
- **Knockout picks:** `bracketContainer` has a static "Loading bracket…" placeholder in HTML — shown while async fetch is in flight
- **Leaderboard — header + sticky bar:** `visibility: hidden` in CSS; revealed by `document.fonts.ready.then(_revealChrome)`. A `setTimeout(_revealChrome, 3000)` fallback fires if fonts never load (e.g. offline).
- **Leaderboard — section labels + card bodies:** `.section-label` and `.section-body` have `visibility: hidden` in CSS; revealed by `_revealSections()` called at the end of `init()` (both success and error paths). **Exception: `#bracket-body` is excluded from the generic `_revealSections` sweep** — it is revealed inside `positionAndConnectBracket`'s rAF callback (after absolute cards are positioned), preventing a 2-frame flash where R16/QF/SF/Final cards appear at `top:0` before being placed. The early-return path in `renderBracket` (pre-tournament) reveals it immediately since no positioning is needed.
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

**Third-place qualification highlighting** only activates once ALL 12 groups are fully played (`isGroupDone` for every group). This gate uses `isGroupDone` (all 6 matches played), not `isGroupStarted`. `thirdPlaceTeams` also filters out groups where the 3rd-place team has `P === 0` to prevent ghost entries from corrupting the cross-group ranking.

**Group table legend** (rendered below the grid in `renderGroupTables`): solid-color 11px squares, no border. Colors: Swiftly Blue (qualified top 2), `#22863a` green (3rd qualified), `#ff9e16` amber (3rd pending), `#e24b4a` red (eliminated). Padding: `8px 12px 10px` to keep squares off the card edge.

### Group stage tiebreaker chain (FIFA official, source: Wikipedia)

Applied when two or more teams are level on points. Criteria in order:

- **a.** H2H points (among tied teams only)
- **b.** H2H goal difference (among tied teams only)
- **c.** H2H goals scored (among tied teams only)
- *(if still tied: re-apply a–c exclusively among the still-level subset)*
- **d.** Overall goal difference
- **e.** Overall goals scored
- **f.** Fair play score — yellow: −1, indirect red: −3, direct red: −4, yellow+direct red: −5 *(implemented; YDR treated as IR since ESPN data can't distinguish — see below)*
- **g.** FIFA ranking (most recent) *(implemented)*
- **h.** Progressively older FIFA rankings *(not implemented — single ranking only)*

**Card data pipeline:** `parse_results.py` → `parse_card_data(events)` → `results/group_cards.json`. Format: `{"1": {"Mexico": {"Y":1,"IR":0,"DR":0}, ...}, ...}`. Fetched in `init()` as `CARDS_URL` → `_cardData` global. Graceful degradation: if fetch fails, `_cardData = null` and fair play returns 0 (falls through to FIFA ranking).

**Regression guard in `__main__`:** Before writing the CSV, the existing `group_results.csv` is loaded. If ESPN returns fewer matches than are already on disk (e.g. on days with no group-stage games), the new results are merged into the existing ones rather than overwriting. ESPN wins for any match it does return; existing data is preserved for all others. This prevents a day-between-matchdays ESPN gap from clearing confirmed results.

`parse_card_data` runs **before** `write_bracket_json` in `__main__` so the provisional bracket also applies fair play to the thirds ranking. `write_bracket_json(results, cards)` receives the card dict and passes it to `_fair_play_score_py(team, grp, cards)` in the thirds sort key. `cards=None` is accepted gracefully (fair play = 0).

`compute_group_standings(results, cards=None)` also accepts cards and applies `_fair_play_score_py` in the within-group sort key (between GF and FIFA ranking). This corrects cases where teams are tied through overall GD/GF but differ on cards — e.g. Netherlands 3 yellows vs Japan 0 cards in Group F, making Japan 2nd. H2H (criteria a–c) is still omitted from Python; Wikipedia cross-check is the final arbiter for confirmed status.

**ESPN card classification per athlete per match:** yellow only → Y (−1); red with prior yellow → IR (−3, second yellow); red with no prior yellow → DR (−4). True YDR (yellow + direct red, −5) is indistinguishable from second yellow in ESPN data — classified as IR (−3), which underestimates the deduction. Coaches/officials without `athletesInvolved` are counted at team level; coach reds are DR.

**Sorting implementation:** All group-ranking sort logic is centralized in module-scope `groupSort(teams, stats, grpMatches, results, cardData)`. It replaces the old pairwise comparator in both places:

- **`sortedStandings(grp)`** — inner function in `renderGroupTables`. Now one line: calls `groupSort(order, stats, grpMatches, results, _cardData)`.
- **`computeGroupStandings(results, cardData)`** — bracket display and 3rd-place ranking. Calls `groupSort` per group; thirds sort adds `fairPlayScore` between GF and FIFA ranking.

**`groupSort` algorithm:**
1. Partition teams by points (descending)
2. For each pts-tied group: `_applyH2HTiebreak(group, ...)`
   - First pass: H2H Pts → H2H GD → H2H GF among the full tied group (`_h2hMiniStats`)
   - Identify segments still tied after first pass
   - Second pass (per segment): re-compute H2H among the smaller subset; if still tied, fall through to d (overall GD) → e (overall GF) → f (`fairPlayScore`) → g (FIFA ranking)

**Removed:** `h2hStats(teamA, teamB, ...)` module-scope helper — replaced by `_h2hMiniStats(team, allTeams, ...)` which computes mini-tournament stats for one team among a set.

Both `sortedStandings` and `computeGroupStandings` must stay in sync by always calling `groupSort`. The group picks page uses a simplified chain (no GD/GF since users don't pick scores) — this is intentional.

### Correctness pill

Shows `N/total` for completed matches. Locations: in its own `td-correct` column in the group results table; right-aligned in `.bk-mnum` header (KO desktop); inline in `.bk-mob-meta` (KO mobile). `bracket.js` is not modified — injected entirely in the leaderboard.

**Color classes** (% of participants correct):
- ≥ 67%: `.cp-hi` — `#d4f0fb` bg / `#00628a` text
- 33–66%: `.cp-mid` — `#fff0d0` bg / `#a05800` text
- < 33%: `.cp-lo` — `#fce0e7` bg / `#b3003d` text

**Pill tooltip:** Hovering a `.cp-pill` shows the shared `#sq-tooltip` with "Picked correctly:" header and a `✓ Name` line per correct picker (or "— nobody" if zero). Pill carries `data-cp-names` (pipe-delimited abbreviated names). `buildGrpCounts` and `buildKoCounts` both store `names: []` alongside `correct`/`total`. The live correctness block in `renderResults` also collects `liveNames`. `.cp-pill` has `cursor: help`.

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
| **update** | Push to `picks/**` (always) · Every 10 min Jun 11–Jul 20 (schedule, fallback) · Manual | Push trigger: aggregates picks immediately. Schedule: aggregates picks + fetches ESPN results. Primary trigger is cron-job.org every 5 min (see below). |

**To simulate N users for github.io testing:**
GitHub → Actions → "Simulate picks and results" → Run workflow → participants=N, stage=all

**To clear simulation data:**
GitHub → Actions → "Clear simulation data" → Run workflow
- Only deletes files matching `*simulation*` — real picks are never touched
- Clears both `group_results.csv` and `knockout_results.csv`
- Also fires automatically at 1pm ET on June 11
- No CDN purge needed — leaderboard uses `raw.githubusercontent.com` directly

## Participant name format

Names are stored as keys in the picks JSON and displayed on the leaderboard. Format: **"First L"** — first name(s) in full, last name abbreviated to initial (no period). Abbreviation is UI-only via `_abbrevName(name)` in the leaderboard JS — full names are stored in the picks JSON. Examples: stored as `Cole Mccarren`, displayed as `Cole M`. Numeric suffixes are not abbreviated (`Simulation 1` stays as-is). This sidesteps `.title()` mangling (McCarren → Mccarren) since the mangled last name is never visible.

---

## Leaderboard data fetching

All data files are fetched from `raw.githubusercontent.com` with `cache: 'no-store'` and a `?t=${Date.now()}` cache-buster appended inside `init()` on every call — bypasses browser cache. Note: Fastly CDN (which serves raw.githubusercontent.com) ignores query parameters and caches responses for 5 minutes (`max-age=300`), so there is an independent up-to-5-minute lag between a GitHub push and the leaderboard reflecting it. No cache purging is possible or needed — just wait up to 5 minutes.

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

**GitHub Actions schedule reliability** — GitHub throttles high-frequency cron jobs on low-traffic repos. The 5-min schedule may silently skip runs. Fix: **cron-job.org** externally triggers the workflow via `workflow_dispatch` every 5 min — this is live and running. The GitHub native cron is set to 10 min as a fallback only.

**Bracket write guard** — `write_bracket_json` only writes `data/knockout_bracket.json` when the substantive content changes. It compares the new bracket against the existing file (ignoring `generated_at`); if identical, skips the write entirely. This prevents a spurious commit every 5 minutes when no results have changed.

Setup (already done):
- GitHub PAT `wc26-cron-trigger` with `Actions: write` on `wc26` repo — **expires 2026-08-11**, regenerate before then
- cron-job.org job `wc26-update` POSTs every 5 min to:
  ```
  https://api.github.com/repos/riteshwarade/wc26/actions/workflows/update.yml/dispatches
  ```
  with headers `Authorization: Bearer <PAT>`, `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28` and body `{"ref":"main"}`

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

Group `pickResults[num].status`: `correct` · `correct-upset` · `wrong` · `pending` (result not yet in) · `empty` (no pick made)

**`empty` behavior:** `.sq-empty` renders as a faint outlined square (transparent fill, `1px solid var(--neutral-light)`). Tooltip hides the pick line and shows "— No pick". `pickResults[num].result` is populated even for empty picks (so the tooltip shows the actual score if the game was played). To make a participant a late joiner, blank their pick in the CSV for already-played matches — `aggregate_picks.py` skips empty pick fields, leaving the key absent from the JSON, which `computeStandings` treats as `empty`.

KO `koPickResults[num].status`: same five + `cascaded` (team already eliminated, pick voids)

### Upset detection (`correct-upset`)

A pick is promoted from `correct` to `correct-upset` when the winning team had a worse FIFA ranking (higher rank number) than the loser.

```js
function _isUpsetResult(t1, t2, outcome) {
  if (!outcome || outcome === 'Draw') return false;
  const r1 = RANKINGS[t1] || 999, r2 = RANKINGS[t2] || 999;
  if (r1 === r2) return false;
  const favWon = r1 < r2 ? outcome === 'W1' : outcome === 'W2';
  return !favWon;
}
```

`sqStatus` in the square builder:
```js
const sqStatus = pr.status === 'correct' && _isUpsetResult(t1, t2, pr.result?.outcome)
  ? 'correct-upset' : pr.status;
```

**Visual:** `.sq-correct-upset` — same Swiftly Blue background as `.sq-correct`, with a white ✦ (U+2726, 4-pointed star) via `::after` pseudo-element at 6px font-size (5px for `.sq-sm`).

**Tooltip:** `'✓ Correct ✦ Upset'` — uses `.correct` CSS class for the status line color (same green as a normal correct pick).

---

## Post-tournament / WC2030 cleanup

Once WC2026 ends, do these before reusing the codebase for 2030:

**Before building anything: plan first, then recheck the plan.** Each item below touches more files than it appears to — grep for all consumers before writing a line of code.

- **Extract `data/group_matches.json`** — move the hardcoded match arrays out of `scoring.js`, `WC2026_Pool_Group_Picks.html` (inline), and `parse_results.py` (`GROUP_MATCHES`) into a single `data/group_matches.json`. Schema: `[{ "num", "group", "dateStr", "utcKickoff", "home", "away" }, ...]`. Not done in 2026 because group matches are static mid-tournament and the async-fetch complexity wasn't worth it. In 2030 it's the right starting point.
  - `scoring.js`: Node loads via `fs.readFileSync`; browser gets `initMatches(data)` called from each page's async init
  - `WC2026_Pool_Group_Picks.html`: remove inline MATCHES, add `<script src="scoring.js">`, make `buildForm()` async
  - `parse_results.py`: derive `GROUP_MATCHES` from the JSON — `aggregate_picks.py`, `simulate.py`, `test_bracket.py`, `test_parse_results.py` import from `parse_results` and need no changes

- **Convert results files from CSV to JSON, with match info included** — `results/group_results.csv` and `results/knockout_results.csv` should become `results/group_results.json` and `results/knockout_results.json`. Current CSVs are opaque (match number + scores only); JSON should be self-documenting like the picks CSVs. Schemas:
  - Group: `{ "1": { "group": "A", "home": "Mexico", "away": "South Africa", "home_score": 2, "away_score": 0, "outcome": "W1" }, ... }`
  - KO: `{ "73": { "home": "Mexico", "away": "Canada", "home_score": 2, "away_score": 1, "winner": "Mexico", "decided_by": "FT" }, ... }` — `decided_by` is `"FT"`, `"ET"`, or `"Pens"`; penalty games also include `"home_pen"` and `"away_pen"` (e.g. `"home_score": 1, "away_score": 1, "home_pen": 5, "away_pen": 4, "decided_by": "Pens"`)
  - Current KO CSV is fragile: `write_ko_results_csv` writes 2, 4, or 6 columns depending on whether scores/penalties exist, forcing two separate parse functions (`parseKoResults` + `parseKoScores`) reading the same file. JSON collapses these to one `JSON.parse()` call.
  - `decided_by` is currently tracked nowhere — `parse_results.py` correctly parses penalty scores but never records how the game was decided. A regular 2–1 and a 2–1 AET are indistinguishable in the current data. The `decided_by` field fixes this.
  - `parse_results.py`: replace `write_csv()` + `write_ko_results_csv()` with JSON equivalents; team names + group looked up from `GROUP_MATCHES`/`MATCH_LOOKUP` (already available)
  - `simulate.py`: same — write JSON instead of CSV
  - `scoring.js`: delete `parseResults()` + `parseKoResults()` (exist solely due to CSV format); leaderboard uses `JSON.parse()` directly — consumers ignore the extra fields
  - `test_parse_results.py`: rewrite `write_csv` / `write_ko_results_csv` tests
  - `test_bracket.py`: update `load_results()` to parse JSON
  - `test_leaderboard.js`: remove/update §7 (`parseKoResults` CSV tests)
  - `clear_simulation.yml` + `auto_clear_simulation.yml`: replace `printf "match,...\n"` with `printf '{}'`

- **Extract inline JS from HTML pages (Tier 1 refactor)** — the three HTML pages each contain hundreds of lines of logic in `<script>` tags. Extract into standalone `.js` files; no behavior changes. Do this before the Tier 3 items above, since it's a prerequisite for modularizing cleanly.
  - Create `leaderboard.js` from Leaderboard Swiftly lines 848–2825 (~1,980 lines). Keep a 2-line config block inline: `const POOL_ID = 'swiftly'` and `const LIVE_SCORES_ENABLED = true`. `make_fandf.py` is unchanged — it still matches the exact `POOL_ID` string.
  - Create `ko_picks.js` from KO Picks lines 392–813 (~422 lines). No page-specific config; moves verbatim.
  - Create `group_picks.js` from Group Picks lines 624–1043 (~420 lines). Add `<script src="scoring.js">` and `<script src="bracket.js">` to Group Picks `<head>`, then remove the inline MATCHES copy (lines 627–700) and the inline RANKINGS/FLAGS copies (same values as bracket.js — diff to confirm before deleting).
  - Verify: `python3 make_fandf.py` still works; run all 4 test suites; smoke-test all 3 pages at `?games=88`.
  - **Tier 2 (post-Tier 1):** Convert to ES modules (`<script type="module">`), retire `make_fandf.py` by reading `POOL_ID` from a URL param, and split `leaderboard.js` into render / live / standings modules.
