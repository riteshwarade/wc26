# WC2026 Pool — Analytics Playbook

Run any analysis by number: "run analysis #N" or "run analysis #N for fandf".

Default pool is **swiftly** unless otherwise specified.

**Cross-pool note:** Ritesh Warade participates in both pools. When running analytics across all participants, count him once (use his Swiftly picks; skip the FandF duplicate). Merge with: Swiftly first, then FandF entries only if the name doesn't already exist.

---

## Completed

### #1 — Consensus picks
Shows which group stage matches everyone agrees on (100% consensus) and which are most contested (split picks). Useful for seeing where the pool will diverge.

**Data:** `data/group_swiftly_picks.json` + match list from `scoring.js`
**Output:** Two lists — 100% consensus matches, and matches with <60% agreement with full breakdown.
**Last run:** Jun 7, 2026 (26 unique participants, both pools combined)

---

### #2 — Contrarian picks
Ranks participants by how many times they picked the lower-ranked (worse FIFA ranking) team to win. Higher count = more contrarian / willing to back underdogs. An upset pick is any match where a participant picks the team with the higher rank number to beat the team with the lower rank number.

**Data:** `data/group_{pool}_picks.json` + `RANKINGS` from `bracket.js`
**Output:** Ranked list of participants with their upset pick count and the specific upsets they backed.
**Last run:** —

---

## Planned

- **Group picks consensus by group** — Same as #1 but broken out group by group (A–L). Shows which groups have the most disagreement overall.
- **Unique picks** — For each match, which participants are the "odd one out" — picking differently from everyone else. Highlights who is taking the most contrarian positions.
- **Per-participant boldness score** — Counts how many times each participant picked against the majority. Higher score = more contrarian. Could correlate with risk/reward once results come in.
- **Most picked group winners** — For each group, who does the pool collectively expect to finish 1st and 2nd? Based on aggregating picks across all 6 group matches per team.
- **Score accuracy (post-tournament)** — Once results are in, how many correct picks does each participant have, broken down by group. Leaderboard within the group stage only.
- **Knockout picks consensus** — Same as #1 but for knockout picks — which R32/R16/QF/SF matches does everyone agree on, and where is there disagreement.
- **Champion pick breakdown** — How many participants picked each team to win the whole tournament. Who is the consensus champion pick?
