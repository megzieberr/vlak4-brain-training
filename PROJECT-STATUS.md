# Vlak 4 Brain Training: project status

## Where we are

- The shell is built from `APP-SPEC.md`. **`content\v01` is the REAL Vraag 1 since 2026-09-29**
  (exported by `_sjabloon\export_content.py` in the content folder, not yet read by Megan, NOT
  committed). `content\v02` is still a dummy (0 hints, 20 minutes).
- Hint, route and solution pictures of a real question carry random file names, listed in its
  `vraag.json`. Never rename them by hand: re-run the export.
- `tools/verify_shell.py` plays it through headless at 800 x 1280 and 1280 x 800 and passes
  (392 of 392 with the real Vraag 1). Since 2026-09-29 it reads what it expects of Vraag 1 and 2
  from their own `vraag.json`, so it keeps working as dummies are replaced.
- Checker play-through done 2026-09-29 (`CHECK-SHELL-2026-09-29.md`). Fix round 1 done the same day:
  Tuis tiles in reading order with a joining line, a fixed action bar on the Vraag screen, Begin
  waits for the question picture, Terugkyk taps survive a trip to the card (draft in
  sessionStorage, never in `vlak4.v1`), back closes only the confirm box or the picture, and the
  small looks (heading gap, lit Terugkyk choice, aligned tables, Roman numeral in JetBrains Mono).
  The verify script now has fix1 to fix6 checks and a tall-picture test; all pass.
- **NOT online.** PRIVATE GitHub repo megzieberr/vlak4-brain-training since 2026-09-29 (branch master). No Netlify site, no GitHub Pages.

## Decisions taken while building

- Every screen except Tuis, the card and the rules has a `Terug` button at the top left
  (the spec's own word). The question screens (Vraag, Die roete, Terugkyk) also carry the
  `Vasgevang-kaart` link at the top right.
- `Ek verstaan, wys die eerste vraag` lands on Tuis with Vraag 1 glowing.
- The werkblad button sits in the action bar before Begin and moves back into the page, under the
  question picture, after Begin.
- The Meer screen uses `Meer` as its heading.
- The closing line (`Vraag N is toe. Vraag M is oop.`) shows only when the next question is
  published; after Vraag 20 it does not show.
- My patrone: Geen is left out of `Wat maak vrae vir my oop`; the share and save buttons show
  only once a question is finished; average sukkeltyd shows as whole minutes (`14 min`), or
  `60+ min` at the cap.
- The full-screen picture closes with `Terug` or the tablet's back button.
- Dummy `subtopic` is `dummy`.
- Tuis: 4 columns upright, 5 sideways. The joining line is lit in `--accent` up to the current
  tile and `--brd-2` after it. Sideways, row 4 can sit under the foot bar at the top of the page
  when the closing line or a "nog nie hier nie" tile makes the page taller; scrolling shows it.
- Hover looks only apply on devices with a real pointer, so a tapped button never keeps them.

## Open questions for Megan

- Rule 6 (`Geen punte nie. ...`) contains the word "punte", while spec 7.16 says "punte" must
  not appear on any screen. The rule is kept word for word; the check allows that one line.

## Next

1. Content batch 1: replace v01 and v02 with the real Vraag 1 and 2, add the rest of the batch,
   update `content/index.json`.
2. Ship: private GitHub repo and Netlify, only after Megan says so. Still NOT online.
