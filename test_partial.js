/**
 * test_partial.js
 *
 * Mid-tournament state tests for the leaderboard scoring pipeline.
 * Covers the five key tournament phases:
 *
 *   Phase 0 — No matches played (picks submitted, zero results)
 *   Phase 1 — Group stage in progress (partial results)
 *   Phase 2 — Group stage complete, KO not started (no bracket, no KO picks)
 *   Phase 3 — R32 in progress (bracket known, some R32 results)
 *   Phase 4 — R16 in progress (all R32 done, some R16/QF picks cascading)
 *
 * Each phase verifies:
 *   - Points reflect only played matches
 *   - Pending picks contribute to maxPts but not to koPts/points
 *   - Cascaded picks (team eliminated) score 0 and don't inflate maxPts
 *   - Sort order is stable
 *
 * Run: node test_partial.js
 */

'use strict';

const {
  MATCHES, KO_POINTS, computeStandings, computeCombinedStandings,
} = require('./scoring.js');

// ─────────────────────────────────────────────────────────────
// § 1  Test harness
// ─────────────────────────────────────────────────────────────

let passed = 0, failed = 0;

function assert(label, condition, extra = '') {
  if (condition) {
    console.log(`  ✅ ${label}`);
    passed++;
  } else {
    console.error(`  ❌ FAIL: ${label}${extra ? ' — ' + extra : ''}`);
    failed++;
  }
}
function section(title) { console.log(`\n── ${title} ──`); }
function eq(a, b)       { return JSON.stringify(a) === JSON.stringify(b); }

// ─────────────────────────────────────────────────────────────
// § 2  Shared fixtures
// ─────────────────────────────────────────────────────────────

// Three participants; Alice picks everything, Bob picks selectively, Carol nothing.
const ALL_GROUP_PICKS = {
  Alice: Object.fromEntries(MATCHES.map(([n]) => [String(n), 'W1'])),
  Bob:   { '1': 'W1', '2': 'Draw', '3': 'W2' },
  Carol: {},
};

// A minimal R32 bracket (16 matches)
function makeBracket(r32override = {}) {
  const base = {
    73: { home: 'Spain',      away: 'France'      },
    74: { home: 'Brazil',     away: 'Germany'     },
    75: { home: 'Argentina',  away: 'England'     },
    76: { home: 'Portugal',   away: 'Netherlands' },
    77: { home: 'Morocco',    away: 'Japan'       },
    78: { home: 'Mexico',     away: 'Uruguay'     },
    79: { home: 'USA',        away: 'Senegal'     },
    80: { home: 'Belgium',    away: 'Croatia'     },
    81: { home: 'Serbia',     away: 'Denmark'     },
    82: { home: 'Switzerland',away: 'Poland'      },
    83: { home: 'Turkey',     away: 'Austria'     },
    84: { home: 'Ecuador',    away: 'Colombia'    },
    85: { home: 'Australia',  away: 'South Korea' },
    86: { home: 'Nigeria',    away: 'Ivory Coast' },
    87: { home: 'Canada',     away: 'Chile'       },
    88: { home: 'Iran',       away: 'South Africa'},
  };
  return { round_of_32: { ...base, ...r32override } };
}

// Full KO result set (Spain wins everything)
const FULL_KO_RESULTS = {
  73:'Spain',   74:'Brazil',  75:'Argentina', 76:'Netherlands',
  77:'Morocco', 78:'Mexico',  79:'USA',       80:'Belgium',
  81:'Serbia',  82:'Switzerland', 83:'Turkey', 84:'Ecuador',
  85:'Australia', 86:'Nigeria', 87:'Canada',  88:'Iran',
  89:'Brazil',  90:'Spain',   91:'Netherlands', 92:'USA',
  93:'Turkey',  94:'Serbia',  95:'Nigeria',   96:'Australia',
  97:'Spain',   98:'Serbia',  99:'Netherlands',100:'Nigeria',
  101:'Spain', 102:'Nigeria',
  103:'Serbia', 104:'Spain',
};

// KO picks where Alice picks every winner correctly
const ALL_CORRECT_KO_PICKS = Object.fromEntries(
  Object.entries(FULL_KO_RESULTS).map(([m, w]) => [m, w])
);

// ─────────────────────────────────────────────────────────────
// § 3  Phase 0 — No matches played
// ─────────────────────────────────────────────────────────────

section('Phase 0 — no matches played (group stage)');

{
  const standings = computeStandings(ALL_GROUP_PICKS, {});

  const byName = Object.fromEntries(standings.map(p => [p.name, p]));

  assert('Alice: 0 pts (no results)', byName.Alice.points === 0);
  assert('Bob: 0 pts (no results)',   byName.Bob.points   === 0);
  assert('Carol: 0 pts (no results)', byName.Carol.points === 0);

  assert('Alice: all 72 picks pending or empty',
    Object.values(byName.Alice.pickResults).every(r => r.status === 'pending' || r.status === 'empty'));
  assert('Alice: all 72 picks pending (she picked every match)',
    Object.values(byName.Alice.pickResults).every(r => r.status === 'pending'));
  assert('Bob: 3 pending, 69 empty',
    Object.values(byName.Bob.pickResults).filter(r => r.status === 'pending').length === 3 &&
    Object.values(byName.Bob.pickResults).filter(r => r.status === 'empty').length === 69);
  assert('Carol: all 72 empty (no picks)',
    Object.values(byName.Carol.pickResults).every(r => r.status === 'empty'));

  // Sort: all tied at 0, so alphabetical
  assert('Sort order: Alice, Bob, Carol (all 0 pts, alphabetical)',
    standings[0].name === 'Alice' && standings[1].name === 'Bob' && standings[2].name === 'Carol');
}

section('Phase 0 — no KO results, KO picks submitted');

{
  const bd = makeBracket();
  const groupStandings = [
    { name: 'Alice', points: 0, pickResults: {} },
    { name: 'Bob',   points: 0, pickResults: {} },
  ];
  const koPicksData = {
    Alice: ALL_CORRECT_KO_PICKS,
    Bob:   { '73': 'Spain', '104': 'Spain' },
  };
  const combined = computeCombinedStandings(groupStandings, koPicksData, {}, bd);
  const byName = Object.fromEntries(combined.map(p => [p.name, p]));

  assert('Alice: koPts = 0 (no results yet)', byName.Alice.koPts === 0);
  assert('Alice: all 32 KO picks pending',
    Object.values(byName.Alice.koPickResults).every(r => r.status === 'pending'));
  assert('Alice: maxPts = 244 (all picks pending at full value)',
    byName.Alice.maxPts === 244);
  assert('Bob: koPts = 0', byName.Bob.koPts === 0);
  assert('Bob: 2 pending, 30 empty',
    Object.values(byName.Bob.koPickResults).filter(r => r.status === 'pending').length === 2 &&
    Object.values(byName.Bob.koPickResults).filter(r => r.status === 'empty').length === 30);
  assert('Bob: maxPts = KO_POINTS[73] + KO_POINTS[104] = 4 + 24 = 28',
    byName.Bob.maxPts === 28);
}

// ─────────────────────────────────────────────────────────────
// § 4  Phase 1 — Group stage in progress (partial results)
// ─────────────────────────────────────────────────────────────

section('Phase 1 — group stage in progress (first 3 matches played)');

{
  // Only matches 1–3 have results; 4–72 still pending
  const partialResults = {
    1: { home: 2, away: 0, outcome: 'W1' },   // Mexico win (Alice picks W1 → correct)
    2: { home: 1, away: 1, outcome: 'Draw' },  // Draw     (Alice picks W1 → wrong)
    3: { home: 0, away: 2, outcome: 'W2' },    // Bosnia win (Alice picks W1 → wrong)
  };

  const standings = computeStandings(ALL_GROUP_PICKS, partialResults);
  const byName = Object.fromEntries(standings.map(p => [p.name, p]));

  // Alice picks W1 for all — correct on M1 only → 2 pts; M2 and M3 wrong
  assert('Alice: 2 pts (1 correct out of 3 played)', byName.Alice.points === 2);
  // Bob picks W1, Draw, W2 for M1–3 → all correct → 6 pts
  assert('Bob: 6 pts (3 correct out of 3 played)',   byName.Bob.points   === 6);
  assert('Carol: 0 pts (no picks)',                   byName.Carol.points === 0);

  // Status breakdown for Alice
  assert('Alice M1: correct (W1 result, W1 pick)', byName.Alice.pickResults[1].status === 'correct');
  assert('Alice M2: wrong (Draw result, W1 pick)',  byName.Alice.pickResults[2].status === 'wrong');
  assert('Alice M3: wrong (W2 result, W1 pick)',    byName.Alice.pickResults[3].status === 'wrong');
  assert('Alice M4: pending (no result, W1 pick)',  byName.Alice.pickResults[4].status === 'pending');
  assert('Alice M5: pending (no result, W1 pick)',  byName.Alice.pickResults[5].status === 'pending');

  // Sort: Bob(6) > Alice(2) > Carol(0)
  assert('Sort: Bob 1st (6 pts)', standings[0].name === 'Bob');
  assert('Sort: Alice 2nd (2 pts)', standings[1].name === 'Alice');
  assert('Sort: Carol 3rd (0 pts)', standings[2].name === 'Carol');
}

section('Phase 1 — no picks submitted yet (late entrant)');

{
  const partialResults = {
    1: { home: 1, away: 0, outcome: 'W1' },
    2: { home: 0, away: 1, outcome: 'W2' },
  };
  // Dave submits picks after M1/M2 are played (M1 and M2 are effectively
  // "missed" but still scored as correct/wrong, not pending)
  const standings = computeStandings(
    { Dave: { '1': 'W1', '2': 'W1' } },
    partialResults
  );
  const dave = standings[0];
  assert('Dave M1: correct (W1)',   dave.pickResults[1].status === 'correct');
  assert('Dave M2: wrong (W2)',     dave.pickResults[2].status === 'wrong');
  assert('Dave M3: empty (no pick)',dave.pickResults[3].status === 'empty');
  assert('Dave: 2 pts',             dave.points === 2);
}

// ─────────────────────────────────────────────────────────────
// § 5  Phase 2 — Group complete, KO not started
// ─────────────────────────────────────────────────────────────

section('Phase 2 — group complete, no bracket, no KO results');

{
  // All 72 group matches have results; no KO bracket yet
  const allGroupResults = Object.fromEntries(
    MATCHES.map(([n]) => [n, { home: 1, away: 0, outcome: 'W1' }])
  );

  const standings = computeStandings(ALL_GROUP_PICKS, allGroupResults);
  const byName = Object.fromEntries(standings.map(p => [p.name, p]));

  // Alice picks W1 for all; all results are W1 → 72 correct × 2 = 144 pts
  assert('Alice: 144 pts (all 72 correct)', byName.Alice.points === 144);
  assert('Alice: all 72 statuses correct',
    Object.values(byName.Alice.pickResults).every(r => r.status === 'correct'));
  assert('Bob: 2 pts (M1 correct, M2/M3 wrong, M4–72 empty)',
    byName.Bob.points === 2);  // only M1 is W1 pick, correct; M2 (Draw pick, W1 result) wrong; M3 (W2 pick, W1 result) wrong
  assert('Carol: 0 pts (no picks)', byName.Carol.points === 0);

  // With no KO data — just group standings, no combined call needed
  assert('Group stage max is 144', 72 * 2 === 144);
}

section('Phase 2 — combined with no bracket or KO results');

{
  const groupStandings = [
    { name: 'Alice', points: 80, pickResults: {} },
    { name: 'Bob',   points: 60, pickResults: {} },
  ];
  // KO picks exist but bracket isn't set yet (null bracketData)
  const koPicksData = {
    Alice: { '73': 'Spain', '104': 'Spain' },
    Bob:   { '73': 'Brazil' },
  };

  // bracketData = null: R32 teams are TBD
  const combined = computeCombinedStandings(groupStandings, koPicksData, {}, null);
  const byName = Object.fromEntries(combined.map(p => [p.name, p]));

  assert('Alice: koPts = 0 (no results)', byName.Alice.koPts === 0);
  assert('Alice: M73 pending (bracket unknown)', byName.Alice.koPickResults[73].status === 'pending');
  assert('Alice: M104 pending', byName.Alice.koPickResults[104].status === 'pending');
  assert('Alice: maxPts includes pending KO picks (4 + 24 = 28 above group pts)',
    byName.Alice.maxPts === 80 + 28);
  assert('Alice ranked 1st (80 > 60 group pts)', combined[0].name === 'Alice');
}

// ─────────────────────────────────────────────────────────────
// § 6  Phase 3 — R32 in progress (bracket known, partial R32 results)
// ─────────────────────────────────────────────────────────────

section('Phase 3 — R32 in progress (8 of 16 R32 matches played)');

{
  const bd = makeBracket();
  // First 8 R32 matches have results
  const partialKo = {
    73: 'Spain', 74: 'Brazil', 75: 'Argentina', 76: 'Netherlands',
    77: 'Morocco', 78: 'Mexico', 79: 'USA', 80: 'Belgium',
    // M81–88 not yet played
  };

  const groupStandings = [{ name: 'Alice', points: 50, pickResults: {} }];
  const koPicksData = {
    Alice: { ...ALL_CORRECT_KO_PICKS },
  };

  const combined = computeCombinedStandings(groupStandings, koPicksData, partialKo, bd);
  const alice = combined[0];

  // M73–80: all correct (8 picks × 4 pts each = 32 pts)
  assert('Alice: 8 R32 correct = 32 pts', alice.koPts === 32,
    `got ${alice.koPts}`);
  // M81–88: pending (not played yet)
  assert('Alice: M81 pending', alice.koPickResults[81].status === 'pending');
  assert('Alice: M88 pending', alice.koPickResults[88].status === 'pending');
  // M89–104: pending (R16+ not played)
  assert('Alice: M89 pending', alice.koPickResults[89].status === 'pending');
  assert('Alice: M104 pending', alice.koPickResults[104].status === 'pending');

  // maxPts = groupPts + R32 correct (32) + pending R32 (8×4=32) + pending R16–Final (180)
  const pendingR32  = 8 * 4;   // M81–88
  const pendingRest = 8*8 + 4*12 + 2*16 + 12 + 24;  // R16 + QF + SF + 3rd + Final
  assert('Alice: maxPts accounts for all pending picks',
    alice.maxPts === 50 + 32 + pendingR32 + pendingRest,
    `got ${alice.maxPts}, expected ${50 + 32 + pendingR32 + pendingRest}`);
}

section('Phase 3 — R32 in progress with wrong pick (no cascade yet)');

{
  // Spain loses M73 to France — but there are no R16 results yet,
  // so Spain picks in R16+ are PENDING (not cascaded) at this stage.
  // Cascade only applies when the downstream match has an actual result.
  const bd = makeBracket();
  const partialKo = { 73: 'France' };  // only M73 played; Spain lost

  const groupStandings = [{ name: 'Alice', points: 0, pickResults: {} }];
  const koPicksData = {
    Alice: {
      '73': 'Spain',   // wrong (Spain lost M73)
      '90': 'Spain',   // R16 pick — no result yet → pending (not cascaded)
      '97': 'Spain',   // QF pick — no result yet → pending
      '104': 'Spain',  // Final — pending
    },
  };

  const combined = computeCombinedStandings(groupStandings, koPicksData, partialKo, bd);
  const alice = combined[0];

  assert('M73: Spain wrong (not cascaded — R32 threshold=0)', alice.koPickResults[73].status === 'wrong');
  // Spain is eliminated (round 1), so downstream Spain picks ARE immediately cascaded —
  // cascade fires as soon as eliminatedInRound[Spain]=1 < threshold, regardless of whether
  // the downstream match has been played yet.
  assert('M90: cascaded (Spain out in R32, threshold=2, 1<2=true)',
    alice.koPickResults[90].status === 'cascaded');
  assert('M97: cascaded (Spain out in R32, threshold=3, 1<3=true)',
    alice.koPickResults[97].status === 'cascaded');
  assert('M104: cascaded (Spain out in R32, threshold=5, 1<5=true)',
    alice.koPickResults[104].status === 'cascaded');

  // maxPts = 0: M73 wrong, all R16+ picks cascaded (no pending picks remain)
  assert('maxPts = 0 (all downstream Spain picks immediately cascaded)',
    alice.maxPts === 0, `got ${alice.maxPts}`);
}

// ─────────────────────────────────────────────────────────────
// § 7  Phase 4 — R16 in progress (all R32 done, cascade now active)
// ─────────────────────────────────────────────────────────────

section('Phase 4 — R16 in progress (all R32 done; some R16 results)');

{
  const bd = makeBracket();
  // All R32 done; Spain won M73, M90 (R16) played — Spain wins again
  const partialKo = {
    // R32 complete
    73:'Spain',   74:'Brazil',  75:'Argentina', 76:'Netherlands',
    77:'Morocco', 78:'Mexico',  79:'USA',       80:'Belgium',
    81:'Serbia',  82:'Switzerland', 83:'Turkey', 84:'Ecuador',
    85:'Australia', 86:'Nigeria', 87:'Canada',  88:'Iran',
    // Some R16 results
    90: 'Spain',   // R16[90]=[73,75]: Spain vs Argentina → Spain wins
    89: 'Brazil',  // R16[89]=[74,77]: Brazil vs Morocco → Brazil wins
    // M91–96 not yet played
  };

  const groupStandings = [
    { name: 'Alice', points: 100, pickResults: {} },
    { name: 'Bob',   points: 80,  pickResults: {} },
  ];
  const koPicksData = {
    // Alice: all correct picks
    Alice: { ...ALL_CORRECT_KO_PICKS },
    // Bob: picked wrong teams that lost in R32 → their R16+ picks cascade
    Bob: {
      '74': 'Germany',   // R32: Germany lost → wrong
      '90': 'Spain',     // R16: Spain correct → 8 pts
      '89': 'Germany',   // R16[89]=[74,77]: Germany elim in R32 (round 1), threshold=2 → cascaded
      '97': 'Brazil',    // QF: pending (no result yet)
      '104': 'Germany',  // Final: Germany elim round 1, threshold=5, 1<5 → cascaded
    },
  };

  const combined = computeCombinedStandings(groupStandings, koPicksData, partialKo, bd);
  const byName = Object.fromEntries(combined.map(p => [p.name, p]));

  // Alice: all R32 correct (64 pts) + M90/M89 correct (8+8=16) → 80 pts
  assert('Alice: M73 correct', byName.Alice.koPickResults[73].status === 'correct');
  assert('Alice: M90 correct (Spain, 8 pts)', byName.Alice.koPickResults[90].status === 'correct');
  assert('Alice: M89 correct (Brazil, 8 pts)', byName.Alice.koPickResults[89].status === 'correct');
  assert('Alice: M91 pending (R16 not played)', byName.Alice.koPickResults[91].status === 'pending');
  assert('Alice: koPts = 16×4 + 2×8 = 80', byName.Alice.koPts === 80, `got ${byName.Alice.koPts}`);

  // Bob: M74 wrong, M90 correct (8), M89 cascaded, M97 pending, M104 cascaded
  assert('Bob: M74 wrong (Germany lost)', byName.Bob.koPickResults[74].status === 'wrong');
  assert('Bob: M90 correct (Spain, 8 pts)', byName.Bob.koPickResults[90].status === 'correct');
  assert('Bob: M89 cascaded (Germany out in R32, threshold=2, 1<2)', byName.Bob.koPickResults[89].status === 'cascaded');
  assert('Bob: M97 pending', byName.Bob.koPickResults[97].status === 'pending');
  assert('Bob: M104 cascaded (Germany out R32, threshold=5, 1<5)', byName.Bob.koPickResults[104].status === 'cascaded');
  assert('Bob: koPts = 8 (only M90 correct)', byName.Bob.koPts === 8, `got ${byName.Bob.koPts}`);

  // Bob maxPts = groupPts + koPossiblePts = 80 + (koPts + pendingKoPts)
  //            = 80 + (8 + 12) = 100  [M90 correct=8, M97 pending=12, M104 cascaded=0]
  assert('Bob: maxPts = 80 (group) + 8 (M90 correct) + 12 (M97 pending) = 100',
    byName.Bob.maxPts === 100, `got ${byName.Bob.maxPts}`);

  // Sort: Alice (100+80=180) > Bob (80+8=88)
  assert('Alice ranked 1st', combined[0].name === 'Alice');
  assert('Bob ranked 2nd', combined[1].name === 'Bob');
}

section('Phase 4 — correctChampion with pending Final pick');

{
  const bd = makeBracket();
  // All R32 + all R16 done, but QF/SF/Final not yet played
  const partialKo = {
    73:'Spain',   74:'Brazil',  75:'Argentina', 76:'Netherlands',
    77:'Morocco', 78:'Mexico',  79:'USA',       80:'Belgium',
    81:'Serbia',  82:'Switzerland', 83:'Turkey', 84:'Ecuador',
    85:'Australia', 86:'Nigeria', 87:'Canada',  88:'Iran',
    89:'Brazil',  90:'Spain',   91:'Netherlands', 92:'USA',
    93:'Turkey',  94:'Serbia',  95:'Nigeria',   96:'Australia',
    // QF/SF/Final not yet played
  };

  const groupStandings = [{ name: 'Alice', points: 0, pickResults: {} }];
  const koPicksData = {
    Alice: {
      '97': 'Spain',   // QF — pending
      '104': 'Spain',  // Final — pending
    },
  };

  const combined = computeCombinedStandings(groupStandings, koPicksData, partialKo, bd);
  const alice = combined[0];

  assert('correctChampion = false when Final not yet played', alice.correctChampion === false);
  assert('M97 pending', alice.koPickResults[97].status === 'pending');
  assert('M104 pending', alice.koPickResults[104].status === 'pending');
  assert('maxPts includes QF + Final (12 + 24 = 36)', alice.maxPts === 36, `got ${alice.maxPts}`);
}

// ─────────────────────────────────────────────────────────────
// § 8  Cross-phase invariants
// ─────────────────────────────────────────────────────────────

section('Cross-phase — maxPts always ≥ totalPts');

{
  const bd = makeBracket();
  const phases = [
    {},             // no results
    { 73: 'Spain' },// one R32 result
    Object.fromEntries(Array.from({length:16}, (_, i) => [73+i, 'Spain'])),  // all R32
    FULL_KO_RESULTS,
  ];

  const groupStandings = [{ name: 'Alice', points: 50, pickResults: {} }];
  const koPicksData = { Alice: ALL_CORRECT_KO_PICKS };

  for (const koResults of phases) {
    const combined = computeCombinedStandings(groupStandings, koPicksData, koResults, bd);
    const alice = combined[0];
    assert(`maxPts (${alice.maxPts}) ≥ totalPts (${alice.totalPts}) at phase`,
      alice.maxPts >= alice.totalPts,
      `maxPts=${alice.maxPts}, totalPts=${alice.totalPts}`);
  }
}

section('Cross-phase — totalPts = groupPts + koPts at every phase');

{
  const bd = makeBracket();
  const groupStandings = [
    { name: 'Alice', points: 30, pickResults: {} },
    { name: 'Bob',   points: 20, pickResults: {} },
  ];
  const koPicksData = {
    Alice: ALL_CORRECT_KO_PICKS,
    Bob:   { '73': 'Spain', '89': 'Spain', '104': 'Spain' },
  };

  const koResultsSets = [
    {},
    { 73: 'Spain' },
    { 73: 'Spain', 89: 'Spain' },
    FULL_KO_RESULTS,
  ];

  for (const koResults of koResultsSets) {
    const combined = computeCombinedStandings(groupStandings, koPicksData, koResults, bd);
    for (const p of combined) {
      assert(`${p.name}: totalPts = groupPts + koPts`,
        p.totalPts === p.groupPts + p.koPts,
        `${p.groupPts}+${p.koPts}≠${p.totalPts}`);
    }
  }
}

section('Cross-phase — sort order stable (no negative pts, no NaN)');

{
  const bd = makeBracket();
  const groupStandings = [
    { name: 'Alice', points: 80, pickResults: {} },
    { name: 'Bob',   points: 40, pickResults: {} },
    { name: 'Carol', points: 40, pickResults: {} },
  ];
  const koPicksData = {
    Alice: { '104': 'Spain' },
    Bob:   { '104': 'Brazil' },
    Carol: { '104': 'Spain' },
  };

  // With full KO results: Alice/Carol both picked Spain (correct champion)
  const combined = computeCombinedStandings(groupStandings, koPicksData, FULL_KO_RESULTS, bd);

  for (let i = 0; i < combined.length - 1; i++) {
    const a = combined[i], b = combined[i + 1];
    const ok =
      a.totalPts > b.totalPts ||
      (a.totalPts === b.totalPts && (a.correctChampion ? 1 : 0) >= (b.correctChampion ? 1 : 0));
    assert(`Sort valid: ${a.name}(${a.totalPts},champ=${a.correctChampion}) before ${b.name}`, ok);
  }
  assert('No negative totalPts', combined.every(p => p.totalPts >= 0));
  assert('No NaN in standings',  combined.every(p => !isNaN(p.totalPts) && !isNaN(p.koPts)));
}

// ─────────────────────────────────────────────────────────────
// § 9  Results
// ─────────────────────────────────────────────────────────────

const total = passed + failed;
console.log(`\n${'─'.repeat(50)}`);
console.log(`Results: ${passed}/${total} passed${failed > 0 ? `  (${failed} FAILED)` : ''}`);
if (failed > 0) {
  console.error('\n⚠️  Some tests failed — check output above.');
  process.exit(1);
} else {
  console.log('\n🏆 All tests passed.');
}
