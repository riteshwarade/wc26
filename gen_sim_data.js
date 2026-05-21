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

// ── Seeded PRNG (xorshift32) ──────────────────────────────
let _seed = 20260611;
function rand() {
  _seed ^= _seed << 13; _seed ^= _seed >> 17; _seed ^= _seed << 5;
  return (_seed >>> 0) / 0xFFFFFFFF;
}
function randChoice(arr) { return arr[Math.floor(rand() * arr.length)]; }

// ── Match data ────────────────────────────────────────────
const MATCHES = [
  [1,'Mexico','South Africa'],[2,'South Korea','Czech Republic'],
  [3,'Canada','Bosnia and Herzegovina'],[4,'United States','Paraguay'],
  [5,'Haiti','Scotland'],[6,'Australia','Turkey'],
  [7,'Brazil','Morocco'],[8,'Qatar','Switzerland'],
  [9,'Ivory Coast','Ecuador'],[10,'Germany','Curaçao'],
  [11,'Netherlands','Japan'],[12,'Sweden','Tunisia'],
  [13,'Saudi Arabia','Uruguay'],[14,'Spain','Cape Verde'],
  [15,'Iran','New Zealand'],[16,'Belgium','Egypt'],
  [17,'France','Senegal'],[18,'Iraq','Norway'],
  [19,'Argentina','Algeria'],[20,'Austria','Jordan'],
  [21,'Ghana','Panama'],[22,'England','Croatia'],
  [23,'Portugal','DR Congo'],[24,'Uzbekistan','Colombia'],
  [25,'Czech Republic','South Africa'],[26,'Switzerland','Bosnia and Herzegovina'],
  [27,'Canada','Qatar'],[28,'Mexico','South Korea'],
  [29,'Brazil','Haiti'],[30,'Scotland','Morocco'],
  [31,'Turkey','Paraguay'],[32,'United States','Australia'],
  [33,'Germany','Ivory Coast'],[34,'Ecuador','Curaçao'],
  [35,'Netherlands','Sweden'],[36,'Tunisia','Japan'],
  [37,'Uruguay','Cape Verde'],[38,'Spain','Saudi Arabia'],
  [39,'Belgium','Iran'],[40,'New Zealand','Egypt'],
  [41,'Norway','Senegal'],[42,'France','Iraq'],
  [43,'Argentina','Austria'],[44,'Jordan','Algeria'],
  [45,'England','Ghana'],[46,'Panama','Croatia'],
  [47,'Portugal','Uzbekistan'],[48,'Colombia','DR Congo'],
  [49,'Scotland','Brazil'],[50,'Morocco','Haiti'],
  [51,'Switzerland','Canada'],[52,'Bosnia and Herzegovina','Qatar'],
  [53,'Czech Republic','Mexico'],[54,'South Africa','South Korea'],
  [55,'Curaçao','Ivory Coast'],[56,'Ecuador','Germany'],
  [57,'Japan','Sweden'],[58,'Tunisia','Netherlands'],
  [59,'Turkey','United States'],[60,'Paraguay','Australia'],
  [61,'Norway','France'],[62,'Senegal','Iraq'],
  [63,'Egypt','Iran'],[64,'New Zealand','Belgium'],
  [65,'Cape Verde','Saudi Arabia'],[66,'Uruguay','Spain'],
  [67,'Panama','England'],[68,'Croatia','Ghana'],
  [69,'Algeria','Austria'],[70,'Jordan','Argentina'],
  [71,'Colombia','Portugal'],[72,'DR Congo','Uzbekistan'],
];

const R32_TEAMS = {
  73:['Brazil','Morocco'],      74:['France','Norway'],
  75:['Spain','Ecuador'],       76:['Germany','Switzerland'],
  77:['Argentina','Mexico'],    78:['Netherlands','Senegal'],
  79:['England','Ivory Coast'], 80:['Portugal','Colombia'],
  81:['Belgium','United States'],82:['Croatia','Japan'],
  83:['South Korea','Saudi Arabia'],84:['Uruguay','Egypt'],
  85:['Turkey','Canada'],       86:['Austria','Sweden'],
  87:['Tunisia','Ghana'],       88:['Panama','Australia'],
};

const R16 = {89:[74,77],90:[73,75],91:[76,78],92:[79,80],93:[83,84],94:[81,82],95:[86,88],96:[85,87]};
const QF  = {97:[89,90],98:[93,94],99:[91,92],100:[95,96]};
const SF  = {101:[97,98],102:[99,100]};
const KO_ORDER = [...Array.from({length:16},(_,i)=>73+i),
                  ...Array.from({length:8},(_,i)=>89+i),
                  ...Array.from({length:4},(_,i)=>97+i),
                  101,102,103,104];

// ── Generators ────────────────────────────────────────────

function generateGroupResults() {
  const rows = ['match,home_score,away_score,outcome'];
  for (const [num] of MATCHES) {
    const outcome = randChoice(['W1','W2','Draw']);
    let h, a;
    if (outcome==='W1')  { h=Math.floor(rand()*3)+1; a=Math.floor(rand()*h); }
    else if (outcome==='W2') { a=Math.floor(rand()*3)+1; h=Math.floor(rand()*a); }
    else { const s=Math.floor(rand()*3); h=s; a=s; }
    rows.push(`${num},${h},${a},${outcome}`);
  }
  return rows.join('\n');
}

function generateKoTournament() {
  const winners = {}, matchTeams = {};
  for (const [m,[home,away]] of Object.entries(R32_TEAMS)) {
    matchTeams[+m] = [home, away];
    winners[+m] = randChoice([home, away]);
  }
  for (const feeds of [R16, QF, SF]) {
    for (const [m,[f1,f2]] of Object.entries(feeds)) {
      matchTeams[+m] = [winners[f1], winners[f2]];
      winners[+m] = randChoice([winners[f1], winners[f2]]);
    }
  }
  const [sf1h,sf1a]=matchTeams[101], [sf2h,sf2a]=matchTeams[102];
  const l101 = winners[101]===sf1h ? sf1a : sf1h;
  const l102 = winners[102]===sf2h ? sf2a : sf2h;
  matchTeams[103]=[l101,l102]; winners[103]=randChoice([l101,l102]);
  matchTeams[104]=[winners[101],winners[102]]; winners[104]=randChoice([winners[101],winners[102]]);
  return { winners, matchTeams };
}

function generateKoResultsCsv(winners) {
  return ['match,winner', ...KO_ORDER.map(m=>`${m},${winners[m]}`)].join('\n');
}

function generateGroupPicks() {
  const picks = {};
  for (const [num] of MATCHES) picks[String(num)] = randChoice(['W1','W2','Draw']);
  return picks;
}

function generateKoPicks(koWinners, koMatchTeams) {
  const picks = {}, myW = {}, myT = {...R32_TEAMS};
  for (const [m,[home,away]] of Object.entries(R32_TEAMS)) {
    myW[+m] = randChoice([home, away]);
    picks[String(m)] = myW[+m];
  }
  for (const feeds of [R16, QF, SF]) {
    for (const [m,[f1,f2]] of Object.entries(feeds)) {
      myT[+m] = [myW[f1], myW[f2]];
      myW[+m] = randChoice([myW[f1], myW[f2]]);
      picks[String(m)] = myW[+m];
    }
  }
  const [sf1h,sf1a]=myT[101],[sf2h,sf2a]=myT[102];
  const l101=myW[101]===sf1h?sf1a:sf1h, l102=myW[102]===sf2h?sf2a:sf2h;
  picks['103'] = randChoice([l101, l102]);
  picks['104'] = randChoice([myW[101], myW[102]]);
  return picks;
}

// ── Run ───────────────────────────────────────────────────

const NAMES = ['Alice','Bob','Carol','Dave','Eve','Frank','Grace','Hank','Ivy','Jack'];

const localResultsCsv   = generateGroupResults();
const { winners, matchTeams } = generateKoTournament();
const localKoResultsCsv = generateKoResultsCsv(winners);

const localPicks   = {};
const localKoPicks = {};
for (const name of NAMES) {
  localPicks[name]   = generateGroupPicks();
  localKoPicks[name] = generateKoPicks(winners, matchTeams);
}

const localBracketData = {
  confirmed: true,
  round_of_32: Object.fromEntries(
    Object.entries(R32_TEAMS).map(([m,[home,away]])=>[m,{home,away}])
  ),
};

// ── Print summary ─────────────────────────────────────────
console.error(`Champion    : ${winners[104]}`);
console.error(`Finalist    : ${winners[101]} vs ${winners[102]}`);
console.error(`3rd place   : ${winners[103]}`);
console.error(`Participants: ${NAMES.join(', ')}`);

// ── Output JSON ───────────────────────────────────────────
const output = { localPicks, localResultsCsv, localKoPicks, localKoResultsCsv, localBracketData };
process.stdout.write(JSON.stringify(output, null, 2));
