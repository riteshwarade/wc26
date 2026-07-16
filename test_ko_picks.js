/**
 * test_ko_picks.js — unit tests for ko_picks.js pure logic
 *
 * Tests: feedsInto topology, getTeams resolution, clearInvalidDownstream cascade.
 *
 * ko_picks.js depends on R16/QF/SF/isTbd from bracket.js — we seed these as
 * globals before require(). The DOM event-wiring in ko_picks.js is guarded by
 * `typeof module === 'undefined'` so it doesn't run here.
 *
 * Run: node test_ko_picks.js
 */

'use strict';

// ── Seed bracket.js globals before requiring ko_picks.js ─────────────────────
global.R16 = {
   89:[74,77],  90:[73,75],  91:[76,78],  92:[79,80],
   93:[83,84],  94:[81,82],  95:[86,88],  96:[85,87],
};
global.QF = {
   97:[89,90],  98:[93,94],  99:[91,92], 100:[95,96],
};
global.SF = {
  101:[97,98], 102:[99,100],
};
global.isTbd = (name) =>
  !name || name === 'TBD' || /^[WL]\d+$/.test(name)
  || /^[12][A-L]$/.test(name) || /^3M\d+$/.test(name);

// Stub browser functions not needed for pure logic tests
global.FLAGS     = {};
global.RANKINGS  = {};
global.KO_SCHEDULE = {};
global.fetch     = () => Promise.resolve({ ok: false });
global.matchCard = () => '';
global.buildBracketHtml = () => '';
global.buildMobTabHtml  = () => '';
global.buildPodiumHtml  = () => '';
global.positionAndConnectBracket = () => {};
global.switchBracketTab = () => {};
global.koDisplay  = () => '';
global.teamHtml   = (n) => n || '';
global.roundLabel = () => '';
global.requestAnimationFrame = () => {};
global.document = undefined; // triggers browser-guard in ko_picks.js

const {
  feedsInto, picks, r32Teams,
  buildFeedsInto, getTeams, clearInvalidDownstream, MATCH_ORDER,
} = require('./ko_picks.js');

// ── Test data: stable fake teams for all 16 R32 matches ──────────────────────
const TEAMS = {
  73:['TeamA','TeamB'],   74:['TeamC','TeamD'],   75:['TeamE','TeamF'],   76:['TeamG','TeamH'],
  77:['TeamI','TeamJ'],   78:['TeamK','TeamL'],   79:['TeamM','TeamN'],   80:['TeamO','TeamP'],
  81:['TeamQ','TeamR'],   82:['TeamS','TeamT'],   83:['TeamU','TeamV'],   84:['TeamW','TeamX'],
  85:['TeamY','TeamZ'],   86:['TeamAA','TeamBB'], 87:['TeamCC','TeamDD'], 88:['TeamEE','TeamFF'],
};

function resetState() {
  // Clear shared mutable state between tests
  Object.keys(r32Teams).forEach(k => delete r32Teams[k]);
  Object.keys(picks).forEach(k => delete picks[k]);
  Object.assign(r32Teams, TEAMS);
}

// ── Assertion helpers ─────────────────────────────────────────────────────────
let passed = 0, failed = 0;
function assert(condition, label) {
  if (condition) { console.log(`  ✓ ${label}`); passed++; }
  else           { console.error(`  ✗ ${label}`); failed++; }
}
function eq(a, b, label) {
  const ok = JSON.stringify(a) === JSON.stringify(b);
  if (!ok) console.error(`    Expected: ${JSON.stringify(b)}\n    Got:      ${JSON.stringify(a)}`);
  assert(ok, label);
}
function section(name) { console.log(`\n§ ${name}`); }

// ── Initialise topology ───────────────────────────────────────────────────────
buildFeedsInto();

// ─────────────────────────────────────────────────────────────────────────────
// §1 — feedsInto topology
// ─────────────────────────────────────────────────────────────────────────────
section('feedsInto topology');

const r32Matches = [73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88];
assert(r32Matches.every(m => feedsInto[m] >= 89 && feedsInto[m] <= 96),
  'All 16 R32 matches feed into R16 (89-96)');

// Specific R32→R16 chains derived from R16 topology
eq(feedsInto[74], 89,  'M74 winner feeds M89');
eq(feedsInto[77], 89,  'M77 winner feeds M89');
eq(feedsInto[73], 90,  'M73 winner feeds M90');
eq(feedsInto[75], 90,  'M75 winner feeds M90');
eq(feedsInto[83], 93,  'M83 winner feeds M93');
eq(feedsInto[84], 93,  'M84 winner feeds M93');
eq(feedsInto[81], 94,  'M81 winner feeds M94');
eq(feedsInto[82], 94,  'M82 winner feeds M94');
eq(feedsInto[76], 91,  'M76 winner feeds M91');
eq(feedsInto[78], 91,  'M78 winner feeds M91');
eq(feedsInto[86], 95,  'M86 winner feeds M95');
eq(feedsInto[88], 95,  'M88 winner feeds M95');

// R16→QF
eq(feedsInto[89], 97,  'M89 winner feeds M97');
eq(feedsInto[90], 97,  'M90 winner feeds M97');
eq(feedsInto[93], 98,  'M93 winner feeds M98');
eq(feedsInto[94], 98,  'M94 winner feeds M98');
eq(feedsInto[91], 99,  'M91 winner feeds M99');
eq(feedsInto[92], 99,  'M92 winner feeds M99');
eq(feedsInto[95], 100, 'M95 winner feeds M100');
eq(feedsInto[96], 100, 'M96 winner feeds M100');

// QF→SF
eq(feedsInto[97],  101, 'M97 winner feeds M101 (SF1)');
eq(feedsInto[98],  101, 'M98 winner feeds M101 (SF1)');
eq(feedsInto[99],  102, 'M99 winner feeds M102 (SF2)');
eq(feedsInto[100], 102, 'M100 winner feeds M102 (SF2)');

// SF→Final
eq(feedsInto[101], 104, 'M101 winner feeds M104 (Final)');
eq(feedsInto[102], 104, 'M102 winner feeds M104 (Final)');

// No feedsInto for 3rd place or Final
assert(feedsInto[103] === undefined, 'M103 (3rd place) has no feedsInto');
assert(feedsInto[104] === undefined, 'M104 (Final) has no feedsInto');

// ─────────────────────────────────────────────────────────────────────────────
// §2 — getTeams: R32 resolved from r32Teams
// ─────────────────────────────────────────────────────────────────────────────
section('getTeams — R32 from r32Teams');
resetState();

eq(getTeams(73), ['TeamA','TeamB'], 'M73 teams');
eq(getTeams(74), ['TeamC','TeamD'], 'M74 teams');
eq(getTeams(88), ['TeamEE','TeamFF'], 'M88 teams');

// ─────────────────────────────────────────────────────────────────────────────
// §3 — getTeams: R16 resolves from picks
// ─────────────────────────────────────────────────────────────────────────────
section('getTeams — R16 resolution from R32 picks');
resetState();

// No picks → TBD placeholders
const [h0, a0] = getTeams(89); // M89 feeds from M74 and M77
assert(global.isTbd(h0), 'M89 home TBD when no picks');
assert(global.isTbd(a0), 'M89 away TBD when no picks');

// Pick both feeders
picks[74] = 'TeamC'; picks[77] = 'TeamI';
eq(getTeams(89), ['TeamC','TeamI'], 'M89 resolves after M74+M77 picks');

// Partial
delete picks[77];
const [h1, a1] = getTeams(89);
eq(h1, 'TeamC', 'M89 home resolves from M74 pick');
assert(global.isTbd(a1), 'M89 away still TBD when M77 not picked');

// ─────────────────────────────────────────────────────────────────────────────
// §4 — getTeams: QF resolves through R16 picks
// ─────────────────────────────────────────────────────────────────────────────
section('getTeams — QF resolution chain');
resetState();

picks[74]='TeamC'; picks[77]='TeamI'; picks[89]='TeamC';
picks[73]='TeamA'; picks[75]='TeamE'; picks[90]='TeamA';

// M97 feeds from M89 and M90 — but M89/M90 not picked yet doesn't matter;
// getTeams(97) looks at picks[QF[97][0]] = picks[89] and picks[QF[97][1]] = picks[90]
eq(getTeams(97), ['TeamC','TeamA'], 'M97 resolves from M89+M90 picks');

// Clear M89 pick — M97 home becomes TBD
delete picks[89];
const [h2, a2] = getTeams(97);
assert(global.isTbd(h2), 'M97 home TBD when M89 not picked');
eq(a2, 'TeamA', 'M97 away still resolves from M90 pick');

// ─────────────────────────────────────────────────────────────────────────────
// §5 — getTeams: 3rd place (SF losers)
// ─────────────────────────────────────────────────────────────────────────────
section('getTeams — 3rd place (SF losers)');
resetState();

// SF1: TeamC vs TeamU → TeamC wins → TeamU is 3rd place home
// Wire up enough picks to make SF1 teams resolvable
picks[74]='TeamC'; picks[77]='TeamI'; picks[89]='TeamC';
picks[73]='TeamA'; picks[75]='TeamE'; picks[90]='TeamA';
picks[97]='TeamC'; // QF1 → TeamC to SF1
picks[83]='TeamU'; picks[84]='TeamW'; picks[93]='TeamU';
picks[81]='TeamQ'; picks[82]='TeamS'; picks[94]='TeamQ';
picks[98]='TeamU'; // QF2 → TeamU to SF1
picks[101]='TeamC'; // SF1 winner = TeamC; loser = TeamU

// SF2 not picked yet
const [h3, a3] = getTeams(103);
eq(h3, 'TeamU', '3rd place home = SF1 loser (TeamU)');
assert(global.isTbd(a3), '3rd place away TBD when SF2 not picked');

// Pick SF2
picks[76]='TeamG'; picks[78]='TeamK'; picks[91]='TeamG';
picks[79]='TeamM'; picks[80]='TeamO'; picks[92]='TeamM';
picks[99]='TeamG'; // QF3
picks[86]='TeamAA'; picks[88]='TeamEE'; picks[95]='TeamAA';
picks[85]='TeamY';  picks[87]='TeamCC'; picks[96]='TeamY';
picks[100]='TeamAA'; // QF4
picks[102]='TeamG'; // SF2 winner = TeamG; loser = TeamAA
eq(getTeams(103), ['TeamU','TeamAA'], '3rd place resolves when both SFs picked');

// ─────────────────────────────────────────────────────────────────────────────
// §6 — clearInvalidDownstream: pick changes cascade
// ─────────────────────────────────────────────────────────────────────────────
section('clearInvalidDownstream — cascading on pick change');
resetState();

// Set up M74 → M89 → M97 chain
picks[74]='TeamC'; picks[77]='TeamI'; picks[89]='TeamC';
picks[73]='TeamA'; picks[75]='TeamE'; picks[90]='TeamA';
picks[97]='TeamC'; // QF1 pick

// Change M74 winner → TeamD (not TeamC); M89 had TeamC which is no longer valid
picks[74] = 'TeamD';
clearInvalidDownstream(74);
assert(!picks[89], 'M89 cleared: TeamC no longer in M89 after M74→TeamD');
assert(!picks[97], 'M97 cascade-cleared: depended on M89 which was cleared');

// ─────────────────────────────────────────────────────────────────────────────
// §7 — clearInvalidDownstream: valid pick survives
// ─────────────────────────────────────────────────────────────────────────────
section('clearInvalidDownstream — valid downstream pick survives');
resetState();

picks[74]='TeamC'; picks[77]='TeamI'; picks[89]='TeamC';
picks[73]='TeamA'; picks[75]='TeamE'; picks[90]='TeamA';
picks[97]='TeamC';

// Change M77 winner → TeamJ (both teams in M89 change, but TeamC came from M74 not M77)
// M89 = [winner of M74, winner of M77] = [TeamC, TeamJ]
// picks[89] = TeamC, which IS still in M89 → should survive
picks[77] = 'TeamJ';
clearInvalidDownstream(77);
assert(picks[89] === 'TeamC', 'M89 pick survives: TeamC still valid in M89 after M77 changes');
assert(picks[97] === 'TeamC', 'M97 pick survives: cascade not triggered');

// ─────────────────────────────────────────────────────────────────────────────
// §8 — clearInvalidDownstream: 3rd place cascade (SF losers path)
// ─────────────────────────────────────────────────────────────────────────────
section('clearInvalidDownstream — 3rd place (SF losers path)');
resetState();

picks[74]='TeamC'; picks[77]='TeamI'; picks[89]='TeamC';
picks[73]='TeamA'; picks[75]='TeamE'; picks[90]='TeamA';
picks[97]='TeamC'; picks[83]='TeamU'; picks[84]='TeamW'; picks[93]='TeamU';
picks[81]='TeamQ'; picks[82]='TeamS'; picks[94]='TeamQ'; picks[98]='TeamU';
picks[101]='TeamC'; // SF1: TeamC wins, TeamU loses
picks[76]='TeamG'; picks[78]='TeamK'; picks[91]='TeamG';
picks[79]='TeamM'; picks[80]='TeamO'; picks[92]='TeamM';
picks[99]='TeamG'; picks[86]='TeamAA'; picks[88]='TeamEE'; picks[95]='TeamAA';
picks[85]='TeamY'; picks[87]='TeamCC'; picks[96]='TeamY';
picks[100]='TeamAA'; picks[102]='TeamG'; // SF2: TeamG wins, TeamAA loses
picks[103]='TeamU'; // 3rd place pick = SF1 loser

// Flip SF1 winner to TeamU → loser becomes TeamC → picks[103]=TeamU no longer valid
picks[101] = 'TeamU';
clearInvalidDownstream(101);
assert(!picks[103], '3rd place pick cleared when SF1 winner changes invalidates it');

// ─────────────────────────────────────────────────────────────────────────────
// §9 — MATCH_ORDER
// ─────────────────────────────────────────────────────────────────────────────
section('MATCH_ORDER');

eq(MATCH_ORDER.length, 32, '32 matches in MATCH_ORDER');
assert([73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88].every(m => MATCH_ORDER.includes(m)),
  'All 16 R32 matches present');
assert([89,90,91,92,93,94,95,96].every(m => MATCH_ORDER.includes(m)),
  'All 8 R16 matches present');
assert([97,98,99,100].every(m => MATCH_ORDER.includes(m)), 'All 4 QF matches present');
assert([101,102].every(m => MATCH_ORDER.includes(m)), 'Both SF matches present');
assert(MATCH_ORDER.includes(103) && MATCH_ORDER.includes(104), '3rd place + Final present');
assert(MATCH_ORDER.indexOf(88) < MATCH_ORDER.indexOf(89), 'R32 before R16');
assert(MATCH_ORDER.indexOf(96) < MATCH_ORDER.indexOf(97), 'R16 before QF');
assert(MATCH_ORDER.indexOf(100) < MATCH_ORDER.indexOf(101), 'QF before SF');
assert(MATCH_ORDER.indexOf(102) < MATCH_ORDER.indexOf(103), 'SF before 3rd/Final');

// ─────────────────────────────────────────────────────────────────────────────
// Results
// ─────────────────────────────────────────────────────────────────────────────
console.log(`\n${'═'.repeat(72)}`);
console.log(`KO picks tests: ${passed}/${passed + failed} passed`);
if (failed > 0) {
  console.error(`\n✗ ${failed} test(s) failed`);
  process.exit(1);
} else {
  console.log('\n🏆 All KO picks tests passed.');
}
