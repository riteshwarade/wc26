/**
 * test_e2e.js
 *
 * Full end-to-end simulation with 10 dummy participants.
 * Generates group picks + KO picks + group results + KO results,
 * runs the real leaderboard scoring pipeline, prints a ranked
 * leaderboard, and asserts structural invariants.
 *
 * Run: node test_e2e.js
 */

'use strict';

const {
  MATCHES, KO_POINTS, getKoTeams,
  computeStandings, computeCombinedStandings,
} = require('./scoring.js');

// ─────────────────────────────────────────────────────────────
// § 1  Seeded PRNG (xorshift32) — reproducible output
// ─────────────────────────────────────────────────────────────

let _seed = 20260611;
function rand() {
  _seed ^= _seed << 13;
  _seed ^= _seed >> 17;
  _seed ^= _seed << 5;
  return (_seed >>> 0) / 0xFFFFFFFF;
}
function randInt(n)   { return Math.floor(rand() * n); }
function randChoice(arr) { return arr[randInt(arr.length)]; }

// ─────────────────────────────────────────────────────────────
// § 2  Simulation constants — KO bracket topology + R32 teams
// ─────────────────────────────────────────────────────────────

// Bracket topology (used by generateKoResults/generateKoPicks)
const R16 = {
   89:[74,77],  90:[73,75],  91:[76,78],  92:[79,80],
   93:[83,84],  94:[81,82],  95:[86,88],  96:[85,87],
};
const QF = {
   97:[89,90],  98:[93,94],  99:[91,92], 100:[95,96],
};
const SF = {
  101:[97,98], 102:[99,100],
};

// R32 simulated teams (same as simulate.py — representative names only)
const R32_TEAMS = {
  73:['Brazil','Morocco'],      74:['France','Norway'],
  75:['Spain','Ecuador'],       76:['Germany','Switzerland'],
  77:['Argentina','Mexico'],    78:['Netherlands','Senegal'],
  79:['England','Ivory Coast'], 80:['Portugal','Colombia'],
  81:['Belgium','United States'], 82:['Croatia','Japan'],
  83:['South Korea','Saudi Arabia'], 84:['Uruguay','Egypt'],
  85:['Turkey','Canada'],       86:['Austria','Sweden'],
  87:['Tunisia','Ghana'],       88:['Panama','Australia'],
};

// ─────────────────────────────────────────────────────────────
// § 3  Data generation
// ─────────────────────────────────────────────────────────────

function generateGroupResults() {
  // Returns { matchNum: { home, away, outcome } } for all 72 matches
  const results = {};
  for (const [num, , , , t1, t2] of MATCHES) {
    const outcome = randChoice(['W1', 'W2', 'Draw']);
    let home, away;
    if (outcome === 'W1') { home = randInt(3) + 1; away = randInt(home); }
    else if (outcome === 'W2') { away = randInt(3) + 1; home = randInt(away); }
    else { const s = randInt(3); home = s; away = s; }
    results[num] = { home, away, outcome };
  }
  return results;
}

function generateKoResults() {
  // Simulate round-by-round knockout. Returns { matchNum: winnerName }.
  const winners = {};
  const matchTeams = { ...R32_TEAMS };

  for (const [m, [home, away]] of Object.entries(R32_TEAMS)) {
    winners[+m] = randChoice([home, away]);
  }
  for (const feeds of [R16, QF, SF]) {
    for (const [m, [f1, f2]] of Object.entries(feeds)) {
      matchTeams[+m] = [winners[f1], winners[f2]];
      winners[+m] = randChoice([winners[f1], winners[f2]]);
    }
  }
  // 3rd place: SF losers
  const [sf1h, sf1a] = matchTeams[101];
  const [sf2h, sf2a] = matchTeams[102];
  const loser101 = winners[101] === sf1h ? sf1a : sf1h;
  const loser102 = winners[102] === sf2h ? sf2a : sf2h;
  matchTeams[103] = [loser101, loser102];
  winners[103] = randChoice([loser101, loser102]);
  // Final
  matchTeams[104] = [winners[101], winners[102]];
  winners[104] = randChoice([winners[101], winners[102]]);

  return { winners, matchTeams };
}

function generateGroupPicks() {
  // Returns { '1': 'W1', '2': 'Draw', ... } for all 72 matches
  const picks = {};
  for (const [num] of MATCHES) {
    picks[String(num)] = randChoice(['W1', 'W2', 'Draw']);
  }
  return picks;
}

function generateKoPicks(koWinners, koMatchTeams) {
  // Simulate a participant who picks random winners round by round,
  // but from the actual teams in each match (not always correct).
  const picks = {};
  const myWinners = {};
  const myTeams = { ...R32_TEAMS };

  for (const [m, [home, away]] of Object.entries(R32_TEAMS)) {
    myWinners[+m] = randChoice([home, away]);
    picks[String(m)] = myWinners[+m];
  }
  for (const feeds of [R16, QF, SF]) {
    for (const [m, [f1, f2]] of Object.entries(feeds)) {
      myTeams[+m] = [myWinners[f1], myWinners[f2]];
      myWinners[+m] = randChoice([myWinners[f1], myWinners[f2]]);
      picks[String(m)] = myWinners[+m];
    }
  }
  // 3rd place: pick from participants' own SF losers (valid picks for M103)
  const [sf1h, sf1a] = myTeams[101];
  const [sf2h, sf2a] = myTeams[102];
  const loser101 = myWinners[101] === sf1h ? sf1a : sf1h;
  const loser102 = myWinners[102] === sf2h ? sf2a : sf2h;
  picks['103'] = randChoice([loser101, loser102]);
  // Final
  picks['104'] = myWinners[101] || myWinners[102];  // pick one SF winner
  return picks;
}

// ─────────────────────────────────────────────────────────────
// § 5  Test harness
// ─────────────────────────────────────────────────────────────

let passed = 0, failed = 0;
function assert(label, cond, extra='') {
  if (cond) { console.log(`  ✅ ${label}`); passed++; }
  else { console.error(`  ❌ FAIL: ${label}${extra?' — '+extra:''}`); failed++; }
}
function section(t) { console.log(`\n── ${t} ──`); }

// ─────────────────────────────────────────────────────────────
// § 6  Run the simulation
// ─────────────────────────────────────────────────────────────

const PARTICIPANT_NAMES = [
  'Alice','Bob','Carol','Dave','Eve','Frank','Grace','Hank','Ivy','Jack'
];

console.log('Generating tournament data...\n');

// Generate results (shared for all participants)
const groupResults = generateGroupResults();
const { winners: koWinners, matchTeams: koMatchTeams } = generateKoResults();

// bracketData mirrors knockout_bracket.json format
const bracketData = {
  confirmed: true,
  round_of_32: Object.fromEntries(
    Object.entries(R32_TEAMS).map(([m, [home, away]]) => [m, { home, away }])
  ),
};

// Generate each participant's picks
const allGroupPicks = {};
const allKoPicks    = {};
for (const name of PARTICIPANT_NAMES) {
  allGroupPicks[name] = generateGroupPicks();
  allKoPicks[name]    = generateKoPicks(koWinners, koMatchTeams);
}

// Print tournament summary
const champion = koWinners[104];
const third    = koWinners[103];
const finalists = [koWinners[101], koWinners[102]];
console.log(`Tournament champion  : ${champion}`);
console.log(`3rd place winner     : ${third}`);
console.log(`Finalists            : ${finalists.join(' vs ')}`);
console.log(`Group results        : ${MATCHES.length} matches simulated`);
console.log(`KO results           : 32 matches simulated\n`);

// Run scoring pipeline
const groupStandings = computeStandings(allGroupPicks, groupResults);
const combined       = computeCombinedStandings(groupStandings, allKoPicks, koWinners, bracketData);

// ─────────────────────────────────────────────────────────────
// § 7  Print leaderboard
// ─────────────────────────────────────────────────────────────

console.log('═'.repeat(72));
console.log(' FINAL LEADERBOARD (10 participants, full tournament simulated)');
console.log('═'.repeat(72));

const col = (s, w, right=false) => {
  const str = String(s);
  return right ? str.padStart(w) : str.padEnd(w);
};

console.log(
  col('#',   3) +
  col('Name', 10) +
  col('Grp', 6, true) +
  col('KO',  6, true) +
  col('Tot', 6, true) +
  col('Max', 6, true) +
  col('Champ', 7) +
  '  Group √  KO √'
);
console.log('─'.repeat(72));

let prevPts = null, rank = 1;
combined.forEach((p, i) => {
  if (p.totalPts !== prevPts) { rank = i + 1; prevPts = p.totalPts; }
  const grpCorrect = Object.values(p.pickResults).filter(r=>r.status==='correct').length;
  const koCorrect  = Object.values(p.koPickResults).filter(r=>r.status==='correct').length;
  const champMark  = p.correctChampion ? '✓' : ' ';
  console.log(
    col(rank,  3) +
    col(p.name,10) +
    col(p.groupPts, 6, true) +
    col(p.koPts,    6, true) +
    col(p.totalPts, 6, true) +
    col(p.maxPts,   6, true) +
    '  ' + col(champMark, 5) +
    '  ' + col(grpCorrect+'/72', 8) +
    '  ' + col(koCorrect+'/32', 8)
  );
});
console.log('─'.repeat(72));

// KO status breakdown across all participants
const allStatuses = combined.flatMap(p => Object.values(p.koPickResults).map(r=>r.status));
const statusCounts = allStatuses.reduce((acc,s)=>{acc[s]=(acc[s]||0)+1;return acc;},{});
console.log(`\nKO pick status across all ${combined.length} participants (${combined.length*32} total picks):`);
for (const [s,n] of Object.entries(statusCounts)) {
  console.log(`  ${s.padEnd(10)}: ${n}`);
}

// ─────────────────────────────────────────────────────────────
// § 8  Structural invariants
// ─────────────────────────────────────────────────────────────

section('Invariant checks — structure');

assert('All 10 participants in standings',
  combined.length === PARTICIPANT_NAMES.length,
  `got ${combined.length}`);

assert('All participant names present',
  PARTICIPANT_NAMES.every(n => combined.find(p => p.name === n)));

for (const p of combined) {
  assert(`${p.name}: groupPts in [0, 144]`,
    p.groupPts >= 0 && p.groupPts <= 144,
    `got ${p.groupPts}`);
  assert(`${p.name}: koPts in [0, 244]`,
    p.koPts >= 0 && p.koPts <= 244,
    `got ${p.koPts}`);
  assert(`${p.name}: totalPts = groupPts + koPts`,
    p.totalPts === p.groupPts + p.koPts,
    `${p.groupPts}+${p.koPts}=${p.groupPts+p.koPts} ≠ ${p.totalPts}`);
}

section('Invariant checks — completeness (all results provided)');

for (const p of combined) {
  const statuses = Object.values(p.koPickResults).map(r=>r.status);
  assert(`${p.name}: no 'pending' KO picks (all 32 results provided)`,
    !statuses.includes('pending'),
    `pending: ${statuses.filter(s=>s==='pending').length}`);
  assert(`${p.name}: maxPts = totalPts (no pending → no upside remaining)`,
    p.maxPts === p.totalPts,
    `maxPts=${p.maxPts}, totalPts=${p.totalPts}`);
}

section('Invariant checks — group pick completeness');

for (const p of combined) {
  const grpStatuses = Object.values(p.pickResults).map(r=>r.status);
  assert(`${p.name}: no 'pending' group picks (all 72 results provided)`,
    !grpStatuses.includes('pending'),
    `pending: ${grpStatuses.filter(s=>s==='pending').length}`);
  assert(`${p.name}: exactly 72 group pick results`,
    grpStatuses.length === 72,
    `got ${grpStatuses.length}`);
}

section('Invariant checks — sort order');

for (let i = 0; i < combined.length - 1; i++) {
  const a = combined[i], b = combined[i+1];
  const sortOk =
    a.totalPts > b.totalPts ||
    (a.totalPts === b.totalPts && (a.correctChampion ? 1:0) > (b.correctChampion ? 1:0)) ||
    (a.totalPts === b.totalPts && (a.correctChampion===b.correctChampion) && a.totalCorrect > b.totalCorrect) ||
    (a.totalPts === b.totalPts && (a.correctChampion===b.correctChampion) && a.totalCorrect === b.totalCorrect && a.name <= b.name);
  assert(`Sort order valid: ${a.name}(${a.totalPts}) before ${b.name}(${b.totalPts})`, sortOk);
}

section('Invariant checks — cascade consistency');

for (const p of combined) {
  // A 'cascaded' pick must score 0 (not contribute to koPts)
  // We verify: if we zero out cascaded and recompute, koPts is unchanged.
  // Easier: verify correct picks actually contributed their points.
  let recomputedKo = 0;
  for (const [mStr, pr] of Object.entries(p.koPickResults)) {
    if (pr.status === 'correct') recomputedKo += KO_POINTS[+mStr] || 0;
  }
  assert(`${p.name}: koPts matches sum of correct KO picks`,
    recomputedKo === p.koPts,
    `recomputed=${recomputedKo}, stored=${p.koPts}`);
}

section('Invariant checks — correctChampion consistency');

for (const p of combined) {
  const m104pick = allKoPicks[p.name]?.['104'];
  const expectedChampion = m104pick === champion;
  // correctChampion is true iff their M104 pick equals the actual champion
  // BUT only if the pick was not cascaded
  const m104status = p.koPickResults[104]?.status;
  const isCorrectFinal = m104status === 'correct';
  assert(`${p.name}: correctChampion consistent with M104 pick status`,
    p.correctChampion === isCorrectFinal,
    `correctChampion=${p.correctChampion}, m104status=${m104status}, pick=${m104pick}, winner=${champion}`);
}

section('Invariant checks — point range sanity');

const totalGroupPts = combined.reduce((s,p) => s+p.groupPts, 0);
const totalKoPts    = combined.reduce((s,p) => s+p.koPts, 0);
const maxGroupPts   = PARTICIPANT_NAMES.length * 144;
const maxKoPts      = PARTICIPANT_NAMES.length * 244;

assert('Total group pts across all players ≤ max possible (10 × 144)',
  totalGroupPts <= maxGroupPts,
  `${totalGroupPts} > ${maxGroupPts}`);
assert('Total KO pts across all players ≤ max possible (10 × 244)',
  totalKoPts <= maxKoPts,
  `${totalKoPts} > ${maxKoPts}`);
assert('At least one correct group pick across all players',
  combined.some(p => Object.values(p.pickResults).some(r => r.status==='correct')));
assert('At least one correct KO pick across all players',
  combined.some(p => Object.values(p.koPickResults).some(r => r.status==='correct')));

// ─────────────────────────────────────────────────────────────
// § 9  Results
// ─────────────────────────────────────────────────────────────

const total = passed + failed;
console.log(`\n${'═'.repeat(72)}`);
console.log(`Invariant checks: ${passed}/${total} passed${failed>0?`  (${failed} FAILED)`:''}`);
if (failed > 0) {
  console.error('\n⚠️  Some invariants failed — check output above.');
  process.exit(1);
} else {
  console.log('\n🏆 All invariants passed.');
}
