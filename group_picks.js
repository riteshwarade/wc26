// group_picks.js — WC2026 Pool group picks page logic
// Depends on: scoring.js (MATCHES), bracket.js (FLAGS, RANKINGS)

// ── Local match time (UTC ISO → user's local timezone) ────
// TZ abbreviation for column header (e.g. 'EDT', 'PDT', 'BST')
const _tzAbbr = new Date().toLocaleTimeString('en-US', { timeZoneName: 'short' }).split(' ').pop();

function localMatchTime(utcStr) {
  try {
    const dt = new Date(utcStr);
    const t = dt.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
    return `${t}<span class="cell-tz"> ${_tzAbbr}</span>`;
  } catch (e) { return utcStr; }
}

// ── Build form ────────────────────────────────────────────
function buildForm() {
  const form = document.getElementById('poolForm');

  // Single table with all 72 matches sorted by match number
  const table = document.createElement('div');
  table.className = 'matches-table';

  // Column header row
  const hdr = document.createElement('div');
  hdr.className = 'col-layout col-header';
  hdr.innerHTML = `
    <span>#</span>
    <span>Grp</span>
    <span class="ch-date">Date</span>
    <span class="ch-time">Time (${_tzAbbr})</span>
    <span style="text-align:center">Your pick</span>
  `;
  table.appendChild(hdr);

  MATCHES.forEach(m => {
    const [num, grp, date, time, t1, t2] = m;

    const row = document.createElement('div');
    row.className = 'match-row col-layout';
    row.id = `row-${num}`;

    row.innerHTML = `
      <div class="match-num">${num}</div>
      <div class="match-grp">${grp}</div>
      <div class="match-date">${date}</div>
      <div class="match-time">${localMatchTime(time)}</div>
      <div class="pick-group">
        <input type="radio" name="m${num}" id="m${num}_w1" value="w1" class="win1-radio" onchange="onPick(${num})">
        <label class="pick-btn" for="m${num}_w1">${teamHtmlPick(t1)}</label>

        <input type="radio" name="m${num}" id="m${num}_d" value="draw" class="draw-radio" onchange="onPick(${num})">
        <label class="pick-btn" for="m${num}_d">Draw</label>

        <input type="radio" name="m${num}" id="m${num}_w2" value="w2" class="win2-radio" onchange="onPick(${num})">
        <label class="pick-btn" for="m${num}_w2">${teamHtmlPick(t2)}</label>
      </div>
    `;

    table.appendChild(row);
  });

  form.appendChild(table);
}

// ── Progress tracking ─────────────────────────────────────
let picked = 0;

function onPick(num) {
  const row = document.getElementById(`row-${num}`);
  const hasSelection = !!document.querySelector(`input[name="m${num}"]:checked`);
  if (hasSelection && !row.classList.contains('picked')) {
    row.classList.add('picked');
    picked++;
    updateProgress();
  } else if (!hasSelection && row.classList.contains('picked')) {
    row.classList.remove('picked');
    picked--;
    updateProgress();
  }
  document.getElementById('confirmRow').classList.remove('visible');
  document.querySelector('.submit-btn').style.display = '';
  renderPickGroupTables();
}

// ── Fixed group order (per Wikipedia) ────────────────────
const GROUP_ORDER = {
  A: ['Mexico','South Africa','South Korea','Czech Republic'],
  B: ['Canada','Bosnia and Herzegovina','Qatar','Switzerland'],
  C: ['Brazil','Morocco','Haiti','Scotland'],
  D: ['United States','Paraguay','Australia','Turkey'],
  E: ['Germany','Curaçao','Ivory Coast','Ecuador'],
  F: ['Netherlands','Japan','Sweden','Tunisia'],
  G: ['Belgium','Egypt','Iran','New Zealand'],
  H: ['Spain','Cape Verde','Saudi Arabia','Uruguay'],
  I: ['France','Senegal','Iraq','Norway'],
  J: ['Argentina','Algeria','Austria','Jordan'],
  K: ['Portugal','DR Congo','Uzbekistan','Colombia'],
  L: ['England','Croatia','Ghana','Panama'],
};

// ── Live group tables ─────────────────────────────────────
function renderPickGroupTables() {
  const groups = {}, stats = {};

  MATCHES.forEach(([num, grp, , , t1, t2]) => {
    if (!groups[grp]) groups[grp] = [];
    if (!groups[grp].includes(t1)) groups[grp].push(t1);
    if (!groups[grp].includes(t2)) groups[grp].push(t2);
    [t1, t2].forEach(t => {
      if (!stats[t]) stats[t] = { P:0, W:0, D:0, L:0, Pts:0 };
    });

    const val = document.querySelector(`input[name="m${num}"]:checked`)?.value;
    if (!val) return;

    stats[t1].P++; stats[t2].P++;
    if (val === 'w1') {
      stats[t1].W++; stats[t1].Pts += 3; stats[t2].L++;
    } else if (val === 'w2') {
      stats[t2].W++; stats[t2].Pts += 3; stats[t1].L++;
    } else {
      stats[t1].D++; stats[t1].Pts++;
      stats[t2].D++; stats[t2].Pts++;
    }
  });

  // H2H points from user's picks between two teams
  function h2hPts(teamA, teamB) {
    let pa = 0, pb = 0;
    MATCHES.forEach(([num, , , , t1, t2]) => {
      if (!((t1===teamA&&t2===teamB)||(t1===teamB&&t2===teamA))) return;
      const val = document.querySelector(`input[name="m${num}"]:checked`)?.value;
      if (!val) return;
      const aIsT1 = t1 === teamA;
      if (val==='draw') { pa++; pb++; }
      else if ((val==='w1'&&aIsT1)||(val==='w2'&&!aIsT1)) pa += 3;
      else pb += 3;
    });
    return { a: pa, b: pb };
  }

  const html = Object.keys(groups).sort().map(grp => {
    const order = GROUP_ORDER[grp] || groups[grp];
    const teams = [...order].sort((a, b) => {
      const sa = stats[a], sb = stats[b];
      // 1. Points
      if (sb.Pts !== sa.Pts) return sb.Pts - sa.Pts;
      // 2. H2H points (criterion a)
      const h2h = h2hPts(a, b);
      if (h2h.b !== h2h.a) return h2h.b - h2h.a;
      // 3. Overall wins (proxy for GD — no scores in picks)
      if (sb.W !== sa.W) return sb.W - sa.W;
      // 4. FIFA ranking (lower = better)
      const ra = RANKINGS[a] ?? 999, rb = RANKINGS[b] ?? 999;
      if (ra !== rb) return ra - rb;
      // 5. Wikipedia order
      return order.indexOf(a) - order.indexOf(b);
    });

    const grpStarted = teams.every(t => stats[t].P > 0);
    const rowClassFn = (t, i) => grpStarted
      ? (i < 2 ? 'qualified' : i === 2 ? 'third-pending' : 'eliminated')
      : '';

    return renderGroupTableCard(grp, teams, stats, { rowClassFn, showGD: false });
  }).join('');

  document.getElementById('pickGroupTables').innerHTML = `<div class="group-tables-grid">${html}</div>`;
}

function updateProgress() {
  document.getElementById('progressCount').textContent = `${picked} / 72 matches picked`;
  document.getElementById('progressFill').style.width = `${(picked / 72) * 100}%`;
}

// ── Submit / validation ───────────────────────────────────
function handleSubmit() {
  const name = document.getElementById('entrantName').value.trim();
  const valMsg = document.getElementById('validationMsg');
  valMsg.style.display = 'none';

  if (!name) {
    valMsg.textContent = 'Please enter your name before reviewing your picks.';
    valMsg.style.display = 'block';
    document.getElementById('entrantName').focus();
    return;
  }

  if (picked < 72) {
    const remaining = 72 - picked;
    valMsg.textContent = `You still have ${remaining} match${remaining === 1 ? '' : 'es'} without a pick. Please select a result for every match before submitting.`;
    valMsg.style.display = 'block';

    for (const m of MATCHES) {
      const row = document.getElementById(`row-${m[0]}`);
      if (!row.classList.contains('picked')) {
        row.scrollIntoView({ behavior: 'smooth', block: 'center' });
        row.style.outline = `2px solid var(--swiftly-orange)`;
        setTimeout(() => row.style.outline = '', 2200);
        break;
      }
    }
    return;
  }

  document.getElementById('confirmRow').classList.add('visible');
  document.querySelector('.submit-btn').style.display = 'none';
}


// ── Reusable team display: flag + name + rank ─────────────
// ── Group table card template (matches leaderboard) ──────
function renderGroupTableCard(grp, teams, stats, opts={}) {
  const { rowClassFn = () => '', showGD = false } = opts;
  const rows = teams.map((t, i) => {
    const s = stats[t] || {P:0,W:0,D:0,L:0,GF:0,GA:0,Pts:0};
    const rc = rowClassFn(t, i);
    const gdCell = showGD ? `<td>${s.GF}</td><td>${s.GA}</td><td>${(s.GF-s.GA)>=0?'+':''}${s.GF-s.GA}</td>` : '';
    return `<tr${rc ? ` class="${rc}"` : ''}><td class="td-team">${teamHtml(t)}</td><td>${s.P}</td><td>${s.W}</td><td>${s.D}</td><td>${s.L}</td>${gdCell}<td class="td-pts">${s.Pts}</td></tr>`;
  }).join('');
  const gdHeaders = showGD ? `<th title="Goals for">GF</th><th title="Goals against">GA</th><th title="Goal difference">GD</th>` : '';
  return `<div class="group-table-card"><div class="group-table-header">Group ${grp}</div><div class="group-table"><table><thead><tr><th class="th-team">Team</th><th title="Played">P</th><th title="Won">W</th><th title="Drawn">D</th><th title="Lost">L</th>${gdHeaders}<th title="Points">Pts</th></tr></thead><tbody>${rows}</tbody></table></div></div>`;
}

function teamHtml(name, showRank=true) {
  if (!name) return '';
  const flag = FLAGS[name] || '';
  const rank = showRank ? (RANKINGS[name] || null) : null;
  const rankHtml = rank ? ` <span class="team-rank">(${rank})</span>` : '';
  return `${flag ? flag + ' ' : ''}${name}${rankHtml}`;
}

// Shortened names used only inside pick buttons on narrow screens (≤ 640 px)
const SHORT_NAMES = {
  'Bosnia and Herzegovina': 'Bosnia…',
  'Czech Republic':         'Czech…',
};
function teamHtmlPick(name) {
  if (!name) return '';
  const flag  = FLAGS[name] || '';
  const rank  = RANKINGS[name] || null;
  const rankHtml = rank ? ` <span class="team-rank">(${rank})</span>` : '';
  const display  = SHORT_NAMES[name] || name;
  return `${flag ? flag + ' ' : ''}${display}${rankHtml}`;
}



function confirmSubmit() {
  const name = document.getElementById('entrantName').value.trim();
  downloadCSV(name);
  document.getElementById('confirmRow').classList.remove('visible');
  const msg = document.getElementById('validationMsg');
  msg.style.background = '#ebf9ff';
  msg.style.borderColor = 'var(--swiftly-blue)';
  msg.style.color = 'var(--neutral-darkest)';
  msg.textContent = `✓ Done! Your picks have been downloaded as a CSV file. Please send to Ritesh.`;
  msg.style.display = 'block';
}

function runShortcut(mode) {
  if (mode === 'reset') {  // reset doesn't need a name
    MATCHES.forEach(m => {
      const [num] = m;
      document.querySelectorAll(`input[name="m${num}"]`).forEach(r => r.checked = false);
      onPick(num);
    });
    return;
  }
  const options = ['w1', 'draw', 'w2'];
  MATCHES.forEach(m => {
    const [num, , , , t1, t2] = m;
    let pick;
    if (mode === 'random') {
      pick = options[Math.floor(Math.random() * 3)];
    } else if (mode === 'draw') {
      pick = 'draw';
    } else {
      const r1 = RANKINGS[t1] ?? 999;
      const r2 = RANKINGS[t2] ?? 999;
      pick = r1 <= r2 ? 'w1' : 'w2';
    }
    const idSuffix = pick === 'w1' ? 'w1' : pick === 'draw' ? 'd' : 'w2';
    const radio = document.getElementById(`m${num}_${idSuffix}`);
    if (radio) { radio.checked = true; onPick(num); }
  });
}

function downloadCSV(name) {
  const escape = v => (String(v).includes(',') ? `"${v}"` : v);
  const rows = [['match', 'group', 'matchup', 'pick']];
  MATCHES.forEach(m => {
    const [num, grp, , , t1, t2] = m;
    const val = document.querySelector(`input[name="m${num}"]:checked`)?.value;
    const matchup = escape(`${t1} v ${t2}`);
    const pick = val === 'w1' ? t1 : val === 'draw' ? 'Draw' : t2;
    rows.push([num, grp, matchup, escape(pick)]);
  });
  const csv  = rows.map(r => r.join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = `wc26_group_${name.replace(/\s+/g, '-').toLowerCase()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

// Init
document.getElementById('headerSubtitle').textContent =
  'Pick a result (win for either team or draw) for all 72 group stage matches';
buildForm();
renderPickGroupTables();
document.querySelector('.container').style.visibility = 'visible';
