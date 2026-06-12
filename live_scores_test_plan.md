# Live Scores Test Plan
## Canada vs Bosnia (M3) — Jun 12, 3:00 PM ET

---

### Phase 1 — Kickoff (~3:00–3:01 PM)

- [ ] Squares for match 3 turn blue (correct pick) or red (wrong pick)
- [ ] Squares pulse (opacity fades in/out every 1.8s)
- [ ] Results table shows match 3 with live minute (e.g. `5′`) and `0 – 0` score, both pulsing

---

### Phase 2 — Goal scored

- [ ] Results table score updates live (e.g. `1 – 0`)
- [ ] Squares flip color if pick is now wrong (blue → red or vice versa)

---

### Phase 3 — Full time (~4:45 PM, ESPN flips to post)

- [ ] Results table shows `FT` in time cell, final score non-pulsing
- [ ] Squares **keep pulsing** (bridge state — CSV not confirmed yet)
- [ ] Points still show pre-game values

> If squares go gray here, bridge logic broke — note the time and report.

---

### Phase 4 — cron-job.org fires, CSV updates (within ~5 min of FT)

- [ ] Squares snap to solid (no more pulsing)
- [ ] Points update — winners gain 2 pts (correct) or 4 pts (correct upset)
- [ ] Standings reorder if rank changes
- [ ] Group B table updates with result + standings
- [ ] "Updated HH:MM" timestamp refreshes

> Max lag = cron-job.org delay (~5 min) + Fastly CDN cache (~5 min) + 60s poll cycle. Worst case ~11 min.

---

### Console simulation (run anytime without a live game)

```js
// Simulate bridge state for match 3
_bridgeScores[3] = { homeScore: 1, awayScore: 0 };
_pendingResults.add(3);
await fetchLiveScores();
// → squares for M3 should pulse live-correct/live-wrong

// Simulate CSV arrival
_lastResults[3] = { outcome: 'W1' };
await fetchLiveScores();
// → squares snap solid, _pendingResults.size === 0
```

---

### Diagnostic commands

```js
// Check live square count
document.querySelectorAll('.sq-live-correct, .sq-live-wrong').length

// Inspect live data state
_liveData[3]
_lastResults?.[3]
_bridgeScores[3]
_pendingResults.size
_livePoller          // null = poller stopped; number = running

// Force re-render with live data
renderStandings(_lastStandings, _liveData);
```
