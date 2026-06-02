# WC2026 Pool — Analytics Playbook

Run any analysis by number: "run analysis #N" or "run analysis #N for fandf".

Default pool is **swiftly** unless otherwise specified.

---

## Completed

### #1 — Group picks consensus
Shows which group stage matches everyone agrees on (100% consensus) and which are most contested (split picks). Useful for seeing where the pool will diverge.

**Data:** `data/group_swiftly_picks.json` + match list from `scoring.js`
**Output:** Two lists — 100% consensus matches, and matches with <60% agreement with full breakdown.
**Last run:** May 31, 2026 (10 participants, Swiftly pool)

---

## Planned

- **Group picks consensus by group** — Same as #1 but broken out group by group (A–L). Shows which groups have the most disagreement overall.
- **Unique picks** — For each match, which participants are the "odd one out" — picking differently from everyone else. Highlights who is taking the most contrarian positions.
- **Per-participant boldness score** — Counts how many times each participant picked against the majority. Higher score = more contrarian. Could correlate with risk/reward once results come in.
- **Most picked group winners** — For each group, who does the pool collectively expect to finish 1st and 2nd? Based on aggregating picks across all 6 group matches per team.
- **Score accuracy (post-tournament)** — Once results are in, how many correct picks does each participant have, broken down by group. Leaderboard within the group stage only.
- **Knockout picks consensus** — Same as #1 but for knockout picks — which R32/R16/QF/SF matches does everyone agree on, and where is there disagreement.
- **Champion pick breakdown** — How many participants picked each team to win the whole tournament. Who is the consensus champion pick?
