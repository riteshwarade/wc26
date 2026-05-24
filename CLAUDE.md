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
// koDisplay(num) → 'Jun 28 · 3:00 PM EDT'
// Used in matchCard() and all mobile card renderers
```

---

## Bracket architecture

- `bracket.js` defines: `KO_SCHEDULE`, `koDisplay()`, `R16`, `QF`, `SF`, `R32_SLOTS`, `FLAGS`, `RANKINGS`, `roundLabel()`, `matchCard()`, `buildBracketHtml()`, `positionAndConnectBracket()`, `drawBracketConnectors()`
- Match numbers: R32=73–88, R16=89–96, QF=97–100, SF=101–102, 3rd=103, Final=104
- R32 display order follows Wikipedia bracket (not M73–M88 numeric): `[74,77,73,75,83,84,81,82,76,78,79,80,86,88,85,87]`
- All `.bk-col` use `flex: 1` — no per-round flex overrides; `.bk-mnum` uses `white-space: nowrap; overflow: hidden; text-overflow: ellipsis`
- `bkTeamRow` renders flag in `.bk-fl` and name+rank in `.bk-tn` separately — do NOT call `teamHtml()` inside bracket cards (double-flag bug)
- R16/QF/SF/Final cards are `position: absolute` inside `.bk-float` — absolutely positioned cards have no intrinsic width, so column sizing is driven by R32 content only
- `roundLabel(103)` returns `'3rd'` (not `'3rd Place'`)

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
