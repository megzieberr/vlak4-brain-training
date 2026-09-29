# Vlak 4 Brain Training

A small private web app for one Grade 12 learner on a Samsung tablet (Android, Chrome).
Afrikaans on screen. It shows 20 questions one after the other: it opens the next question,
keeps the hints locked until she has struggled long enough, shows the route and the solution
when she asks, and shows her own patterns back to her. It never marks, never scores and never
looks at the calendar. She works on paper or in Samsung Notes, never in the app.

The full brief is `APP-SPEC.md` in the Vlak 4 folder under Tutoring Resources. This repo is the
shell only; right now it holds two DUMMY questions (v01 and v02) with placeholder pictures.

Plain HTML, CSS and JavaScript (ES modules). No framework, no build step, no service worker,
no login, no database.

## Run it locally

```
cd vlak4-brain-training
python -m http.server 5230
```

Then open `http://localhost:5230/` in Chrome.

### Test speed: `?toets=1`

`http://localhost:5230/?toets=1` makes one minute last one second, so a 10 minute hint wait
takes 10 seconds. It only works when the host is `localhost` or `127.0.0.1`. On any other host
(the live link) the switch does nothing.

### The automatic check

```
python tools/verify_shell.py <a temp folder for test downloads>
```

It serves the repo on port 5230 by itself, plays the app through with Playwright's own
headless Chromium at 800 x 1280 and 1280 x 800, and prints PASS or FAIL per check. It reads the
page text and structure only, no screenshots.

## Files

```
index.html
css/styles.css
js/app.js        screens and navigation (hash routes)
js/strings.js    every Afrikaans line on screen, in one place
js/store.js      everything that reads or writes the tablet's storage
js/clock.js      hint timing, pure functions
js/stats.js      the My patrone numbers, pure functions
content/index.json
content/v01/ ... v20/
manifest.json, icons/
tools/make_dummies.py   makes the dummy pictures, werkblad PDFs and icons
tools/verify_shell.py   the automatic check
```

## Adding a batch of questions

1. Drop the new folders into `content/` (for example `content/v03/` to `content/v05/`). Each
   folder holds `vraag.json`, the pictures and `werkblad-vNN.pdf`, as in spec section 5.3.
2. Add the numbers to `published` in `content/index.json`, and raise `contentVersion` by one
   so the tablet fetches fresh files.
3. The shell itself is not touched. Hint count and struggle minutes come from each
   question's `vraag.json`.

When batch 1 lands, the real Vraag 1 and 2 replace the dummy `v01` and `v02` folders.

## Wording

Every on-screen line lives in `js/strings.js`. The wording was approved as written; change a
line only after it has been approved again.

## Storage

One `localStorage` key: `vlak4.v1` (shape in spec section 5.5). Every read and write goes
through `js/store.js`. Empty or broken storage starts clean at the rules screen.

The backup and patterns file is `vlak4-rugsteun.json`: the storage object plus, for each
finished question, a copy of its tags. It is saved through a `blob:` link. Restoring checks the
file first and asks before it replaces anything.
