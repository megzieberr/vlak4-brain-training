// Screens and navigation. Hash routes so the tablet's back button works:
// #/  #/vraag/N  #/roete/N  #/terugkyk/N  #/kaart  #/patrone  #/meer  #/reels
// All on-screen wording comes from strings.js.

import { S } from './strings.js';
import * as store from './store.js';
import * as clock from './clock.js';
import * as stats from './stats.js';

const TOTAL = 20;
const SPEED = clock.speedFactor(location.hostname, location.search);
const app = document.getElementById('app');

let contentIndex = { published: [], contentVersion: 0 };
const metaCache = {};
let tickTimer = null;
let routeSeq = 0;
let internalNav = false;
let flash = null;

// ---------- small helpers ----------

function h(tag, attrs, ...children) {
  const el = document.createElement(tag);
  if (attrs) {
    for (const [k, v] of Object.entries(attrs)) {
      if (v === null || v === undefined || v === false) continue;
      if (k === 'class') el.className = v;
      else if (k === 'text') el.textContent = v;
      else if (k === 'html') el.innerHTML = v;
      else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
      else el.setAttribute(k, v === true ? '' : v);
    }
  }
  for (const c of children.flat()) {
    if (c === null || c === undefined || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}

function btn(label, onclick, cls = 'btn') {
  return h('button', { type: 'button', class: cls, onclick }, label);
}

function folder(n) {
  return `content/v${String(n).padStart(2, '0')}`;
}

function contentUrl(n, file) {
  return `${folder(n)}/${file}?v=${contentIndex.contentVersion}`;
}

function isPublished(n) {
  return contentIndex.published.includes(n);
}

function isClosed(state, n) {
  const q = state.questions[String(n)];
  return !!(q && q.closedAt);
}

function currentNumber(state) {
  for (let n = 1; n <= TOTAL; n++) if (!isClosed(state, n)) return n;
  return null;
}

async function loadIndex() {
  try {
    const r = await fetch('content/index.json', { cache: 'no-store' });
    if (!r.ok) throw new Error('index');
    const j = await r.json();
    contentIndex = {
      published: Array.isArray(j.published) ? j.published.map(Number).filter(Number.isInteger) : [],
      contentVersion: Number(j.contentVersion) || 0,
    };
  } catch (e) {
    contentIndex = { published: [], contentVersion: 0 };
  }
}

async function loadMeta(n) {
  if (metaCache[n]) return metaCache[n];
  const r = await fetch(contentUrl(n, 'vraag.json'), { cache: 'no-cache' });
  if (!r.ok) throw new Error('meta');
  const j = await r.json();
  metaCache[n] = j;
  return j;
}

function go(hash) {
  location.hash = hash;
}

function redirect(hash) {
  location.replace(hash);
}

function goBack(fallback) {
  if (internalNav && history.length > 1) history.back();
  else redirect(fallback);
}

function stopTick() {
  if (tickTimer) clearInterval(tickTimer);
  tickTimer = null;
}

function view(...children) {
  app.replaceChildren(h('main', { class: 'view' }, ...children));
  window.scrollTo(0, 0);
}

// A bar fixed to the foot of the screen: give the page bottom padding equal to the bar's real
// height (plus a little air), so the bar never hides the last of the page.
function padForFootBar(bar) {
  const main = bar.closest('main');
  if (!main) return;
  const fit = () => {
    if (!bar.isConnected) return;
    main.style.paddingBottom = `${Math.ceil(bar.getBoundingClientRect().height) + 24}px`;
  };
  fit();
  watchSize(bar, fit);
}

function watchSize(el, fn) {
  if (typeof ResizeObserver === 'function') new ResizeObserver(fn).observe(el);
  else window.addEventListener('resize', fn);
}

function topbar(backTo, withCard) {
  return h('div', { class: 'topbar' },
    btn(S.terug, () => goBack(backTo), 'btn ghost'),
    withCard ? btn(S.cardLink, () => go('#/kaart'), 'btn ghost') : null,
  );
}

function downloadBlob(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = h('a', { href: url, download: name, class: 'hidden-link' });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10000);
}

// ---------- pictures ----------

// onChange (optional) is called each time one of the pictures finishes loading or fails.
function pictures(n, files, onChange) {
  const wrap = h('div', { class: 'papers' });
  for (const f of files || []) wrap.append(picture(contentUrl(n, f), onChange));
  return wrap;
}

// True when every picture in the block has loaded (a failed one counts as not loaded).
function allLoaded(wrap) {
  return [...wrap.querySelectorAll('.paper-slot')].every((s) => s.dataset.state === 'loaded');
}

function picture(url, onChange) {
  const card = h('div', { class: 'paper-slot' });
  const setState = (st) => { card.dataset.state = st; if (onChange) onChange(); };
  const show = (src) => {
    const img = h('img', { src, alt: '', class: 'paper-img' });
    const b = h('button', { type: 'button', class: 'paper', onclick: () => openOverlay(src) }, img);
    img.addEventListener('load', () => setState('loaded'));
    img.addEventListener('error', () => {
      card.replaceChildren(h('div', { class: 'paper-error' },
        h('p', { text: S.imgFail }),
        btn(S.retry, () => show(`${url}&r=${Date.now()}`)),
      ));
      setState('failed');
    });
    card.replaceChildren(b);
    setState('loading');
  };
  show(url);
  return card;
}

let overlayEl = null;

function openOverlay(src) {
  closeOverlay();
  overlayEl = h('div', { class: 'overlay', role: 'dialog' },
    h('div', { class: 'overlay-bar' }, btn(S.terug, () => history.back(), 'btn')),
    h('div', { class: 'overlay-paper' }, h('img', { src, alt: '' })),
  );
  document.body.append(overlayEl);
  document.body.classList.add('no-scroll');
  history.pushState({ overlay: true }, '');
}

function closeOverlay() {
  if (!overlayEl) return;
  overlayEl.remove();
  overlayEl = null;
  document.body.classList.remove('no-scroll');
}

// ---------- confirm box ----------
// Opening the box adds one history entry (same address), so the tablet's back button closes
// the box and nothing else. Both buttons step back over that entry first; the chosen action
// runs once the step back has landed.

let modalState = null; // { el, after }

function confirmBox(title, line, yesLabel, noLabel, onYes) {
  const back = h('div', { class: 'modal-back' });
  const finish = (after) => {
    if (!modalState || modalState.el !== back) return;
    back.remove();
    modalState.after = after;
    history.back();
  };
  back.append(h('div', { class: 'modal card', role: 'dialog', 'aria-modal': 'true' },
    title ? h('h2', { text: title }) : null,
    h('p', { text: line }),
    h('div', { class: 'row' },
      btn(yesLabel, () => finish(onYes), 'btn primary'),
      btn(noLabel, () => finish(null), 'btn'),
    ),
  ));
  document.body.append(back);
  modalState = { el: back, after: null };
  history.pushState({ modal: true }, '');
}

window.addEventListener('popstate', () => {
  if (modalState) {
    const m = modalState;
    modalState = null;
    m.el.remove();
    if (m.after) m.after();
    return;
  }
  if (overlayEl) closeOverlay();
});

// ---------- router ----------

function parse() {
  const hash = location.hash || '#/';
  const m = hash.match(/^#\/(vraag|roete|terugkyk)\/(\d+)$/);
  if (m) return { name: m[1], n: Number(m[2]) };
  const s = hash.match(/^#\/(kaart|patrone|meer|reels)$/);
  if (s) return { name: s[1] };
  return { name: 'tuis' };
}

async function route() {
  const seq = ++routeSeq;
  stopTick();
  closeOverlay();
  document.querySelectorAll('.modal-back').forEach((m) => m.remove());
  modalState = null;
  const state = store.load();
  const r = parse();

  if (!state.rulesSeen) {
    if (r.name !== 'reels') { redirect('#/reels'); return; }
    renderRules(true);
    return;
  }

  switch (r.name) {
    case 'vraag': return renderVraag(r.n, state, seq);
    case 'roete': return renderRoete(r.n, state, seq);
    case 'terugkyk': return renderTerugkyk(r.n, state, seq);
    case 'kaart': return renderKaart();
    case 'patrone': return renderPatrone(state, seq);
    case 'meer': return renderMeer();
    case 'reels': return renderRules(false);
    default:
      if (location.hash && location.hash !== '#/') { redirect('#/'); return; }
      return renderTuis(state);
  }
}

// ---------- 4.1 Tuis ----------

function lockIcon() {
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('class', 'lock');
  svg.setAttribute('aria-hidden', 'true');
  svg.innerHTML = '<rect x="5" y="11" width="14" height="10" rx="1.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3" fill="none" stroke="currentColor" stroke-width="2"/>';
  return svg;
}

function renderTuis(state) {
  const current = currentNumber(state);
  const allDone = current === null;
  const path = h('div', { class: 'path' });
  const redraw = () => drawPathLine(path, allDone ? TOTAL : current);

  for (let n = 1; n <= TOTAL; n++) {
    let tile;
    if (isClosed(state, n)) {
      const topic = h('span', { class: 'tile-topic' });
      tile = h('button', { type: 'button', class: 'tile done', 'data-n': n, onclick: () => go(`#/vraag/${n}`) },
        h('span', { class: 'tile-n' }, S.vraag(n), h('span', { class: 'tick', 'aria-hidden': 'true' }, ' ✓')),
        topic,
      );
      loadMeta(n).then((m) => { topic.textContent = (m.tags && m.tags.topic) || ''; redraw(); }).catch(() => {});
    } else if (n === current) {
      tile = h('div', { class: 'tile current', 'data-n': n },
        h('span', { class: 'tile-n', text: S.vraag(n) }),
        isPublished(n)
          ? btn(S.maakOop, () => go(`#/vraag/${n}`), 'btn primary')
          : h('p', { class: 'tile-wait', text: S.notHereYet(n) }),
      );
    } else {
      tile = h('div', { class: 'tile locked', 'data-n': n, 'aria-disabled': 'true' },
        h('span', { class: 'tile-n', text: S.vraag(n) }),
        lockIcon(),
      );
    }
    path.append(tile);
  }

  const toast = flash ? h('p', { class: 'toast', role: 'status', text: flash }) : null;
  flash = null;
  if (toast) setTimeout(() => toast.remove(), 5000);

  const foot = h('nav', { class: 'foot' },
    btn(S.footCard, () => go('#/kaart')),
    btn(S.footPatrone, () => go('#/patrone')),
    btn(S.footMeer, () => go('#/meer')),
  );
  view(
    h('header', { class: 'home-head' },
      h('h1', { text: S.appTitle }),
      h('p', { class: 'muted', text: allDone ? S.allDone : S.tagline }),
    ),
    toast,
    path,
    foot,
  );
  padForFootBar(foot);
  redraw();
  watchSize(path, redraw);
}

// The thin line that joins the 20 tiles into one path, in reading order. It runs only through
// the gaps between tiles, never over a tile: a short link between neighbours in a row, and
// from the end of a row down into the gap, across, and down into the start of the next row.
// Links up to the current tile are lit; links after it are dim.
function drawPathLine(path, litUpTo) {
  const ns = 'http://www.w3.org/2000/svg';
  let svg = path.querySelector('svg.path-line');
  if (!svg) {
    svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('class', 'path-line');
    svg.setAttribute('aria-hidden', 'true');
    path.prepend(svg);
  }
  const W = path.clientWidth;
  const H = path.clientHeight;
  svg.setAttribute('width', W);
  svg.setAttribute('height', H);
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  const tiles = [...path.querySelectorAll('.tile')];
  const box = (t) => ({ l: t.offsetLeft, t: t.offsetTop, r: t.offsetLeft + t.offsetWidth, b: t.offsetTop + t.offsetHeight });
  const parts = [];
  for (let i = 0; i < tiles.length - 1; i++) {
    const a = box(tiles[i]);
    const b = box(tiles[i + 1]);
    const lit = i + 2 <= (litUpTo || 0);
    const cls = lit ? 'lit' : 'dim';
    const seg = (x1, y1, x2, y2) => `<line class="${cls}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}"/>`;
    let lines;
    if (Math.abs(a.t - b.t) < 2) {
      const y = (a.t + a.b) / 2;
      lines = seg(a.r, y, b.l, y);
    } else {
      const ax = (a.l + a.r) / 2;
      const bx = (b.l + b.r) / 2;
      const gy = (a.b + b.t) / 2;
      lines = seg(ax, a.b, ax, gy) + seg(ax, gy, bx, gy) + seg(bx, gy, bx, b.t);
    }
    parts.push(`<g data-link="${i + 1}" class="${cls}">${lines}</g>`);
  }
  svg.innerHTML = parts.join('');
}

// ---------- 4.2, 4.3, 4.8 Vraag ----------

// The werkblad button, its error line and its small line. The block keeps the lines; the button
// sits in the block, or in the Vraag action bar before Begin.
function werkbladParts(n, meta) {
  const msg = h('p', { class: 'error-line', role: 'status' });
  const button = btn(S.werkbladBtn, async () => {
    msg.textContent = '';
    try {
      const r = await fetch(contentUrl(n, meta.werkblad));
      if (!r.ok) throw new Error('werkblad');
      const blob = await r.blob();
      downloadBlob(blob, meta.werkblad);
    } catch (e) {
      msg.textContent = S.werkbladFail;
    }
  });
  const block = h('div', { class: 'block werkblad' }, button, msg, h('p', { class: 'small-line', text: S.werkbladLine }));
  return { block, button };
}

function werkbladBlock(n, meta) {
  return werkbladParts(n, meta).block;
}

async function metaOrError(n, seq) {
  try {
    return await loadMeta(n);
  } catch (e) {
    if (seq === routeSeq) {
      view(topbar('#/', false), h('div', { class: 'paper-error' },
        h('p', { text: S.imgFail }),
        btn(S.retry, () => route()),
      ));
    }
    return null;
  }
}

async function renderVraag(n, state, seq) {
  const q = state.questions[String(n)];
  const closed = !!(q && q.closedAt);
  if (!closed) {
    if (n !== currentNumber(state) || !isPublished(n)) { redirect('#/'); return; }
    if (q && Number.isFinite(q.routeOpenedAt)) { redirect(`#/roete/${n}`); return; }
  }
  const meta = await metaOrError(n, seq);
  if (!meta || seq !== routeSeq) return;
  const images = meta.images || {};

  if (closed) {
    view(
      topbar('#/', true),
      h('h1', { text: S.vraag(n) }),
      pictures(n, images.question),
      werkbladBlock(n, meta),
      (images.hints || []).map((f, i) => h('section', { class: 'block' },
        h('h2', { text: S.hintHeading(i + 1) }), pictures(n, [f]))),
      routeSections(n, meta),
      terugkykAnswers(q.terugkyk),
    );
    return;
  }

  // Page flow: heading, question picture(s), werkblad lines, then the run zone.
  // The buttons live in the action bar fixed to the foot of the screen (spec 4.2, 4.3).
  let onPictures = () => {};
  const pics = pictures(n, images.question, () => onPictures());
  const werkblad = werkbladParts(n, meta);
  const zone = h('div', { class: 'run-zone' });
  const bar = h('div', { class: 'foot actionbar' });
  view(
    topbar('#/', true),
    h('h1', { text: S.vraag(n) }),
    pics,
    werkblad.block,
    zone,
    bar,
  );
  padForFootBar(bar);
  fillRunZone({ zone, bar, werkblad, pics, setOnPictures: (fn) => { onPictures = fn; } }, n, meta);
}

function fillRunZone(ctx, n, meta) {
  const { zone, bar, werkblad, pics } = ctx;
  const q = store.getQ(n);
  if (!q || !Number.isFinite(q.beganAt)) {
    // Before Begin: the werkblad button and Begin sit in the bar. Begin stays disabled until
    // every question picture has loaded.
    const beginBtn = btn(S.begin, () => {
      if (!allLoaded(pics)) return;
      store.begin(n, Date.now());
      fillRunZone(ctx, n, meta);
    }, 'btn primary');
    const gate = () => { beginBtn.disabled = !allLoaded(pics); };
    gate();
    ctx.setOnPictures(gate);
    werkblad.button.remove();
    bar.replaceChildren(werkblad.button, beginBtn);
    zone.replaceChildren(h('p', { class: 'small-line begin-line', text: S.beginLine }));
    return;
  }
  ctx.setOnPictures(() => {});

  // After Begin: the werkblad button goes back into the page under the question picture.
  if (werkblad.button.parentNode !== werkblad.block) werkblad.block.prepend(werkblad.button);

  const hintFiles = (meta.images && meta.images.hints) || [];
  const openedList = h('div', { class: 'hints-opened' });
  const nextSlot = h('div', { class: 'hint-next' });
  const actions = h('div', { class: 'actions' });
  const answerBtn = btn(S.haveAnswer, () => askRoute(n, 'antwoord'), 'btn');
  const struggleBtn = btn(S.struggledEnough, () => askRoute(n, 'gesukkel'), 'btn');
  actions.append(answerBtn);

  const hasHints = (meta.hints | 0) > 0;
  zone.replaceChildren(
    h('p', { class: 'lead', text: S.twoMinutes }),
    hasHints ? h('div', { class: 'hint-row' }, openedList) : h('p', { class: 'no-hints', text: S.noHints }),
  );
  if (hasHints) bar.replaceChildren(nextSlot, actions);
  else bar.replaceChildren(actions);

  let nextKey = '';
  let scrollToNew = false;
  const tick = () => {
    const st = clock.status(meta, store.getQ(n), Date.now(), SPEED);
    if (hasHints) {
      while (openedList.children.length < st.opened) {
        const i = openedList.children.length;
        const sec = h('section', { class: 'block hint-open' },
          h('h2', { text: S.hintHeading(i + 1) }),
          pictures(n, hintFiles[i] ? [hintFiles[i]] : []),
        );
        openedList.append(sec);
        if (scrollToNew && openedList.children.length === st.opened) {
          scrollToNew = false;
          sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }
      if (!st.next) {
        if (nextKey !== 'none') { nextSlot.replaceChildren(); nextKey = 'none'; }
      } else if (st.next.ready) {
        const key = `ready${st.next.index}`;
        if (nextKey !== key) {
          const idx = st.next.index;
          nextSlot.replaceChildren(btn(S.hintReady(idx + 1), () => {
            store.openHint(n, idx, Date.now());
            scrollToNew = true;
            tick();
          }, 'btn primary'));
          nextKey = key;
        }
      } else {
        const key = `wait${st.next.index}`;
        const text = clock.formatCountdown(st.next.shownSeconds);
        if (nextKey !== key) {
          nextSlot.replaceChildren(h('button', { type: 'button', class: 'btn hint-locked', disabled: true },
            S.hintLocked(st.next.index + 1), h('span', { class: 'num countdown', text })));
          nextKey = key;
        } else {
          const cd = nextSlot.querySelector('.countdown');
          if (cd && cd.textContent !== text) cd.textContent = text;
        }
      }
    }
    if (st.canStruggleOut && !struggleBtn.isConnected) actions.append(struggleBtn);
    if (!st.canStruggleOut && struggleBtn.isConnected) struggleBtn.remove();
  };
  tick();
  stopTick();
  tickTimer = setInterval(tick, 250);
}

function askRoute(n, via) {
  confirmBox(S.confirmTitle, S.confirmLine, S.confirmYes, S.confirmNo, () => {
    store.openRoute(n, via, Date.now());
    redirect(`#/roete/${n}`);
  });
}

// ---------- 4.4 Die roete ----------

function routeSections(n, meta) {
  const images = meta.images || {};
  const opened = meta.openedBy || {};
  const href = 'https://wa.me/?text=' + encodeURIComponent(S.whatsappMessage(n, meta.stry || ''));
  return [
    h('section', { class: 'block' }, h('h2', { text: S.routeHeading }), pictures(n, images.route)),
    h('section', { class: 'block' }, h('h2', { text: S.solutionHeading }), pictures(n, images.solution)),
    h('section', { class: 'block' }, h('h2', { text: S.openedByHeading }), h('p', { class: 'opened-line', text: opened.line || '' })),
    h('section', { class: 'block' },
      h('h2', { text: S.stryHeading }),
      h('p', { class: 'stry', text: meta.stry || '' }),
      h('a', { class: 'btn', href, target: '_blank', rel: 'noopener', id: 'whatsapp' }, S.whatsapp),
      h('p', { class: 'small-line', text: S.whatsappLine }),
    ),
  ];
}

async function renderRoete(n, state, seq) {
  const q = state.questions[String(n)];
  if (!q || !Number.isFinite(q.routeOpenedAt) || q.closedAt || !isPublished(n)) {
    redirect(`#/vraag/${n}`); // the question screen has its own guard
    return;
  }
  const meta = await metaOrError(n, seq);
  if (!meta || seq !== routeSeq) return;
  view(
    topbar('#/', true),
    h('h1', { text: S.vraag(n) }),
    routeSections(n, meta),
    h('div', { class: 'block' }, btn(S.toTerugkyk, () => go(`#/terugkyk/${n}`), 'btn primary big')),
  );
}

// ---------- 4.5 Terugkyk ----------

function choiceGroup(question, options, onPick, chosen) {
  const wrap = h('div', { class: 'choices' });
  const buttons = options.map(([value, label]) => {
    const on = chosen !== null && chosen !== undefined && value === chosen;
    const b = h('button', { type: 'button', class: 'btn choice', 'aria-pressed': on ? 'true' : 'false' }, label);
    b.addEventListener('click', () => {
      buttons.forEach((x) => x.setAttribute('aria-pressed', x === b ? 'true' : 'false'));
      onPick(value);
    });
    return b;
  });
  wrap.append(...buttons);
  return h('fieldset', { class: 'block tk-group' }, h('legend', { text: question }), wrap);
}

function renderTerugkyk(n, state) {
  const q = state.questions[String(n)];
  if (!q || !Number.isFinite(q.routeOpenedAt) || q.closedAt || !isPublished(n)) {
    redirect(`#/vraag/${n}`); // the question screen has its own guard
    return;
  }
  // Taps made earlier (before a trip to the card, or a back and return) come back from the
  // draft. The draft is not an answer until Stoor en maak toe.
  const d = store.getDraft(n) || {};
  const answers = {
    withinTwoMinutes: typeof d.withinTwoMinutes === 'boolean' ? d.withinTwoMinutes : null,
    move: Number.isInteger(d.move) && d.move >= 0 && d.move <= 8 ? d.move : null,
    stuck: Object.prototype.hasOwnProperty.call(S.stuckNames, d.stuck) ? d.stuck : null,
  };
  const pick = (key) => (v) => { answers[key] = v; store.setDraft(n, answers); refresh(); };
  const save = btn(S.tkSave, () => {
    if (!ready()) return;
    store.closeQuestion(n, answers, Date.now());
    store.clearDraft();
    const m = n + 1;
    flash = m <= TOTAL && isPublished(m) ? S.closedToast(n, m) : null;
    redirect('#/');
  }, 'btn primary big');
  const ready = () => answers.withinTwoMinutes !== null && answers.move !== null && answers.stuck !== null;
  const refresh = () => { save.disabled = !ready(); };
  refresh();

  const moveOptions = [1, 2, 3, 4, 5, 6, 7, 8].map((m) => [m, S.moveNames[m]]);
  moveOptions.push([0, S.geen]);

  view(
    topbar(`#/roete/${n}`, true),
    h('h1', { text: S.terugkyk }),
    choiceGroup(S.tkWithin, [[true, S.ja], [false, S.nee]], pick('withinTwoMinutes'), answers.withinTwoMinutes),
    choiceGroup(S.tkMove, moveOptions, pick('move'), answers.move),
    choiceGroup(S.tkStuck, Object.entries(S.stuckNames), pick('stuck'), answers.stuck),
    h('div', { class: 'block' }, save),
  );
}

function terugkykAnswers(t) {
  if (!t) return null;
  const moveText = t.move === 0 ? S.geen : S.moveNames[t.move];
  const rows = [
    [S.tkWithin, t.withinTwoMinutes ? S.ja : S.nee],
    [S.tkMove, moveText],
    [S.tkStuck, S.stuckNames[t.stuck]],
  ];
  return h('section', { class: 'block my-terugkyk' },
    h('h2', { text: S.myTerugkyk }),
    rows.map(([question, answer]) => h('div', { class: 'tk-answer' },
      h('p', { class: 'muted', text: question }),
      h('p', { class: 'answer', text: answer }),
    )),
  );
}

// ---------- 4.6 Vasgevang-kaart ----------

function renderKaart() {
  view(
    h('h1', { text: S.cardHeading }),
    h('p', { class: 'lead', text: S.cardIntro }),
    h('ol', { class: 'card-moves' }, S.cardMovesHtml.map((html) => h('li', { html }))),
    h('p', { class: 'foot-line', text: S.cardFoot }),
    h('div', { class: 'block' }, btn(S.terug, () => goBack('#/'), 'btn big')),
  );
}

// ---------- 4.7 Die reëls van die spel ----------

function renderRules(first) {
  view(
    h('h1', { text: S.rulesHeading }),
    h('ol', { class: 'rules' }, S.rulesHtml.map((text) => h('li', { text }))),
    h('div', { class: 'block' }, first
      ? btn(S.rulesAccept, () => { store.setRulesSeen(); redirect('#/'); }, 'btn primary big')
      : btn(S.terug, () => goBack('#/meer'), 'btn big')),
  );
}

// ---------- 4.9 My patrone ----------

async function finishedMetas(state) {
  const done = Object.keys(state.questions).filter((k) => state.questions[k].closedAt);
  const metas = {};
  await Promise.all(done.map(async (k) => {
    try { metas[k] = await loadMeta(Number(k)); } catch (e) { /* counted without tags */ }
  }));
  return metas;
}

function bars(rows, max) {
  return h('div', { class: 'bars' }, rows.map(([label, count]) => h('div', { class: 'bar-row' },
    h('span', { class: 'bar-label', text: label }),
    h('span', { class: 'bar-track' }, h('span', { class: 'bar-fill', style: `width:${max ? (count / max) * 100 : 0}%` })),
    h('span', { class: 'num bar-count', text: String(count) }),
  )));
}

// A trailing Roman numeral (Vraestel I, Vraestel II) is set in the number font, whose capital I
// has serifs, so it cannot read as the letter l. The text itself stays the same.
function withRoman(name) {
  const m = /^(.*\s)([IVX]+)$/.exec(String(name));
  if (!m) return String(name);
  return [m[1], h('span', { class: 'roman', text: m[2] })];
}

function statTable(caption, rows, nameOf) {
  if (!rows.length) return null;
  const tyd = (avg) => (avg ? (avg.capped ? S.cappedMinutes : S.minutes(avg.minutes)) : '');
  return h('div', { class: 'stat-table' },
    h('h3', { text: caption }),
    h('table', null,
      h('colgroup', null, h('col', { class: 'c-name' }), h('col', { class: 'c-vrae' }), h('col', { class: 'c-wenke' }), h('col', { class: 'c-tyd' })),
      h('thead', null, h('tr', null,
        h('th', { scope: 'col' }), h('th', { scope: 'col', text: S.colVrae }),
        h('th', { scope: 'col', text: S.colWenke }), h('th', { scope: 'col', text: S.colTyd }))),
      h('tbody', null, rows.map((r) => h('tr', null,
        h('th', { scope: 'row' }, withRoman(nameOf(r.name))),
        h('td', { class: 'num', text: String(r.count) }),
        h('td', { class: 'num', text: String(r.hints) }),
        h('td', { class: 'num', text: tyd(r.avg) }),
      ))),
    ),
  );
}

async function exportFile(state) {
  const metas = await finishedMetas(state);
  const tags = {};
  for (const k of Object.keys(metas)) {
    const m = metas[k];
    const t = m.tags || {};
    tags[k] = { topic: t.topic, subtopic: t.subtopic, paper: m.paper, kind: t.kind, device: t.device, marks: m.marks };
  }
  const data = store.buildExport(tags);
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  return { blob, name: 'vlak4-rugsteun.json' };
}

async function saveExport() {
  const { blob, name } = await exportFile(store.load());
  downloadBlob(blob, name);
}

async function shareExport() {
  const { blob, name } = await exportFile(store.load());
  let file = null;
  try { file = new File([blob], name, { type: 'application/json' }); } catch (e) { file = null; }
  if (file && navigator.canShare && navigator.share && navigator.canShare({ files: [file] })) {
    try {
      await navigator.share({ files: [file] });
    } catch (e) {
      if (!e || e.name !== 'AbortError') downloadBlob(blob, name);
    }
    return;
  }
  downloadBlob(blob, name);
}

async function renderPatrone(state, seq) {
  const done = Object.keys(state.questions).filter((k) => state.questions[k].closedAt);
  if (!done.length) {
    view(topbar('#/', false), h('h1', { text: S.patroneHeading }), h('p', { class: 'lead', text: S.patroneEmpty }));
    return;
  }
  const metas = await finishedMetas(state);
  if (seq !== routeSeq) return;
  const r = stats.compute(state.questions, metas, clock.minuteMs(SPEED));
  const stuckRows = stats.STUCK_ORDER.map((k) => [S.stuckNames[k], r.stuck[k]]);
  const moveRows = r.moves.map((m) => [S.moveNames[m.move], m.count]);
  const moveMax = Math.max(0, ...r.moves.map((m) => m.count));

  view(
    topbar('#/', false),
    h('h1', { text: S.patroneHeading }),
    h('section', { class: 'block stat' }, h('h2', { text: S.blkClosed }), h('p', { class: 'num big-number', text: String(r.closed) })),
    h('section', { class: 'block stat' }, h('h2', { text: S.blkFirst2 }), h('p', { text: S.first2Line(r.within, r.closed) })),
    h('section', { class: 'block stat' }, h('h2', { text: S.blkStuck }), bars(stuckRows, r.closed)),
    moveRows.length ? h('section', { class: 'block stat' }, h('h2', { text: S.blkOpened }), bars(moveRows, moveMax)) : null,
    h('section', { class: 'block stat' },
      h('h2', { text: S.blkHints }),
      statTable(S.tblTopic, r.tables.topic, (x) => x),
      statTable(S.tblPaper, r.tables.paper, (x) => S.paperNames[x] || x),
      statTable(S.tblKind, r.tables.kind, (x) => S.kindNames[x] || x),
    ),
    h('div', { class: 'block foot-buttons' },
      btn(S.sharePatrone, shareExport, 'btn primary big'),
      btn(S.savePatrone, saveExport, 'btn big'),
      h('p', { class: 'small-line', text: S.onlyYou }),
    ),
  );
}

// ---------- 4.10 Meer ----------

function renderMeer() {
  const msg = h('p', { class: 'status-line', role: 'status' });
  const input = h('input', { type: 'file', accept: 'application/json,.json', class: 'hidden-input', id: 'restore-file' });
  input.addEventListener('change', async () => {
    const file = input.files && input.files[0];
    input.value = '';
    msg.textContent = '';
    if (!file) return;
    let obj = null;
    try { obj = JSON.parse(await file.text()); } catch (e) { obj = null; }
    if (!store.isBackup(obj)) { msg.textContent = S.restoreBad; return; }
    confirmBox(null, S.restoreConfirm, S.restoreYes, S.restoreNo, () => {
      msg.textContent = store.replaceAll(obj) ? S.restoreOk : S.restoreBad;
    });
  });

  view(
    topbar('#/', false),
    h('h1', { text: S.meerHeading }),
    h('div', { class: 'block' }, btn(S.rulesLink, () => go('#/reels'), 'btn big')),
    h('section', { class: 'block' },
      h('h2', { text: S.backupHeading }),
      h('p', { text: S.backupExplain }),
      h('div', { class: 'stack' },
        btn(S.backupSave, saveExport, 'btn big'),
        btn(S.backupLoad, () => input.click(), 'btn big'),
      ),
      input,
      msg,
    ),
  );
}

// ---------- start ----------

window.addEventListener('hashchange', () => { internalNav = true; route(); });

(async function start() {
  await loadIndex();
  route();
})();
