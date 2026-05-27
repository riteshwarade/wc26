'use strict';
/**
 * sim_core.js
 *
 * Shared simulation utilities used by test_e2e.js and gen_sim_data.js.
 * Provides a seeded PRNG, the R32 bracket topology, and participant
 * pick/result generators.  Everything here is deterministic given the seed.
 *
 * Usage (Node):
 *   const { resetSeed, randChoice, R32_TEAMS,
 *           generateKoTournament, generateGroupPicks, generateKoPicks,
 *         } = require('./sim_core.js');
 */

// ── Seeded PRNG (xorshift32) ──────────────────────────────────────────────────
// Default seed = 20260611 (tournament kick-off date).
// Call resetSeed() before each independent simulation to get reproducible results.

let _seed = 20260611;

function resetSeed(seed = 20260611) { _seed = seed; }

function rand() {
  _seed ^= _seed << 13;
  _seed ^= _seed >> 17;
  _seed ^= _seed << 5;
  return (_seed >>> 0) / 0xFFFFFFFF;
}
function randInt(n)       { return Math.floor(rand() * n); }
function randChoice(arr)  { return arr[randInt(arr.length)]; }

// ── R32 bracket — simulated team assignments ──────────────────────────────────
// These match simulate.py and the embedded LOCAL_BRACKET_DATA in the leaderboard.

const R32_TEAMS = {
  73:['Brazil','Morocco'],       74:['France','Norway'],
  75:['Spain','Ecuador'],        76:['Germany','Switzerland'],
  77:['Argentina','Mexico'],     78:['Netherlands','Senegal'],
  79:['England','Ivory Coast'],  80:['Portugal','Colombia'],
  81:['Belgium','United States'],82:['Croatia','Japan'],
  83:['South Korea','Saudi Arabia'],84:['Uruguay','Egypt'],
  85:['Turkey','Canada'],        86:['Austria','Sweden'],
  87:['Tunisia','Ghana'],        88:['Panama','Australia'],
};

// ── KO bracket topology ───────────────────────────────────────────────────────
// Canonical source: bracket.js (R16 / QF / SF).
// This Node-only copy is used by simulation scripts that don't load bracket.js.
// If you ever change the topology, update bracket.js first, then mirror here.
const R16 = {89:[74,77],90:[73,75],91:[76,78],92:[79,80],93:[83,84],94:[81,82],95:[86,88],96:[85,87]};
const QF  = {97:[89,90],98:[93,94],99:[91,92],100:[95,96]};
const SF  = {101:[97,98],102:[99,100]};

// ── Generators ────────────────────────────────────────────────────────────────

/**
 * Simulate a full 32-match knockout tournament.
 * Returns { winners, matchTeams } where:
 *   winners    = { matchNum → winnerName }
 *   matchTeams = { matchNum → [home, away] }
 */
function generateKoTournament() {
  const winners = {}, matchTeams = {};
  for (const [m, [home, away]] of Object.entries(R32_TEAMS)) {
    matchTeams[+m] = [home, away];
    winners[+m]    = randChoice([home, away]);
  }
  for (const feeds of [R16, QF, SF]) {
    for (const [m, [f1, f2]] of Object.entries(feeds)) {
      matchTeams[+m] = [winners[f1], winners[f2]];
      winners[+m]    = randChoice([winners[f1], winners[f2]]);
    }
  }
  // 3rd place: SF losers
  const [sf1h, sf1a] = matchTeams[101], [sf2h, sf2a] = matchTeams[102];
  const l101 = winners[101] === sf1h ? sf1a : sf1h;
  const l102 = winners[102] === sf2h ? sf2a : sf2h;
  matchTeams[103] = [l101, l102];  winners[103] = randChoice([l101, l102]);
  // Final: SF winners
  matchTeams[104] = [winners[101], winners[102]];
  winners[104]    = randChoice([winners[101], winners[102]]);
  return { winners, matchTeams };
}

/**
 * Generate random group-stage picks for one participant.
 * matchNums is an array of match numbers (e.g. from MATCHES.map(m => m[0])).
 * Returns { '1': 'W1', '2': 'Draw', ... }
 */
function generateGroupPicks(matchNums) {
  const picks = {};
  for (const num of matchNums) {
    picks[String(num)] = randChoice(['W1', 'W2', 'Draw']);
  }
  return picks;
}

/**
 * Generate KO picks for one participant, round by round from real R32 teams.
 * Returns { '73': 'Brazil', '89': 'Brazil', ..., '104': 'France' }
 */
function generateKoPicks() {
  const picks = {}, myW = {}, myT = { ...R32_TEAMS };
  for (const [m, [home, away]] of Object.entries(R32_TEAMS)) {
    myW[+m]       = randChoice([home, away]);
    picks[String(m)] = myW[+m];
  }
  for (const feeds of [R16, QF, SF]) {
    for (const [m, [f1, f2]] of Object.entries(feeds)) {
      myT[+m]          = [myW[f1], myW[f2]];
      myW[+m]          = randChoice([myW[f1], myW[f2]]);
      picks[String(m)] = myW[+m];
    }
  }
  // 3rd place: pick from own SF losers (always a valid pick for M103)
  const [sf1h, sf1a] = myT[101], [sf2h, sf2a] = myT[102];
  const l101 = myW[101] === sf1h ? sf1a : sf1h;
  const l102 = myW[102] === sf2h ? sf2a : sf2h;
  picks['103'] = randChoice([l101, l102]);
  // Final: pick one of own SF winners at random
  picks['104'] = randChoice([myW[101], myW[102]]);
  return picks;
}

if (typeof module !== 'undefined') {
  module.exports = {
    resetSeed, rand, randInt, randChoice,
    R32_TEAMS, R16, QF, SF,
    generateKoTournament, generateGroupPicks, generateKoPicks,
  };
}
