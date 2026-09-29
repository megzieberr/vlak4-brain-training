# Shell check, 2026-09-29 (fresh-eyes checker)

## 1. What I played

The full learner walk (rules, Tuis, Vraag 1 with 3 hints, route, Terugkyk, Vraag 2 with no hints, Vraag 3 not here yet, My patrone, Meer, backup, clear, restore, wrong file, read-again, back button from each screen) plus cheating tries and extra probes (no internet, all 20 finished, tablet clock moved forward).
Playwright's own headless Chromium, touch on, mobile context, scale factor 2, `?toets=1`, served on port 5231, at 800 x 1280 (upright) and 1280 x 800 (sideways).
Screenshots, scripts and downloads are in the session scratchpad under `checker\`. No app file was changed.

## 2. Defects, worst first

No BLOCKER found. All ten hard rules in section 2 held on every screen at both sizes: no date, day name, percent sign, score, streak, praise, em-dash or level label; no red or green; the only clock is the hint countdown; the only outside requests were the Google fonts.

1. **SHOULD FIX. Tuis, both sizes. The path of 20 is hard to read as a path.** The tiles are a plain 4 x 5 grid with no line joining them. Rows 2 and 4 run right to left, so reading the screen normally gives 1 2 3 4 / 8 7 6 5 / 9 10 11 12 / 16 15 14 13. Nothing on screen shows the snake (spec 4.1 says "a path of 20 tiles, in order, snaking down the screen"). She will find the glowing tile, but the order looks jumbled. Sure: medium to high.
2. **SHOULD FIX. Vraag after Begin, sideways (1280 x 800).** Even with the short dummy picture, the hint button `Wenk 1 maak oop oor 08:59` starts at 766 px of an 800 px screen, so it shows half cut off at the bottom. `Ek het 'n antwoord` is out of sight. Nothing tells her to scroll. Real pictures (spec 5.4 allows up to about 1240 px tall on screen) will push the countdown, the buttons and even `Begin` below the fold upright too. Sure: high for sideways with the dummy; medium for how bad it gets with real pictures.
3. **NOTE. Hint gate, both sizes. Moving the tablet clock forward opens the hints.** With the real clock (no toets), I tapped Begin (`Wenk 1 maak oop oor 10:00`), moved the system time one hour ahead and reloaded. `Wys Wenk 1` and `Ek het genoeg gesukkel` were both there at once. This follows spec 4.3 ("plain time since the Begin tap, saved on the tablet"), so it is a limit of the design, not a build mistake. The teacher decides whether it matters. Sure: high.
4. **NOTE. Terugkyk, both sizes. Taps are lost after a trip to the card.** I tapped `Ja` and `Geen`, opened `Vasgevang-kaart` from the top bar, tapped `Terug`: all three groups were empty again and `Stoor en maak toe` dimmed. Small, but she has to re-tap. Sure: high.
5. **NOTE. Vraag, both sizes. The tablet back button while the confirm box is open leaves the question.** Back with `Maak die roete oop?` showing closes the box AND goes to Tuis. Nothing is opened or lost (the route stays closed, the clock keeps running), but she may expect back to close only the box. Sure: high.
6. **NOTE. Tuis after saving, both sizes. Back opens the question she just closed.** After `Stoor en maak toe` she lands on Tuis; the back button then opens that question in read-again mode. Harmless, a little odd. Sure: high.
7. **NOTE. Vraag with no internet, upright.** When the question picture fails, the error card and `Probeer weer` show (spec 4.11 wording correct, and `Probeer weer` does reload the picture once the internet is back), but `Begin` is still there, so she can start the clock without seeing the question. Sure: high.
8. **NOTE. Tuis, sideways.** At the top of the page the fixed foot bar covers the lower half of tiles 17 to 20. Scrolling down shows them fully. Sure: high.
9. **NOTE. Look, all screens.** It reads as dark navy with thin electric-blue borders and the faint grid, and every picture sits on a white card with a blue border. The "glassy panels" are thin, though: only My patrone, the confirm box and the buttons have panels; the rules, the card, Meer, the question and route screens put text straight on the background. Sure: medium (a judgement of look).
10. **NOTE. Every screen with a top bar, both sizes.** The page heading (`Vraag 1`, `My patrone`, `Meer`, `Terugkyk`) sits only 6 px under the `Terug` button and looks cramped. Sure: high that the gap is 6 px; low on how much it matters.
11. **NOTE. My patrone, both sizes.** The three small tables each size their own columns, so `Vrae`, `Wenke oopgemaak` and `Gemiddelde sukkeltyd` jump sideways from table to table. In the Sora font the capital I looks like a small l, so `Vraestel II` can read as "Vraestel ll". Sure: high that it looks this way; low on importance.
12. **NOTE. Terugkyk, upright.** The chosen button is only a little brighter than the others (blue fill and blue ring, no other mark). The last button tapped also shows the hover colour, which looks different from the other chosen buttons. Visible, but subtle. Sure: medium.
13. **NOTE for the teacher, not a build defect. Spec 7 check 16 clashes with approved wording.** Check 16 says "punte" must be absent outside a question picture, but approved rule 6 on the rules screen is `Geen punte nie. Die app hou net boek van jou patrone, vir jou.` Rule 1 also contains "dag" (`Slaan 'n dag oor ...`), which is not a day name. The build follows the approved wording, which is right.

## 3. Visible text that is not in the spec

- `Terug` as a top-left button on: Vraag (before and after Begin), Die roete, Terugkyk, My patrone (empty and filled), Meer, the read-again screen, and the full-screen picture. Spec 4 lists `Terug` only on the Vasgevang-kaart (4.6) and the rules screen (4.7).
- `Meer` as the page heading on the Meer screen (4.10 lists no heading).
- `Vraag 1` as the page heading on Die roete (4.4 lists only its five section headings).
- `Vasgevang-kaart` link on the Terugkyk screen (4.2 puts it on "every question screen"; the Terugkyk is not listed). Also on Die roete, which arguably counts as a question screen.
- `min` after each average in the three tables (for example `26 min`). Spec only shows `60+ min`, so this is the natural reading, listed for completeness.
- The dummy texts `DUMMY: dit is 'n toetsvraag sonder inhoud.` (Stry line) and `Kaart-stap 1: Skryf in simbole.` (Vraag 2's opened-by line, shorter than move 1 in the plan). Both come from the dummy data files, not the shell, and go when the real questions land.

No spec line was missing or altered. Every line in 4.1 to 4.11 showed character for character, including `Al 20 vrae is toe. Jou patrone staan onder My patrone.` (seen by seeding 20 finished questions), the toast `Vraag 1 is toe. Vraag 2 is oop.` (gone after 5 s), both error lines of 4.11, the restore lines, the card moves and the six rules. After Vraag 2 no toast shows, because Vraag 3 is not published; I think that is the sensible reading.

## 4. Cheating attempts and what happened

- Typed `#/roete/1` and `#/terugkyk/1` before Begin and again after Begin (route not opened): both sent back to `#/vraag/1`. Gate held.
- Typed `#/vraag/2`, `#/vraag/3`, `#/roete/2`, `#/vraag/0` while Vraag 1 was current: all sent to Tuis. `#/vraag/01` shows Vraag 1 (harmless).
- Tapping a locked tile: nothing happens.
- Back button after `Ja, wys die roete`: goes to Tuis; the route stays open (no way to "unopen" it), `Maak oop` then goes straight to Die roete. After `Nog nie`, nothing was saved (`routeOpenedAt` stayed empty).
- Reload mid-countdown: the countdown carries on from the right place (05:21 before, 04:08 after about 1.2 s at toets speed).
- Leaving for the card and coming back: the countdown kept running.
- Second tab on `#/vraag/1`: shows the same countdown as the first tab. No reset.
- Clearing storage: the app starts clean at the rules screen, all ticks gone (so it is a loss, not a cheat).
- Moving the tablet clock forward: WORKS as a cheat (defect 3).
- A backup file edited by hand (for example an old `beganAt`) would also unlock hints on restore. Not tried by hand; follows from the same design. Hard for her to do on a tablet.
- Direct URLs (expected on a static site): `content/v01/wenk-1.png`, `roete-1.png`, `oplossing-1.png`, `vraag.json`, `content/v02/roete-1.png`, `content/index.json` and even the folder listing `content/` all answered 200 on the local server (Netlify will not list folders). How guessable: very. The werkblad download is named `werkblad-v01.pdf`, and a long press on the question picture in Chrome most likely offers "open image in new tab", which shows `content/v01/vraag-1.png?v=1`; changing `vraag` to `oplossing` or `roete` gives the answer. `vraag.json` for any published question also shows its topic, paper, marks and kind before she reaches it.

## 5. What I could NOT check

- A real Samsung tablet: real touch, pinch-zoom in the full-screen picture, Chrome's own long-press menu, sticky hover after a tap, the home-screen icon.
- The Android share sheet for `Stuur my patrone` (headless Chromium has no share, so it fell back to a download of `vlak4-rugsteun.json`, as the spec says it should).
- Opening WhatsApp (checked the link only: `https://wa.me/?text=` with no number, message `Vraag 1, Stry met juffrou: <stry>` then a blank line and `Ek dink:`, opens in a new tab).
- Real question pictures (only the dummies exist), so the fold problem in defect 2 is judged from the spec's picture sizes.
- The live Netlify host (that `?toets=1` does nothing there).

No defect found on: the ten hard rules, horizontal scroll (none at either size), button size (every button 48 px or more), text size (nothing under 17 px), the confirm box (centred over a dimmed page at both sizes), the full-screen picture (clear `Terug`, and the back button closes it), the countdown and hint ladder (10 min, then 5 min after each opening), `Ek het genoeg gesukkel` appearing only at the struggle time, the Terugkyk save button staying dimmed until all three are answered, ticks kept after reload, the no-hints line on Vraag 2, Vraag 3's "nog nie hier nie" tile, My patrone (finished questions only, no totals out of 20, one blue colour, empty-state line), backup, restore with `Kanselleer` and `Ja, laai terug`, wrong file and non-JSON file (line shown, nothing changed), read-again mode (everything open, `My terugkyk` answers as plain text).
