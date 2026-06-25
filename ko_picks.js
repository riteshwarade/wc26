// ko_picks.js — WC2026 Pool knockout picks page logic
// Depends on: bracket.js
// FLAGS, RANKINGS, KO_SCHEDULE, R16, QF, SF, isTbd, slotCls, matchCard,
// buildBracketHtml, buildPodiumHtml, positionAndConnectBracket → bracket.js

const BRACKET_URL = 'https://raw.githubusercontent.com/riteshwarade/wc26/main/data/knockout_bracket.json';

var r32Teams = {}; // { matchNum: [home, away] } — from knockout_bracket.json
var picks    = {}; // { matchNum: winnerName }   — user's current picks
var r32Data  = {}; // round_of_32 from knockout_bracket.json — includes wiki_home/wiki_away

// ── feedsInto[m] = the match that the winner of m feeds into ──
// Built at runtime from R16/QF/SF topology in bracket.js.
var feedsInto = {};
function buildFeedsInto() {
  for (const [next, feeders] of Object.entries({...R16, ...QF, ...SF}))
    for (const f of feeders) feedsInto[f] = +next;
  feedsInto[101] = 104; // SF1 winner → Final
  feedsInto[102] = 104; // SF2 winner → Final
  // Note: SF losers → M103 (3rd place) is handled separately in clearInvalidDownstream
}

// ── Process matches in round order so each shortcut cascades correctly ──
const MATCH_ORDER = [
  73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88, // R32
  89,90,91,92,93,94,95,96,                          // R16
  97,98,99,100,                                      // QF
  101,102,                                           // SF
  103,104,                                           // 3rd place & Final
];

function koRoundLabel(m) {
  if (m >= 73 && m <= 88)  return 'R32';
  if (m >= 89 && m <= 96)  return 'R16';
  if (m >= 97 && m <= 100) return 'QF';
  if (m === 101 || m === 102) return 'SF';
  if (m === 103) return '3rd';
  if (m === 104) return 'Final';
  return '';
}

// ── Resolve teams for any match based on current picks ──
function getTeams(m) {
  if (r32Teams[m]) return r32Teams[m];
  if (R16[m]) return [picks[R16[m][0]] || `W${R16[m][0]}`, picks[R16[m][1]] || `W${R16[m][1]}`];
  if (QF[m])  return [picks[QF[m][0]]  || `W${QF[m][0]}`,  picks[QF[m][1]]  || `W${QF[m][1]}`];
  if (SF[m])  return [picks[SF[m][0]]  || `W${SF[m][0]}`,  picks[SF[m][1]]  || `W${SF[m][1]}`];
  if (m === 104) return [picks[101] || 'W101', picks[102] || 'W102'];
  if (m === 103) {
    // Teams are the losers of each SF match
    const [h1, a1] = getTeams(101);
    const [h2, a2] = getTeams(102);
    const loser101 = picks[101] ? (picks[101] === h1 ? a1 : h1) : 'L101';
    const loser102 = picks[102] ? (picks[102] === h2 ? a2 : h2) : 'L102';
    return [loser101, loser102];
  }
  return ['TBD', 'TBD'];
}

// ── Clear any picks that became invalid after picks[m] changed ──
function clearInvalidDownstream(m) {
  // Winner path: feedsInto[m] is the next match this winner populates
  const nextM = feedsInto[m];
  if (nextM !== undefined) {
    const [h, a] = getTeams(nextM);
    if (picks[nextM] && picks[nextM] !== h && picks[nextM] !== a) {
      delete picks[nextM];
      clearInvalidDownstream(nextM);
    }
  }
  // Loser path: SF losers feed M103 (3rd place match)
  if (m === 101 || m === 102) {
    const [h3, a3] = getTeams(103);
    if (picks[103] && picks[103] !== h3 && picks[103] !== a3) {
      delete picks[103];
    }
  }
}

// ── Build one card's HTML (shared by full render and surgical update) ──
function mkCard(m) {
  const [h, a]   = getTeams(m);
  const picked   = picks[m];
  const slot     = m >= 73 && m <= 88 ? r32Data[String(m)] : null;
  const hSlotCls = slot && !isTbd(h) ? slotCls(slot.wiki_home ?? null, h, a) : '';
  const aSlotCls = slot && !isTbd(a) ? slotCls(slot.wiki_away ?? null, h, a) : '';
  const homeCls  = picked ? (picked === h ? 'w' : 'l') : hSlotCls;
  const awayCls  = picked ? (picked === a ? 'w' : 'l') : aSlotCls;
  // Both teams must be known AND Wikipedia-confirmed before the match is pickable
  const bothPickable = !isTbd(h) && !isTbd(a) && hSlotCls === '' && aSlotCls === '';
  const homeAttrs = bothPickable ? `data-match="${m}" data-team="${h.replace(/"/g,'&quot;')}"` : '';
  const awayAttrs = bothPickable ? `data-match="${m}" data-team="${a.replace(/"/g,'&quot;')}"` : '';
  return matchCard(m, h, a, '', '', '', homeCls, awayCls, homeAttrs, awayAttrs);
}

// ── Surgical card update — no re-render, no repositioning, no flash ──
// Replaces only the card HTML for each match in place, preserving style.top
// on absolutely-positioned cards (R16+). Connectors don't change because
// card heights are fixed (always 2 team rows).
function updateCards() {
  const container = document.getElementById('bracketContainer');
  for (const m of MATCH_ORDER) {
    const cardEl = container.querySelector(`.bk-card[data-match="${m}"]`);
    if (!cardEl) continue;
    const savedTop = cardEl.style.top; // preserve absolute position of R16+ cards
    cardEl.outerHTML = mkCard(m);
    if (savedTop) {
      // Re-query since outerHTML replaced the element
      const newEl = container.querySelector(`.bk-card[data-match="${m}"]`);
      if (newEl) newEl.style.top = savedTop;
    }
  }

  // Update podium in-place
  const [h104, a104] = getTeams(104);
  const champion   = picks[104] || null;
  const runnerUp   = champion ? (champion === h104 ? a104 : h104) : null;
  const podiumEl   = document.getElementById('bk-podium-results');
  if (podiumEl) podiumEl.outerHTML = buildPodiumHtml(champion, runnerUp, picks[103] || null);

  // Update mobile pick cards (surgical — preserves active tab)
  for (const m of MATCH_ORDER) {
    const mobEl = document.getElementById(`mob-card-${m}`);
    if (mobEl) mobEl.outerHTML = mobPickCard(m);
  }

  // Update progress bar
  const done = Object.keys(picks).length;
  document.getElementById('progressFill').style.width = `${(done / 32) * 100}%`;
  document.getElementById('progressCount').textContent = `${done} / 32 matches picked`;
}

// ── Round-advance toast with countdown ──
const ROUND_FULL_LABELS = {
  r32: 'Round of 32', r16: 'Round of 16', qf: 'Quarter-Finals',
  sf: 'Semi-Finals', '3rd': '3rd Place Match', fin: 'Final',
};

function showAdvanceToast(nextRound) {
  // Cancel any in-progress toast
  const existing = document.getElementById('tab-advance-toast');
  if (existing) {
    existing._cancel?.();
    existing.remove();
  }

  const toast = document.createElement('div');
  toast.id = 'tab-advance-toast';
  toast.className = 'tab-advance-toast';
  document.body.appendChild(toast);

  let remaining = 3;
  let cancelled = false;

  function updateText() {
    toast.textContent = `Moving to ${ROUND_FULL_LABELS[nextRound.id]} in ${remaining}s…`;
  }
  updateText();

  // Fade in
  requestAnimationFrame(() => requestAnimationFrame(() => toast.classList.add('visible')));

  const interval = setInterval(() => {
    if (cancelled) return;
    remaining--;
    if (remaining > 0) {
      updateText();
    } else {
      clearInterval(interval);
      toast.classList.remove('visible');
      setTimeout(() => {
        if (cancelled) return;
        toast.remove();
        switchBracketTab(nextRound.id);
        const tabsEl = document.querySelector('.bk-mobile-tabs');
        if (tabsEl) tabsEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 200);
    }
  }, 1000);

  toast._cancel = () => { cancelled = true; clearInterval(interval); };
}

// ── Auto-advance to next tab when all picks in current tab are done (mobile) ──
function maybeAdvanceTab() {
  const activeTab = document.querySelector('.bk-tab.active');
  if (!activeTab) return;
  const roundIdx = MOB_ROUNDS.findIndex(r => r.id === activeTab.dataset.round);
  if (roundIdx < 0 || roundIdx >= MOB_ROUNDS.length - 1) return; // already on last tab
  const currentRound = MOB_ROUNDS[roundIdx];
  if (currentRound.matches.every(m => !!picks[m])) {
    showAdvanceToast(MOB_ROUNDS[roundIdx + 1]);
  }
}

// ── Pick a winner for match m, cascade downstream ──
function pickTeam(m, team) {
  if (!team) return; // guard: click bubbled to .bk-card (has data-match but no data-team)
  picks[m] = team;
  clearInvalidDownstream(m);
  updateCards(); // surgical — no re-render
  maybeAdvanceTab();
}

// ── Full render (initial load only) ──
function renderBracket() {
  const el = document.getElementById('bracketContainer');

  // Derive podium from current picks
  const [h104, a104] = getTeams(104);
  const champion   = picks[104] || null;
  const runnerUp   = champion ? (champion === h104 ? a104 : h104) : null;
  const thirdPlace = picks[103] || null;

  el.innerHTML = buildBracketHtml(mkCard, { podiumHtml: buildPodiumHtml(champion, runnerUp, thirdPlace) }) + buildMobTabHtml();
  requestAnimationFrame(() => requestAnimationFrame(positionAndConnectBracket));

  // Update progress bar
  const done = Object.keys(picks).length;
  document.getElementById('progressFill').style.width = `${(done / 32) * 100}%`;
  document.getElementById('progressCount').textContent = `${done} / 32 matches picked`;
}

// ── Shortcuts ──
function pickRandom() {
  picks = {};
  for (const m of MATCH_ORDER) {
    const [h, a] = getTeams(m);
    if (!isTbd(h) && !isTbd(a)) picks[m] = Math.random() < 0.5 ? h : a;
  }
  updateCards();
}

function pickFavourites() {
  picks = {};
  for (const m of MATCH_ORDER) {
    const [h, a] = getTeams(m);
    if (!isTbd(h) && !isTbd(a))
      picks[m] = (RANKINGS[h] || 999) <= (RANKINGS[a] || 999) ? h : a;
  }
  updateCards();
}

function resetPicks() {
  picks = {};
  updateCards();
}

// Wire up shortcut buttons and click delegation (browser only)
if (typeof document !== 'undefined' && typeof module === 'undefined') {
  const _btns = document.querySelectorAll('.shortcut-btn');
  _btns[0].addEventListener('click', pickRandom);
  _btns[1].addEventListener('click', pickFavourites);
  _btns[2].addEventListener('click', resetPicks);

  document.getElementById('bracketContainer').addEventListener('click', e => {
    const row = e.target.closest('[data-match]');
    if (!row) return;
    pickTeam(+row.dataset.match, row.dataset.team);
  });
}

// ── Submit / CSV download ──────────────────────────────────────────────────
function handleSubmit() {
  const name   = document.getElementById('entrantName').value.trim();
  const valMsg = document.getElementById('validationMsg');
  valMsg.style.background   = '#fff8e6';
  valMsg.style.borderColor  = 'var(--swiftly-orange)';
  valMsg.style.color        = '#7a4a00';
  valMsg.style.display      = 'none';
  document.getElementById('confirmRow').classList.remove('visible');

  if (!name) {
    valMsg.textContent = 'Please enter your name before submitting.';
    valMsg.style.display = 'block';
    document.getElementById('entrantName').focus();
    return;
  }

  const done = Object.keys(picks).length;
  if (done < 32) {
    const remaining = 32 - done;
    valMsg.textContent = `You still have ${remaining} match${remaining === 1 ? '' : 'es'} without a pick. Please complete all 32 matches before submitting.`;
    valMsg.style.display = 'block';
    return;
  }

  document.getElementById('confirmRow').classList.add('visible');
  document.getElementById('submitBtn').style.display = 'none';
}

function confirmSubmit() {
  const name = document.getElementById('entrantName').value.trim();
  downloadCSV(name);
  document.getElementById('confirmRow').classList.remove('visible');
  const valMsg = document.getElementById('validationMsg');
  valMsg.style.background  = '#ebf9ff';
  valMsg.style.borderColor = 'var(--swiftly-blue)';
  valMsg.style.color       = 'var(--neutral-darkest)';
  valMsg.textContent = '✓ Done! Your picks have been downloaded as a CSV file. Please send to Ritesh.';
  valMsg.style.display = 'block';
  document.getElementById('submitBtn').style.display = '';
}

function downloadCSV(name) {
  const escape = v => (String(v).includes(',') ? `"${v}"` : v);
  const rows = [['match', 'round', 'matchup', 'pick']];
  for (const m of MATCH_ORDER) {
    const [home, away] = getTeams(m);
    const matchup = escape(`${home} v ${away}`);
    rows.push([m, koRoundLabel(m), matchup, escape(picks[m] || '')]);
  }
  const csv  = rows.map(r => r.join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = `wc26_knockout_${name.replace(/\s+/g, '-').toLowerCase()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Mobile tab view (Variant 2) ──────────────────────────────────────────────
function switchBracketTab(roundId) {
  document.querySelectorAll('.bk-tab').forEach(b =>
    b.classList.toggle('active', b.dataset.round === roundId));
  document.querySelectorAll('.bk-tab-panel').forEach(p =>
    p.classList.toggle('active', p.id === 'bk-panel-' + roundId));
}

const MOB_ROUNDS = [
  { id: 'r32', label: 'R32',   matches: [74,77,73,75,83,84,81,82,76,78,79,80,86,88,85,87] },
  { id: 'r16', label: 'R16',   matches: [89,90,93,94,91,92,95,96] },
  { id: 'qf',  label: 'QF',    matches: [97,98,99,100] },
  { id: 'sf',  label: 'SF',    matches: [101,102] },
  { id: '3rd', label: '3rd',   matches: [103] },
  { id: 'fin', label: 'Final', matches: [104] },
];

function mobPickCard(m) {
  const [h, a]   = getTeams(m);
  const picked   = picks[m];
  const hTbd = isTbd(h), aTbd = isTbd(a);
  const slot     = m >= 73 && m <= 88 ? r32Data[String(m)] : null;
  const hSlotCls = slot && !hTbd ? slotCls(slot.wiki_home ?? null, h, a) : '';
  const aSlotCls = slot && !aTbd ? slotCls(slot.wiki_away ?? null, h, a) : '';
  let hCls = picked ? (picked === h ? ' w' : ' l') : (hSlotCls ? ' ' + hSlotCls : '');
  let aCls = picked ? (picked === a ? ' w' : ' l') : (aSlotCls ? ' ' + aSlotCls : '');
  // Both teams must be known AND Wikipedia-confirmed before the match is pickable
  const bothPickable = !hTbd && !aTbd && hSlotCls === '' && aSlotCls === '';
  const date   = KO_SCHEDULE[m] ? ` · ${koDisplay(m)}` : '';
  const hAttrs = bothPickable ? ` data-match="${m}" data-team="${h.replace(/"/g,'&quot;')}"` : '';
  const aAttrs = bothPickable ? ` data-match="${m}" data-team="${a.replace(/"/g,'&quot;')}"` : '';
  const hHtml  = hTbd ? h : teamHtml(h);
  const aHtml  = aTbd ? a : teamHtml(a);
  return `<div class="bk-mob-match" id="mob-card-${m}">
    <div class="bk-mob-meta">${roundLabel(m)} · M${m}${date}</div>
    <div class="bk-mob-teams">
      <div class="bk-mob-pick-team${hTbd ? ' tbd' : hCls}"${hAttrs}><span class="bk-mob-team-name">${hHtml}</span></div>
      <div class="bk-mob-pick-team${aTbd ? ' tbd' : aCls}"${aAttrs}><span class="bk-mob-team-name">${aHtml}</span></div>
    </div>
  </div>`;
}

const PAIR_NEXT = {
  r32: [['R16','M89'],['R16','M90'],['R16','M93'],['R16','M94'],['R16','M91'],['R16','M92'],['R16','M95'],['R16','M96']],
  r16: [['QF','M97'],['QF','M98'],['QF','M99'],['QF','M100']],
  qf:  [['SF','M101'],['SF','M102']],
  sf:  [['Final','M104']],
};

function buildMobTabHtml() {
  // Auto-open first round with any unpicked matches
  let activeRound = MOB_ROUNDS[MOB_ROUNDS.length - 1].id;
  for (const r of MOB_ROUNDS) {
    if (r.matches.some(m => !picks[m])) { activeRound = r.id; break; }
  }
  const tabBar = MOB_ROUNDS.map(r =>
    `<button class="bk-tab${r.id === activeRound ? ' active' : ''}" onclick="switchBracketTab('${r.id}')" data-round="${r.id}">${r.label}</button>`
  ).join('');
  const panels = MOB_ROUNDS.map(r => {
    const pairs = PAIR_NEXT[r.id] || [];
    let html = '';
    for (let i = 0; i < r.matches.length; i += 2) {
      const m1 = r.matches[i];
      const m2 = r.matches[i + 1];
      const pair = pairs[i / 2];
      if (m2 !== undefined && pair) {
        const [rl, mn] = pair;
        html += `<div class="bk-mob-pair-group">`;
        html += mobPickCard(m1);
        html += `<div class="bk-mob-pair-pill"><span>winners meet in ${rl} · ${mn}</span></div>`;
        html += mobPickCard(m2);
        html += `</div>`;
      } else {
        html += mobPickCard(m1);
        if (m2 !== undefined) html += mobPickCard(m2);
      }
    }
    return `<div class="bk-tab-panel${r.id === activeRound ? ' active' : ''}" id="bk-panel-${r.id}">${html}</div>`;
  }).join('');
  return `<div class="bk-mobile-tabs"><div class="bk-tab-bar">${tabBar}</div>${panels}</div>`;
}

// ── Load bracket JSON, then render ──
async function init() {
  const el = document.getElementById('bracketContainer');

  let bracketData = null;
  try {
    const resp = await fetch(`${BRACKET_URL}?t=${Date.now()}`);
    if (resp.ok) bracketData = await resp.json();
  } catch (e) { /* offline or file not yet generated */ }

  if (!bracketData) {
    el.innerHTML = '<div style="padding:40px;text-align:center;color:var(--neutral-dark);font-size:0.875rem;">Bracket not yet available — check back after all group matches are complete (around Jun 27).</div>';
    return;
  }

  // Populate r32Teams + r32Data (includes wiki_home/wiki_away for slot confirmation)
  r32Data = bracketData.round_of_32 || {};
  for (let m = 73; m <= 88; m++) {
    const slot = r32Data[String(m)];
    if (slot && slot.home && slot.away) r32Teams[m] = [slot.home, slot.away];
  }

  buildFeedsInto();
  renderBracket();
}

if (typeof module === 'undefined') init();

// ── Node.js exports (for unit tests) ──────────────────────
// Exports pure functions and mutable state references.
// Call buildFeedsInto() after setting up R16/QF/SF globals.
if (typeof module !== 'undefined') {
  module.exports = {
    feedsInto, picks, r32Teams,
    buildFeedsInto, getTeams, clearInvalidDownstream, MATCH_ORDER,
  };
}
