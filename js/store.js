// Everything that reads or writes the tablet's storage goes through this file.
// One key, vlak4.v1. Empty or broken storage gives a clean start, never a crash.

export const KEY = 'vlak4.v1';

export function fresh() {
  return { version: 1, rulesSeen: false, questions: {} };
}

// Keep only the parts of a stored object that the app understands.
export function sanitize(obj) {
  if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return null;
  if (obj.version !== 1) return null;
  const qs = obj.questions;
  if (!qs || typeof qs !== 'object' || Array.isArray(qs)) return null;
  const out = { version: 1, rulesSeen: obj.rulesSeen === true, questions: {} };
  for (const k of Object.keys(qs)) {
    const n = Number(k);
    const q = qs[k];
    if (!Number.isInteger(n) || n < 1 || n > 20) continue;
    if (!q || typeof q !== 'object' || Array.isArray(q)) continue;
    const e = {};
    if (Number.isFinite(q.beganAt)) e.beganAt = q.beganAt;
    e.hintsOpenedAt = Array.isArray(q.hintsOpenedAt) ? q.hintsOpenedAt.filter(Number.isFinite) : [];
    if (Number.isFinite(q.routeOpenedAt)) e.routeOpenedAt = q.routeOpenedAt;
    if (q.routeVia === 'antwoord' || q.routeVia === 'gesukkel') e.routeVia = q.routeVia;
    const t = q.terugkyk;
    if (t && typeof t === 'object'
        && typeof t.withinTwoMinutes === 'boolean'
        && Number.isInteger(t.move) && t.move >= 0 && t.move <= 8
        && ['begin', 'middel', 'einde', 'nerens'].includes(t.stuck)) {
      e.terugkyk = { withinTwoMinutes: t.withinTwoMinutes, move: t.move, stuck: t.stuck };
    }
    if (Number.isFinite(q.closedAt) && e.terugkyk) e.closedAt = q.closedAt;
    out.questions[String(n)] = e;
  }
  return out;
}

export function load() {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return fresh();
    return sanitize(JSON.parse(raw)) || fresh();
  } catch (e) {
    return fresh();
  }
}

function save(state) {
  try {
    localStorage.setItem(KEY, JSON.stringify(state));
    return true;
  } catch (e) {
    return false;
  }
}

export function rawString() {
  try { return localStorage.getItem(KEY); } catch (e) { return null; }
}

export function getQ(n) {
  return load().questions[String(n)] || null;
}

function update(n, fn) {
  const s = load();
  const key = String(n);
  const q = s.questions[key] || { hintsOpenedAt: [] };
  if (q.closedAt) return s; // a finished question never changes
  fn(q);
  s.questions[key] = q;
  save(s);
  return s;
}

export function setRulesSeen() {
  const s = load();
  s.rulesSeen = true;
  save(s);
}

export function begin(n, now) {
  return update(n, (q) => { if (!Number.isFinite(q.beganAt)) q.beganAt = now; });
}

export function openHint(n, index, now) {
  // index is 0-based; only the next hint in line can be opened
  return update(n, (q) => {
    if (!Array.isArray(q.hintsOpenedAt)) q.hintsOpenedAt = [];
    if (q.hintsOpenedAt.length === index) q.hintsOpenedAt.push(now);
  });
}

export function openRoute(n, via, now) {
  return update(n, (q) => {
    if (!Number.isFinite(q.routeOpenedAt)) {
      q.routeOpenedAt = now;
      q.routeVia = via;
    }
  });
}

export function closeQuestion(n, terugkyk, now) {
  return update(n, (q) => {
    if (!Number.isFinite(q.routeOpenedAt)) return;
    q.terugkyk = { withinTwoMinutes: terugkyk.withinTwoMinutes, move: terugkyk.move, stuck: terugkyk.stuck };
    q.closedAt = now;
  });
}

// Replace everything with a checked backup object. Returns true when it worked.
export function replaceAll(obj) {
  const clean = sanitize(obj);
  if (!clean) return false;
  clean.rulesSeen = true;
  return save(clean);
}

export function clearAll() {
  try { localStorage.removeItem(KEY); } catch (e) { /* nothing to do */ }
}

// The backup and patterns file (spec 5.6): the storage object plus tags per finished question.
export function buildExport(tagsByNumber) {
  const s = load();
  const tags = {};
  for (const k of Object.keys(s.questions)) {
    if (s.questions[k].closedAt && tagsByNumber[k]) tags[k] = tagsByNumber[k];
  }
  return { ...s, tags };
}

// Check a file's parsed contents before anything is replaced.
export function isBackup(obj) {
  return !!(obj && typeof obj === 'object' && !Array.isArray(obj)
    && 'version' in obj && 'questions' in obj && sanitize(obj));
}
