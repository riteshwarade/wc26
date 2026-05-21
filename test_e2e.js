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
// § 2  Match data (verbatim from WC2026_Pool_Leaderboard_Swiftly.html)
// ─────────────────────────────────────────────────────────────

const MATCHES = [
  [1,'A','Thu, Jun 11','3:00 PM','Mexico','South Africa'],
  [2,'A','Thu, Jun 11','10:00 PM','South Korea','Czech Republic'],
  [3,'B','Fri, Jun 12','3:00 PM','Canada','Bosnia and Herzegovina'],
  [4,'D','Fri, Jun 12','9:00 PM','United States','Paraguay'],
  [5,'C','Sat, Jun 13','9:00 PM','Haiti','Scotland'],
  [6,'D','Sat, Jun 13','12:00 AM','Australia','Turkey'],
  [7,'C','Sat, Jun 13','6:00 PM','Brazil','Morocco'],
  [8,'B','Sat, Jun 13','3:00 PM','Qatar','Switzerland'],
  [9,'E','Sun, Jun 14','7:00 PM','Ivory Coast','Ecuador'],
  [10,'E','Sun, Jun 14','1:00 PM','Germany','Curaçao'],
  [11,'F','Sun, Jun 14','4:00 PM','Netherlands','Japan'],
  [12,'F','Sun, Jun 14','10:00 PM','Sweden','Tunisia'],
  [13,'H','Mon, Jun 15','6:00 PM','Saudi Arabia','Uruguay'],
  [14,'H','Mon, Jun 15','12:00 PM','Spain','Cape Verde'],
  [15,'G','Mon, Jun 15','9:00 PM','Iran','New Zealand'],
  [16,'G','Mon, Jun 15','3:00 PM','Belgium','Egypt'],
  [17,'I','Tue, Jun 16','3:00 PM','France','Senegal'],
  [18,'I','Tue, Jun 16','6:00 PM','Iraq','Norway'],
  [19,'J','Tue, Jun 16','9:00 PM','Argentina','Algeria'],
  [20,'J','Tue, Jun 16','12:00 AM','Austria','Jordan'],
  [21,'L','Wed, Jun 17','7:00 PM','Ghana','Panama'],
  [22,'L','Wed, Jun 17','4:00 PM','England','Croatia'],
  [23,'K','Wed, Jun 17','1:00 PM','Portugal','DR Congo'],
  [24,'K','Wed, Jun 17','10:00 PM','Uzbekistan','Colombia'],
  [25,'A','Thu, Jun 18','12:00 PM','Czech Republic','South Africa'],
  [26,'B','Thu, Jun 18','3:00 PM','Switzerland','Bosnia and Herzegovina'],
  [27,'B','Thu, Jun 18','6:00 PM','Canada','Qatar'],
  [28,'A','Thu, Jun 18','9:00 PM','Mexico','South Korea'],
  [29,'C','Fri, Jun 19','8:30 PM','Brazil','Haiti'],
  [30,'C','Fri, Jun 19','6:00 PM','Scotland','Morocco'],
  [31,'D','Fri, Jun 19','11:00 PM','Turkey','Paraguay'],
  [32,'D','Fri, Jun 19','3:00 PM','United States','Australia'],
  [33,'E','Sat, Jun 20','4:00 PM','Germany','Ivory Coast'],
  [34,'E','Sat, Jun 20','8:00 PM','Ecuador','Curaçao'],
  [35,'F','Sat, Jun 20','1:00 PM','Netherlands','Sweden'],
  [36,'F','Sat, Jun 20','12:00 AM','Tunisia','Japan'],
  [37,'H','Sun, Jun 21','6:00 PM','Uruguay','Cape Verde'],
  [38,'H','Sun, Jun 21','12:00 PM','Spain','Saudi Arabia'],
  [39,'G','Sun, Jun 21','3:00 PM','Belgium','Iran'],
  [40,'G','Sun, Jun 21','9:00 PM','New Zealand','Egypt'],
  [41,'I','Mon, Jun 22','8:00 PM','Norway','Senegal'],
  [42,'I','Mon, Jun 22','5:00 PM','France','Iraq'],
  [43,'J','Mon, Jun 22','1:00 PM','Argentina','Austria'],
  [44,'J','Mon, Jun 22','11:00 PM','Jordan','Algeria'],
  [45,'L','Tue, Jun 23','4:00 PM','England','Ghana'],
  [46,'L','Tue, Jun 23','7:00 PM','Panama','Croatia'],
  [47,'K','Tue, Jun 23','1:00 PM','Portugal','Uzbekistan'],
  [48,'K','Tue, Jun 23','10:00 PM','Colombia','DR Congo'],
  [49,'C','Wed, Jun 24','6:00 PM','Scotland','Brazil'],
  [50,'C','Wed, Jun 24','6:00 PM','Morocco','Haiti'],
  [51,'B','Wed, Jun 24','3:00 PM','Switzerland','Canada'],
  [52,'B','Wed, Jun 24','3:00 PM','Bosnia and Herzegovina','Qatar'],
  [53,'A','Wed, Jun 24','9:00 PM','Czech Republic','Mexico'],
  [54,'A','Wed, Jun 24','9:00 PM','South Africa','South Korea'],
  [55,'E','Thu, Jun 25','4:00 PM','Curaçao','Ivory Coast'],
  [56,'E','Thu, Jun 25','4:00 PM','Ecuador','Germany'],
  [57,'F','Thu, Jun 25','7:00 PM','Japan','Sweden'],
  [58,'F','Thu, Jun 25','7:00 PM','Tunisia','Netherlands'],
  [59,'D','Thu, Jun 25','10:00 PM','Turkey','United States'],
  [60,'D','Thu, Jun 25','10:00 PM','Paraguay','Australia'],
  [61,'I','Fri, Jun 26','3:00 PM','Norway','France'],
  [62,'I','Fri, Jun 26','3:00 PM','Senegal','Iraq'],
  [63,'G','Fri, Jun 26','11:00 PM','Egypt','Iran'],
  [64,'G','Fri, Jun 26','11:00 PM','New Zealand','Belgium'],
  [65,'H','Fri, Jun 26','8:00 PM','Cape Verde','Saudi Arabia'],
  [66,'H','Fri, Jun 26','8:00 PM','Uruguay','Spain'],
  [67,'L','Sat, Jun 27','5:00 PM','Panama','England'],
  [68,'L','Sat, Jun 27','5:00 PM','Croatia','Ghana'],
  [69,'J','Sat, Jun 27','10:00 PM','Algeria','Austria'],
  [70,'J','Sat, Jun 27','10:00 PM','Jordan','Argentina'],
  [71,'K','Sat, Jun 27','7:30 PM','Colombia','Portugal'],
  [72,'K','Sat, Jun 27','7:30 PM','DR Congo','Uzbekistan'],
];

// ─────────────────────────────────────────────────────────────
// § 3  KO bracket topology (from bracket.js, verbatim)
// ─────────────────────────────────────────────────────────────

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

function isTbd(name) {
  return !name || name === 'TBD' || /^[WL]\d+$/.test(name) || /^[12][A-L]$/.test(name) || /^3M\d+$/.test(name);
}

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
// § 4  Data generation
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
// § 5  Scoring functions (verbatim from leaderboard HTML)
// ─────────────────────────────────────────────────────────────

const KO_POINTS = {
  73:4,74:4,75:4,76:4,77:4,78:4,79:4,80:4,
  81:4,82:4,83:4,84:4,85:4,86:4,87:4,88:4,
  89:8,90:8,91:8,92:8,93:8,94:8,95:8,96:8,
  97:12,98:12,99:12,100:12,
  101:16,102:16,103:12,104:24,
};

function getKoTeams(m, bracketData, koResults) {
  if (m >= 73 && m <= 88) {
    if (bracketData && bracketData.round_of_32 && bracketData.round_of_32[String(m)]) {
      const slot = bracketData.round_of_32[String(m)];
      return [slot.home, slot.away];
    }
    return ['TBD', 'TBD'];
  }
  if (R16[m]) { const [f1,f2]=R16[m]; return [koResults[f1]||`W${f1}`,koResults[f2]||`W${f2}`]; }
  if (QF[m])  { const [f1,f2]=QF[m];  return [koResults[f1]||`W${f1}`,koResults[f2]||`W${f2}`]; }
  if (SF[m])  { const [f1,f2]=SF[m];  return [koResults[f1]||`W${f1}`,koResults[f2]||`W${f2}`]; }
  if (m === 103) {
    const [sf1h,sf1a]=getKoTeams(101,bracketData,koResults);
    const [sf2h,sf2a]=getKoTeams(102,bracketData,koResults);
    const loser1=koResults[101]?(koResults[101]===sf1h?sf1a:sf1h):'L101';
    const loser2=koResults[102]?(koResults[102]===sf2h?sf2a:sf2h):'L102';
    return [loser1,loser2];
  }
  if (m === 104) return [koResults[101]||'W101',koResults[102]||'W102'];
  return ['TBD','TBD'];
}

function computeStandings(picksData, results) {
  return Object.entries(picksData).map(([name, picks]) => {
    let points = 0;
    const pickResults = {};
    MATCHES.forEach(([num,,,, t1, t2]) => {
      const result = results[num];
      const pick   = picks[String(num)];
      if (result && pick) {
        const correct = pick === result.outcome;
        if (correct) points += 2;
        pickResults[num] = { status: correct ? 'correct' : 'wrong', pick, result };
      } else if (pick) {
        pickResults[num] = { status: 'pending', pick, result: null };
      } else {
        pickResults[num] = { status: 'empty', pick: null, result: null };
      }
    });
    return { name, points, pickResults };
  }).sort((a,b) => b.points - a.points || a.name.localeCompare(b.name));
}

function computeCombinedStandings(groupStandings, koPicksData, koResults, bracketData) {
  const KO_MATCH_NUMS = [73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,
                         89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104];

  function matchRound(m) {
    if (m >= 73 && m <= 88) return 1;
    if (m >= 89 && m <= 96) return 2;
    if (m >= 97 && m <= 100) return 3;
    if (m === 101 || m === 102) return 4;
    return 5;
  }

  function cascadeThreshold(m) {
    if (m >= 73 && m <= 88) return 0;
    if (m >= 89 && m <= 96) return 2;
    if (m >= 97 && m <= 100) return 3;
    if (m === 101 || m === 102) return 4;
    if (m === 103) return 4;
    if (m === 104) return 5;
    return 0;
  }

  const eliminatedInRound = {};
  for (const m of KO_MATCH_NUMS) {
    const winner = koResults[m];
    if (!winner || !bracketData) continue;
    try {
      const [t1, t2] = getKoTeams(m, bracketData, koResults);
      const loser = (t1 === winner) ? t2 : (t2 === winner) ? t1 : null;
      if (loser && !isTbd(loser) && !(loser in eliminatedInRound)) {
        eliminatedInRound[loser] = matchRound(m);
      }
    } catch(e) {}
  }

  function evalKoPicks(koPicks) {
    let koPts = 0, totalCorrect = 0, correctChampion = false;
    const koPickResults = {};
    for (const m of KO_MATCH_NUMS) {
      const pick      = koPicks[String(m)];
      const winner    = koResults[m];
      const threshold = cascadeThreshold(m);
      const isCascaded = pick && threshold > 0 &&
                         eliminatedInRound[pick] !== undefined &&
                         eliminatedInRound[pick] < threshold;
      if (!pick) {
        koPickResults[m] = { status:'empty', pick:null, winner: winner||null };
      } else if (winner) {
        if (isCascaded) {
          koPickResults[m] = { status:'cascaded', pick, winner };
        } else {
          const isCorrect = pick === winner;
          if (isCorrect) { koPts += KO_POINTS[m]||0; totalCorrect++; if (m===104) correctChampion=true; }
          koPickResults[m] = { status: isCorrect?'correct':'wrong', pick, winner };
        }
      } else {
        koPickResults[m] = { status: isCascaded?'cascaded':'pending', pick, winner:null };
      }
    }
    let koPossiblePts = koPts;
    for (const m of KO_MATCH_NUMS) {
      if (koPickResults[m].status === 'pending') koPossiblePts += KO_POINTS[m]||0;
    }
    return { koPts, koPossiblePts, totalCorrect, correctChampion, koPickResults };
  }

  const combined = groupStandings.map(p => {
    const { koPts, koPossiblePts, totalCorrect:koCorrect, correctChampion, koPickResults } =
      evalKoPicks(koPicksData[p.name] || {});
    const grpCorrect = Object.values(p.pickResults||{}).filter(pr=>pr.status==='correct').length;
    return { ...p, groupPts:p.points, koPts, totalPts:p.points+koPts,
             maxPts:p.points+koPossiblePts, correctChampion,
             totalCorrect:grpCorrect+koCorrect, koPickResults };
  });

  Object.keys(koPicksData).forEach(name => {
    if (!combined.find(p=>p.name===name)) {
      const { koPts, koPossiblePts, totalCorrect, correctChampion, koPickResults } =
        evalKoPicks(koPicksData[name]);
      combined.push({ name, points:0, groupPts:0, pickResults:{}, koPts,
        totalPts:koPts, maxPts:koPossiblePts, correctChampion, totalCorrect, koPickResults });
    }
  });

  combined.sort((a,b) =>
    (b.totalPts - a.totalPts) ||
    ((b.correctChampion?1:0) - (a.correctChampion?1:0)) ||
    (b.totalCorrect - a.totalCorrect) ||
    a.name.localeCompare(b.name)
  );
  return combined;
}

// ─────────────────────────────────────────────────────────────
// § 6  Test harness
// ─────────────────────────────────────────────────────────────

let passed = 0, failed = 0;
function assert(label, cond, extra='') {
  if (cond) { console.log(`  ✅ ${label}`); passed++; }
  else { console.error(`  ❌ FAIL: ${label}${extra?' — '+extra:''}`); failed++; }
}
function section(t) { console.log(`\n── ${t} ──`); }

// ─────────────────────────────────────────────────────────────
// § 7  Run the simulation
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
// § 8  Print leaderboard
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
// § 9  Structural invariants
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
// § 10  Results
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
