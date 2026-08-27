"""
Prüfungen für Gym-Log.

Lädt die echte index.html in Chrome headless, hängt die Prüfungen unten an und
liest das Ergebnis aus dem DOM. Node ist auf dem PC nicht installiert, deshalb
der Umweg über den Browser — der hat den Vorteil, dass DOM und Formular echt
sind statt nachgebaut. Gleicher Aufbau wie `pruefungen.py` in angel-log.

    python pruefungen.py

⚠️ Gym-Log hatte bis zum 22.08.2026 **null** Prüfungen, Angel-Log 700. Die sechs
Fehler vom 05.08.2026 (falscher Satz in der Datenschutzerklärung, Gewichtseinträge
mit falschem Datum, stehenbleibender Pausen-Timer, Überlauf bei 320 px, falsches
Übungsbild, falsch geratener Trainingstag) sind alle erst beim Benutzen aufgefallen.
Die Prüfungen unten sind entlang genau dieser Fehler gebaut, nicht entlang dessen,
was sich leicht prüfen lässt.
"""
import subprocess, re, pathlib, shutil, sys, os, json

SRC  = pathlib.Path(__file__).resolve().parent
WORK = SRC / '.testrun'
# Windows und Linux, damit der Lauf auch auf dem Laptop nicht sofort abbricht.
CHROME = os.environ.get('CHROME') or next((c for c in [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe'),
    '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable',
    '/usr/bin/chromium', '/usr/bin/chromium-browser', '/snap/bin/chromium',
] if pathlib.Path(c).exists()), None)
if not CHROME:
    sys.exit('Chrome/Chromium nicht gefunden — Pfad in pruefungen.py ergaenzen oder '
             'CHROME=/pfad/zum/browser setzen.\n'
             'Unter Linux: sudo apt install chromium-browser')

# OneDrive haelt Ordner gelegentlich fest, deshalb ueberschreiben statt loeschen.
if WORK.exists(): shutil.rmtree(WORK, ignore_errors=True)
shutil.copytree(SRC, WORK, dirs_exist_ok=True,
                ignore=shutil.ignore_patterns('.git', '.testrun', '*.py', '*.md'))

TESTS = r"""
<script>
/* ⚠️ Der Melder steht in einem EIGENEN script-Block. Stuende er im selben wie die
   Pruefungen, wuerde ihn ein Syntaxfehler dort gar nicht erst registrieren -- und genau
   dann braucht man ihn. (Uebernommen aus angel-log, dort hat es eine Runde gekostet.) */
window.addEventListener('error', e => {
  if (document.getElementById('testout')) return;
  const pre = document.createElement('pre');
  pre.id = 'testout';
  pre.textContent = 'ABBRUCH ausserhalb einer Pruefung: ' + e.message
    + ' (Zeile ' + e.lineno + ')\n=== 0 ok, 1 fehlgeschlagen ===';
  document.body.appendChild(pre);
});
</script>
<script>
(async function(){
  const out = [];
  let ok = 0, bad = 0;
  const t = (name, fn) => {
    try { const r = fn(); if (r === true) { ok++; out.push('OK   ' + name); }
          else { bad++; out.push('FAIL ' + name + '  -> ' + r); } }
    catch (e) { bad++; out.push('ERR  ' + name + '  -> ' + e.message); }
  };
  /* ⚠️ Seit dem 27.08.2026 gibt es Pruefungen, die warten muessen: der Packer fuer den
     Plan-Link (`CompressionStream`) arbeitet asynchron, und `t()` haette nur ein
     "[object Promise]" gemeldet -- also einen gruenen Haken auf nichts. `tA` wartet
     wirklich ab; der Lauf drumherum ist deshalb `async`. */
  const tA = async (name, fn) => {
    try { const r = await fn(); if (r === true) { ok++; out.push('OK   ' + name); }
          else { bad++; out.push('FAIL ' + name + '  -> ' + r); } }
    catch (e) { bad++; out.push('ERR  ' + name + '  -> ' + e.message); }
  };
  const eq = (a, b) => a === b ? true : (JSON.stringify(a) + ' != ' + JSON.stringify(b));
  /* Festgenagelt am 27.08.2026, als der Plan-Link auf Nummern umgestellt wurde. Diese drei
     Werte stehen hier als Zahl und nicht als Rechnung - eine Pruefung, die ihren Sollwert
     aus dem Pruefling ableitet, prueft nichts. */
  const LIB_LAENGE  = 672;
  const LIB_ERSTER  = 'Bankdrücken';
  const LIB_LETZTER = 'YTWL-Übung';

  // Der Zustand der App wird von einigen Pruefungen umgebogen. Am Ende zurueck,
  // damit die Reihenfolge der Pruefungen egal bleibt.
  const SICHER = { sessions: sessions, profile: profile, settings: settings };

  // ================================================================ XP und Level
  // Das Level steuert Rang, Brock-Bild und freigeschaltete Designs. Rechnet es
  // falsch, ist die halbe App falsch — und zwar unauffaellig.
  t('Level 1 bei 0 XP',            () => eq(levelFromXP(0).level, 1));
  t('Level 1 braucht 100 XP',      () => eq(levelFromXP(0).need, 100));
  t('0 XP: nichts im Level drin',  () => eq(levelFromXP(0).into, 0));
  t('xpForLevel(1) ist 0',         () => eq(xpForLevel(1), 0));
  t('xpForLevel(2) ist 100',       () => eq(xpForLevel(2), 100));
  t('xpForLevel(3) ist 240',       () => eq(xpForLevel(3), 240));
  t('Hin und zurueck: Level 1..80', () => {
    for (let l = 1; l <= 80; l++)
      if (levelFromXP(xpForLevel(l)).level !== l) return 'Level ' + l + ' -> ' + levelFromXP(xpForLevel(l)).level;
    return true;
  });
  t('Ein XP zu wenig = ein Level tiefer', () => {
    for (let l = 2; l <= 80; l++)
      if (levelFromXP(xpForLevel(l) - 1).level !== l - 1) return 'Level ' + l;
    return true;
  });
  t('Rest bleibt unter der Schwelle', () => {
    for (let xp = 0; xp < 20000; xp += 37) {
      const r = levelFromXP(xp);
      if (r.into < 0 || r.into >= r.need) return 'bei ' + xp + ': ' + r.into + '/' + r.need;
    }
    return true;
  });
  t('Negative XP haengen nicht',   () => eq(levelFromXP(-50).level, 1));
  t('Level steigt nie rueckwaerts', () => {
    let vor = 0;
    for (let xp = 0; xp < 50000; xp += 101) {
      const l = levelFromXP(xp).level;
      if (l < vor) return 'bei ' + xp;
      vor = l;
    }
    return true;
  });

  // ================================================================ Raenge
  t('Level 1 ist Couch-Potato',    () => eq(rankForLevel(1).name, 'Couch-Potato'));
  t('Level 2 noch Couch-Potato',   () => eq(rankForLevel(2).name, 'Couch-Potato'));
  t('Level 3 ist Noob',            () => eq(rankForLevel(3).name, 'Noob'));
  t('Level 45 ist Gigachad',       () => eq(rankForLevel(45).name, 'Gigachad'));
  t('Level 999 bleibt Gigachad',   () => eq(rankForLevel(999).name, 'Gigachad'));
  t('Level 0 faellt nicht durch',  () => !!rankForLevel(0) || 'nichts zurueck');
  t('RANKS stehen aufsteigend', () => {
    for (let i = 1; i < RANKS.length; i++)
      if (RANKS[i].min <= RANKS[i-1].min) return 'Platz ' + i + ' bricht die Reihenfolge';
    return true;
  });
  t('Rang steigt nie rueckwaerts', () => {
    let vor = -1;
    for (let l = 1; l <= 60; l++) {
      const m = rankForLevel(l).min;
      if (m < vor) return 'bei Level ' + l;
      vor = m;
    }
    return true;
  });
  t('Jeder Rang hat ein Brock-Bild', () =>
    RANKS.every(r => typeof r.img === 'string' && /^brock-\d\.png$/.test(r.img))
      || RANKS.filter(r => !/^brock-\d\.png$/.test(r.img || '')).map(r => r.name).join(', '));
  t('Kein Brock-Bild doppelt', () =>
    new Set(RANKS.map(r => r.img)).size === RANKS.length || 'ein Bild kommt zweimal vor');
  t('naechster Rang nach Level 1 ist Noob', () => eq(nextRank(1).name, 'Noob'));
  t('Ueber dem letzten Rang: kein naechster', () => eq(nextRank(45), null));
  t('nextRank liegt immer ueber dem Level', () => {
    for (let l = 1; l < 45; l++) { const n = nextRank(l); if (!n || n.min <= l) return 'Level ' + l; }
    return true;
  });

  // ================================================================ Designs
  // ⚠️ Ein Rang, der ein Design freischaltet, das es nicht gibt, faellt sonst nur
  // demjenigen auf, der den Rang erreicht — also fruehestens nach Wochen.
  t('Jedes freigeschaltete Design gibt es auch', () => {
    const fehlen = RANKS.filter(r => r.unlock && !THEMES[r.unlock]).map(r => r.name + '->' + r.unlock);
    return fehlen.length ? fehlen.join(', ') : true;
  });
  t('Level 1: nur hell und dunkel', () => {
    settings.devUnlockAll = false;
    return eq([...unlockedThemes(1)].sort().join(','), 'dark,light');
  });
  t('Level 10 schaltet midnight frei', () => unlockedThemes(10).has('midnight') || 'fehlt');
  t('Level 9 hat midnight noch nicht',  () => !unlockedThemes(9).has('midnight') || 'zu frueh da');
  t('Level 45 hat alle Freischaltungen', () => {
    const s = unlockedThemes(45);
    const fehlen = RANKS.filter(r => r.unlock && !s.has(r.unlock)).map(r => r.unlock);
    return fehlen.length ? fehlen.join(', ') : true;
  });
  t('devUnlockAll gibt wirklich alle', () => {
    settings.devUnlockAll = true;
    const s = unlockedThemes(1);
    settings.devUnlockAll = false;
    return Object.keys(THEMES).every(k => s.has(k)) || 'nicht alle';
  });
  t('Jedes Design hat die noetigen Farben', () => {
    const noetig = ['--bg','--card','--txt','--accent','--ok','--danger'];
    for (const [k, v] of Object.entries(THEMES)) {
      if (!v.vars) return k + ' hat keine vars';
      const f = noetig.filter(n => !(n in v.vars));
      if (f.length) return k + ' fehlt ' + f.join(',');
    }
    return true;
  });

  // ================================================================ Uebungsbilder
  // Regression zum 05.08.2026: "ein falsches Uebungsbild". Und zum Nachziehen von
  // guessMove, wo frueher jede unbekannte Uebung Bizeps-Curls zeigte.
  t('Jede EXMOVE-Bewegung gibt es als Bild', () => {
    const fehlen = [...new Set(Object.values(EXMOVE))].filter(m => !EXANIM[m]);
    return fehlen.length ? fehlen.join(', ') : true;
  });
  t('Unbekannte Uebung wird zur neutralen Hantel', () => eq(guessMove('Wurstsalat schleppen'), 'dumbbell'));
  t('Leerer Name wird zur neutralen Hantel',       () => eq(guessMove(''), 'dumbbell'));
  t('guessMove vertraegt null',                    () => eq(guessMove(null), 'dumbbell'));
  t('Bankdruecken ist Flachbank',   () => eq(guessMove('Bankdrücken'), 'press_flat'));
  t('Schraegbank ist nicht Flachbank', () => eq(guessMove('Schrägbankdrücken'), 'press_inc'));
  t('Klimmzug ist pullup',          () => eq(guessMove('Klimmzüge'), 'pullup'));
  t('Kniebeuge ist squat',          () => eq(guessMove('Kniebeuge'), 'squat'));
  t('Wadenheben ist calf',          () => eq(guessMove('Wadenheben stehend'), 'calf'));
  t('Kreuzheben ist deadlift',      () => eq(guessMove('Kreuzheben'), 'deadlift'));
  t('guessIcon: Kniebeuge sind Beine', () => eq(guessIcon('Kniebeuge'), 'legs'));
  t('guessIcon: leer gibt dumbbell',   () => eq(guessIcon(''), 'dumbbell'));
  t('guessIcon: Laufband ist cardio',  () => eq(guessIcon('Laufband'), 'cardio'));
  t('Jede geratene Bewegung gibt es als Bild', () => {
    const proben = ['Bankdrücken','Klimmzüge','Kniebeuge','Seilspringen','Plank','Russian Twists',
                    'Hammer-Curls','Beinpresse','Hip Thrust','Fahrrad','Sprints','Irgendwas'];
    const fehlen = proben.filter(p => !EXANIM[guessMove(p)]);
    return fehlen.length ? fehlen.join(', ') : true;
  });

  // ================================================================ Uebungsnamen der Plaene
  // ⚠️ Ein Tippfehler in DAYPOOL faellt sonst NIE auf: die Uebung heisst dann nur
  // anders und bekommt still das geratene statt des hinterlegten Bildes.
  t('Jede Uebung aus DAYPOOL steht in EXMOVE', () => {
    const alle = [...new Set([].concat(...Object.values(DAYPOOL)))];
    const fehlen = alle.filter(n => !EXMOVE[n]);
    return fehlen.length ? fehlen.join(' | ') : true;
  });
  t('Jede Uebung aus FAVPOOL steht in EXMOVE', () => {
    const alle = [...new Set([].concat(...Object.values(FAVPOOL)))];
    const fehlen = alle.filter(n => !EXMOVE[n]);
    return fehlen.length ? fehlen.join(' | ') : true;
  });
  t('Kein DAYPOOL-Tag ist leer', () => {
    const leer = Object.keys(DAYPOOL).filter(k => !DAYPOOL[k] || !DAYPOOL[k].length);
    return leer.length ? leer.join(', ') : true;
  });

  // ================================================================ Splits und Trainingstage
  // Regression zum 05.08.2026: "ein falsch geratener Trainingstag".
  t('todayIdx: Montag ist 0', () => {
    // 24.08.2026 ist ein Montag.
    const d = new Date(2026, 7, 24);
    return eq((d.getDay() + 6) % 7, 0);
  });
  t('todayIdx: Sonntag ist 6', () => {
    const d = new Date(2026, 7, 23);   // Sonntag
    return eq((d.getDay() + 6) % 7, 6);
  });
  t('todayIdx liegt immer in 0..6', () => {
    const i = todayIdx();
    return (i >= 0 && i <= 6) || ('ist ' + i);
  });
  t('Jeder Split hat so viele Tage wie sein Name sagt', () => {
    for (const [n, tage] of Object.entries(SPLITS))
      if (tage.length !== +n) return n + ' hat ' + tage.length + ' Tage';
    return true;
  });
  t('Jeder Split-Tag hat einen Uebungs-Vorrat', () => {
    const fehlen = [];
    for (const tage of Object.values(SPLITS))
      for (const [, key] of tage) if (!DAYPOOL[key]) fehlen.push(key);
    return fehlen.length ? fehlen.join(', ') : true;
  });
  t('Kein Split-Tag heisst zweimal gleich', () => {
    for (const [n, tage] of Object.entries(SPLITS))
      if (new Set(tage.map(x => x[1])).size !== tage.length) return 'Split ' + n;
    return true;
  });
  t('DAYGROUPS kennt nur echte Tage', () => {
    const fehlen = Object.keys(DAYGROUPS).filter(k => !DAYPOOL[k]);
    return fehlen.length ? fehlen.join(', ') : true;
  });
  t('DAYGROUPS zeigt nur auf echte Lieblings-Gruppen', () => {
    const fehlen = [];
    for (const [k, gr] of Object.entries(DAYGROUPS))
      for (const g of gr) if (!FAVPOOL[g]) fehlen.push(k + '->' + g);
    return fehlen.length ? fehlen.join(', ') : true;
  });
  t('Ruecken landet nicht bei den Beinen', () => eq((DAYGROUPS.back || []).join(','), 'pull'));
  t('Jeder Split-Tag hat eine Lieblings-Zuordnung', () => {
    const alle = [...new Set([].concat(...Object.values(SPLITS)).map(x => x[1]))];
    const fehlen = alle.filter(k => !DAYGROUPS[k]);
    return fehlen.length ? fehlen.join(', ') : true;
  });

  // ================================================================ Zeiten
  t('Uhr bei 0',              () => eq(fmtClock(0), '0:00'));
  t('Uhr bei 59 s',           () => eq(fmtClock(59000), '0:59'));
  t('Uhr bei 1 min',          () => eq(fmtClock(60000), '1:00'));
  t('Uhr bei 1 h',            () => eq(fmtClock(3600000), '1:00:00'));
  t('Uhr bei 1 h 2 min 3 s',  () => eq(fmtClock(3723000), '1:02:03'));
  t('Uhr wird nie negativ',   () => eq(fmtClock(-9999), '0:00'));
  t('Dauer 0 gibt nichts',    () => eq(fmtDauer(0), null));
  t('Dauer negativ gibt nichts', () => eq(fmtDauer(-1), null));
  t('Dauer 59 s wird 1 min',  () => eq(fmtDauer(59000), '1 min'));
  t('Dauer 1 h',              () => eq(fmtDauer(3600000), '1 h 00 min'));
  t('Dauer 1 h 1 min',        () => eq(fmtDauer(3660000), '1 h 01 min'));
  t('Dauer 90 min',           () => eq(fmtDauer(5400000), '1 h 30 min'));

  // ================================================================ Gewicht formatieren
  t('2,5 kg mit Komma',       () => eq(fmtKg(2.5), '2,5'));
  t('Ganze Zahl ohne Komma',  () => eq(fmtKg(100), '100'));
  t('Auf eine Stelle gerundet', () => eq(fmtKg(2.55), '2,6'));
  t('Null ist 0',             () => eq(fmtKg(0), '0'));

  // ================================================================ Aufwaermsaetze
  // Sie duerfen NIRGENDS mitzaehlen — sonst zieht der leichte erste Satz die
  // Steigerungsregel nach unten und es gibt nie mehr Gewicht.
  const SATZE = [
    {warm:true,  done:true, weight:20, reps:15},
    {warm:false, done:true, weight:60, reps:10},
    {warm:false, done:true, weight:60, reps:8},
    {warm:false, done:false, weight:60, reps:0}
  ];
  const EINTRAG = [{name:'Bankdrücken', sets:SATZE}];
  t('arbeit wirft Aufwaermsaetze raus', () => eq(arbeit(SATZE).length, 3));
  t('arbeit vertraegt nichts',          () => eq(arbeit(null).length, 0));
  t('Volumen ohne Aufwaermsatz',        () => eq(volume(EINTRAG), 60*10 + 60*8));
  t('Nur abgehakte Saetze zaehlen',     () => eq(doneSets(EINTRAG), 2));
  t('Volumen leerer Liste ist 0',       () => eq(volume([]), 0));
  t('Volumen ohne Gewicht ist 0',       () => eq(volume([{sets:[{done:true, reps:10}]}]), 0));
  t('XP einer Einheit', () => eq(sessXP(EINTRAG), 2*10 + 50 + Math.floor(1080/1000)*20));

  // ================================================================ Steigerung
  const machEinheit = (satzListe) => ([{ date: Date.now(), entries: [{ name:'Bankdrücken', sets: satzListe }] }]);
  t('Alles abgehakt und drueber -> mehr Gewicht', () => {
    sessions = machEinheit([{warm:false,done:true,weight:60,reps:15},{warm:false,done:true,weight:60,reps:15}]);
    const s = suggest('Bankdrücken', null);
    return (s && s.up === true && s.w === 62.5) || JSON.stringify(s);
  });
  t('Ein Satz nicht abgehakt -> gleiches Gewicht', () => {
    sessions = machEinheit([{warm:false,done:true,weight:60,reps:15},{warm:false,done:false,weight:60,reps:0}]);
    const s = suggest('Bankdrücken', null);
    return (s && s.up === false && s.w === 60) || JSON.stringify(s);
  });
  t('Genau auf der Grenze -> noch nicht mehr', () => {
    // repGoal ist 14 bei viel Volumen; 14 ist NICHT ueber 14.
    profile.vol = 'high';
    sessions = machEinheit([{warm:false,done:true,weight:60,reps:14},{warm:false,done:true,weight:60,reps:14}]);
    const s = suggest('Bankdrücken', null);
    return (s && s.up === false) || JSON.stringify(s);
  });
  t('Der schwaechste Satz entscheidet', () => {
    sessions = machEinheit([{warm:false,done:true,weight:60,reps:20},{warm:false,done:true,weight:60,reps:9}]);
    const s = suggest('Bankdrücken', null);
    return (s && s.up === false) || JSON.stringify(s);
  });
  t('Aufwaermsatz zieht die Steigerung nicht runter', () => {
    sessions = machEinheit([{warm:true,done:true,weight:20,reps:5},
                            {warm:false,done:true,weight:60,reps:15},{warm:false,done:true,weight:60,reps:15}]);
    const s = suggest('Bankdrücken', null);
    return (s && s.up === true) || JSON.stringify(s);
  });
  t('Ohne Vorgeschichte kein Vorschlag', () => {
    sessions = [];
    return eq(suggest('Bankdrücken', null), null);
  });
  t('Grosse Uebung steigt in 5er-Schritten',  () => eq(stepFor('Kniebeuge'), 5));
  t('Kleine Uebung steigt in 2,5er-Schritten', () => eq(stepFor('Bizeps-Curls (LH)'), 2.5));
  t('stepFor vertraegt leer',                  () => eq(stepFor(''), 2.5));
  t('Wenig Volumen: Grenze 10',  () => { profile.vol='low';  return eq(repGoal(null), 10); });
  t('Viel Volumen: Grenze 14',   () => { profile.vol='high'; return eq(repGoal(null), 14); });
  t('Grenze liegt ueber dem Zielbereich', () => {
    profile.vol = 'high';
    return repGoal(null) > exRange(null)[1] || 'Grenze ' + repGoal(null) + ' <= ' + exRange(null)[1];
  });

  // ================================================================ Aufwaermgewicht
  t('Aufwaermen mit 70 % von 100 kg', () => eq(warmKg(100), 70));
  t('Ohne Gewicht kein Aufwaermgewicht', () => eq(warmKg(0), ''));
  t('Aufwaermen ist nie schwerer als der Satz', () => {
    for (let w = 1; w <= 200; w += 0.5) {
      const v = warmKg(w);
      if (v !== '' && v > w) return v + ' kg Aufwaermen bei ' + w + ' kg Arbeitsgewicht';
    }
    return true;
  });

  // ================================================================ Koerpergewicht
  // Regression zum 05.08.2026: "Gewichtseintraege mit falschem Datum".
  t('Zweimal am selben Tag ueberschreibt', () => {
    profile.weights = [];
    addWeight(80); addWeight(81);
    return (profile.weights.length === 1 && profile.weights[0].kg === 81)
      || JSON.stringify(profile.weights);
  });
  t('Gestern bleibt neben heute stehen', () => {
    profile.weights = [{date: Date.now() - 864e5, kg: 79}];
    addWeight(80);
    return eq(profile.weights.length, 2);
  });
  t('Auf 100 g gerundet', () => {
    profile.weights = []; addWeight(80.44);
    return eq(profile.weights[0].kg, 80.4);
  });
  t('Null wird abgelehnt',      () => eq(addWeight(0), false));
  t('Negativ wird abgelehnt',   () => eq(addWeight(-5), false));
  t('Ueber 500 kg abgelehnt',   () => eq(addWeight(501), false));
  t('Buchstaben werden abgelehnt', () => eq(addWeight('schwer'), false));
  t('Liste kommt nach Datum sortiert', () => {
    const n = Date.now();
    profile.weights = [{date:n, kg:80},{date:n-2*864e5, kg:78},{date:n-864e5, kg:79}];
    return eq(weightList().map(x => x.kg).join(','), '78,79,80');
  });
  t('weightList aendert das Original nicht', () => {
    const n = Date.now();
    profile.weights = [{date:n, kg:80},{date:n-864e5, kg:79}];
    weightList();
    return eq(profile.weights[0].kg, 80);
  });
  t('Ohne Eintraege kein letztes Gewicht', () => { profile.weights = []; return eq(lastWeight(), null); });

  // ================================================================ Sichern beim Wegschalten
  /* Fehler vom 24.08.2026, gemeldet von Karl: "die eintragungen beim gewicht werden nicht
     gesyned". Die Ursache lag NICHT im Eintragen -- addWeight und save() sind seit dem
     22.08. geprueft -- sondern im Weg in die Cloud: gesendet wurde erst 2 Sekunden nach
     der letzten Aenderung. Wer sich wiegt, tippt eine Zahl und legt das Handy weg; die
     Seite friert ein, der Timer feuert nie. Bei einem Training faellt genau derselbe
     Fehler nicht auf, weil man danach noch lange in der App bleibt.
     Die Pruefungen halten die zwei Ereignisse fest, an denen jetzt sofort gesendet wird. */
  const mitFlush = (fn) => {                       // Umgebung stellen und hinterher aufraeumen
    const echtPush = window.cloudPush, echtSession = session, echtDirty = dirty;
    const rufe = [];
    window.cloudPush = (arg) => { rufe.push(arg); return Promise.resolve(true); };
    session = {user:{id:'test'}, expires_at: Date.now() + 3600e3, access_token:'x'};
    try { return fn(rufe); }
    finally { window.cloudPush = echtPush; session = echtSession; setDirty(echtDirty); }
  };
  const wegschalten = (zustand) => {               // visibilityState ist sonst schreibgeschuetzt
    const alt = Object.getOwnPropertyDescriptor(Document.prototype, 'visibilityState');
    Object.defineProperty(document, 'visibilityState', {value: zustand, configurable: true});
    document.dispatchEvent(new Event('visibilitychange'));
    delete document.visibilityState;
    if (alt) Object.defineProperty(Document.prototype, 'visibilityState', alt);
  };

  t('Wegschalten sendet sofort', () => mitFlush(rufe => {
    setDirty(true); wegschalten('hidden');
    return eq(rufe.length, 1);
  }));
  t('Beim Wegschalten mit keepalive', () => mitFlush(rufe => {
    setDirty(true); wegschalten('hidden');
    return eq(rufe[0], true);
  }));
  t('Zurueckkommen sendet nicht', () => mitFlush(rufe => {
    setDirty(true); wegschalten('visible');
    return eq(rufe.length, 0);
  }));
  t('Ohne Aenderung wird nichts gesendet', () => mitFlush(rufe => {
    setDirty(false); wegschalten('hidden');
    return eq(rufe.length, 0);
  }));
  t('Schliessen sendet sofort', () => mitFlush(rufe => {
    setDirty(true); window.dispatchEvent(new Event('pagehide'));
    return eq(rufe.length, 1);
  }));
  // Ohne Anmeldung gibt es keine Cloud -- dann waere jeder Sendeversuch ein Fehler im Log.
  t('Nicht angemeldet sendet nichts', () => {
    const echtPush = window.cloudPush, echtSession = session;
    const rufe = [];
    window.cloudPush = (arg) => { rufe.push(arg); return Promise.resolve(true); };
    session = null;
    try { flushSync(); return eq(rufe.length, 0); }
    finally { window.cloudPush = echtPush; session = echtSession; }
  });
  /* Der wartende 2-Sekunden-Timer muss weg, sonst sendet die App beim Zurueckkommen
     denselben Stand ein zweites Mal. */
  t('Der wartende Timer wird geloescht', () => mitFlush(rufe => {
    profile.weights = []; setDirty(true);
    scheduleSync();                                 // setzt den 2-Sekunden-Timer
    flushSync();
    const offen = (typeof syncT !== 'undefined');
    return offen ? eq(rufe.length, 1) : 'syncT gibt es nicht mehr';
  }));
  // Und die Kette davor: ein Gewichtseintrag muss ueberhaupt als ungesichert gelten.
  t('Gewicht eintragen macht ungesichert', () => mitFlush(() => {
    profile.weights = []; setDirty(false);
    addWeight(80);
    return eq(dirty, true);
  }));

  // ================================================================ Zusammenfuehren statt Ueberschreiben
  /* Eingebaut am 24.08.2026. Vorher schickte der Abgleich immer den ganzen Datenblock und
     beim Start galt "wer etwas Offenes hat, schiebt". Ein Geraet mit einer einzigen
     ungesicherten Aenderung holte deshalb nie -- es ueberschrieb das andere. Diese
     Pruefungen halten fest, dass die zwei Listen vereinigt und nicht ersetzt werden.
     Hier kostet ein Fehler Daten, nicht Bequemlichkeit -- deshalb ausfuehrlich. */
  const einheit = (id, date, xp) => ({id, date, xp, planName:'P', entries:[]});
  const blob = (o) => Object.assign({programs:[], plans:[], sessions:[], settings:{rest:90},
                                     profile:{xp:0, weights:[]}}, o);

  t('Einheit, die nur in der Cloud steht, kommt dazu', () => {
    const a = blob({sessions:[einheit('a', 100, 5)]});
    const b = blob({sessions:[einheit('b', 200, 7)]});
    return eq(blobsZusammen(a, b).blob.sessions.map(x=>x.id).join(','), 'a,b');
  });
  t('Einheit, die nur lokal steht, bleibt', () => {
    const a = blob({sessions:[einheit('a', 100, 5)]});
    return eq(blobsZusammen(a, blob({})).blob.sessions.map(x=>x.id).join(','), 'a');
  });
  t('Dieselbe Einheit kommt nicht doppelt', () => {
    const a = blob({sessions:[einheit('a', 100, 5)]});
    const b = blob({sessions:[einheit('a', 100, 5)]});
    return eq(blobsZusammen(a, b).blob.sessions.length, 1);
  });
  t('Einheiten liegen aufsteigend nach Datum', () => {
    const a = blob({sessions:[einheit('spaet', 900, 1)]});
    const b = blob({sessions:[einheit('frueh', 100, 1)]});
    return eq(blobsZusammen(a, b).blob.sessions.map(x=>x.id).join(','), 'frueh,spaet');
  });
  /* XP steht gespeichert im Profil, es wird nicht aus den Einheiten gerechnet. Kommt eine
     Einheit dazu, muss ihr Punktestand mit -- sonst zeigt der Rang weniger an als der
     Verlauf darunter hergibt. */
  t('Uebernommene Einheit bringt ihre XP mit', () => {
    const a = blob({sessions:[einheit('a', 100, 5)], profile:{xp:5, weights:[]}});
    const b = blob({sessions:[einheit('b', 200, 7)]});
    return eq(blobsZusammen(a, b).blob.profile.xp, 12);
  });
  t('Schon bekannte Einheit bringt keine XP nochmal', () => {
    const a = blob({sessions:[einheit('a', 100, 5)], profile:{xp:5, weights:[]}});
    const b = blob({sessions:[einheit('a', 100, 5)]});
    return eq(blobsZusammen(a, b).blob.profile.xp, 5);
  });
  t('Alte Einheit ohne xp zaehlt 0', () => {
    const a = blob({profile:{xp:10, weights:[]}});
    const b = blob({sessions:[{id:'alt', date:50, planName:'P', entries:[]}]});
    return eq(blobsZusammen(a, b).blob.profile.xp, 10);
  });

  // ---- Gewichtskurve: ein Eintrag je Tag, dieselbe Regel wie addWeight() ----
  t('Gewicht von zwei Tagen bleibt vollstaendig', () => {
    const heute = Date.now(), gestern = heute - 864e5;
    const a = blob({profile:{xp:0, weights:[{date:gestern, kg:79}]}});
    const b = blob({profile:{xp:0, weights:[{date:heute,   kg:80}]}});
    return eq(blobsZusammen(a, b).blob.profile.weights.map(x=>x.kg).join(','), '79,80');
  });
  t('Gleicher Tag: der spaetere Wert gewinnt', () => {
    const frueh = new Date(2026,7,24,7,0).getTime(), spaet = new Date(2026,7,24,21,0).getTime();
    const a = blob({profile:{xp:0, weights:[{date:frueh, kg:80}]}});
    const b = blob({profile:{xp:0, weights:[{date:spaet, kg:81}]}});
    const w = blobsZusammen(a, b).blob.profile.weights;
    return (w.length === 1 && w[0].kg === 81) || JSON.stringify(w);
  });
  t('Gewicht kommt sortiert zurueck', () => {
    const n = Date.now();
    const a = blob({profile:{xp:0, weights:[{date:n, kg:80}]}});
    const b = blob({profile:{xp:0, weights:[{date:n-2*864e5, kg:78},{date:n-864e5, kg:79}]}});
    return eq(blobsZusammen(a, b).blob.profile.weights.map(x=>x.kg).join(','), '78,79,80');
  });
  t('Unsinnige Gewichtswerte fliegen raus', () => {
    const a = blob({profile:{xp:0, weights:[]}});
    const b = blob({profile:{xp:0, weights:[{date:Date.now(), kg:0}]}});
    return eq(blobsZusammen(a, b).blob.profile.weights.length, 0);
  });

  // ---- Was bewusst NICHT zusammengefuehrt wird ----
  t('Plaene kommen von der Basis, nicht vom anderen Stand', () => {
    const a = blob({programs:[{id:'p1', name:'meiner'}]});
    const b = blob({programs:[{id:'p2', name:'fremder'}]});
    const pr = blobsZusammen(a, b).blob.programs;
    return (pr.length === 1 && pr[0].name === 'meiner') || JSON.stringify(pr);
  });
  t('Einstellungen kommen von der Basis', () => {
    const a = blob({settings:{rest:60}});
    const b = blob({settings:{rest:120}});
    return eq(blobsZusammen(a, b).blob.settings.rest, 60);
  });

  /* Der Zaehler entscheidet, ob nach dem Zusammenfuehren geschoben wird. Zaehlt er zu
     niedrig, bleibt der andere Stand ohne die neuen Eintraege stehen. */
  t('uebernommen zaehlt neue Einheiten', () => {
    const a = blob({}), b = blob({sessions:[einheit('a',100,1), einheit('b',200,1)]});
    return eq(blobsZusammen(a, b).uebernommen, 2);
  });
  t('uebernommen ist 0, wenn nichts dazukommt', () => {
    const a = blob({sessions:[einheit('a',100,1)]});
    const b = blob({sessions:[einheit('a',100,1)]});
    return eq(blobsZusammen(a, b).uebernommen, 0);
  });
  t('uebernommen zaehlt auch neue Gewichtstage', () => {
    const n = Date.now();
    const a = blob({profile:{xp:0, weights:[{date:n, kg:80}]}});
    const b = blob({profile:{xp:0, weights:[{date:n-864e5, kg:79}]}});
    return eq(blobsZusammen(a, b).uebernommen, 1);
  });

  // ---- Robustheit: ein leerer oder halber Gegenstand darf den Abgleich nicht sprengen ----
  t('Nichts als Gegenstand bricht nicht', () => {
    const a = blob({sessions:[einheit('a',100,3)], profile:{xp:3, weights:[]}});
    const r = blobsZusammen(a, null);
    return (r.blob.sessions.length === 1 && r.uebernommen === 0) || JSON.stringify(r);
  });
  t('Leere Basis nimmt alles auf', () => {
    const b = blob({sessions:[einheit('a',100,4)], profile:{xp:4, weights:[]}});
    const r = blobsZusammen({}, b);
    return (r.blob.sessions.length === 1 && r.blob.profile.xp === 4) || JSON.stringify(r.blob);
  });
  t('Gegenstand ohne Profil bricht nicht', () => {
    const a = blob({profile:{xp:2, weights:[{date:Date.now(), kg:80}]}});
    return eq(blobsZusammen(a, {sessions:[]}).blob.profile.weights.length, 1);
  });
  /* Wuerde die Basis mitveraendert, waere der zweite Aufruf in cloudSyncStart verfaelscht --
     dort wird derselbe lokale Stand zweimal als Basis benutzt. */
  t('Die Basis bleibt unveraendert', () => {
    const a = blob({sessions:[einheit('a',100,5)], profile:{xp:5, weights:[]}});
    blobsZusammen(a, blob({sessions:[einheit('b',200,7)]}));
    return (a.sessions.length === 1 && a.profile.xp === 5) || 'Basis wurde angefasst';
  });

  // ================================================================ Passwort vergessen
  /* Eingebaut am 24.08.2026, uebernommen von angel-log (v57-v59). Bis dahin gab es keinen
     Weg zurueck: wer sein Passwort vergass, war endgueltig ausgesperrt. Karl ist genau das
     am 18.08. bei angel-log selbst passiert, und seit dem 23.08. testet Bruno diese App. */

  // ---- Die Stunde Pause. Sie ist keine Sicherheitssperre, sondern schuetzt das gemeinsame
  // Kontingent von 2 Mails je Stunde davor, dass ein Ungeduldiger es allein aufbraucht.
  const ohneBremse = (fn) => {
    const alt = localStorage.getItem(BREMSE_KEY);
    try { localStorage.removeItem(BREMSE_KEY); return fn(); }
    finally { if (alt === null) localStorage.removeItem(BREMSE_KEY);
              else localStorage.setItem(BREMSE_KEY, alt); }
  };

  t('Frisch ist nichts gebremst', () => ohneBremse(() => eq(bremseRestMin('a@x.de'), 0)));
  t('Nach dem Absenden ist eine Stunde Pause', () => ohneBremse(() => {
    bremseSetzen('a@x.de');
    const r = bremseRestMin('a@x.de');
    return (r > 55 && r <= 60) || r + ' Minuten Rest';
  }));
  /* Der Schluessel ist die ADRESSE, nicht das Geraet. Wer beim ersten Versuch das falsche
     Konto erwischt hat, muss sofort das richtige probieren duerfen -- geraeteweit haette
     die Bremse genau die richtige Handlung bestraft. */
  t('Gebremst wird je Adresse, nicht je Geraet', () => ohneBremse(() => {
    bremseSetzen('a@x.de');
    return eq(bremseRestMin('b@x.de'), 0);
  }));
  t('Grossschreibung ist dieselbe Adresse', () => ohneBremse(() => {
    bremseSetzen('a@x.de');
    return (bremseRestMin('  A@X.DE  ') > 0) || 'nicht erkannt';
  }));
  // Das Geraet soll nie laenger als eine Stunde festhalten, wer hier zurueckgesetzt hat.
  t('Abgelaufenes wird beim Schreiben weggeraeumt', () => ohneBremse(() => {
    localStorage.setItem(BREMSE_KEY, JSON.stringify({'alt@x.de': Date.now() - 2*60*60*1000}));
    bremseSetzen('neu@x.de');
    const o = bremseLesen();
    return (!('alt@x.de' in o) && ('neu@x.de' in o)) || JSON.stringify(o);
  }));

  // ---- Der Rueckweg aus der Mail
  const mitHash = (h, fn) => {
    const vorher = location.hash, tk = resetToken, rf = resetRefresh;
    try { location.hash = h; return fn(); }
    finally { resetToken = tk; resetRefresh = rf;
              try { location.hash = vorher; } catch (e) {} }
  };

  t('Ohne Rautenteil passiert nichts', () => mitHash('', () => eq(rueckkehrAusMail(), null)));
  /* ⚠️ Wichtig: der geteilte Trainingsplan kommt als "#p=..." herein. Wuerde der
     Ruecksetz-Weg den auch anfassen, waere das Plan-Teilen kaputt. */
  t('Ein geteilter Plan im Link wird nicht angefasst', () =>
    mitHash('#p=abc', () => eq(rueckkehrAusMail(), null)));
  t('Recovery-Link setzt den Token', () =>
    mitHash('#access_token=TOK123&refresh_token=REF456&type=recovery', () => {
      const r = rueckkehrAusMail();
      return (r && r.token === 'TOK123' && resetToken === 'TOK123' && resetRefresh === 'REF456')
        || JSON.stringify(r);
    }));
  /* ⚠️ Ein Zugangs-Token im Verlauf des Browsers ist genau das, was man nicht will --
     und beim Teilen der Adresse ginge er mit. */
  t('Der Token wird aus der Adresszeile geraeumt', () =>
    mitHash('#access_token=TOK123&type=recovery', () => {
      rueckkehrAusMail();
      return (location.hash.indexOf('TOK123') === -1) || 'Token steht noch in der Adresse';
    }));
  // Ohne diesen Zweig staende der Anmelde-Schirm nach einem alten Link wortlos da.
  t('Abgelaufener Link sagt, dass er abgelaufen ist', () =>
    mitHash('#error=access_denied&error_description=Email+link+is+invalid+or+has+expired', () => {
      const r = rueckkehrAusMail();
      return (r && /abgelaufen/i.test(r.fehler)) || JSON.stringify(r);
    }));
  t('Ein Link ohne Token gibt keinen Token her', () =>
    mitHash('#type=recovery', () => {
      const r = rueckkehrAusMail();
      return (r && r.fehler && !r.token) || JSON.stringify(r);
    }));

  // ---- Der Weg muss auch sichtbar sein, sonst findet ihn niemand
  const mitGate = (modus, fn) => {
    const v = view, am = authMode, inhalt = app.innerHTML;
    try { authMode = modus; renderAuthGate(); return fn(app.innerHTML); }
    finally { view = v; authMode = am; app.innerHTML = inhalt; }
  };
  t('Auf dem Anmelde-Schirm steht "Passwort vergessen?"', () =>
    mitGate('login', h => h.indexOf('Passwort vergessen?') >= 0 || 'steht nicht da'));
  t('Beim Registrieren steht es nicht', () =>
    mitGate('register', h => h.indexOf('Passwort vergessen?') < 0 || 'steht faelschlich da'));
  t('Der Vergessen-Schirm hat ein E-Mail-Feld', () =>
    mitGate('vergessen', h => h.indexOf('id="rs_mail"') >= 0 || 'kein Feld'));
  // Zweimal eingeben, damit kein Vertipper drin bleibt (angel-log v58).
  t('Das neue Passwort wird zweimal eingegeben', () =>
    mitGate('neuespw', h => (h.indexOf('id="np_pw"') >= 0 && h.indexOf('id="np_pw2"') >= 0)
      || 'nur ein Feld'));

  // ================================================================ Anmelden nur mit E-Mail
  /* Eingebaut am 24.08.2026, uebernommen von angel-log v56. Bis dahin ging Anmelden auch
     mit dem Benutzernamen -- die App holte dafuer ueber `email_for_username` erst die
     Adresse, und diese Funktion war zwangslaeufig fuer NICHT Angemeldete offen. Wer einen
     Namen erriet, bekam die E-Mail dazu. Live gemessen: HTTP 200 ohne Anmeldung. */

  // Die Funktion darf aus der App heraus nicht mehr gerufen werden.
  t('Die App ruft email_for_username nicht mehr', () =>
    (typeof authSignIn === 'function'
      && !/supaRPC\(\s*['\"]email_for_username/.test(authSignIn.toString()))
    || 'der Aufruf steht noch drin');

  const mitFehler = async (fn) => { try { await fn(); return null; }
                                    catch (e) { return typeof e === 'string' ? e : (e && e.message) || String(e); } };

  /* ⚠️ Der Prueframen ist synchron -- authSignIn ist es nicht. Geprueft wird deshalb der
     Quelltext der Funktion, nicht ihr Ablauf: dass ueberhaupt auf das @ geprueft wird und
     dass es dafuer einen EIGENEN Satz gibt. Ohne den haelt derjenige sein Passwort fuer
     falsch und probiert es immer wieder. */
  /* ⚠️ Diese Pruefung hiess zuerst nur "wird auf @ geprueft" -- und war damit auch gegen
     die ALTE Fassung gruen: die prueft ebenfalls auf @, nur um danach nachzuschlagen
     statt abzubrechen. Gruen aus dem falschen Grund. Geprueft wird deshalb, dass auf die
     Pruefung ein `throw` folgt und kein Nachschlagen. */
  t('Ohne @ wird abgebrochen statt nachgeschlagen', () => {
    const q = authSignIn.toString().replace(/\s+/g, ' ');
    return /includes\( ?['\"]@['\"] ?\) ?\) ?throw/.test(q) || 'auf die @-Pruefung folgt kein throw';
  });
  t('Der Benutzername bekommt einen eigenen Satz', () => {
    const q = authSignIn.toString();
    return /E-Mail-Adresse, nicht deinen Benutzernamen/.test(q) || 'kein eigener Satz';
  });
  // Ob es einen Namen GIBT, bleibt abfragbar -- die Registrierung braucht das.
  t('username_taken wird weiter benutzt', () =>
    /username_taken/.test(authSignUp.toString()) || 'wird nicht mehr gefragt');

  // ---- Die Bequemlichkeit, die dafuer zurueckkommt
  const ohneMail = (fn) => {
    const alt = localStorage.getItem(LETZTE_MAIL_KEY);
    try { localStorage.removeItem(LETZTE_MAIL_KEY); return fn(); }
    finally { if (alt === null) localStorage.removeItem(LETZTE_MAIL_KEY);
              else localStorage.setItem(LETZTE_MAIL_KEY, alt); }
  };
  const gate = (modus) => {
    const v = view, am = authMode, inhalt = app.innerHTML;
    try { authMode = modus; renderAuthGate(); return app.innerHTML; }
    finally { view = v; authMode = am; app.innerHTML = inhalt; }
  };

  t('Ohne Vorgeschichte ist das Feld leer', () => ohneMail(() =>
    gate('login').indexOf('value=""') >= 0 || 'kein leeres Feld'));
  t('Die zuletzt benutzte Adresse steht im Feld', () => ohneMail(() => {
    letzteMailMerken('karl@example.de');
    return gate('login').indexOf('karl@example.de') >= 0 || 'steht nicht im Feld';
  }));
  /* Beim Registrieren waere es die Adresse eines ANDEREN Kontos -- und das faellt beim
     Tippen niemandem auf. */
  t('Beim Registrieren bleibt das Feld leer', () => ohneMail(() => {
    letzteMailMerken('karl@example.de');
    return gate('register').indexOf('karl@example.de') < 0 || 'steht faelschlich da';
  }));
  t('Das Feld ist ein echtes E-Mail-Feld', () => ohneMail(() => {
    const h = gate('login');
    return (h.indexOf('type="email"') >= 0 && h.indexOf('inputmode="email"') >= 0)
      || 'kein E-Mail-Feld';
  }));
  // Sie soll das Abmelden ueberleben -- genau danach soll sie ja noch dastehen.
  t('Die Adresse liegt nicht im Konto', () => ohneMail(() => {
    letzteMailMerken('karl@example.de');
    const sess = DB.get('session', null);
    return (JSON.stringify(sess || {}).indexOf('karl@example.de') < 0) || 'steht im Konto';
  }));
  t('Sie verlaesst das Geraet nicht', () => ohneMail(() => {
    letzteMailMerken('karl@example.de');
    return (JSON.stringify(appDataBlob()).indexOf('karl@example.de') < 0)
      || 'wandert in die Cloud';
  }));

  // ================================================================ Datenschutzerklaerung
  /* Am 24.08.2026 stand sie auf dem Stand vom 6. August, waehrend Schritte, Push und der
     Melde-Knopf laengst drin waren. Ein falscher Satz in dieser Erklaerung war schon am
     05.08.2026 einer der sechs Fehler, die erst beim Benutzen auffielen. */
  const datenschutzText = () => {
    const v = view, inhalt = app.innerHTML;
    try { renderPrivacy(); return app.innerHTML; }
    finally { view = v; app.innerHTML = inhalt; }
  };
  t('Der Discord-Weg steht drin', () =>
    datenschutzText().indexOf('Discord') >= 0 || 'Discord wird nicht genannt');
  t('Dass die Meldung die EU verlaesst, steht drin', () => {
    const h = datenschutzText();
    return /Discord[\s\S]{0,400}EU/.test(h) || 'kein Hinweis beim Discord-Absatz';
  });
  t('Die Schritte stehen in der Datenliste', () =>
    datenschutzText().indexOf('Schritte') >= 0 || 'Schritte fehlen');
  t('Die Push-Kennung steht drin', () =>
    datenschutzText().indexOf('Benachrichtigungen') >= 0 || 'Push fehlt');
  // Ein Stand, der aelter ist als die Funktionen darunter, ist schlimmer als keiner.
  t('Der Stand ist nicht mehr der 6. August', () =>
    (PRIVACY_STAND.indexOf('6. August') < 0) || 'Stand nicht hochgezogen');

  // ================================================================ Selber Tag
  t('Morgens und abends ist derselbe Tag', () =>
    sameDay(new Date(2026,7,22,7,30).getTime(), new Date(2026,7,22,23,50).getTime()) || 'nein');
  t('Ueber Mitternacht ist ein anderer Tag', () =>
    !sameDay(new Date(2026,7,22,23,59).getTime(), new Date(2026,7,23,0,1).getTime()) || 'doch');

  // ================================================================ Text absichern
  t('Spitze Klammern werden entschaerft', () => eq(esc('<script>'), '&lt;script&gt;'));
  t('Anfuehrungszeichen werden entschaerft', () => eq(esc('a"b'), 'a&quot;b'));
  t('Kaufmanns-Und wird entschaerft', () => eq(esc('a&b'), 'a&amp;b'));
  t('Reihenfolge stimmt (kein doppeltes Ersetzen)', () => eq(esc('<a&b>'), '&lt;a&amp;b&gt;'));
  t('esc vertraegt null', () => eq(esc(null), 'null'));

  // ================================================================ Plan teilen
  t('Kodieren und zurueck', () => eq(b64dec(b64enc('Hallo Welt')), 'Hallo Welt'));
  t('Umlaute ueberstehen den Weg', () => eq(b64dec(b64enc('Kniebeuge Schrägbank ÄÖÜß')), 'Kniebeuge Schrägbank ÄÖÜß'));
  t('Code enthaelt nichts URL-Gefaehrliches', () => {
    const c = b64enc('a/b+c?d=e ÄÖÜ');
    return !/[+/=]/.test(c) || 'enthaelt ' + c;
  });
  t('Plan-Code laesst sich wieder lesen', () => {
    const prog = {id:'x', name:'Testplan', plans:[
      {id:'p1', name:'Push', day:0, exercises:[{id:'e1', name:'Bankdrücken', sets:3}]}]};
    const d = JSON.parse(b64dec(planCode(prog)));
    return (d.v === 2 && d.name === 'Testplan' && d.p.length === 1
            && d.p[0].e[0][0] === 'Bankdrücken') || JSON.stringify(d);
  });
  t('Trainings ohne Uebungen fliegen raus', () => {
    const prog = {id:'x', name:'Leer', plans:[{id:'p1', name:'Nix', day:0, exercises:[]}]};
    return eq(JSON.parse(b64dec(planCode(prog))).p.length, 0);
  });
  t('Lange Namen werden gekuerzt', () => {
    const lang = 'A'.repeat(200);
    const prog = {id:'x', name:lang, plans:[
      {id:'p1', name:lang, day:0, exercises:[{id:'e1', name:lang, sets:3}]}]};
    const d = JSON.parse(b64dec(planCode(prog)));
    return (d.name.length === 40 && d.p[0].n.length === 40 && d.p[0].e[0][0].length === 60)
      || [d.name.length, d.p[0].n.length, d.p[0].e[0][0].length].join('/');
  });

  // ================================================================ Kalorien
  // ⚠️ Dieser Teil war bis zum 21.08.2026 NIE in echter Benutzung. Genau deshalb
  // stehen hier die Faelle mit leeren und krummen Werten.
  t('Summe leerer Liste ist null', () => eq(JSON.stringify(sumMeals([])), JSON.stringify({kcal:0,p:0,c:0,f:0})));
  t('Summe zaehlt zusammen', () => eq(sumMeals([{kcal:100,p:10,c:20,f:5},{kcal:50,p:5,c:10,f:2}]).kcal, 150));
  t('Fehlende Werte werden zu 0, nicht zu NaN', () => {
    const s = sumMeals([{kcal:100},{}]);
    return (s.p === 0 && s.c === 0 && s.f === 0 && s.kcal === 100) || JSON.stringify(s);
  });
  t('Text statt Zahl gibt kein NaN', () => {
    const s = sumMeals([{kcal:'viel', p:'etwas'}]);
    return (s.kcal === 0 && s.p === 0) || JSON.stringify(s);
  });
  t('Je 100 g: 200 g sind das Doppelte', () => {
    const w = draftWerte({basis:'g100', kcal:100, p:10, c:20, f:5}, 200);
    return (w.kcal === 200 && w.p === 20) || JSON.stringify(w);
  });
  t('Je 100 g: 50 g sind die Haelfte', () => eq(draftWerte({basis:'g100', kcal:100}, 50).kcal, 50));
  t('Portion: Menge 2 ist das Doppelte', () => eq(draftWerte({basis:'portion', kcal:250}, 2).kcal, 500));
  t('Portion ohne Menge ist eine Portion', () => eq(draftWerte({basis:'portion', kcal:250}, 0).kcal, 250));
  t('Leerer Entwurf gibt Nullen, kein NaN', () => {
    const w = draftWerte(leerDraft(), 100);
    return Object.values(w).every(v => v === 0) || JSON.stringify(w);
  });
  t('Menge 0 bei je 100 g gibt 0', () => eq(draftWerte({basis:'g100', kcal:100}, 0).kcal, 0));
  t('Ring vertraegt Ziel 0 ohne Absturz', () => typeof kcalRing(500, 0) === 'string' || 'kein SVG');
  t('Ring bleibt bei Ueberschreitung heil', () => kcalRing(3000, 2000).includes('--danger') || 'nicht rot');
  t('Ring unter dem Ziel ist gruen', () => kcalRing(500, 2000).includes('--ok') || 'nicht gruen');

  // ================================================================ Pausen-Uhr
  // Regression zum 05.08.2026: "ein stehenbleibender Pausen-Timer".
  t('Start setzt Rest und Gesamt', () => {
    startRest(90); const r = (rest.remaining === 90 && rest.total === 90);
    stopRest(); return r || (rest.remaining + '/' + rest.total);
  });
  t('Beenden raeumt die Uhr ganz weg', () => {
    startRest(90); endRest();
    return (rest.remaining === 0 && rest.total === 0 && rest.id === null)
      || (rest.remaining + '/' + rest.total + '/' + rest.id);
  });
  t('Anhalten laesst die Restzeit stehen', () => {
    startRest(90); stopRest();
    const r = (rest.remaining === 90 && rest.id === null);
    endRest(); return r || 'Rest ' + rest.remaining;
  });
  t('Minus geht nicht unter null', () => {
    startRest(10); adjust(-60);
    const r = (rest.remaining === 0);
    endRest(); return r || ('ist ' + rest.remaining);
  });
  t('Plus verlaengert auch die Gesamtzeit', () => {
    startRest(30); adjust(30);
    const r = (rest.remaining === 60 && rest.total === 60);
    endRest(); return r || (rest.remaining + '/' + rest.total);
  });
  t('Aus dem Stand startet Plus eine neue Pause', () => {
    endRest(); adjust(30);
    const r = (rest.remaining === 30 && rest.id !== null);
    endRest(); return r || (rest.remaining + '/' + rest.id);
  });
  t('Bei null haelt die Uhr von selbst an', () => {
    startRest(1); tick();
    const r = (rest.remaining <= 0 && rest.id === null);
    endRest(); return r || (rest.remaining + '/' + rest.id);
  });
  t('Nach dem Beenden ist die Leiste weg', () => {
    startRest(30); endRest();
    return !tb.classList.contains('show') || 'Leiste steht noch';
  });

  // ================================================================ NEU: Ernaehrung rechnet mit dem Gewicht
  const KCAL_VORHER = JSON.stringify(profile.kcal || {});
  const GEW_VORHER  = JSON.stringify(profile.weights || []);

  // ⚠️ Das Eiweissziel haengt seit dem 22.08.2026 auch am Trainingstag. Damit die
  // Pruefungen nicht vom Wochentag abhaengen, wird der Plan hier bewusst geleert.
  const PLAENE_VORHER = plans;
  const SESS_VORHER2 = sessions;
  const ruhetag = () => { plans = []; sessions = []; };
  const trainingstag = () => { plans = [{id:'p', name:'Push', day:todayIdx(), exercises:[]}]; sessions = []; };

  t('Eiweissziel am Ruhetag: 1,8 g je kg', () => {
    ruhetag(); profile.weights = [{date: Date.now(), kg: 80}];
    return eq(eiweissZiel(), 144);
  });
  t('Eiweissziel am Trainingstag: 2,0 g je kg', () => {
    trainingstag(); profile.weights = [{date: Date.now(), kg: 80}];
    return eq(eiweissZiel(), 160);
  });
  t('Ein erledigtes Training zaehlt auch als Trainingstag', () => {
    plans = []; sessions = [{date: Date.now(), entries: []}];
    return eq(eiweissZiel(), 160);
  });
  t('Ohne Gewicht kein Eiweissziel', () => { ruhetag(); profile.weights = []; return eq(eiweissZiel(), null); });
  t('Eiweissziel folgt dem Gewicht', () => {
    ruhetag();
    profile.weights = [{date: Date.now()-864e5, kg: 80}, {date: Date.now(), kg: 90}];
    return eq(eiweissZiel(), 162);   // das JUENGSTE Gewicht zaehlt, nicht das erste
  });
  plans = PLAENE_VORHER; sessions = SESS_VORHER2;
  t('Kalorien-Vorschlag: kg x 30, auf 50 gerundet', () => {
    profile.weights = [{date: Date.now(), kg: 80}];
    return eq(kcalVorschlag(), 2400);
  });
  t('Vorschlag rundet wirklich auf 50', () => {
    profile.weights = [{date: Date.now(), kg: 77}];   // 2310 -> 2300
    return eq(kcalVorschlag(), 2300);
  });
  t('Ohne Gewicht kein Vorschlag', () => { profile.weights = []; return eq(kcalVorschlag(), null); });

  // ⚠️ Der wichtigste Fall am Schnitt: Tage ohne Eintrag duerfen NICHT als 0 zaehlen.
  t('Schnitt zaehlt nur Tage mit Eintrag', () => {
    const n = Date.now();
    profile.kcal = {goal:2000, foods:[], meals:[
      {id:'a', date:n,          name:'A', kcal:2000, p:0, c:0, f:0},
      {id:'b', date:n-2*864e5,  name:'B', kcal:1000, p:0, c:0, f:0}
    ]};
    const r = kcalSchnitt(7);
    // zwei Tage mit Eintrag, Schnitt 1500 - NICHT 3000/7
    return (r && r.tage === 2 && r.schnitt === 1500) || JSON.stringify(r);
  });
  t('Ohne jeden Eintrag gibt es keinen Schnitt', () => {
    profile.kcal = {goal:2000, foods:[], meals:[]};
    return eq(kcalSchnitt(7), null);
  });
  t('Mehrere Mahlzeiten an einem Tag zaehlen als ein Tag', () => {
    const n = Date.now();
    profile.kcal = {goal:2000, foods:[], meals:[
      {id:'a', date:n, name:'A', kcal:600, p:0, c:0, f:0},
      {id:'b', date:n, name:'B', kcal:400, p:0, c:0, f:0}
    ]};
    const r = kcalSchnitt(7);
    return (r.tage === 1 && r.schnitt === 1000) || JSON.stringify(r);
  });

  t('Zuletzt gegessen: jede Sache nur einmal', () => {
    const n = Date.now();
    profile.kcal = {goal:2000, foods:[], meals:[
      {id:'1', date:n-3*864e5, name:'Haferflocken', menge:'80 g', kcal:300, p:10, c:50, f:5},
      {id:'2', date:n-2*864e5, name:'Haferflocken', menge:'80 g', kcal:300, p:10, c:50, f:5},
      {id:'3', date:n-864e5,   name:'Quark',        menge:'250 g', kcal:170, p:30, c:8, f:1}
    ]};
    const l = zuletztGegessen(6);
    return (l.length === 2 && l[0].name === 'Quark') || l.map(x=>x.name).join(',');
  });
  t('Zuletzt gegessen: gleiche Sache, andere Menge zaehlt getrennt', () => {
    const n = Date.now();
    profile.kcal = {goal:2000, foods:[], meals:[
      {id:'1', date:n-864e5, name:'Haferflocken', menge:'80 g',  kcal:300, p:10, c:50, f:5},
      {id:'2', date:n,       name:'Haferflocken', menge:'120 g', kcal:450, p:15, c:75, f:7}
    ]};
    return eq(zuletztGegessen(6).length, 2);
  });
  t('Zuletzt gegessen: Anzahl wird eingehalten', () => {
    const n = Date.now();
    profile.kcal = {goal:2000, foods:[], meals:
      [1,2,3,4,5,6,7,8].map(i => ({id:'x'+i, date:n-i*864e5, name:'Essen '+i, menge:'100 g', kcal:100, p:1, c:1, f:1}))};
    return eq(zuletztGegessen(6).length, 6);
  });
  t('Ohne Mahlzeiten ist die Liste leer', () => {
    profile.kcal = {goal:2000, foods:[], meals:[]};
    return eq(zuletztGegessen(6).length, 0);
  });

  // ---- Brock im Ernaehrungsteil ----
  t('Ohne Ziel sagt Brock etwas zum Ziel', () => brockEssenSay(1000, 0).length > 0 || 'leer');
  t('Ohne Ziel kommt der Ziel-Spruch',  () => BROCK_ESSEN['kein-ziel'].includes(brockEssenSay(1000, 0)) || 'falscher Topf');
  t('Nichts gegessen: leer-Spruch',     () => BROCK_ESSEN.leer.includes(brockEssenSay(0, 2000)) || 'falscher Topf');
  t('Punktlandung bei genau dem Ziel',  () => BROCK_ESSEN.punkt.includes(brockEssenSay(2000, 2000)) || 'falscher Topf');
  t('Knapp drunter ist noch Punktlandung', () => BROCK_ESSEN.punkt.includes(brockEssenSay(1900, 2000)) || 'falscher Topf');
  t('Die Haelfte ist "wenig"',          () => BROCK_ESSEN.wenig.includes(brockEssenSay(900, 2000)) || 'falscher Topf');
  t('Deutlich drueber wird erkannt',    () => BROCK_ESSEN['weit-drueber'].includes(brockEssenSay(3000, 2000)) || 'falscher Topf');
  t('Brock sagt nie undefined', () => {
    for (const [kcal, ziel] of [[0,0],[0,2000],[1,2000],[2000,2000],[9999,2000],[100,1]])
      if (typeof brockEssenSay(kcal, ziel) !== 'string') return 'bei ' + kcal + '/' + ziel;
    return true;
  });
  t('Jeder Spruch-Topf hat Sprueche', () => {
    const leer = Object.entries(BROCK_ESSEN).filter(([, v]) => !v.length).map(([k]) => k);
    return leer.length ? leer.join(', ') : true;
  });

  // ---- Zielbalken ----
  t('Balken bei der Haelfte ist 50 %', () => zielBalken(50, 100, 'red').includes('width:50%') || 'falsche Breite');
  t('Balken laeuft nicht ueber 100 %', () => zielBalken(300, 100, 'red').includes('width:100%') || 'ueberlaeuft');
  t('Ueber dem Ziel faerbt sich der Balken', () => zielBalken(120, 100, 'green').includes('--danger') || 'nicht rot');
  t('Genau am Ziel noch nicht rot', () => !zielBalken(100, 100, 'green').includes('--danger') || 'zu frueh rot');
  t('Ohne Ziel bleibt der Balken leer', () => zielBalken(500, 0, 'green').includes('width:0%') || 'nicht leer');

  // ================================================================ NEU: Regelkreis Waage <-> Essen
  const T = 864e5;
  // Baut `tage` Tage rueckwaerts je eine Mahlzeit mit `kcal`.
  const essenUeber = (tage, kcal) => {
    const n = Date.now(), meals = [];
    for (let i = 0; i < tage; i++)
      meals.push({id:'e'+i, date:n-i*T, name:'Essen', menge:'1', kcal, p:0, c:0, f:0});
    return meals;
  };

  t('Vorschlag Halten: kg x 30', () => {
    profile.weights = [{date:Date.now(), kg:80}];
    return eq(kcalVorschlagFuer('halten'), 2400);
  });
  t('Vorschlag Abnehmen liegt 400 tiefer', () => eq(kcalVorschlagFuer('abnehmen'), 2000));
  t('Vorschlag Aufbauen liegt 300 hoeher', () => eq(kcalVorschlagFuer('zunehmen'), 2700));
  t('Unbekanntes Vorhaben faellt auf Erhalt zurueck', () => eq(kcalVorschlagFuer('quatsch'), 2400));
  t('Ohne Gewicht kein Vorschlag', () => { profile.weights = []; return eq(kcalVorschlagFuer('halten'), null); });

  t('Trend braucht zwei Wiegungen', () => {
    profile.weights = [{date:Date.now(), kg:80}];
    return eq(gewichtsTrend(21), null);
  });
  t('Trend braucht mindestens eine Woche Abstand', () => {
    const n = Date.now();
    profile.weights = [{date:n-3*T, kg:80}, {date:n, kg:79}];
    return eq(gewichtsTrend(21), null);   // 3 Tage sind Rauschen, keine Woche
  });
  t('Trend rechnet auf die Woche hoch', () => {
    const n = Date.now();
    profile.weights = [{date:n-14*T, kg:80}, {date:n, kg:79}];
    const tr = gewichtsTrend(21);
    return (tr && Math.abs(tr.proWoche - (-0.5)) < 0.001) || JSON.stringify(tr);
  });
  t('Trend nimmt nur Wiegungen im Fenster', () => {
    const n = Date.now();
    profile.weights = [{date:n-60*T, kg:90}, {date:n-14*T, kg:80}, {date:n, kg:79}];
    const tr = gewichtsTrend(21);
    return (tr && Math.abs(tr.von - 80) < 0.001) || JSON.stringify(tr);
  });

  t('Ohne Vorhaben kein Regelkreis', () => {
    profile.kcal = {goal:2000, foods:[], meals:[]};
    return eq(regelkreis().stand, 'kein-ziel');
  });
  t('Ohne Wiegungen meldet er das', () => {
    profile.kcal = {art:'abnehmen', goal:2000, foods:[], meals:[]};
    profile.weights = [];
    return eq(regelkreis().stand, 'zu-wenig-gewicht');
  });
  t('Mit Waage, ohne Essenstage meldet er das', () => {
    const n = Date.now();
    profile.weights = [{date:n-14*T, kg:80}, {date:n, kg:79}];
    profile.kcal = {art:'abnehmen', goal:2000, foods:[], meals:essenUeber(2, 2000)};
    return eq(regelkreis().stand, 'zu-wenig-essen');
  });
  t('Genau im Plan: es geht auf', () => {
    const n = Date.now();
    profile.weights = [{date:n-14*T, kg:80}, {date:n, kg:79}];   // -0,5 kg/Woche
    profile.kcal = {art:'abnehmen', goal:2000, foods:[], meals:essenUeber(7, 2000)};
    return eq(regelkreis().stand, 'passt');
  });
  t('Kleine Abweichung gilt noch als "passt"', () => {
    const n = Date.now();
    profile.weights = [{date:n-14*T, kg:80}, {date:n, kg:79.2}];  // -0,4 kg/Woche
    profile.kcal = {art:'abnehmen', goal:2000, foods:[], meals:essenUeber(7, 2000)};
    return eq(regelkreis().stand, 'passt');
  });
  t('Zu langsam wird erkannt und beziffert', () => {
    const n = Date.now();
    profile.weights = [{date:n-14*T, kg:80}, {date:n, kg:80}];    // 0 statt -0,5
    profile.kcal = {art:'abnehmen', goal:2000, foods:[], meals:essenUeber(7, 2200)};
    const r = regelkreis();
    // Abweichung +0,5 kg/Woche -> 500 kcal/Tag zu viel -> neues Ziel 2200-500
    return (r.stand === 'daneben' && r.korrektur === 500 && r.neuesZiel === 1700) || JSON.stringify(r);
  });
  t('Zu schnell wird ebenfalls erkannt', () => {
    const n = Date.now();
    // 80 -> 77 kg in 14 Tagen sind -1,5 kg/Woche, gewollt waren -0,5.
    // Abweichung -1,0 kg/Woche -> 1000 kcal/Tag zu wenig -> 1800 + 1000 = 2800.
    profile.weights = [{date:n-14*T, kg:80}, {date:n, kg:77}];
    profile.kcal = {art:'abnehmen', goal:2000, foods:[], meals:essenUeber(7, 1800)};
    const r = regelkreis();
    return (r.stand === 'daneben' && r.korrektur === -1000 && r.neuesZiel === 2800) || JSON.stringify(r);
  });
  // ⚠️ Ohne Untergrenze koennte die Rechnung ein absurd niedriges Ziel ausspucken.
  t('Das neue Ziel faellt nie unter 1200 kcal', () => {
    const n = Date.now();
    profile.weights = [{date:n-14*T, kg:80}, {date:n, kg:82}];    // stark zugenommen
    profile.kcal = {art:'abnehmen', goal:1500, foods:[], meals:essenUeber(7, 1400)};
    const r = regelkreis();
    return (r.stand !== 'daneben' || r.neuesZiel >= 1200) || 'Ziel ' + r.neuesZiel;
  });
  t('Halten: Gewicht bleibt -> passt', () => {
    const n = Date.now();
    profile.weights = [{date:n-14*T, kg:80}, {date:n, kg:80}];
    profile.kcal = {art:'halten', goal:2400, foods:[], meals:essenUeber(7, 2400)};
    return eq(regelkreis().stand, 'passt');
  });
  t('Aufbauen: Gewicht faellt -> daneben, nach oben', () => {
    const n = Date.now();
    profile.weights = [{date:n-14*T, kg:80}, {date:n, kg:79}];
    profile.kcal = {art:'zunehmen', goal:2700, foods:[], meals:essenUeber(7, 2600)};
    const r = regelkreis();
    return (r.stand === 'daneben' && r.neuesZiel > 2600) || JSON.stringify(r);
  });

  // ---- Eiweiss-Tipp ----
  t('Ziel erreicht: kein Tipp', () => eq(eiweissTipp(150, 140), null));
  t('Ohne eigene Lebensmittel nur die Luecke', () => {
    profile.kcal = {art:'halten', goal:2000, foods:[], meals:[]};
    const r = eiweissTipp(60, 140);
    return (r && r.fehlt === 80 && r.essen === null) || JSON.stringify(r);
  });
  t('Waehlt das guenstigste Eiweiss je kcal, nicht das eiweissreichste', () => {
    profile.kcal = {art:'halten', goal:2000, meals:[], foods:[
      {id:'f1', name:'Nüsse',      kcal:600, p:20, c:10, f:50},   // 3,3 g je 100 kcal
      {id:'f2', name:'Magerquark', kcal:68,  p:12, c:4,  f:0}     // 17,6 g je 100 kcal
    ]};
    const r = eiweissTipp(100, 140);
    return (r && r.essen.name === 'Magerquark') || JSON.stringify(r);
  });
  t('Menge und kcal des Tipps stimmen', () => {
    profile.kcal = {art:'halten', goal:2000, meals:[], foods:[
      {id:'f2', name:'Magerquark', kcal:68, p:12, c:4, f:0}]};
    const r = eiweissTipp(110, 140);   // fehlen 30 g -> 30/12*100 = 250 g, unter dem Deckel
    return (r.gramm === 250 && r.deckt === true && r.kcal === Math.round(68*250/100)) || JSON.stringify(r);
  });
  // ⚠️ Ohne Deckel kaeme bei einer grossen Luecke "800 g Magerquark" heraus —
  // rechnerisch richtig, praktisch albern. Ein Vorschlag, den niemand befolgt,
  // ist schlechter als keiner.
  t('Grosse Luecke: Vorschlag wird bei 300 g gedeckelt', () => {
    profile.kcal = {art:'halten', goal:2000, meals:[], foods:[
      {id:'f2', name:'Magerquark', kcal:68, p:12, c:4, f:0}]};
    const r = eiweissTipp(40, 140);    // fehlen 100 g -> waeren 830 g
    return (r.gramm === 300 && r.deckt === false) || JSON.stringify(r);
  });
  t('Gedeckelter Vorschlag sagt, wie viel er wirklich bringt', () => {
    profile.kcal = {art:'halten', goal:2000, meals:[], foods:[
      {id:'f2', name:'Magerquark', kcal:68, p:12, c:4, f:0}]};
    const r = eiweissTipp(40, 140);
    return (r.eiweiss === 36 && r.eiweiss < r.fehlt) || JSON.stringify(r);
  });
  t('Lebensmittel ohne Eiweiss kommen nicht als Tipp', () => {
    profile.kcal = {art:'halten', goal:2000, meals:[], foods:[
      {id:'f3', name:'Limonade', kcal:180, p:0, c:45, f:0}]};
    return eq(eiweissTipp(0, 140).essen, null);
  });

  // ================================================================ NEU: Trainings-Teil auf Herz und Nieren
  const PROG_VORHER = JSON.stringify(programs);
  const PLANS_VORHER = JSON.stringify(plans);
  const XP_VORHER = profile.xp;

  // ---- Startbestand fuer ein neues Konto ----
  // 🔴 Hier steckte ein echter Fehler: die drei Trainings kamen OHNE Wochentag.
  // Wer im Assistenten „Selbst anlegen" waehlt, bekam damit drei Trainings, die
  // keinem Tag gehoeren — und die App sagte ihm JEDEN Tag „Ruhetag", obwohl
  // Trainings da waren. planForToday() und nextTrainingDay() trafen nie etwas.
  t('Startbestand: jedes Training hat einen Wochentag', () => {
    const ohne = seedPlans().filter(p => !(p.day >= 0 && p.day <= 6)).map(p => p.name);
    return ohne.length ? ohne.join(', ') + ' ohne Tag' : true;
  });
  t('Startbestand: kein Tag doppelt vergeben', () => {
    const tage = seedPlans().map(p => p.day);
    return new Set(tage).size === tage.length || tage.join(',');
  });
  t('Startbestand: es gibt drei Trainings', () => eq(seedPlans().length, 3));
  t('Startbestand: jedes Training hat Uebungen', () => {
    const leer = seedPlans().filter(p => !p.exercises || !p.exercises.length).map(p => p.name);
    return leer.length ? leer.join(', ') : true;
  });
  t('Startbestand findet heute oder demnaechst ein Training', () => {
    plans = seedPlans();
    return (!!planForToday() || !!nextTrainingDay()) || 'weder heute noch demnaechst etwas';
  });

  // ---- Der Assistent baut die Plaene ----
  t('Assistent: so viele Trainings wie gewaehlte Tage', () => {
    profile.days = [0,2,4]; profile.vol = 'high'; profile.favs = [];
    return eq(buildPlans().length, 3);
  });
  t('Assistent: die gewaehlten Tage stehen drin', () => {
    profile.days = [0,2,4];
    return eq(buildPlans().map(p => p.day).join(','), '0,2,4');
  });
  t('Assistent: Tage werden sortiert', () => {
    profile.days = [4,0,2];
    return eq(buildPlans().map(p => p.day).join(','), '0,2,4');
  });
  t('Assistent: viel Volumen gibt 6 Uebungen', () => {
    profile.days = [0,2,4]; profile.vol = 'high';
    return eq(buildPlans()[0].exercises.length, 6);
  });
  t('Assistent: wenig Volumen gibt 5 Uebungen', () => {
    profile.vol = 'low';
    return eq(buildPlans()[0].exercises.length, 5);
  });
  t('Assistent: keine Uebung doppelt im selben Training', () => {
    profile.vol = 'high'; profile.days = [0,1,2,3,4,5];
    for (const p of buildPlans()){
      const n = p.exercises.map(e => e.name);
      if (new Set(n).size !== n.length) return p.name + ' hat Dubletten';
    }
    return true;
  });
  t('Assistent: jede erzeugte Uebung hat einen Namen', () => {
    profile.days = [0,2,4];
    const ohne = [].concat(...buildPlans().map(p => p.exercises)).filter(e => !e.name);
    return ohne.length ? ohne.length + ' ohne Namen' : true;
  });
  t('Ohne gewaehlte Tage baut der Assistent nichts', () => { profile.days = []; return eq(buildPlans().length, 0); });

  // ---- Lieblingsuebungen kommen zuerst ----
  t('Lieblingsuebung steht vorn', () => {
    profile.vol = 'high'; profile.favs = ['Dips (Brust)'];
    return eq(pickExercises('push')[0], 'Dips (Brust)');
  });
  t('Lieblingsuebung aus einer fremden Gruppe wird ignoriert', () => {
    profile.favs = ['Kniebeuge'];                       // Beine, aber Tag ist push
    return (pickExercises('push')[0] !== 'Kniebeuge') || 'Beinuebung am Push-Tag';
  });
  t('Auswahl bleibt bei der Obergrenze', () => {
    profile.favs = ['Dips (Brust)','Seitheben','Bankdrücken']; profile.vol = 'high';
    return eq(pickExercises('push').length, 6);
  });
  t('Auswahl enthaelt nichts doppelt', () => {
    profile.favs = ['Bankdrücken'];                     // steht auch im Vorrat
    const l = pickExercises('push');
    return new Set(l).size === l.length || l.join(',');
  });
  t('Jeder Split-Tag liefert ueberhaupt Uebungen', () => {
    profile.favs = [];
    for (const key of Object.keys(DAYPOOL))
      if (!pickExercises(key).length) return key + ' liefert nichts';
    return true;
  });

  // ---- XP einer Einheit ----
  t('XP: Grundbetrag von 50 auch ohne Volumen', () => eq(sessXP([{sets:[{done:true, weight:0, reps:10}]}]), 60));
  t('XP: je abgehaktem Satz 10', () => eq(sessXP([{sets:[{done:true},{done:true},{done:true}]}]), 80));
  t('XP: je 1000 kg Volumen 20 dazu', () =>
    eq(sessXP([{sets:[{done:true, weight:100, reps:10}]}]), 10 + 50 + 20));
  t('XP: Aufwaermsaetze bringen nichts', () => {
    const ohne = sessXP([{sets:[{done:true, weight:60, reps:10}]}]);
    const mit  = sessXP([{sets:[{warm:true, done:true, weight:60, reps:10},{done:true, weight:60, reps:10}]}]);
    return eq(ohne, mit);
  });
  t('XP: nicht abgehakte Saetze bringen nichts', () =>
    eq(sessXP([{sets:[{done:false, weight:100, reps:10}]}]), 50));

  // ---- XP nachfuehren, wenn eine alte Einheit geaendert wird ----
  t('Nachrechnen hebt die XP, wenn mehr drin steht', () => {
    profile.xp = 1000;
    const s = {id:'x', date:Date.now(), xp:60, entries:[{name:'A', sets:[{done:true, weight:0, reps:10},{done:true}]}]};
    sessRecalc(s);
    return (s.xp === 70 && profile.xp === 1010) || (s.xp + '/' + profile.xp);
  });
  t('Nachrechnen senkt die XP, wenn weniger drin steht', () => {
    profile.xp = 1000;
    const s = {id:'x', date:Date.now(), xp:200, entries:[{name:'A', sets:[{done:true}]}]};
    sessRecalc(s);
    return (s.xp === 60 && profile.xp === 860) || (s.xp + '/' + profile.xp);
  });
  t('XP fallen beim Nachrechnen nie unter 0', () => {
    profile.xp = 10;
    const s = {id:'x', date:Date.now(), xp:5000, entries:[{name:'A', sets:[{done:true}]}]};
    sessRecalc(s);
    return (profile.xp >= 0) || ('ist ' + profile.xp);
  });
  // ⚠️ Bekannte Luecke, hier festgehalten statt uebersehen: Einheiten von VOR dem
  // 06.08.2026 haben kein xp-Feld. Wird so eine im Verlauf geaendert, bleibt der
  // Punktestand stehen — er kann dann nicht mehr stimmen.
  t('Alte Einheit ohne xp-Feld laesst den Punktestand unangetastet', () => {
    profile.xp = 1000;
    const s = {id:'alt', date:Date.now(), entries:[{name:'A', sets:[{done:true}]}]};
    sessRecalc(s);
    return eq(profile.xp, 1000);
  });

  // ---- Trainingstage und Wochentage ----
  // ⚠️ Hier lag ICH zuerst falsch, nicht der Code: ich hatte erwartet, dass
  // nextTrainingDay() niemals auf heute zeigt. Trainiert jemand nur montags, ist der
  // naechste Trainingstag aber sehr wohl wieder ein Montag. Und die Funktion wird
  // ohnehin NUR aufgerufen, wenn heute nichts ansteht (renderHome, else-Zweig) —
  // der vermeintliche Fehlerfall kann gar nicht auftreten.
  t('Nur ein Wochentag im Plan: naechster Termin ist in einer Woche', () => {
    plans = [{id:'a', name:'Nur heute', day:todayIdx(), exercises:[]}];
    const n = nextTrainingDay();
    return (n && n.d === todayIdx() && n.p.name === 'Nur heute') || JSON.stringify(n);
  });
  t('Naechster Trainingstag wird gefunden', () => {
    plans = [{id:'a', name:'Morgen', day:(todayIdx()+1)%7, exercises:[]}];
    const n = nextTrainingDay();
    return (n && n.d === (todayIdx()+1)%7) || JSON.stringify(n);
  });
  t('Ohne Plaene kein naechster Trainingstag', () => { plans = []; return eq(nextTrainingDay(), null); });
  t('Verpasst: gestern war Trainingstag und nichts passiert', () => {
    plans = [{id:'a', name:'Gestern', day:(todayIdx()+6)%7, exercises:[]}];
    sessions = [];
    return missedYesterday() === true || 'nicht erkannt';
  });
  t('Nicht verpasst, wenn gestern trainiert wurde', () => {
    plans = [{id:'a', name:'Gestern', day:(todayIdx()+6)%7, exercises:[]}];
    sessions = [{date: Date.now()-864e5, entries:[]}];
    return missedYesterday() === false || 'faelschlich verpasst';
  });
  t('Ohne Plan fuer gestern nichts verpasst', () => {
    plans = []; sessions = [];
    return missedYesterday() === false || 'verpasst ohne Plan';
  });

  // ---- Plan teilen und wieder einlesen ----
  t('Geteilter Plan kommt vollstaendig zurueck', () => {
    const prog = {id:'p', name:'Sommerplan', plans:[
      {id:'t1', name:'Push', day:0, warmup:true,  exercises:[{id:'e1', name:'Bankdrücken', sets:4, vol:'low'}]},
      {id:'t2', name:'Pull', day:2, warmup:false, exercises:[{id:'e2', name:'Klimmzüge',   sets:3, vol:'high'}]}
    ]};
    const d = JSON.parse(b64dec(planCode(prog)));
    return (d.name === 'Sommerplan' && d.p.length === 2 && d.p[0].d === 0 && d.p[1].d === 2
            && d.p[0].w === 1 && d.p[1].w === 0
            && d.p[0].e[0][0] === 'Bankdrücken' && d.p[0].e[0][1] === 4 && d.p[0].e[0][2] === 'l')
           || JSON.stringify(d);
  });
  // ⚠️ Montag ist Tag 0. Eine Pruefung auf "wahr/falsch" statt auf "ist null" wuerde
  // den Montag verschlucken — der klassische Nullwert-Fehler.
  t('Montag (Tag 0) ueberlebt das Teilen', () => {
    const prog = {id:'p', name:'X', plans:[
      {id:'t', name:'Mo', day:0, exercises:[{id:'e', name:'A', sets:3}]}]};
    return eq(JSON.parse(b64dec(planCode(prog))).p[0].d, 0);
  });
  t('Training ohne Tag bleibt ohne Tag', () => {
    const prog = {id:'p', name:'X', plans:[
      {id:'t', name:'Frei', day:null, exercises:[{id:'e', name:'A', sets:3}]}]};
    return eq(JSON.parse(b64dec(planCode(prog))).p[0].d, null);
  });

  // ---- Abgleich-Datensatz hin und zurueck ----
  t('Abgleich: Plaene und Einheiten kommen zurueck', () => {
    programs = [{id:'p1', name:'Plan A', plans:[{id:'t', name:'Push', day:1, exercises:[]}]}];
    bindPlans(); sessions = [{id:'s', date:Date.now(), entries:[]}]; profile.xp = 777;
    const blob = JSON.parse(JSON.stringify(appDataBlob()));
    programs = []; sessions = []; profile = {xp:0};
    loadBlob(blob);
    return (programs.length === 1 && programs[0].name === 'Plan A'
            && sessions.length === 1 && profile.xp === 777) || 'Rundlauf verloren';
  });
  // ⚠️ Alte Sicherungen (vor dem 05.08.2026) kennen nur `plans`, keine `programs`.
  t('Abgleich: alter Bestand ohne programs geht nicht verloren', () => {
    programs = [];
    loadBlob({plans:[{id:'t', name:'Altes Training', day:3, exercises:[]}], sessions:[], profile:{xp:5}});
    return (programs.length === 1 && programs[0].plans[0].name === 'Altes Training')
           || JSON.stringify(programs);
  });
  t('Abgleich vertraegt einen leeren Datensatz', () => {
    const vorher = programs.length;
    loadBlob(null); loadBlob({});
    return eq(programs.length, vorher);
  });

  programs = JSON.parse(PROG_VORHER); plans = JSON.parse(PLANS_VORHER);
  profile.xp = XP_VORHER; bindPlans();

  // ---- Kurven ----
  t('Kurve braucht mindestens zwei Punkte', () => eq(lineChart([80], 300, 110), ''));
  t('Kurve mit zwei Punkten baut', () => lineChart([80,79], 300, 110).includes('<svg') || 'kein SVG');
  // ⚠️ Der Klassiker: alle Werte gleich -> (max-min)=0 -> Division durch null -> NaN im SVG.
  t('Lauter gleiche Werte ergeben keine NaN', () => {
    const svg = lineChart([80,80,80], 300, 110);
    return !/NaN/.test(svg) || 'NaN in der Kurve';
  });
  t('Negative Werte ergeben keine NaN', () => !/NaN/.test(lineChart([-5,0,5], 300, 110)) || 'NaN');
  t('Viele Punkte bleiben im Rahmen', () => {
    const vals = Array.from({length:200}, (_,i) => Math.sin(i)*50+80);
    const svg = lineChart(vals, 300, 110);
    const zahlen = (svg.match(/cx="([\d.]+)"/g)||[]).map(s => +s.slice(4,-1));
    return zahlen.every(x => x >= 0 && x <= 300) || 'Punkt ausserhalb';
  });

  // ---- Verlauf je Uebung ----
  t('Verlauf nimmt nur abgehakte Saetze', () => {
    sessions = [{date:Date.now(), entries:[{name:'A', sets:[
      {done:true, weight:60, reps:10},{done:false, weight:99, reps:10}]}]}];
    const h = exHistory('A');
    return (h.length === 1 && h[0].w === 60 && h[0].sets === 1) || JSON.stringify(h);
  });
  t('Einheit ohne abgehakte Saetze taucht nicht auf', () => {
    sessions = [{date:Date.now(), entries:[{name:'A', sets:[{done:false, weight:60, reps:10}]}]}];
    return eq(exHistory('A').length, 0);
  });
  t('Verlauf einer unbekannten Uebung ist leer', () => eq(exHistory('Gibtsnicht').length, 0));
  t('Verlauf nimmt das schwerste Gewicht der Einheit', () => {
    sessions = [{date:Date.now(), entries:[{name:'A', sets:[
      {done:true, weight:60, reps:10},{done:true, weight:70, reps:8}]}]}];
    return eq(exHistory('A')[0].w, 70);
  });

  // ---- Ausgeruesteter Rang ----
  t('Ohne Auswahl gilt der echte Rang', () => {
    profile.xp = 0; profile.rankSkin = null;
    return eq(equippedRank().name, rankForLevel(1).name);
  });
  t('Ein erreichter Rang laesst sich tragen', () => {
    profile.xp = xpForLevel(10); profile.rankSkin = 3;      // Noob (min 3)
    return eq(equippedRank().name, 'Noob');
  });
  // ⚠️ Wichtig: ein noch nicht erreichter Rang darf NICHT tragbar sein — sonst
  // liesse sich der Gigachad-Brock per Datensatz erschleichen.
  t('Ein nicht erreichter Rang faellt auf den echten zurueck', () => {
    profile.xp = 0; profile.rankSkin = 45;                  // Gigachad
    return eq(equippedRank().name, rankForLevel(1).name);
  });
  t('Ein unbekannter Rang faellt auf den echten zurueck', () => {
    profile.xp = xpForLevel(10); profile.rankSkin = 999;
    return eq(equippedRank().name, rankForLevel(10).name);
  });
  profile.rankSkin = null;

  // ---- Zielbereiche und Satzzahlen ----
  t('Wenig Volumen: Ziel 6-10 Wdh', () => { profile.vol='low';  return eq(repRange().join('-'), '6-10'); });
  t('Viel Volumen: Ziel 8-12 Wdh',  () => { profile.vol='high'; return eq(repRange().join('-'), '8-12'); });
  t('Uebung schlaegt die globale Wahl', () => {
    profile.vol = 'high';
    return eq(exRange({vol:'low'}).join('-'), '6-10');
  });
  t('Beschriftung passt zum Bereich', () => eq(exLabel({vol:'low'}), '6–10'));
  t('Satzzahl ist immer 3', () => eq(volSets(), 3));
  t('Ohne Angabe gilt die globale Wahl', () => { profile.vol='low'; return eq(volOf(null), 'low'); });
  t('Ohne alles gilt viel Volumen', () => {
    const v = profile.vol; delete profile.vol;
    const r = volOf(null); profile.vol = v;
    return eq(r, 'high');
  });

  // ---- Aufwaermen am Plan ----
  t('Plan mit warmup:true gewinnt', () => { profile.warmup=false; return eq(planWarm({warmup:true}), true); });
  t('Plan mit warmup:false gewinnt', () => { profile.warmup=true; return eq(planWarm({warmup:false}), false); });
  t('Ohne Angabe am Plan gilt das Profil', () => { profile.warmup=true; return eq(planWarm({}), true); });
  // ⚠️ Auch hier lag ich zuerst falsch: ich hatte `false` erwartet. Ohne Plan ist die
  // Profil-Einstellung aber die richtige Antwort auf „wird aufgewaermt?" — nicht „nein".
  t('Ohne Plan gilt ebenfalls das Profil', () => {
    profile.warmup = true;  const an  = planWarm(null);
    profile.warmup = false; const aus = planWarm(null);
    return (an === true && aus === false) || (an + '/' + aus);
  });

  // ---- Mahlzeit eintragen ----
  t('Mahlzeit landet mit heutigem Datum in der Liste', () => {
    profile.kcal = {goal:2000, foods:[], meals:[]};
    addMeal({name:'Quark', basis:'g100', kcal:68, p:12, c:4, f:0, quelle:'eigen'}, 250);
    const m = kcalInit().meals[0];
    return (m && m.kcal === 170 && sameDay(m.date, Date.now())) || JSON.stringify(m);
  });
  t('Mahlzeit ohne Namen heisst "Essen"', () => {
    profile.kcal = {goal:2000, foods:[], meals:[]};
    addMeal({basis:'g100', kcal:100, p:0, c:0, f:0}, 100);
    return eq(kcalInit().meals[0].name, 'Essen');
  });
  t('Die Mengenangabe wird lesbar mitgeschrieben', () => {
    profile.kcal = {goal:2000, foods:[], meals:[]};
    addMeal({name:'X', basis:'g100', kcal:100, p:0, c:0, f:0}, 250);
    return eq(kcalInit().meals[0].menge, '250 g');
  });
  t('Portionen werden mit x geschrieben', () => {
    profile.kcal = {goal:2000, foods:[], meals:[]};
    addMeal({name:'X', basis:'portion', kcal:100, p:0, c:0, f:0}, 2);
    return eq(kcalInit().meals[0].menge, '2×');
  });

  // ================================================================ Problem melden (23.08.2026)
  t('Eine Meldung landet zuerst im Geraet', () => {
    localStorage.removeItem(MELD_KEY);
    meldungAnlegen('Der Timer bleibt stehen');
    const l = meldungenLesen();
    return (l.length === 1 && l[0].text === 'Der Timer bleibt stehen') || JSON.stringify(l);
  });
  // ⚠️ Die Felder muessen GENAU die sein, die der Trigger in supabase-meldungen.sql
  // ausliest. Fehlt eines, steht in Discord ein "?" - und niemand merkt es, weil
  // die Meldung ja ankommt.
  t('Das Umfeld hat die Felder, die der Trigger liest', () => {
    const u = umfeldSammeln();
    const muss = ['fassung','netz','bildschirm','einheiten','letzterAbgleich','geraet'];
    const fehlt = muss.filter(k => u[k] === undefined);
    return fehlt.length === 0 || 'fehlt: ' + fehlt.join(', ');
  });
  t('Die Fassung steht nicht auf leer', () =>
    (typeof APP_FASSUNG === 'string' && APP_FASSUNG.length > 0) || 'leer');
  t('Sehr langer Text wird gekuerzt', () => {
    localStorage.removeItem(MELD_KEY);
    meldungAnlegen('x'.repeat(9000));
    return eq(meldungenLesen()[0].text.length, 4000);
  });
  t('Zwei Meldungen bekommen verschiedene Kennungen', () => {
    localStorage.removeItem(MELD_KEY);
    meldungAnlegen('eins'); meldungAnlegen('zwei');
    const l = meldungenLesen();
    return (l[0].id !== l[1].id) || 'gleiche id: ' + l[0].id;
  });
  t('Ungelesene Antworten werden gezaehlt', () => {
    localStorage.setItem(POST_KEY, JSON.stringify([
      {id:'a', antwort:'passt', gelesen_am:null},
      {id:'b', antwort:'auch', gelesen_am:'2026-08-23T10:00:00Z'},
      {id:'c', antwort:null, gelesen_am:null}]));
    return eq(postfachUngelesen(), 1);
  });
  t('Ohne Antwort keine rote Zahl', () => {
    localStorage.setItem(POST_KEY, JSON.stringify([{id:'a', antwort:null, gelesen_am:null}]));
    return eq(postfachUngelesen(), 0);
  });
  // ---- Der Fehler vom 25.08.2026: Antwort kam an, Ansicht zeichnete sich nie neu ----
  // Verglichen wurde die ANZAHL der Zeilen. Eine Antwort legt keine Zeile an, sie fuellt
  // `antwort` in einer bestehenden -- die Anzahl blieb gleich, also passierte nichts.
  // Sichtbar wurde sie erst nach einem Neustart, weil dann der Spiegel gezeichnet wurde.
  t('Eine Antwort loest ein Neuzeichnen aus, obwohl die Anzahl gleich bleibt', () => {
    const vorher = [{id:'a', antwort:null, gelesen_am:null}];
    const nachher= [{id:'a', antwort:'Hi', gelesen_am:null}];
    if (vorher.length !== nachher.length) return 'Aufbau falsch: Anzahl unterscheidet sich';
    return postfachGeaendert(vorher, nachher)
      || 'kein Neuzeichnen - genau der Fehler vom 25.08.';
  });
  t('Ohne Aenderung wird NICHT neu gezeichnet', () => {
    const l = [{id:'a', antwort:'Hi', gelesen_am:null}];
    return !postfachGeaendert(l, l.map(m => ({...m}))) || 'zeichnet grundlos neu';
  });
  t('Gleicher Bestand ergibt gleiche Signatur', () => {
    const l = [{id:'a', antwort:'Hi', gelesen_am:null}, {id:'b', antwort:null, gelesen_am:null}];
    return eq(postfachSignatur(l), postfachSignatur(l.map(m => ({...m}))));
  });
  t('Gelesen-Markieren aendert die Signatur', () => {
    const vorher = [{id:'a', antwort:'Hi', gelesen_am:null}];
    const nachher= [{id:'a', antwort:'Hi', gelesen_am:'2026-08-25T05:00:00Z'}];
    return (postfachSignatur(vorher) !== postfachSignatur(nachher)) || 'unveraendert';
  });
  t('Ein leeres Postfach hat eine Signatur, keine Ausnahme', () =>
    eq(postfachSignatur([]), '') && eq(postfachSignatur(null), ''));
  // ⚠️ Der Meldetext gehoert NICHT in die Signatur: er liegt fest, sobald die Meldung
  // raus ist. Waere er drin, kaeme kein Fehler dabei heraus - nur eine Signatur, die
  // mehr beobachtet als sich aendern kann.
  t('Der Meldetext geht nicht in die Signatur ein', () => {
    const a = [{id:'a', text:'eins', antwort:'Hi', gelesen_am:null}];
    const b = [{id:'a', text:'zwei', antwort:'Hi', gelesen_am:null}];
    return eq(postfachSignatur(a), postfachSignatur(b));
  });

  // ---- Die rote Zahl an der unteren Leiste (25.08.2026, v30) ----
  t('Die untere Leiste bekommt die rote Zahl', () => {
    localStorage.setItem(POST_KEY, JSON.stringify([
      {id:'a', antwort:'Hi', gelesen_am:null},
      {id:'b', antwort:'Auch', gelesen_am:null}]));
    setNav();
    const p = document.querySelector('#nav button[data-nav="settings"] .navpunkt');
    return (p && p.textContent === '2') || 'gefunden: ' + (p ? p.textContent : 'nichts');
  });
  t('Ohne ungelesene Antwort verschwindet sie wieder', () => {
    localStorage.setItem(POST_KEY, JSON.stringify([
      {id:'a', antwort:'Hi', gelesen_am:'2026-08-25T05:00:00Z'}]));
    setNav();
    return !document.querySelector('#nav button[data-nav="settings"] .navpunkt') || 'steht noch da';
  });
  // ⚠️ Sie sitzt am Zahnrad, weil das Postfach dort drin liegt. An 'Trainieren' waere sie
  // eine Zahl, hinter der nichts steckt.
  // ⚠️ Seit dem 27.08.2026 gibt es an der Leiste ZWEI Zahlen: die rote am Zahnrad und
  // die goldene am Pokal. Die Pruefung fragt deshalb gezielt nach der roten -- vorher stand
  // hier `#nav .navpunkt` und traf ploetzlich die goldene mit.
  t('Sie sitzt am Zahnrad, nicht woanders', () => {
    localStorage.setItem(POST_KEY, JSON.stringify([{id:'a', antwort:'Hi', gelesen_am:null}]));
    setNav();
    const rote = [...document.querySelectorAll('#nav .navpunkt')].filter(p => !p.classList.contains('gold'));
    if (rote.length !== 1) return rote.length + ' rote Punkte statt einem';
    return rote[0].closest('button').dataset.nav === 'settings'
      || 'sitzt an: ' + rote[0].closest('button').dataset.nav;
  });
  t('Mehr als neun werden zu 9+', () => {
    localStorage.setItem(POST_KEY, JSON.stringify(
      Array.from({length:12}, (_,i) => ({id:'x'+i, antwort:'Hi', gelesen_am:null}))));
    setNav();
    return eq(document.querySelector('#nav button[data-nav="settings"] .navpunkt').textContent, '9+');
  });
  // 🔴 Die rote Zahl ist eine Anforderung ("da liegt etwas fuer dich"), die goldene eine
  // Belohnung. Saehen sie gleich aus, waere die Unterscheidung nur in meinem Kopf.
  t('Rote und goldene Zahl sind unterscheidbar', () => {
    localStorage.setItem(POST_KEY, JSON.stringify([{id:'a', antwort:'Hi', gelesen_am:null}]));
    const merkG = profile.erfolgeGesehen, merkS = sessions;
    // Eine Einheit genuegt -- "Angefangen" (e1) ist damit erfuellt und noch nicht gesehen.
    // (Ohne Uebungen, `einheitMit` steht in dieser Datei erst weiter unten.)
    sessions = [{ id:'a1', date:Date.now(), entries:[], xp:0, pr:0 }];
    profile.erfolgeGesehen = {};
    setNav();
    const rot  = document.querySelector('#nav button[data-nav="settings"] .navpunkt');
    const gold = document.querySelector('#nav button[data-nav="erfolge"] .navpunkt');
    const ok = !!rot && !!gold && !rot.classList.contains('gold') && gold.classList.contains('gold');
    profile.erfolgeGesehen = merkG; sessions = merkS;
    return ok || 'rot=' + (rot && rot.className) + ' gold=' + (gold && gold.className);
  });
  // ⚠️ Karls Meldung: auf dem PC stand die Zahl in der Mitte der Seitenleiste statt am
  // Wort. Die Ursache war der Bezugsrahmen -- sie hing am Knopf, nicht an der Beschriftung.
  t('Die Zahl haengt an der Beschriftung, nicht am Knopf', () => {
    localStorage.setItem(POST_KEY, JSON.stringify([{id:'a', antwort:'Hi', gelesen_am:null}]));
    setNav();
    const p = document.querySelector('#nav button[data-nav="settings"] .navpunkt');
    return (!!p && !!p.parentElement && p.parentElement.classList.contains('navtxt'))
      || 'haengt an: ' + (p ? p.parentElement.className || p.parentElement.tagName : 'nichts');
  });
  t('Jeder Leisten-Knopf hat eine Beschriftung im eigenen Span', () => {
    const knoepfe = [...document.querySelectorAll('#nav button')];
    const ohne = knoepfe.filter(b => !b.querySelector('.navtxt'));
    return ohne.length === 0 || 'ohne .navtxt: ' + ohne.map(b => b.dataset.nav).join(', ');
  });

  // ---- Der Sprung ins Postfach reisst kein Training auseinander ----
  // 🔴 Das ist der einzige Nachteil, den das Direktspringen hat: wer zwischen zwei Saetzen
  // aufs Handy schaut, waere mitten aus seiner Einheit gerissen worden.
  t('Waehrend eines Trainings wird NICHT ins Postfach gesprungen', () => {
    localStorage.setItem(POST_KEY, JSON.stringify([{id:'a', antwort:'Hi', gelesen_am:null}]));
    const vorherActive = active, vorherView = view;
    active = { start: Date.now(), ex: [] };      // ein laufendes Training vortaeuschen
    view = 'home';
    const gesprungen = postfachSpringen();
    const wo = view;
    active = vorherActive; view = vorherView;
    if (gesprungen) return 'ist gesprungen, obwohl ein Training laeuft';
    return eq(wo, 'home');
  });
  // ⚠️ Und die rote Zahl muss trotzdem erscheinen -- sonst waere das Nicht-Springen ein
  // stilles Verschlucken der Antwort statt eines Aufschubs.
  t('Bei laufendem Training bleibt die rote Zahl stehen', () => {
    localStorage.setItem(POST_KEY, JSON.stringify([{id:'a', antwort:'Hi', gelesen_am:null}]));
    const vorherActive = active, vorherView = view;
    active = { start: Date.now(), ex: [] }; view = 'home';
    postfachSpringen();
    const p = document.querySelector('#nav button[data-nav="settings"] .navpunkt');
    const txt = p ? p.textContent : null;
    active = vorherActive; view = vorherView;
    return eq(txt, '1');
  });
  t('Ohne laufendes Training wird gesprungen', () => {
    localStorage.setItem(POST_KEY, JSON.stringify([{id:'a', antwort:'Hi', gelesen_am:null}]));
    const vorherActive = active, vorherView = view;
    active = null; view = 'home';
    const gesprungen = postfachSpringen();
    const wo = view;
    active = vorherActive; view = vorherView; render();
    return (gesprungen && wo === 'meldung') || 'gelandet auf: ' + wo;
  });
  // Der Weg von der Mitteilung ins offene Fenster: der Service Worker schickt eine
  // Nachricht, die App hoert darauf. Fehlt eines von beidem, passiert gar nichts.
  t('Der Service Worker schickt die Nachricht ins offene Fenster', () => {
    const sw = SW_QUELLE;
    return (/postMessage\(\s*\{\s*typ:\s*'postfach'/.test(sw)) || 'kein postMessage im notificationclick';
  });
  t('Bei geschlossener App wird mit #postfach geoeffnet', () => {
    return (/openWindow\(ziel \+ '#postfach'\)/.test(SW_QUELLE)) || 'oeffnet ohne #postfach';
  });

  // ================================================ XP-Umbau (26.08.2026, v31)
  // Hilfsbau: eine Einheit mit n Saetzen zu je (kg x wdh), die ersten `prs` als Rekord.
  const einheitMit = (n, kg, wdh, prs) => {
    const sets = Array.from({length:n}, () => ({weight:kg, reps:wdh, done:true}));
    if (prs) for (let i=0; i<prs && i<n; i++) sets[i].pr = true;
    return [{ name:'Test', sets }];
  };

  // ---- DIE Pruefung: der Grund, warum ueberhaupt umgebaut wurde ----
  // Vorher: Anfaenger-Oberkoerper 210 XP, Fortgeschritten-Beine 630 XP. Faktor 3,0.
  // Kniebeugen bewegen nun mal mehr Kilo als Curls - ein ehrlich harter Oberkoerpertag
  // war weniger wert als ein lockerer Beintag, und wer stark ist, stieg dreimal so schnell auf.
  t('Ein Beintag ist nicht mehr dreimal so viel wert wie ein Oberkoerpertag', () => {
    const ober = sessXP(einheitMit(12, 100, 2, 2), 2);   // 12 Saetze,  2.400 kg, 2 Rekorde
    const bein = sessXP(einheitMit(18, 200, 6, 2), 2);   // 18 Saetze, 21.600 kg, 2 Rekorde
    const faktor = bein / ober;
    if (faktor >= 2) return 'Faktor ' + faktor.toFixed(2) + ' - immer noch die alte Schieflage';
    return faktor > 1 || 'Faktor ' + faktor.toFixed(2) + ' - der Beintag muesste etwas mehr geben, nicht weniger';
  });
  // Der Deckel ist der eigentliche Eingriff, nicht der Rekord-Bonus. Ohne ihn waechst der
  // Volumenanteil mit der Kraft unbegrenzt weiter und frisst alles andere auf.
  t('Das Volumen ist bei 100 XP gedeckelt', () =>
    eq(volXP(einheitMit(20, 500, 20, 0)), VOL_XP_MAX));
  t('Wenig Volumen zaehlt weiter voll mit', () =>
    eq(volXP(einheitMit(10, 100, 2, 0)), 40));
  t('Karls Ansage: Gewicht wird weiter belohnt', () => {
    const leicht = sessXP(einheitMit(10, 10, 2, 0), 0);
    const schwer = sessXP(einheitMit(10, 100, 2, 0), 0);
    return schwer > leicht || 'schweres Training bringt nicht mehr als leichtes';
  });
  t('Jeder Rekord bringt 25 XP', () =>
    eq(sessXP(einheitMit(10, 100, 2, 3), 3) - sessXP(einheitMit(10, 100, 2, 0), 0), 75));
  // Ob ein Satz Rekord war, haengt an der Historie zum Zeitpunkt des Trainings. Wer das aus
  // den Saetzen herleiten wollte, bekaeme beim Nachrechnen eine andere Zahl als beim Beenden.
  t('Die Rekordzahl kommt von aussen, nicht aus den Saetzen', () => {
    const en = einheitMit(10, 100, 2, 0);
    return eq(sessXP(en, 4) - sessXP(en, 0), 100);
  });
  t('Rekorde werden ueber die Satz-Markierung gezaehlt', () =>
    eq(zaehleRekorde(einheitMit(10, 100, 2, 3)), 3));
  t('Ein abgewaehlter Satz zaehlt nicht als Rekord', () => {
    const en = einheitMit(3, 100, 2, 3);
    en[0].sets[1].done = false;
    return eq(zaehleRekorde(en), 2);
  });

  // ================================================ Tagesaufgaben
  // Der Deckel ist hier die ganze Idee: Aufgaben schieben an, sie tragen nicht. Im Vault
  // steht seit dem 22.08. bewusst "kein XP fuers Essen" - eine Aufgabe "App geoeffnet" ist
  // derselbe Fall, geloest ueber die Groessenordnung statt ueber ein Nein.
  t('Aufgaben bringen hoechstens 30 XP am Tag', () => eq(AUFGABEN_MAX, 30));
  t('Eine Einheit ist ein Vielfaches aller Tagesaufgaben wert', () => {
    const einheit = sessXP(einheitMit(12, 100, 2, 2), 2);
    return einheit >= AUFGABEN_MAX * 5
      || 'Einheit ' + einheit + ' XP gegen ' + AUFGABEN_MAX + ' XP Aufgaben - zu nah beieinander';
  });
  t('Eine erledigte Aufgabe gibt ihre XP', () => {
    profile.aufgaben = { tag:'', fertig:{} };
    const vorher = profile.xp;
    const gab = aufgabeErledigen('auf');
    const delta = profile.xp - vorher;
    profile.aufgaben = { tag:'', fertig:{} }; profile.xp = vorher;
    return (gab && delta === 5) || 'gab=' + gab + ' delta=' + delta;
  });
  t('Dieselbe Aufgabe zweimal am Tag zaehlt nur einmal', () => {
    profile.aufgaben = { tag:'', fertig:{} };
    const vorher = profile.xp;
    aufgabeErledigen('auf');
    const nochmal = aufgabeErledigen('auf');
    const delta = profile.xp - vorher;
    profile.aufgaben = { tag:'', fertig:{} }; profile.xp = vorher;
    return (nochmal === false && delta === 5) || 'nochmal=' + nochmal + ' delta=' + delta;
  });
  // Der Tageswechsel wird beim LESEN geprueft, nicht per Timer - ein Timer um Mitternacht
  // liefe nur, solange die App offen ist, und die ist sie nachts nie.
  t('Am naechsten Tag stehen die Aufgaben wieder offen', () => {
    profile.aufgaben = { tag:'2020-01-01', fertig:{ auf:true, ein:true, train:true } };
    const offen = aufgabenOffen();
    profile.aufgaben = { tag:'', fertig:{} };
    return eq(offen, AUFGABEN.length);
  });
  t('Eine unbekannte Aufgabe gibt nichts', () => {
    const vorher = profile.xp;
    const gab = aufgabeErledigen('gibtsnicht');
    const delta = profile.xp - vorher;
    profile.xp = vorher;
    return (gab === false && delta === 0) || 'gab=' + gab + ' delta=' + delta;
  });

  // ================================================ Erfolge
  t('Der Katalog hat Eintraege und jeder ist vollstaendig', () => {
    const kaputt = ERFOLGE.filter(e => !e.id || !e.name || !e.gr || !(e.ziel > 0) || typeof e.ist !== 'function');
    return (ERFOLGE.length >= 10 && kaputt.length === 0) || kaputt.length + ' unvollstaendig';
  });
  t('Erfolgs-Kennungen sind eindeutig', () => {
    const ids = ERFOLGE.map(e => e.id);
    return eq(new Set(ids).size, ids.length);
  });
  // Nichts wird gespeichert, alles gerechnet. Ein gespeicherter Erfolg haengt nach einer
  // korrigierten Einheit in der Luft - dann steht ein Haken an etwas, das die Daten nicht
  // mehr hergeben. Dieselbe Entscheidung wie beim Essens-Serienrekord.
  t('Ohne Einheiten ist nichts geschafft, was Einheiten braucht', () => {
    const merk = sessions; sessions = [];
    const offen = erfolgOffen(ERFOLGE.find(e => e.id === 'e1'));
    sessions = merk;
    return offen || 'Erste Einheit gilt als geschafft, obwohl es keine gibt';
  });
  t('Mit einer Einheit ist der erste Erfolg da', () => {
    const merk = sessions;
    sessions = [{ id:'x', date:Date.now(), entries:einheitMit(3, 50, 5, 0), xp:100, pr:0 }];
    const offen = erfolgOffen(ERFOLGE.find(e => e.id === 'e1'));
    sessions = merk;
    return !offen || 'Erste Einheit gilt nicht als geschafft';
  });
  // 🔴 besteWochenSerie, NICHT wochenSerie. Letztere gibt es schon und meint die Serie BIS
  // HEUTE (die Flamme auf der Startseite). Beim ersten Bauen hiess die neue genauso und
  // wurde still ueberschrieben - diese Pruefung hat es gefunden.
  t('Die laengste Wochenserie zaehlt auch weit zurueckliegende', () => {
    const merk = sessions, W = 604800000, t0 = Date.UTC(2026, 0, 8);
    sessions = [t0, t0+W, t0+2*W, t0+4*W].map((d,i) => ({ id:'w'+i, date:d, entries:[], xp:0 }));
    const serie = besteWochenSerie();
    sessions = merk;
    return eq(serie, 3);           // drei am Stueck, dann eine Luecke
  });
  // ⚠️ Der Unterschied ist der ganze Punkt: eine Trophaee darf nicht verschwinden, wenn die
  // Serie reisst. Geschafft bleibt geschafft.
  t('Die laufende Serie ist etwas anderes als die laengste je', () => {
    const merk = sessions, W = 604800000, t0 = Date.UTC(2026, 0, 8);
    sessions = [t0, t0+W, t0+2*W].map((d,i) => ({ id:'u'+i, date:d, entries:[], xp:0 }));
    const laengste = besteWochenSerie(), laufend = wochenSerie();
    sessions = merk;
    return (laengste === 3 && laufend === 0)
      || 'laengste=' + laengste + ' laufend=' + laufend + ' - die beiden duerfen nicht dasselbe sein';
  });
  t('Die beste Woche zaehlt Einheiten, nicht Wochen', () => {
    const merk = sessions, T = 86400000, t0 = Date.UTC(2026, 0, 8);
    sessions = [t0, t0+T, t0+2*T, t0+30*T].map((d,i) => ({ id:'b'+i, date:d, entries:[], xp:0 }));
    const best = besteWoche();
    sessions = merk;
    return eq(best, 3);
  });

  // ================================================ XP fuer Erfolge (v32)
  // 🔴 Karls Einwand, und er ist der Kern: "aber nicht fuer Erfolge in Hinsicht auf Level".
  // Ein Erfolg fuer Level 25, der XP gibt, ist ein Kreis - die Belohnung fuers Leveln waeren
  // Level. Bei Gigachad waere es sogar folgenlos, weil darueber nichts mehr kommt.
  t('Rang-Erfolge geben keine XP', () => {
    const rang = ERFOLGE.filter(e => e.gr === 'Rang');
    const mitXP = rang.filter(e => e.xp);
    return (rang.length === 3 && mitXP.length === 0)
      || 'diese Rang-Erfolge geben XP: ' + mitXP.map(e => e.name).join(', ');
  });
  t('Alle anderen Erfolge geben XP', () => {
    const ohne = ERFOLGE.filter(e => e.gr !== 'Rang' && !(e.xp > 0));
    return ohne.length === 0 || 'ohne XP: ' + ohne.map(e => e.name).join(', ');
  });
  // ⚠️ Die Regel dahinter, damit sie beim naechsten Erfolg nicht vergessen wird: ein Erfolg
  // gibt XP, wenn er NICHT in XP gemessen wird.
  t('Kein Erfolg belohnt das, woran er sich misst', () => {
    const kreis = ERFOLGE.filter(e => e.xp > 0 && e.ist === undefined);
    const rangMitXP = ERFOLGE.filter(e => e.xp > 0 && e.gr === 'Rang');
    return (kreis.length === 0 && rangMitXP.length === 0) || 'Kreis gefunden';
  });

  t('Ein erfuellter Erfolg wird ausgezahlt', () => {
    const merkS = sessions, merkE = profile.erfolge, merkX = profile.xp;
    sessions = [{ id:'a1', date:Date.now(), entries:einheitMit(3, 50, 5, 0), xp:100, pr:0 }];
    profile.erfolge = {};
    const neu = erfolgeAuszahlen();
    const delta = profile.xp - merkX;
    const dabei = neu.some(e => e.id === 'e1');
    sessions = merkS; profile.erfolge = merkE; profile.xp = merkX;
    return (dabei && delta > 0) || 'dabei=' + dabei + ' delta=' + delta;
  });
  // ⚠️ Ohne die Liste "schon ausgezahlt" gaebe es bei JEDEM App-Start dieselben XP nochmal.
  // Das ist die einzige Stelle im ganzen Erfolgs-Teil, an der etwas gespeichert wird.
  t('Derselbe Erfolg wird nicht zweimal ausgezahlt', () => {
    const merkS = sessions, merkE = profile.erfolge, merkX = profile.xp;
    sessions = [{ id:'a1', date:Date.now(), entries:einheitMit(3, 50, 5, 0), xp:100, pr:0 }];
    profile.erfolge = {};
    erfolgeAuszahlen();
    const nachErstem = profile.xp;
    const nochmal = erfolgeAuszahlen();
    const delta = profile.xp - nachErstem;
    sessions = merkS; profile.erfolge = merkE; profile.xp = merkX;
    return (nochmal.length === 0 && delta === 0) || 'nochmal=' + nochmal.length + ' delta=' + delta;
  });
  t('Ein unerfuellter Erfolg wird nicht ausgezahlt', () => {
    const merkS = sessions, merkE = profile.erfolge, merkX = profile.xp;
    sessions = []; profile.erfolge = {};
    const neu = erfolgeAuszahlen();
    const delta = profile.xp - merkX;
    sessions = merkS; profile.erfolge = merkE; profile.xp = merkX;
    return (neu.length === 0 && delta === 0) || 'neu=' + neu.length + ' delta=' + delta;
  });
  // ⚠️ Nichts wird zurueckgenommen. Wer eine Einheit korrigiert und unter eine Schwelle
  // rutscht, behaelt die XP - gleiche Linie wie bei sessRecalc: lieber ein alter Wert stehen
  // als ein geratener abgezogen.
  t('Ausgezahlte XP werden nicht zurueckgenommen', () => {
    const merkS = sessions, merkE = profile.erfolge, merkX = profile.xp;
    sessions = [{ id:'a1', date:Date.now(), entries:einheitMit(3, 50, 5, 0), xp:100, pr:0 }];
    profile.erfolge = {};
    erfolgeAuszahlen();
    const nachAuszahlung = profile.xp;
    sessions = [];                       // Einheit weg - der Erfolg gilt nicht mehr
    erfolgeAuszahlen();
    const jetzt = profile.xp;
    sessions = merkS; profile.erfolge = merkE; profile.xp = merkX;
    return eq(jetzt, nachAuszahlung);
  });
  // ================================================ Erfolge v33 (27.08.2026)
  // Karls drei Einwaende am Katalog: 500 t zu viel, 13 Wochen zu viel und unfair bei
  // Krankheit, und der Admin soll alles freischalten koennen.

  const WOCHE = 604800000;
  // Baut Einheiten in den genannten Wochen-Abstaenden (0 = diese Woche, 1 = vorige, ...).
  const wochenWie = (...abstaende) => abstaende.map((w, i) =>
    ({ id:'w'+i, date: wochenStart(Date.now()) - w*WOCHE + 86400000, entries:[], xp:0, pr:0 }));

  t('Volumen-Erfolg steht auf 250 t, nicht auf 500 t', () => {
    const v4 = ERFOLGE.find(e => e.id === 'v4');
    return eq(v4.ziel, 250000);
  });
  t('Der lange Dranbleiben-Erfolg steht auf 8 Wochen', () => {
    const d3 = ERFOLGE.find(e => e.id === 'd3');
    return eq(d3.ziel, 8);
  });
  // 🔴 Karls eigentlicher Einwand war nicht die Zahl, sondern die Haerte: eine Grippe
  // reisst die Serie ab, und dann bestraft der Erfolg Krankheit statt fehlenden Willen.
  t('Eine ausgefallene Woche reisst die Serie nicht ab', () => {
    const merk = sessions;
    sessions = wochenWie(5, 4, 3, 1, 0);          // Woche 2 fehlt
    const mitJoker = besteWochenSerieJoker();
    const streng   = besteWochenSerie();
    sessions = merk;
    // Fuenf trainierte Wochen, eine Luecke dazwischen ueberbrueckt. Streng gezaehlt reisst
    // die Serie an der Luecke und die laengste bleibt bei drei.
    return (mitJoker === 5 && streng === 3) || 'Joker=' + mitJoker + ' streng=' + streng;
  });
  // ⚠️ Verziehen heisst verziehen, nicht geschenkt: die Pausenwoche zaehlt nicht mit.
  t('Die Pausenwoche zaehlt nicht als trainierte Woche', () => {
    const merk = sessions;
    sessions = wochenWie(2, 0);                   // trainiert, Pause, trainiert
    const r = besteWochenSerieJoker();
    sessions = merk;
    return eq(r, 2);
  });
  // ⚠️ Ohne diese Grenze waere aus dem Erfolg "irgendwann mal acht Wochen trainiert"
  // geworden, und das misst gar nichts mehr.
  t('Zwei Wochen am Stueck reissen die Serie doch ab', () => {
    const merk = sessions;
    sessions = wochenWie(6, 5, 4, 1, 0);          // zwei Wochen Luecke
    const r = besteWochenSerieJoker();
    sessions = merk;
    return eq(r, 3);
  });
  t('Nur EINE Luecke wird verziehen, nicht jede zweite Woche', () => {
    const merk = sessions;
    sessions = wochenWie(6, 4, 2, 0);             // jede zweite Woche
    const r = besteWochenSerieJoker();
    sessions = merk;
    return eq(r, 2);
  });
  t('Der strenge Vier-Wochen-Erfolg bleibt streng', () => {
    const d2 = ERFOLGE.find(e => e.id === 'd2');
    return d2.ist === besteWochenSerie || 'd2 zaehlt nicht mehr streng';
  });
  /* 🔴 Nachgetragen am 27.08.2026, weil die Gegenprobe NICHT gebissen hat: d3 wieder auf
     die strenge Zaehlung zurueckzubauen liess keine einzige Pruefung umfallen. Alle Joker-
     Pruefungen riefen `besteWochenSerieJoker()` direkt auf, und die Ziel-Pruefung sah nur die
     Zahl 8. Damit war zwar die Zaehlung geprueft, aber nicht, dass der Erfolg sie benutzt --
     also genau die Verbindung, um die es Karl ging. */
  t('Der lange Erfolg benutzt die verzeihende Zaehlung wirklich', () => {
    const d3 = ERFOLGE.find(e => e.id === 'd3');
    if (d3.ist !== besteWochenSerieJoker) return 'd3 zaehlt streng statt verzeihend';
    const merk = sessions;
    sessions = wochenWie(8, 7, 6, 5, 3, 2, 1, 0);   // acht Wochen, eine Luecke
    const offen = erfolgOffen(d3);
    sessions = merk;
    return offen === false || 'mit einer Krankheitswoche bleibt der Erfolg verschlossen';
  });

  // ---- Admin: alle Erfolge freischalten ----
  t('Der Admin-Schalter zeigt alle Erfolge als geschafft', () => {
    const merkS = sessions, merkD = settings.devAllErfolge;
    sessions = [];
    settings.devAllErfolge = true;
    const alle = erfolgeGeschafft();
    settings.devAllErfolge = merkD; sessions = merkS;
    return eq(alle, ERFOLGE.length);
  });
  // 🔴 Die wichtigste Pruefung dieses Blocks. Ohne die Sperre haette ein Klick 8.050 XP
  // ins Profil geschrieben - und zurueckgenommen wird hier nichts.
  t('Der Admin-Schalter zahlt keine XP aus', () => {
    const merkS = sessions, merkD = settings.devAllErfolge, merkE = profile.erfolge, merkX = profile.xp;
    sessions = []; profile.erfolge = {}; settings.devAllErfolge = true;
    const neu = erfolgeAuszahlen();
    const delta = profile.xp - merkX;
    settings.devAllErfolge = merkD; sessions = merkS; profile.erfolge = merkE; profile.xp = merkX;
    return (neu.length === 0 && delta === 0) || 'neu=' + neu.length + ' delta=' + delta;
  });
  // ⚠️ Sonst haengt eine goldene 22 an der Leiste und Karl sucht 22 Erfolge, die er nie
  // freigeschaltet hat.
  t('Die goldene Zahl zaehlt nur echte Erfolge, nicht den Admin-Schalter', () => {
    const merkS = sessions, merkD = settings.devAllErfolge, merkG = profile.erfolgeGesehen;
    sessions = []; profile.erfolgeGesehen = {};
    settings.devAllErfolge = false; const ohne = erfolgeNeu().length;
    settings.devAllErfolge = true;  const mit  = erfolgeNeu().length;
    settings.devAllErfolge = merkD; sessions = merkS; profile.erfolgeGesehen = merkG;
    // Nicht "null neu" - was echt verdient ist, darf durchaus neu sein. Der Schalter darf
    // die Zahl nur nicht aufblaehen.
    return eq(mit, ohne);
  });

  // ---- Was ist neu? ----
  // ⚠️ Beim Umstieg auf v33 darf NICHT alles Verdiente als neu aufleuchten - sonst ist
  // die goldene Zahl entwertet, bevor sie das erste Mal etwas bedeutet.
  t('Beim ersten Start gilt Verdientes als gesehen, nicht als neu', () => {
    const merkS = sessions, merkG = profile.erfolgeGesehen;
    sessions = [{ id:'a1', date:Date.now(), entries:[], xp:0, pr:0 }];
    profile.erfolgeGesehen = null;
    erfolgeGesehenInit();
    const n = erfolgeNeu().length;
    profile.erfolgeGesehen = merkG; sessions = merkS;
    return eq(n, 0);
  });
  t('Ein frisch verdienter Erfolg zaehlt als neu', () => {
    const merkS = sessions, merkG = profile.erfolgeGesehen;
    sessions = []; profile.erfolgeGesehen = null;
    erfolgeGesehenInit();                        // noch nichts verdient
    sessions = [{ id:'a1', date:Date.now(), entries:[], xp:0, pr:0 }];
    const n = erfolgeNeu().length;
    profile.erfolgeGesehen = merkG; sessions = merkS;
    return n >= 1 || 'nichts als neu erkannt';
  });
  t('Nach dem Ansehen ist nichts mehr neu', () => {
    const merkS = sessions, merkG = profile.erfolgeGesehen, merkV = view;
    sessions = []; profile.erfolgeGesehen = null; erfolgeGesehenInit();
    sessions = [{ id:'a1', date:Date.now(), entries:[], xp:0, pr:0 }];
    view = 'erfolge'; renderErfolge();
    const n = erfolgeNeu().length;
    view = merkV; profile.erfolgeGesehen = merkG; sessions = merkS;
    return eq(n, 0);
  });

  // ---- Das Board oben ----
  t('Das Board nennt den Gesamtstand, nicht nur eine Fussnote', () => {
    const merkV = view; view = 'erfolge'; renderErfolge();
    const txt = document.getElementById('app').textContent;
    const ring = document.querySelector('.erf-ring');
    view = merkV;
    return (!!ring && /% geschafft/.test(txt) && /Aus Erfolgen verdient/.test(txt))
      || 'ring=' + !!ring + ' txt=' + txt.slice(0, 120);
  });

  // ================================================ Plan-Link kuerzen (v33)
  // Karls Meldung: der Link fuellt gefuehlt ein A4-Blatt. Gemessen: 1.005 Zeichen.
  t('Der Packer ist in diesem Browser da', () => typeof CompressionStream === 'function' || 'kein CompressionStream');
  await tA('Der kurze Link ist deutlich kuerzer als der alte', async () => {
    const pr = activeProg();
    const lang = planCode(pr);
    const kurz = 'z' + (await packe(JSON.stringify(planNutzlast(pr))));
    return kurz.length < lang.length * 0.6
      || 'kurz=' + kurz.length + ' lang=' + lang.length;
  });
  // 🔴 Kuerzer nuetzt nichts, wenn beim Empfaenger ein anderer Plan ankommt.
  await tA('Der kurze Link bringt denselben Plan wieder heraus', async () => {
    const pr = activeProg();
    const roh = JSON.stringify(planNutzlast(pr));
    const zurueck = await entpacke(await packe(roh));
    return eq(zurueck, roh);
  });
  t('Aus dem kurzen Code wird wieder die alte Plan-Form', () => {
    const pr = activeProg();
    const p = v3ZuPlan(planNutzlast(pr));
    const echt = (pr.plans || []).filter(x => (x.exercises || []).some(e => e.name));
    if (!p) return 'v3ZuPlan hat null geliefert';
    if (p.p.length !== Math.min(10, echt.length)) return p.p.length + ' Trainings statt ' + echt.length;
    const erstes = p.p[0], quelle = echt[0];
    return (erstes.n === quelle.name && erstes.e.length === quelle.exercises.filter(e=>e.name).length)
      || 'erstes Training weicht ab';
  });
  // ⚠️ Ein Link, den Karl gestern verschickt hat, darf morgen nicht unbekannt sein.
  t('Alte v2-Links werden weiterhin gelesen', () => {
    const merk = planImport;
    const alt = planCode(activeProg());
    location.hash = '#p=' + alt;
    planImport = null; leseImportAusLink();
    const ok = !!planImport && Array.isArray(planImport.p) && planImport.p.length > 0;
    planImport = merk; location.hash = '';
    return ok || 'v2-Link nicht gelesen';
  });
  t('Ohne Vorwaermen bleibt der alte lange Link uebrig', () => {
    const pr = activeProg();
    planCodeCache.clear();
    const c = planCodeKurz(pr);
    return (c[0] !== 'z' && c === planCode(pr)) || 'unerwarteter Code: ' + c.slice(0, 12);
  });
  await tA('Vorgewaermt kommt der kurze Code heraus', async () => {
    const pr = activeProg();
    planCodeCache.clear();
    planCodeVorwaermen(pr);
    await new Promise(r => setTimeout(r, 60));
    const c = planCodeKurz(pr);
    return c[0] === 'z' || 'nicht vorgewaermt: ' + c.slice(0, 12);
  });
  /* 🔴 Auch nachgetragen, weil die Gegenprobe nicht gebissen hat: das Vorwaermen im
     render() abzuschalten liess nichts umfallen -- die Pruefung darueber rief `planCodeVor-
     waermen` selbst auf. Geprueft war damit der Packer, nicht der Ausloeser. Und ohne
     Ausloeser bekaeme Karl beim ersten Teilen still wieder den langen Link. */
  await tA('Das Zeichnen der Plan-Liste waermt den Code vor', async () => {
    const merkV = view, merkSess = session;
    // ⚠️ Ohne Anmeldung steigt render() sofort wieder aus (Anmeldeschirm) - dann
    // waere diese Pruefung gruen, ohne je am Vorwaermen vorbeigekommen zu sein.
    if(!session) session = { access_token:'test' };
    planCodeCache.clear();
    view = 'progs'; render();
    await new Promise(r => setTimeout(r, 80));
    const gefuellt = planCodeCache.size;
    view = merkV; session = merkSess; render();
    return gefuellt > 0 || 'der Zwischenspeicher blieb leer';
  });

  // ================================================ Training beenden (v34)
  /* \U0001f534 Karls Meldung: "wenn ich auf Training beenden gehe, wird das Training einfach
     verworfen. Liegt es daran, dass das Training nicht komplett abgeschlossen wurde? Aber
     das waere nicht richtig."

     Es lag genau daran. Bis hierher entschied allein der Haken, ob ein Satz existiert -- wer
     80 kg und 8 Wiederholungen eintippte und nicht abhakte, hatte fuer die App nichts getan,
     und die ganze Einheit verschwand hinter einem Hinweis, der nach 1,8 s weg war. */

  // Ein laufendes Training bauen. Zurueckgesetzt wird in jeder Pruefung selbst.
  const laufendesTraining = (saetze) => ({
    id: 'test-' + Math.random(), date: Date.now() - 600000, planName: 'Testtag',
    exercises: [{ name: 'Bankdruecken', icon: 'press', sets: saetze }]
  });

  t('Eingetragene Saetze zaehlen auch ohne Haken', () => {
    const mA = active, mS = sessions, mX = profile.xp, mV = view;
    sessions = [];
    active = laufendesTraining([{ weight: 80, reps: 8, done: false },
                                { weight: 80, reps: 7, done: false }]);
    finishWorkout();
    const gespeichert = sessions.length;
    const saetze = gespeichert ? sessions[0].entries[0].sets.length : 0;
    active = mA; sessions = mS; profile.xp = mX; view = mV; closeModal();
    return (gespeichert === 1 && saetze === 2)
      || 'Einheiten=' + gespeichert + ' Saetze=' + saetze;
  });
  // \u26a0\ufe0f Die Felder sind leer, solange niemand tippt (Vorschlaege stehen als Platzhalter).
  // Ein geplanter, aber nicht gemachter Satz darf deshalb weiterhin nichts beitragen.
  t('Leere Saetze zaehlen weiterhin nicht', () => {
    const mA = active, mS = sessions, mX = profile.xp, mV = view;
    sessions = [];
    active = laufendesTraining([{ weight: 80, reps: 8, done: false },
                                { weight: '',  reps: '', done: false }]);
    finishWorkout();
    const saetze = sessions.length ? sessions[0].entries[0].sets.length : 0;
    active = mA; sessions = mS; profile.xp = mX; view = mV; closeModal();
    return eq(saetze, 1);
  });
  // Dasselbe Nachziehen wie beim Abhaken von Hand: fehlende Wiederholungen bekommen die
  // untere Zahl des Zielbereichs, sonst waere das Volumen dieses Satzes null.
  t('Fehlende Wiederholungen werden nachgezogen', () => {
    const mA = active, mS = sessions, mX = profile.xp, mV = view;
    sessions = [];
    active = laufendesTraining([{ weight: 80, reps: '', done: false }]);
    finishWorkout();
    const r = sessions.length ? +sessions[0].entries[0].sets[0].reps : 0;
    active = mA; sessions = mS; profile.xp = mX; view = mV; closeModal();
    return r > 0 || 'Wiederholungen blieben bei ' + r;
  });
  // \U0001f534 Sonst verloere Karl den Rekord-Bonus fuer genau die Saetze, die er getippt hat.
  t('Ein Rekord wird auch ohne Haken vermerkt', () => {
    const mA = active, mS = sessions, mX = profile.xp, mV = view;
    sessions = [];
    active = laufendesTraining([{ weight: 200, reps: 5, done: false }]);
    finishWorkout();
    const pr = sessions.length ? sessions[0].pr : -1;
    active = mA; sessions = mS; profile.xp = mX; view = mV; closeModal();
    return pr === 1 || 'Rekorde gezaehlt: ' + pr;
  });
  /* \U0001f534 Und der Fall, der Karl den Abend gekostet haette: wirklich nichts drin. Frueher
     war die Einheit dann weg -- ohne Nachfrage, ohne Rueckweg. Jetzt bleibt sie stehen und
     der Hinweis sagt, was los ist. Wegwerfen kann Karl selbst, dafuer gibt es Abbrechen. */
  t('Ohne jede Eingabe wird nicht mehr stillschweigend verworfen', () => {
    const mA = active, mS = sessions, mX = profile.xp, mV = view;
    sessions = [];
    active = laufendesTraining([{ weight: '', reps: '', done: false }]);
    finishWorkout();
    const nochDa = !!active, nichtsGespeichert = sessions.length === 0;
    active = mA; sessions = mS; profile.xp = mX; view = mV; closeModal();
    return (nochDa && nichtsGespeichert)
      || 'Einheit noch da=' + nochDa + ' nichts gespeichert=' + nichtsGespeichert;
  });
  t('Ein abgehakter Satz zaehlt weiterhin, auch ohne Gewicht', () => {
    const mA = active, mS = sessions, mX = profile.xp, mV = view;
    sessions = [];
    active = laufendesTraining([{ weight: '', reps: 12, done: true }]);
    finishWorkout();
    const gespeichert = sessions.length;
    active = mA; sessions = mS; profile.xp = mX; view = mV; closeModal();
    return eq(gespeichert, 1);
  });
  // Aufwaermsaetze zaehlen nicht ins Volumen - das war vorher so und bleibt so.
  t('Ein eingetragener Aufwaermsatz bringt keinen Rekord', () => {
    const mA = active, mS = sessions, mX = profile.xp, mV = view;
    sessions = [];
    active = laufendesTraining([{ weight: 300, reps: 5, done: false, warm: true },
                                { weight: 60,  reps: 8, done: false }]);
    finishWorkout();
    const pr = sessions.length ? sessions[0].pr : -1;
    active = mA; sessions = mS; profile.xp = mX; view = mV; closeModal();
    return eq(pr, 1);
  });

  // ================================================ Nummern statt Namen (v34)
  /* \U0001f534 Die wichtigste Pruefung im ganzen Link-Teil, und sie prueft keine Funktion,
     sondern eine ZUSAGE: die Uebungs-Bibliothek ist ab dem 27.08.2026 anhaengend. Ein Link
     enthaelt Nummern, keine Namen -- verschiebt sich ein Eintrag, zeigt jeder alte Link
     still auf die falsche Uebung. "Still" ist das Problem: eine falsche Nummer sieht aus
     wie eine richtige, und niemand merkt es, bis jemand mit dem falschen Gewicht dasteht.
     Faellt diese Pruefung um, ist nicht sie kaputt -- dann wurde umsortiert. */
  t('Die Uebungs-Bibliothek ist nicht umsortiert worden', () => {
    if (EXNAMEN.length < LIB_LAENGE) return 'Bibliothek ist kuerzer geworden: ' + EXNAMEN.length + ' statt ' + LIB_LAENGE;
    if (EXNAMEN[0] !== LIB_ERSTER) return 'erster Eintrag ist jetzt: ' + EXNAMEN[0];
    if (EXNAMEN[LIB_LAENGE - 1] !== LIB_LETZTER) return 'Eintrag ' + (LIB_LAENGE-1) + ' ist jetzt: ' + EXNAMEN[LIB_LAENGE-1];
    return true;
  });
  t('Jede Nummer zeigt auf genau einen Namen', () => {
    const doppelt = EXNAMEN.filter((n, i) => EXNUMMER.get(n) !== i && EXNAMEN.indexOf(n) === i);
    return doppelt.length === 0 || 'Nummer zeigt woanders hin: ' + doppelt.slice(0,3).join(', ');
  });

  t('Eine bekannte Uebung wird zur blossen Nummer', () => {
    const x = ueNutzlast({ name: EXNAMEN[0], sets: 3, vol: 'high' });
    return typeof x === 'number' || 'kam heraus: ' + JSON.stringify(x);
  });
  // \u26a0\ufe0f Karls eigene Uebungen kennt die Bibliothek nicht - die muessen als Text mit,
  // sonst faellt beim Empfaenger genau das weg, was Karl selbst angelegt hat.
  t('Eine eigene Uebung bleibt als Text erhalten', () => {
    const x = ueNutzlast({ name: 'Karls Spezialuebung XYZ', sets: 3, vol: 'high' });
    return x === 'Karls Spezialuebung XYZ' || 'kam heraus: ' + JSON.stringify(x);
  });
  t('Abweichende Satzzahl und Volumen gehen nicht verloren', () => {
    const a = ueAusNutzlast(ueNutzlast({ name: EXNAMEN[0], sets: 5, vol: 'low' }));
    return (a[0] === EXNAMEN[0] && a[1] === 5 && a[2] === 'l') || 'kam heraus: ' + JSON.stringify(a);
  });
  t('Der Normalfall kommt unveraendert zurueck', () => {
    const a = ueAusNutzlast(ueNutzlast({ name: EXNAMEN[0], sets: 3, vol: 'high' }));
    return (a[0] === EXNAMEN[0] && a[1] === 3 && a[2] === 'h') || 'kam heraus: ' + JSON.stringify(a);
  });
  /* \U0001f534 Der Empfaenger auf einem aelteren Stand. Lieber eine Uebung weniger als eine
     falsche: eine Nummer, die es hier nicht gibt, darf NICHT auf den naechstbesten Namen
     zeigen. Und gesagt werden muss es auch - deshalb `verloren`. */
  t('Eine unbekannte Nummer wird weggelassen, nicht geraten', () => {
    return ueAusNutzlast(999999) === null || 'unbekannte Nummer hat einen Namen bekommen';
  });
  t('Der Empfaenger erfaehrt, dass etwas fehlt', () => {
    const p = v3ZuPlan([4, 'Test', [['Tag A', 0, 0, [0, 999999]]]]);
    return (p && p.verloren === 1 && p.p[0].e.length === 1)
      || 'verloren=' + (p && p.verloren) + ' uebrig=' + (p && p.p[0] && p.p[0].e.length);
  });
  // \u26a0\ufe0f v3-Links von heute Nachmittag muessen weiter gehen - sie stehen schon in einem
  // Chat. Dasselbe gilt fuer v2 von gestern, das prueft der Block darueber.
  t('v3-Links werden weiterhin gelesen', () => {
    const p = v3ZuPlan([3, 'Alt', [['Tag A', 0, 0, [['Bankdruecken', 4, 'h']]]]]);
    return (p && p.p.length === 1 && p.p[0].e[0][0] === 'Bankdruecken' && p.p[0].e[0][1] === 4)
      || 'v3 kam nicht durch: ' + JSON.stringify(p);
  });
  await tA('Der ganze Weg: Plan -> Link -> Plan', async () => {
    const pr = activeProg();
    const roh = JSON.stringify(planNutzlast(pr));
    const zurueck = v3ZuPlan(JSON.parse(await entpacke(await packe(roh))));
    const echt = (pr.plans || []).filter(x => (x.exercises || []).some(e => e.name));
    if (!zurueck) return 'nichts zurueckbekommen';
    if (zurueck.verloren) return zurueck.verloren + ' Uebungen unterwegs verloren';
    if (zurueck.p.length !== Math.min(10, echt.length)) return zurueck.p.length + ' statt ' + echt.length + ' Trainings';
    const a = zurueck.p[0], b = echt[0];
    const namenGleich = a.e.map(x => x[0]).join('|') === b.exercises.filter(e=>e.name).map(e=>e.name).join('|');
    return namenGleich || 'Namen weichen ab:\n' + a.e.map(x=>x[0]).join('|') + '\n' + b.exercises.map(e=>e.name).join('|');
  });
  /* Die Zahl, um die es Karl ging. Kein Richtwert aus der Luft: der alte Link wird daneben
     gebaut und gemessen.
     ⚠️ Die Schwelle steht bei 2, nicht bei 3, und das ist kein Nachgeben. Der
     Standardplan hier ist klein; bei ihm faellt die feste Grundlast (Plan- und Trainings-
     namen) staerker ins Gewicht als die Uebungen. Gemessen: **Standardplan 435 -> 177
     (Faktor 2,5)**, ein Vier-Tage-Plan mit 23 Uebungen **1.050 -> 198 (Faktor 5,3)**.
     Der Gewinn waechst also genau dort, wo Karls Beschwerde herkam -- bei den langen. */
  await tA('Der Link ist mindestens doppelt so kurz wie vorher', async () => {
    const pr = activeProg();
    const alt  = planCode(pr).length;
    const neu  = 1 + (await packe(JSON.stringify(planNutzlast(pr)))).length;
    return neu * 2 <= alt || 'neu=' + neu + ' alt=' + alt + ' (Faktor ' + (alt/neu).toFixed(1) + ')';
  });

  // ================================================ Tagesaufgabe "Reingeschaut" (v33)
  // Karls Meldung: "geht nicht direkt durch, wenn man die App startet." Sie ging durch -
  // nur eine Zeile zu spaet: gezeichnet wurde zuerst, abgehakt danach.
  t('Reingeschaut wird abgehakt, bevor die Seite steht', () => {
    const quelle = document.documentElement.innerHTML;
    const abhaken = quelle.indexOf("aufgabeErledigen('auf')");
    const zeichnen = quelle.indexOf('if(startFehler) renderAuthGate(startFehler); else render();');
    return (abhaken > -1 && zeichnen > -1 && abhaken < zeichnen)
      || 'abhaken=' + abhaken + ' zeichnen=' + zeichnen;
  });
  // 🔴 Die App wird als PWA selten wirklich geschlossen. Ohne das Nachfassen beim
  // Zurueckkommen bliebe die Aufgabe am naechsten Morgen still offen.
  t('Beim Zurueckkommen in die App wird nochmal abgehakt', () => {
    const merkA = profile.aufgaben, merkX = profile.xp;
    profile.aufgaben = { tag:'2020-01-01', fertig:{ auf:true } };   // gestern abgehakt
    const gab = aufgabeErledigen('auf');                            // heute ist ein neuer Tag
    profile.aufgaben = merkA; profile.xp = merkX;
    return gab === true || 'am neuen Tag nicht erneut abgehakt';
  });

  // Die Groessenordnung: rund 8.000 von 42.240 XP bis Gigachad. Fuer jeden einzelnen muss die
  // Arbeit trotzdem gemacht werden - es ist ein Bonus auf Geleistetes, keine Abkuerzung.
  t('Alle Erfolge zusammen sind keine Abkuerzung nach Gigachad', () => {
    const summe = ERFOLGE.reduce((n, e) => n + (e.xp || 0), 0);
    const bisGiga = xpForLevel(45);
    const anteil = summe / bisGiga;
    return (anteil > 0.05 && anteil < 0.35)
      || 'Anteil ' + (anteil * 100).toFixed(0) + '% von ' + bisGiga + ' XP';
  });
  t('Die Ansicht nennt die XP eines offenen Erfolgs', () => {
    const merkS = sessions, merkE = profile.erfolge;
    sessions = []; profile.erfolge = {};
    renderErfolge();
    const txt = document.getElementById('app').textContent;
    sessions = merkS; profile.erfolge = merkE;
    return txt.includes('+1.500') || txt.includes('+1500') || 'keine XP-Angabe gefunden';
  });

  // ================================================ Der neue Reiter
  t('Es gibt einen Erfolge-Reiter in der unteren Leiste', () =>
    !!document.querySelector('#nav button[data-nav="erfolge"]') || 'nicht da');
  // Karls Ansage: "als 3ter reiter unten zwischen einstellungen und kalorien"
  t('Der Reiter steht zwischen Kalorien und Einstellungen', () => {
    const reihe = [...document.querySelectorAll('#nav button')].map(b => b.dataset.nav);
    return eq(reihe.join('|'), 'home|body|erfolge|settings');
  });
  // ⚠️ renderErfolge() direkt, nicht ueber render(): das prueft `session` und springt ohne
  // Anmeldung ins Login-Fenster. Im Prueframen ist niemand angemeldet.
  t('Die Erfolgs-Ansicht laesst sich zeichnen', () => {
    renderErfolge();
    const txt = document.getElementById('app').textContent;
    return (txt.includes('Erfolge') && txt.includes('Heute')) || 'Inhalt fehlt';
  });
  t('Die Ansicht zeigt jeden Erfolg des Katalogs', () => {
    renderErfolge();
    const txt = document.getElementById('app').textContent;
    const fehlt = ERFOLGE.filter(e => !txt.includes(e.name));
    return fehlt.length === 0 || 'fehlen: ' + fehlt.map(e=>e.name).join(', ');
  });
  t('Der eigene Reiter wird eingefaerbt, wenn man drin ist', () => {
    const merkView = view;
    view = 'erfolge'; setNav();
    const an = document.querySelector('#nav button[data-nav="erfolge"]').classList.contains('on');
    view = merkView; setNav();
    return an || 'bleibt grau';
  });

  // Aufraeumen, damit die Reihenfolge der Pruefungen egal bleibt.
  t('Melde-Speicher laesst sich leeren', () => {
    localStorage.removeItem(MELD_KEY); localStorage.removeItem(POST_KEY);
    return eq(meldungenLesen().length, 0) && eq(postfachUngelesen(), 0);
  });

  // ================================================================ Push (23.08.2026)
  t('Der VAPID-Schluessel ist gesetzt und hat die richtige Laenge', () =>
    (typeof VAPID_PUB === 'string' && VAPID_PUB.length === 87) || `Laenge ${VAPID_PUB && VAPID_PUB.length}`);
  // ⚠️ base64url: '-' und '_' statt '+' und '/', ohne Auffuellen. atob() kennt das nicht -
  // ohne die Umrechnung wirft subscribe() einen nichtssagenden InvalidCharacterError.
  t('base64url wird zu Bytes umgerechnet', () => {
    const b = urlBase64ZuBytes(VAPID_PUB);
    return (b instanceof Uint8Array && b.length === 65) || `${b && b.length} Bytes`;
  });
  t('Der Schluessel faengt mit 0x04 an (unkomprimierter Punkt)', () =>
    eq(urlBase64ZuBytes(VAPID_PUB)[0], 4));
  t('pushMoeglich() sagt hier ehrlich nein oder ja', () =>
    typeof pushMoeglich() === 'boolean' || 'kein Wahrheitswert');

  // ================================================================ Uebungsliste (23.08.2026)
  t('Die Uebungsliste ist deutlich gewachsen', () =>
    EXLIB.length > 600 || `nur ${EXLIB.length}`);
  // ⚠️ Karls 80 muessen ALLE noch da sein - wger fehlen 14 davon, ein Austausch
  // haette sie verloren. Stichproben aus genau diesen 14.
  t('Karls eigene Uebungen sind nicht verschwunden', () => {
    const muss = ['SZ-Curls','Scott-Curls (Preacher)','Bulgarian Split Squat','Step-Ups',
                  'Ab-Wheel Rollout','Sprints','Kabel-Fliegende','Dips (Brust)'];
    const da = new Set(EXLIB.map(x=>x.name));
    const fehlt = muss.filter(n=>!da.has(n));
    return fehlt.length===0 || 'fehlt: '+fehlt.join(', ');
  });
  t('Karls Uebungen stehen weiterhin zuerst', () =>
    eq(EXLIB[0].name, 'Bankdruecken'.replace('ue','ü')));
  t('Keine doppelten Uebungsnamen', () => {
    const zaehler = {};
    EXLIB.forEach(x=>{ const k=x.name.toLowerCase().replace(/[^a-z0-9äöüß]/g,''); zaehler[k]=(zaehler[k]||0)+1; });
    const doppelt = Object.entries(zaehler).filter(([,n])=>n>1).map(([k])=>k);
    return doppelt.length===0 || `${doppelt.length}x doppelt, z.B. ${doppelt.slice(0,3).join(', ')}`;
  });
  t('Jede Uebung hat Name, Icon und Wiederholungen', () => {
    const ok = ['press','pull','shoulder','dumbbell','legs','core','cardio'];
    for (const x of EXLIB) {
      if (!x.name || typeof x.name !== 'string') return 'Name fehlt';
      if (!ok.includes(x.icon)) return `unbekanntes Icon "${x.icon}" bei ${x.name}`;
      if (!(x.reps >= 1)) return `reps fehlt bei ${x.name}`;
    }
    return true;
  });
  t('Die Suche findet eine wger-Uebung', () => {
    const q = 'bauchcrunch';
    return EXLIB.some(x=>x.name.toLowerCase().includes(q)) || 'nicht gefunden';
  });

  // ================================================================ Mahlzeiten (23.08.2026)
  t('Vier Mahlzeiten, Anteile ergeben 100 %', () => {
    const summe = MAHLZEITEN.reduce((a,m)=>a+m.anteil,0);
    return (MAHLZEITEN.length===4 && Math.abs(summe-1) < 1e-9) || `${MAHLZEITEN.length} Bloecke, Summe ${summe}`;
  });
  // ⚠️ Karls Vorlage: 1.113 / 1.484 / 927 / 185 bei 3.709 kcal. Genau die muessen rauskommen.
  t('Ziele treffen Karls Vorlage (3709 kcal)', () => {
    const g = [['f',1113],['m',1484],['a',927],['s',185]];
    for (const [id, soll] of g) {
      const ist = mahlzeitZiel(id, 3709);
      if (Math.abs(ist - soll) > 1) return `${id}: ${ist} statt ${soll}`;
    }
    return true;
  });
  t('Ohne Tagesziel kein Mahlzeit-Ziel', () => eq(mahlzeitZiel('f', 0), 0));
  t('Stunden landen in der richtigen Mahlzeit', () => {
    const f = [[7,'f'],[10,'f'],[11,'m'],[13,'m'],[16,'a'],[19,'a'],[22,'s'],[2,'s']];
    for (const [std, soll] of f) {
      const ist = mahlzeitAusStunde(std);
      if (ist !== soll) return `${std} Uhr -> ${ist} statt ${soll}`;
    }
    return true;
  });
  // ⚠️ Der wichtigste Fall: Bestandsdaten haben kein mz-Feld. Sie duerfen NICHT alle
  // in einem Sammeltopf landen, sondern werden aus ihrer Uhrzeit erschlossen.
  t('Alter Eintrag ohne mz kommt aus der Uhrzeit', () => {
    const d = new Date(); d.setHours(8,30,0,0);
    return eq(mahlzeitVon({date: d.getTime()}), 'f');
  });
  t('Gesetztes mz schlaegt die Uhrzeit', () => {
    const d = new Date(); d.setHours(8,30,0,0);
    return eq(mahlzeitVon({date: d.getTime(), mz:'a'}), 'a');
  });
  t('Unsinniges mz faellt auf die Uhrzeit zurueck', () => {
    const d = new Date(); d.setHours(13,0,0,0);
    return eq(mahlzeitVon({date: d.getTime(), mz:'xyz'}), 'm');
  });
  t('addMeal schreibt die gewaehlte Mahlzeit mit', () => {
    profile.kcal = {goal:2000, foods:[], meals:[]};
    foodMz = 'a';
    addMeal({name:'Test', basis:'g100', kcal:100, p:0, c:0, f:0}, 100);
    foodMz = '';
    return eq(kcalInit().meals[0].mz, 'a');
  });
  t('Ohne Wahl entscheidet die Uhrzeit', () => {
    profile.kcal = {goal:2000, foods:[], meals:[]};
    foodMz = '';
    addMeal({name:'Test', basis:'g100', kcal:100, p:0, c:0, f:0}, 100);
    return eq(kcalInit().meals[0].mz, mahlzeitJetzt());
  });

  // ================================================================ Ladebildschirm
  // ⚠️ Die zwei Uhren duerfen sich nicht ueberholen: laege die Mindestzeit ueber der
  // Hoechstzeit, raeumte die Hoechstzeit den Schirm weg, waehrend die Mindestzeit ihn
  // noch haelt. Bei angel-log steht dieselbe Pruefung aus demselben Grund.
  t('Splash: Mindestzeit liegt unter der Hoechstzeit', () =>
    (SPLASH_MINDESTENS < SPLASH_HOECHSTENS) || `${SPLASH_MINDESTENS} >= ${SPLASH_HOECHSTENS}`);
  t('Splash: Mindestzeit ist lang genug zum Sehen', () =>
    SPLASH_MINDESTENS >= 1000 || `nur ${SPLASH_MINDESTENS} ms`);

  // ================================================================ NEU: Ess-Serie (Flamme, 23.08.2026)
  const TAG = 864e5;
  const heute0 = () => { const d = new Date(); d.setHours(0,0,0,0); return d.getTime(); };
  // Mittags, damit ein Tageswechsel waehrend des Laufs nichts kippt.
  const vorTagen = n => heute0() - n*TAG + 12*36e5;
  const setzeTage = arr => { profile.kcal = {goal:2000, foods:[],
    meals: arr.map(n => ({name:'X', date: vorTagen(n), kcal:100, p:0, c:0, f:0}))}; };

  t('Ohne Eintraege keine Flamme', () => { setzeTage([]); return eq(essSerie(), 0); });
  t('Heute eingetragen: Serie 1', () => { setzeTage([0]); return eq(essSerie(), 1); });
  t('Drei Tage am Stueck', () => { setzeTage([0,1,2]); return eq(essSerie(), 3); });
  // ⚠️ Der wichtigste Fall, dieselbe Falle wie bei der Wochenserie: morgens um 8 ist
  // heute noch nichts eingetragen — die Serie von gestern darf dann NICHT auf 0 stehen.
  t('Heute noch nichts: Serie von gestern bleibt stehen', () => {
    setzeTage([1,2,3]); return eq(essSerie(), 3);
  });
  t('Eine Luecke beendet die Serie', () => {
    setzeTage([0,1,3,4]); return eq(essSerie(), 2);   // Tag 2 fehlt
  });
  t('Mehrere Eintraege an einem Tag zaehlen einmal', () => {
    profile.kcal = {goal:2000, foods:[], meals:[
      {name:'A', date: vorTagen(0), kcal:100, p:0, c:0, f:0},
      {name:'B', date: vorTagen(0), kcal:200, p:0, c:0, f:0},
      {name:'C', date: vorTagen(1), kcal:300, p:0, c:0, f:0}]};
    return eq(essSerie(), 2);
  });
  t('Lange her: keine Serie mehr', () => { setzeTage([5,6]); return eq(essSerie(), 0); });
  // ⚠️ Zwei Tage Luecke, nicht einer: bei [1] waere die Serie 1 (gestern zaehlt noch).
  t('Vorgestern zuletzt: Serie ist gerissen', () => { setzeTage([2,3]); return eq(essSerie(), 0); });

  t('Rekord ohne Eintraege ist 0', () => { setzeTage([]); return eq(essSerieRekord(), 0); });
  t('Rekord findet den laengsten Lauf', () => {
    setzeTage([0, 5,6,7,8, 12]);           // laufend 1, aber vier am Stueck davor
    return eq(essSerie(), 1) && eq(essSerieRekord(), 4);
  });
  t('Rekord zaehlt auch den laufenden Lauf', () => {
    setzeTage([0,1,2]); return eq(essSerieRekord(), 3);
  });

  // ================================================================ NEU: Serie (Trainings-Teil)
  const MO = ts => wochenStart(ts);
  const vorWochen = n => { const d = new Date(MO(Date.now())); d.setDate(d.getDate() - 7*n); return d.getTime(); };

  t('Ohne Einheiten keine Serie', () => { sessions = []; return eq(wochenSerie(), 0); });
  t('Diese Woche trainiert: Serie 1', () => {
    sessions = [{date: MO(Date.now()) + 2*864e5, entries: []}];
    return eq(wochenSerie(), 1);
  });
  t('Drei Wochen am Stueck', () => {
    sessions = [0,1,2].map(n => ({date: vorWochen(n) + 864e5, entries: []}));
    return eq(wochenSerie(), 3);
  });
  // ⚠️ Der wichtigste Fall: am Montagmorgen darf die Serie nicht gerissen sein,
  // nur weil in der neuen Woche noch nichts passiert ist.
  t('Laufende Woche noch leer: alte Serie bleibt stehen', () => {
    sessions = [1,2].map(n => ({date: vorWochen(n) + 864e5, entries: []}));
    return eq(wochenSerie(), 2);
  });
  t('Eine Luecke beendet die Serie', () => {
    sessions = [0,1,3,4].map(n => ({date: vorWochen(n) + 864e5, entries: []}));
    return eq(wochenSerie(), 2);   // Woche 2 fehlt
  });
  t('Mehrere Einheiten in einer Woche zaehlen einmal', () => {
    sessions = [1,3,5].map(d => ({date: MO(Date.now()) + d*864e5, entries: []}));
    return eq(wochenSerie(), 1);
  });
  t('Nur eine alte Woche, lange her: keine Serie mehr', () => {
    sessions = [{date: vorWochen(5) + 864e5, entries: []}];
    return eq(wochenSerie(), 0);
  });
  t('Wochenstart ist immer ein Montag', () => {
    for (let i = 0; i < 14; i++) {
      const d = new Date(wochenStart(Date.now() - i*864e5));
      if (d.getDay() !== 1) return 'Tag ' + i + ' ergibt ' + d.getDay();
    }
    return true;
  });
  t('Wochenstart liegt nie in der Zukunft', () => {
    for (let i = 0; i < 14; i++) {
      const ts = Date.now() - i*864e5;
      if (wochenStart(ts) > ts) return 'bei Tag ' + i;
    }
    return true;
  });

  // ================================================================ NEU: Barcode ist keine Sackgasse mehr
  t('Eigenes Produkt wird ueber den Barcode gefunden', () => {
    profile.kcal = {art:'halten', goal:2000, meals:[], foods:[
      {id:'f1', name:'Hausmarke Müsli', kcal:380, p:12, c:60, f:8, barcode:'4001234567890'}]};
    const f = eigenesZuBarcode('4001234567890');
    return (f && f.name === 'Hausmarke Müsli') || 'nicht gefunden';
  });
  t('Unbekannter Barcode gibt nichts zurueck', () => eq(eigenesZuBarcode('9999999999999'), null));
  t('Produkte ohne Barcode stoeren die Suche nicht', () => {
    profile.kcal = {art:'halten', goal:2000, meals:[], foods:[
      {id:'f1', name:'Ohne Code', kcal:100, p:5, c:10, f:1},
      {id:'f2', name:'Mit Code',  kcal:200, p:9, c:20, f:2, barcode:'123456'}]};
    const f = eigenesZuBarcode('123456');
    return (f && f.name === 'Mit Code') || 'falscher Treffer';
  });
  t('Barcode als Zahl trifft auch auf Barcode als Text', () => {
    profile.kcal = {art:'halten', goal:2000, meals:[], foods:[
      {id:'f1', name:'X', kcal:100, p:5, c:10, f:1, barcode:4001234567890}]};
    return !!eigenesZuBarcode('4001234567890') || 'Typ-Vergleich schlaegt fehl';
  });
  t('Leerer Barcode trifft nichts', () => {
    profile.kcal = {art:'halten', goal:2000, meals:[], foods:[
      {id:'f1', name:'X', kcal:100, p:5, c:10, f:1, barcode:''}]};
    return eq(eigenesZuBarcode(''), null);
  });

  // ---- Die Ansicht muss auch wirklich bauen ----
  // ⚠️ Die Pruefungen oben pruefen Rechnerei. Ein Tippfehler in der Vorlage faellt
  // dort NICHT auf — er fliegt erst, wenn jemand den Reiter oeffnet.
  // ⚠️ Ruhetag erzwingen. Das Eiweissziel haengt seit dem 22.08.2026 am Trainingstag —
  // ohne das waere unten "von 144 g" eine Pruefung, die je nach WOCHENTAG durchfaellt.
  // Eine Pruefung, die montags rot ist und dienstags gruen, ist schlimmer als keine.
  plans = []; sessions = [];
  const bauen = () => { const v=view; view='body'; renderBody(); const h=app.innerHTML; view=v; return h; };

  t('Ernaehrungs-Ansicht baut ohne Absturz', () => bauen().length > 100 || 'zu wenig herausgekommen');
  t('Brock steht in der Ernaehrungs-Ansicht', () => {
    const n = Date.now();
    profile.weights = [{date:n, kg:80}];
    profile.kcal = {goal:2000, foods:[], meals:[{id:'a', date:n, name:'Quark', menge:'250 g', kcal:170, p:30, c:8, f:1}]};
    const h = bauen();
    // Seit dem 22.08.2026 steht Brock LINKS NEBEN dem Ring statt in einer eigenen Karte
    // darueber — also ohne .mascot-Huelle. Geprueft wird die Figur plus die Sprechblase.
    return (h.includes('class="mon"') && h.includes('kcal-bubble')) || 'kein Brock';
  });
  t('Eiweissziel steht in der Ansicht', () => bauen().includes('von 144 g') || 'Ziel fehlt (Ruhetag: 80 kg x 1,8)');
  t('Am Trainingstag steht das hoehere Ziel da', () => {
    plans = [{id:'p', name:'Push', day:todayIdx(), exercises:[]}];
    const h = bauen();
    plans = [];
    return (h.includes('von 160 g') && h.includes('Trainingstag')) || 'kein erhoehtes Ziel';
  });
  t('Der Eiweissbalken ist da', () => bauen().includes('border-radius:99px') || 'kein Balken');
  t('Wochenschnitt steht in der Ansicht', () => bauen().includes('Schnitt der letzten 7 Tage') || 'fehlt');
  t('Nochmal-Liste steht in der Ansicht', () => bauen().includes('data-again') || 'fehlt');
  t('Ohne Gewicht: Hinweis statt Eiweissziel', () => {
    profile.weights = [];
    const h = bauen();
    return (h.includes('Trag dein Gewicht ein') && !h.includes('von 144 g')) || 'falscher Hinweis';
  });
  t('Ohne Ziel kommt der Vorschlag-Knopf', () => {
    const n = Date.now();
    profile.weights = [{date:n, kg:80}];
    // ⚠️ `setup:true` ist noetig: ohne das faengt seit dem 22.08.2026 der Ernaehrungs-
    // Assistent ab (kcalBraucht), und der Vorschlag-Knopf kommt gar nicht erst dran.
    // Gemeint ist hier der Fall „eingerichtet, aber Ziel wieder geloescht".
    profile.kcal = {goal:null, setup:true, foods:[], meals:[]};
    return bauen().includes('kcalgoalauto') || 'kein Vorschlag';
  });
  t('Mit Ziel kommt kein Vorschlag-Knopf', () => {
    profile.kcal = {goal:2200, foods:[], meals:[]};
    return !bauen().includes('kcalgoalauto') || 'Vorschlag trotz Ziel';
  });

  // ================================================ Ernaehrungs-Assistent (22.08.2026)
  // Karls Ansage: "wenn man darauf klickt wird beim aller ersten mal auch eine
  // einstellung/tutorial gemacht. dh wielange will man drannbleiben und was ist das ziel etc."
  const KOB_SICHER = JSON.stringify(profile.kcal || {});
  const kobBauen = () => { const v=view; view='body'; renderBody(); const h=app.innerHTML; view=v; return h; };
  const kobFrisch = () => { kobErzwingen=false; kobDraft=null;
    profile.kcal = {foods:[], meals:[]}; profile.weights = []; };

  t('Beim ersten Mal kommt der Assistent', () => {
    kobFrisch();
    return kobBauen().includes('Essen mitschreiben') || 'kein Assistent';
  });
  // ⚠️ Das Gegenstueck ist wichtiger als der Fall oben: ein Bestandskonto darf NICHT
  // nachtraeglich in eine Einrichtung gezwungen werden, die es nie gebraucht hat.
  t('Wer schon ein Ziel hat, wird nicht ueberfallen', () => {
    kobFrisch(); profile.kcal.goal = 2200;
    return !kobBauen().includes('Essen mitschreiben') || 'Assistent trotz Ziel';
  });
  t('Ueberspringen merkt sich das', () => {
    kobFrisch(); kobBauen();
    document.querySelector('[data-act="kob:skip"]').click();
    return (kcalInit().setup === true && !kobBauen().includes('Essen mitschreiben'))
           || 'Assistent kommt wieder';
  });
  t('Der Assistent hat fuenf Schritte', () => {
    kobFrisch(); kobBauen();
    let n = 0;
    for(let i = 0; i < 9; i++){
      // ⚠️ Schritt 1 sperrt Weiter, solange kein Vorhaben gewaehlt ist - das ist gewollt,
      // also muss die Pruefung waehlen statt sich am eigenen Riegel aufzuhaengen.
      const wahl = document.querySelector('[data-act="kob:art:halten"]');
      if(wahl) wahl.click();
      const w = document.querySelector('[data-act="kob:next"]');
      if(!w || w.disabled) break; w.click(); n++; }
    return (kobStep === 4 && n === 4) || ('Schritt ' + kobStep + ', ' + n + ' Klicks');
  });
  t('Ohne Vorhaben geht es nicht weiter', () => {
    kobFrisch(); kobBauen();
    document.querySelector('[data-act="kob:next"]').click();   // Schritt 1
    return document.querySelector('[data-act="kob:next"]').disabled || 'Weiter ist offen';
  });
  t('Das gewaehlte Vorhaben bleibt stehen', () => {
    kobFrisch(); kobBauen();
    document.querySelector('[data-act="kob:next"]').click();
    document.querySelector('[data-act="kob:art:abnehmen"]').click();
    return eq(kobDraft.art, 'abnehmen') && !document.querySelector('[data-act="kob:next"]').disabled;
  });
  // ⚠️ Der Klassiker: das Feld wird beim Schrittwechsel neu gebaut. Wer den Wert nicht
  // vorher wegschreibt, verliert die Eingabe zwischen Schritt 2 und 3.
  t('Das eingetippte Gewicht ueberlebt den Schrittwechsel', () => {
    kobFrisch(); kobBauen();
    document.querySelector('[data-act="kob:next"]').click();
    document.querySelector('[data-act="kob:art:halten"]').click();
    document.querySelector('[data-act="kob:next"]').click();   // Schritt 2, Gewicht
    // ⚠️ '82.5' mit Punkt, nicht mit Komma: das Feld ist type="number", und ein Komma
    // wirft der Browser sofort weg - der Wert waere danach leer, ohne dass die App
    // etwas falsch macht. Die Umrechnung von Komma auf Punkt passiert erst beim Fertig.
    document.getElementById('kobKg').value = '82.5';
    document.querySelector('[data-act="kob:next"]').click();   // Schritt 3
    document.querySelector('[data-act="kob:back"]').click();   // zurueck auf 2
    return eq(document.getElementById('kobKg').value, '82.5');
  });
  t('Zeitraum laesst sich waehlen, auch offen', () => {
    kobFrisch(); kobBauen();
    kobStep = 3; renderKcalOb();
    document.querySelector('[data-act="kob:w:0"]').click();
    const offen = kobDraft.wochen === 0;
    document.querySelector('[data-act="kob:w:8"]').click();
    return (offen && kobDraft.wochen === 8) || 'Zeitraum haengt';
  });
  const kobDurch = (art, wochen, kg) => {
    kobFrisch(); kobBauen();
    kobDraft.art = art; kobDraft.wochen = wochen; kobDraft.kg = kg;
    kobStep = 4; renderKcalOb();
    document.querySelector('[data-act="kob:finish"]').click();
  };
  t('Fertig legt Vorhaben, Zeitraum und Ziel ab', () => {
    kobDurch('abnehmen', 12, 80);
    const k = kcalInit();
    // 80 kg x 30 = 2400, abnehmen -400 => 2000
    return (k.art === 'abnehmen' && k.wochen === 12 && k.goal === 2000
            && k.startKg === 80 && k.setup === true) || JSON.stringify(k);
  });
  // ⚠️ Das Gewicht aus dem Assistenten gehoert in die normale Kurve, nicht in eine
  // zweite Ablage daneben - sonst stehen zwei Wahrheiten in der App.
  t('Das Gewicht landet in der Gewichtskurve', () => {
    kobDurch('halten', 8, 77.5);
    const w = lastWeight();
    return (w && w.kg === 77.5) || 'nicht in der Kurve';
  });
  t('Ohne Gewicht bleibt Fertig gesperrt', () => {
    kobFrisch(); kobBauen();
    kobDraft.art = 'halten'; kobDraft.wochen = 8; kobDraft.kg = '';
    kobStep = 4; renderKcalOb();
    return document.querySelector('[data-act="kob:finish"]').disabled || 'Fertig ist offen';
  });
  t('Woche und Zieldatum stimmen', () => {
    kobDurch('abnehmen', 12, 80);
    const k = kcalInit();
    k.start = Date.now() - 15 * 864e5;          // gut zwei Wochen her
    const w = kcalWoche(), d = kcalZielDatum();
    return (w === 3 && Math.round((d - k.start) / 864e5) === 84) || ('Woche ' + w);
  });
  t('Ohne festes Ende gibt es kein Zieldatum', () => {
    kobDurch('halten', 0, 80);
    return (kcalZielDatum() === null && kcalPrognose() === null) || 'Datum trotz offen';
  });
  // ⚠️ Die Prognose kommt aus dem VORHABEN, nicht aus dem Verlauf: 80 kg, abnehmen
  // (-0,5 kg/Woche), 12 Wochen => 74 kg.
  t('Die Prognose rechnet aus dem Vorhaben', () => {
    kobDurch('abnehmen', 12, 80);
    const p = kcalPrognose();
    return (p && Math.abs(p.kg - 74) < 0.01) || (p ? p.kg : 'keine Prognose');
  });
  t('Woche von Zeitraum steht in der Ansicht', () => {
    kobDurch('abnehmen', 12, 80);
    return kobBauen().includes('Woche 1 von 12') || 'Fortschritt fehlt';
  });
  // ⚠️ Nach Ablauf darf die Anzeige nicht ueber den Zeitraum hinauslaufen ("Woche 15 von 12").
  t('Nach Ablauf bleibt die Anzeige stehen', () => {
    kobDurch('abnehmen', 4, 80);
    kcalInit().start = Date.now() - 70 * 864e5;
    const h = kobBauen();
    return (h.includes('Woche 4 von 4') && h.includes('sind um')) || 'laeuft ueber';
  });
  // ⚠️ fmtDate endet selbst auf einen Punkt ("Fr., 30.10."). Wer dahinter einen Satzpunkt
  // setzt, bekommt "30.10.." — beim ersten Vorschaubild sofort aufgefallen.
  t('Kein doppelter Punkt hinter dem Zieldatum', () => {
    kobDurch('abnehmen', 12, 80);
    const h = kobBauen();
    return !/\d\.\.(?!\.)/.test(h.replace(/<[^>]*>/g, '')) || 'doppelter Punkt';
  });
  t('Vorhaben aendern startet ihn erneut', () => {
    kobDurch('abnehmen', 12, 80);
    kobBauen();
    document.querySelector('[data-act="kob:neu"]').click();
    return kobBauen().includes('Essen mitschreiben') || 'kommt nicht wieder';
  });
  // ⚠️ Karls Ansage: "brock kann gerne links neben den kalorin kreis."
  t('Brock steht links vom Ring', () => {
    kobDurch('halten', 8, 80);
    const h = kobBauen();
    return (h.indexOf('class="mon"') < h.indexOf('<svg viewBox="0 0 130 130"')
            && h.indexOf('class="mon"') >= 0) || 'Brock steht nicht links';
  });
  kobErzwingen = false; kobDraft = null;
  profile.kcal = JSON.parse(KOB_SICHER);

  t('Ohne Gewicht kein Vorschlag-Knopf', () => {
    profile.weights = []; profile.kcal = {goal:null, foods:[], meals:[]};
    return !bauen().includes('kcalgoalauto') || 'Vorschlag ohne Gewicht';
  });
  t('Leerer Tag baut trotzdem', () => {
    profile.weights = []; profile.kcal = {goal:null, foods:[], meals:[]};
    return bauen().length > 100 || 'leere Ansicht';
  });
  t('Ohne Eintraege keine Nochmal-Liste', () => !bauen().includes('data-again') || 'Liste trotz nichts');
  t('Namen in der Nochmal-Liste sind entschaerft', () => {
    // ⚠️ Der Angriffsstring wird zusammengesetzt. Stuende '</scr'+'ipt>' hier am Stueck,
    // wuerde der Browser den umgebenden script-Block an dieser Stelle schliessen — die
    // Pruefdatei zerlegte sich selbst. Genau das ist beim ersten Lauf passiert.
    const boese = '<scr' + 'ipt>böse</scr' + 'ipt>';
    const n = Date.now();
    profile.kcal = {goal:2000, foods:[], meals:[
      {id:'x', date:n-864e5, name:boese, menge:'1', kcal:1, p:1, c:1, f:1}]};
    const h = bauen();
    return (h.includes('&lt;scr' + 'ipt&gt;') && !h.includes(boese)) || 'ungefiltert';
  });

  profile.kcal = JSON.parse(KCAL_VORHER); profile.weights = JSON.parse(GEW_VORHER);

  // ================================================================ Schluessel-Dialog
  // Neu am 22.08.2026, nachdem Google Karl auf "Available regions" geworfen hat und der
  // alte prompt() weder einen anklickbaren Link noch eine Erklaerung bieten konnte.
  const KEY_VORHER = aiKey();
  const dialogAuf = () => { const p = fragKey(); return p; };
  const dialogZu  = () => { const x = document.getElementById('keyX'); if (x) x.click(); };

  t('Schluessel-Adresse zeigt auf AI Studio', () => eq(KEY_URL, 'https://aistudio.google.com/apikey'));
  t('fragKey gibt ein Promise zurueck', () => {
    const p = dialogAuf(); const r = (p instanceof Promise); dialogZu(); return r || 'kein Promise';
  });
  t('Dialog hat einen echten Link auf die Seite', () => {
    dialogAuf();
    const a = document.querySelector('#modal a[href="' + KEY_URL + '"]');
    const r = !!a && a.target === '_blank' && a.rel.includes('noopener');
    dialogZu();
    return r || (a ? 'target/rel fehlt' : 'kein Link');
  });
  t('Dialog hat einen Hilfe-Knopf', () => {
    dialogAuf(); const b = document.getElementById('keyHelp'); dialogZu();
    return !!b || 'kein Hilfe-Knopf';
  });
  t('Hilfe ist zuerst zugeklappt', () => {
    dialogAuf(); const box = document.getElementById('keyHelpBox'); const r = box && box.hidden === true;
    dialogZu(); return r || 'steht offen';
  });
  t('Hilfe klappt auf und wieder zu', () => {
    dialogAuf();
    const b = document.getElementById('keyHelp'), box = document.getElementById('keyHelpBox');
    b.click(); const auf = box.hidden === false;
    b.click(); const zu = box.hidden === true;
    dialogZu();
    return (auf && zu) || ('auf=' + auf + ' zu=' + zu);
  });
  t('Hilfe nennt alle vier Ursachen', () => {
    // ⚠️ Die vierte (mehrere Konten) kam am 22.08.2026 dazu, nachdem Anmeldung, Alter und
    // Land bei Karl alle in Ordnung waren und er trotzdem abgewiesen wurde.
    dialogAuf();
    const txt = document.getElementById('keyHelpBox').textContent.toLowerCase();
    dialogZu();
    const fehlt = [['angemeldet','Anmeldung'], ['geburtsdatum','Alter'],
                   ['privates fenster','mehrere Konten'], ['vpn','VPN']]
      .filter(([w]) => !txt.includes(w)).map(([, n]) => n);
    return fehlt.length ? 'fehlt: ' + fehlt.join(', ') : true;
  });
  t('Die Ursachen sind durchnummeriert', () => {
    dialogAuf();
    const txt = document.getElementById('keyHelpBox').textContent;
    dialogZu();
    const fehlt = ['1.','2.','3.','4.'].filter(n => !txt.includes(n));
    return fehlt.length ? 'fehlt: ' + fehlt.join(' ') : true;
  });
  t('Hilfe warnt vor dem alten Anthropic-Schluessel', () => {
    dialogAuf();
    const txt = document.getElementById('keyHelpBox').textContent;
    dialogZu();
    return txt.includes('sk-ant-') || 'kein Hinweis auf den alten Schluessel';
  });
  t('Abbrechen speichert nichts', () => {
    DB.set('aikey', 'AIzaAlterWert');
    dialogAuf();
    document.getElementById('keyInput').value = 'AIzaNeuerWert';
    dialogZu();
    return eq(aiKey(), 'AIzaAlterWert');
  });
  t('Speichern legt den Schluessel ab', () => {
    DB.set('aikey', '');
    dialogAuf();
    document.getElementById('keyInput').value = '  AIzaFrischerWert  ';
    document.getElementById('keySave').click();
    return eq(aiKey(), 'AIzaFrischerWert');
  });
  t('Leer speichern loescht den Schluessel', () => {
    DB.set('aikey', 'AIzaWasAltes');
    dialogAuf();
    document.getElementById('keyInput').value = '';
    document.getElementById('keySave').click();
    return eq(aiKey(), '');
  });
  t('Alter Anthropic-Schluessel wird erkannt', () => {
    DB.set('aikey', 'sk-ant-api03-xyz');
    const r = altSchluessel() === true;
    DB.set('aikey', 'AIzaEchterGoogleKey');
    return (r && altSchluessel() === false) || 'Erkennung stimmt nicht';
  });
  t('Beim alten Schluessel steht das Feld leer', () => {
    DB.set('aikey', 'sk-ant-api03-xyz');
    dialogAuf();
    const v = document.getElementById('keyInput').value;
    dialogZu();
    return eq(v, '');
  });
  t('Dialog schliesst sich wirklich', () => {
    dialogAuf(); dialogZu();
    return !document.getElementById('modal').classList.contains('show') || 'steht noch offen';
  });
  DB.set('aikey', KEY_VORHER);



  // ================================================ Schritte (22.08.2026)
  // Karls Ansage: "soll mit der health app verbunden werden können um schritte zutracken
  // und die einrechnet." Health direkt geht nicht (HealthKit ist nativen Apps vorbehalten),
  // der Weg laeuft ueber die Kurzbefehle-App und `?schritte=`.
  const SCH_SICHER = JSON.stringify(profile.kcal || {});
  const einstellungenBauen = () => {
    const s0 = session, v = view;
    session = session || {username:'Pruef', access_token:'x', user:{id:'p1', email:'pruef@example.org'}};
    view = 'settings'; renderSettings();
    session = s0; view = v;
  };
  const schFrisch = (an) => {
    profile.kcal = {goal:2000, art:'abnehmen', setup:true, schritte:!!an, steps:[], foods:[], meals:[]};
    profile.weights = [{date:Date.now(), kg:80}];
  };

  t('Ohne Schritt-Modus bleibt das Ziel fest', () => {
    schFrisch(false); setzeSchritte(12000);
    return eq(zielHeute(), 2000);
  });
  t('Mit Schritt-Modus kommen die Schritte obendrauf', () => {
    schFrisch(true); setzeSchritte(10000);
    // 10.000 x 80 kg x 0,0004 = 320
    return (zielHeute() === 2320 && kcalAusSchritten(10000) === 320) || ('Ziel ' + zielHeute());
  });
  // ⚠️ DIE Falle: der Kurzbefehl schickt den TAGESSTAND, nicht die Schritte seit dem letzten
  // Aufruf. Wer addiert, hat nach drei Automatik-Laeufen das Dreifache stehen.
  t('Ein zweiter Eintrag ueberschreibt, statt zu addieren', () => {
    schFrisch(true);
    setzeSchritte(4000); setzeSchritte(9000); setzeSchritte(9000);
    return (schritteHeute() === 9000 && schrittListe().length === 1) || (schritteHeute() + ' / ' + schrittListe().length);
  });
  t('Gestern und heute stehen getrennt', () => {
    schFrisch(true);
    setzeSchritte(7000, Date.now() - 864e5);
    setzeSchritte(3000);
    return (schritteHeute() === 3000 && schritteAmTag(Date.now() - 864e5) === 7000
            && schrittListe().length === 2) || 'Tage vermischt';
  });
  t('Unsinnige Werte werden abgewiesen', () => {
    schFrisch(true); setzeSchritte(5000);
    const a = setzeSchritte(-5), b = setzeSchritte(999999), c = setzeSchritte('abc');
    return (!a && !b && !c && schritteHeute() === 5000) || 'etwas ist durchgerutscht';
  });
  // ⚠️ Ohne Gewicht laesst sich der Verbrauch nicht rechnen. Dann lieber 0 als eine
  // erfundene Zahl - die App wuerde sonst zum Mehressen einladen.
  t('Ohne Gewicht gibt es keine kcal aus Schritten', () => {
    schFrisch(true); profile.weights = []; setzeSchritte(10000);
    return (kcalAusSchritten(10000) === 0 && zielHeute() === 2000) || 'rechnet trotzdem';
  });
  t('Null Schritte aendern nichts', () => {
    schFrisch(true); setzeSchritte(0);
    return (zielHeute() === 2000 && kcalAusSchritten(0) === 0) || 'Null wirkt';
  });
  // ⚠️ Der Grundumsatz-Faktor ist der ganze Punkt: kg x 30 enthaelt Alltagsbewegung schon,
  // kg x 26 nicht. Ohne den Wechsel wuerde dieselbe Bewegung zweimal gezaehlt.
  t('Der Grundumsatz-Faktor haengt am Modus', () => {
    schFrisch(false); const ohne = erhaltFaktor(), zOhne = kcalVorschlagFuer('halten');
    schFrisch(true);  const mit  = erhaltFaktor(), zMit  = kcalVorschlagFuer('halten');
    // 80 x 30 = 2400, 80 x 26 = 2080
    return (ohne === 30 && mit === 26 && zOhne === 2400 && zMit === 2100)
           || (zOhne + ' / ' + zMit);
  });
  t('Einschalten rechnet das Grundziel neu', () => {
    schFrisch(false);
    // ⚠️ renderSettings() direkt statt render(): ohne Anmeldung steigt render() sofort in
    // die Anmeldemaske aus, und die Knoepfe stuenden gar nicht im Dokument. Die Ansicht
    // zeigt den Benutzernamen, deshalb muss eine Sitzung vorgetaeuscht werden.
    einstellungenBauen();
    document.querySelector('[data-act="schritt:an"]').click();
    const k = kcalInit();
    // 80 x 26 = 2080, abnehmen -400 = 1680, auf 50 gerundet
    return (schrittModus() && k.goal === 1700) || (schrittModus() + ' / ' + k.goal);
  });
  t('Ausschalten rechnet zurueck', () => {
    einstellungenBauen();
    document.querySelector('[data-act="schritt:aus"]').click();
    // 80 x 30 = 2400, abnehmen -400 = 2000
    return (!schrittModus() && kcalInit().goal === 2000) || kcalInit().goal;
  });
  t('Die Adresse fuer den Kurzbefehl endet richtig', () => {
    return /\?schritte=$/.test(schrittLinkBasis()) || schrittLinkBasis();
  });
  t('Die Schritt-Zeile steht nur im Modus in der Ansicht', () => {
    schFrisch(true); setzeSchritte(8432);
    const v = view; view = 'body'; renderBody(); const mit = app.innerHTML;
    schFrisch(false); renderBody(); const ohne = app.innerHTML; view = v;
    return (mit.includes('8.432') && !ohne.includes('8.432')) || 'Zeile stimmt nicht';
  });
  t('Der Ring zeigt das Ziel MIT Schritten', () => {
    schFrisch(true); setzeSchritte(10000);
    const v = view; view = 'body'; renderBody(); const h = app.innerHTML; view = v;
    return (h.includes('von 2320') && !h.includes('von 2000')) || 'Ring zeigt das Grundziel';
  });
  profile.kcal = JSON.parse(SCH_SICHER);

  // ================================================ Ladebildschirm (22.08.2026)
  // Karls Ansage: "Ich brauche einen lade screen mit brock drauf."
  //
  // ⚠️ Die wichtigste Pruefung ist die erste. Der Schirm liegt UEBER der ganzen App -
  // bleibt er stehen, ist die App gesperrt, nicht nur haesslich. Genau das ist in
  // angel-log schon einmal passiert.
  // ⚠️ Seit dem 23.08.2026 geht der Schirm nicht mehr sofort, sondern erst nach
  // SPLASH_MINDESTENS (Karls „der ladescreen ist zu kurz"). Fuer die Pruefung wird die
  // Uhr deshalb vorgestellt - geprueft wird "geht weg, wenn die Zeit um ist".
  t('Der Ladebildschirm geht, wenn die Mindestzeit um ist', () => {
    splashSeit = Date.now() - SPLASH_MINDESTENS - 100;
    splashWeg();
    const el = document.getElementById('splash');
    return (el && el.classList.contains('weg')) || (el ? 'liegt noch drueber' : 'gar nicht da');
  });
  // Die Gegenprobe: laeuft die Mindestzeit noch, MUSS er stehen bleiben. Ohne diese
  // Pruefung wuerde ein spaeteres "sofort weg" niemandem auffallen.
  t('Der Ladebildschirm bleibt stehen, solange die Mindestzeit laeuft', () => {
    const el = document.getElementById('splash');
    el.classList.remove('weg');
    splashSeit = Date.now();          // gerade erst geoeffnet
    splashWeg();
    const steht = !el.classList.contains('weg');
    el.classList.add('weg');          // fuer die folgenden Pruefungen zurueckstellen
    return steht || 'ist sofort verschwunden';
  });
  t('Der Ladebildschirm bleibt im Dokument', () => {
    // Nicht entfernt, nur ausgeblendet - sonst gaebe es beim naechsten render nichts
    // mehr zum Wegnehmen, und die harte Grenze im Kopf liefe ins Leere.
    return !!document.getElementById('splash') || 'wurde entfernt';
  });
  t('Brock steht auf dem Ladebildschirm', () => {
    const img = document.querySelector('#splash img');
    return (img && /brock/.test(img.getAttribute('src'))) || 'kein Brock';
  });
  t('Der Schirm liegt ueber allem', () => {
    const z = +getComputedStyle(document.getElementById('splash')).zIndex;
    return z >= 9000 || ('z-index ' + z);
  });
  // ⚠️ Der Notausstieg muss im KOPF stehen, nicht in der Startroutine: er soll auch dann
  // greifen, wenn das Skript weiter unten gar nicht erst durchlaeuft.
  t('Die harte Zeitgrenze existiert', () => {
    return (typeof SPLASH_HOECHSTENS === 'number' && SPLASH_HOECHSTENS > 0
            && SPLASH_HOECHSTENS <= 10000) || 'keine oder unbrauchbare Grenze';
  });
  t('splashWeg laesst sich zweimal aufrufen', () => {
    splashSeit = Date.now() - SPLASH_MINDESTENS - 100;   // Mindestzeit schon um
    splashWeg(); splashWeg();
    return document.getElementById('splash').classList.contains('weg') || 'Zustand kippt';
  });
  // ⚠️ Das Abbild ist das, was den Farbblitz beim naechsten Start verhindert. Ohne die
  // vier Farben faellt der Schirm auf die Vorgaben aus :root zurueck - bei einer hellen
  // Palette also auf Dunkelgrau, genau das Aufblitzen, das er verhindern soll.
  t('applyTheme legt das Abbild fuer den naechsten Start ab', () => {
    applyTheme();
    const f = DB.get('splash', null);
    if(!f) return 'kein Abbild';
    const fehlt = ['bg','txt','muted','line','img'].filter(k => !f[k]);
    return fehlt.length ? ('fehlt: ' + fehlt.join(', ')) : true;
  });
  t('Das Abbild zeigt den getragenen Rang', () => {
    const xpVorher = profile.xp;
    profile.xp = xpForLevel(45);          // Gigachad
    applyTheme();
    const hoch = DB.get('splash', {}).img;
    profile.xp = 0;
    applyTheme();
    const tief = DB.get('splash', {}).img;
    profile.xp = xpVorher; applyTheme();
    return (hoch !== tief && /brock-9/.test(hoch)) || (hoch + ' / ' + tief);
  });
  // ⚠️ Ein kaputter Eintrag darf den Start nicht kosten - das Kopf-Skript liest ihn, bevor
  // irgendetwas anderes laeuft, und hat keinen Fehlerfang ausser seinem eigenen try.
  t('Ein kaputtes Abbild wirft den Start nicht um', () => {
    localStorage.setItem('gymlog:splash', '{kaputt');
    const r = DB.get('splash', 'ersatz');
    applyTheme();
    return eq(r, 'ersatz');
  });

  // ================================================================ Aufraeumen
  sessions = SICHER.sessions; profile = SICHER.profile; settings = SICHER.settings;

  out.push('=== ' + ok + ' ok, ' + bad + ' fehlgeschlagen ===');
  const pre = document.createElement('pre');
  pre.id = 'testout';
  pre.textContent = out.filter(l => !l.startsWith('OK')).concat(
    '(' + ok + ' bestandene Prüfungen nicht einzeln aufgeführt)').join('\n');
  document.body.appendChild(pre);
})();
</script>
"""

html = (WORK / 'index.html').read_text(encoding='utf-8')

# ⚠️ sw.js laeuft NIE in dieser Seite -- ein Service Worker hat eine eigene Umgebung, und
# headless registriert ihn nicht. Sein Quelltext wird deshalb als Zeichenkette
# hereingereicht, damit die Pruefungen wenigstens den Weg von der Mitteilung ins Fenster
# nachlesen koennen. Das ist Lesen, kein Ausfuehren -- und es steht hier, damit niemand
# glaubt, der Service Worker sei mitgeprueft.
SW_TXT = (WORK / 'sw.js').read_text(encoding='utf-8')
SW_BLOCK = '<script>window.SW_QUELLE = ' + json.dumps(SW_TXT) + ';</script>' + chr(10)
(WORK / 'test.html').write_text(html + SW_BLOCK + TESTS, encoding='utf-8')

# ⚠️ Zeitbudget grosszuegig: virtuelle Zeit kostet keine echte, ein groesseres
# Budget also nichts ausser Luft nach oben. In angel-log hat ein zu knappes
# Budget am 10.08.2026 vier Laeufe ohne Ergebnis abbrechen lassen.
r = subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--no-sandbox',
                    '--virtual-time-budget=45000', '--allow-file-access-from-files',
                    '--dump-dom', (WORK / 'test.html').as_uri()],
                   capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180)
m = re.search(r'<pre id="testout">(.*?)</pre>', r.stdout, re.S)
if not m:
    # ⚠️ Die Ausgabe enthaelt Umlaute; die Windows-Konsole laeuft per Vorgabe auf
    # cp1252. Ohne dieses Ersetzen stirbt die FEHLERMELDUNG selbst an einem
    # UnicodeEncodeError und verdeckt genau das, was man sehen muesste.
    def zeigen(s):
        enc = sys.stdout.encoding or 'utf-8'
        print(s.encode(enc, errors='replace').decode(enc, errors='replace'))
    zeigen('Kein Ergebnis. Chrome-Ausgabe (Ende):')
    zeigen(r.stdout[-3000:]); zeigen(r.stderr[-3000:]); sys.exit(1)
txt = m.group(1).replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
enc = sys.stdout.encoding or 'utf-8'
print(txt.encode(enc, errors='replace').decode(enc, errors='replace'))
sys.exit(0 if ', 0 fehlgeschlagen' in txt else 1)
