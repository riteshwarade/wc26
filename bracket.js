// bracket.js — shared bracket rendering primitives
// Used by: WC2026_Pool_Leaderboard_*.html (Variant 1)
//           WC2026_Pool_Knockout_Picks_*.html (Variant 2)
//           Results bracket during knockout (Variant 3)
//
// Each page includes this file, then defines its own renderBracket()
// that calls buildBracketHtml(mkCard) with a page-specific card builder.

// ── Inject shared bracket CSS once ───────────────────────
// Handles .bk-header-strip (sticky round headers). Injected here so all
// three variants get it automatically without per-page style changes.
(function injectBracketCss() {
  if (document.getElementById('bk-shared-css')) return;
  const s = document.createElement('style');
  s.id = 'bk-shared-css';
  s.textContent = `
    .bk-outer { position: relative; }
    .bk-header-strip {
      position: sticky;
      z-index: 50;
      background: var(--neutral-lightest, #f7f7f7);
      display: flex;
      width: 100%;
      padding: 0 4px;
    }
    .bk-header-strip .bk-col-hdr { margin-bottom: 0; padding-top: 6px; padding-bottom: 7px; }
  `;
  document.head.appendChild(s);
})();

// ── Flag emoji lookup ─────────────────────────────────────
const FLAGS = {
  'Mexico':'🇲🇽','South Africa':'🇿🇦','South Korea':'🇰🇷','Czech Republic':'🇨🇿',
  'Canada':'🇨🇦','Bosnia and Herzegovina':'🇧🇦','Qatar':'🇶🇦','Switzerland':'🇨🇭',
  'Brazil':'🇧🇷','Morocco':'🇲🇦','Haiti':'🇭🇹','Scotland':'🏴󠁧󠁢󠁳󠁣󠁴󠁿',
  'United States':'🇺🇸','Paraguay':'🇵🇾','Australia':'🇦🇺','Turkey':'🇹🇷',
  'Germany':'🇩🇪','Curaçao':'🇨🇼','Ivory Coast':'🇨🇮','Ecuador':'🇪🇨',
  'Netherlands':'🇳🇱','Japan':'🇯🇵','Sweden':'🇸🇪','Tunisia':'🇹🇳',
  'Belgium':'🇧🇪','Egypt':'🇪🇬','Iran':'🇮🇷','New Zealand':'🇳🇿',
  'Spain':'🇪🇸','Cape Verde':'🇨🇻','Saudi Arabia':'🇸🇦','Uruguay':'🇺🇾',
  'France':'🇫🇷','Senegal':'🇸🇳','Iraq':'🇮🇶','Norway':'🇳🇴',
  'Argentina':'🇦🇷','Algeria':'🇩🇿','Austria':'🇦🇹','Jordan':'🇯🇴',
  'Portugal':'🇵🇹','DR Congo':'🇨🇩','Uzbekistan':'🇺🇿','Colombia':'🇨🇴',
  'England':'🏴󠁧󠁢󠁥󠁮󠁧󠁿','Croatia':'🇭🇷','Ghana':'🇬🇭','Panama':'🇵🇦',
};

// ── FIFA rankings ─────────────────────────────────────────
// Used for tiebreaking, display, and "pick higher-ranked" shortcut.
// Canonical source: data/rankings.json (parse_results.py loads from there).
// Keep this copy in sync with data/rankings.json when updating rankings.
const RANKINGS = {
  'Mexico':15,'South Africa':60,'South Korea':25,'Czech Republic':41,
  'Canada':30,'Bosnia and Herzegovina':65,'Qatar':55,'Switzerland':19,
  'Brazil':6,'Morocco':8,'Haiti':83,'Scotland':43,
  'United States':16,'Paraguay':40,'Australia':27,'Turkey':22,
  'Germany':10,'Curaçao':82,'Ivory Coast':34,'Ecuador':23,
  'Netherlands':7,'Japan':18,'Sweden':38,'Tunisia':44,
  'Belgium':9,'Egypt':29,'Iran':21,'New Zealand':85,
  'Spain':2,'Cape Verde':69,'Saudi Arabia':61,'Uruguay':17,
  'France':1,'Senegal':14,'Iraq':57,'Norway':31,
  'Argentina':3,'Algeria':28,'Austria':24,'Jordan':63,
  'Portugal':5,'DR Congo':46,'Uzbekistan':50,'Colombia':13,
  'England':4,'Croatia':11,'Ghana':74,'Panama':33,
};

// ── Knockout match UTC kick-off times (ISO 8601) ──────────
// Verified against ESPN API (fifa.world scoreboard).
// R32 times confirmed by matching ESPN team-slot descriptions to R32_SLOTS.
// R16/QF/SF/Final assigned chronologically within each local date.
const KO_SCHEDULE = {
  // Round of 32 (Jun 28 – Jul 3)
  73:'2026-06-28T19:00Z',
  74:'2026-06-29T20:30Z', 75:'2026-06-30T01:00Z', 76:'2026-06-29T17:00Z',
  77:'2026-06-30T21:00Z', 78:'2026-06-30T17:00Z', 79:'2026-07-01T02:00Z',
  80:'2026-07-01T16:00Z', 81:'2026-07-02T00:00Z', 82:'2026-07-01T20:00Z',
  83:'2026-07-02T23:00Z', 84:'2026-07-02T19:00Z', 85:'2026-07-03T03:00Z',
  86:'2026-07-03T22:00Z', 87:'2026-07-04T01:30Z', 88:'2026-07-03T18:00Z',
  // Round of 16 (Jul 4 – Jul 7)
  89:'2026-07-04T21:00Z', 90:'2026-07-04T17:00Z',
  91:'2026-07-05T20:00Z', 92:'2026-07-06T00:00Z',
  93:'2026-07-06T19:00Z', 94:'2026-07-07T00:00Z',
  95:'2026-07-07T16:00Z', 96:'2026-07-07T20:00Z',
  // Quarterfinals (Jul 9 – Jul 11)
  97:'2026-07-09T20:00Z', 98:'2026-07-10T19:00Z',
  99:'2026-07-11T21:00Z', 100:'2026-07-12T01:00Z',
  // Semifinals (Jul 14 – Jul 15)
  101:'2026-07-14T19:00Z', 102:'2026-07-15T19:00Z',
  // 3rd place & Final
  103:'2026-07-18T21:00Z', 104:'2026-07-19T19:00Z',
};

// ── Format a KO match time for display ────────────────────
// Returns e.g. "Mon, Jun 28 · 3:00 PM" in the viewer's local timezone (TZ abbreviation omitted).
function koDisplay(num) {
  const utc = KO_SCHEDULE[num];
  if (!utc) return '';
  try {
    const dt = new Date(utc);
    const dateStr = dt.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
    const timeStr = dt.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
    return `${dateStr} · ${timeStr}`;
  } catch(e) { return utc; }
}

// ── Bracket topology: feeders for each round ─────────────
// These define the bracket structure for all three variants.
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

// ── Round of 32 slot assignments ──────────────────────────
// match → [home slot, away slot]
// Slots: 1X = group X winner, 2X = group X runner-up, 3MNN = best 3rd (from match NN's group pool)
// Validated against FIFA/Wikipedia WC2026 bracket.
const R32_SLOTS = {
  73: ['2A','2B'], 74: ['1E','3M74'], 75: ['1F','2C'], 76: ['1C','2F'],
  77: ['1I','3M77'], 78: ['2E','2I'], 79: ['1A','3M79'], 80: ['1L','3M80'],
  81: ['1D','3M81'], 82: ['1G','3M82'], 83: ['2K','2L'], 84: ['1H','2J'],
  85: ['1B','3M85'], 86: ['1J','2H'], 87: ['1K','3M87'], 88: ['2D','2G'],
};
// Column index in the best-3rd combination array [M79,M85,M81,M74,M82,M77,M87,M80]
const THIRD_MATCH_COL = { 79:0, 85:1, 81:2, 74:3, 82:4, 77:5, 87:6, 80:7 };

// ── Mobile rounds (shared by all variants) ────────────────
// Round definitions for the mobile tab view. Matches listed in display order
// (mirrors R32_SLOTS for R32; chronological/natural order for later rounds).
const MOB_ROUNDS = [
  { id: 'r32', label: 'R32',   matches: [74,77,73,75,83,84,81,82,76,78,79,80,86,88,85,87] },
  { id: 'r16', label: 'R16',   matches: [89,90,93,94,91,92,95,96] },
  { id: 'qf',  label: 'QF',    matches: [97,98,99,100] },
  { id: 'sf',  label: 'SF',    matches: [101,102] },
  { id: '3rd', label: '3rd',   matches: [103] },
  { id: 'fin', label: 'Final', matches: [104] },
];

// ── Mobile pair-next lookup (shared by all variants) ─────
// Maps each mobile tab round to the next-round matches its winners feed into.
// Used by buildMobTabHtml() to render "winners meet in R16 · M89" connector pills.
// Order within each round matches the display order in MOB_ROUNDS.
const MOB_PAIR_NEXT = {
  r32: [['R16','M89'],['R16','M90'],['R16','M93'],['R16','M94'],['R16','M91'],['R16','M92'],['R16','M95'],['R16','M96']],
  r16: [['QF','M97'],['QF','M98'],['QF','M99'],['QF','M100']],
  qf:  [['SF','M101'],['SF','M102']],
  sf:  [['Final','M104']],
};

// ── Reusable team display: flag + name + rank ─────────────
// showRank=false when rank is shown separately (e.g. pick form rank column)
// display=string overrides the visible name text (e.g. shortened names in group tables)
function teamHtml(name, showRank=true, display=null) {
  if (!name) return '';
  const flag  = FLAGS[name] || '';
  const rank  = showRank ? (RANKINGS[name] || null) : null;
  const rankHtml = rank ? ` <span class="team-rank">(${rank})</span>` : '';
  return `${flag ? flag + ' ' : ''}${display || name}${rankHtml}`;
}

// ── TBD slot detection ────────────────────────────────────
function isTbd(name) {
  return !name || name === 'TBD' || /^[WL]\d+$/.test(name) || /^[12][A-L]$/.test(name) || /^3M\d+$/.test(name);
}

// ── Wikipedia R32 slot confirmation class ─────────────────
// Returns '' (confirmed), 'slot-tbd' (null/unconfirmed), or 'slot-mismatch' (wrong team).
// Order-independent: wiki team checked against both computed home and away
// because Wikipedia's row ordering may differ from our bracket topology.
// Used by leaderboard (Variant 1) and KO picks (Variant 2).
function slotCls(wikiTeam, compHome, compAway) {
  if (!wikiTeam) return 'slot-tbd';
  if (wikiTeam === compHome || wikiTeam === compAway) return '';
  return 'slot-mismatch';
}

// ── Single team row inside a bracket card ─────────────────
// extraAttrs: optional HTML attribute string, e.g. 'data-match="73" data-team="Mexico"'
// Used by Variant 2 (picks) to attach click-target data.
function bkTeamRow(name, stateCls, score, extraAttrs='') {
  const tbd  = isTbd(name);
  const cls  = tbd ? 'tbd' : (stateCls || '');
  const flag = tbd ? '—' : (FLAGS[name] || '🏳');
  // Name + rank only — flag is already in .bk-fl, so don't call teamHtml() here
  const rank     = (!tbd && RANKINGS[name]) ? RANKINGS[name] : null;
  const rankHtml = rank ? ` <span class="team-rank">(${rank})</span>` : '';
  const label    = tbd ? name : `${name}${rankHtml}`;
  const sc       = (score !== undefined && score !== null && score !== '')
                     ? `<span class="bk-sc">${score}</span>` : '';
  return `<div class="bk-team ${cls}"${extraAttrs ? ' ' + extraAttrs : ''}><span class="bk-fl">${flag}</span><span class="bk-tn">${label}</span>${sc}</div>`;
}

// ── Mobile team HTML: flag + name as separate flex children ──────────────
// Mirrors bkTeamRow structure so flag emoji doesn't inflate the text line-box.
// TBD placeholders (no flag) get just a .bk-mob-tn span.
function mobTeamHtml(name) {
  if (!name) return '';
  if (isTbd(name)) return `<span class="bk-mob-tn">${name}</span>`;
  const flag     = FLAGS[name] || '🏳';
  const rank     = RANKINGS[name] ? RANKINGS[name] : null;
  const rankHtml = rank ? ` <span class="team-rank">(${rank})</span>` : '';
  return `<span class="bk-mob-fl">${flag}</span><span class="bk-mob-tn">${name}${rankHtml}</span>`;
}

// ── Round label for a given match number ─────────────────
function roundLabel(num) {
  if (num >= 73 && num <= 88) return 'R32';
  if (num >= 89 && num <= 96) return 'R16';
  if (num >= 97 && num <= 100) return 'QF';
  if (num === 101 || num === 102) return 'SF';
  if (num === 103) return '3rd';
  if (num === 104) return 'Final';
  return '';
}

// ── Bracket match card ────────────────────────────────────
// homeAttrs / awayAttrs: optional extra HTML attributes for each team row.
// mnumLabelCls: if set, wraps the mnum text in <span class="..."> (e.g. 'bk-mnum-label')
// mnumExtra: HTML appended inside .bk-mnum after the (possibly wrapped) label text
//   — used by Variant 3 to inject correctness pills and live-minute spans without
//     post-hoc regex surgery on the returned HTML string.
function matchCard(num, home, away, label, homeScore, awayScore, homeCls, awayCls,
                   homeAttrs='', awayAttrs='', mnumExtra='', mnumLabelCls='', suppressDate=false) {
  const round = roundLabel(num);
  const date = (!suppressDate && KO_SCHEDULE[num]) ? ` · ${koDisplay(num)}` : '';
  const mnumText = `${round} · M${num}${date}${label ? ' · ' + label : ''}`;
  const mnumInner = mnumLabelCls
    ? `<span class="${mnumLabelCls}">${mnumText}</span>${mnumExtra}`
    : mnumText;
  return `<div class="bk-card" data-match="${num}">
    <div class="bk-mnum">${mnumInner}</div>
    ${bkTeamRow(home, homeCls, homeScore, homeAttrs)}
    ${bkTeamRow(away, awayCls, awayScore, awayAttrs)}
  </div>`;
}

// ── Build bracket HTML ────────────────────────────────────
// mkCard(matchNum) → HTML string
// Each page provides its own mkCard — the only thing that varies between
// variants is how teams and state are resolved per match.
//
// Bracket layout (top half → bottom half):
//   Top:    (M74,M77)+(M73,M75) → M89,M90 → M97
//           (M83,M84)+(M81,M82) → M93,M94 → M98  → M101
//   Bottom: (M76,M78)+(M79,M80) → M91,M92 → M99
//           (M86,M88)+(M85,M87) → M95,M96 → M100 → M102
//   3rd place M103 and Final M104 share the fin column.
// ── Podium / final results section ───────────────────────
// Renders champion, runner-up, and third-place in the fin column.
// Pass null for any team that isn't known yet — shows as TBD.
//
// Intended for Variant 2 (picks) and Variant 3 (live results).
// Currently also passed in Variant 1 for preview; will be removed there
// once Variants 2/3 are complete.
//
// CSS for .bk-podium must be present in the page's <style> block — see
// the "── Knockout bracket ──" section in the leaderboard pages.
function buildPodiumHtml(champion, runnerUp, thirdPlace) {
  function row(medal, team, rowCls) {
    const tbd = !team || isTbd(team);
    const teamContent = tbd
      ? `<span class="bk-podium-team tbd">TBD</span>`
      : `<span class="bk-podium-team">${teamHtml(team, false)}</span>`;
    return `<div class="bk-podium-row ${rowCls}">
      <span class="bk-podium-medal">${medal}</span>
      ${teamContent}
    </div>`;
  }
  return `<div class="bk-podium" id="bk-podium-results">
    <div class="bk-podium-hdr">Podium</div>
    ${row('🥇', champion,   'gold')}
    ${row('🥈', runnerUp,   'silver')}
    ${row('🥉', thirdPlace, 'bronze')}
  </div>`;
}

// ── Build bracket HTML ────────────────────────────────────
// mkCard(matchNum) → HTML string
// opts.podiumHtml: optional HTML injected below the Final column's float
//   (below the 3rd place and Final cards). Used by Variants 2 & 3.
function buildBracketHtml(mkCard, opts={}) {
  function mkPair(ms)  { return `<div class="bk-pair">${ms.map(mkCard).join('')}</div>`; }
  function mkQtr(ps)   { return `<div class="bk-quarter">${ps.map(mkPair).join('')}</div>`; }
  function mkHalf(qs)  { return `<div class="bk-half">${qs.map(mkQtr).join('')}</div>`; }

  const r32Html = `<div class="bk-col r32">
    <div class="bk-matches" id="bk-r32-matches">
      ${mkHalf([[[74,77],[73,75]], [[83,84],[81,82]]])}
      ${mkHalf([[[76,78],[79,80]], [[86,88],[85,87]]])}
    </div>
  </div>`;

  // All non-R32 cards (including podium) are absolutely positioned by JS.
  // Headers are no longer inside the columns — they live in the sticky strip above.
  function floatCol(cls, matches, floatExtra='') {
    const cards = matches.map(mkCard).join('');
    return `<div class="bk-col ${cls}">
      <div class="bk-float" id="bk-float-${cls}">${cards}${floatExtra}</div>
    </div>`;
  }

  // 3rd place card and optional podium are both inside the float,
  // positioned by positionAndConnectBracket().
  const thirdPlaceHtml = mkCard(103);
  const podiumSection  = opts.podiumHtml || '';

  // Sticky round header strip — top is set dynamically by positionAndConnectBracket
  // to sit flush below whatever .sticky-bar is on the page.
  const headerStrip = `<div class="bk-header-strip">
    <div class="bk-col r32"><div class="bk-col-hdr">Round of 32</div></div>
    <div class="bk-col r16"><div class="bk-col-hdr">Round of 16</div></div>
    <div class="bk-col qf"><div class="bk-col-hdr">Quarterfinals</div></div>
    <div class="bk-col sf"><div class="bk-col-hdr">Semifinals</div></div>
    <div class="bk-col fin"><div class="bk-col-hdr">🏆 Final (and 3rd place)</div></div>
  </div>`;

  return `<div class="bk-outer">
    ${headerStrip}
    <div class="bk-wrap"><div class="bk-bracket">
      ${r32Html}
      ${floatCol('r16', [89,90,93,94,91,92,95,96])}
      ${floatCol('qf',  [97,98,99,100])}
      ${floatCol('sf',  [101,102])}
      ${floatCol('fin', [104], thirdPlaceHtml + podiumSection)}
    </div></div>
  </div>`;
}

// ── Mobile tab HTML (Variants 1 & 3) ─────────────────────
// Shared renderer for read-only mobile bracket tabs (provisional + results).
// Variant 2 (picks) has its own version with pick-specific click-handler rows.
// rounds:      [{ id, label, matches }]
// activeRound: string id of the tab to open on load
// mkCard(m):   fn returning HTML string for a single match
function buildMobTabHtml(rounds, activeRound, mkCard) {
  const tabBarHtml = rounds.map(r =>
    `<button class="bk-tab${r.id === activeRound ? ' active' : ''}" onclick="switchBracketTab('${r.id}')" data-round="${r.id}">${r.label}</button>`
  ).join('');
  const panelsHtml = rounds.map(r => {
    const pairs = MOB_PAIR_NEXT[r.id] || [];
    let html = '';
    for (let j = 0; j < r.matches.length; j += 2) {
      const m1 = r.matches[j];
      const m2 = r.matches[j + 1];
      const pair = pairs[j / 2];
      if (m2 !== undefined && pair) {
        const [rl, mn] = pair;
        html += `<div class="bk-mob-pair-group">`;
        html += mkCard(m1);
        html += `<div class="bk-mob-pair-pill"><span>winners meet in ${rl} · ${mn}</span></div>`;
        html += mkCard(m2);
        html += `</div>`;
      } else {
        html += mkCard(m1);
        if (m2 !== undefined) html += mkCard(m2);
      }
    }
    return `<div class="bk-tab-panel${r.id === activeRound ? ' active' : ''}" id="bk-panel-${r.id}">${html}</div>`;
  }).join('');
  return `<div class="bk-mobile-tabs"><div class="bk-tab-bar">${tabBarHtml}</div>${panelsHtml}</div>`;
}

// ── Mobile bracket tab switcher ───────────────────────────
// Toggles active state on tabs and panels. Called from inline onclick attrs
// generated by buildMobTabHtml() — must remain a global (not an ES module export).
function switchBracketTab(roundId) {
  document.querySelectorAll('.bk-tab').forEach(b =>
    b.classList.toggle('active', b.dataset.round === roundId));
  document.querySelectorAll('.bk-tab-panel').forEach(p =>
    p.classList.toggle('active', p.id === 'bk-panel-' + roundId));
}

// ── Position float columns then draw connectors ───────────
// Call after injecting bracket HTML:
//   requestAnimationFrame(() => requestAnimationFrame(positionAndConnectBracket));
function positionAndConnectBracket() {
  const bracket = document.querySelector('.bk-bracket');
  if (!bracket) return;

  // Pin the sticky header strip flush below the page's .sticky-bar
  const headerStrip = bracket.closest('.bk-outer')?.querySelector('.bk-header-strip');
  if (headerStrip) {
    const stickyBar = document.querySelector('.sticky-bar');
    headerStrip.style.top = (stickyBar ? stickyBar.getBoundingClientRect().height : 0) + 'px';
  }

  // Size all float containers to match R32 matches height
  const r32m = document.getElementById('bk-r32-matches');
  if (!r32m) return;
  const r32H = r32m.getBoundingClientRect().height;
  document.querySelectorAll('.bk-float').forEach(d => { d.style.height = r32H + 'px'; });

  const br = bracket.getBoundingClientRect();

  // Returns the y-coord of the dividing line between the two team rows
  function teamMidY(el, refTop) {
    const rows = el.querySelectorAll('.bk-team');
    if (rows.length >= 2) {
      const a = rows[0].getBoundingClientRect();
      const b = rows[1].getBoundingClientRect();
      return (a.bottom + b.top) / 2 - refTop;
    }
    const r = el.getBoundingClientRect();
    return (r.top + r.bottom) / 2 - refTop;
  }

  function yc(m) {
    const el = bracket.querySelector(`[data-match="${m}"]`);
    if (!el) return null;
    return teamMidY(el, br.top);
  }

  function setY(m, targetY) {
    const el = bracket.querySelector(`[data-match="${m}"]`);
    if (!el) return;
    const container = el.parentElement;
    const ct = container.getBoundingClientRect().top - br.top;
    // Offset from card top to the team-dividing line
    const midOffset = teamMidY(el, el.getBoundingClientRect().top);
    el.style.top = `${targetY - ct - midOffset}px`;
  }

  // Position each non-R32 card at the midpoint of its two feeders, level by level
  const LEVELS = [
    [[74,77,89],[73,75,90],[83,84,93],[81,82,94],
     [76,78,91],[79,80,92],[86,88,95],[85,87,96]],
    [[89,90,97],[93,94,98],[91,92,99],[95,96,100]],
    [[97,98,101],[99,100,102]],
    [[101,102,104]],
  ];

  LEVELS.forEach(level => {
    level.forEach(([m1, m2, mn]) => {
      const y1 = yc(m1), y2 = yc(m2);
      if (y1 !== null && y2 !== null) setY(mn, (y1 + y2) / 2);
    });
  });

  // Position M103 (3rd place): align its team-dividing line with M99 in the QF column
  const m103el = bracket.querySelector('[data-match="103"]');
  const m104el = bracket.querySelector('[data-match="104"]');
  const m99el  = bracket.querySelector('[data-match="99"]');
  if (m103el) {
    const ct = m103el.parentElement.getBoundingClientRect().top - br.top;
    let targetY;
    if (m99el) {
      targetY = teamMidY(m99el, br.top);
    } else if (m104el) {
      const bot104 = m104el.getBoundingClientRect().bottom - br.top;
      targetY = bot104 + 80;
    }
    if (targetY !== undefined) {
      const midOffset = teamMidY(m103el, m103el.getBoundingClientRect().top);
      m103el.style.top = `${targetY - ct - midOffset}px`;
    }
  }

  // Position podium: top edge aligned with M89 (top of Round of 16)
  const podiumEl = bracket.querySelector('#bk-podium-results');
  const m89el    = bracket.querySelector('[data-match="89"]');
  if (podiumEl && m89el) {
    const ct     = podiumEl.parentElement.getBoundingClientRect().top - br.top;
    const m89top = m89el.getBoundingClientRect().top - br.top;
    podiumEl.style.top = `${m89top - ct}px`;
  }

  // Draw SVG connectors between positioned cards
  drawBracketConnectors();
}

// ── Draw SVG bracket connectors ───────────────────────────
function drawBracketConnectors() {
  const bracket = document.querySelector('.bk-bracket');
  if (!bracket) return;
  const old = bracket.querySelector('.bk-svg');
  if (old) old.remove();

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.className = 'bk-svg';
  svg.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;overflow:visible;';
  bracket.appendChild(svg);

  const br = bracket.getBoundingClientRect();

  const CONNS = [
    [74,77,89],[73,75,90],[83,84,93],[81,82,94],
    [76,78,91],[79,80,92],[86,88,95],[85,87,96],
    [89,90,97],[93,94,98],[91,92,99],[95,96,100],
    [97,98,101],[99,100,102],
    [101,102,104],
  ];

  const color = '#B5D4F4';

  CONNS.forEach(([m1, m2, mn]) => {
    const e1 = bracket.querySelector(`[data-match="${m1}"]`);
    const e2 = bracket.querySelector(`[data-match="${m2}"]`);
    const en = mn ? bracket.querySelector(`[data-match="${mn}"]`) : null;
    if (!e1 || !e2) return;

    const r1 = e1.getBoundingClientRect();
    const r2 = e2.getBoundingClientRect();

    // Connect at the dividing line between the two team rows
    function tmY(el) {
      const rows = el.querySelectorAll('.bk-team');
      if (rows.length >= 2) {
        const a = rows[0].getBoundingClientRect();
        const b = rows[1].getBoundingClientRect();
        return (a.bottom + b.top) / 2 - br.top;
      }
      return (el.getBoundingClientRect().top + el.getBoundingClientRect().bottom) / 2 - br.top;
    }

    const x1 = r1.right  - br.left;
    const y1 = tmY(e1);
    const y2 = tmY(e2);
    const ym = (y1 + y2) / 2;

    let xc = x1 + 14;
    if (en) {
      const rn = en.getBoundingClientRect();
      xc = (x1 + (rn.left - br.left)) / 2;
    }

    // ] bracket shape + horizontal line to next card's team-dividing-line y
    const xn = en ? en.getBoundingClientRect().left - br.left : xc;
    const d  = `M${x1},${y1} H${xc} V${y2} M${x1},${y2} H${xc}` +
               (en ? ` M${xc},${ym} H${xn}` : '');

    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', d);
    path.setAttribute('stroke', color);
    path.setAttribute('stroke-width', '1.5');
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke-linecap', 'round');
    svg.appendChild(path);
  });
}
