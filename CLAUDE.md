# WC2026 Pool — Claude Context

Full design doc: `WC2026_Pool_Plan.md`

---

## Working style

**Always plan before building.** Present the plan and wait for explicit approval before writing any code or making file changes.

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
| `leaderboard.js` | Leaderboard logic (extracted from Swiftly HTML). Depends on bracket.js + scoring.js. Config (`POOL_ID`, `LIVE_SCORES_ENABLED`) stays inline in HTML. |
| `ko_picks.js` | KO picks page logic (extracted from Knockout Picks HTML). Depends on bracket.js. |
| `group_picks.js` | Group picks page logic (extracted from Group Picks HTML). Depends on scoring.js (MATCHES) + bracket.js (FLAGS, RANKINGS). |
| `WC2026_Pool_Leaderboard_Swiftly.html` | Main leaderboard — edit this, never FandF. Inline config: `POOL_ID`, `LIVE_SCORES_ENABLED`. |
| `WC2026_Pool_Leaderboard_FandF.html` | Auto-generated from Swiftly via `make_fandf.py` |
| `WC2026_Pool_Knockout_Picks.html` | KO picks entry page |
| `WC2026_Pool_Group_Picks.html` | Group stage picks entry page |
| `make_fandf.py` | Regenerates FandF from Swiftly (3 substitutions: title, header, POOL_ID) |
| `data/rankings.json` | **Canonical** FIFA rankings — single source of truth for all scripts |
| `WC2026_Intro.pptx` | Swiftly-branded intro deck (13 slides, incl. host cities map as slide 6) — share with pool participants before Jun 11 |
| `WC2026_Bracket_QF_to_Final.png` | **Superseded by `WC2026_Bracket_Sharing.html` (see below).** Static bracket graphic built via SVG → `cairosvg` → PNG; kept only as a stale snapshot. The cairosvg pipeline couldn't rasterize color-emoji-font flags (required a twemoji vendoring workaround) and needed manual regeneration after every result — the HTML version fixes both by rendering natively in a real browser. |
| `WC2026_Bracket_Sharing.html` | (Renamed from `WC2026_Bracket_QF_to_Final.html`, Jul 9 2026 — same file, name shortened for sharing.) Standalone bracket snapshot page to share with pool participants — QF/SF/Final only (no R32/R16/3rd place). Loads the real `bracket.js` via `<script src="bracket.js">` and calls its actual `matchCard()`/`bkTeamRow()` so card markup, flags, FIFA ranks, and `{round} · M{num} · {date}` headers are byte-identical to the live bracket — no re-implementation. `.bk-*` CSS is copied verbatim from `WC2026_Pool_Leaderboard_Swiftly.html`. QF/SF/Final data is hardcoded (not fetched): QF shows the real confirmed matchups once all R16 results are in `results/knockout_results.csv`; SF/Final show `W{num}`-style TBD placeholders via the same `isTbd()`/`bkTeamRow()` convention. Positioning/connectors are a small inline script adapted from `positionAndConnectBracket()`/`drawBracketConnectors()` in `bracket.js`, scoped down to just the `[[97,98,101],[99,100,102],[101,102,104]]` levels — the real functions require R32 DOM elements that don't exist on this page. Snapshot as of generation date; re-run by hand (update the `QF_MATCHES`/`SF_MATCHES`/`FINAL_MATCH` arrays) once new results land, no auto-refresh. Real fonts (Google Fonts Inter/Poppins) and real emoji flags render natively — open the file in a browser and screenshot. |
| `test_aggregate_picks.py` | Python unit tests for aggregate_picks.py: CSV parsing + filename extraction (28 tests) |
| `test_parse_results.py` | Python unit tests for parse_results.py (103 tests) |
| `test_e2e.js` | JS end-to-end: 10-user full-tournament + 152 invariant checks |
| `test_bracket.py` | Bracket + standings end-to-end (all 495 3rd-place combos) |
| `test_ko_picks.js` | Node unit tests for ko_picks.js pure logic: feedsInto topology, getTeams resolution, clearInvalidDownstream cascades (58 tests) |
| `.github/workflows/ci.yml` | CI: runs all four test suites on every push/PR |
| `.github/workflows/pages.yml` | Deploys GitHub Pages via `peaceiris/actions-gh-pages@v4` — pushes to `gh-pages` branch (no Deployments API, no hangs). Triggered only on HTML/JS/CSS changes; cron data pushes never trigger it. GitHub Pages source is set to `gh-pages` branch in repo Settings. |
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
- **Variant 1** — Provisional bracket. Embedded in both leaderboard pages. Read-only; derived from group results. Shows Provisional (orange) / Confirmed ✓ (green) badge. `renderBracket()`. Mobile: matches grouped in pairs with "winners meet in R16 · M89" connector pills (`MOB_PAIR_NEXT`), same as Variants 2/3.
- **Variant 2** — Pick bracket. `WC2026_Pool_Knockout_Picks.html`. Interactive; users click to pick winners. Uses `data-match`/`data-team` attrs via `bkTeamRow`'s `extraAttrs` param.
- **Variant 3** — Results bracket. Leaderboard, KO stage. Same cards as Variant 1 but `mkCard` reads `koResults`: winner solid blue, loser muted, scores + penalty rendering, correctness pill in `.bk-mnum`. `renderKoBracket()`.

### JS primitives (`bracket.js`)

- Exports: `KO_SCHEDULE`, `koDisplay()`, `R16`, `QF`, `SF`, `R32_SLOTS`, `FLAGS`, `RANKINGS`, `roundLabel()`, `matchCard()`, `buildBracketHtml()`, `positionAndConnectBracket()`, `drawBracketConnectors()`, `slotCls()`, `MOB_ROUNDS`, `MOB_PAIR_NEXT`, `buildMobTabHtml()`, `switchBracketTab()`
- Match numbers: R32=73–88, R16=89–96, QF=97–100, SF=101–102, 3rd=103, Final=104
- R32 display order follows Wikipedia bracket (not M73–M88 numeric): `[74,77,73,75,83,84,81,82,76,78,79,80,86,88,85,87]`
- `bkTeamRow` renders flag in `.bk-fl` and name+rank in `.bk-tn` separately — do NOT call `teamHtml()` inside bracket cards (double-flag bug)
- R16/QF/SF/Final cards are `position: absolute` inside `.bk-float` — absolutely positioned cards have no intrinsic width, so column sizing is driven by R32 content only
- `roundLabel(103)` returns `'3rd'` (not `'3rd Place'`)

### Wikipedia slot confirmation (R32 bracket)

Per-slot confirmation is fetched from Wikipedia on every cron run (once all 12 groups have started) and stored in `knockout_bracket.json` alongside each R32 match:

```json
"74": { "home": "Germany", "away": "Paraguay", "wiki_home": "Germany", "wiki_away": null }
```

`wiki_home`/`wiki_away` are `null` when Wikipedia hasn't confirmed that slot yet. Stored via `fetch_wikipedia_r32_slots()` in `parse_results.py`, which calls `_parse_wiki_r32_slots()`.

**Wikipedia template format:** `{{#invoke:flag|fb|CODE}}` (confirmed) vs `<!--{{#invoke:flag|fb|}}-->placeholder` (unconfirmed). Parsing strips HTML comments first, then splits rows on `||`.

**Row order:** Wikipedia bracket rows follow `_R32_DISPLAY_ORDER = [74,77,73,75,83,84,81,82,76,78,79,80,86,88,85,87]` — same as `bracket.js` R32_SLOTS display order.

**`slotCls(wikiTeam, compHome, compAway)`** — shared primitive in `bracket.js` (used by Variant 1 leaderboard and Variant 2 KO picks). Returns:
- `'slot-tbd'` — Wikipedia hasn't confirmed this slot → team row pulses
- `''` — Wikipedia team matches our computed team (order-independent) → normal
- `'slot-mismatch'` — Wikipedia has a different team → red border + text

Only applied to R32 slots (M73–M88).

**Variant 1 (leaderboard):** Re-render triggered by `_lastBracketWikiKey` tracker (JSON of all `[wiki_home, wiki_away]` pairs) alongside the existing `bracketChanged` guard.

**Variant 2 (KO picks):** `r32Data` (module-level in `ko_picks.js`) holds the full `round_of_32` object from `knockout_bracket.json`, including `wiki_home`/`wiki_away`. Slot state is applied in `mkCard` and `mobPickCard`. Importantly, a slot-tbd or slot-mismatch team row is **not pickable** — `data-team` attrs are only set when `bothPickable = !isTbd(h) && !isTbd(a) && hSlotCls === '' && aSlotCls === ''`. Mobile rows use `pointer-events: none` to suppress hover on unconfirmed slots (desktop hover is already gated on `[data-match]`). `simulate.py` writes `wiki_home: home, wiki_away: away` so simulated brackets are fully confirmed/pickable.

**`verify_r32_against_wikipedia`** was fixed in this feature — the old regex `{{fb[a-z]*|CODE}}` never matched; Wikipedia uses `{{#invoke:flag|fb|CODE}}`. Now shares `_parse_wiki_r32_slots()` / `_fetch_ko_wikitext()` helpers.

### Bracket display condition (leaderboard)

The bracket section shows "Bracket appears once every team has played." until `allTeamsPlayed` is true. This requires all 24 matchday-1 results to be in the CSV (M1–M24 = 2 matches per group × 12 groups). The check:
```js
const allTeamsPlayed = Array.from({length: 24}, (_, i) => i + 1).every(m => _lastResults[m]);
renderBracket(_lastResults, allTeamsPlayed, bracketConfirmed);
```
M24 (Uzbekistan vs Colombia, Group K) is the last matchday-1 game chronologically — Jun 18 02:00 UTC. Once it completes and the pipeline picks it up, the bracket unlocks.

`bracketConfirmed` is set by `parse_results.py` after three independent gates all pass:
1. **ESPN double-confirmation** — the existing `group_results.csv` already had 72 results when this cron run started (i.e., the previous run also saw 72)
2. **Wikipedia R32 cross-check passes**
3. **Wikipedia confirmed twice** — `wikipedia_seen: true` is already in `knockout_bracket.json` from a prior run

State is persisted via a `wikipedia_seen` boolean field in `knockout_bracket.json`. On a Wikipedia fetch failure (transient), `wikipedia_seen` is not reset — only a loss of double-confirmation resets it. `simulate.py` writes `confirmed: true, wikipedia_seen: true` directly so simulation confirms immediately. Until all three gates pass, the badge reads "Provisional".

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
| `.l` (loser) | transparent | `#c4c4c4` (fixed Jul 12, 2026 — was transparent) | `var(--neutral-medium)`; flag 35% opacity |
| `:hover` (unset) | `var(--blue-lightest)` | `var(--swiftly-blue)` | — |
| `.w:hover` | `var(--swiftly-blue)` + `brightness(0.92)` | same | — |
| `.l:hover` | `var(--blue-lightest)` | `var(--swiftly-blue)` | restored to normal |

Mobile equivalent `.bk-mob-team.bk-mob-los` (used by `leaderboard.js` for the mobile KO results bracket) got the same border-color fix — was `transparent`, now `#c4c4c4`. `WC2026_Pool_Knockout_Picks.html` has its own copy of `.bk-team.l` (applied to whichever team a user didn't pick, via `ko_picks.js`'s `homeCls`/`awayCls`) — updated identically. Originated from a design tweak tried first on the one-off `WC2026_Bracket_Sharing.html` snapshot, then ported to the shared styles once confirmed.

**Gotchas:**
- `.bk-team[data-match].w:hover` must re-assert `background: var(--swiftly-blue)` — the less-specific `:hover` rule otherwise wins and reverts the row to light blue
- `.team-rank` has its own `color: var(--neutral-dark)` rule; losers need explicit `.bk-team.l .team-rank { color: var(--neutral-medium); }` to override it
- Do NOT add `font-weight` to loser hover — font-weight changes cause text reflow even with `white-space: nowrap`
- `matchCard()` always puts `data-match="${num}"` on the outer `.bk-card` div. The click handler uses `closest('[data-match]')`, which will bubble up to `.bk-card` if the click lands outside a team row. `.bk-card` has no `data-team`, so `pickTeam` receives `undefined` — guard with `if (!team) return` at the top of `pickTeam`
- `matchCard()` optional params `mnumLabelCls` / `mnumExtra`: if `mnumLabelCls` is set (e.g. `'bk-mnum-label'`), the mnum text is wrapped in `<span class="...">` and `mnumExtra` (pill HTML, live-minute span, etc.) is appended inside `.bk-mnum`. Used by Variant 3 to avoid post-hoc regex surgery. Defaults to `''` (plain text) so all other callers are unaffected.

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
- **KO mode** (`renderKoStandings`): last 5 of `KO_MATCH_ORDER` **by kickoff time** (same issue — KO match numbers are also not chronological). `koChronoOrder` sorts `KO_MATCH_ORDER` by `KO_SCHEDULE[m]` with match-number tiebreaker, computed inside `renderKoStandings`. `KO_MOB_LAST = 5`. `koPlayedNums` filters `koChronoOrder` to entries in `koResults` or `koLiveData` (same as group stage — includes live matches). Squares assembled from `koSqByNum` map in `koChronoOrder` order.
- Column header: `Recent`. Tooltip data attributes are present on every mob square — existing tooltip handler works automatically.

---

## Live scores (leaderboard — group stage + KO)

> **Built.** Group stage and KO stage.

**Toggle:** `const LIVE_SCORES_ENABLED = true/false` at the top of the leaderboard JS. Off = no ESPN fetch, no live UI. This is an internal dev toggle, not a URL param.

**Data:** Client-side ESPN fetch (`https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates=YYYYMMDD`). Polls every ~60s while any match is in-progress (`status.type.state === 'in'`). Stops polling when all today's matches are `post`. Uses existing ESPN name mapping (`ESPN_TEAM_MAP`). **ESPN indexes matches by ET date, not UTC** — fetches yesterday + today UTC to catch late ET games (e.g. 10 PM ET = 2 AM UTC next day).

**Pick statuses (new):** `live-correct`, `live-wrong`, and `live-draw` — evaluated against current live score, applied only while game is in progress. For group matches, `Draw` is a valid pick so `live-draw` isn't needed (tied score → `cur='Draw'` → `live-correct` if they picked Draw, `live-wrong` otherwise). For KO matches, picks are team names — if the score is tied, the outcome is unknown → `live-draw` (amber/orange pulse). Squares pulse (opacity 1→0.3→1, 1.8s): blue for `live-correct`, red for `live-wrong`, `--swiftly-orange` for `live-draw`. Tooltip: `🔴 Live · tied`. Once final, squares snap to solid.

**Results table:** For in-progress matches (`state: 'in'`), the time cell shows the current minute (e.g. `67′`) and the score cell shows the live score — both pulsing (opacity 1→0.3→1, 1.8s) in default text color. During the bridge period (`state: 'post'`, CSV unconfirmed), the score and `FT` also pulse — same animation — so the results table stays consistent with the pulsing squares. `isBridge = lm.state === 'post'`; `pulse()` applies to both `isLive` and `isBridge`. Scheduled rows unchanged. Final rows (CSV confirmed) show `FT` + solid score. The Correct column also pulses during live and bridge; its count is computed on the fly from `_lastStandings` + current live score (not from `grpCounts`, which only tracks finalized `correct`/`wrong` statuses).

**Standings:** Points, rank, and all aggregate numbers stay frozen during live. Only squares change color. (May extend to preview standings in future.)

**Scope:** Group stage and KO stage.

**Diagnostics (DevTools console):**
```js
// Group stage
document.querySelectorAll('.sq-live-correct, .sq-live-wrong, .sq-live-draw').length  // should be > 0 while game is live
_liveData[matchNum]       // { homeScore, awayScore, state, minute }
_lastResults?.[matchNum]  // undefined = CSV not updated yet
_bridgeScores[matchNum]   // { homeScore, awayScore } — persists after ESPN drops event
_pendingResults.size      // > 0 = waiting for CSV confirmation
_livePoller               // null = stopped; number = interval ID (running)
_groupFrozen              // true = group standings locked (bracketConfirmed + 72 results seen)
renderStandings(_lastStandings, _liveData);  // force re-render if squares look wrong
// KO stage
_koLiveData[matchNum]     // { homeScore, awayScore, state, minute }
_lastKoResults?.[matchNum]
_koBridgeScores[matchNum]
_koPendingResults.size
_koLivePoller
renderKoBracket(_lastKoBracketData, _lastKoResults, _lastKoScores, _lastKoCounts, _koLiveData);
```

**`_pendingResults` seeding — two paths:**
- **Score-based (primary):** if `_bridgeScores[mNum]` is set (we saw ESPN live data) and CSV hasn't confirmed, add to `_pendingResults` immediately on every `fetchLiveScores` call. Handles ESPN dropping the event without a `post` state transition (`in` → gone).
- **Time-based (page-reload fallback):** if elapsed > 95 min from kickoff and < 24 h, add to `_pendingResults`. Covers page reloads after ESPN has already dropped the event and `_bridgeScores` is empty. 95 min covers 90 min + normal stoppage; 24 h cap prevents indefinite polling.

**Known behavior (fixed):** Previously, `stopLivePolling()` was called immediately when a game ended, creating a gap before the bridge restarted polling. Fixed: during the bridge period (`_pendingResults.size > 0`), the polling interval is never stopped — it keeps running and `init()` is called each cycle to re-check the CSV. Polling only stops when `_pendingResults` is empty (all results CSV-confirmed). See `live_scores_test_plan.md` for the full manual test checklist.

**Stale-CSV regression fix:** After the bridge resolves, the 5-minute `setInterval` can call `init()` and Fastly CDN (up to 5-min cache on raw.githubusercontent.com) may serve a stale CSV that does NOT contain the just-confirmed result. Before this fix, `_lastResults` and `_lastStandings` would be overwritten with the stale data — squares stay solid (correct) but points revert to old values. Fix (in `init()`): guard the `_lastResults`/`_lastStandings`/`_lastGrpCounts` update with a regression check:
```js
const _newMatchCount = Object.keys(results).length;
const _oldMatchCount = _lastResults ? Object.keys(_lastResults).length : -1;
// Update BEFORE setting freeze — see order note below.
if (!_groupFrozen && _newMatchCount >= _oldMatchCount) {
  _lastStandings = standings; _lastResults = results; _lastGrpCounts = grpCounts;
}
if (!_groupFrozen && bracketConfirmed && _newMatchCount === 72) _groupFrozen = true;
renderStandings(_lastStandings, _liveData);
```
`_groupFrozen` (module-scope, init: `false`) is set permanently the first time `bracketConfirmed && matchCount === 72`. Once frozen, `_lastResults`/`_lastStandings`/`_lastGrpCounts` are never overwritten — group points are locked even if ESPN later corrects a score. The stale-CSV match-count guard still runs for the non-frozen case (group stage in progress). All downstream renders (`renderResults`, `renderGroupTables`, `renderBracket`) and the sticky bar `played` count use `_lastResults`/`_lastGrpCounts` instead of local `results`/`grpCounts`, so match count and points always move in lockstep.

**Order matters — update before freeze:** The update block must run before the freeze check. If `_lastResults` is `null` (first page load) and the first `init()` call already sees 72 results + `bracketConfirmed=true`, the old order set `_groupFrozen=true` first, then the update guard failed (`!_groupFrozen` = false), leaving `_lastResults=null`. `Object.keys(null)` then threw `"Cannot convert undefined or null to object"` — crashing every section. Fixed Jun 28 by swapping the two `if` blocks.

**Bridge-period flash fix:** During the bridge, `fetchLiveScores` calls `init()` (to re-check the CSV), and `init()` was calling `fetchLiveScores()` again unconditionally — creating a rapid loop (~200–500ms per iteration) that re-rendered `renderBracket` on each pass, causing the bracket to flash between positioned and unpositioned states every ~1s. Two fixes: (1) `renderGroupTables` and `renderBracket` in `init()` are now gated on `freshData || bracketChanged` — `freshData = currentMatchCount > _lastRenderedMatchCount` (only true when the CSV gains a confirmed result); `bracketChanged = bracketConfirmed !== _lastBracketConfirmed` (only true when Provisional flips to Confirmed). Tracked by module-scope `_lastRenderedMatchCount` (init: -1) and `_lastBracketConfirmed` (init: `undefined`). (2) The inner `fetchLiveScores()` call in `init()` is guarded with `&& !_livePoller` — only fires on initial page load before the 60s interval is started.

**`#provisional_bracket` deep link:** `_revealSections()` calls `bracketSectionLabel.scrollIntoView({ behavior: 'smooth' })` when `window.location.hash === '#provisional_bracket'`. Shareable URLs: `WC2026_Pool_Leaderboard_Swiftly.html#provisional_bracket` and `WC2026_Pool_Leaderboard_FandF.html#provisional_bracket`.

**Not doing:** KO upset detection — decided against it.

**KO bracket live treatment (built):** During a live KO match, both team rows pulse (1→0.3→1, 1.8s). Currently winning team: `.live-win` — pulsing solid blue. Currently losing team: `.live-lose` — pulsing muted/transparent. If tied: both rows get `.live-tied` — pulsing with default styling; label also pulses via `.bk-mnum-label.live`. Live minute shown in `.bk-mnum-live` span; correctness pill shown alongside (minute first, then pill) once a leader is known. Date/time stripped from bracket card header once match is live or final — shows only `R32 · M73`. `matchCard()` accepts a 13th `suppressDate=false` param; `mkCard` and `koMobMatchCard` pass `true` when `winner` or `lm` is set. Live pill computed inline from `_lastKoCombined`: counts who has the current leader picked; pill hidden when tied (no leader). On FT (CSV confirmed), rows snap to solid `.w`/`.l` winner/loser state. Bridge period (ESPN post, CSV unconfirmed): `_koPendingResults` tracks; polling continues. 135 min threshold (vs 95 for group) to account for ET + pens.

**KO live polling startup (fixed):** `startKoLivePolling()` is now called unconditionally after the first `fetchKoLiveScores()` on page load — same pattern as `stopKoLivePolling()` self-terminating when `anyIn = false && _koPendingResults.size === 0`. Previously the poller was only started if `_koLiveData` was non-empty after the first fetch; if the page loaded before ESPN marked the game `in`, the 60s poller never started and live scores would be missing for up to 5 minutes (until the next `init()` retry).

**KO live — `_pendingResults` seeding (same two paths as group):**
- **Score-based:** `_koBridgeScores[num]` set + CSV not confirmed → added to `_koPendingResults` each poll cycle.
- **Time-based fallback:** elapsed > 135 min from kickoff and < 24 h → add to `_koPendingResults`.

**KO stale-CSV regression fix:** Same pattern as group stage. In `init()` KO branch, `_lastKo*` globals are only updated when `_newKoMatchCount >= _oldKoMatchCount`. Renders use `_lastKo*` rather than local fetch results, so a Fastly-stale CSV during the bridge can't revert confirmed KO results.

**Cascaded pick vs. live overlay (fixed, Jul 4 2026):** A pick that cascaded in an earlier round (e.g. picked Netherlands, but Netherlands lost in R32) keeps `pr.status === 'cascaded'` permanently — `scoring.js`'s cascade check takes precedence over the winner comparison in both the pending and confirmed branches (never flips to `wrong`). But `leaderboard.js`'s live-overlay block (in the KO squares loop) was overwriting that correct status whenever the *current* match was live and unconfirmed — it compared the cascaded pick's team against the live score of a match that pick isn't even part of, and always came back `live-wrong` (a Netherlands pick can never be "leading" a Canada v Morocco match). Fixed by adding `&& pr.status !== 'cascaded'` to the live-overlay guard, so cascaded picks are skipped by the live overlay and keep rendering as `sq-cascaded` (red outline, transparent) with the "⚡ Void — team eliminated earlier" tooltip instead of a bogus live "wrong so far".

**KO bracket flash fixes:** `renderKoBracket` triggers `positionAndConnectBracket` via two rAF frames (cards flash at `top:0` before positioning). Two guards prevent unnecessary re-renders: (1) From `init()`: `renderKoBracket` only fires when `_newKoMatchCount > _lastRenderedKoMatchCount` — i.e., only when a new KO match is confirmed. `_lastRenderedKoMatchCount` is a module-scope tracker (init: -1). (2) From `fetchKoLiveScores`: `renderKoBracket` only fires when `_koLiveData` actually changed — checked by serializing `newLive` to JSON and comparing to `_lastKoLiveStr`. `renderKoStandings` (no absolute positioning, no flash) is called every time from both paths.

---

## Mobile breakpoints (leaderboard)

### Mobile bracket card styling (all 3 variants)

`.bk-mob-pair-group` — white background (`#ffffff`), `1px solid var(--blue-light)` border, `border-radius: 12px`. Groups two matches + connector pill.
`.bk-mob-match` — grey background (`#f4f5f6`), `0.5px solid #dde3ea` border, `border-radius: 10px`. Individual match card nested inside the pair group.
Team rows (`.bk-team`) remain white with `#cce8f4` border. Selected winner: solid Swiftly Blue. Loser: transparent/faded. Defined in each HTML file (not `bracket.js`).

**Mobile team row flag separation:** `mobTeamHtml(name)` in `bracket.js` renders flag in `.bk-mob-fl` (separate flex child, `flex-shrink: 0`) and name+rank in `.bk-mob-tn` (flex: 1, overflow ellipsis) — same pattern as desktop `bkTeamRow`. This prevents flag emoji from inflating the line-box height for known-team rows vs TBD rows. TBD placeholders get just a `.bk-mob-tn` span (no flag). Used by all 3 mobile card builders: `mobMatchCard` (V1, `leaderboard.js`), `mobPickCard` (V2, `ko_picks.js`), `koMobMatchCard` (V3, `leaderboard.js`). CSS: `.bk-mob-fl` and `.bk-mob-tn` defined in both HTML files; `.bk-mob-team-name` removed.

---

## Mobile breakpoints (leaderboard)

Two media queries govern mobile layout:

- **Portrait** — `@media (max-width: 640px)`: stacks group tables/results, hides squares + max-pts columns, hides date/time/# in results table, shows mobile bracket tabs. Also reveals `.th-mob-sq` / `.td-mob-sq` — the last-5 recent squares column (see below).
- **Landscape** — `@media (max-width: 896px) and (orientation: landscape)`: stacks group tables/results (same order as portrait); both group standings (`#standings-body .card`) and KO standings (`#koStandingsSection .card`) are `overflow-x: auto` (horizontally scrollable); bracket switches to tab view (`.bk-outer` hidden, `.bk-mobile-tabs` shown — same as portrait). Landscape phones (~667–896px wide) miss the 640px portrait breakpoint entirely, hence the separate query. The KO Picks page has its own landscape block with just the bracket rules (no layout stacking needed there).

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

### Pool standings tiebreaker chain (participants, not teams)

Not to be confused with the FIFA group-stage tiebreaker chain below, which ranks *teams* within a World Cup group. This chain ranks *pool participants* on the leaderboard. Implemented as the final `.sort()` inside `computeCombinedStandings` (`scoring.js`) — **two-phase, changed Jul 12, 2026**, branching on whether the Final (M104) has a result yet (`tournamentComplete = !!koResults[104]`):

**Mid-tournament** (Final not yet decided):
1. **Total points** (group + KO combined) desc
2. **Name**, alphabetically (`localeCompare`) — orders which row prints first among a tie; does *not* imply anyone actually ranks above anyone else

**Post-Final** (`koResults[104]` set):
1. **Total points** (group + KO combined) desc
2. **Correct champion pick** (picked the actual M104 winner) desc
3. **Total correct picks** (group + KO combined) desc
4. **Name**, alphabetically — again, ordering only, not a real tiebreak

**Ties are intentional and permanent in both phases.** Nothing forces a full ordering anymore — anyone still equal after the phase's criteria stays tied. `groupPts` (the participant's group-stage score) was removed from the sort entirely — it was briefly a 4th tiebreak criterion (added, then removed, both on Jul 12, 2026) and is now purely a display-only column (`p.groupPts`, shown in the Grp column on KO standings).

**Rank number display** (`#` column, `_rankMap` in `leaderboard.js`'s `renderKoStandings`) mirrors the same two-phase tie condition so the badge reflects genuine ties: pre-Final, two rows share a rank iff `totalPts` matches; post-Final, iff `totalPts` + `correctChampion` + `totalCorrect` all match. A tied group of size > 3 can legitimately all show as `top3` if they're tied for a podium spot — this is expected, not a bug.

Test coverage: `test_e2e.js`'s "Invariant checks — sort order" section validates the post-Final chain (its simulation always completes the Final). `test_leaderboard.js` §12 has dedicated cases for both phases — a post-Final tie (Eve vs Frank, tied through correctChampion/totalCorrect, differing only on groupPts, confirmed still tied) and a mid-tournament tie (Alice/Mike/Zara, tied only on totalPts, differing on groupPts and totalCorrect, confirmed still tied) — plus the pre-existing alphabetical-ordering case.

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
- ≥ 90%: `.cp-hi` — Consensus — `#d4f0fb` bg / `#00628a` text
- 11–89%: `.cp-mid` — Middle — `#fff0d0` bg / `#a05800` text
- ≤ 10%: `.cp-lo` — Contrarian — `#fce0e7` bg / `#b3003d` text

**Pill tooltip:** Hovering a `.cp-pill` shows the shared `#sq-tooltip` with "Picked correctly:" header and a `✓ Name` line per correct picker (or "— nobody" if zero). Pill carries `data-cp-names` (pipe-delimited abbreviated names). `buildGrpCounts` and `buildKoCounts` both store `names: []` alongside `correct`/`total`. The live correctness block in `renderResults` also collects `liveNames`. `.cp-pill` has `cursor: help`.

**Denominator differs between group and KO (fixed Jul 4, 2026).** Group picks can never cascade, so `buildGrpCounts`'s `total` is naturally the full pool. KO picks can cascade (team eliminated in an earlier round), and `buildKoCounts` previously only counted picks with status `correct`/`wrong` toward `total` — silently excluding cascaded picks, which shrank the denominator and inflated the percentage (e.g. a match where 13 of 33 KO players actually had the winner, but 17 others had a cascaded pick, showed as `13/16` = 81% instead of `13/33` = 39%). Fixed: `total` is now `combined.filter(p => p.koParticipant).length` — a fixed count per render, computed once — so cascaded/wrong/empty-on-this-match picks all count against the total but only `correct` ever increments the numerator. `koParticipant` (`scoring.js`, set in both branches of `computeCombinedStandings`) is `true` iff the participant's raw KO picks object has at least one key, distinguishing "played KO but got this one wrong/cascaded" from "never submitted KO picks at all" — the latter must not be counted in the denominator. **Note:** the "Knockout Standings" header player-count badge (`${combinedStandings.length} players`) intentionally still shows total pool size, not KO-participant count — left as-is by design, so it will legitimately be a larger number than any individual pill's denominator when there are group-only participants.

**Square tooltip points-won line (added Jul 9, 2026):** `_showSqTooltip()` in `leaderboard.js` appends a `.tt-points` line (`+N pts`, blue, bold) below the status line — only when `status` is `correct` or `correct-upset`; hidden (no line at all) for wrong/pending/cascaded/empty. Points are derived purely from data already on the square, no new dataset attributes needed: `Number(sq.dataset.match) >= 73` → KO match → `KO_POINTS[matchNum]` (the same round-scaled table `scoring.js` uses for real scoring: 4/8/12/16/12/24 for R32/R16/QF/SF/3rd/Final); otherwise a flat `2` (every group match is worth 2). `KO_POINTS` is a `scoring.js` top-level `const`, reachable from `leaderboard.js` the same way `KO_SCHEDULE`/`FLAGS`/`RANKINGS` cross from `bracket.js` — classic `<script>` tags on one page share a global lexical scope even though nothing is attached to `window`. Applies identically to both group and KO squares, desktop hover and mobile tap, since both paths funnel through the one shared `_showSqTooltip()`.

### "How scoring works" tooltip (KO standings)

A `<div class="scoring-info-anchor">` is injected in the KO standings section-label (right side) by `renderKoStandings`. Contains a `<span class="scoring-info-link">Scoring ⓘ</span>` and a `<div class="scoring-tooltip-box">` child with the KO points table plus a "Tiebreakers" list.

- **Desktop:** purely CSS-driven — `.scoring-info-anchor:hover .scoring-tooltip-box { display: block }`. Tooltip is `position: absolute; right: 0; top: calc(100% + 8px)` — floats below the anchor, anchored right.
- **Mobile:** CSS hover disabled. Tap on `.scoring-info-link` toggles `.tooltip-open` class on `.scoring-info-anchor` via the `touchstart` handler (added before the existing `.cp-pill`/`.sq` checks). Tooltip is `position: static` and expands inline below the header row. Tap elsewhere closes it.
- The section-label `<p>` was changed to `<div class="section-label section-label-row">` to allow block children and flex layout. `_revealSections()` still picks it up via `.section-label` selector.
- **Does not share `#sq-tooltip`** — self-contained CSS/class toggle. No interference with existing square or pill tooltips.
- **Gotcha:** `.scoring-info-anchor` has `white-space: nowrap` (to keep the link text on one line). `.scoring-tooltip-box` must explicitly set `white-space: normal` to prevent inheriting `nowrap`, which would cause the note text to overflow without wrapping.
- **Tiebreakers list (added Jul 12, 2026):** below the points table, a `<div class="stt-tb-title">Tiebreakers</div>` + `<ul class="stt-tb-list">` lists the post-Final tiebreak order (`Correct champion pick`, `Total correct picks`, `Still tied? Stay tied.`) — mirrors the two-phase sort in `computeCombinedStandings` (see "Pool standings tiebreaker chain" above). Deliberately styled to match the existing `.stt-row` text (0.70rem, weight 400, `var(--neutral-dark)`) rather than the bolder unused `.stt-title` class, so it reads as part of the same list rather than a separate heading. `.stt-tb-title` adds the divider (`border-top`) that separates it from the points table above.

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
# NOTE: simulate.py will refuse to overwrite results CSVs that already contain real data.
# Use --force only if you intentionally want to overwrite real results (dangerous):
# python .github/scripts/simulate.py --participants 10 --stage all --force
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

**KO mode trigger:** `knockoutMode` is true when `?games=N` with N ≥ 73, OR when `new Date() >= new Date('2026-06-28T17:00:00Z')` — 2 hours before M73 (19:00 UTC). This is the live date-driven flip; update the timestamp for future tournaments.

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

**macOS NFD filename bug (fixed):** macOS APFS/HFS+ stores all filenames in NFD Unicode normalization. Python's `.title()` treats NFD combining accent characters (e.g. U+0301) as word separators, so `víctor` (NFD: `vi` + combining-accent + `ctor`) would title-case to `VíCtor` instead of `Víctor`. Fixed in `aggregate_picks.py` (`name_from_filename` and `name_from_knockout_filename`) by NFC-normalizing before calling `.title()`: `unicodedata.normalize('NFC', name_part.replace('-', ' ')).title()`. Affects any participant with accented characters in their filename (Víctor, Jesús, Joaquín, etc.).

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

**Bracket confirmed immutability** — `write_bracket_json` returns immediately if `existing_bracket.get('confirmed') is True`. Once confirmed, R32 teams are locked (CSV regression guard) and wiki slots are fully populated — nothing can change. This prevents a transient Wikipedia fetch error on any post-confirmation cron run from reverting `confirmed: True` back to `False`.

**KO results regression guard** — Before writing `knockout_results.csv`, `__main__` reads the existing file and merges if ESPN returned fewer results than are already on disk (same pattern as the group results guard). Guards against transient ESPN outages (0 events returned) wiping confirmed KO results.

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
| KO kickoff times | `bracket.js` `const KO_SCHEDULE` | No copies — single source, but no automated cross-check exists (see below) |

**Rankings update process:** edit `data/rankings.json` first, then update `bracket.js` `const RANKINGS` to match.

**Topology update process:** edit `bracket.js` `R16`/`QF`/`SF` first, then mirror changes to `scoring.js`, `sim_core.js`, and `simulate.py`. The `scoring.js` runtime assertion (`_assertEq`) will log a `console.error` in the browser if the copies drift.

**`KO_SCHEDULE` verification process (manual only — no CI check):** Ground truth is the ESPN scoreboard API (`https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates=YYYYMMDD`, same endpoint `parse_results.py` uses for results) — it returns the real `date` (kickoff, UTC) and `venue` for every match, keyed by generic slot labels (`Round of 32 N` = match `72+N`, `Round of 16 N` = match `88+N`, `Quarterfinal N` = match `96+N`, `Semifinal N` = match `100+N`), which lets you match a slot to an internal match number even before real teams are confirmed. Wikipedia's knockout-stage page (`2026_FIFA_World_Cup_knockout_stage`) confirms bracket topology and venue-to-date pairing but does not expose a parseable per-match kickoff-time table, so it's a topology cross-check, not a time cross-check.

**Fixed Jul 4, 2026 — two `KO_SCHEDULE` bugs found via full ESPN audit (all 32 KO slots):**
- **M89/M90 swapped at data entry.** Match 89 (Paraguay v France, Philadelphia) was listed as `17:00Z`; Match 90 (Canada v Morocco, Houston) was listed as `21:00Z` — backwards. ESPN confirms M90 = `17:00Z` (Houston), M89 = `21:00Z` (Philadelphia). Root cause was traced from a leaderboard bug report: the mobile "Recent" squares column (chronological by kickoff, see below) showed M90 as more recent than M89, when in reality M89 kicked off (and finished) later that day.
- **M79 stale after a live schedule change.** Match 79 (Mexico v Ecuador) was hardcoded to the originally-announced `01:00Z`, but the game was delayed an hour by thunderstorms in Mexico City — actual kickoff was `02:00Z`, which is what ESPN reflects. `KO_SCHEDULE` is a static hardcoded table with no live-update mechanism, so it can only ever hold the announced time, not weather/broadcast-driven changes — ESPN is authoritative for what actually happened.
- All other 29 R32–Final slots matched ESPN exactly on both time and venue.

## Pick status values

Group `pickResults[num].status`: `correct` · `correct-upset` · `wrong` · `pending` (result not yet in) · `empty` (no pick made)

**`empty` behavior:** `.sq-empty` renders as a faint outlined square (transparent fill, `1px solid var(--neutral-light)`). Tooltip hides the pick line and shows "— No pick". `pickResults[num].result` is populated even for empty picks (so the tooltip shows the actual score if the game was played). To make a participant a late joiner, blank their pick in the CSV for already-played matches — `aggregate_picks.py` skips empty pick fields, leaving the key absent from the JSON, which `computeStandings` treats as `empty`.

KO `koPickResults[num].status`: same five + `cascaded` (team already eliminated, pick voids)

**`cascaded` visual:** `.sq-cascaded` renders as transparent fill with `1.5px solid var(--swiftly-red)` border — distinguishes voided-future picks from confirmed-wrong (solid red). Game hasn't been played yet so the outline signals "this will be wrong once played."

**M103 eligibility is reversed from every other match (fixed Jul 16, 2026).** For R32–Final, a pending pick cascades only if the picked team was *eliminated* earlier than needed (`eliminatedInRound` check in `scoring.js`'s `evalKoPicks`). M103 (3rd place) is fed by the two SF *losers* specifically — the two SF *winners* are still alive (never "eliminated") but are just as ineligible for M103 since they play in the Final instead. The elimination check alone can't catch this, so `evalKoPicks` also checks the pick against `getKoTeams(103, bracketData, koResults)` (the two real M103 participants, resolved once both SF results are in) and cascades any pick that isn't one of them. Before this fix, a pick of either SF winner for M103 stayed `pending` and kept adding 12 pts to `maxPts` even though it could never become correct — inflated `maxPts` for anyone (roughly half the pool at the time) who picked an eventual SF winner for 3rd place.

### Contrarian detection (`correct-upset`)

A pick is promoted from `correct` to `correct-upset` when ≤ 10% of participants got that match correct (i.e., the match's correctness pill is in the Contrarian tier). `_isUpsetResult` has been removed — contrarian is pool-consensus-based, not FIFA-ranking-based. Applies to both group and KO squares.

`sqStatus` in the group square builder (uses `_lastGrpCounts`):
```js
const _c = _lastGrpCounts && _lastGrpCounts[num];
const _isContrarian = _c && _c.total > 0 && (_c.correct / _c.total) <= 0.10;
let sqStatus = pr.status === 'correct' && _isContrarian ? 'correct-upset' : pr.status;
```

`sqStatus` in the KO square builder (uses `_lastKoCounts`):
```js
const _kc = _lastKoCounts && _lastKoCounts[m];
const _isKoContrarian = _kc && _kc.total > 0 && (_kc.correct / _kc.total) <= 0.10;
let sqStatus = pr.status === 'correct' && _isKoContrarian ? 'correct-upset' : pr.status;
```

**Visual:** `.sq-correct-upset` — same Swiftly Blue background as `.sq-correct`, with a white ✦ (U+2726, 4-pointed star) via `::after` pseudo-element at 6px font-size (5px for `.sq-sm`).

**Tooltip:** `'✓ Correct ✦ Contrarian'` — uses `.correct` CSS class for the status line color (same green as a normal correct pick).

---

## KO standings layout

**Columns:** `#` · Name · Grp · KO · **Total** · Max · 1·2·3 · Picks · Recent (mobile only)

**Square sizing:** Group stage uses `sq-sm` (10px); KO stage uses `sq` (14px). Row height is driven by text cells (~0.78rem ≈ 15px line-height + 16px td padding = ~31px). 14px is the safe maximum — text line-height (~15px) still exceeds square height so text drives row height. 15px would be at the boundary and risky due to sub-pixel rounding. `.td-squares` is `display: none` on mobile so the larger size has no mobile impact; mobile KO squares are explicitly forced to `sq-sm` (10px) in JS.

**Podium column (`.td-podium` / `.th-podium`):** Replaces the old Champion column. Shows three flags per user: 🥇 champion pick (M104), 🥈 runner-up (the SF pick — M101 or M102 — that isn't the champion pick), 🥉 3rd place pick (M103). Each flag fades (`opacity: 0.2`) when the team is eliminated (`status === 'wrong' || 'cascaded'`). Missing picks render as a faint `—`. Header text: `1·2·3` — same on desktop and mobile. Rendered via `.podium-flags` (inline-flex, gap 5px) + `.podium-fl` per flag. Silver derivation: if `champPick === pr101.pick` → silver = `pr102.pick` (and use `pr102.status` for fading); otherwise silver = `pr101.pick`. **Gotcha:** `.standings-table th { text-align: left }` overrides the `text-align: center` on `.th-podium, .td-podium` — header centering requires the more-specific `.standings-table th.th-podium { text-align: center }` rule (grouped with th-grp-pts/ko-pts/max-pts/total-pts). Do not remove it during cleanup.

**Sortable columns (KO standings):** Grp, KO, Total, and Max columns are clickable to sort. Module-level `_koSortCol` (default `'total'`) and `_koSortDir` (default `'desc'`) persist across live re-renders. Click a column once to sort desc; click again to flip to asc. Clicking a different column resets direction to desc. Rank (`#`) is always frozen to Total-desc order via `_rankMap` (computed once from the unsorted `combinedStandings` before sorting). Sort operates on `[...combinedStandings]` copy — `_lastKoCombined` stays untouched (needed for live pill computation). Tiebreaker: Total desc → `localeCompare` by name. No sort arrow icons — headers are clickable but no visual indicator (cursor changes to pointer on hover). Click listener re-attached to `th[data-sort]` elements after each `innerHTML =` assignment. CSS: `th[data-sort] { cursor: pointer; user-select: none }`, `th[data-sort]:hover { color: var(--neutral-darkest) }`.

**`.squares-wrap` in KO mode:** Uses `nowrap` class (same as group stage). KO round breaks use `sq-divider` (14px, matching `sq` squares); group stage uses `sq-divider-sm` (10px, matching `sq-sm`).

**Color:** `.td-total-pts` uses `var(--swiftly-blue)` + `font-weight: 700` — matches group stage `.td-points` style.

**Mobile:** `.th-squares`, `.td-squares` hidden at `max-width: 640px`. Max and Podium columns shown. Total cell shows plain `totalPts` number only (no breakdown). `.th-mob-sq` / `.td-mob-sq` revealed (last 5 KO squares, chronological order, `sq-sm` size). Mobile columns (matching desktop order): `#` · Name · Total · Max · Podium · Recent. Column widths (mobile): `#`=24px, Name=auto (capped at 88px, nowrap+ellipsis), Total=40px, Max=40px, Podium=67px, Recent=80px — consistent 5px internal padding; fits ~343px with Name getting ~92px.

### KO-only participants

A participant who submitted KO picks but has no matching group picks (by name) is flagged `koOnly: true` and `groupPtsIsFloor: true` in `computeCombinedStandings` (`scoring.js`). They receive the minimum group score of all group-stage participants as their baseline (floor), not 0. This prevents a legitimate KO-only joiner from starting at a hopeless deficit.

**`scoring.js`:** `minGroupPts = Math.min(...groupStandings.map(p => p.points))` — computed once before the KO-only loop; falls back to 0 if `groupStandings` is empty. KO-only row: `groupPts: minGroupPts, points: minGroupPts, totalPts: minGroupPts + koPts, maxPts: minGroupPts + koPossiblePts`.

**`leaderboard.js`:** When `p.groupPtsIsFloor`, the Grp cell renders as `<span class="grp-floor">N<span class="grp-floor-mark">*</span></span>` — amber number + small amber superscript asterisk. Hovering shows the custom `#sq-tooltip` ("Floor score / Minimum group pts — no group picks submitted") via `_showFloorTooltip()` wired into the mouseover/mouseout/touchstart handlers. No `title` attribute (avoids native ~1s delay and `?` cursor).

**CSS:** `.grp-floor { color: #b45309 }` · `.grp-floor-mark { font-size: 0.65rem; color: #ba7517; vertical-align: baseline; position: relative; top: -0.4em }` (use `position: relative` not `vertical-align: super` — the latter expands the line box and adds ~1.6px to row height) — all in Swiftly HTML. No `cursor: help` (removed — was showing a `?` next to the cursor).

**⚠ icon:** Removed. The amber `N*` in the Grp cell is sufficient signal for both legitimate KO-only joiners and name mismatches.

**Name mismatch:** Both the orphaned KO row (showing floor pts + amber `*`) and the real group-only row (group pts + 0 KO) appear simultaneously. Fix by renaming the KO picks file to match the group picks name.

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

- **Extract inline JS from HTML pages (Tier 1 refactor)** — **ALL STEPS DONE (Jun 20, 2026).**
  - **Step 1 — Consolidate mobile-bracket primitives into `bracket.js`. DONE.** `MOB_PAIR_NEXT`, `MOB_ROUNDS`, `buildMobTabHtml(rounds, activeRound, mkCard)`, and `switchBracketTab()` all live in `bracket.js`. Per-page copies removed from all variants. `ko_picks.js` local `buildMobTabHtml`, `PAIR_NEXT`, `MOB_ROUNDS`, and `koRoundLabel` deleted; V1/V3 local `MOB_ROUNDS`/`KO_MOB_ROUNDS` deleted. V1 and V3 mobile rendering loops reduced from ~30 lines each to a single function call.
  - **Step 2 — Extract JS files. DONE.** `leaderboard.js` (1,936 lines), `ko_picks.js` (422 lines), `group_picks.js` (315 lines) created. Inline MATCHES/FLAGS/RANKINGS removed from group_picks.js (already in scoring.js/bracket.js). Config block (`POOL_ID`, `LIVE_SCORES_ENABLED`) stays inline in the Swiftly HTML. `make_fandf.py` unchanged — still finds the `POOL_ID` string via substring search.
  - **Step 3 — Add tests for `ko_picks.js`. DONE.** `test_ko_picks.js` — 58 Node unit tests covering feedsInto topology (all R32→R16→QF→SF→Final chains), getTeams resolution (R32/R16/QF/3rd-place), and clearInvalidDownstream cascade logic. Uses `require()` with bracket.js globals seeded via `global.*` before require. ko_picks.js exports pure functions via `module.exports`; DOM event wiring guarded by `typeof module === 'undefined'`. Mobile auto-advance (maybeAdvanceTab) not covered — requires DOM; manual test plan covers it.
  - **Step 4 — Verify. DONE.** `make_fandf.py` works (3 substitutions); all 5 test suites pass (103 + 29 + 152 + bracket + 58 ko_picks); no `</script>` or inline globals leak into extracted files.
  - **`switchBracketTab` note:** lives in `bracket.js` (moved there post-Tier-1). Called via inline `onclick` attributes in generated HTML — must remain a global. Fine for regular `<script>` tags. Becomes an issue in Tier 2 (ES modules) — switch to event delegation at that point.
  - **Tier 2 (post-Tier 1):** Convert to ES modules (`<script type="module">`), retire `make_fandf.py` by reading `POOL_ID` from a URL param, and split `leaderboard.js` into render / live / standings modules.
