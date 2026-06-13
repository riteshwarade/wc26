# Live Scores Test Plan
## Generic — run against any upcoming group stage match

---

### Phase 1 — Kickoff

- [ ] Squares for the match turn blue (correct pick) or red (wrong pick)
- [ ] Squares pulse (opacity 1→0.3→1, 1.8s)
- [ ] Results table shows the match with live minute (e.g. `5′`) pulsing and score (e.g. `0 – 0`) pulsing
- [ ] `_livePoller` is a non-null number (interval running)

---

### Phase 2 — Goal scored

- [ ] Results table score updates live (e.g. `1 – 0`)
- [ ] Squares flip color if pick is now wrong (blue → red or vice versa)

---

### Phase 3 — Full time (ESPN flips to `post`)

- [ ] Results table time cell shows `FT` **pulsing** (wrapped in `.live-pulse`)
- [ ] Results table score **keeps pulsing** (same animation)
- [ ] Squares **keep pulsing** (bridge state — `_liveData[num].state === 'post'`)
- [ ] Points still show pre-game values (CSV not confirmed yet)
- [ ] `_pendingResults.size > 0`
- [ ] `_bridgeScores[num]` is set to the final score

> ⚠️ If squares go gray/solid here, bridge logic broke — note the time.
> ⚠️ FT and score NOT pulsing = `isBridge` check failed in renderResults.

---

### Phase 4 — cron-job.org fires, CSV updates (within ~5 min of FT)

- [ ] Squares snap to solid (blue = correct, red = wrong — no animation)
- [ ] Results table FT and score become non-pulsing
- [ ] Points update — winners gain 2 pts (correct) or 4 pts (correct upset)
- [ ] Standings reorder if rank changes
- [ ] Group table updates with result + standings
- [ ] "Updated HH:MM" timestamp refreshes
- [ ] `_pendingResults.size === 0`
- [ ] `_livePoller === null` (interval stopped)

> Max lag = cron-job.org delay (~5 min) + Fastly CDN cache (~5 min) + 60s poll cycle ≈ 11 min worst case.

---

### Phase 5 — Stale-CSV regression check (run ~1–2 min after Phase 4)

After the bridge resolves, the 5-min `setInterval` may call `init()` with a Fastly-cached stale CSV
that doesn't have the just-confirmed result. Before the Jun 13 fix this would revert points to old values.

- [ ] Verify points are still correct ~5–10 min after Phase 4 (no regression)
- [ ] `Object.keys(_lastResults).length` does not decrease after Phase 4

> If points revert to pre-game values after going correct, the stale-CSV guard broke.

---

### Console simulation (run anytime without a live game)

```js
// ── Simulate live in-progress ────────────────────────────
_bridgeScores[7] = { homeScore: 1, awayScore: 0 };
_liveData[7] = { homeScore: 1, awayScore: 0, state: 'in', minute: '67' };
renderStandings(_lastStandings, _liveData);
// → squares for M7 should pulse blue (correct W1 pickers) / red (wrong pickers)
// → results table shows '67′' pulsing and '1 – 0' pulsing

// ── Simulate bridge (game over, CSV not yet updated) ─────
_pendingResults.add(7);
_liveData[7] = { homeScore: 1, awayScore: 0, state: 'post', minute: '' };
renderStandings(_lastStandings, _liveData);
renderResults(_lastResults, _lastGrpCounts, _liveData);
// → squares still pulse
// → results table shows 'FT' pulsing and '1 – 0' pulsing

// ── Simulate CSV arrival ──────────────────────────────────
// (triggers the drop step in fetchLiveScores)
await fetchLiveScores();
// Manually seed _lastResults to simulate confirmed result:
_lastResults[7] = { outcome: 'W1', home: 1, away: 0 };
await fetchLiveScores();
// → squares snap solid, _pendingResults.size === 0, _liveData[7] undefined

// ── Simulate stale-CSV regression (should be blocked by fix) ─
const goodCount = Object.keys(_lastResults).length;
// Force a fake "stale" init — lower count would have overwritten before fix:
console.assert(goodCount >= Object.keys(_lastResults).length, 'Regression guard OK');
```

---

### Diagnostic commands

```js
// Square state
document.querySelectorAll('.sq-live-correct, .sq-live-wrong').length  // > 0 while live or bridging

// Match-level state (replace 7 with actual match number)
_liveData[7]              // { homeScore, awayScore, state, minute }  — undefined = not live/bridging
_lastResults?.[7]         // set = CSV confirmed; undefined = not yet
_bridgeScores[7]          // set = have a score to re-inject; undefined = page loaded after ESPN dropped
_pendingResults.has(7)    // true = bridge period active

// Poller + data health
_pendingResults.size      // 0 = bridge resolved; > 0 = waiting for CSV
_livePoller               // null = stopped; non-null = running
Object.keys(_lastResults || {}).length  // should never decrease after a confirmed result

// Force re-render
renderStandings(_lastStandings, _liveData);
renderResults(_lastResults, _lastGrpCounts, _liveData);
```
