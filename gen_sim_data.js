/**
 * gen_sim_data.js
 *
 * Generates embedded simulation data for WC2026_Pool_Leaderboard_Swiftly.html.
 * Outputs JSON-ready values for LOCAL_PICKS, LOCAL_RESULTS_CSV,
 * LOCAL_KO_PICKS, LOCAL_KO_RESULTS_CSV, LOCAL_BRACKET_DATA.
 *
 * Run: node gen_sim_data.js
 * Writes: sim_data_output.json (consumed by patch_sim_data.js)
 */

'use strict';

const { MATCHES } = require('./scoring.js');

const {
  randInt, randChoice, R32_TEAMS,
  generateKoTournament, generateGroupPicks, generateKoPicks,
} = require('./sim_core.js');

// ── KO match order for CSV output ─────────────────────────────────────────────
const KO_ORDER = [
  ...Array.from({ length: 16 }, (_, i) => 73 + i),
  ...Array.from({ length:  8 }, (_, i) => 89 + i),
  ...Array.from({ length:  4 }, (_, i) => 97 + i),
  101, 102, 103, 104,
];

// ── CSV generators ────────────────────────────────────────────────────────────

function generateGroupResultsCsv() {
  const rows = ['match,home_score,away_score,outcome'];
  for (const [num] of MATCHES) {
    const outcome = randChoice(['W1', 'W2', 'Draw']);
    let h, a;
    if (outcome === 'W1')      { h = randInt(3) + 1; a = randInt(h); }
    else if (outcome === 'W2') { a = randInt(3) + 1; h = randInt(a); }
    else                       { const s = randInt(3); h = s; a = s; }
    rows.push(`${num},${h},${a},${outcome}`);
  }
  return rows.join('\n');
}

function generateKoResultsCsv(winners) {
  return ['match,winner', ...KO_ORDER.map(m => `${m},${winners[m]}`)].join('\n');
}

// ── Run ───────────────────────────────────────────────────────────────────────

const NAMES = ['Alice', 'Bob', 'Carol', 'Dave', 'Eve', 'Frank', 'Grace', 'Hank', 'Ivy', 'Jack'];

const localResultsCsv          = generateGroupResultsCsv();
const { winners, matchTeams }  = generateKoTournament();
const localKoResultsCsv        = generateKoResultsCsv(winners);

const localPicks   = {};
const localKoPicks = {};
const matchNums    = MATCHES.map(m => m[0]);
for (const name of NAMES) {
  localPicks[name]   = generateGroupPicks(matchNums);
  localKoPicks[name] = generateKoPicks();
}

const localBracketData = {
  confirmed: true,
  round_of_32: Object.fromEntries(
    Object.entries(R32_TEAMS).map(([m, [home, away]]) => [m, { home, away }])
  ),
};

// ── Print summary ─────────────────────────────────────────────────────────────
console.error(`Champion    : ${winners[104]}`);
console.error(`Finalist    : ${winners[101]} vs ${winners[102]}`);
console.error(`3rd place   : ${winners[103]}`);
console.error(`Participants: ${NAMES.join(', ')}`);

// ── Output JSON ───────────────────────────────────────────────────────────────
const output = { localPicks, localResultsCsv, localKoPicks, localKoResultsCsv, localBracketData };
process.stdout.write(JSON.stringify(output, null, 2));
