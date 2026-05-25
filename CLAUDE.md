# WC2026 Pool — Claude Context

Full design doc: `WC2026_Pool_Plan.md`

---

## Hard rules

**Never edit `WC2026_Pool_Leaderboard_FandF.html` directly.**
Always edit `WC2026_Pool_Leaderboard_Swiftly.html`, then run:
```
python3 make_fandf.py
```
The two files are identical except 4 lines (title, header, POOL_ID, POOL_NAME).

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
| `WC2026_Pool_Leaderboard_Swiftly.html` | Main leaderboard — edit this, never FandF |
| `WC2026_Pool_Leaderboard_FandF.html` | Auto-generated from Swiftly via `make_fandf.py` |
| `WC2026_Pool_Knockout_Picks.html` | KO picks entry page |
| `WC2026_Pool_Group_Picks.html` | Group stage picks entry page |
| `make_fandf.py` | Regenerates FandF from Swiftly (4 substitutions) |

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

**Match header:** `.bk-mnum { letter-spacing: 0.2px; }`

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

## Group match results table

- Column order: `#` · `Grp` · `Date` · `Time (TZ)` · `Result` · `Score`
- Mobile (`max-width: 680px`): Time column hidden; `#` and `Grp` also hidden
- Group picks CSS grid: `grid-template-columns: 30px 28px 88px 72px auto`; mobile breakpoint `max-width: 640px`

---

## ESPN API

Results and time verification both use:
```
https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates=YYYYMMDD
```
No API key required. Returns events with UTC `date` field and team `displayName`.

ESPN name mapping (5 teams differ from internal names):
`Czechia→Czech Republic`, `Türkiye→Turkey`, `Bosnia-Herzegovina→Bosnia and Herzegovina`, `Congo DR→DR Congo`, `Curacao→Curaçao`

---

## Local dev / testing

```bash
python .github/scripts/simulate.py --participants 10 --stage all
python .github/scripts/aggregate_picks.py
python -m http.server 8000
# open http://localhost:8000/WC2026_Pool_Leaderboard_Swiftly.html?games=88
```
Append `?games=N` to simulate any point in the tournament (e.g. `?games=88` = R32 complete).
