"""Play the Vlak 4 shell through with Playwright's own Chromium, headless, and print PASS or FAIL per check.

Run:  python tools/verify_shell.py [download-folder]
It serves the repo on http://localhost:5230 by itself. Test downloads go to the folder given
(default: a fresh temp folder), never to the Downloads folder. It reads the page through the
DOM and the page text only: no screenshots.
Covers APP-SPEC.md section 7, items 1 to 17, at 800 x 1280 and 1280 x 800, using ?toets=1.
"""
import json
import re
import sys
import tempfile
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
PORT = 5230
BASE = f"http://localhost:{PORT}/"
T = BASE + "?toets=1"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix="vlak4-verify-"))
OUT.mkdir(parents=True, exist_ok=True)

RESULTS = []


def check(label, name, ok, detail=""):
    RESULTS.append(bool(ok))
    line = f"{'PASS' if ok else 'FAIL'} [{label}] {name}"
    if not ok and detail:
        line += f"  ({detail})"
    print(line, flush=True)


# ---------- server ----------

class Quiet(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".js": "text/javascript", ".json": "application/json", ".css": "text/css",
        ".png": "image/png", ".pdf": "application/pdf", ".html": "text/html",
    }

    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def serve():
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


# ---------- expected approved wording (copied independently from the plan and spec) ----------

RULES = [
    "Een vraag op 'n slag. Die volgende een maak oop wanneer hierdie een toe is. Slaan 'n dag oor of doen twee op 'n goeie dag: jou keuse.",
    "Skryf iets binne 2 minute, al is dit verkeerd. 'n Leë bladsy is die enigste manier om te misluk.",
    "Sukkel eers eerlik. Die Wenk-knoppie maak vanself oop wanneer die tyd om is.",
    "Die roete is vir NÁ jou poging. Lees die roete, nie net die antwoord nie.",
    'Elke vraag het een "Stry met juffrou". Jy mag dit WhatsApp. Jy hoef nie.',
    "Geen punte nie. Die app hou net boek van jou patrone, vir jou.",
]
MOVES = [
    ("Skryf neer wat jy weet, in simbole.", "Elke gegewe word 'n vergelyking of 'n etiket."),
    ("Teken dit, of teken dit oor, groter.", "Sit elke gegewe op die figuur."),
    ("Probeer 'n regte getal.", "As daar 'n k of 'n t is, kies 2 en kyk wat gebeur."),
    ("Werk terugwaarts.", "Wat vra hulle? Wat sou ek nodig hê om DIT te kry?"),
    ("Vra: wat sou dit maklik maak?", "Watter feit ontbreek? Waar kom dit vandaan?"),
    ("Soek die versteekte ding.", "360° in 'n sirkel, 30° per uur, 'n hoek van 90° wat nie geteken is nie, die woord \"raaklyn\"."),
    ('Gebruik die "wys dat".', "'n \"Wys dat\"-antwoord is gegee. Gebruik dit al kon jy dit nie bewys nie, en gaan aan."),
    ("Skryf 'n argument.", "As daar geen berekening is nie, skryf 'n sin met 'n rede. Die IEB betaal daarvoor."),
]
CARD_FOOT = "Sukkel is nie 'n teken dat die vraag stukkend is nie. Dit is die oefening."
APPROVED_PUNTE_LINE = RULES[5]

ALL_TOPICS = ["Rye en reekse", "Finansies", "Funksies en inverses", "Calculus", "Waarskynlikheid",
              "Statistiek", "Analitiese meetkunde", "Trigonometrie", "Euklidiese meetkunde"]

FORBIDDEN = [
    ("a date (d/m)", re.compile(r"\b\d{1,2}[/.\-]\d{1,2}([/.\-]\d{2,4})?\b")),
    ("a year", re.compile(r"\b(19|20)\d{2}\b")),
    ("a month name", re.compile(r"\b(januarie|februarie|maart|april|mei|junie|julie|augustus|september|oktober|november|desember|january|february|march|june|july|august|october|december)\b", re.I)),
    ("a day name", re.compile(r"\b(maandag|dinsdag|woensdag|donderdag|vrydag|saterdag|sondag|monday|tuesday|wednesday|thursday|friday|saturday|sunday|vandag|gister)\b", re.I)),
    ("a percent sign", re.compile(r"%")),
    ("goed gedaan", re.compile(r"goed\s+gedaan", re.I)),
    ("an em-dash", re.compile("\u2014")),
]
PUNTE = re.compile(r"punte", re.I)


# ---------- page helpers ----------

LAYOUT_JS = """() => {
  const de = document.documentElement;
  const hscroll = Math.max(de.scrollWidth, document.body.scrollWidth) > de.clientWidth + 1;
  const small = [];
  for (const el of document.querySelectorAll('button, a.btn, [role=button]')) {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    if (!r.width || !r.height || cs.display === 'none' || cs.visibility === 'hidden') continue;
    if (r.height < 48) small.push((el.innerText || '').trim().slice(0, 30) + ' ' + Math.round(r.height) + 'px');
  }
  const tiny = [];
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (w.nextNode()) {
    const t = w.currentNode;
    if (!t.textContent.trim()) continue;
    const el = t.parentElement;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    const fs = parseFloat(getComputedStyle(el).fontSize);
    if (fs < 17) tiny.push(t.textContent.trim().slice(0, 30) + ' ' + fs + 'px');
  }
  return { hscroll, sw: de.scrollWidth, cw: de.clientWidth, small, tiny };
}"""

PALETTE_JS = """() => {
  const bad = ['52, 211, 153', '251, 113, 133'];
  const hits = [];
  for (const el of document.querySelectorAll('*')) {
    const cs = getComputedStyle(el);
    for (const p of ['color', 'backgroundColor', 'borderTopColor', 'borderRightColor', 'borderBottomColor', 'borderLeftColor', 'outlineColor']) {
      if (bad.some((b) => cs[p].includes(b))) hits.push(el.tagName + '.' + el.className + ' ' + p);
    }
  }
  return hits;
}"""


class Run:
    def __init__(self, page, label):
        self.page = page
        self.label = label
        self.texts = {}
        self.layout_fail = []
        self.button_fail = []
        self.font_fail = []

    def ok(self, name, cond, detail=""):
        check(self.label, name, cond, detail)

    def body(self):
        return self.page.evaluate("document.body.innerText")

    def snap(self, name):
        self.page.wait_for_timeout(150)
        self.texts[name] = self.body()
        lay = self.page.evaluate(LAYOUT_JS)
        if lay["hscroll"]:
            self.layout_fail.append(f"{name}: {lay['sw']}>{lay['cw']}")
        if lay["small"]:
            self.button_fail.append(f"{name}: {lay['small'][:3]}")
        if lay["tiny"]:
            self.font_fail.append(f"{name}: {lay['tiny'][:3]}")

    def hash(self):
        return self.page.evaluate("location.hash")

    def set_hash(self, h):
        self.page.evaluate(f"location.hash = {json.dumps(h)}")
        self.page.wait_for_timeout(400)

    def storage(self):
        return self.page.evaluate("localStorage.getItem('vlak4.v1')")

    def state(self):
        raw = self.storage()
        return json.loads(raw) if raw else None

    def btn(self, name):
        return self.page.get_by_role("button", name=name, exact=True)

    def countdown(self):
        t = self.page.locator(".countdown").first.inner_text()
        m, s = t.split(":")
        return int(m) * 60 + int(s)

    def imgs_loaded(self):
        return self.page.evaluate("[...document.querySelectorAll('.paper-img')].every(i => i.complete && i.naturalWidth > 0)")


def wait_imgs(r):
    r.page.wait_for_function("[...document.querySelectorAll('.paper-img')].every(i => i.complete)", timeout=10000)


# ---------- the play-through ----------

def play(browser, w, hgt):
    label = f"{w}x{hgt}"
    ctx = browser.new_context(viewport={"width": w, "height": hgt}, accept_downloads=True)
    page = ctx.new_page()
    errors, hosts = [], set()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("request", lambda req: hosts.add(urlparse(req.url).hostname or req.url.split(":")[0]))
    r = Run(page, label)
    dl = OUT / label
    dl.mkdir(exist_ok=True)

    # 1. first open: rules, then Tuis
    page.goto(T)
    page.wait_for_selector("h1")
    r.snap("rules-first")
    lis = page.locator("ol.rules li").all_inner_texts()
    r.ok("01 first open shows the rules screen", page.locator("h1").inner_text() == "Die reëls van die spel" and r.btn("Ek verstaan, wys die eerste vraag").count() == 1)
    r.ok("01 six rules word for word", [x.strip() for x in lis] == RULES, str(lis))
    r.btn("Ek verstaan, wys die eerste vraag").click()
    page.wait_for_selector(".tile")
    r.snap("tuis-start")
    tiles = page.evaluate("[...document.querySelectorAll('.tile')].map(t => ({n: +t.dataset.n, cls: t.className, text: t.innerText.trim()}))")
    t1 = tiles[0]
    locked = [t for t in tiles[1:] if "locked" in t["cls"] and t["text"] == f"Vraag {t['n']}"]
    r.ok("01 Tuis: Vraag 1 glowing with Maak oop", "current" in t1["cls"] and "Maak oop" in t1["text"], str(t1))
    r.ok("01 Tuis: 19 locked tiles show the number only", len(tiles) == 20 and len(locked) == 19, str(tiles[1:3]))
    head = page.locator(".home-head").inner_text()
    r.ok("01 Tuis heading and line", "Vlak 4 Brain Training" in head and "Een vraag op 'n slag." in head)
    foot = page.locator("nav.foot button").all_inner_texts()
    r.ok("01 Tuis foot buttons", foot == ["Vasgevang-kaart", "My patrone", "Meer"], str(foot))

    # route guards before anything is done
    r.set_hash("#/vraag/2")
    r.ok("guard: #/vraag/2 does not open while Vraag 1 is open", r.hash() in ("#/", "") and "Maak oop" in r.body())
    r.set_hash("#/vraag/3")
    r.ok("guard: #/vraag/3 (unpublished, locked) does not open", r.hash() in ("#/", ""))
    r.set_hash("#/roete/1")
    r.ok("guard: #/roete/1 does not open before the confirm box", r.hash() != "#/roete/1" and "Die oplossing" not in r.body())
    r.set_hash("#/terugkyk/1")
    r.ok("guard: #/terugkyk/1 does not open before the route", r.hash() != "#/terugkyk/1" and "Stoor en maak toe" not in r.body())

    # My patrone before anything is finished
    r.set_hash("#/patrone")
    r.snap("patrone-empty")
    r.ok("12 My patrone empty line before the first question", "Hier is nog niks nie. Jou patrone verskyn sodra jou eerste vraag toe is." in r.body())
    r.set_hash("#/")

    # 2. before Begin
    page.locator(".tile.current").get_by_role("button", name="Maak oop").click()
    page.wait_for_selector(".paper-img")
    wait_imgs(r)
    r.snap("vraag1-before")
    b = r.body()
    r.ok("02 before Begin: no countdown, no hint row, no route buttons",
         page.locator(".countdown").count() == 0 and page.locator(".hint-row").count() == 0
         and r.btn("Ek het 'n antwoord").count() == 0 and r.btn("Ek het genoeg gesukkel").count() == 0
         and "maak oop oor" not in b and "Wys Wenk" not in b, b[:200])
    r.ok("02 before Begin: heading, werkblad, Begin and both small lines",
         page.locator("h1").inner_text() == "Vraag 1" and r.btn("Laai die werkblad af").count() == 1 and r.btn("Begin").count() == 1
         and "Maak die werkblad in Samsung Notes oop en werk daar." in b
         and "Die wenke se horlosie begin loop wanneer jy Begin tik, en loop aan terwyl jy skryf." in b)
    r.ok("02 Vasgevang-kaart link at the top of the question screen", page.locator(".topbar").get_by_role("button", name="Vasgevang-kaart").count() == 1)
    r.ok("02 question picture loaded in a paper card", r.imgs_loaded() and page.locator(".paper .paper-img").count() >= 1)

    # werkblad download (blob) and a failed download
    with page.expect_download() as d:
        r.btn("Laai die werkblad af").click()
    dwn = d.value
    target = dl / dwn.suggested_filename
    dwn.save_as(str(target))
    r.ok("werkblad downloads through a blob: link as a PDF",
         dwn.url.startswith("blob:") and dwn.suggested_filename == "werkblad-v01.pdf" and target.read_bytes()[:4] == b"%PDF", dwn.url[:30])
    page.route("**/werkblad-v01.pdf*", lambda route: route.abort())
    r.btn("Laai die werkblad af").click()
    page.wait_for_timeout(500)
    r.snap("werkblad-error")
    r.ok("werkblad failure shows the spec line", "Die werkblad wou nie aflaai nie. Probeer weer." in r.body())
    page.unroute("**/werkblad-v01.pdf*")

    # picture that will not load, then Probeer weer
    page.route("**/v01/vraag-1.png*", lambda route: route.abort())
    page.reload()
    page.wait_for_selector(".paper-error")
    r.snap("img-error")
    r.ok("picture failure shows the spec line and Probeer weer",
         "Die prent wou nie laai nie. Kyk of jy internet het en probeer weer." in r.body() and r.btn("Probeer weer").count() == 1)
    page.unroute("**/v01/vraag-1.png*")
    r.btn("Probeer weer").click()
    page.wait_for_selector(".paper-img")
    wait_imgs(r)
    r.ok("Probeer weer loads the picture", r.imgs_loaded())

    # tap a picture: full-screen overlay with Terug, zoom allowed
    page.locator(".paper").first.click()
    page.wait_for_selector(".overlay img")
    r.snap("overlay")
    vp = page.evaluate("document.querySelector('meta[name=viewport]').content")
    r.ok("tap picture opens full screen with Terug", page.locator(".overlay").get_by_role("button", name="Terug").count() == 1)
    r.ok("page zoom is allowed (no user-scalable=no, no maximum-scale)", "user-scalable" not in vp and "maximum-scale" not in vp, vp)
    page.locator(".overlay").get_by_role("button", name="Terug").click()
    page.wait_for_timeout(300)
    r.ok("Terug closes the picture and stays on the question", page.locator(".overlay").count() == 0 and r.hash() == "#/vraag/1")

    # 3. after Begin
    r.btn("Begin").click()
    page.wait_for_selector(".countdown")
    r.snap("vraag1-running")
    b = r.body()
    hint_text = page.locator(".hint-locked").inner_text()
    r.ok("03 after Begin: Wenk 1 locked with a countdown", re.fullmatch(r"Wenk 1 maak oop oor \d\d:\d\d", hint_text.strip()) is not None
         and page.locator(".hint-locked").is_disabled(), hint_text)
    r.ok("03 after Begin: 'Ek het genoeg gesukkel' absent, 'Ek het 'n antwoord' present",
         r.btn("Ek het genoeg gesukkel").count() == 0 and r.btn("Ek het 'n antwoord").count() == 1)
    r.ok("03 after Begin: the 2 minute line shows", "Skryf iets neer binne 2 minute, al is dit verkeerd." in b)
    r.ok("03 Begin button gone after Begin", r.btn("Begin").count() == 0)
    r.ok("countdown uses JetBrains Mono", "JetBrains Mono" in page.evaluate("getComputedStyle(document.querySelector('.countdown')).fontFamily"))

    # 4. reload mid-countdown
    c1 = r.countdown()
    t1 = time.time()
    page.wait_for_timeout(2000)
    page.reload()
    page.wait_for_selector(".countdown")
    c2 = r.countdown()
    real = time.time() - t1
    expected = c1 - real * 60
    r.ok("04 reload mid-countdown carries on from the right place", 0 < c2 < c1 - 60 and abs(c2 - expected) <= 90,
         f"before {c1}s, after {c2}s, expected about {int(expected)}s")

    # the card never stops the clock
    page.locator(".topbar").get_by_role("button", name="Vasgevang-kaart").click()
    page.wait_for_selector("ol.card-moves")
    r.snap("kaart")
    moves = page.evaluate("[...document.querySelectorAll('ol.card-moves li')].map(li => ({t: li.innerText.trim(), b: li.querySelector('strong') && li.querySelector('strong').innerText.trim()}))")
    r.ok("kaart: eight moves word for word with bold names",
         len(moves) == 8 and all(m["b"] == MOVES[i][0] and m["t"] == f"{MOVES[i][0]} {MOVES[i][1]}" for i, m in enumerate(moves)), str(moves[:2]))
    kb = r.body()
    r.ok("kaart: heading, intro line and foot line",
         page.locator("h1").inner_text() == "Vasgevang-kaart"
         and 'Agt stappe, in hierdie volgorde, voordat jy mag sê "ek weet nie".' in kb and CARD_FOOT in kb)
    before = r.storage()
    page.wait_for_timeout(1000)
    r.btn("Terug").click()
    page.wait_for_selector(".countdown, .hint-next button")
    r.ok("kaart: Terug returns to the question, clock still running, nothing counted",
         r.hash() == "#/vraag/1" and r.storage() == before
         and (page.locator(".countdown").count() == 0 or r.countdown() < c2))

    # 5. hints open on time
    r.btn("Wys Wenk 1").wait_for(timeout=15000)
    r.snap("vraag1-hint1-ready")
    r.ok("05 Wenk 1 ready when the time is up, 'Ek het genoeg gesukkel' now shows",
         r.btn("Wys Wenk 1").count() == 1 and r.btn("Ek het genoeg gesukkel").count() == 1)
    r.btn("Wys Wenk 1").click()
    page.wait_for_selector(".hint-open h2")
    page.wait_for_selector(".countdown")
    c = r.countdown()
    ht = page.locator(".hint-locked").inner_text().strip()
    r.ok("05 Wenk 1 opens with its picture, Wenk 2 starts a 5 minute countdown",
         page.locator(".hint-open h2").first.inner_text() == "Wenk 1" and ht.startswith("Wenk 2 maak oop oor") and 240 <= c <= 300, f"{ht}")
    r.btn("Wys Wenk 2").wait_for(timeout=10000)
    r.btn("Wys Wenk 2").click()
    r.btn("Wys Wenk 3").wait_for(timeout=10000)
    r.btn("Wys Wenk 3").click()
    page.wait_for_timeout(500)
    wait_imgs(r)
    r.snap("vraag1-all-hints")
    heads = page.locator(".hint-open h2").all_inner_texts()
    r.ok("05 all three hints stay open, no further countdown",
         heads == ["Wenk 1", "Wenk 2", "Wenk 3"] and page.locator(".countdown").count() == 0 and r.imgs_loaded(), str(heads))

    # 6. confirm box
    r.btn("Ek het genoeg gesukkel").click()
    page.wait_for_selector(".modal")
    r.snap("confirm")
    mt = page.locator(".modal").inner_text()
    r.ok("06 confirm box shows its two lines and two buttons",
         "Maak die roete oop?" in mt and "Daarna kan jy dit nie weer toemaak vir hierdie vraag nie." in mt
         and r.btn("Ja, wys die roete").count() == 1 and r.btn("Nog nie").count() == 1)
    r.btn("Nog nie").click()
    page.wait_for_timeout(300)
    st = r.state()
    r.ok("06 'Nog nie' opens nothing", page.locator(".modal").count() == 0 and r.hash() == "#/vraag/1"
         and "routeOpenedAt" not in st["questions"]["1"] and "Die oplossing" not in r.body())
    r.set_hash("#/roete/1")
    r.ok("guard: #/roete/1 typed after 'Nog nie' still does not open", r.hash() == "#/vraag/1" and "Die oplossing" not in r.body())
    page.wait_for_selector(".actions button")
    r.btn("Ek het 'n antwoord").click()
    r.btn("Ja, wys die roete").click()
    page.wait_for_selector("h2:has-text('Die oplossing')")
    wait_imgs(r)
    r.snap("roete1")
    st = r.state()
    heads = page.locator("main h2").all_inner_texts()
    rb = r.body()
    r.ok("06 'Ja, wys die roete' opens the route", r.hash() == "#/roete/1" and st["questions"]["1"].get("routeVia") == "antwoord"
         and isinstance(st["questions"]["1"].get("routeOpenedAt"), (int, float)))
    r.ok("roete: sections in the spec order", heads == ["Die roete", "Die oplossing", "Wat het dit oopgemaak", "Stry met juffrou"], str(heads))
    r.ok("roete: opened-by line, stry line, small line, Gaan na Terugkyk",
         "Kaart-stap 3: Probeer 'n regte getal." in rb and "DUMMY: dit is 'n toetsvraag sonder inhoud." in rb
         and "Jy kies self vir wie jy dit stuur. Jy hoef nie." in rb and r.btn("Gaan na Terugkyk").count() == 1)

    # 15. WhatsApp link
    a = page.locator("a#whatsapp")
    href = a.get_attribute("href")
    u = urlparse(href)
    text = parse_qs(u.query).get("text", [""])[0]
    r.ok("15 WhatsApp: wa.me with no number, ready message, new tab",
         u.scheme == "https" and u.netloc == "wa.me" and u.path == "/" and a.get_attribute("target") == "_blank"
         and a.inner_text().strip() == "Stuur op WhatsApp"
         and text == "Vraag 1, Stry met juffrou: DUMMY: dit is 'n toetsvraag sonder inhoud.\n\nEk dink:", href)

    # 7. Terugkyk
    r.btn("Gaan na Terugkyk").click()
    page.wait_for_selector("fieldset")
    r.snap("terugkyk1")
    save = r.btn("Stoor en maak toe")
    s0 = save.is_disabled()
    groups = page.locator("fieldset")
    legends = page.locator("fieldset legend").all_inner_texts()
    opts = [groups.nth(i).locator("button").all_inner_texts() for i in range(3)]
    r.ok("07 Terugkyk: three questions with the spec buttons",
         legends == ["Het ek binne 2 minute iets neergeskryf?", "Watter kaart-stap het dit oopgemaak?", "Waar het ek vasgehaak?"]
         and opts[0] == ["Ja", "Nee"]
         and opts[1] == ["Skryf in simbole", "Teken dit groter", "Probeer 'n regte getal", "Werk terugwaarts", "Wat sou dit maklik maak?",
                         "Soek die versteekte ding", 'Gebruik die "wys dat"', "Skryf 'n argument", "Geen"]
         and opts[2] == ["Begin", "Middel", "Einde", "Nêrens"], str(opts))
    groups.nth(0).get_by_role("button", name="Ja", exact=True).click()
    s1 = save.is_disabled()
    groups.nth(1).get_by_role("button", name="Probeer 'n regte getal", exact=True).click()
    s2 = save.is_disabled()
    groups.nth(2).get_by_role("button", name="Middel", exact=True).click()
    s3 = save.is_disabled()
    r.ok("07 save stays dimmed until all three are answered", s0 and s1 and s2 and not s3, f"{s0} {s1} {s2} {s3}")
    hits = page.evaluate(PALETTE_JS)
    r.ok("Terugkyk uses no --good/--bad colours", not hits, str(hits[:3]))

    # 8. saving
    save.click()
    page.wait_for_selector(".tile.done")
    page.wait_for_function("document.querySelector('.tile.done .tile-topic').textContent.length > 0", timeout=5000)
    r.snap("tuis-after-1")
    tiles = page.evaluate("[...document.querySelectorAll('.tile')].map(t => ({n: +t.dataset.n, cls: t.className, text: t.innerText.trim()}))")
    toast = page.locator(".toast").inner_text() if page.locator(".toast").count() else ""
    r.ok("08 saving ticks Vraag 1, shows its topic, opens Vraag 2",
         r.hash() in ("#/", "") and "done" in tiles[0]["cls"] and "\u2713" in tiles[0]["text"] and "Rye en reekse" in tiles[0]["text"]
         and "current" in tiles[1]["cls"] and "Maak oop" in tiles[1]["text"], str(tiles[:2]))
    r.ok("08 the closing line shows", toast == "Vraag 1 is toe. Vraag 2 is oop.", toast)
    st = r.state()
    q1 = st["questions"]["1"]
    r.ok("08 storage shape as spec 5.5", st["version"] == 1 and st["rulesSeen"] is True
         and q1["terugkyk"] == {"withinTwoMinutes": True, "move": 3, "stuck": "middel"} and len(q1["hintsOpenedAt"]) == 3
         and isinstance(q1["beganAt"], (int, float)) and isinstance(q1["closedAt"], (int, float)), json.dumps(q1))
    page.wait_for_timeout(5500)
    r.ok("08 the closing line goes away after a few seconds", page.locator(".toast").count() == 0)

    # 9. reload keeps the tick
    page.reload()
    page.wait_for_selector(".tile")
    r.ok("09 reload keeps the tick", "done" in page.locator(".tile").first.get_attribute("class"))

    # 4.8 read again
    stored = r.storage()
    r.set_hash("#/vraag/1")
    page.wait_for_selector("h2:has-text('My terugkyk')")
    wait_imgs(r)
    r.snap("vraag1-read-again")
    rb = r.body()
    heads = page.locator("main h2").all_inner_texts()
    r.ok("4.8 read again: question, hints, route, solution, stry, My terugkyk",
         heads == ["Wenk 1", "Wenk 2", "Wenk 3", "Die roete", "Die oplossing", "Wat het dit oopgemaak", "Stry met juffrou", "My terugkyk"]
         and r.btn("Laai die werkblad af").count() == 1 and page.locator("a#whatsapp").count() == 1, str(heads))
    tk = page.locator(".my-terugkyk .answer").all_inner_texts()
    r.ok("4.8 her three answers as plain text, no buttons to change them",
         tk == ["Ja", "Probeer 'n regte getal", "Middel"] and page.locator(".my-terugkyk button").count() == 0, str(tk))
    r.ok("4.8 no Begin, no countdown, no route buttons",
         r.btn("Begin").count() == 0 and page.locator(".countdown").count() == 0 and r.btn("Ek het 'n antwoord").count() == 0)
    page.locator(".paper").first.click()
    page.wait_for_selector(".overlay")
    page.locator(".overlay").get_by_role("button", name="Terug").click()
    with page.expect_download():
        r.btn("Laai die werkblad af").click()
    r.ok("4.8 nothing done in read-again mode is counted", r.storage() == stored)
    r.set_hash("#/roete/1")
    r.ok("guard: #/roete/1 of a finished question goes to read-again", r.hash() == "#/vraag/1")
    r.set_hash("#/terugkyk/1")
    r.ok("guard: #/terugkyk/1 of a finished question cannot be answered again", r.hash() == "#/vraag/1" and r.storage() == stored)

    # 10. the dummy with no hints
    r.set_hash("#/")
    page.locator(".tile.current").get_by_role("button", name="Maak oop").click()
    page.wait_for_selector("h1:has-text('Vraag 2')")
    r.btn("Begin").click()
    page.wait_for_selector(".no-hints")
    r.snap("vraag2-running")
    b = r.body()
    r.ok("10 no-hints line and no hint row",
         "Hierdie vraag het geen wenke nie. Die Vasgevang-kaart is altyd hier." in b and page.locator(".hint-row").count() == 0
         and page.locator(".countdown").count() == 0 and "Wys Wenk" not in b and "maak oop oor" not in b)
    r.ok("10 'Ek het genoeg gesukkel' absent before 20 minutes", r.btn("Ek het genoeg gesukkel").count() == 0)
    r.btn("Ek het genoeg gesukkel").wait_for(timeout=26000)
    r.ok("10 'Ek het genoeg gesukkel' appears after 20 minutes", r.btn("Ek het genoeg gesukkel").count() == 1)
    r.btn("Ek het genoeg gesukkel").click()
    r.btn("Ja, wys die roete").click()
    page.wait_for_selector("h2:has-text('Die oplossing')")
    r.snap("roete2")
    r.ok("10 route of Vraag 2 shows its opened-by line", "Kaart-stap 1: Skryf in simbole." in r.body()
         and r.state()["questions"]["2"]["routeVia"] == "gesukkel")
    r.btn("Gaan na Terugkyk").click()
    page.wait_for_selector("fieldset")
    g = page.locator("fieldset")
    g.nth(0).get_by_role("button", name="Nee", exact=True).click()
    g.nth(1).get_by_role("button", name="Geen", exact=True).click()
    g.nth(2).get_by_role("button", name="Nêrens", exact=True).click()
    r.btn("Stoor en maak toe").click()
    page.wait_for_selector(".tile")
    page.wait_for_timeout(300)
    r.snap("tuis-after-2")

    # 11. Vraag 3 not here yet
    tiles = page.evaluate("[...document.querySelectorAll('.tile')].map(t => ({n: +t.dataset.n, cls: t.className, text: t.innerText.trim()}))")
    t3 = tiles[2]
    r.ok("11 Vraag 3 shows the 'nog nie hier nie' line and no button",
         "current" in t3["cls"] and "Vraag 3 is nog nie hier nie. Dit kom binnekort." in t3["text"]
         and page.locator(".tile.current button").count() == 0, str(t3))
    r.ok("11 no 'Vraag 3 is oop' line when Vraag 3 is not published", page.locator(".toast").count() == 0)
    r.ok("11 tiles 4 to 20 still locked with the number only",
         all("locked" in t["cls"] and t["text"] == f"Vraag {t['n']}" for t in tiles[3:]))
    r.set_hash("#/vraag/3")
    r.ok("guard: #/vraag/3 (unpublished current) does not open", r.hash() in ("#/", ""))

    # 12. My patrone
    r.set_hash("#/patrone")
    page.wait_for_selector("h2:has-text('Vrae toe')")
    r.snap("patrone")
    pb = r.body()
    heads = page.locator("main h2").all_inner_texts()
    r.ok("12 My patrone blocks in order", heads == ["Vrae toe", "Die eerste 2 minute", "Waar ek vashaak", "Wat maak vrae vir my oop", "Wenke en sukkeltyd"], str(heads))
    r.ok("12 counts finished questions only", page.locator(".big-number").inner_text() == "2" and "Iets op papier binne 2 minute: 1 uit 2 vrae" in pb)
    stuck = page.evaluate("[...document.querySelectorAll('section.stat')[2].querySelectorAll('.bar-row')].map(r => r.innerText.replace(/\\s+/g,' ').trim())")
    r.ok("12 four stuck bars with counts", stuck == ["Begin 0", "Middel 1", "Einde 0", "Nêrens 1"], str(stuck))
    mv = page.evaluate("[...document.querySelectorAll('section.stat')[3].querySelectorAll('.bar-row')].map(r => r.innerText.replace(/\\s+/g,' ').trim())")
    r.ok("12 card moves picked, with counts (Geen left out)", mv == ["Probeer 'n regte getal 1"], str(mv))
    caps = page.locator(".stat-table h3").all_inner_texts()
    rows = page.evaluate("[...document.querySelectorAll('.stat-table tbody th')].map(t => t.innerText.trim())")
    cols = page.evaluate("[...document.querySelector('.stat-table thead tr').children].map(t => t.innerText.trim())")
    r.ok("12 three tables with the spec columns and display names",
         caps == ["Per onderwerp", "Per vraestel", "Per soort vraag"] and cols == ["", "Vrae", "Wenke oopgemaak", "Gemiddelde sukkeltyd"]
         and rows == ["Rye en reekse", "Statistiek", "Vraestel I", "Vraestel II", "Raaisel", "Vreemd gevra"], f"{caps} {cols} {rows}")
    unseen = [t for t in ALL_TOPICS if t not in ("Rye en reekse", "Statistiek") and t in pb]
    totals = re.findall(r"\d+\s*(uit|van|of|/)\s*\d+", pb)
    r.ok("12 nothing about unfinished questions, no totals per topic",
         not unseen and "Groot vraag" not in pb and "Redeneer dit" not in pb and totals == ["uit"]
         and not re.search(r"\b20\b(?! min)", pb) and "Vraag 3" not in pb, f"{unseen} {totals}")
    hits = page.evaluate(PALETTE_JS)
    fills = set(page.evaluate("[...document.querySelectorAll('.bar-fill')].map(f => getComputedStyle(f).backgroundColor)"))
    r.ok("12 no --good/--bad colours, every bar one colour (--accent)", not hits and fills == {"rgb(58, 160, 255)"}, f"{hits[:3]} {fills}")
    r.ok("12 foot: share, save, small line", r.btn("Stuur my patrone").count() == 1 and r.btn("Stoor my patrone as 'n lêer").count() == 1
         and "Net jy besluit of jy dit stuur." in pb)

    # share sheet when offered, download when not
    page.evaluate("""() => { window.__shared = null;
      Object.defineProperty(navigator, 'canShare', {value: (d) => !!(d && d.files), configurable: true});
      Object.defineProperty(navigator, 'share', {value: async (d) => { window.__shared = d.files.map(f => f.name + '|' + f.type); }, configurable: true}); }""")
    r.btn("Stuur my patrone").click()
    page.wait_for_function("window.__shared !== null", timeout=5000)
    r.ok("Stuur my patrone uses the share sheet with the file", page.evaluate("window.__shared") == ["vlak4-rugsteun.json|application/json"])
    page.evaluate("() => { Object.defineProperty(navigator, 'canShare', {value: () => false, configurable: true}); }")
    with page.expect_download() as d:
        r.btn("Stuur my patrone").click()
    r.ok("Stuur my patrone falls back to a blob: download", d.value.url.startswith("blob:") and d.value.suggested_filename == "vlak4-rugsteun.json")
    with page.expect_download() as d:
        r.btn("Stoor my patrone as 'n lêer").click()
    p = dl / "patrone.json"
    d.value.save_as(str(p))
    ex = json.loads(p.read_text(encoding="utf-8"))
    r.ok("patterns file: storage object plus tags per finished question",
         ex["version"] == 1 and set(ex["questions"]) == {"1", "2"}
         and ex["tags"]["1"] == {"topic": "Rye en reekse", "subtopic": "dummy", "paper": "I", "kind": "P", "device": "dummy", "marks": 6}
         and ex["tags"]["2"]["kind"] == "S" and d.value.url.startswith("blob:"), json.dumps(ex.get("tags")))

    # 13. backup, clear, restore
    r.set_hash("#/meer")
    page.wait_for_selector("h2:has-text('Rugsteun')")
    r.snap("meer")
    mb = r.body()
    r.ok("Meer: rules link, Rugsteun text and both buttons",
         r.btn("Die reëls van die spel").count() == 1 and r.btn("Stoor 'n rugsteun").count() == 1 and r.btn("Laai 'n rugsteun terug").count() == 1
         and "Jou vordering bly net op hierdie tablet. 'n Rugsteun is 'n klein lêer wat jy kan bêre, sodat niks verlore gaan as die tablet skoongemaak word nie." in mb)
    with page.expect_download() as d:
        r.btn("Stoor 'n rugsteun").click()
    backup = dl / "vlak4-rugsteun.json"
    d.value.save_as(str(backup))
    r.ok("13 backup file saved through a blob: link", d.value.url.startswith("blob:") and d.value.suggested_filename == "vlak4-rugsteun.json")
    original = r.state()
    page.evaluate("localStorage.clear()")
    page.reload()
    page.wait_for_selector("h1")
    r.ok("13 cleared storage starts clean at the rules screen", page.locator("h1").inner_text() == "Die reëls van die spel")
    r.btn("Ek verstaan, wys die eerste vraag").click()
    page.wait_for_selector(".tile")
    r.ok("13 after clearing, no ticks", page.locator(".tile.done").count() == 0)
    r.set_hash("#/meer")
    page.wait_for_selector("#restore-file", state="attached")
    fresh_raw = r.storage()
    page.set_input_files("#restore-file", str(backup))
    page.wait_for_selector(".modal")
    r.snap("restore-confirm")
    r.ok("13 restore asks first", "Dit vervang die vordering wat nou op hierdie tablet is. Gaan voort?" in page.locator(".modal").inner_text()
         and r.btn("Ja, laai terug").count() == 1 and r.btn("Kanselleer").count() == 1)
    r.btn("Kanselleer").click()
    page.wait_for_timeout(300)
    r.ok("13 Kanselleer changes nothing", r.storage() == fresh_raw)
    page.set_input_files("#restore-file", str(backup))
    r.btn("Ja, laai terug").click()
    page.wait_for_timeout(400)
    r.ok("13 good restore shows its line", "Rugsteun is teruggelaai." in r.body())
    restored = r.state()
    r.ok("13 every tick and every Terugkyk answer is back", restored["questions"] == original["questions"])
    r.set_hash("#/")
    page.wait_for_selector(".tile")
    r.ok("13 Tuis shows both ticks again", page.locator(".tile.done").count() == 2)

    # 14. wrong files
    r.set_hash("#/meer")
    page.wait_for_selector("#restore-file", state="attached")
    bad = [("bad-object.json", '{"hello": 1}'), ("bad-text.json", "not json at all"),
           ("bad-array.json", '{"version": 1, "questions": []}'), ("bad-list.json", "[1, 2]")]
    all_ok = True
    for name, body in bad:
        f = dl / name
        f.write_text(body, encoding="utf-8")
        before = r.storage()
        page.set_input_files("#restore-file", str(f))
        page.wait_for_timeout(400)
        good = "Hierdie lêer is nie 'n Vlak 4-rugsteun nie." in r.body() and page.locator(".modal").count() == 0 and r.storage() == before
        all_ok = all_ok and good
    r.snap("restore-wrong")
    r.ok("14 wrong file gives the wrong-file line and changes nothing", all_ok)

    # rules via Meer
    r.btn("Die reëls van die spel").click()
    page.wait_for_selector("ol.rules")
    r.snap("rules-again")
    r.ok("rules from Meer end with Terug", r.btn("Terug").count() >= 1 and r.btn("Ek verstaan, wys die eerste vraag").count() == 0)
    page.locator("main > .block").get_by_role("button", name="Terug").click()
    page.wait_for_timeout(400)
    r.ok("rules Terug goes back to Meer", r.hash() == "#/meer")

    # 16. walk every route and scan the text
    for h in ["#/", "#/vraag/1", "#/vraag/2", "#/kaart", "#/patrone", "#/meer", "#/reels"]:
        r.set_hash(h)
        page.wait_for_timeout(500)
        r.snap("walk " + h)
    found = []
    for screen, text in r.texts.items():
        for what, rx in FORBIDDEN:
            m = rx.search(text)
            if m:
                found.append(f"{screen}: {what} '{m.group(0)}'")
        cleaned = text.replace(APPROVED_PUNTE_LINE, "")
        if PUNTE.search(cleaned):
            found.append(f"{screen}: punte")
    r.ok(f"16 no date, day name, percent, 'punte', 'Goed gedaan', em-dash on {len(r.texts)} screens", not found, "; ".join(found[:5]))
    r.ok("16 note: 'punte' appears only inside approved rule 6 ('Geen punte nie.')",
         all(PUNTE.search(t) is None or APPROVED_PUNTE_LINE in t for t in r.texts.values()))

    # 17. layout
    r.ok("17 no horizontal scrolling on any screen", not r.layout_fail, "; ".join(r.layout_fail[:4]))
    r.ok("17 every button at least 48 px tall", not r.button_fail, "; ".join(r.button_fail[:4]))
    r.ok("body text at least 17 px everywhere", not r.font_fail, "; ".join(r.font_fail[:4]))
    col = page.evaluate("document.querySelector('main.view').getBoundingClientRect().width")
    r.ok("content column at most 860 px", col <= 860.5, str(col))

    # no outside requests except fonts, no service worker, no page errors
    outside = sorted(h for h in hosts if h not in ("localhost", "127.0.0.1", "fonts.googleapis.com", "fonts.gstatic.com", "blob", "data"))
    r.ok("no outside requests except the fonts", not outside, str(outside))
    r.ok("no service worker registered", page.evaluate("navigator.serviceWorker ? navigator.serviceWorker.getRegistrations().then(x => x.length) : 0") == 0)
    r.ok("no JavaScript errors during the play-through", not errors, "; ".join(errors[:3]))
    ctx.close()


def corrupt_storage(browser):
    label = "storage"
    ctx = browser.new_context(viewport={"width": 800, "height": 1280})
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(T)
    page.wait_for_selector("h1")
    for val in ["{not json", "null", "[]", '"text"', '{"version":1,"questions":[]}', '{"version":2,"questions":{}}',
                '{"version":1,"rulesSeen":true,"questions":{"1":"x","abc":{}}}']:
        page.evaluate(f"localStorage.setItem('vlak4.v1', {json.dumps(val)}); history.replaceState(null, '', '/?toets=1#/')")
        page.reload()
        page.wait_for_selector("h1")
        h1 = page.locator("h1").inner_text()
        if val.startswith('{"version":1,"rulesSeen":true'):
            ok = h1 == "Vlak 4 Brain Training" and page.locator(".tile.done").count() == 0
        else:
            ok = h1 == "Die reëls van die spel"
        check(label, f"corrupt storage {val[:32]!r} starts clean without a crash", ok and not errors, h1 + " " + "; ".join(errors))
    # all 20 finished: the end line replaces the line under the heading
    done = {str(n): {"beganAt": 1, "hintsOpenedAt": [], "routeOpenedAt": 2, "routeVia": "antwoord",
                     "terugkyk": {"withinTwoMinutes": True, "move": 1, "stuck": "begin"}, "closedAt": 3} for n in range(1, 21)}
    page.evaluate(f"localStorage.setItem('vlak4.v1', {json.dumps(json.dumps({'version': 1, 'rulesSeen': True, 'questions': done}))}); history.replaceState(null, '', '/?toets=1#/')")
    page.reload()
    page.wait_for_selector(".tile")
    head = page.locator(".home-head").inner_text()
    check(label, "all 20 finished: end line shows, no current tile",
          "Al 20 vrae is toe. Jou patrone staan onder My patrone." in head and "Een vraag op 'n slag." not in head
          and page.locator(".tile.done").count() == 20 and page.locator(".tile.current").count() == 0, head)
    ctx.close()


def pure_functions(browser):
    label = "unit"
    ctx = browser.new_context()
    page = ctx.new_page()
    page.goto(BASE)
    res = page.evaluate("""async () => {
      const c = await import('/js/clock.js');
      const s = await import('/js/stats.js');
      const out = {};
      out.speed = [c.speedFactor('localhost','?toets=1'), c.speedFactor('127.0.0.1','?toets=1'),
                   c.speedFactor('vlak4.netlify.app','?toets=1'), c.speedFactor('example.com','?toets=1'),
                   c.speedFactor('192.168.1.5','?toets=1'), c.speedFactor('localhost',''), c.speedFactor('localhost','?toets=0')];
      const meta = {hints: 3, struggleMinutes: 10};
      const M = 60000, b = 1000000;
      out.notStarted = c.status(meta, null, b, 1);
      out.early = c.status(meta, {beganAt: b, hintsOpenedAt: []}, b + 3*M, 1);
      out.due = c.status(meta, {beganAt: b, hintsOpenedAt: []}, b + 10*M, 1);
      out.second = c.status(meta, {beganAt: b, hintsOpenedAt: [b + 12*M]}, b + 14*M, 1);
      out.done = c.status(meta, {beganAt: b, hintsOpenedAt: [1,2,3]}, b + 40*M, 1);
      out.zero = c.status({hints: 0, struggleMinutes: 20}, {beganAt: b, hintsOpenedAt: []}, b + 19*M, 1);
      out.zeroDue = c.status({hints: 0, struggleMinutes: 20}, {beganAt: b, hintsOpenedAt: []}, b + 20*M, 1);
      out.fmt = [c.formatCountdown(581), c.formatCountdown(0), c.formatCountdown(299)];
      const qs = {
        '1': {beganAt: 0, hintsOpenedAt: [1, 2], routeOpenedAt: 90*M, closedAt: 1, terugkyk: {withinTwoMinutes: true, move: 3, stuck: 'begin'}},
        '2': {beganAt: 0, hintsOpenedAt: [], routeOpenedAt: 20*M, closedAt: 1, terugkyk: {withinTwoMinutes: false, move: 0, stuck: 'einde'}},
        '3': {beganAt: 0, hintsOpenedAt: [5], routeOpenedAt: 5*M},
      };
      const metas = {'1': {paper: 'I', tags: {topic: 'Calculus', kind: 'N'}}, '2': {paper: 'I', tags: {topic: 'Calculus', kind: 'A'}}};
      out.stats = s.compute(qs, metas, M);
      return out;
    }""")
    check(label, "?toets=1 only speeds up on localhost and 127.0.0.1", res["speed"] == [60, 60, 1, 1, 1, 1, 1], str(res["speed"]))
    check(label, "clock: not started has no countdown", res["notStarted"]["started"] is False and res["notStarted"]["next"] is None)
    check(label, "clock: Wenk 1 counts down from the struggle time", res["early"]["next"]["ready"] is False and res["early"]["next"]["shownSeconds"] == 420 and not res["early"]["canStruggleOut"])
    check(label, "clock: Wenk 1 ready at the struggle time", res["due"]["next"]["ready"] is True and res["due"]["canStruggleOut"])
    check(label, "clock: next hint 5 minutes after the last one was opened", res["second"]["next"]["index"] == 1 and res["second"]["next"]["shownSeconds"] == 180)
    check(label, "clock: no countdown after the last hint", res["done"]["next"] is None and res["done"]["opened"] == 3)
    check(label, "clock: 0 hints, struggle button only after 20 minutes", res["zero"]["next"] is None and not res["zero"]["canStruggleOut"] and res["zeroDue"]["canStruggleOut"])
    check(label, "clock: countdown format", res["fmt"] == ["09:41", "00:00", "04:59"], str(res["fmt"]))
    st = res["stats"]
    check(label, "stats: counts finished questions only", st["closed"] == 2 and st["within"] == 1)
    check(label, "stats: stuck counts and moves (Geen not listed)", st["stuck"] == {"begin": 1, "middel": 0, "einde": 1, "nerens": 0} and st["moves"] == [{"move": 3, "count": 1}])
    topic = st["tables"]["topic"]
    check(label, "stats: sukkeltyd capped at 60 minutes per question", topic == [{"name": "Calculus", "count": 2, "hints": 2, "avg": {"minutes": 40, "capped": False}}], json.dumps(topic))
    ctx.close()


def host_gate_live(pw):
    """Open the app on a non-local name that points at this machine: ?toets=1 must do nothing there."""
    browser = pw.chromium.launch(headless=True, args=["--host-resolver-rules=MAP vlak4-live.test 127.0.0.1"])
    page = browser.new_page()
    page.goto(f"http://vlak4-live.test:{PORT}/?toets=1")
    page.get_by_role("button", name="Ek verstaan, wys die eerste vraag", exact=True).click()
    page.locator(".tile.current").get_by_role("button", name="Maak oop").click()
    page.get_by_role("button", name="Begin", exact=True).click()
    page.wait_for_selector(".countdown")
    t = page.locator(".countdown").inner_text()
    page.wait_for_timeout(2500)
    t2 = page.locator(".countdown").inner_text()
    secs = lambda x: int(x.split(":")[0]) * 60 + int(x.split(":")[1])
    check("host", "?toets=1 does nothing on a non-local host (real clock speed)",
          secs(t) >= 598 and secs(t) - secs(t2) <= 4, f"{t} then {t2}")
    browser.close()


def static_checks():
    label = "files"
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    check(label, "index.html: noindex, lang af, manifest, the three fonts",
          '<meta name="robots" content="noindex">' in html and '<html lang="af">' in html and 'rel="manifest"' in html
          and all(f in html for f in ("Space+Grotesk", "Sora", "JetBrains+Mono")))
    check(label, "index.html: zoom allowed", "user-scalable" not in html and "maximum-scale" not in html)
    man = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    check(label, "manifest icons 192 and 512 exist", all((ROOT / i["src"]).exists() for i in man["icons"]) and {i["sizes"] for i in man["icons"]} == {"192x192", "512x512"})
    texts = [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and p.suffix in (".html", ".css", ".js", ".json", ".md", ".py")]
    dash = [str(p.relative_to(ROOT)) for p in texts if "\u2014" in p.read_text(encoding="utf-8")]
    check(label, "no em-dash in any file", not dash, str(dash))
    email = re.compile(r"[\w.]+@[\w-]+\.[\w.]+")
    phone = re.compile(r"(\+27|\b0[6-8]\d)[ -]?\d{3}[ -]?\d{4}\b")
    hits = [str(p.relative_to(ROOT)) for p in texts if email.search(p.read_text(encoding="utf-8")) or phone.search(p.read_text(encoding="utf-8"))]
    check(label, "no email or phone number in any file", not hits, str(hits))
    sw = [str(p.relative_to(ROOT)) for p in texts if "tools" not in p.parts and "serviceWorker.register" in p.read_text(encoding="utf-8")]
    check(label, "no service worker in the code", not sw, str(sw))
    js = "".join((ROOT / "js" / f).read_text(encoding="utf-8") for f in ("clock.js", "stats.js"))
    check(label, "clock.js and stats.js have no DOM or storage code",
          not re.search(r"\bdocument\b|\bwindow\b|localStorage|querySelector", js))
    app = (ROOT / "js" / "app.js").read_text(encoding="utf-8")
    check(label, "only store.js touches localStorage",
          "localStorage" not in app and "localStorage" not in (ROOT / "js" / "strings.js").read_text(encoding="utf-8"))


def main():
    srv = serve()
    print(f"serving {ROOT} on {BASE}; downloads go to {OUT}", flush=True)
    static_checks()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        pure_functions(browser)
        corrupt_storage(browser)
        for w, hgt in ((800, 1280), (1280, 800)):
            play(browser, w, hgt)
        browser.close()
        host_gate_live(pw)
    srv.shutdown()
    passed = sum(RESULTS)
    print(f"\n{passed} of {len(RESULTS)} checks passed", flush=True)
    sys.exit(0 if passed == len(RESULTS) else 1)


if __name__ == "__main__":
    main()
