// Hint timing. Pure functions only: no screen code, no storage code.
// Every answer is worked out from the saved beganAt stamp and the current time,
// so a reload or a closed tab can never reset the clock.

export const MINUTE = 60000;
export const NEXT_HINT_MINUTES = 5;

// ?toets=1 makes one minute last one second, but only on localhost or 127.0.0.1.
export function speedFactor(hostname, search) {
  const local = hostname === 'localhost' || hostname === '127.0.0.1';
  if (!local) return 1;
  const params = new URLSearchParams(search || '');
  return params.get('toets') === '1' ? 60 : 1;
}

export function minuteMs(speed) {
  return MINUTE / (speed || 1);
}

// meta: { hints, struggleMinutes }  q: the saved entry for this question (or null)
export function status(meta, q, now, speed) {
  const m = minuteMs(speed);
  const hints = Math.max(0, meta.hints | 0);
  if (!q || !Number.isFinite(q.beganAt)) {
    return { started: false, hints, opened: 0, next: null, canStruggleOut: false };
  }
  const struggleReadyAt = q.beganAt + meta.struggleMinutes * m;
  const openedTimes = Array.isArray(q.hintsOpenedAt) ? q.hintsOpenedAt : [];
  const opened = Math.min(openedTimes.length, hints);
  let next = null;
  if (opened < hints) {
    const readyAt = opened === 0
      ? struggleReadyAt
      : openedTimes[opened - 1] + NEXT_HINT_MINUTES * m;
    const remaining = Math.max(0, readyAt - now);
    next = {
      index: opened,              // 0-based
      ready: remaining === 0,
      remainingMs: remaining,
      // what the countdown shows, in the question's own minutes
      shownSeconds: Math.ceil((remaining * (speed || 1)) / 1000),
    };
  }
  return {
    started: true,
    hints,
    opened,
    next,
    canStruggleOut: now >= struggleReadyAt,
  };
}

export function formatCountdown(totalSeconds) {
  const s = Math.max(0, totalSeconds | 0);
  const mm = Math.floor(s / 60);
  const ss = s % 60;
  return `${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}`;
}
