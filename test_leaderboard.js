/**
 * test_leaderboard.js
 *
 * End-to-end tests for leaderboard scoring calculations.
 * Imports scoring functions from scoring.js (the shared module).
 *
 * Run: node test_leaderboard.js
 */

'use strict';

const {
  KO_POINTS, parseKoResults, getKoTeams,
  computeStandings, computeCombinedStandings,
} = require('./scoring.js');

// ─────────────────────────────────────────────────────────────
// § 4  Test harness
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

function eq(a, b) { return JSON.stringify(a) === JSON.stringify(b); }

function section(title) { console.log(`\n── ${title} ──`); }

// ─────────────────────────────────────────────────────────────
// § 5  Fixtures
// ─────────────────────────────────────────────────────────────

// Six group results for our 6-match MATCHES stub.
// Format: { matchNum: { home, away, outcome } }
const SIX_RESULTS = {
  1: { home:2, away:1, outcome:'W1'   },  // Mexico win
  2: { home:1, away:1, outcome:'Draw' },  // Draw
  3: { home:0, away:2, outcome:'W2'   },  // Bosnia win
  4: { home:3, away:0, outcome:'W1'   },  // Qatar win
  5: { home:2, away:0, outcome:'W1'   },  // Brazil win
  6: { home:1, away:2, outcome:'W2'   },  // Scotland win
};

// Minimal R32 bracket — just the 16 matches we need for KO tests.
// Uses real team names so cascade logic has something to work with.
function makeBracket(r32override = {}) {
  const base = {
    73: { home: 'Spain',     away: 'France'   },
    74: { home: 'Brazil',    away: 'Germany'  },
    75: { home: 'Argentina', away: 'England'  },
    76: { home: 'Portugal',  away: 'Netherlands' },
    77: { home: 'Morocco',   away: 'Japan'    },
    78: { home: 'Mexico',    away: 'Uruguay'  },
    79: { home: 'USA',       away: 'Senegal'  },
    80: { home: 'Belgium',   away: 'Croatia'  },
    81: { home: 'Serbia',    away: 'Denmark'  },
    82: { home: 'Switzerland', away: 'Poland' },
    83: { home: 'Turkey',    away: 'Austria'  },
    84: { home: 'Ecuador',   away: 'Colombia' },
    85: { home: 'Australia', away: 'South Korea' },
    86: { home: 'Nigeria',   away: 'Ivory Coast' },
    87: { home: 'Canada',    away: 'Chile'    },
    88: { home: 'Iran',      away: 'South Africa' },
  };
  return { round_of_32: { ...base, ...r32override } };
}

// ─────────────────────────────────────────────────────────────
// § 6  GROUP STAGE SCORING
// ─────────────────────────────────────────────────────────────

section('Group stage — basic scoring');

{
  const picksData = {
    Alice: { '1':'W1', '2':'Draw', '3':'W2', '4':'W1', '5':'W1', '6':'W2' },  // all correct
    Bob:   { '1':'W2', '2':'W1',   '3':'W1', '4':'W2', '5':'W2', '6':'W1' },  // all wrong
    Carol: { '1':'W1', '2':'W1',   '3':'W2'  },                                // 3 results available, 2 correct, 1 wrong + 3 pending
    Dave:  {},                                                                   // no picks
  };
  const standings = computeStandings(picksData, SIX_RESULTS);
  const byName = Object.fromEntries(standings.map(p => [p.name, p]));

  assert('Alice scores 12 pts (6 correct × 2)', byName.Alice.points === 12);
  assert('Bob scores 0 pts (6 wrong)', byName.Bob.points === 0);
  assert('Carol scores 4 pts (2 correct × 2, 1 wrong)', byName.Carol.points === 4);
  assert('Dave scores 0 pts (no picks)', byName.Dave.points === 0);

  // scoring.js uses all 72 MATCHES; picks for matches 7–72 are 'empty' for these players
  assert('Alice: matches 1–6 all correct',
    [1,2,3,4,5,6].every(n => byName.Alice.pickResults[n].status === 'correct'));
  assert('Bob: matches 1–6 all wrong',
    [1,2,3,4,5,6].every(n => byName.Bob.pickResults[n].status === 'wrong'));

  const carolStatuses = Object.values(byName.Carol.pickResults).map(r => r.status);
  assert('Carol: 2 correct, 1 wrong, rest empty',
    carolStatuses.filter(s => s === 'correct').length === 2 &&
    carolStatuses.filter(s => s === 'wrong').length === 1 &&
    carolStatuses.filter(s => s === 'empty').length === carolStatuses.length - 3
  );
}

section('Group stage — sort order');

{
  const picksData = {
    Zara:  { '1':'W1', '2':'Draw' },  // 4 pts
    Alice: { '1':'W1', '2':'Draw' },  // 4 pts (tie with Zara → alphabetical)
    Bob:   { '1':'W1' },              // 2 pts
  };
  const standings = computeStandings(picksData, SIX_RESULTS);
  assert('Tied players sorted alphabetically (Alice before Zara)', standings[0].name === 'Alice' && standings[1].name === 'Zara');
  assert('Bob ranked last with 2 pts', standings[2].name === 'Bob' && standings[2].points === 2);
}

section('Group stage — pending picks');

{
  const partialResults = { 1: { home:2, away:1, outcome:'W1' } };
  const picksData = { Alice: { '1':'W1', '2':'Draw', '3':'W2' } };
  const standings = computeStandings(picksData, partialResults);
  const alice = standings[0];
  assert('Alice: 1 correct, 2 pending, 3 empty',
    alice.pickResults[1].status === 'correct' &&
    alice.pickResults[2].status === 'pending' &&
    alice.pickResults[3].status === 'pending' &&
    alice.pickResults[4].status === 'empty'
  );
  assert('Alice: 2 pts (only 1 result available)', alice.points === 2);
}

// ─────────────────────────────────────────────────────────────
// § 7  parseKoResults CSV
// ─────────────────────────────────────────────────────────────

section('parseKoResults — CSV parsing');

{
  const csv = `match,winner\n73,Spain\n89,France\n97,Brazil\n104,Brazil`;
  const r = parseKoResults(csv);
  assert('M73 winner parsed', r[73] === 'Spain');
  assert('M89 winner parsed', r[89] === 'France');
  assert('M104 winner parsed', r[104] === 'Brazil');
  assert('4 entries total', Object.keys(r).length === 4);
}

{
  assert('Empty CSV → empty object', eq(parseKoResults(''), {}));
  assert('Header-only CSV → empty object', eq(parseKoResults('match,winner\n'), {}));
}

{
  const csv = `match,winner\n73,Spain\n\n89,France\n`;  // trailing blank line
  const r = parseKoResults(csv);
  assert('Trailing blank lines ignored', Object.keys(r).length === 2);
}

// ─────────────────────────────────────────────────────────────
// § 8  getKoTeams — team name resolution
// ─────────────────────────────────────────────────────────────

section('getKoTeams — bracket resolution');

{
  const bd = makeBracket();
  const noResults = {};

  // R32 from bracketData
  assert('M73 teams from bracketData', eq(getKoTeams(73, bd, noResults), ['Spain', 'France']));
  assert('M88 teams from bracketData', eq(getKoTeams(88, bd, noResults), ['Iran', 'South Africa']));

  // R16 before R32 results available
  const [h, a] = getKoTeams(89, bd, noResults);  // R16[89] = [74,77]
  assert('M89 before results: W74 and W77 placeholders', h === 'W74' && a === 'W77');

  // R16 with R32 results
  const r32Results = { 74:'Brazil', 77:'Morocco' };
  assert('M89 after R32: Brazil vs Morocco', eq(getKoTeams(89, bd, r32Results), ['Brazil', 'Morocco']));

  // QF — chain through R16
  const r32r16 = { 74:'Brazil', 77:'Morocco', 73:'Spain', 75:'Argentina',
                    89:'Brazil', 90:'Spain' };
  const [qfH, qfA] = getKoTeams(97, bd, r32r16);  // QF[97] = [89,90]
  assert('M97 (QF) resolves to W89/W90 winners', qfH === 'Brazil' && qfA === 'Spain');

  // SF
  const sfResults = { ...r32r16, 97:'Brazil', 98:'England',
                       99:'Netherlands', 100:'France' };
  assert('M101 (SF) teams: Brazil vs England', eq(getKoTeams(101, bd, sfResults), ['Brazil', 'England']));

  // 3rd place: losers of M101 and M102
  const finalResults = { ...sfResults, 101:'Brazil', 102:'France' };
  assert('M103 (3rd) teams: England and Netherlands (SF losers)',
    eq(getKoTeams(103, bd, finalResults), ['England', 'Netherlands']));

  // Final: winners of M101 and M102
  assert('M104 (Final) teams: Brazil and France',
    eq(getKoTeams(104, bd, finalResults), ['Brazil', 'France']));

  // No bracketData → TBD
  assert('M73 with no bracketData → TBD', eq(getKoTeams(73, null, noResults), ['TBD', 'TBD']));
}

// ─────────────────────────────────────────────────────────────
// § 9  KO SCORING — correct, wrong, empty
// ─────────────────────────────────────────────────────────────

section('KO scoring — correct picks per round');

{
  const bd = makeBracket();
  // Complete results for all 32 matches (Spain wins the tournament)
  const koResults = {
    // R32
    73:'Spain',  74:'Brazil',  75:'Argentina', 76:'Netherlands',
    77:'Morocco', 78:'Mexico', 79:'USA',       80:'Belgium',
    81:'Serbia', 82:'Switzerland', 83:'Turkey', 84:'Ecuador',
    85:'Australia', 86:'Nigeria', 87:'Canada', 88:'Iran',
    // R16: winners of pairs per R16 topology
    89:'Brazil',   90:'Spain',  91:'Netherlands', 92:'USA',
    93:'Turkey',   94:'Serbia', 95:'Nigeria',     96:'Australia',
    // QF
    97:'Spain',   98:'Serbia',  99:'Netherlands', 100:'Nigeria',
    // SF
    101:'Spain',  102:'Nigeria',
    // 3rd + Final
    103:'Serbia', 104:'Spain',
  };

  const groupStandings = [{ name:'Alice', points:10, pickResults:{} }];

  // Alice picks every correct winner
  const koPicksData = { Alice: {} };
  Object.entries(koResults).forEach(([m, w]) => koPicksData.Alice[m] = w);

  const combined = computeCombinedStandings(groupStandings, koPicksData, koResults, bd);
  const alice = combined[0];

  const maxKo = 16*4 + 8*8 + 4*12 + 2*16 + 12 + 24;  // 244
  assert('All KO correct: koPts = 244', alice.koPts === maxKo, `got ${alice.koPts}`);
  assert('Total pts = 10 + 244 = 254', alice.totalPts === 254);
  assert('correctChampion = true (Spain picked for M104)', alice.correctChampion === true);
  assert('maxPts = totalPts (no pending)', alice.maxPts === alice.totalPts);
  assert('All KO statuses correct',
    Object.values(alice.koPickResults).every(r => r.status === 'correct'));
}

{
  section('KO scoring — individual round point values');
  const bd = makeBracket();
  const koResults = {
    73:'Spain', 74:'Brazil',
    89:'Brazil',  // R16 win
    97:'Brazil',  // QF win
    101:'Brazil', // SF win
    104:'Brazil', // Final win
    103:'Spain',  // 3rd place
  };
  const groupStandings = [{ name:'Alice', points:0, pickResults:{} }];

  // Alice only picks the played matches correctly
  const koPicksData = { Alice: {
    '73':'Spain',   // R32 correct → 4 pts
    '74':'Brazil',  // R32 correct → 4 pts
    '89':'Brazil',  // R16 correct → 8 pts
    '97':'Brazil',  // QF correct  → 12 pts
    '101':'Brazil', // SF correct  → 16 pts
    '104':'Brazil', // Final correct → 24 pts
    '103':'Spain',  // 3rd correct  → 12 pts
  }};

  const combined = computeCombinedStandings(groupStandings, koPicksData, koResults, bd);
  const alice = combined[0];
  assert('R32 (2 matches): 8 pts', alice.koPickResults[73].status === 'correct' && alice.koPickResults[74].status === 'correct');
  assert('R16 (1 match): 8 pts', alice.koPickResults[89].status === 'correct');
  assert('QF (1 match): 12 pts', alice.koPickResults[97].status === 'correct');
  assert('SF (1 match): 16 pts', alice.koPickResults[101].status === 'correct');
  assert('Final (1 match): 24 pts', alice.koPickResults[104].status === 'correct');
  assert('3rd place (1 match): 12 pts', alice.koPickResults[103].status === 'correct');
  assert('Total ko pts = 4+4+8+12+16+12+24 = 80', alice.koPts === 80, `got ${alice.koPts}`);
}

// ─────────────────────────────────────────────────────────────
// § 10  CASCADE RULES
// ─────────────────────────────────────────────────────────────

section('Cascade — R32 loser voids all downstream picks');

{
  const bd = makeBracket();
  // Spain loses in R32 (M73), France wins
  const koResults = {
    73:'France',  74:'Brazil',   75:'Argentina', 76:'Netherlands',
    77:'Morocco', 78:'Mexico',   79:'USA',       80:'Belgium',
    81:'Serbia',  82:'Switzerland', 83:'Turkey', 84:'Ecuador',
    85:'Australia', 86:'Nigeria', 87:'Canada',  88:'Iran',
    89:'Brazil',  90:'France',   91:'Netherlands', 92:'USA',
    93:'Turkey',  94:'Serbia',   95:'Nigeria',  96:'Australia',
    97:'France',  98:'Serbia',   99:'Netherlands', 100:'Nigeria',
    101:'France', 102:'Nigeria',
    103:'Serbia', 104:'France',
  };

  const groupStandings = [{ name:'Alice', points:0, pickResults:{} }];

  // Alice picked Spain to win everything (Spain eliminated in R32)
  const koPicksData = { Alice: {
    '73':'Spain',   // R32: Spain loses → wrong (NOT cascaded — R32 threshold=0)
    '90':'Spain',   // R16 M90 involves W73 winner. Spain lost M73 so wasn't in M90. Cascaded.
    '97':'Spain',   // QF. Spain didn't reach QF. Cascaded.
    '101':'Spain',  // SF. Cascaded.
    '104':'Spain',  // Final. Cascaded.
  }};

  const combined = computeCombinedStandings(groupStandings, koPicksData, koResults, bd);
  const alice = combined[0];

  assert('M73 (R32): Spain picked, Spain lost → wrong (not cascaded)',
    alice.koPickResults[73].status === 'wrong');
  assert('M90 (R16): Spain pick cascaded (Spain out in R32, threshold=2, elim=1)',
    alice.koPickResults[90].status === 'cascaded');
  assert('M97 (QF): Spain pick cascaded',
    alice.koPickResults[97].status === 'cascaded');
  assert('M101 (SF): Spain pick cascaded',
    alice.koPickResults[101].status === 'cascaded');
  assert('M104 (Final): Spain pick cascaded',
    alice.koPickResults[104].status === 'cascaded');
  assert('0 KO points when all downstream picks cascaded', alice.koPts === 0);
  assert('correctChampion = false', alice.correctChampion === false);
}

section('Cascade — R16 loser voids QF/SF/Final but not R32');

{
  const bd = makeBracket();
  // Brazil wins R32 (M74) but loses R16 (M89) to Morocco.
  // M89 teams = [M74 winner, M77 winner] = [Brazil, Morocco].
  // Setting 89:'Morocco' means Brazil loses M89 → eliminatedInRound['Brazil'] = 2.
  const koResults = {
    73:'Spain',   74:'Brazil',   75:'Argentina', 76:'Netherlands',
    77:'Morocco', 78:'Mexico',   79:'USA',       80:'Belgium',
    81:'Serbia',  82:'Switzerland', 83:'Turkey', 84:'Ecuador',
    85:'Australia', 86:'Nigeria', 87:'Canada',  88:'Iran',
    89:'Morocco', // Brazil loses R16 (M89 = Brazil vs Morocco; Morocco wins)
    90:'Spain',   91:'Netherlands', 92:'USA',
    93:'Turkey',  94:'Serbia',   95:'Nigeria',  96:'Australia',
    97:'Spain',   98:'Serbia',   99:'Netherlands', 100:'Nigeria',
    101:'Spain',  102:'Nigeria',
    103:'Serbia', 104:'Spain',
  };

  const groupStandings = [{ name:'Bob', points:6, pickResults:{} }];
  const koPicksData = { Bob: {
    '74':'Brazil',  // R32 correct (Brazil won M74) → 4 pts
    '89':'Brazil',  // R16 Brazil lost → wrong (not cascaded — threshold=2, elim=2 is NOT < 2)
    '97':'Brazil',  // QF cascaded (Brazil out in R16, elim=2, threshold=3, 2 < 3)
    '101':'Brazil', // SF cascaded
    '104':'Brazil', // Final cascaded
  }};

  const combined = computeCombinedStandings(groupStandings, koPicksData, koResults, bd);
  const bob = combined[0];

  assert('M74 (R32): Brazil correct → 4 pts', bob.koPickResults[74].status === 'correct');
  assert('M89 (R16): Brazil wrong (lost R16, not cascaded)', bob.koPickResults[89].status === 'wrong');
  assert('M97 (QF): Brazil cascaded (out in R16)', bob.koPickResults[97].status === 'cascaded');
  assert('M101 (SF): Brazil cascaded', bob.koPickResults[101].status === 'cascaded');
  assert('M104 (Final): Brazil cascaded', bob.koPickResults[104].status === 'cascaded');
  assert('koPts = 4 (only R32 correct)', bob.koPts === 4, `got ${bob.koPts}`);
}

section('Cascade — M103 (3rd place): SF losers ARE valid picks');

{
  // Serbia's path: M81 (R32) → M94 (R16, feeders 81+82) → M98 (QF, feeders 93+94)
  //               → M101 (SF, feeders 97+98) — loses to Spain → plays M103 (3rd place)
  //
  // Why Serbia (not Germany): Germany appears in both M74 AND M81 of the default bracket,
  // so it gets registered as eliminated in round 1 (M74 loser) before round 4 (SF loser).
  // Serbia appears ONLY in M81 in the default bracket, so its path is unambiguous.
  //
  // Bracket topology:  R16[94]=[81,82]  QF[98]=[93,94]  SF[101]=[97,98]
  // Spain's path:      M73 → M90 → M97 → M101 (wins SF)
  //
  // eliminatedInRound['Serbia'] = matchRound(101) = 4
  // M103 cascadeThreshold = 4 → 4 < 4 = FALSE → Serbia pick NOT cascaded (SF loser IS valid)
  // M104 cascadeThreshold = 5 → 4 < 5 = TRUE  → Serbia pick cascaded (didn't win SF)

  const bd = makeBracket();  // default bracket — Serbia in M81 vs Denmark

  const koResults = {
    // R32
    73:'Spain',   74:'Brazil',  75:'Argentina', 76:'Netherlands',
    77:'Morocco', 78:'Mexico',  79:'USA',       80:'Belgium',
    81:'Serbia',  82:'Switzerland', 83:'Turkey', 84:'Ecuador',
    85:'Australia', 86:'Nigeria', 87:'Canada',  88:'Iran',
    // R16
    90:'Spain',   // Spain beats Argentina (M73 winner vs M75 winner, R16[90]=[73,75])
    94:'Serbia',  // Serbia beats Switzerland (M81 winner vs M82 winner, R16[94]=[81,82])
    // QF (M98=[93,94]; M93 unset → 'W93' placeholder for the other side)
    97:'Spain',
    98:'Serbia',  // Serbia beats W93 winner
    // SF
    101:'Spain',  // Spain beats Serbia → Serbia eliminated round 4
    102:'France',
    // 3rd + Final
    103:'Serbia', // Serbia wins 3rd place
    104:'Spain',
  };

  const groupStandings = [{ name:'Carol', points:0, pickResults:{} }];
  const koPicksData = { Carol: {
    '81':'Serbia',   // R32 correct (Serbia wins M81) → 4 pts
    '103':'Serbia',  // 3rd place: Serbia is SF loser (round 4), threshold=4, elim=4, 4<4=FALSE → valid!
    '104':'Serbia',  // Final: Serbia eliminated in SF (round 4), threshold=5, elim=4 < 5 → CASCADED
  }};

  const combined = computeCombinedStandings(groupStandings, koPicksData, koResults, bd);
  const carol = combined[0];

  assert('M81: Serbia correct → 4 pts', carol.koPickResults[81].status === 'correct');
  assert('M103: Serbia (SF loser) is a VALID pick — not cascaded',
    carol.koPickResults[103].status === 'correct');
  assert('M104: Serbia cascaded (lost SF, cannot reach Final)',
    carol.koPickResults[104].status === 'cascaded');
  assert('koPts = 4 (R32) + 12 (3rd correct) = 16', carol.koPts === 16, `got ${carol.koPts}`);
}

// ─────────────────────────────────────────────────────────────
// § 11  MAX PTS CALCULATION
// ─────────────────────────────────────────────────────────────

section('Max pts — pending picks counted at full value');

{
  const bd = makeBracket();
  // Only R32 results are known
  const koResults = {
    73:'Spain', 74:'Brazil', 75:'Argentina', 76:'Netherlands',
    77:'Morocco', 78:'Mexico', 79:'USA', 80:'Belgium',
    81:'Serbia', 82:'Switzerland', 83:'Turkey', 84:'Ecuador',
    85:'Australia', 86:'Nigeria', 87:'Canada', 88:'Iran',
  };

  const groupStandings = [{ name:'Alice', points:20, pickResults:{} }];
  const koPicksData = { Alice: {
    // All R32 picks correct
    '73':'Spain', '74':'Brazil', '75':'Argentina', '76':'Netherlands',
    '77':'Morocco', '78':'Mexico', '79':'USA', '80':'Belgium',
    '81':'Serbia', '82':'Switzerland', '83':'Turkey', '84':'Ecuador',
    '85':'Australia', '86':'Nigeria', '87':'Canada', '88':'Iran',
    // R16+ picks (all pending since no R16 results yet)
    '89':'Brazil', '90':'Spain', '91':'Netherlands', '92':'USA',
    '93':'Turkey', '94':'Serbia', '95':'Nigeria', '96':'Australia',
    '97':'Spain', '98':'Serbia', '99':'Netherlands', '100':'Nigeria',
    '101':'Spain', '102':'Nigeria', '103':'Serbia', '104':'Spain',
  }};

  const combined = computeCombinedStandings(groupStandings, koPicksData, koResults, bd);
  const alice = combined[0];

  const r32Pts = 16 * 4;   // 64 — all 16 R32 picks correct
  const r16Pts = 8 * 8;    // 64 — pending
  const qfPts  = 4 * 12;   // 48 — pending
  const sfPts  = 2 * 16;   // 32 — pending
  const thirdPts = 12;     // pending
  const finalPts = 24;     // pending
  const pendingKo = r16Pts + qfPts + sfPts + thirdPts + finalPts;  // 180

  assert('R32 pts = 64 (all correct)', alice.koPts === r32Pts, `got ${alice.koPts}`);
  assert('maxPts = groupPts + r32Pts + pendingKo',
    alice.maxPts === 20 + r32Pts + pendingKo,
    `got ${alice.maxPts}, expected ${20 + r32Pts + pendingKo}`);
  assert('16 R32 picks correct, 16 R16+ picks pending',
    Object.values(alice.koPickResults).filter(r => r.status === 'correct').length === 16 &&
    Object.values(alice.koPickResults).filter(r => r.status === 'pending').length === 16
  );
}

section('Max pts — cascaded picks excluded from max');

{
  const bd = makeBracket();
  // Spain loses R32 M73 → Alice's R16/QF/SF/Final picks for Spain cascade
  const koResults = {
    73:'France',  74:'Brazil',  75:'Argentina', 76:'Netherlands',
    77:'Morocco', 78:'Mexico',  79:'USA',       80:'Belgium',
    81:'Serbia',  82:'Switzerland', 83:'Turkey', 84:'Ecuador',
    85:'Australia', 86:'Nigeria', 87:'Canada',  88:'Iran',
    // No R16+ results yet
  };

  const groupStandings = [{ name:'Alice', points:0, pickResults:{} }];
  const koPicksData = { Alice: {
    '73':'Spain',   // wrong (Spain lost)
    '90':'Spain',   // cascaded (Spain out in R32) — NOT pending
    '97':'Spain',   // cascaded
    '104':'Spain',  // cascaded
    '74':'Brazil',  // correct → 4 pts
    '89':'Brazil',  // pending (R16 not played yet) → adds to max pts
  }};

  const combined = computeCombinedStandings(groupStandings, koPicksData, koResults, bd);
  const alice = combined[0];

  assert('M73 wrong, M74 correct (4 pts), M89 pending', alice.koPts === 4);
  assert('Cascaded picks do NOT contribute to maxPts',
    alice.maxPts === 4 + 8,  // koPts + M89 pending (8)
    `got ${alice.maxPts}`);
  assert('M90 cascaded status', alice.koPickResults[90].status === 'cascaded');
  assert('M89 pending status', alice.koPickResults[89].status === 'pending');
}

// ─────────────────────────────────────────────────────────────
// § 12  TIEBREAKER SORT ORDER
// ─────────────────────────────────────────────────────────────

section('Tiebreaker — totalPts → correctChampion → totalCorrect → groupPts → name');

{
  const bd = makeBracket();
  const koResults = {
    73:'Spain', 74:'Brazil', 75:'Argentina', 76:'Netherlands',
    77:'Morocco', 78:'Mexico', 79:'USA', 80:'Belgium',
    81:'Serbia', 82:'Switzerland', 83:'Turkey', 84:'Ecuador',
    85:'Australia', 86:'Nigeria', 87:'Canada', 88:'Iran',
    89:'Brazil', 90:'Spain', 91:'Netherlands', 92:'USA',
    93:'Turkey', 94:'Serbia', 95:'Nigeria', 96:'Australia',
    97:'Spain', 98:'Serbia', 99:'Netherlands', 100:'Nigeria',
    101:'Spain', 102:'Nigeria', 103:'Serbia', 104:'Spain',
  };

  // All four players have 0 group pts; differ only on KO
  const groupStandings = [
    { name:'Alice', points:0, pickResults:{} },
    { name:'Bob',   points:0, pickResults:{} },
    { name:'Carol', points:0, pickResults:{} },
    { name:'Dave',  points:0, pickResults:{} },
  ];

  const koPicksData = {
    // Alice: 8 pts total, got champion right (Spain M104), 2 correct picks
    Alice: { '73':'Spain', '74':'Brazil', '104':'Spain' },
    // Bob: 8 pts total, did NOT get champion, 2 correct picks
    Bob:   { '73':'Spain', '74':'Brazil', '104':'Brazil' },
    // Carol: 8 pts total, did NOT get champion, 3 correct picks (tiebreak vs Bob)
    Carol: { '73':'Spain', '74':'Brazil', '90':'Spain', '104':'Brazil' },
    // Dave: 4 pts total (only 1 correct)
    Dave:  { '73':'Spain', '104':'Brazil' },
  };

  const combined = computeCombinedStandings(groupStandings, koPicksData, koResults, bd);
  const names = combined.map(p => p.name);

  assert('Alice ranked 1st (tied pts, has champion)', names[0] === 'Alice',
    `got ${names[0]}`);
  assert('Carol ranked 2nd (tied pts, no champion, more correct picks than Bob)', names[1] === 'Carol',
    `got ${names[1]}`);
  assert('Bob ranked 3rd (tied pts, no champion, fewer correct picks than Carol)', names[2] === 'Bob',
    `got ${names[2]}`);
  assert('Dave ranked 4th (fewest pts)', names[3] === 'Dave',
    `got ${names[3]}`);
}

section('Tiebreaker — most group points (new 4th tiebreak, before name)');

{
  const bd = makeBracket();
  const koResults = {
    73:'Spain', 74:'Brazil', 75:'Argentina', 76:'Netherlands',
    77:'Morocco', 78:'Mexico', 79:'USA', 80:'Belgium',
    81:'Serbia', 82:'Switzerland', 83:'Turkey', 84:'Ecuador',
    85:'Australia', 86:'Nigeria', 87:'Canada', 88:'Iran',
    89:'Brazil', 90:'Spain', 91:'Netherlands', 92:'USA',
    93:'Turkey', 94:'Serbia', 95:'Nigeria', 96:'Australia',
    97:'Spain', 98:'Serbia', 99:'Netherlands', 100:'Nigeria',
    101:'Spain', 102:'Nigeria', 103:'Serbia', 104:'Spain',
  };

  // Eve and Frank tie on totalPts (22), correctChampion (both false), and
  // totalCorrect (both 1 correct pick) — only groupPts differs. Under the
  // old 3-level tiebreak this would fall straight to name (Eve < Frank
  // alphabetically); the new 4th tiebreak should rank Frank first instead
  // since his group score is higher.
  const groupStandings = [
    { name:'Eve',   points:14, pickResults:{} },  // 14 groupPts + 8 koPts (M89, R16) = 22
    { name:'Frank', points:18, pickResults:{} },  // 18 groupPts + 4 koPts (M73, R32) = 22
  ];
  const koPicksData = {
    Eve:   { '89':'Brazil' },
    Frank: { '73':'Spain' },
  };

  const combined = computeCombinedStandings(groupStandings, koPicksData, koResults, bd);
  const names = combined.map(p => p.name);

  assert('Eve and Frank tied on totalPts', combined[0].totalPts === combined[1].totalPts,
    `got ${combined[0].totalPts} vs ${combined[1].totalPts}`);
  assert('Frank ranked 1st (higher groupPts breaks the tie)', names[0] === 'Frank',
    `got ${names[0]}`);
  assert('Eve ranked 2nd', names[1] === 'Eve',
    `got ${names[1]}`);
}

section('Tiebreaker — alphabetical as final tiebreak');

{
  const bd = makeBracket();
  const koResults = { 73:'Spain', 74:'Brazil' };
  const groupStandings = [
    { name:'Zara',  points:4, pickResults:{} },
    { name:'Alice', points:4, pickResults:{} },
    { name:'Mike',  points:4, pickResults:{} },
  ];
  const koPicksData = {
    // All have same total pts, no champion pick, same correct count → sort by name
    Zara:  { '73':'Spain', '74':'Brazil' },  // 8 KO pts
    Alice: { '73':'Spain', '74':'Brazil' },  // 8 KO pts
    Mike:  { '73':'Spain', '74':'Brazil' },  // 8 KO pts
  };

  const combined = computeCombinedStandings(groupStandings, koPicksData, koResults, bd);
  const names = combined.map(p => p.name);
  assert('Alphabetical: Alice, Mike, Zara',
    names[0] === 'Alice' && names[1] === 'Mike' && names[2] === 'Zara',
    `got ${names.join(', ')}`);
}

// ─────────────────────────────────────────────────────────────
// § 13  KO-ONLY PARTICIPANTS (no group picks)
// ─────────────────────────────────────────────────────────────

section('KO-only participant — not in group standings');

{
  const bd = makeBracket();
  const koResults = { 73:'Spain', 74:'Brazil' };
  const groupStandings = [{ name:'Alice', points:10, pickResults:{} }];

  // Eve submitted KO picks but no group picks (not in groupStandings)
  const koPicksData = {
    Alice: { '73':'Spain' },   // 4 pts
    Eve:   { '73':'Spain', '74':'Brazil' },  // 8 pts, but 0 group pts → 8 total
  };

  const combined = computeCombinedStandings(groupStandings, koPicksData, koResults, bd);
  const byName = Object.fromEntries(combined.map(p => [p.name, p]));

  assert('Eve appears in standings despite no group picks', 'Eve' in byName);
  assert('Eve: groupPts=0, koPts=8, totalPts=8', byName.Eve.groupPts === 0 && byName.Eve.koPts === 8);
  assert('Alice: totalPts=14 (10 group + 4 ko)', byName.Alice.totalPts === 14);
  assert('Alice ranked 1st (14 > 8)', combined[0].name === 'Alice');
}

// ─────────────────────────────────────────────────────────────
// § 14  GRAND TOTAL POINTS RANGE SANITY CHECK
// ─────────────────────────────────────────────────────────────

section('Sanity — KO_POINTS table totals 244');

{
  const koTotal = Object.values(KO_POINTS).reduce((s, v) => s + v, 0);
  assert(`KO_POINTS sum = 244 (16×4 + 8×8 + 4×12 + 2×16 + 12 + 24)`,
    koTotal === 244, `got ${koTotal}`);
  assert('Grand max = 144 (group) + 244 (KO) = 388', 144 + koTotal === 388);
}

section('Sanity — KO match count');

{
  assert('16 R32 matches (M73–88)',   Object.keys(KO_POINTS).filter(m => m >= 73 && m <= 88).length === 16);
  assert('8 R16 matches (M89–96)',    Object.keys(KO_POINTS).filter(m => m >= 89 && m <= 96).length === 8);
  assert('4 QF matches (M97–100)',    Object.keys(KO_POINTS).filter(m => m >= 97 && m <= 100).length === 4);
  assert('2 SF matches (M101–102)',   [101,102].every(m => KO_POINTS[m] === 16));
  assert('3rd place (M103) = 12 pts', KO_POINTS[103] === 12);
  assert('Final (M104) = 24 pts',     KO_POINTS[104] === 24);
}

// ─────────────────────────────────────────────────────────────
// § 15  Results
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
