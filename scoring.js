/**
 * scoring.js
 *
 * Shared scoring module for WC2026 pool leaderboard.
 * Loaded via <script src="scoring.js"> in the browser (after bracket.js)
 * and via require('./scoring.js') in Node test files.
 *
 * Exports (Node only): MATCHES, KO_POINTS, parseResults, parseKoResults,
 *   parseKoScores, getKoTeams, computeStandings, computeCombinedStandings
 */

'use strict';

// ── Match list ────────────────────────────────────────────────────────────────
// [num, group, date (ET display), utcKickoff (ISO 8601 UTC), home, away]
const MATCHES = [
  [1,  'A', 'Thu, Jun 11', '2026-06-11T19:00:00Z', 'Mexico',                'South Africa'],
  [2,  'A', 'Thu, Jun 11', '2026-06-12T02:00:00Z', 'South Korea',           'Czech Republic'],
  [3,  'B', 'Fri, Jun 12', '2026-06-12T19:00:00Z', 'Canada',                'Bosnia and Herzegovina'],
  [4,  'D', 'Fri, Jun 12', '2026-06-13T01:00:00Z', 'United States',         'Paraguay'],
  [5,  'C', 'Sat, Jun 13', '2026-06-14T01:00:00Z', 'Haiti',                 'Scotland'],
  [6,  'D', 'Sun, Jun 14', '2026-06-14T04:00:00Z', 'Australia',             'Turkey'],
  [7,  'C', 'Sat, Jun 13', '2026-06-13T22:00:00Z', 'Brazil',                'Morocco'],
  [8,  'B', 'Sat, Jun 13', '2026-06-13T19:00:00Z', 'Qatar',                 'Switzerland'],
  [9,  'E', 'Sun, Jun 14', '2026-06-14T23:00:00Z', 'Ivory Coast',           'Ecuador'],
  [10, 'E', 'Sun, Jun 14', '2026-06-14T17:00:00Z', 'Germany',               'Curaçao'],
  [11, 'F', 'Sun, Jun 14', '2026-06-14T20:00:00Z', 'Netherlands',           'Japan'],
  [12, 'F', 'Sun, Jun 14', '2026-06-15T02:00:00Z', 'Sweden',                'Tunisia'],
  [13, 'H', 'Mon, Jun 15', '2026-06-15T22:00:00Z', 'Saudi Arabia',          'Uruguay'],
  [14, 'H', 'Mon, Jun 15', '2026-06-15T16:00:00Z', 'Spain',                 'Cape Verde'],
  [15, 'G', 'Mon, Jun 15', '2026-06-16T01:00:00Z', 'Iran',                  'New Zealand'],
  [16, 'G', 'Mon, Jun 15', '2026-06-15T19:00:00Z', 'Belgium',               'Egypt'],
  [17, 'I', 'Tue, Jun 16', '2026-06-16T19:00:00Z', 'France',                'Senegal'],
  [18, 'I', 'Tue, Jun 16', '2026-06-16T22:00:00Z', 'Iraq',                  'Norway'],
  [19, 'J', 'Tue, Jun 16', '2026-06-17T01:00:00Z', 'Argentina',             'Algeria'],
  [20, 'J', 'Wed, Jun 17', '2026-06-17T04:00:00Z', 'Austria',               'Jordan'],
  [21, 'L', 'Wed, Jun 17', '2026-06-17T23:00:00Z', 'Ghana',                 'Panama'],
  [22, 'L', 'Wed, Jun 17', '2026-06-17T20:00:00Z', 'England',               'Croatia'],
  [23, 'K', 'Wed, Jun 17', '2026-06-17T17:00:00Z', 'Portugal',              'DR Congo'],
  [24, 'K', 'Wed, Jun 17', '2026-06-18T02:00:00Z', 'Uzbekistan',            'Colombia'],
  [25, 'A', 'Thu, Jun 18', '2026-06-18T16:00:00Z', 'Czech Republic',        'South Africa'],
  [26, 'B', 'Thu, Jun 18', '2026-06-18T19:00:00Z', 'Switzerland',           'Bosnia and Herzegovina'],
  [27, 'B', 'Thu, Jun 18', '2026-06-18T22:00:00Z', 'Canada',                'Qatar'],
  [28, 'A', 'Thu, Jun 18', '2026-06-19T01:00:00Z', 'Mexico',                'South Korea'],
  [29, 'C', 'Fri, Jun 19', '2026-06-20T00:30:00Z', 'Brazil',                'Haiti'],
  [30, 'C', 'Fri, Jun 19', '2026-06-19T22:00:00Z', 'Scotland',              'Morocco'],
  [31, 'D', 'Fri, Jun 19', '2026-06-20T03:00:00Z', 'Turkey',                'Paraguay'],
  [32, 'D', 'Fri, Jun 19', '2026-06-19T19:00:00Z', 'United States',         'Australia'],
  [33, 'E', 'Sat, Jun 20', '2026-06-20T20:00:00Z', 'Germany',               'Ivory Coast'],
  [34, 'E', 'Sat, Jun 20', '2026-06-21T00:00:00Z', 'Ecuador',               'Curaçao'],
  [35, 'F', 'Sat, Jun 20', '2026-06-20T17:00:00Z', 'Netherlands',           'Sweden'],
  [36, 'F', 'Sun, Jun 21', '2026-06-21T04:00:00Z', 'Tunisia',               'Japan'],
  [37, 'H', 'Sun, Jun 21', '2026-06-21T22:00:00Z', 'Uruguay',               'Cape Verde'],
  [38, 'H', 'Sun, Jun 21', '2026-06-21T16:00:00Z', 'Spain',                 'Saudi Arabia'],
  [39, 'G', 'Sun, Jun 21', '2026-06-21T19:00:00Z', 'Belgium',               'Iran'],
  [40, 'G', 'Sun, Jun 21', '2026-06-22T01:00:00Z', 'New Zealand',           'Egypt'],
  [41, 'I', 'Mon, Jun 22', '2026-06-23T00:00:00Z', 'Norway',                'Senegal'],
  [42, 'I', 'Mon, Jun 22', '2026-06-22T21:00:00Z', 'France',                'Iraq'],
  [43, 'J', 'Mon, Jun 22', '2026-06-22T17:00:00Z', 'Argentina',             'Austria'],
  [44, 'J', 'Mon, Jun 22', '2026-06-23T03:00:00Z', 'Jordan',                'Algeria'],
  [45, 'L', 'Tue, Jun 23', '2026-06-23T20:00:00Z', 'England',               'Ghana'],
  [46, 'L', 'Tue, Jun 23', '2026-06-23T23:00:00Z', 'Panama',                'Croatia'],
  [47, 'K', 'Tue, Jun 23', '2026-06-23T17:00:00Z', 'Portugal',              'Uzbekistan'],
  [48, 'K', 'Tue, Jun 23', '2026-06-24T02:00:00Z', 'Colombia',              'DR Congo'],
  [49, 'C', 'Wed, Jun 24', '2026-06-24T22:00:00Z', 'Scotland',              'Brazil'],
  [50, 'C', 'Wed, Jun 24', '2026-06-24T22:00:00Z', 'Morocco',               'Haiti'],
  [51, 'B', 'Wed, Jun 24', '2026-06-24T19:00:00Z', 'Switzerland',           'Canada'],
  [52, 'B', 'Wed, Jun 24', '2026-06-24T19:00:00Z', 'Bosnia and Herzegovina','Qatar'],
  [53, 'A', 'Wed, Jun 24', '2026-06-25T01:00:00Z', 'Czech Republic',        'Mexico'],
  [54, 'A', 'Wed, Jun 24', '2026-06-25T01:00:00Z', 'South Africa',          'South Korea'],
  [55, 'E', 'Thu, Jun 25', '2026-06-25T20:00:00Z', 'Curaçao',               'Ivory Coast'],
  [56, 'E', 'Thu, Jun 25', '2026-06-25T20:00:00Z', 'Ecuador',               'Germany'],
  [57, 'F', 'Thu, Jun 25', '2026-06-25T23:00:00Z', 'Japan',                 'Sweden'],
  [58, 'F', 'Thu, Jun 25', '2026-06-25T23:00:00Z', 'Tunisia',               'Netherlands'],
  [59, 'D', 'Thu, Jun 25', '2026-06-26T02:00:00Z', 'Turkey',                'United States'],
  [60, 'D', 'Thu, Jun 25', '2026-06-26T02:00:00Z', 'Paraguay',              'Australia'],
  [61, 'I', 'Fri, Jun 26', '2026-06-26T19:00:00Z', 'Norway',                'France'],
  [62, 'I', 'Fri, Jun 26', '2026-06-26T19:00:00Z', 'Senegal',               'Iraq'],
  [63, 'G', 'Fri, Jun 26', '2026-06-27T03:00:00Z', 'Egypt',                 'Iran'],
  [64, 'G', 'Fri, Jun 26', '2026-06-27T03:00:00Z', 'New Zealand',           'Belgium'],
  [65, 'H', 'Fri, Jun 26', '2026-06-27T00:00:00Z', 'Cape Verde',            'Saudi Arabia'],
  [66, 'H', 'Fri, Jun 26', '2026-06-27T00:00:00Z', 'Uruguay',               'Spain'],
  [67, 'L', 'Sat, Jun 27', '2026-06-27T21:00:00Z', 'Panama',                'England'],
  [68, 'L', 'Sat, Jun 27', '2026-06-27T21:00:00Z', 'Croatia',               'Ghana'],
  [69, 'J', 'Sat, Jun 27', '2026-06-28T02:00:00Z', 'Algeria',               'Austria'],
  [70, 'J', 'Sat, Jun 27', '2026-06-28T02:00:00Z', 'Jordan',                'Argentina'],
  [71, 'K', 'Sat, Jun 27', '2026-06-27T23:30:00Z', 'Colombia',              'Portugal'],
  [72, 'K', 'Sat, Jun 27', '2026-06-27T23:30:00Z', 'DR Congo',              'Uzbekistan'],
];

// ── KO bracket topology ───────────────────────────────────────────────────────
// Canonical source: bracket.js (R16 / QF / SF).
// This copy exists for Node.js contexts where bracket.js is not loaded.
// If you ever change the topology, update bracket.js first, then mirror here.
const _R16 = {
   89:[74,77],  90:[73,75],  91:[76,78],  92:[79,80],
   93:[83,84],  94:[81,82],  95:[86,88],  96:[85,87],
};
const _QF = {
   97:[89,90],  98:[93,94],  99:[91,92],  100:[95,96],
};
const _SF = {
  101:[97,98], 102:[99,100],
};
// Browser sanity-check: assert this copy matches bracket.js at runtime.
if (typeof R16 !== 'undefined') {
  const _assertEq = (a, b, label) => {
    if (JSON.stringify(a) !== JSON.stringify(b))
      console.error(`scoring.js topology mismatch vs bracket.js: ${label}`);
  };
  _assertEq(_R16, R16, '_R16/R16');
  _assertEq(_QF,  QF,  '_QF/QF');
  _assertEq(_SF,  SF,  '_SF/SF');
}

function _isTbd(name) {
  return !name || name === 'TBD' || /^[WL]\d+$/.test(name) ||
         /^[12][A-L]$/.test(name) || /^3M\d+$/.test(name);
}

// ── KO match points ───────────────────────────────────────────────────────────
const KO_POINTS = {
  73:4,  74:4,  75:4,  76:4,  77:4,  78:4,  79:4,  80:4,
  81:4,  82:4,  83:4,  84:4,  85:4,  86:4,  87:4,  88:4,
  89:8,  90:8,  91:8,  92:8,  93:8,  94:8,  95:8,  96:8,
  97:12, 98:12, 99:12, 100:12,
  101:16, 102:16, 103:12, 104:24,
};

// ── Parse group results CSV ───────────────────────────────────────────────────
// Format: match,home_score,away_score,outcome  (header + data rows)
// Returns { matchNum: { home, away, outcome } }
function parseResults(csvText) {
  const results = {};
  csvText.trim().split('\n').slice(1).forEach(line => {
    const [match, home, away, outcome] = line.split(',');
    const num = parseInt(match);
    if (num && outcome) {
      results[num] = { home: parseInt(home), away: parseInt(away), outcome: outcome.trim() };
    }
  });
  return results;
}

// ── Parse KO results CSV ──────────────────────────────────────────────────────
// Format: match,winner  (header + data rows)
// Returns { matchNum: winnerName }
function parseKoResults(csvText) {
  const results = {};
  if (!csvText || !csvText.trim()) return results;
  csvText.trim().split('\n').slice(1).forEach(line => {
    const parts = line.split(',');
    const num = parseInt(parts[0]);
    const winner = parts[1] ? parts[1].trim() : null;
    if (num && winner) results[num] = winner;
  });
  return results;
}

// ── Parse KO scores CSV ───────────────────────────────────────────────────────
// Format: match,winner,home_score,away_score[,home_pen,away_pen]
// Returns { matchNum: { home, away[, homePen, awayPen] } } — only rows with score data
function parseKoScores(csvText) {
  const scores = {};
  if (!csvText || !csvText.trim()) return scores;
  const lines = csvText.trim().split('\n');
  if (lines.length < 2) return scores;
  const header   = lines[0].split(',').map(s => s.trim());
  const homeIdx  = header.indexOf('home_score');
  const awayIdx  = header.indexOf('away_score');
  const hPenIdx  = header.indexOf('home_pen');
  const aPenIdx  = header.indexOf('away_pen');
  if (homeIdx === -1 || awayIdx === -1) return scores;
  lines.slice(1).forEach(line => {
    const parts = line.split(',');
    const num   = parseInt(parts[0]);
    const home  = parseInt(parts[homeIdx]);
    const away  = parseInt(parts[awayIdx]);
    if (num && !isNaN(home) && !isNaN(away)) {
      const obj = { home, away };
      if (hPenIdx !== -1 && aPenIdx !== -1) {
        const hp = parseInt(parts[hPenIdx]);
        const ap = parseInt(parts[aPenIdx]);
        if (!isNaN(hp) && !isNaN(ap)) { obj.homePen = hp; obj.awayPen = ap; }
      }
      scores[num] = obj;
    }
  });
  return scores;
}

// ── Resolve KO team names for a match ────────────────────────────────────────
// Uses bracket topology + completed results to derive home/away for any match.
function getKoTeams(m, bracketData, koResults) {
  if (m >= 73 && m <= 88) {
    if (bracketData && bracketData.round_of_32 && bracketData.round_of_32[String(m)]) {
      const slot = bracketData.round_of_32[String(m)];
      return [slot.home, slot.away];
    }
    return ['TBD', 'TBD'];
  }
  if (_R16[m]) {
    const [f1, f2] = _R16[m];
    return [koResults[f1] || `W${f1}`, koResults[f2] || `W${f2}`];
  }
  if (_QF[m]) {
    const [f1, f2] = _QF[m];
    return [koResults[f1] || `W${f1}`, koResults[f2] || `W${f2}`];
  }
  if (_SF[m]) {
    const [f1, f2] = _SF[m];
    return [koResults[f1] || `W${f1}`, koResults[f2] || `W${f2}`];
  }
  if (m === 103) {
    const [sf1h, sf1a] = getKoTeams(101, bracketData, koResults);
    const [sf2h, sf2a] = getKoTeams(102, bracketData, koResults);
    const loser1 = koResults[101] ? (koResults[101] === sf1h ? sf1a : sf1h) : 'L101';
    const loser2 = koResults[102] ? (koResults[102] === sf2h ? sf2a : sf2h) : 'L102';
    return [loser1, loser2];
  }
  if (m === 104) {
    return [koResults[101] || 'W101', koResults[102] || 'W102'];
  }
  return ['TBD', 'TBD'];
}

// ── Compute group-only standings ──────────────────────────────────────────────
// Returns array of { name, points, pickResults } sorted by points desc, name asc.
function computeStandings(picksData, results) {
  return Object.entries(picksData).map(([name, picks]) => {
    let points = 0;
    const pickResults = {};
    MATCHES.forEach(([num, , , , t1, t2]) => {
      const result = results[num];
      const pick   = picks[String(num)];
      if (result && pick) {
        const correct = pick === result.outcome;
        if (correct) points += 2;
        pickResults[num] = { status: correct ? 'correct' : 'wrong', pick, result };
      } else if (pick) {
        pickResults[num] = { status: 'pending', pick, result: null };
      } else {
        pickResults[num] = { status: 'empty', pick: null, result: result || null };
      }
    });
    return { name, points, pickResults };
  }).sort((a, b) => b.points - a.points || a.name.localeCompare(b.name));
}

// ── Compute combined KO+group standings ───────────────────────────────────────
// Returns array sorted by: totalPts desc → correctChampion desc →
//   totalCorrect desc → name asc.
function computeCombinedStandings(groupStandings, koPicksData, koResults, bracketData) {
  const KO_MATCH_NUMS = [
    73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,
    89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,
  ];

  function matchRound(m) {
    if (m >= 73 && m <= 88)         return 1;  // R32
    if (m >= 89 && m <= 96)         return 2;  // R16
    if (m >= 97 && m <= 100)        return 3;  // QF
    if (m === 101 || m === 102)     return 4;  // SF
    return 5;                                  // 3rd / Final
  }

  // A pick for match m is cascaded if eliminatedInRound[team] < threshold.
  // M103: SF losers (round 4) are valid → threshold 4 (must be < 4 to cascade).
  // M104: SF winners only → threshold 5.
  function cascadeThreshold(m) {
    if (m >= 73 && m <= 88)         return 0;
    if (m >= 89 && m <= 96)         return 2;
    if (m >= 97 && m <= 100)        return 3;
    if (m === 101 || m === 102)     return 4;
    if (m === 103)                  return 4;
    if (m === 104)                  return 5;
    return 0;
  }

  // Build eliminated map: team → round they were knocked out.
  const eliminatedInRound = {};
  for (const m of KO_MATCH_NUMS) {
    const winner = koResults[m];
    if (!winner || !bracketData) continue;
    try {
      const [t1, t2] = getKoTeams(m, bracketData, koResults);
      const loser = (t1 === winner) ? t2 : (t2 === winner) ? t1 : null;
      if (loser && !_isTbd(loser) && !(loser in eliminatedInRound)) {
        eliminatedInRound[loser] = matchRound(m);
      }
    } catch (e) { /* bracket not yet fully resolved */ }
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
        koPickResults[m] = { status: 'empty', pick: null, winner: winner || null };
      } else if (winner) {
        if (isCascaded) {
          koPickResults[m] = { status: 'cascaded', pick, winner };
        } else {
          const isCorrect = pick === winner;
          if (isCorrect) {
            koPts += KO_POINTS[m] || 0;
            totalCorrect++;
            if (m === 104) correctChampion = true;
          }
          koPickResults[m] = { status: isCorrect ? 'correct' : 'wrong', pick, winner };
        }
      } else {
        koPickResults[m] = { status: isCascaded ? 'cascaded' : 'pending', pick, winner: null };
      }
    }
    let koPossiblePts = koPts;
    for (const m of KO_MATCH_NUMS) {
      if (koPickResults[m].status === 'pending') koPossiblePts += KO_POINTS[m] || 0;
    }
    return { koPts, koPossiblePts, totalCorrect, correctChampion, koPickResults };
  }

  const combined = groupStandings.map(p => {
    const { koPts, koPossiblePts, totalCorrect: koCorrect, correctChampion, koPickResults } =
      evalKoPicks(koPicksData[p.name] || {});
    const grpCorrect = Object.values(p.pickResults || {}).filter(pr => pr.status === 'correct').length;
    return {
      ...p,
      groupPts: p.points,
      koPts,
      totalPts: p.points + koPts,
      maxPts: p.points + koPossiblePts,
      correctChampion,
      totalCorrect: grpCorrect + koCorrect,
      koPickResults,
    };
  });

  // Minimum group pts — floor baseline for KO-only participants
  const minGroupPts = groupStandings.length
    ? Math.min(...groupStandings.map(p => p.points))
    : 0;

  // Add KO-only participants not in group standings
  Object.keys(koPicksData).forEach(name => {
    if (!combined.find(p => p.name === name)) {
      const { koPts, koPossiblePts, totalCorrect, correctChampion, koPickResults } =
        evalKoPicks(koPicksData[name]);
      combined.push({ name, points: minGroupPts, groupPts: minGroupPts, pickResults: {}, koPts,
        totalPts: minGroupPts + koPts, maxPts: minGroupPts + koPossiblePts,
        correctChampion, totalCorrect, koPickResults,
        koOnly: true, groupPtsIsFloor: true });
    }
  });

  combined.sort((a, b) =>
    (b.totalPts - a.totalPts) ||
    ((b.correctChampion ? 1 : 0) - (a.correctChampion ? 1 : 0)) ||
    (b.totalCorrect - a.totalCorrect) ||
    a.name.localeCompare(b.name)
  );

  return combined;
}

// ── Node.js export ────────────────────────────────────────────────────────────
if (typeof module !== 'undefined') {
  module.exports = {
    MATCHES,
    KO_POINTS,
    parseResults,
    parseKoResults,
    parseKoScores,
    getKoTeams,
    computeStandings,
    computeCombinedStandings,
  };
}
