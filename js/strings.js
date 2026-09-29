// Every Afrikaans line that shows on screen lives here, so wording can be changed in one place.
// Source: APP-SPEC.md section 4 (approved wording) and VLAK4-PLAN.md (the card and the rules).
// Change a line here only after it has been approved.

export const S = {
  // 4.1 Tuis
  appTitle: 'Vlak 4 Brain Training',
  tagline: "Een vraag op 'n slag.",
  allDone: 'Al 20 vrae is toe. Jou patrone staan onder My patrone.',
  vraag: (n) => `Vraag ${n}`,
  maakOop: 'Maak oop',
  notHereYet: (n) => `Vraag ${n} is nog nie hier nie. Dit kom binnekort.`,
  footCard: 'Vasgevang-kaart',
  footPatrone: 'My patrone',
  footMeer: 'Meer',
  rulesAccept: 'Ek verstaan, wys die eerste vraag',
  closedToast: (n, m) => `Vraag ${n} is toe. Vraag ${m} is oop.`,

  // 4.2 Vraag, before Begin
  werkbladBtn: 'Laai die werkblad af',
  werkbladLine: 'Maak die werkblad in Samsung Notes oop en werk daar.',
  begin: 'Begin',
  beginLine: 'Die wenke se horlosie begin loop wanneer jy Begin tik, en loop aan terwyl jy skryf.',
  cardLink: 'Vasgevang-kaart',

  // 4.3 Vraag, after Begin
  twoMinutes: 'Skryf iets neer binne 2 minute, al is dit verkeerd.',
  hintLocked: (i) => `Wenk ${i} maak oop oor `, // followed by the countdown
  hintReady: (i) => `Wys Wenk ${i}`,
  hintHeading: (i) => `Wenk ${i}`,
  noHints: 'Hierdie vraag het geen wenke nie. Die Vasgevang-kaart is altyd hier.',
  haveAnswer: "Ek het 'n antwoord",
  struggledEnough: 'Ek het genoeg gesukkel',
  confirmTitle: 'Maak die roete oop?',
  confirmLine: 'Daarna kan jy dit nie weer toemaak vir hierdie vraag nie.',
  confirmYes: 'Ja, wys die roete',
  confirmNo: 'Nog nie',

  // 4.4 Die roete
  routeHeading: 'Die roete',
  solutionHeading: 'Die oplossing',
  openedByHeading: 'Wat het dit oopgemaak',
  stryHeading: 'Stry met juffrou',
  whatsapp: 'Stuur op WhatsApp',
  whatsappLine: 'Jy kies self vir wie jy dit stuur. Jy hoef nie.',
  toTerugkyk: 'Gaan na Terugkyk',
  whatsappMessage: (n, stry) => `Vraag ${n}, Stry met juffrou: ${stry}\n\nEk dink:`,

  // 4.5 Terugkyk
  terugkyk: 'Terugkyk',
  tkWithin: 'Het ek binne 2 minute iets neergeskryf?',
  ja: 'Ja',
  nee: 'Nee',
  tkMove: 'Watter kaart-stap het dit oopgemaak?',
  geen: 'Geen',
  tkStuck: 'Waar het ek vasgehaak?',
  stuckNames: { begin: 'Begin', middel: 'Middel', einde: 'Einde', nerens: 'Nêrens' },
  tkSave: 'Stoor en maak toe',
  moveNames: {
    1: 'Skryf in simbole',
    2: 'Teken dit groter',
    3: "Probeer 'n regte getal",
    4: 'Werk terugwaarts',
    5: 'Wat sou dit maklik maak?',
    6: 'Soek die versteekte ding',
    7: 'Gebruik die "wys dat"',
    8: "Skryf 'n argument",
  },

  // 4.6 Vasgevang-kaart (moves word for word from VLAK4-PLAN.md; bold on the move names)
  cardHeading: 'Vasgevang-kaart',
  cardIntro: 'Agt stappe, in hierdie volgorde, voordat jy mag sê "ek weet nie".',
  cardMovesHtml: [
    "<strong>Skryf neer wat jy weet, in simbole.</strong> Elke gegewe word 'n vergelyking of 'n etiket.",
    '<strong>Teken dit, of teken dit oor, groter.</strong> Sit elke gegewe op die figuur.',
    "<strong>Probeer 'n regte getal.</strong> As daar 'n <em>k</em> of 'n <em>t</em> is, kies 2 en kyk wat gebeur.",
    '<strong>Werk terugwaarts.</strong> Wat vra hulle? Wat sou ek nodig hê om DIT te kry?',
    '<strong>Vra: wat sou dit maklik maak?</strong> Watter feit ontbreek? Waar kom dit vandaan?',
    "<strong>Soek die versteekte ding.</strong> 360° in 'n sirkel, 30° per uur, 'n hoek van 90° wat nie geteken is nie, die woord \"raaklyn\".",
    "<strong>Gebruik die \"wys dat\".</strong> 'n \"Wys dat\"-antwoord is gegee. Gebruik dit al kon jy dit nie bewys nie, en gaan aan.",
    "<strong>Skryf 'n argument.</strong> As daar geen berekening is nie, skryf 'n sin met 'n rede. Die IEB betaal daarvoor.",
  ],
  cardFoot: "Sukkel is nie 'n teken dat die vraag stukkend is nie. Dit is die oefening.",
  terug: 'Terug',

  // 4.7 Die reëls van die spel (word for word from VLAK4-PLAN.md)
  rulesHeading: 'Die reëls van die spel',
  rulesHtml: [
    "Een vraag op 'n slag. Die volgende een maak oop wanneer hierdie een toe is. Slaan 'n dag oor of doen twee op 'n goeie dag: jou keuse.",
    "Skryf iets binne 2 minute, al is dit verkeerd. 'n Leë bladsy is die enigste manier om te misluk.",
    'Sukkel eers eerlik. Die Wenk-knoppie maak vanself oop wanneer die tyd om is.',
    'Die roete is vir NÁ jou poging. Lees die roete, nie net die antwoord nie.',
    'Elke vraag het een "Stry met juffrou". Jy mag dit WhatsApp. Jy hoef nie.',
    'Geen punte nie. Die app hou net boek van jou patrone, vir jou.',
  ],

  // 4.8 read again
  myTerugkyk: 'My terugkyk',

  // 4.9 My patrone
  patroneHeading: 'My patrone',
  patroneEmpty: 'Hier is nog niks nie. Jou patrone verskyn sodra jou eerste vraag toe is.',
  blkClosed: 'Vrae toe',
  blkFirst2: 'Die eerste 2 minute',
  first2Line: (k, n) => `Iets op papier binne 2 minute: ${k} uit ${n} vrae`,
  blkStuck: 'Waar ek vashaak',
  blkOpened: 'Wat maak vrae vir my oop',
  blkHints: 'Wenke en sukkeltyd',
  tblTopic: 'Per onderwerp',
  tblPaper: 'Per vraestel',
  tblKind: 'Per soort vraag',
  colVrae: 'Vrae',
  colWenke: 'Wenke oopgemaak',
  colTyd: 'Gemiddelde sukkeltyd',
  minutes: (m) => `${m} min`,
  cappedMinutes: '60+ min',
  paperNames: { I: 'Vraestel I', II: 'Vraestel II' },
  kindNames: { N: 'Groot vraag', S: 'Vreemd gevra', P: 'Raaisel', A: 'Redeneer dit' },
  topics: [
    'Rye en reekse', 'Finansies', 'Funksies en inverses', 'Calculus', 'Waarskynlikheid',
    'Statistiek', 'Analitiese meetkunde', 'Trigonometrie', 'Euklidiese meetkunde',
  ],
  sharePatrone: 'Stuur my patrone',
  savePatrone: "Stoor my patrone as 'n lêer",
  onlyYou: 'Net jy besluit of jy dit stuur.',

  // 4.10 Meer
  meerHeading: 'Meer',
  rulesLink: 'Die reëls van die spel',
  backupHeading: 'Rugsteun',
  backupExplain: "Jou vordering bly net op hierdie tablet. 'n Rugsteun is 'n klein lêer wat jy kan bêre, sodat niks verlore gaan as die tablet skoongemaak word nie.",
  backupSave: "Stoor 'n rugsteun",
  backupLoad: "Laai 'n rugsteun terug",
  restoreConfirm: 'Dit vervang die vordering wat nou op hierdie tablet is. Gaan voort?',
  restoreYes: 'Ja, laai terug',
  restoreNo: 'Kanselleer',
  restoreOk: 'Rugsteun is teruggelaai.',
  restoreBad: 'Hierdie lêer is nie \'n Vlak 4-rugsteun nie.',

  // 4.11 errors
  imgFail: 'Die prent wou nie laai nie. Kyk of jy internet het en probeer weer.',
  retry: 'Probeer weer',
  werkbladFail: 'Die werkblad wou nie aflaai nie. Probeer weer.',
};
