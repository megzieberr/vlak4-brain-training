// The My patrone numbers. Pure functions only: no screen code, no storage code.
// Only finished questions (closedAt set) are counted. Nothing here knows how many
// questions exist in total, so no total can give away what is still coming.

export const CAP_MINUTES = 60;
export const STUCK_ORDER = ['begin', 'middel', 'einde', 'nerens'];

// questions: the saved questions object. metaByNumber: { "1": vraag.json, ... }
export function compute(questions, metaByNumber, minuteMs) {
  const finished = Object.keys(questions || {})
    .filter((k) => questions[k] && questions[k].closedAt && questions[k].terugkyk)
    .sort((a, b) => Number(a) - Number(b));

  const stuck = { begin: 0, middel: 0, einde: 0, nerens: 0 };
  const moves = {};
  let within = 0;
  const groups = { topic: {}, paper: {}, kind: {} };

  for (const k of finished) {
    const q = questions[k];
    const t = q.terugkyk;
    if (t.withinTwoMinutes) within += 1;
    if (t.stuck in stuck) stuck[t.stuck] += 1;
    if (t.move >= 1 && t.move <= 8) moves[t.move] = (moves[t.move] || 0) + 1;

    const meta = metaByNumber[k];
    if (!meta) continue;
    const hintsOpened = Array.isArray(q.hintsOpenedAt) ? q.hintsOpenedAt.length : 0;
    const time = struggleMinutes(q, minuteMs);
    const keys = {
      topic: meta.tags && meta.tags.topic,
      paper: meta.paper,
      kind: meta.tags && meta.tags.kind,
    };
    for (const g of Object.keys(keys)) {
      const name = keys[g];
      if (!name) continue;
      const row = groups[g][name] || (groups[g][name] = { count: 0, hints: 0, times: [] });
      row.count += 1;
      row.hints += hintsOpened;
      if (time !== null) row.times.push(time);
    }
  }

  const moveList = Object.keys(moves)
    .map((m) => ({ move: Number(m), count: moves[m] }))
    .sort((a, b) => b.count - a.count || a.move - b.move);

  const tables = {};
  for (const g of Object.keys(groups)) {
    tables[g] = Object.keys(groups[g]).map((name) => {
      const row = groups[g][name];
      return { name, count: row.count, hints: row.hints, avg: average(row.times) };
    });
  }

  return {
    closed: finished.length,
    within,
    stuck,
    moves: moveList,
    tables,
  };
}

// Minutes from Begin until the route was opened, capped at 60. null when unknown.
export function struggleMinutes(q, minuteMs) {
  if (!Number.isFinite(q.beganAt) || !Number.isFinite(q.routeOpenedAt)) return null;
  const m = (q.routeOpenedAt - q.beganAt) / (minuteMs || 60000);
  return Math.max(0, Math.min(CAP_MINUTES, m));
}

// { minutes, capped }: capped is true when the average sits at the 60 minute cap.
export function average(times) {
  if (!times.length) return null;
  const avg = times.reduce((a, b) => a + b, 0) / times.length;
  return { minutes: Math.round(avg), capped: avg >= CAP_MINUTES };
}
