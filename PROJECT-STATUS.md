# Vlak 4 Brain Training: project status

## Where we are

- The shell is built from `APP-SPEC.md` with two DUMMY questions (v01: 3 hints, 10 minutes;
  v02: 0 hints, 20 minutes). No real question, hint or route is in this repo.
- `tools/verify_shell.py` plays it through headless at 800 x 1280 and 1280 x 800 and passes.
- **NOT online.** No GitHub repo yet, no Netlify site yet. Local git only, no remote.

## Decisions taken while building

- Every screen except Tuis, the card and the rules has a `Terug` button at the top left
  (the spec's own word). The question screens (Vraag, Die roete, Terugkyk) also carry the
  `Vasgevang-kaart` link at the top right.
- `Ek verstaan, wys die eerste vraag` lands on Tuis with Vraag 1 glowing.
- The werkblad button stays on the question after Begin.
- The Meer screen uses `Meer` as its heading.
- The closing line (`Vraag N is toe. Vraag M is oop.`) shows only when the next question is
  published; after Vraag 20 it does not show.
- My patrone: Geen is left out of `Wat maak vrae vir my oop`; the share and save buttons show
  only once a question is finished; average sukkeltyd shows as whole minutes (`14 min`), or
  `60+ min` at the cap.
- The full-screen picture closes with `Terug` or the tablet's back button.
- Dummy `subtopic` is `dummy`.

## Open questions for Megan

- Rule 6 (`Geen punte nie. ...`) contains the word "punte", while spec 7.16 says "punte" must
  not appear on any screen. The rule is kept word for word; the check allows that one line.

## Next

1. Checker play-through on a real tablet size (fresh session).
2. Content batch 1: replace v01 and v02 with the real Vraag 1 and 2, add the rest of the batch,
   update `content/index.json`.
3. Ship: private GitHub repo and Netlify, only after Megan says so.
