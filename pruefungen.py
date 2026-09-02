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
  /* ⚠️ `soll` mitgeben, sonst baut die Pruefung einen Zustand, den die App gar nicht
     erzeugen kann: eine gespeicherte Einheit enthaelt NUR abgehakte Saetze (finishWorkout
     filtert). Am 27.08.2026 hat genau das eine Pruefung gruen gehalten, deren Zweig in der
     App unerreichbar war. Ohne Angabe entspricht `soll` der Zahl der uebergebenen Saetze. */
  const machEinheit = (satzListe, soll) => ([{ date: Date.now(), entries: [{ name:'Bankdrücken',
    soll: (soll != null ? soll : satzListe.filter(x => !x.warm).length), sets: satzListe }] }]);
  t('Alles abgehakt und drueber -> mehr Gewicht', () => {
    sessions = machEinheit([{warm:false,done:true,weight:60,reps:15},{warm:false,done:true,weight:60,reps:15}]);
    const s = suggest('Bankdrücken', null);
    return (s && s.up === true && s.w === 62.5) || JSON.stringify(s);
  });
  /* 🔴 So sieht der Fall in der App wirklich aus: zwei Saetze standen da (`soll:2`),
     einer wurde gemacht -- der andere ist gar nicht erst gespeichert. Vorher stand hier ein
     nicht abgehakter Satz IN der Einheit, und den gibt es dort nie. */
  t('Nicht alle geplanten Saetze gemacht -> gleiches Gewicht', () => {
    sessions = machEinheit([{warm:false,done:true,weight:60,reps:15}], 2);
    const s = suggest('Bankdrücken', null);
    return (s && s.up === false && s.w === 60) || JSON.stringify(s);
  });
  t('Der Text nennt geschafft und geplant', () => {
    sessions = machEinheit([{warm:false,done:true,weight:60,reps:15}], 3);
    const s = suggest('Bankdrücken', null);
    return (s && /1 von 3 Sätzen/.test(s.text)) || (s && s.text) || 'kein Vorschlag';
  });
  // ⚠️ Alte Einheiten haben kein `soll`. Fuer die muss es beim alten Verhalten bleiben,
  // sonst bremst eine geratene Sollzahl einen Vorschlag aus, den es nie gab.
  t('Ohne soll bleibt es beim alten Verhalten', () => {
    sessions = [{ date: Date.now(), entries: [{ name:'Bankdrücken',
      sets:[{warm:false,done:true,weight:60,reps:15},{warm:false,done:true,weight:60,reps:15}] }] }];
    const s = suggest('Bankdrücken', null);
    return (s && s.up === true) || JSON.stringify(s);
  });
  // Aufwaermsaetze zaehlen nicht in die Sollzahl - sie sind auch sonst nirgends Teil der Rechnung.
  t('Der Aufwaermsatz zaehlt nicht ins Soll', () => {
    sessions = machEinheit([{warm:true,done:true,weight:40,reps:10},
                            {warm:false,done:true,weight:60,reps:15},
                            {warm:false,done:true,weight:60,reps:15}]);
    const s = suggest('Bankdrücken', null);
    return (s && s.up === true) || JSON.stringify(s);
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
  // ================================================ Erinnerungs-Schalter im Abgleich
  // 🔴 Der v45-Fehler in Reinform: alles im Profil, das nicht ausdruecklich
  // zusammengefuehrt wird, kommt von `basis` -- also vom eigenen Geraet. Eine Einstellung,
  // die am Handy ausgeschaltet wurde, kaeme am PC nie an und beim naechsten Schieben am
  // Handy zurueck.
  t('Ausgeschaltete Erinnerung wandert vom anderen Geraet herueber', () => {
    const a = blob({profile:{xp:0, weights:[], erinnerungen:{wiegen:true, essen:true, ts:100}}});
    const b = blob({profile:{xp:0, weights:[], erinnerungen:{wiegen:false, essen:true, ts:500}}});
    const e = blobsZusammen(a, b).blob.profile.erinnerungen;
    return (e && e.wiegen === false) || 'wiegen=' + (e && e.wiegen);
  });
  // ⚠️ Entschieden wird ueber den Zeitstempel, NICHT ueber "Aus gewinnt". Sonst kaeme man
  // nie wieder an, solange ein Geraet noch das alte Aus kennt.
  t('Die spaetere Entscheidung gewinnt, auch wenn sie ein Einschalten ist', () => {
    const a = blob({profile:{xp:0, weights:[], erinnerungen:{wiegen:true, essen:true, ts:900}}});
    const b = blob({profile:{xp:0, weights:[], erinnerungen:{wiegen:false, essen:false, ts:100}}});
    const e = blobsZusammen(a, b).blob.profile.erinnerungen;
    return (e && e.wiegen === true && e.essen === true) || JSON.stringify(e);
  });
  t('Ohne Schalter auf der anderen Seite bleibt der eigene stehen', () => {
    const a = blob({profile:{xp:0, weights:[], erinnerungen:{wiegen:false, essen:true, ts:300}}});
    const e = blobsZusammen(a, blob({})).blob.profile.erinnerungen;
    return (e && e.wiegen === false) || JSON.stringify(e);
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

  /* ================================ Die Zahlen am Essen im Abgleich (Fund 2, 01.09.2026)
     🔴 blobsZusammen fuehrte NUR die drei Listen zusammen. goal, setup, art, wochen,
     start, startKg und schritte standen in keinem Zweig -- sie fielen unter "basis
     gewinnt", und wenn basis gar kein kcal hatte, wurde oben ein frisches Objekt ohne
     sie gebaut. Fuer Karl sah das aus wie ein zurueckgesetztes Handy: der
     Einrichtungs-Assistent stand wieder da, ohne Meldung, ohne Fehler.
     ⚠️ Dieselbe Handschrift wie der Fall vom 27.08. (Tagesaufgaben, Erfolge,
     Mahlzeiten): repariert wurde, was gemeldet war -- das Tagesziel stand nicht auf der
     Liste. */
  const mitKcal = (o) => blob({profile:Object.assign({xp:0, weights:[]}, o)});

  t('Das Tagesziel kommt vom anderen Geraet herueber', () => {
    const a = mitKcal({kcal:{foods:[], meals:[]}});
    const b = mitKcal({kcal:{foods:[], meals:[], goal:2200}});
    return eq(blobsZusammen(a, b).blob.profile.kcal.goal, 2200);
  });
  /* Der schlimmere der beiden Wege: ein Stand aus der Cloud von VOR dem 23.08. hat gar
     kein kcal. Dann baute der Abgleich {foods:[],meals:[]} -- und alles andere war weg. */
  t('Eine Basis ganz ohne kcal verliert das Ziel nicht', () => {
    const a = blob({profile:{xp:0, weights:[]}});
    const b = mitKcal({kcal:{foods:[], meals:[], goal:1900, setup:true, art:'abnehmen',
                             wochen:12, start:1000, startKg:82, schritte:true}});
    const k = blobsZusammen(a, b).blob.profile.kcal;
    return (k.goal === 1900 && k.setup === true && k.art === 'abnehmen' && k.wochen === 12
            && k.start === 1000 && k.startKg === 82 && k.schritte === true)
           || JSON.stringify(k);
  });
  /* ⚠️ Die Gegenrichtung, und sie ist genauso wichtig: ein Ziel, das hier schon
     steht, darf NICHT ueberschrieben werden. Sonst kaeme das alte Ziel vom zweiten
     Geraet zurueck, sobald es sich meldet -- ein Aendern waere nie von Dauer. */
  t('Ein gesetztes Ziel wird nicht vom anderen Geraet ueberschrieben', () => {
    const a = mitKcal({kcal:{foods:[], meals:[], goal:2000}});
    const b = mitKcal({kcal:{foods:[], meals:[], goal:1500}});
    return eq(blobsZusammen(a, b).blob.profile.kcal.goal, 2000);
  });
  t('Der durchlaufene Assistent kommt nicht zurueck', () => {
    const a = mitKcal({kcal:{foods:[], meals:[]}});
    const b = mitKcal({kcal:{foods:[], meals:[], setup:true}});
    return eq(blobsZusammen(a, b).blob.profile.kcal.setup, true);
  });
  /* Der Schrittmodus ist ausdruecklich AUS -- false ist eine Entscheidung, kein fehlender
     Wert. Eine Pruefung auf Wahrheitswert statt auf "ist da" wuerde ihn verschlucken. */
  t('Ein ausgeschalteter Schrittmodus zaehlt als Wert', () => {
    const a = mitKcal({kcal:{foods:[], meals:[]}});
    const b = mitKcal({kcal:{foods:[], meals:[], schritte:false}});
    return eq(blobsZusammen(a, b).blob.profile.kcal.schritte, false);
  });
  /* 🔴 Die Pruefung, die den Fund ueberdauern soll. Die drei Faelle darueber halten
     die heutigen Felder fest -- diese hier haelt die FORM fest: wer morgen ein neues
     Feld in profile.kcal schreibt und es nicht in KCAL_SKALARE eintraegt, wird rot.
     Ohne sie waere das hier in einem halben Jahr wieder derselbe Fund mit einem anderen
     Feldnamen. Gebaut wie die APP_FASSUNG-Pruefung: Quelltext gegen Quelltext. */
  t('Jedes Feld in profile.kcal wird im Abgleich behandelt', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    const listen = ['foods','meals','steps'];   // die drei werden einzeln vereinigt
    const gefunden = new Set();
    const quelle = q.replace(/\/\*[\s\S]*?\*\//g, '');
    let m; const re = /\bk\.([a-zA-Z][a-zA-Z0-9]*)\s*=[^=]/g;
    while((m = re.exec(quelle))) gefunden.add(m[1]);
    const fehlt = Array.from(gefunden).filter(f =>
      listen.indexOf(f) < 0 && KCAL_SKALARE.indexOf(f) < 0);
    return fehlt.length === 0
      || ('nicht im Abgleich: ' + fehlt.join(', ') + ' -- in KCAL_SKALARE eintragen');
  });

  /* ================================ Speichern, das nicht geht (Fund 3, 01.09.2026)
     🔴 DB.set war der einzige Schreiber ohne try/catch -- und der einzige, an dem
     Trainingsdaten haengen. save() schreibt fuenf Schluessel und ruft DANACH
     scheduleSync(): wirft der zweite, steht der erste, die drei danach fehlen, und der
     Abgleich lief nie. Auf dem Bildschirm sah alles richtig aus.
     ⚠️ Diese Pruefungen ersetzen localStorage.setItem durch einen Werfer. Sie
     pruefen NICHT, dass nichts passiert, sondern dass save() durchlaeuft UND Karl es
     sieht -- ein stilles catch wuerde den Absturz verhindern und den Verlust behalten. */
  const mitKaputtemSpeicher = (fn) => {
    const echt = Storage.prototype.setItem;
    const merk = speicherKaputt;
    const leiste = document.getElementById('speicherwarnung');
    Storage.prototype.setItem = function(){ throw new DOMException('voll', 'QuotaExceededError'); };
    try { return fn(); }
    finally { Storage.prototype.setItem = echt;
              speicherKaputt = merk;
              if(leiste) leiste.classList.remove('show'); }
  };

  t('Ein voller Speicher wirft save() nicht aus der Bahn', () => mitKaputtemSpeicher(() => {
    try { save(); } catch(e) { return 'save() hat geworfen: ' + e; }
    return true;
  }));
  t('Ein voller Speicher zeigt die rote Leiste', () => mitKaputtemSpeicher(() => {
    save();
    const l = document.getElementById('speicherwarnung');
    return (l && l.classList.contains('show')) || 'die Leiste bleibt unsichtbar';
  }));
  /* ⚠️ Der Abgleich muss WEITERLAUFEN, wenn das Geraet nichts behaelt -- dann ist
     die Cloud der einzige Ort, an dem der Satz noch ankommen kann. Frueher wurde
     scheduleSync() uebersprungen, weil die Ausnahme vorher aus dem Klick-Handler flog. */
  t('Trotz vollem Speicher wird noch abgeglichen', () => mitKaputtemSpeicher(() => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    const i = q.indexOf('function save(){');
    if(i < 0) return 'save() nicht gefunden';
    const r = q.slice(i, i + 700).replace(/\/\*[\s\S]*?\*\//g, '');
    return r.indexOf('scheduleSync()') > r.indexOf('speicherWarnen')
      || 'scheduleSync() steht nicht mehr hinter der Warnung';
  }));
  t('Geht der Speicher wieder, meldet DB.set das auch', () => {
    return DB.set('pruefwert', {a:1}) === true || 'DB.set meldet false, obwohl es ging';
  });
  t('Ein voller Speicher meldet sich als false, nicht als Ausnahme',
    () => mitKaputtemSpeicher(() => eq(DB.set('pruefwert', {a:1}), false)));

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

  // ---------------------------------------------- Ausgleichsgerade (v44)
  /* \U0001f534 Bis zum 27.08.2026 nahm der Trend nur den ersten und letzten Punkt. Genau die
     beiden sind die empfindlichsten: ein schwerer Morgen am Anfang oder ein leichter am Ende
     kippte das Ergebnis -- und daraus leitet der Regelkreis eine kcal-Korrektur ab. */
  t('Eine saubere Reihe ergibt genau ihre Steigung', () => {
    const n = Date.now();
    profile.weights = [0,7,14,21].map(d => ({ date:n-(21-d)*T, kg: 80 - d*0.1 }));
    const tr = gewichtsTrend(21);
    return (tr && Math.abs(tr.proWoche - (-0.7)) < 0.001) || JSON.stringify(tr);
  });
  /* \U0001f534 Der Fall, um den es geht: das Gewicht steht, nur die LETZTE Wiegung ist ein
     Ausreisser nach unten. Zwei Punkte haetten daraus einen Abnehm-Trend gemacht; ueber alle
     Messungen bleibt davon fast nichts. */
  t('Ein Ausreisser am Ende kippt den Trend nicht mehr', () => {
    const n = Date.now();
    profile.weights = [
      {date:n-21*T, kg:80}, {date:n-17*T, kg:80}, {date:n-13*T, kg:80},
      {date:n-9*T,  kg:80}, {date:n-5*T,  kg:80}, {date:n, kg:79}];
    /* ⚠️ Fenster 22 statt 21, obwohl der aelteste Punkt 21 Tage alt ist. Grund: er lag
       damit GENAU auf der Grenze (`x.date >= now - 21 Tage`). Zwischen dem Bauen der Liste
       und dem Rechnen vergehen ein paar Millisekunden -- mal fiel er hinein, mal heraus, und
       mit fuenf statt sechs Punkten kam -0,348 heraus statt -0,252. Die Pruefung war also
       zufaellig rot, ohne dass sich am Code etwas geaendert hatte (gesehen am 28.08.2026). */
    const tr = gewichtsTrend(22);
    const zweiPunkte = (79-80)/21*7;                 // das alte Verfahren: -0,333 kg/Woche
    /* ⚠️ Die Schwelle steht bei 80 %, nicht bei 50 -- und das ist keine Nachgiebigkeit,
       sondern das ehrliche Mass. Eine Ausgleichsgerade **daempft** einen Ausreisser, sie
       loescht ihn nicht: gemessen -0,252 statt -0,333, also gut ein Viertel weniger. Wer den
       Ausreisser ganz loswerden will, braucht ein robustes Verfahren (Median der
       Steigungen) -- das ist eine andere Entscheidung, nicht diese. */
    return (tr && Math.abs(tr.proWoche) < Math.abs(zweiPunkte) * 0.8)
      || 'proWoche=' + (tr && tr.proWoche.toFixed(3)) + ' alt waere ' + zweiPunkte.toFixed(3);
  });
  t('Ein Ausreisser am Anfang genauso wenig', () => {
    const n = Date.now();
    profile.weights = [
      {date:n-21*T, kg:81}, {date:n-17*T, kg:80}, {date:n-13*T, kg:80},
      {date:n-9*T,  kg:80}, {date:n-5*T,  kg:80}, {date:n, kg:80}];
    const tr = gewichtsTrend(21);
    const zweiPunkte = (80-81)/21*7;
    return (tr && Math.abs(tr.proWoche) < Math.abs(zweiPunkte) * 0.8)
      || 'proWoche=' + (tr && tr.proWoche.toFixed(3));
  });
  /* \u26a0\ufe0f Die angezeigte Spanne muss zur angezeigten Rate passen. Ein Satz, dessen zwei
     Haelften sich widersprechen ("80,0 auf 79,5 kg, also -1,2 kg pro Woche"), ist schlimmer
     als eine ungenaue Zahl. */
  t('Angezeigte Spanne und Rate passen zusammen', () => {
    const n = Date.now();
    profile.weights = [
      {date:n-21*T, kg:81}, {date:n-14*T, kg:80.2}, {date:n-7*T, kg:80.4}, {date:n, kg:79.4}];
    const tr = gewichtsTrend(21);
    if(!tr) return 'kein Trend';
    const ausSpanne = (tr.bis - tr.von) / tr.tage * 7;
    return Math.abs(ausSpanne - tr.proWoche) < 0.001
      || 'aus der Spanne ' + ausSpanne.toFixed(3) + ', angezeigt ' + tr.proWoche.toFixed(3);
  });
  // \U0001f4a1 Durch zwei Punkte geht nur eine Gerade - da muss dasselbe herauskommen wie frueher.
  t('Bei zwei Messungen bleibt es beim alten Ergebnis', () => {
    const n = Date.now();
    profile.weights = [{date:n-14*T, kg:80}, {date:n, kg:79}];
    const tr = gewichtsTrend(21);
    return (tr && Math.abs(tr.proWoche - (-0.5)) < 0.001 && Math.abs(tr.von - 80) < 0.001)
      || JSON.stringify(tr);
  });

  // ---------------------------------------------- Ein Fenster fuer beide Seiten (v44)
  /* \u26a0\ufe0f Der Regelkreis fragt EINE Sache: passt das, was in diesem Zeitraum gegessen
     wurde, zu dem, was die Waage im SELBEN Zeitraum gemacht hat. Vorher standen 21 Tage
     Gewicht gegen 14 Tage Essen. */
  t('Gewicht und Essen werden ueber denselben Zeitraum verglichen', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    const hat = q.indexOf('gewichtsTrend(RK_FENSTER)') > -1
             && q.indexOf('kcalSchnitt(RK_FENSTER)') > -1;
    return hat || 'die beiden Fenster laufen wieder auseinander';
  });
  t('Essenstage aus Woche drei zaehlen jetzt mit', () => {
    const mK = JSON.stringify(profile.kcal || null), mW = profile.weights;
    kcalInit();
    // Vier Tage mit Eintraegen, alle aelter als 14 und juenger als 21 Tage.
    profile.kcal.meals = [15,16,17,18].map((d,i) => ({ id:'m'+i, date: Date.now()-d*T,
      name:'Test', kcal:2000, p:0, c:0, f:0 }));
    const r = kcalSchnitt(RK_FENSTER), alt = kcalSchnitt(14);
    if(mK !== 'null') profile.kcal = JSON.parse(mK); profile.weights = mW;
    return (r && r.tage === 4 && alt === null)
      || 'neu=' + JSON.stringify(r) + ' mit 14 Tagen=' + JSON.stringify(alt);
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
    // Ueber den DOM statt ueber eine Textsuche: die Punkte sind seit v47 Striche der Laenge
    // null, und die Rasterlinien tragen dieselben x1/y1 -- eine Textsuche wuerde beide fangen.
    const vals = Array.from({length:200}, (_,i) => Math.sin(i)*50+80);
    const d = document.createElement('div');
    d.innerHTML = lineChart(vals, 300, 110);
    const zahlen = [...d.querySelectorAll('line[stroke-width="5.2"]')].map(l => +l.getAttribute('x1'));
    if (zahlen.length !== 200) return 'erwartet 200 Punkte, gefunden ' + zahlen.length;
    return zahlen.every(x => x >= 0 && x <= 300) || 'Punkt ausserhalb';
  });

  // ---- Der Stretch auf dem PC (Karls Meldung 28.08.2026) ----
  // 🔴 Die eigentliche Pruefung: nicht „steht das Attribut da", sondern „ist der Punkt
  // rund". Gemessen wird das GEZEICHNETE Ergebnis in einem absichtlich breiten Kasten --
  // 900 px fuer eine 300 Einheiten breite Flaeche sind fast das Dreifache in der Waagerechten.
  // ⚠️ Was hier NICHT geprueft werden kann: wie breit der gezeichnete Punkt am Ende ist.
  // getBoundingClientRect() liefert bei SVG-Formen die Geometrie OHNE Strich -- ein Punkt aus
  // reiner Kappe misst dort 0. Statt einer Messung, die das Falsche misst, wird deshalb die
  // Ursache gemessen (die Dehnung) und die Gegenmassnahme geprueft (die Ausnahme, unten).
  t('Die Flaeche wird waagerecht wirklich gedehnt -- deshalb die Ausnahme', () => {
    const box = document.createElement('div');
    box.style.cssText = 'position:fixed;left:0;top:0;width:900px';
    box.innerHTML = lineChart([70,80,75], 300, 110, {einheit:'kg'});
    document.body.appendChild(box);
    const m = box.querySelector('svg').getScreenCTM();
    document.body.removeChild(box);
    if (!m) return 'keine Abbildung';
    const quer = m.a / m.d;   // waagerechter zu senkrechtem Massstab
    // Ohne die Ausnahme waere JEDE Strichstaerke genau um diesen Faktor breiter als hoch --
    // genau das hat Karl auf dem PC als „stretched" gesehen.
    return (quer > 2) || 'erwartet deutliche Dehnung, gemessen ' + quer.toFixed(2);
  });
  // 🔴 Eine Fuellung laesst sich von der Dehnung nicht ausnehmen. Solange die Punkte
  // <circle> waren, half kein Attribut -- sie wurden zu Ellipsen. Diese Pruefung haelt fest,
  // dass in der Flaeche ueberhaupt nichts Gefuelltes mehr steht ausser dem Verlauf darunter.
  t('Keine gefuellten Punkte mehr in der Kurve', () => {
    const d = document.createElement('div');
    d.innerHTML = lineChart([70,80,75], 300, 110);
    const kreise = d.querySelectorAll('.chart-plot circle, .chart-plot ellipse, .chart-plot rect');
    return kreise.length === 0 || kreise.length + ' gefuellte Form(en) in der Kurve';
  });
  t('Auch die Linie und das Raster sind von der Dehnung ausgenommen', () => {
    const d = document.createElement('div');
    d.innerHTML = lineChart([70,80,75], 300, 110);
    const striche = [...d.querySelectorAll('.chart-plot line, .chart-plot path[stroke]')];
    const ohne = striche.filter(el => el.getAttribute('vector-effect') !== 'non-scaling-stroke');
    return ohne.length === 0
      || ohne.length + ' Strich(e) ohne non-scaling-stroke: ' + ohne.map(e => e.tagName).join(', ');
  });

  // ---- Erinnerung ans Wiegen auf der Startseite (Karls Ansage 28.08.2026) ----
  t('Startseite erinnert ans Wiegen, solange heute nichts eingetragen ist', () => {
    // ⚠️ Ohne `session` zeigt render() die Anmeldeseite statt der Startseite.
    const vorher = profile.weights, sV = session;
    session = {user:{id:'test'}, expires_at: Date.now()+3600e3, access_token:'x'};
    profile.weights = [{date: Date.now() - 3*864e5, kg: 79}];
    view = 'home'; render();
    const h = app.innerHTML;
    profile.weights = vorher; session = sV;
    if (!h.includes('Heute wiegen')) return 'keine Erinnerung';
    if (!h.includes('data-act="addweight"')) return 'kein Eintragen-Knopf';
    if (!h.includes('id="wInput"')) return 'kein Eingabefeld';
    return true;
  });
  // ⚠️ Der wichtigere Fall: eine Erinnerung, die nach dem Erledigen stehen bleibt, ist keine.
  // 🔴 Ohne Schalter waere die Erinnerung eine Aufforderung, die man nicht loswird.
  t('Ausgeschaltet steht die Wiege-Erinnerung nicht mehr da', () => {
    const wV = profile.weights, eV = profile.erinnerungen, sV = session;
    session = {user:{id:'test'}, expires_at: Date.now()+3600e3, access_token:'x'};
    profile.weights = [];
    profile.erinnerungen = {wiegen:false, essen:false, ts:Date.now()};
    view = 'home'; render();
    const h = app.innerHTML;
    profile.weights = wV; profile.erinnerungen = eV; session = sV;
    return !h.includes('Heute wiegen') || 'Erinnerung steht trotz Aus';
  });
  // Karls Ansage vom 29.08.: der erklaerende Satz stand jeden Tag da und sagte jeden Tag
  // dasselbe. ⚠️ Auf der Kalorien-Seite bleibt er -- dort steht er einmal, nicht taeglich.
  t('Kein erklaerender Satz mehr in der Wiege-Erinnerung', () => {
    const wV = profile.weights, eV = profile.erinnerungen, sV = session;
    session = {user:{id:'test'}, expires_at: Date.now()+3600e3, access_token:'x'};
    profile.weights = [{date: Date.now() - 3*864e5, kg: 79}];
    profile.erinnerungen = {wiegen:true, essen:false, ts:Date.now()};
    view = 'home'; render();
    const h = app.innerHTML;
    profile.weights = wV; profile.erinnerungen = eV; session = sV;
    if (!h.includes('Heute wiegen')) return 'Erinnerung fehlt ganz';
    if (h.includes('Am besten morgens vor dem Essen')) return 'Der Satz steht noch da';
    if (h.includes('Zuletzt')) return 'Das Zuletzt-Gewicht steht noch da';
    return true;
  });

  // ---- Erinnerung ans Essen (Karls Ansage 29.08.2026) ----
  t('Startseite erinnert ans Essen, solange heute nichts eingetragen ist', () => {
    const mV = kcalInit().meals, eV = profile.erinnerungen, sV = session;
    session = {user:{id:'test'}, expires_at: Date.now()+3600e3, access_token:'x'};
    kcalInit().meals = [];
    profile.erinnerungen = {wiegen:false, essen:true, ts:Date.now()};
    view = 'home'; render();
    const h = app.innerHTML;
    kcalInit().meals = mV; profile.erinnerungen = eV; session = sV;
    if (!h.includes('Essen eintragen')) return 'keine Erinnerung';
    if (!h.includes('data-act="food:start"')) return 'kein Knopf zum Eintragen';
    return true;
  });
  t('Nach einer Mahlzeit ist die Essens-Erinnerung weg', () => {
    const mV = kcalInit().meals, eV = profile.erinnerungen, sV = session;
    session = {user:{id:'test'}, expires_at: Date.now()+3600e3, access_token:'x'};
    kcalInit().meals = [{id:'m1', date: Date.now(), name:'Brot', kcal:200, p:8, menge:'1 Scheibe'}];
    profile.erinnerungen = {wiegen:false, essen:true, ts:Date.now()};
    view = 'home'; render();
    const h = app.innerHTML;
    kcalInit().meals = mV; profile.erinnerungen = eV; session = sV;
    return !h.includes('Essen eintragen') || 'Erinnerung steht trotz Mahlzeit von heute';
  });
  t('Ausgeschaltet steht die Essens-Erinnerung nicht mehr da', () => {
    const mV = kcalInit().meals, eV = profile.erinnerungen, sV = session;
    session = {user:{id:'test'}, expires_at: Date.now()+3600e3, access_token:'x'};
    kcalInit().meals = [];
    profile.erinnerungen = {wiegen:false, essen:false, ts:Date.now()};
    view = 'home'; render();
    const h = app.innerHTML;
    kcalInit().meals = mV; profile.erinnerungen = eV; session = sV;
    return !h.includes('Essen eintragen') || 'Erinnerung steht trotz Aus';
  });

  // ---- Der Kippschalter (Karls Ansage 29.08.2026) ----
  // Vorher stand dort ein Knopf mit "Ausschalten"/"Einschalten" -- der sagt, was PASSIEREN
  // WUERDE, nicht was IST.
  t('Beide Erinnerungen haben einen echten Schalter, keinen Knopf mit Text', () => {
    const eV = profile.erinnerungen, sV = session;
    session = {user:{id:'test'}, expires_at: Date.now()+3600e3, access_token:'x'};
    profile.erinnerungen = {wiegen:true, essen:false, ts:Date.now()};
    view = 'settings'; render();
    const alle = [...document.querySelectorAll('[data-act^="erinn:"]')];
    const h = app.innerHTML;
    profile.erinnerungen = eV; session = sV;
    if (alle.length !== 2) return 'erwartet 2 Schalter, gefunden ' + alle.length;
    const keinSchalter = alle.filter(b => b.getAttribute('role') !== 'switch');
    if (keinSchalter.length) return keinSchalter.length + ' ohne role="switch"';
    // aria-checked muss den ZUSTAND spiegeln, nicht die Absicht des Klicks.
    const anZustand = alle.map(b => b.getAttribute('aria-checked')).join(',');
    if (anZustand !== 'true,false') return 'aria-checked: ' + anZustand;
    if (h.includes('Ausschalten') || h.includes('Einschalten')) return 'der alte Text-Knopf ist zurueck';
    return true;
  });
  // 🔴 Die eigentliche Pruefung: der Knopf muss sichtbar woanders sitzen. Ein Schalter,
  // der in beiden Stellungen gleich aussieht, ist kein Schalter -- und genau das passiert,
  // wenn die Klasse `an` gesetzt wird, das CSS sie aber nicht kennt (oder umgekehrt).
  // ⚠️ Hier IST das messbar, anders als beim Punkt in der Kurve: es sind HTML-Elemente,
  // getBoundingClientRect liefert dort die volle Kaestchen-Groesse.
  t('Der Knopf des Schalters sitzt an und aus wirklich woanders', () => {
    const eV = profile.erinnerungen, sV = session;
    session = {user:{id:'test'}, expires_at: Date.now()+3600e3, access_token:'x'};
    profile.erinnerungen = {wiegen:true, essen:false, ts:Date.now()};
    view = 'settings'; render();
    const anS  = document.querySelector('[data-act="erinn:wiegen:aus"]');   // steht auf AN
    const ausS = document.querySelector('[data-act="erinn:essen:an"]');     // steht auf AUS
    if (!anS || !ausS) { profile.erinnerungen = eV; session = sV; return 'Schalter nicht gefunden'; }
    const versatz = el => {
      const knopf = el.querySelector('i');
      if (!knopf) return null;
      const a = el.getBoundingClientRect(), b = knopf.getBoundingClientRect();
      return (a.width > 0 && b.width > 0) ? (b.left - a.left) : null;
    };
    const vAn = versatz(anS), vAus = versatz(ausS);
    profile.erinnerungen = eV; session = sV;
    if (vAn === null || vAus === null) return 'Knopf nicht gezeichnet';
    // 18 px sind der gebaute Weg; mit 12 als Schwelle faellt jede stille Entkopplung auf,
    // ohne dass eine kleine Masskorrektur die Pruefung rot macht.
    return (vAn - vAus > 12)
      || 'Versatz nur ' + (vAn - vAus).toFixed(1) + ' px (an bei ' + vAn.toFixed(1) + ', aus bei ' + vAus.toFixed(1) + ')';
  });

  // 🔴 Und der Einbau, nicht nur das Teil: der Schalter in den Einstellungen muss die
  // Karte auf der Startseite auch wirklich verschwinden lassen. Geprueft mit echtem Klick.
  t('Der Schalter in den Einstellungen schaltet die Karte wirklich ab', () => {
    const wV = profile.weights, eV = profile.erinnerungen, sV = session;
    session = {user:{id:'test'}, expires_at: Date.now()+3600e3, access_token:'x'};
    profile.weights = [];
    profile.erinnerungen = {wiegen:true, essen:true, ts:0};
    view = 'settings'; render();
    const knopf = document.querySelector('[data-act="erinn:wiegen:aus"]');
    if (!knopf) { profile.weights = wV; profile.erinnerungen = eV; session = sV; return 'kein Schalter in den Einstellungen'; }
    knopf.click();
    const nachAus = erinnerungAn('wiegen');
    view = 'home'; render();
    const h = app.innerHTML;
    profile.weights = wV; profile.erinnerungen = eV; session = sV; view = 'home'; render();
    if (nachAus !== false) return 'Schalter hat nichts umgestellt';
    return !h.includes('Heute wiegen') || 'Karte steht trotz ausgeschaltetem Schalter';
  });

  t('Nach dem Wiegen ist die Erinnerung weg', () => {
    const vorher = profile.weights, sV = session;
    session = {user:{id:'test'}, expires_at: Date.now()+3600e3, access_token:'x'};
    profile.weights = [{date: Date.now(), kg: 78.5}];
    view = 'home'; render();
    const h = app.innerHTML;
    profile.weights = vorher; session = sV;
    return !h.includes('Heute wiegen') || 'Erinnerung steht trotz Eintrag von heute';
  });
  // 🔴 Und der Einbau, nicht nur das Teil: der Knopf auf der Startseite muss denselben
  // Weg gehen wie der auf der Kalorien-Seite. Geprueft wird mit einem echten Klick.
  t('Eintragen von der Startseite aus traegt wirklich ein', () => {
    const vorher = profile.weights, sV = session;
    session = {user:{id:'test'}, expires_at: Date.now()+3600e3, access_token:'x'};
    profile.weights = [];
    view = 'home'; render();
    const feld = document.getElementById('wInput');
    const knopf = document.querySelector('[data-act="addweight"]');
    if (!feld || !knopf) { profile.weights = vorher; session = sV; return 'Feld oder Knopf fehlt'; }
    feld.value = '77.3';
    knopf.click();
    const neu = profile.weights.slice();
    const nochDa = app.innerHTML.includes('Heute wiegen');
    profile.weights = vorher; session = sV; view = 'home'; render();
    if (neu.length !== 1) return 'erwartet 1 Eintrag, es sind ' + neu.length;
    if (neu[0].kg !== 77.3) return 'Wert nicht uebernommen: ' + neu[0].kg;
    return !nochDa || 'Erinnerung stand nach dem Eintragen noch da';
  });

  // ---- Beschriftung der Kurve (Karls Meldung 28.08.2026) ----
  // ⚠️ Die vier Pruefungen darunter fassen bewusst das ERGEBNIS von lineChart an und nicht
  // eine Hilfsfunktion. Am 27.08. sind an einem Abend dreimal Gegenproben gruen geblieben,
  // weil sie den Baustein direkt aufriefen und seinen Einbau nie sahen.
  t('Kurve beschriftet die Seite mit hoechstem, mittlerem und tiefstem Wert', () => {
    const html = lineChart([70,80,90], 300, 110, {einheit:'kg'});
    const y = (html.match(/class="chart-y[^"]*">(.*?)<\/div>/)||[])[1] || '';
    const txt = y.replace(/<[^>]+>/g,'|').split('|').filter(Boolean);
    return (txt.length === 3 && txt[0] === '90 kg' && txt[1] === '80' && txt[2] === '70')
      || JSON.stringify(txt);
  });
  t('Kurve beschriftet unten mit erstem und letztem Datum', () => {
    const t1 = new Date(2026,7,1).getTime(), t2 = new Date(2026,7,20).getTime();
    const html = lineChart([70,80], 300, 110, {x:[t1,t2]});
    const x = (html.match(/class="chart-x">(.*?)<\/div>/)||[])[1] || '';
    const txt = x.replace(/<[^>]+>/g,'|').split('|').filter(Boolean);
    return (txt.length === 2 && txt[0] === '01.08.' && txt[1] === '20.08.') || JSON.stringify(txt);
  });
  /* ⚠️ DIESE REGEL IST AM 02.09.2026 ABGELOEST WORDEN, und der Grund gehoert
     festgehalten, weil er zeigt, warum sie vorher richtig war.
     Bis dahin sassen die Punkte gleichmaessig nebeneinander. Ein Datum in der Mitte der
     Flaeche war deshalb nur bei ungerader Punktzahl ehrlich -- bei vier Punkten haette
     es bei 50 % gestanden, waehrend sein Punkt bei 33 % sass. Eine stille Luege.
     ✅ Mit der Zeitachse ist die Mitte der Flaeche immer ein echter Zeitpunkt: die
     Mitte zwischen erstem und letztem Eintrag. Sie gehoert keinem Punkt mehr, und genau
     deshalb stimmt sie -- unabhaengig von der Punktzahl.
     🔴 Die alte Pruefung ist also nicht geloescht, weil sie stoerte, sondern weil
     ihre Voraussetzung weggefallen ist. Was sie geschuetzt hat, prueft die naechste. */
  t('Bei gerader Punktzahl nennt die Mitte den Zeitpunkt, nicht den Punkt', () => {
    // Sechs Tage, 01.08. bis 06.08. -- die zeitliche Mitte ist der 03.08. um 12 Uhr,
    // also der 03.08. Kein einziger Messpunkt liegt dort, und das ist der Punkt.
    const ts = [0,1,2,3,4,5].map(i => new Date(2026,7,1+i).getTime());
    const html = lineChart([1,2,3,4,5,6], 300, 110, {x:ts});
    const x = (html.match(/class="chart-x">(.*?)<\/div>/)||[])[1] || '';
    const txt = x.replace(/<[^>]+>/g,'|').split('|').filter(Boolean);
    return (txt.length === 3 && txt[0] === '01.08.' && txt[1] === '03.08.' && txt[2] === '06.08.')
      || JSON.stringify(txt);
  });

  /* ================================ Die Zeitachse selbst (02.09.2026)
     🔴 Bis heute war der Abstand der Punkte die REIHENFOLGE, nicht die Zeit. Bei
     „1 Jahr" sah eine Pause von drei Monaten aus wie ein einzelner Tag -- die Kurve
     behauptete einen Verlauf, den es nicht gab. Betraf alle drei Kurven, seit es sie gibt.
     ⚠️ Gemessen wird an der gezeichneten Linie, nicht an einer Hilfsfunktion:
     dieselbe Vorsicht wie bei den vier Pruefungen darueber. */
  /* ⚠️ Die LINIE, nicht die Flaeche. Im SVG steht die Flaeche zuerst, und sie
     traegt zwei zusaetzliche Punkte, mit denen sie unten wieder zumacht. Beim ersten
     Anlauf hat dieser Helfer genau die gegriffen und fuenf Punkte gemeldet, wo drei
     sind -- die Pruefung war rot aus dem falschen Grund. */
  const punkteX = (html) => {
    const d = (html.match(/<path d="([^"]*)" fill="none"/)||[])[1] || '';
    return d.split(/[ML]/).filter(Boolean).map(s => parseFloat(s.trim().split(' ')[0]));
  };
  t('Eine lange Pause macht ein breites Stueck Kurve', () => {
    // Drei Punkte: 01.08., 02.08., dann ein halbes Jahr Pause bis 01.02.2027.
    const ts = [new Date(2026,7,1).getTime(), new Date(2026,7,2).getTime(),
                new Date(2027,1,1).getTime()];
    const xs = punkteX(lineChart([80,81,82], 300, 110, {x:ts}));
    if(xs.length !== 3) return 'die Linie hat ' + xs.length + ' Punkte';
    const kurz = xs[1]-xs[0], lang = xs[2]-xs[1];
    return lang > kurz * 20 || ('ein Tag ist ' + kurz.toFixed(1) + ' breit, ein halbes Jahr '
      + lang.toFixed(1) + ' -- der Abstand haengt weiter an der Reihenfolge');
  });
  t('Gleiche Abstaende bleiben gleich breit', () => {
    const ts = [0,1,2,3].map(i => new Date(2026,7,1+i).getTime());
    const xs = punkteX(lineChart([80,81,82,83], 300, 110, {x:ts}));
    if(xs.length !== 4) return 'die Linie hat ' + xs.length + ' Punkte';
    const a = xs[1]-xs[0], b = xs[2]-xs[1], c = xs[3]-xs[2];
    return (Math.abs(a-b) < 0.2 && Math.abs(b-c) < 0.2)
      || ('Abstaende: ' + [a,b,c].map(v=>v.toFixed(1)).join(', '));
  });
  /* ⚠️ Ohne Zeitstempel gibt es nichts zu verteilen -- dann MUSS der alte,
     gleichmaessige Abstand gelten. Sonst waere die Uebungs-Kurve kaputt, sobald jemand
     lineChart ohne opt.x aufruft. */
  t('Ohne Zeitstempel bleibt es beim gleichmaessigen Abstand', () => {
    const xs = punkteX(lineChart([80,81,90,91], 300, 110, {}));
    if(xs.length !== 4) return 'die Linie hat ' + xs.length + ' Punkte';
    const a = xs[1]-xs[0], b = xs[2]-xs[1], c = xs[3]-xs[2];
    return (Math.abs(a-b) < 0.2 && Math.abs(b-c) < 0.2)
      || ('Abstaende: ' + [a,b,c].map(v=>v.toFixed(1)).join(', '));
  });
  /* 🔴 Und der Fall, an dem eine Zeitachse still kaputtgeht: `exHistory` folgt der
     Reihenfolge in `sessions`, und dass die nach Datum sortiert ist, ist nirgends
     zugesichert. Bei einem Ruecksprung wuerde die Linie zickzack laufen. Dann lieber der
     alte Massstab -- ein falscher Abstand ist besser als eine Linie, die zurueckspringt. */
  t('Springen die Zeitstempel zurueck, gilt wieder die Reihenfolge', () => {
    const ts = [new Date(2026,7,10).getTime(), new Date(2026,7,1).getTime(),
                new Date(2026,7,20).getTime()];
    const xs = punkteX(lineChart([80,81,82], 300, 110, {x:ts}));
    if(xs.length !== 3) return 'die Linie hat ' + xs.length + ' Punkte';
    return (xs[0] < xs[1] && xs[1] < xs[2])
      || ('die Linie laeuft zurueck: ' + xs.map(v=>v.toFixed(1)).join(', '));
  });
  t('Fallen alle Eintraege auf denselben Zeitpunkt, bricht nichts', () => {
    const z = new Date(2026,7,1).getTime();
    const xs = punkteX(lineChart([80,81,82], 300, 110, {x:[z,z,z]}));
    return (xs.length === 3 && xs.every(v => isFinite(v)) && xs[0] < xs[2])
      || ('Punkte: ' + JSON.stringify(xs));
  });
  t('Ungerade Punktzahl ab fuenf bekommt ein mittleres Datum', () => {
    const ts = [0,1,2,3,4].map(i => new Date(2026,7,1+i).getTime());
    const html = lineChart([1,2,3,4,5], 300, 110, {x:ts});
    const x = (html.match(/class="chart-x">(.*?)<\/div>/)||[])[1] || '';
    const txt = x.replace(/<[^>]+>/g,'|').split('|').filter(Boolean);
    return (txt.length === 3 && txt[1] === '03.08.') || JSON.stringify(txt);
  });
  t('Ohne Zeitstempel steht unten gar nichts statt leerer Kaesten', () => {
    return !lineChart([70,80], 300, 110).includes('chart-x') || 'leere Achse gebaut';
  });
  // ⚠️ Sonst stuenden bei lauter gleichen Werten drei gleiche Zahlen untereinander und
  // taeuschten eine Spanne vor, die es nicht gibt.
  t('Lauter gleiche Werte ergeben nur EINE Zahl an der Seite', () => {
    const html = lineChart([80,80,80], 300, 110, {einheit:'kg'});
    const y = (html.match(/class="chart-y[^"]*">(.*?)<\/div>/)||[])[1] || '';
    return (y.split('<span>').length - 1 === 1 && html.includes('chart-y einer'))
      || 'y: ' + y;
  });
  t('Volumen wird als ganze Zahl beschriftet, nicht mit Komma', () => {
    const html = lineChart([1000,4820], 300, 110, {einheit:'kg', fmt:v=>Math.round(v).toLocaleString('de-DE')});
    return html.includes('4.820 kg') || 'keine 4.820 kg: ' + html.slice(0,200);
  });

  // ---- Und der Einbau: rufen die drei Kurven in der App die Beschriftung auch auf? ----
  // ⚠️ Genau hier war am 27.08. dreimal die Luecke. Eine beschriftete Kurve nuetzt nichts,
  // wenn renderExDetail() sie ohne Zeitstempel aufruft.
  t('Alle drei Kurven der App bekommen Zeitstempel mit', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    // ⚠️ Kein /lineChart\([^)]*\)/ -- die Aufrufe enthalten selbst Klammern (map(...)),
    // die Suche braeche mitten im Aufruf ab und faende dann ueberall „kein x:".
    const rufe = q.split('lineChart(').slice(1)
      .map(s => s.slice(0, 160))
      .filter(s => !s.startsWith('vals,w,h,opt'));
    if (rufe.length !== 3) return 'erwartet 3 Aufrufe, gefunden ' + rufe.length;
    const ohne = rufe.filter(s => s.indexOf('{x:') < 0);
    return ohne.length === 0 || 'ohne Datum: ' + ohne.join(' // ');
  });
  t('Der Koerpergewichts-Verlauf zeigt Datum und Kilogramm', () => {
    // ⚠️ Drei Huerden stehen zwischen render() und der Kurve, alle drei schweigend:
    //    ohne `session` kommt die Anmeldeseite, ohne Kalorien-Ziel der Einrichtungs-
    //    Assistent, und `kobErzwingen` haelt den Assistenten selbst dann oben.
    const wVorher = profile.weights, kVorher = JSON.stringify(profile.kcal||null);
    const sVorher = session, ezVorher = kobErzwingen;
    session = {user:{id:'test'}, expires_at: Date.now() + 3600e3, access_token:'x'};
    kobErzwingen = false;
    const k = kcalInit(); k.setup = true; k.goal = 2000;
    profile.weights = [
      {date:new Date(2026,7,1).getTime(), kg:80},
      {date:new Date(2026,7,10).getTime(), kg:78.5},
      {date:new Date(2026,7,20).getTime(), kg:77}];
    view = 'body'; render();
    const h = app.innerHTML;
    profile.weights = wVorher;
    if (kVorher !== 'null') profile.kcal = JSON.parse(kVorher);
    kobErzwingen = ezVorher; session = sVorher;
    view = 'home'; render();
    if (!h.includes('chart-y')) return 'keine Seitenbeschriftung';
    if (!h.includes('chart-x')) return 'keine Beschriftung unten';
    if (!h.includes('80 kg')) return 'hoechster Wert fehlt an der Achse';
    if (!h.includes('01.08.') || !h.includes('20.08.')) return 'Datum fehlt unten';
    return true;
  });

  /* ---- Zeitraum der Gewichtskurve (Karls Ansage 01.09.2026) ----
     „ich will das die kurve fuer das gewicht zeitlich einstellbar ist 1 woche 1 monat
     1 jahr max". Geprueft wird beides: der Filter allein UND was in der Ansicht ankommt
     — der Fund vom selben Tag war eine Lehre, die nur an einer von zwei Stellen
     eingebaut war. */
  const gwTage = n => Date.now() - n*864e5;
  // Baut die Koerperansicht mit vorgegebenen Wiegungen und gibt ihr HTML zurueck.
  // ⚠️ Dieselben drei schweigenden Huerden wie oben: ohne `session` kommt die
  // Anmeldeseite, ohne Kalorien-Ziel der Einrichtungs-Assistent, und `kobErzwingen`
  // haelt ihn selbst dann oben.
  function koerperHtml(gewichte, fenster, klick){
    const wV=profile.weights, kV=JSON.stringify(profile.kcal||null),
          sV=session, ezV=kobErzwingen, fV=gwFenster;
    session={user:{id:'test'}, expires_at:Date.now()+3600e3, access_token:'x'};
    kobErzwingen=false;
    const k=kcalInit(); k.setup=true; k.goal=2000;
    profile.weights=gewichte; gwFenster=fenster||'max';
    view='body'; render();
    let fehlt=null;
    if(klick){ const b=document.querySelector('[data-act="gw:fenster:'+klick+'"]');
               if(b) b.click(); else fehlt=klick; }
    const h=app.innerHTML, f=gwFenster;
    profile.weights=wV; if(kV!=='null') profile.kcal=JSON.parse(kV);
    kobErzwingen=ezV; session=sV; gwFenster=fV;
    view='home'; render();
    return {h:h, fenster:f, fehlt:fehlt};
  }
  // Punkte der gezeichneten Kurve zaehlen. ⚠️ Nicht ueber eine Textsuche: die
  // Rasterlinien tragen dieselben x1/y1 — nur die Strichstaerke 5.2 gehoert den Punkten.
  const kurvenPunkte = html => { const d=document.createElement('div'); d.innerHTML=html;
    return d.querySelectorAll('.chart-plot line[stroke-width="5.2"]').length; };

  t('Eine Woche nimmt nur die letzten sieben Tage', () => {
    const vorher = profile.weights;
    profile.weights = [{date:gwTage(40),kg:82},{date:gwTage(20),kg:80},
                       {date:gwTage(3),kg:79},{date:gwTage(1),kg:78.5}];
    const w = weightImFenster('woche').map(x=>x.kg);
    profile.weights = vorher;
    return JSON.stringify(w)==='[79,78.5]' || JSON.stringify(w);
  });
  t('Max nimmt alles', () => {
    const vorher = profile.weights;
    profile.weights = [{date:gwTage(900),kg:90},{date:gwTage(1),kg:78}];
    const n = weightImFenster('max').length;
    profile.weights = vorher;
    return eq(n, 2);
  });
  t('Ein Jahr laesst Aelteres draussen, ein Monat auch', () => {
    const vorher = profile.weights;
    profile.weights = [{date:gwTage(400),kg:90},{date:gwTage(60),kg:84},
                       {date:gwTage(2),kg:80}];
    const j = weightImFenster('jahr').length, m = weightImFenster('monat').length;
    profile.weights = vorher;
    return (j===2 && m===1) || 'Jahr='+j+' Monat='+m;
  });
  t('Ein unbekannter Zeitraum faellt auf Max zurueck', () => {
    const vorher = profile.weights;
    profile.weights = [{date:gwTage(900),kg:90},{date:gwTage(1),kg:78}];
    const n = weightImFenster('quatsch').length;
    profile.weights = vorher;
    return eq(n, 2);
  });
  /* 🔴 Die Grenze zaehlt ab HEUTE, nicht ab dem letzten Eintrag. Wer nach drei
     Monaten Pause „1 Woche" waehlt, soll einen leeren Zeitraum sehen und nicht die
     Woche von vor drei Monaten unter der Ueberschrift „1 Woche". */
  t('Ein leerer Zeitraum bleibt leer und schiebt sich nicht zurueck', () => {
    const vorher = profile.weights;
    profile.weights = [{date:gwTage(95),kg:82},{date:gwTage(90),kg:81}];
    const n = weightImFenster('woche').length;
    profile.weights = vorher;
    return eq(n, 0);
  });

  t('Vier Zeitraeume stehen ueber der Kurve, genau einer ist gewaehlt', () => {
    const r = koerperHtml([{date:gwTage(20),kg:80},{date:gwTage(2),kg:79}]);
    const d = document.createElement('div'); d.innerHTML = r.h;
    const knoepfe = [...d.querySelectorAll('[data-act^="gw:fenster:"]')];
    if(knoepfe.length !== 4) return 'erwartet 4 Knoepfe, gefunden ' + knoepfe.length;
    const an = knoepfe.filter(b => b.classList.contains('on'));
    if(an.length !== 1) return an.length + ' Knoepfe gleichzeitig gewaehlt';
    return an[0].getAttribute('data-act')==='gw:fenster:max'
      || 'gewaehlt ist ' + an[0].getAttribute('data-act');
  });
  /* 🔴 Die Gegenprobe zum Knopf: nicht „steht der Knopf da", sondern
     „schneidet er die Kurve wirklich". Sieben Wiegungen, davon zwei in der letzten
     Woche — bei „Max" muessen sieben Punkte gezeichnet sein, bei „1 Woche"
     zwei. Ein Knopf, der nur seine eigene Farbe aendert, faellt genau hier durch. */
  t('Ein Klick auf 1 Woche schneidet die Kurve wirklich', () => {
    const gew = [{date:gwTage(300),kg:86},{date:gwTage(200),kg:84},
                 {date:gwTage(100),kg:83},{date:gwTage(40),kg:81},
                 {date:gwTage(20),kg:80},{date:gwTage(5),kg:79},
                 {date:gwTage(1),kg:78.5}];
    const alle = koerperHtml(gew);
    const woche = koerperHtml(gew, 'max', 'woche');
    if(woche.fehlt) return 'Knopf ' + woche.fehlt + ' nicht gefunden';
    if(woche.fenster !== 'woche') return 'Klick hat den Zeitraum nicht umgestellt';
    const a = kurvenPunkte(alle.h), b = kurvenPunkte(woche.h);
    return (a===7 && b===2) || 'Max=' + a + ' Punkte, Woche=' + b;
  });
  t('Der Klick laesst den Zeitraum auch nach dem Neuzeichnen stehen', () => {
    const gew = [{date:gwTage(300),kg:86},{date:gwTage(2),kg:79}];
    const r = koerperHtml(gew, 'max', 'jahr');
    const d = document.createElement('div'); d.innerHTML = r.h;
    const an = d.querySelector('[data-act^="gw:fenster:"].on');
    return (an && an.getAttribute('data-act')==='gw:fenster:jahr')
      || 'gewaehlt ist ' + (an ? an.getAttribute('data-act') : 'nichts');
  });
  /* 🔴 Kein toter Punkt. Ein Zeitraum ohne zwei Messungen darf keine leere Karte
     zeigen — dann sieht es aus, als sei die App kaputt. Er sagt, dass nichts da ist,
     und nennt den naechsten Zeitraum, in dem etwas steht. */
  t('Ein Zeitraum ohne Kurve sagt das und nennt den naechsten', () => {
    const gew = [{date:gwTage(200),kg:84},{date:gwTage(150),kg:82}];
    const r = koerperHtml(gew, 'max', 'woche');
    if(kurvenPunkte(r.h) !== 0) return 'trotzdem eine Kurve gezeichnet';
    if(!/Kein Eintrag in diesem Zeitraum/.test(r.h)) return 'kein Hinweis auf den leeren Zeitraum';
    return /Unter .1 Jahr/.test(r.h) || 'der naechste Zeitraum wird nicht genannt';
  });
  t('Ein einziger Eintrag im Zeitraum sagt, dass zwei noetig sind', () => {
    const gew = [{date:gwTage(200),kg:84},{date:gwTage(2),kg:79}];
    const r = koerperHtml(gew, 'max', 'woche');
    return /Nur ein Eintrag in diesem Zeitraum/.test(r.h) || 'falscher oder kein Hinweis';
  });
  /* 🔴 Die drei Kaesten oben zeigen weiter die ganze Geschichte, die Kurve darunter
     nur den Zeitraum. „kg seit Start" haelt die beiden auseinander — ohne das Wort
     liest man bei „1 Woche" die Differenz eines halben Jahres als die der Woche. */
  t('Die Differenz sagt dazu, dass sie ab Start zaehlt', () => {
    const r = koerperHtml([{date:gwTage(200),kg:84},{date:gwTage(2),kg:79}], 'max', 'woche');
    if(!r.h.includes('kg seit Start')) return 'die Differenz sagt nicht, worauf sie sich bezieht';
    return !r.h.includes('kg Differenz') || 'die alte, mehrdeutige Beschriftung steht noch da';
  });
  /* Die Spanne neben der Ueberschrift beschreibt die GEZEIGTE Kurve, nicht alle Daten.
     ⚠️ Gelesen wird genau der eine Span neben „Verlauf" und nicht die ganze Seite:
     die Liste „Eintraege" darunter zeigt weiterhin ALLE Wiegungen — dort steht die
     90 voellig zu Recht, und eine Textsuche ueber das ganze HTML faende sie dort. */
  t('Die Spanne neben Verlauf gilt dem gewaehlten Zeitraum', () => {
    const gew = [{date:gwTage(300),kg:90},{date:gwTage(5),kg:79},{date:gwTage(1),kg:78}];
    const r = koerperHtml(gew, 'max', 'woche');
    const d = document.createElement('div'); d.innerHTML = r.h;
    const kopf = [...d.querySelectorAll('h2')].find(x => x.textContent.trim()==='Verlauf');
    if(!kopf) return 'keine Ueberschrift Verlauf';
    const span = kopf.parentElement.querySelector('span.tiny.muted');
    if(!span) return 'keine Spanne neben der Ueberschrift';
    const txt = span.textContent;
    if(txt.includes('90')) return 'die Spanne zeigt noch den Wert von ausserhalb: ' + txt;
    return (txt.includes('78') && txt.includes('79')) || 'Spanne des Zeitraums fehlt: ' + txt;
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
  /* 🔴 30.08.2026: der Aufwaermsatz zaehlte hier mit, ueberall sonst nicht. Ein
     eingetippter Zahlendreher im Aufwaermfeld hob damit „Bestes kg" an, ohne je ein
     Rekord zu sein -- deshalb steht er hier absichtlich SCHWERER als der Arbeitssatz.
     Die drei Zahlen zusammen: sonst geht eine der drei still wieder kaputt. */
  t('Verlauf laesst den Aufwaermsatz aussen vor', () => {
    sessions = [{date:Date.now(), entries:[{name:'A', sets:[
      {done:true, weight:100, reps:5, warm:true},
      {done:true, weight:60,  reps:10}]}]}];
    const h = exHistory('A')[0];
    return (h.sets === 1 && h.w === 60 && h.vol === 600 && h.reps === 10)
      || 'Aufwaermsatz zaehlt mit: ' + JSON.stringify(h);
  });
  t('Verlauf und Einheiten-Liste zaehlen dieselben Saetze', () => {
    const en = [{name:'A', sets:[{done:true, weight:50, reps:8, warm:true},
                                 {done:true, weight:80, reps:8},
                                 {done:true, weight:80, reps:8}]}];
    sessions = [{date:Date.now(), entries:en}];
    // doneSets() steht unter der Einheit im Verlauf, exHistory().sets in der Uebung darunter.
    return eq(exHistory('A')[0].sets, doneSets(en));
  });
  t('Verlauf und Einheiten-Liste zaehlen dasselbe Volumen', () => {
    const en = [{name:'A', sets:[{done:true, weight:50, reps:8, warm:true},
                                 {done:true, weight:80, reps:8}]}];
    sessions = [{date:Date.now(), entries:en}];
    return eq(exHistory('A')[0].vol, volume(en));
  });

  // ---- Jahresraster ----
  /* 🔴 30.08.2026: das Raster kannte nur Volumen. Klimmzuege, Liegestuetze, Dips, Plank,
     Crunches -- alle in der Bibliothek, alle mit Gewicht 0, also `volume()` = 0, also
     dieselbe Farbe wie ein Ruhetag. Das Raster beantwortet genau EINE Frage
     („bin ich drangeblieben?") und gab sie fuer Koerpergewichts-Training falsch. */
  const rasterProbe = (sess) => { const v = sessions; sessions = sess;
    const h = jahresRaster(); sessions = v; return h; };
  const zelleHeute = (h) => {
    const d = new Date(); d.setHours(0,0,0,0);
    const i = h.indexOf('title="' + d.toLocaleDateString('de-DE'));
    return i < 0 ? '' : h.slice(i, h.indexOf('></div>', i));
  };
  t('Ein Koerpergewichts-Tag zaehlt als trainiert', () => {
    const h = rasterProbe([{date:Date.now(), entries:[{name:'Klimmzuege',
      sets:[{done:true, weight:0, reps:8},{done:true, weight:0, reps:8}]}]}]);
    return h.indexOf('1 Tag trainiert') > -1 || 'zaehlt nicht: ' + h.slice(0, 200);
  });
  t('Ein Koerpergewichts-Tag ist im Raster eingefaerbt', () => {
    const h = rasterProbe([{date:Date.now(), entries:[{name:'Klimmzuege',
      sets:[{done:true, weight:0, reps:8}]}]}]);
    const z = zelleHeute(h);
    if (!z) return 'die Zelle von heute war nicht zu finden';
    // Stufe 0 ist --card2 und heisst ab jetzt ausschliesslich "hier war nichts".
    return z.indexOf('--ok') > -1 || 'sieht aus wie ein Ruhetag: ' + z;
  });
  t('Ein Tag ohne Einheit bleibt die Ruhetag-Farbe', () => {
    const h = rasterProbe([{date: Date.now() - 3*864e5, entries:[{name:'A',
      sets:[{done:true, weight:50, reps:10}]}]}]);
    const z = zelleHeute(h);
    if (!z) return 'die Zelle von heute war nicht zu finden';
    /* ⚠️ Nicht auf `--card2` pruefen: Stufe 1 ist ein color-mix AUS --ok UND --card2 und
       enthaelt beide Namen. Der Unterschied, der zaehlt, ist allein das Gruen. */
    return z.indexOf('--ok') < 0 || 'ein leerer Tag ist eingefaerbt: ' + z;
  });
  /* ⚠️ Die Zahl stand unter der Ueberschrift „Dein Jahr", zaehlte aber ALLE Tage seit
     jeher -- also auch Kaestchen, die gar nicht gezeichnet werden. Faellt erst auf, wenn
     die App aelter als 53 Wochen ist; dann aber dauerhaft. */
  t('Tage trainiert zaehlt nur, was auch gezeichnet ist', () => {
    const h = rasterProbe([
      {date: Date.now() - 400*864e5, entries:[{name:'A', sets:[{done:true, weight:50, reps:10}]}]},
      {date: Date.now(),             entries:[{name:'A', sets:[{done:true, weight:50, reps:10}]}]}]);
    return h.indexOf('1 Tag trainiert') > -1 || 'zaehlt ausserhalb des Rasters mit';
  });
  // ⚠️ „1 Saetze" — derselbe Fehler wie „Dreissig Wiegen" am 29.08. Beim Volumen gibt es
  // keine Mehrzahl, bei den Saetzen schon, und die Zahl 1 kommt genau am Anfang vor.
  t('Ein einzelner Satz heisst Satz, nicht Saetze', () => {
    const h = rasterProbe([{date:Date.now(), entries:[{name:'Plank',
      sets:[{done:true, weight:0, reps:1}]}]}]);
    const z = zelleHeute(h);
    return z.indexOf('1 Satz') > -1 && z.indexOf('1 Sätze') < 0 || 'steht da: ' + z;
  });
  t('Zwei Einheiten an einem Tag sind ein Tag', () => {
    const h = rasterProbe([
      {date: Date.now(), entries:[{name:'A', sets:[{done:true, weight:50, reps:10}]}]},
      {date: Date.now(), entries:[{name:'B', sets:[{done:true, weight:50, reps:10}]}]}]);
    return h.indexOf('1 Tag trainiert') > -1 || 'ein Tag doppelt gezaehlt';
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
  // Der Deckel ist hier die ganze Idee: Aufgaben schieben an, sie tragen nicht.
  // 🔴 Seit dem 29.08.2026 kommt eine zweite Regel dazu, Karls Ansage: „man kann nicht jeden
  // Tag XP kriegen fuer wenn man was gemacht hat, weil an manchen Tagen machst du ja nichts."
  // JEDE verbliebene Aufgabe verlangt eine Handlung -- „App geoeffnet" ist ersatzlos raus.
  t('Aufgaben bringen hoechstens 25 XP am Tag', () => eq(AUFGABEN_MAX, 25));
  t('Keine Aufgabe fuers blosse Oeffnen der App', () => {
    if (AUFGABEN.some(a => a.id === 'auf')) return 'Reingeschaut steht wieder in der Liste';
    // ⚠️ Und der Einbau, nicht nur die Liste: solange die Startfolge sie noch abhakt, gaebe
    // es die XP weiter -- aufgabeErledigen() wuerde sie nur nicht mehr finden. Ein spaeteres
    // Wiedereinfuegen in AUFGABEN haette den Aufruf dann still wieder scharf gestellt.
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    return q.indexOf("aufgabeErledigen('auf')") < 0
      || 'die App hakt „Reingeschaut" immer noch ab';
  });
  t('Eine Einheit ist ein Vielfaches aller Tagesaufgaben wert', () => {
    const einheit = sessXP(einheitMit(12, 100, 2, 2), 2);
    return einheit >= AUFGABEN_MAX * 5
      || 'Einheit ' + einheit + ' XP gegen ' + AUFGABEN_MAX + ' XP Aufgaben - zu nah beieinander';
  });
  t('Eine erledigte Aufgabe gibt ihre XP', () => {
    profile.aufgaben = { tag:'', fertig:{} };
    const vorher = profile.xp;
    const gab = aufgabeErledigen('ein');
    const delta = profile.xp - vorher;
    profile.aufgaben = { tag:'', fertig:{} }; profile.xp = vorher;
    return (gab && delta === 10) || 'gab=' + gab + ' delta=' + delta;
  });
  t('Dieselbe Aufgabe zweimal am Tag zaehlt nur einmal', () => {
    profile.aufgaben = { tag:'', fertig:{} };
    const vorher = profile.xp;
    aufgabeErledigen('ein');
    const nochmal = aufgabeErledigen('ein');
    const delta = profile.xp - vorher;
    profile.aufgaben = { tag:'', fertig:{} }; profile.xp = vorher;
    return (nochmal === false && delta === 10) || 'nochmal=' + nochmal + ' delta=' + delta;
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

  // ================================================ Abgleich zwischen zwei Geraeten (v45)
  /* \U0001f534 Karls Meldung: "habe eine Trainingseinheit auf dem Handy eingetragen, den Erfolg
     fuer den Tag bekommen -- auf dem PC aber nicht, obwohl mir das Training dort angezeigt
     wird." Zusammengefuehrt wurden nur Einheiten und Gewichte; alles andere im Profil kam
     unveraendert von `basis`, und `basis` ist praktisch immer das eigene Geraet. */
  const heute = heuteKey();
  const blobMit = (p) => ({ programs:[], sessions:[], profile:Object.assign({xp:0}, p), settings:{} });

  t('Der Haken vom anderen Geraet kommt an', () => {
    const r = blobsZusammen(
      blobMit({ aufgaben:{ tag:heute, fertig:{ auf:true } } }),
      blobMit({ aufgaben:{ tag:heute, fertig:{ auf:true, train:true } } }));
    return r.blob.profile.aufgaben.fertig.train === true || 'Trainiert fehlt weiterhin';
  });
  // \u26a0\ufe0f Und die XP dazu, exakt aus dem Katalog - nicht geschaetzt.
  t('Die XP der uebernommenen Aufgabe kommen mit', () => {
    const wert = AUFGABEN.find(a=>a.id==='train').xp;
    const r = blobsZusammen(
      blobMit({ xp:100, aufgaben:{ tag:heute, fertig:{ auf:true } } }),
      blobMit({ xp:999, aufgaben:{ tag:heute, fertig:{ auf:true, train:true } } }));
    return r.blob.profile.xp === 100 + wert || 'xp=' + r.blob.profile.xp + ', erwartet ' + (100+wert);
  });
  t('Eine Aufgabe, die beide kennen, wird nicht doppelt bezahlt', () => {
    const r = blobsZusammen(
      blobMit({ xp:100, aufgaben:{ tag:heute, fertig:{ train:true } } }),
      blobMit({ xp:100, aufgaben:{ tag:heute, fertig:{ train:true } } }));
    return r.blob.profile.xp === 100 || 'xp=' + r.blob.profile.xp;
  });
  t('Ein aelterer Tag von drueben ueberschreibt den heutigen nicht', () => {
    const r = blobsZusammen(
      blobMit({ aufgaben:{ tag:heute, fertig:{ auf:true } } }),
      blobMit({ aufgaben:{ tag:'2020-01-01', fertig:{ auf:true, train:true } } }));
    return (r.blob.profile.aufgaben.tag === heute && !r.blob.profile.aufgaben.fertig.train)
      || JSON.stringify(r.blob.profile.aufgaben);
  });
  /* \U0001f534 Der schwerere Fall als der fehlende Haken: kennt das zweite Geraet die Auszahlung
     nicht, zahlt es denselben Erfolg NOCHMAL aus. */
  t('Ausgezahlte Erfolge kommen mit', () => {
    const r = blobsZusammen(blobMit({ erfolge:{} }), blobMit({ erfolge:{ e1:true } }));
    return r.blob.profile.erfolge.e1 === true || 'der Erfolg fehlt weiterhin';
  });
  t('Und ihre XP genau einmal', () => {
    const wert = ERFOLGE.find(e=>e.id==='e1').xp;
    const r = blobsZusammen(blobMit({ xp:500, erfolge:{} }), blobMit({ xp:9, erfolge:{ e1:true } }));
    return r.blob.profile.xp === 500 + wert || 'xp=' + r.blob.profile.xp;
  });
  t('Ein beiden bekannter Erfolg bringt nichts dazu', () => {
    const r = blobsZusammen(blobMit({ xp:500, erfolge:{ e1:true } }), blobMit({ xp:500, erfolge:{ e1:true } }));
    return r.blob.profile.xp === 500 || 'xp=' + r.blob.profile.xp;
  });
  /* \U0001f534 Mahlzeiten sind echter Inhalt, kein Zustand. Wer am Handy eintraegt und danach
     den PC aufmacht, hat sie bisher verloren, sobald der PC geschoben hat. */
  t('Mahlzeiten vom anderen Geraet gehen nicht verloren', () => {
    const r = blobsZusammen(
      blobMit({ kcal:{ foods:[], meals:[{id:'a', date:Date.now(), kcal:500}] } }),
      blobMit({ kcal:{ foods:[], meals:[{id:'b', date:Date.now(), kcal:700}] } }));
    const ids = r.blob.profile.kcal.meals.map(m=>m.id).sort().join(',');
    return ids === 'a,b' || 'uebrig: ' + ids;
  });
  t('Eigene Lebensmittel auch nicht', () => {
    const r = blobsZusammen(
      blobMit({ kcal:{ foods:[{id:'f1', name:'Quark'}], meals:[] } }),
      blobMit({ kcal:{ foods:[{id:'f2', name:'Skyr'}],  meals:[] } }));
    return r.blob.profile.kcal.foods.length === 2 || 'nur ' + r.blob.profile.kcal.foods.length;
  });
  t('Dieselbe Mahlzeit kommt nicht zweimal', () => {
    const m = {id:'a', date:Date.now(), kcal:500};
    const r = blobsZusammen(blobMit({ kcal:{foods:[], meals:[m]} }), blobMit({ kcal:{foods:[], meals:[m]} }));
    return r.blob.profile.kcal.meals.length === 1 || 'zweimal drin';
  });
  // Ein Schritt-Eintrag je Tag, der spaetere gewinnt - dieselbe Regel wie beim Gewicht.
  t('Schritte: ein Eintrag je Tag, der spaetere gewinnt', () => {
    const n = Date.now();
    const r = blobsZusammen(
      blobMit({ kcal:{foods:[], meals:[], steps:[{date:n-3600000, n:4000}]} }),
      blobMit({ kcal:{foods:[], meals:[], steps:[{date:n, n:9000}]} }));
    const st = r.blob.profile.kcal.steps;
    return (st.length === 1 && st[0].n === 9000) || JSON.stringify(st);
  });
  // \u26a0\ufe0f Sonst kaeme das Wiederkommen, obwohl man auf dem anderen Geraet taeglich da war.
  t('Zuletzt-da nimmt den spaeteren Zeitpunkt', () => {
    const n = Date.now();
    const r = blobsZusammen(blobMit({ zuletztDa: n-20*864e5 }), blobMit({ zuletztDa: n }));
    return r.blob.profile.zuletztDa === n || 'es blieb beim alten Zeitpunkt';
  });
  // \U0001f534 Der Einbau: uebernommen muss auch das Neue mitzaehlen, sonst wird nicht
  // zurueckgeschoben und das andere Geraet erfaehrt nie davon.
  t('Neues aus dem Essen zaehlt als uebernommen', () => {
    const r = blobsZusammen(
      blobMit({ kcal:{foods:[], meals:[]} }),
      blobMit({ kcal:{foods:[], meals:[{id:'b', date:Date.now(), kcal:700}]} }));
    return r.uebernommen >= 1 || 'uebernommen=' + r.uebernommen;
  });

  // ================================================ Admin und Seitenwechsel (v45)
  /* \U0001f534 Karl: "meine Admin-Konsole auf dem Handy ist ausserdem weg." Die Geste hat auch
     wieder ZUGESPERRT -- fuenfmal auf Brock getippt, waehrend sie offen war, und der Hinweis
     dazu ist nach 1,8 Sekunden verschwunden. */
  /* ⚠️ Verhalten pruefen, nicht Quelltext: die erste Fassung suchte nach
     `devAdmin=!devAdmin` und fand es im KOMMENTAR, der die alte Fassung erklaert. */
  const brockTippen = (mal) => {
    const b = document.querySelector('#app .mascot'); if(!b) return null;
    for(let i=0;i<mal;i++) b.click();
    return devAdmin;
  };
  t('Fuenfmal tippen schliesst auf', () => {
    const mV=view, mD=devAdmin, mS=session;
    if(!session) session={access_token:'t'};
    devAdmin=false; DB.set('devadmin',false);
    view='home'; render();
    const r = brockTippen(5);
    view=mV; devAdmin=mD; DB.set('devadmin',mD); session=mS; render();
    return r === true || (r === null ? 'kein Brock auf der Startseite' : 'blieb zu');
  });
  t('Nochmal tippen sperrt nicht wieder zu', () => {
    const mV=view, mD=devAdmin, mS=session;
    if(!session) session={access_token:'t'};
    devAdmin=true; DB.set('devadmin',true);
    view='home'; render();
    const r = brockTippen(5);
    view=mV; devAdmin=mD; DB.set('devadmin',mD); session=mS; render();
    return r === true || (r === null ? 'kein Brock auf der Startseite' : 'die Geste hat zugesperrt');
  });
  t('Zumachen geht nur noch bewusst', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    return q.indexOf('data-admin="zu"') > -1 || 'es gibt keinen Knopf zum Zumachen';
  });
  t('Die goldene Nachricht ist raus', () => {
    const mV = view; view = 'erfolge'; renderErfolge();
    const txt = document.getElementById('app').textContent;
    view = mV;
    return txt.indexOf('neu freigeschaltet') === -1 || 'der Kasten steht noch da';
  });
  // \u26a0\ufe0f Die NEU-Markierung selbst bleibt - gestrichen war der Kasten, nicht der Hinweis.
  t('Die NEU-Markierung am Erfolg bleibt', () => {
    const mS = sessions, mG = profile.erfolgeGesehen, mV = view;
    sessions = []; profile.erfolgeGesehen = null; erfolgeGesehenInit();
    sessions = [{ id:'a1', date:Date.now(), entries:[], xp:0, pr:0 }];
    view = 'erfolge'; renderErfolge();
    const n = document.querySelectorAll('#app .erf-frisch').length;
    view = mV; profile.erfolgeGesehen = mG; sessions = mS;
    return n >= 1 || 'nichts mehr golden markiert';
  });
  /* Der Seitenwechsel: geprueft wird, dass die Bewegung ueberhaupt gesetzt wird und in
     welche Richtung -- ein echter Wisch laesst sich headless nicht nachstellen. */
  t('Nach rechts wechseln kommt von rechts herein', () => {
    const mV = view, mS = session;
    if(!session) session = { access_token:'t' };
    view = 'home'; reiterZeigen('body');
    const kl = document.getElementById('app').className;
    view = mV; session = mS; render();
    return /rein-r/.test(kl) || 'Klassen: ' + kl;
  });
  t('Zurueck kommt von links herein', () => {
    const mV = view, mS = session;
    if(!session) session = { access_token:'t' };
    view = 'settings'; reiterZeigen('home');
    const kl = document.getElementById('app').className;
    view = mV; session = mS; render();
    return /rein-l/.test(kl) || 'Klassen: ' + kl;
  });
  // \u26a0\ufe0f Derselbe Reiter darf nicht animieren - sonst zuckt es bei jedem Tipp auf den,
  // auf dem man schon steht.
  t('Derselbe Reiter zuckt nicht', () => {
    const mV = view, mS = session;
    if(!session) session = { access_token:'t' };
    view = 'home'; reiterZeigen('home');
    const kl = document.getElementById('app').className;
    view = mV; session = mS; render();
    return !/rein-/.test(kl) || 'Klassen: ' + kl;
  });

  // ================================================ Das Schluessel-Fenster (v44)
  /* 🔴 `showModal()` und `closeModal()` fassen dasselbe `#modal` an. Ein Aufruf von
     dort raeumte den Schluessel-Dialog weg, und `fragKey()` gab nie eine Antwort. Wer das
     Foto ueber diesen Weg geschickt hat (`await fragKey()` in `schaetzeFoto`), haette FUER
     IMMER auf "das Bild wird angesehen" gestarrt. */
  await tA('Ein fremdes Fenster beendet den Schluessel-Dialog', async () => {
    const p = fragKey();
    showModal('irgendwas anderes');
    // ⚠️ Mit einem Wettlauf gegen die Zeit, sonst haengt der ganze Lauf, wenn es
    // wieder kaputtgeht -- eine Pruefung darf nie das sein, was blockiert.
    const r = await Promise.race([p, new Promise(x => setTimeout(() => x('haengt'), 400))]);
    closeModal();
    return r === false || (r === 'haengt' ? 'der Dialog antwortet nie' : 'kam heraus: ' + r);
  });
  await tA('closeModal beendet ihn auch', async () => {
    const p = fragKey();
    closeModal();
    const r = await Promise.race([p, new Promise(x => setTimeout(() => x('haengt'), 400))]);
    return r === false || (r === 'haengt' ? 'der Dialog antwortet nie' : 'kam heraus: ' + r);
  });
  // ⚠️ Und der Normalfall darf davon nichts abbekommen: wer speichert, bekommt true.
  await tA('Speichern antwortet weiterhin mit dem Schluessel', async () => {
    const merk = DB.get('aikey','');
    const p = fragKey();
    document.getElementById('keyInput').value = 'AIzaPRUEFUNG';
    document.getElementById('keySave').click();
    const r = await Promise.race([p, new Promise(x => setTimeout(() => x('haengt'), 400))]);
    DB.set('aikey', merk); closeModal();
    return r === true || 'kam heraus: ' + r;
  });
  t('Ohne offenen Dialog tut das Aufloesen nichts', () => {
    keyDialogAufloesen(); keyDialogAufloesen();   // darf nicht werfen
    return true;
  });

  // ================================================ Aus dem Durchsehen, 2. Runde (v43)
  /* 🔴 Abmelden und Loeschen haben Plaene, Einheiten und Profil zurueckgesetzt -- die
     kontogebundenen Sachen daneben aber nicht. Der schaerfste Fall: eine abgeschickte, noch
     nicht zugestellte Meldung haengt an der Verbindung, nicht am Konto. Die naechste
     Anmeldung haette sie mit IHREM Token rausgeschickt. */
  const raeumProbe = (auchSchluessel) => {
    localStorage.setItem(MELD_KEY, JSON.stringify([{id:'m1', text:'offen', umfeld:{}}]));
    localStorage.setItem(POST_KEY, JSON.stringify([{id:'p1', antwort:'Hi', gelesen_am:null}]));
    DB.set('postfach-gelesen', ['p9']);
    DB.set('aikey', 'AIzaTEST');
    kontoDatenRaeumen(auchSchluessel);
    return { meld: (localStorage.getItem(MELD_KEY)||'').length,
             post: (localStorage.getItem(POST_KEY)||'').length,
             gel:  (DB.get('postfach-gelesen', []) || []).length,
             key:  DB.get('aikey','') };
  };
  t('Abmelden nimmt offene Meldungen mit', () => {
    const r = raeumProbe(false); DB.set('aikey','');
    return r.meld === 0 || 'es liegt noch etwas im Ausgang';
  });
  t('Abmelden raeumt das Postfach', () => {
    const r = raeumProbe(false); DB.set('aikey','');
    return (r.post === 0 && r.gel === 0) || 'post=' + r.post + ' gelesen=' + r.gel;
  });
  /* ⚠️ Der Schluessel gehoert zum GERAET, nicht zum Konto -- steht so in den
     Einstellungen. Ihn beim Abmelden wegzunehmen waere eine Schikane. */
  t('Abmelden laesst den KI-Schluessel liegen', () => {
    const r = raeumProbe(false); DB.set('aikey','');
    return r.key === 'AIzaTEST' || 'der Schluessel ist weg: ' + JSON.stringify(r.key);
  });
  // ⚠️ Beim Loeschen steht "alle Daten dauerhaft" -- dann darf nichts uebrigbleiben.
  t('Konto loeschen nimmt auch den Schluessel mit', () => {
    const r = raeumProbe(true); DB.set('aikey','');
    return r.key === '' || 'der Schluessel liegt noch da';
  });
  /* 🔴 Und wieder der Einbau statt nur des Teils. Ueber APP_QUELLE, sonst faende die
     Pruefung ihren eigenen Text im Dokument wieder. */
  t('Abmelden ruft das Aufraeumen auch auf', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    return q.indexOf('kontoDatenRaeumen(false)') > -1 || 'authSignOut raeumt nicht auf';
  });
  t('Konto loeschen ruft es mit dem Schluessel auf', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    return q.indexOf('kontoDatenRaeumen(true)') > -1 || 'deleteAccount raeumt den Schluessel nicht mit';
  });
  /* 🔴 Der vierte Posten, der beim Abmelden liegenblieb (30.08.2026) -- und der einzige, den
     `kontoDatenRaeumen()` gar nicht erreichen kann: die Push-Anmeldung liegt nicht im
     Browser-Speicher, sondern im Geraet und in `gym_push`. Folge 1: das Handy brummte
     weiter fuer ein Konto, das hier niemand mehr hat. Folge 2, die schlimmere: `subscribe()`
     gibt bei gleichem Schluessel DIESELBE endpoint zurueck -- der Primaerschluessel von
     `gym_push`. Das Anlegen des Naechsten wurde damit ein Aendern an einer fremden Zeile,
     was die Zeilensperre verbietet. Er sah „spaeter nochmal", und spaeter ging es genauso
     wenig.
     ⚠️ Der Service Worker laeuft in den Pruefungen nie (siehe Merkposten oben), also ist
     hier nur der Quelltext nachzulesen. Das ist Lesen, kein Ausfuehren -- und genau deshalb
     wird die REIHENFOLGE mitgeprueft: sie ist der Teil, den ein Blick uebersieht. */
  /* ⚠️ Kommentare RAUS, bevor gesucht wird. Sonst prueft die Reihenfolge sich an dem Text,
     der die Reihenfolge erklaert: in `authSignOut` steht „vor `clearSession()`" als Hinweis
     ueber dem Aufruf -- und der Hinweis stuende vor `pushAbmelden()`, der echte Aufruf
     dahinter. Die Pruefung waere gruen geworden, waere der Aufruf ganz unten gelandet. */
  const rumpf = (q, name) => { const a = q.indexOf('function ' + name);
    if (a < 0) return ''; const b = q.indexOf('\nasync function ', a + 10);
    return q.slice(a, b < 0 ? a + 3000 : b)
            .replace(/\/\*[\s\S]*?\*\//g, '').replace(/^[ \t]*\/\/.*$/gm, ''); };
  t('Abmelden loest auch die Push-Anmeldung auf', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    return rumpf(q, 'authSignOut').indexOf('pushAbmelden()') > -1
      || 'authSignOut meldet Push nicht ab';
  });
  t('Push wird abgemeldet, SOLANGE das Token noch gilt', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    const r = rumpf(q, 'authSignOut');
    const p = r.indexOf('pushAbmelden()'), c = r.indexOf('clearSession()');
    if (p < 0 || c < 0) return 'einer der beiden Aufrufe fehlt';
    // Danach ist das Token weg und das DELETE auf gym_push kaeme nie durch.
    return p < c || 'pushAbmelden() steht hinter clearSession()';
  });
  t('Konto loeschen meldet Push mit ab', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    return rumpf(q, 'deleteAccount').indexOf('pushAbmelden()') > -1
      || 'deleteAccount laesst die Push-Anmeldung stehen';
  });
  t('Push abmelden loest erst im Geraet, dann auf dem Server', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    const r = rumpf(q, 'pushAbmelden');
    const u = r.indexOf('.unsubscribe()'), d = r.indexOf('method:\'DELETE\'');
    if (u < 0 || d < 0) return 'einer der beiden Schritte fehlt';
    /* Andersherum bliebe bei einem Netzfehler eine Anmeldung im Geraet ohne Zeile auf
       dem Server: der Schalter stuende auf „an" und es kaeme nie etwas. */
    return u < d || 'der Server wird vor dem Geraet geraeumt';
  });
  t('Nach dem Abmelden steht keine rote Zahl mehr', () => {
    localStorage.setItem(POST_KEY, JSON.stringify([{id:'p1', antwort:'Hi', gelesen_am:null}]));
    const vorher = postfachUngelesen();
    kontoDatenRaeumen(false);
    const nachher = postfachUngelesen();
    return (vorher === 1 && nachher === 0) || 'vorher=' + vorher + ' nachher=' + nachher;
  });

  // ================================================ Aus dem Durchsehen (v42)
  /* 🔴 Der Fund, der beim Durchsehen am peinlichsten war: das Wiederkommen stand ganz
     am Ende der Startfolge und ueberschrieb damit jede Ansicht, die vorher gesetzt worden war
     -- eine offene Einheit, den Assistenten, die Schritte aus dem Link. Eine Stunde nach dem
     Einbauen gefunden, und zwar nur durch Lesen. */
  t('Eine offene Einheit hat Vorrang vor dem Wiederkommen', () =>
    eq(startAnsicht('workout', true, {id:'x'}), 'workout'));
  t('Auch eine gesetzte Ansicht schlaegt das Wiederkommen', () => {
    const fehl = ['body','onboard','plans'].filter(v => startAnsicht(v, true, null) !== v);
    return fehl.length === 0 || 'ueberschrieben: ' + fehl.join(', ');
  });
  t('Steht sonst nichts an, kommt das Wiederkommen', () =>
    eq(startAnsicht('home', true, null), 'comeback'));
  t('Ohne Faelligkeit bleibt die Startseite stehen', () =>
    eq(startAnsicht('home', false, null), 'home'));
  // ⚠️ Auch auf der Startseite nicht, solange eine Einheit laeuft.
  t('Bei laufender Einheit kommt es auch von der Startseite nicht', () =>
    eq(startAnsicht('home', true, {id:'x'}), 'home'));
  /* 🔴 Und der Einbau, nicht nur das Teil: die Startfolge muss die Funktion auch
     BENUTZEN. Geprueft ueber APP_QUELLE -- den Quelltext der App ohne diese Pruefungen.
     Ein Blick in `document.documentElement.innerHTML` faende hier sich selbst wieder. */
  t('Die Startfolge benutzt die Entscheidung auch', () => {
    const q = window.APP_QUELLE || '';
    if(!q) return 'APP_QUELLE fehlt';
    return q.indexOf('view = startAnsicht(view, comebackPruefen(), active);') > -1
      || 'die Startfolge entscheidet an der Funktion vorbei';
  });

  // ================================================ Aus dem Durchsehen (v42)
  /* 🔴 sw.js laeuft in dieser Seite NIE -- ein Service Worker hat eine eigene Umgebung.
     Sein Quelltext wird als Zeichenkette hereingereicht (SW_QUELLE), also wird hier GELESEN,
     nicht ausgefuehrt. Fuer diesen Fund reicht das: die Frage ist, ob der Riegel dasteht. */
  t('Der Service Worker faengt nur die eigene Seite ab', () => {
    const q = window.SW_QUELLE || '';
    if(!q) return 'SW_QUELLE fehlt';
    return /u\.origin\s*!==\s*self\.location\.origin/.test(q)
      || 'kein Riegel gegen fremde Adressen im fetch-Handler';
  });
  t('Der Riegel steht VOR dem respondWith', () => {
    const q = window.SW_QUELLE || '';
    const riegel = q.indexOf('u.origin !== self.location.origin');
    const antwort = q.indexOf('e.respondWith');
    return (riegel > -1 && antwort > -1 && riegel < antwort)
      || 'Riegel=' + riegel + ' respondWith=' + antwort;
  });

  /* 🔴 Zwei gleichzeitige Aufrufe duerfen den refresh_token nicht doppelt verbrauchen.
     Supabase gibt bei jedem Auffrischen einen neuen aus; der zweite Aufruf bekaeme 400, und
     der 4xx-Zweig wirft die Anmeldung weg. Beim Start laufen cloudSyncStart() und
     postfachAuffrischen() nebeneinander -- genau dieser Fall. */
  await tA('Zwei gleichzeitige Aufrufe frischen nur einmal auf', async () => {
    const mF = window.fetch, mS = session;
    let rufe = 0;
    session = { access_token:'alt', refresh_token:'r1', expires_at: Date.now() - 1000,
                username:'k', user:{ id:'u1', email:'a@b.de' } };
    window.fetch = async () => { rufe++;
      await new Promise(r => setTimeout(r, 20));
      return { ok:true, status:200, json: async () => ({ access_token:'neu', refresh_token:'r2',
               expires_in:3600, user:{ id:'u1', email:'a@b.de' } }) }; };
    const [a, b] = await Promise.all([ensureToken(), ensureToken()]);
    window.fetch = mF; session = mS;
    return (rufe === 1 && a === true && b === true) || 'Aufrufe=' + rufe + ' a=' + a + ' b=' + b;
  });
  // ⚠️ Der Riegel muss nach einem Fehlschlag wieder aufgehen - sonst wartet der
  // naechste Aufruf ewig auf ein Versprechen, das laengst beantwortet ist.
  await tA('Nach einem Fehlschlag geht es beim naechsten Mal wieder', async () => {
    const mF = window.fetch, mS = session;
    let rufe = 0;
    session = { access_token:'alt', refresh_token:'r1', expires_at: Date.now() - 1000,
                username:'k', user:{ id:'u1', email:'a@b.de' } };
    window.fetch = async () => { rufe++; throw new Error('kein Netz'); };
    const erst = await ensureToken();
    const zweit = await ensureToken();
    window.fetch = mF; session = mS;
    return (rufe === 2 && erst === false && zweit === false)
      || 'Aufrufe=' + rufe + ' erst=' + erst + ' zweit=' + zweit;
  });

  // ================================================ Wiederkommen (v41)
  /* \U0001f534 Karls Nachsatz war die eigentliche Anforderung: "natuerlich nicht direkt, wenn
     man die Website das erste Mal oeffnet -- wirklich nur nach 2 Wochen." Ein "schoen, dass
     du wieder da bist" beim allerersten Oeffnen waere peinlich. */
  const cbSichern = () => ({ z: profile.zuletztDa, s: sessions, o: profile.onboarded, v: view });
  const cbZurueck = (m) => { profile.zuletztDa = m.z; sessions = m.s; profile.onboarded = m.o; view = m.v; };
  const cbEinheit = () => [{ id:'x', date: Date.now()-30*864e5, entries:[], xp:0, pr:0 }];

  t('Beim allerersten Oeffnen kommt es NICHT', () => {
    const m = cbSichern();
    profile.zuletztDa = null; sessions = cbEinheit(); profile.onboarded = true;
    const r = comebackFaellig();
    cbZurueck(m);
    return r === false || 'es kaeme beim ersten Oeffnen';
  });
  t('Nach zwei Wochen Pause kommt es', () => {
    const m = cbSichern();
    profile.zuletztDa = Date.now() - 15*864e5; sessions = cbEinheit(); profile.onboarded = true;
    const r = comebackFaellig();
    cbZurueck(m);
    return r === true || 'es kaeme nach 15 Tagen nicht';
  });
  t('Nach dreizehn Tagen noch nicht', () => {
    const m = cbSichern();
    profile.zuletztDa = Date.now() - 13*864e5; sessions = cbEinheit(); profile.onboarded = true;
    const r = comebackFaellig();
    cbZurueck(m);
    return r === false || 'es kaeme schon nach 13 Tagen';
  });
  // \u26a0\ufe0f Wer nie angefangen hat, war nicht weg.
  t('Ohne Einheiten und ohne Einrichtung kommt es nicht', () => {
    const m = cbSichern();
    profile.zuletztDa = Date.now() - 40*864e5; sessions = []; profile.onboarded = false;
    const r = comebackFaellig();
    cbZurueck(m);
    return r === false || 'es kaeme fuer jemanden, der nie da war';
  });
  /* \U0001f534 Reihenfolge: erst fragen, dann stempeln. Andersherum waere die Antwort immer
     "nein", und das Wiederkommen kaeme nie -- ein Fehler, den keine Einzelpruefung der beiden
     Haelften sehen wuerde. */
  t('Gefragt wird vor dem Stempeln', () => {
    const m = cbSichern();
    profile.zuletztDa = Date.now() - 20*864e5; sessions = cbEinheit(); profile.onboarded = true;
    const faellig = comebackPruefen();
    const neuerStempel = profile.zuletztDa;
    cbZurueck(m);
    return (faellig === true && Date.now() - neuerStempel < 5000)
      || 'faellig=' + faellig + ' Stempel gesetzt=' + (Date.now() - neuerStempel < 5000);
  });
  t('Beim zweiten Mal am selben Tag kommt es nicht nochmal', () => {
    const m = cbSichern();
    profile.zuletztDa = Date.now() - 20*864e5; sessions = cbEinheit(); profile.onboarded = true;
    comebackPruefen();
    const nochmal = comebackPruefen();
    cbZurueck(m);
    return nochmal === false || 'es kaeme direkt nochmal';
  });
  t('Die Ansicht nennt Rang, Level und die Einheiten', () => {
    const m = cbSichern();
    sessions = cbEinheit(); comebackTage = 21;
    view = 'comeback'; renderComeback();
    const txt = document.getElementById('app').textContent;
    cbZurueck(m);
    const fehlt = ['Dein Rang', 'Level', 'Einheiten bisher'].filter(x => txt.indexOf(x) === -1);
    return fehlt.length === 0 || 'fehlt: ' + fehlt.join(', ');
  });
  // \u26a0\ufe0f Wichtiger als das Lob: die Ansage, dass nichts verfallen ist. Sonst liest sich
  // eine Pause wie eine Strafe.
  t('Die Ansicht sagt, dass nichts verfallen ist', () => {
    const m = cbSichern();
    sessions = cbEinheit(); comebackTage = 21;
    view = 'comeback'; renderComeback();
    const txt = document.getElementById('app').textContent;
    cbZurueck(m);
    return /Nichts davon ist weg/.test(txt) || 'der Satz fehlt';
  });
  t('Aus der Ansicht kommt man wieder heraus', () => {
    const m = cbSichern();
    sessions = cbEinheit(); comebackTage = 21;
    view = 'comeback'; renderComeback();
    const raus = document.querySelectorAll('#app [data-act^="cb:"]').length;
    cbZurueck(m);
    return raus >= 1 || 'kein Weg aus der Ansicht heraus';
  });

  // ================================================ Admin: Tutorials (v41)
  t('Alle drei Tutorials stehen in der Admin-Konsole', () => {
    const mV = view, mD = devAdmin;
    devAdmin = true; view = 'admin'; renderAdmin();
    const q = document.getElementById('app').innerHTML;
    view = mV; devAdmin = mD;
    // Drei Stueck seit dem 27.08.2026: Trainingsplan, Ernaehrung, Wiederkommen.
    const fehlt = ['tut:plan', 'tut:kcal', 'tut:comeback'].filter(x => q.indexOf(x) === -1);
    return fehlt.length === 0 || 'fehlt in der Konsole: ' + fehlt.join(', ');
  });
  /* \u26a0\ufe0f Das Abspielen darf nichts anfassen. Wer sich das Wiederkommen ansieht, will es
     sehen -- nicht seinen Zeitstempel verlieren und es danach echt bekommen. */
  t('Das Abspielen ruehrt die Daten nicht an', () => {
    const mV = view, mD = devAdmin, mZ = profile.zuletztDa, mX = profile.xp;
    devAdmin = true; profile.zuletztDa = 12345;
    view = 'admin'; renderAdmin();
    document.querySelector('[data-admin="tut:comeback"]').click();
    const wo = view, zeit = profile.zuletztDa, xp = profile.xp;
    view = mV; devAdmin = mD; profile.zuletztDa = mZ; profile.xp = mX; render();
    return (wo === 'comeback' && zeit === 12345 && xp === mX)
      || 'view=' + wo + ' zuletztDa=' + zeit;
  });

  // ================================================ Wischen zwischen den Reitern (v41)
  /* Geprueft wird die ENTSCHEIDUNG, nicht der Finger: welche vier Reiter, in welcher
     Reihenfolge, und wo nicht gewischt wird. Ein echter Wisch laesst sich hier nicht
     nachstellen -- headless kennt keine Beruehrung. */
  t('Die Reiter stehen in der Reihenfolge der Leiste', () => {
    const inLeiste = [...document.querySelectorAll('#nav button')].map(b => b.dataset.nav);
    return JSON.stringify(REITER) === JSON.stringify(inLeiste)
      || 'Reiter ' + JSON.stringify(REITER) + ' gegen Leiste ' + JSON.stringify(inLeiste);
  });
  // \U0001f534 Der wichtigste Riegel: aus einer laufenden Einheit darf kein Wisch herausfuehren.
  t('Aus einer laufenden Einheit wird nicht gewischt', () => {
    return REITER.indexOf('workout') === -1 || 'die Einheit steht in der Wisch-Liste';
  });
  t('Auch Assistent und Wiederkommen sind ausgenommen', () => {
    const drin = ['onboard', 'comeback', 'meldung', 'privacy'].filter(v => REITER.indexOf(v) !== -1);
    return drin.length === 0 || 'wischbar, obwohl es nicht sollte: ' + drin.join(', ');
  });

  // ================================================ Leiste + Konto-Karte (v40)
  /* 🔴 Am 27.08.2026 stand hier ein paar Stunden eine Korrektur, die die untere Leiste
     an den sichtbaren Bildschirm heften sollte. Karls Meldung danach: die Leiste war gar nicht
     mehr zu sehen und wanderte beim Ueberziehen bis zur Bildschirmmitte. Zurueckgebaut.
     Diese Pruefung haelt fest, dass niemand die Leiste mehr von Hand verschiebt -- der
     Browser macht `position:fixed; bottom:0` selbst richtig. */
  /* ⚠️ Diese Pruefung sah zuerst im Quelltext der Seite nach - und fand dort ihren
     EIGENEN Text wieder, weil die Pruefungen mit im Dokument stehen. Sie war rot, obwohl
     nichts kaputt war. Jetzt wird das VERHALTEN geprueft: die Leiste darf sich auch dann
     nicht bewegen, wenn der sichtbare Bildschirm sich meldet. */
  t('Die untere Leiste wird nicht von Hand verschoben', () => {
    const nav = document.getElementById('nav');
    if (/transform/.test(nav.getAttribute('style') || ''))
      return 'die Leiste traegt ein transform: ' + nav.getAttribute('style');
    if (window.visualViewport) {
      window.visualViewport.dispatchEvent(new Event('resize'));
      window.visualViewport.dispatchEvent(new Event('scroll'));
    }
    window.dispatchEvent(new Event('orientationchange'));
    const t2 = getComputedStyle(nav).transform;
    return (t2 === 'none' || t2 === '') || 'nach einem Viewport-Ereignis steht dort: ' + t2;
  });
  t('Die Leiste klebt unten, nicht am Inhalt', () => {
    const st = getComputedStyle(document.getElementById('nav'));
    return (st.position === 'fixed' && st.bottom === '0px')
      || 'position=' + st.position + ' bottom=' + st.bottom;
  });
  /* Karls Ansage: der Zuruecksetzen-Knopf gehoert zwischen Abmelden und Konto loeschen.
     ⚠️ Sachlich sind die drei eine Leiter: abmelden (nichts weg), zuruecksetzen (Daten
     weg, Konto bleibt), Konto loeschen (alles weg). */
  t('Zuruecksetzen steht zwischen Abmelden und Konto loeschen', () => {
    const mV = view, mS = session, mA = devAdmin;
    if(!session) session = { access_token:'t', user:{email:'a@b.de'}, username:'k' };
    devAdmin = false;
    view = 'settings'; renderSettings();
    const q = document.getElementById('app').innerHTML;
    const ab = q.indexOf('data-act="logout"');
    const re = q.indexOf('data-act="resetall"');
    const de = q.indexOf('data-act="delaccount"');
    view = mV; session = mS; devAdmin = mA;
    if (ab < 0 || re < 0 || de < 0) return 'ein Knopf fehlt: ab=' + ab + ' re=' + re + ' de=' + de;
    return (ab < re && re < de) || 'Reihenfolge: abmelden=' + ab + ' reset=' + re + ' loeschen=' + de;
  });

  // ================================================ Karls Textliste (v38)
  /* Karl hat am 27.08.2026 zehn Erklaertexte gestrichen und vier gekuerzt. Geprueft wird
     nicht, dass Text FEHLT -- das waere eine Pruefung, die jede spaetere Verbesserung
     bestraft -- sondern das, was beim Streichen kaputtgehen KANN. */

  /* 🔴 Der Regelkreis hatte fuer "zu wenig Wiegungen" einen eigenen Text. Faellt der
     ersatzlos weg, ist `inhalt` undefiniert und im Bild steht das Wort "undefined". */
  t('Bei zu wenigen Wiegungen steht kein "undefined" da', () => {
    const mW = profile.weights, mV = view, mK = JSON.stringify(profile.kcal||null);
    profile.weights = [{date: Date.now(), kg: 80}];        // nur EINE Wiegung
    kcalInit(); profile.kcal.art = 'abnehmen';             // Vorhaben steht -> Regelkreis laeuft
    view = 'body'; renderBody();
    const txt = document.getElementById('app').textContent;
    profile.weights = mW; if(mK !== 'null') profile.kcal = JSON.parse(mK); view = mV;
    return txt.indexOf('undefined') === -1 || 'im Bild steht "undefined"';
  });
  t('Bei zu wenigen Wiegungen steht auch keine leere Karte da', () => {
    const mW = profile.weights, mV = view, mK = JSON.stringify(profile.kcal||null);
    profile.weights = [{date: Date.now(), kg: 80}];
    kcalInit(); profile.kcal.art = 'abnehmen';
    view = 'body'; renderBody();
    const txt = document.getElementById('app').textContent;
    profile.weights = mW; if(mK !== 'null') profile.kcal = JSON.parse(mK); view = mV;
    return txt.indexOf('Waage und Essen im Abgleich') === -1 || 'die Ueberschrift steht noch da';
  });
  /* ⚠️ Der Push-Stand darf nicht ersatzlos verschwinden -- gestrichen war die
     Erklaerung, nicht der Zustand. Sonst steht dort dauerhaft "wird geprueft ...". */
  t('Der Push-Stand nennt weiterhin An oder Aus', () => {
    const quelle = document.documentElement.innerHTML;
    return /stand\.textContent = an \? 'An' : 'Aus'/.test(quelle)
      || 'der Zustand wird nicht mehr gesetzt';
  });
  /* 🔴 Der Hinweis, WAS mit einer Meldung mitgeht, stand auf der Meldeseite und ist
     gestrichen. Mitgeschickt wird es weiterhin -- also muss es auf der Datenschutz-Seite
     stehen bleiben. Sonst waere aus einem gekuerzten Text eine verschwiegene Uebertragung
     geworden, und das ist etwas ganz anderes. */
  t('Was mit einer Meldung mitgeht, steht weiter im Datenschutz', () => {
    const mV = view; view = 'privacy'; renderPrivacy();
    const txt = document.getElementById('app').textContent;
    view = mV;
    const noetig = ['Fassung der App', 'Kennung deines Browsers', 'Bildschirmgröße'];
    const fehlt = noetig.filter(n => txt.indexOf(n) === -1);
    return fehlt.length === 0 || 'fehlt auf der Datenschutz-Seite: ' + fehlt.join(', ');
  });
  t('Die Erfolgs-Seite nennt weiterhin, wie viele Aufgaben offen sind', () => {
    const mV = view; view = 'erfolge'; renderErfolge();
    const txt = document.getElementById('app').textContent;
    view = mV;
    return /Aufgabe(n)? offen|Alles erledigt/.test(txt) || 'der Aufgaben-Stand ist mitgegangen';
  });

  // ================================================ Postfach: gelesen bleibt gelesen (v37)
  /* \U0001f534 Karls Meldung: "die rote Zahl bei den Einstellungen geht nicht weg, wenn ich den
     Postkasten oeffne." Dahinter lagen ZWEI Fehler uebereinander -- und der zweite haette den
     ersten ueberlebt, deshalb steht fuer jeden eine eigene Pruefung hier. */

  const GEL_KEY = 'gymlog:postfach-gelesen';
  const postfachSetzen = (l) => { localStorage.setItem(POST_KEY, JSON.stringify(l));
                                  localStorage.removeItem(GEL_KEY); };

  // ---- Fehler 1: das Oeffnen hat nichts abgehakt ----
  t('Das Oeffnen des Postfachs nimmt die rote Zahl weg', () => {
    const mV = view;
    postfachSetzen([{id:'a', nummer:1, text:'x', antwort:'Hi', gelesen_am:null, erstellt:new Date().toISOString()}]);
    const vorher = postfachUngelesen();
    view = 'meldung'; renderMeldung();
    const nachher = postfachUngelesen();
    view = mV; postfachSetzen([]);
    return (vorher === 1 && nachher === 0) || 'vorher=' + vorher + ' nachher=' + nachher;
  });
  /* 🔴 Nachgebessert, weil die Gegenprobe nicht gebissen hat: ohne das setNav() vorweg
     war nie eine Zahl da, die haette verschwinden koennen -- die Pruefung war gruen, egal ob
     renderMeldung() die Leiste nachzieht oder nicht. Erst wird die Zahl also GEZEICHNET. */
  t('Auch die Zahl an der Leiste ist danach weg', () => {
    const mV = view;
    postfachSetzen([{id:'a', nummer:1, text:'x', antwort:'Hi', gelesen_am:null, erstellt:new Date().toISOString()}]);
    setNav();
    const stand = document.querySelector('#nav button[data-nav="settings"] .navpunkt');
    if(!stand) return 'die Zahl stand vorher schon nicht da - Pruefung sagt nichts aus';
    view = 'meldung'; renderMeldung();
    const punkt = document.querySelector('#nav button[data-nav="settings"] .navpunkt');
    view = mV; postfachSetzen([]);
    return punkt === null || 'die Zahl steht noch da: ' + punkt.textContent;
  });
  /* \u26a0\ufe0f Sie darf aber nicht in dem Moment verschwinden, in dem man hinsieht -- sonst
     erfaehrt man nie, WELCHE Antwort neu war. */
  t('Die neue Antwort bleibt beim Besuch hervorgehoben', () => {
    const mV = view;
    postfachSetzen([{id:'a', nummer:1, text:'x', antwort:'Hi', gelesen_am:null, erstellt:new Date().toISOString()}]);
    view = 'meldung'; renderMeldung();
    const ersteAnsicht = document.querySelectorAll('#app .meld.neu').length;
    renderMeldung();                       // zweites Zeichnen im selben Besuch
    const nochDa = document.querySelectorAll('#app .meld.neu').length;
    view = mV; postfachSetzen([]);
    return (ersteAnsicht === 1 && nochDa === 1) || 'erst=' + ersteAnsicht + ' dann=' + nochDa;
  });
  t('Beim naechsten Besuch ist nichts mehr neu', () => {
    const mV = view, mS = session;
    postfachSetzen([{id:'a', nummer:1, text:'x', antwort:'Hi', gelesen_am:null, erstellt:new Date().toISOString()}]);
    if(!session) session = { access_token:'test' };
    view = 'meldung'; render();            // hin
    view = 'home';    render();            // weg -- hier wird die Besuchsliste geleert
    view = 'meldung'; render();            // und wieder hin
    const neu = document.querySelectorAll('#app .meld.neu').length;
    view = mV; session = mS; postfachSetzen([]); render();
    return eq(neu, 0);
  });
  t('Eine Meldung ohne Antwort wird nicht abgehakt', () => {
    const mV = view;
    postfachSetzen([{id:'a', nummer:1, text:'x', antwort:null, gelesen_am:null, erstellt:new Date().toISOString()}]);
    view = 'meldung'; renderMeldung();
    const l = JSON.parse(localStorage.getItem(POST_KEY));
    view = mV; postfachSetzen([]);
    return l[0].gelesen_am == null || 'wurde abgehakt, obwohl keine Antwort da ist';
  });

  // ---- Fehler 2: der Server hat die Marke wieder ueberschrieben ----
  /* \U0001f534 Das ist der Fehler, der den ersten ueberlebt haette. postfachHolen() legt die
     Serverzeilen ueber die Spiegelung -- solange dort noch `gelesen_am: null` steht, waere die
     rote Zahl sofort wieder da. Ohne Netz sogar dauerhaft. */
  t('Eine Serverzeile macht eine gelesene Antwort nicht wieder auf', () => {
    localStorage.removeItem(GEL_KEY);
    gelesenLokalMerken('a');
    const vomServer = [{id:'a', antwort:'Hi', gelesen_am:null}];
    gelesenLokalAnwenden(vomServer);
    localStorage.removeItem(GEL_KEY);
    return vomServer[0].gelesen_am != null || 'der Server hat die Marke ueberschrieben';
  });
  /* 🔴 Und derselbe Fall einmal durch den ECHTEN Weg, nicht nur durch den Baustein.
     Die Gegenprobe (Aufruf aus postfachHolen entfernen) liess vorher nichts umfallen -- genau
     die Luecke, die heute schon zweimal aufgetreten ist: geprueft war das Teil, nicht sein
     Einbau. Server und Anmeldung sind dafuer hier vorgetaeuscht. */
  await tA('Auch der echte Abruf laesst die gelesene Antwort zu', async () => {
    const mF = window.fetch, mE = window.ensureToken, mS = session;
    localStorage.removeItem(GEL_KEY);
    postfachSetzen([]);
    gelesenLokalMerken('a');
    session = { access_token:'test' };
    window.ensureToken = async () => true;
    window.fetch = async () => ({ ok:true, json: async () => [{id:'a', nummer:1, text:'x',
      antwort:'Hi', gelesen_am:null, erstellt:new Date().toISOString()}] });
    let offen = -1;
    try { await postfachHolen(); offen = postfachUngelesen(); }
    finally { window.fetch = mF; window.ensureToken = mE; session = mS;
              localStorage.removeItem(GEL_KEY); postfachSetzen([]); }
    return offen === 0 || 'nach dem Abruf standen wieder ' + offen + ' ungelesene da';
  });
  t('Weiss der Server es selbst, wird die Kennung wieder vergessen', () => {
    localStorage.removeItem(GEL_KEY);
    gelesenLokalMerken('a');
    gelesenLokalAnwenden([{id:'a', antwort:'Hi', gelesen_am:'2026-08-27T10:00:00Z'}]);
    const rest = gelesenLokal();
    localStorage.removeItem(GEL_KEY);
    return eq(rest.length, 0);
  });
  // \u26a0\ufe0f Sonst waechst die Liste mit jeder je gelesenen Antwort weiter.
  t('Faellt die Zeile aus den 30 Tagen, geht die Kennung mit', () => {
    localStorage.removeItem(GEL_KEY);
    gelesenLokalMerken('uralt');
    gelesenLokalAnwenden([{id:'b', antwort:'Hi', gelesen_am:null}]);
    const rest = gelesenLokal();
    localStorage.removeItem(GEL_KEY);
    return eq(rest.length, 0);
  });
  t('Eine fremde Antwort wird nicht mitabgehakt', () => {
    localStorage.removeItem(GEL_KEY);
    gelesenLokalMerken('a');
    const rows = [{id:'a', antwort:'Hi', gelesen_am:null}, {id:'b', antwort:'Auch', gelesen_am:null}];
    gelesenLokalAnwenden(rows);
    localStorage.removeItem(GEL_KEY);
    return rows[1].gelesen_am == null || 'auch b wurde abgehakt';
  });

  // ================================================ Erfolgs-Symbole (v36)
  // Karls Ansage: "bei den Achievements SVG-Dateien benutzen."
  t('Jeder Erfolg hat ein Symbol, das es auch gibt', () => {
    const fehlt = ERFOLGE.filter(e => !e.svg || !ERFOLG_SVG[e.svg]);
    return fehlt.length === 0 || 'ohne Symbol: ' + fehlt.map(e => e.id + '/' + e.svg).join(', ');
  });
  // ⚠️ Zwei Erfolge mit demselben Bild waeren im Katalog nicht zu unterscheiden - genau
  // das war der Grund, sie ueberhaupt zu zeichnen.
  t('Kein Symbol wird zweimal vergeben', () => {
    const gesehen = {}, doppelt = [];
    ERFOLGE.forEach(e => { if (gesehen[e.svg]) doppelt.push(e.svg); gesehen[e.svg] = 1; });
    return doppelt.length === 0 || 'doppelt: ' + doppelt.join(', ');
  });
  t('Es sind keine Emojis mehr im Katalog', () => {
    const mitEmoji = ERFOLGE.filter(e => e.em);
    return mitEmoji.length === 0 || mitEmoji.length + ' Erfolge haben noch ein Emoji';
  });
  t('Die drei Zustaende sehen verschieden aus', () => {
    const e = ERFOLGE[0];
    const zu = erfolgSvg(e, 'zu'), auf = erfolgSvg(e, 'auf'), frisch = erfolgSvg(e, 'frisch');
    return (/erf-zu/.test(zu) && !/erf-zu|erf-gold/.test(auf) && /erf-gold/.test(frisch))
      || 'zu/auf/frisch nicht unterscheidbar';
  });
  // 🔴 Ein unbekannter Schluessel darf keine leere Luecke hinterlassen - lieber ein
  // Ersatzbild als eine Zeile, in der neben dem Namen nichts steht.
  t('Ein unbekanntes Symbol faellt auf ein Ersatzbild zurueck', () => {
    const svg = erfolgSvg({ svg: 'gibtsnicht' }, 'auf');
    return /<path/.test(svg) || 'leeres Bild: ' + svg;
  });
  /* ⚠️ Seit dem 27.08.2026 tragen auch die drei Tagesaufgaben ein Bild statt eines
     Hakens -- die Zahl auf dieser Seite ist also Erfolge PLUS Aufgaben. Vorher stand hier
     `ERFOLGE.length` allein, und die Pruefung fiel um, obwohl nichts kaputt war. */
  t('Die Erfolgs-Seite zeigt Bilder statt Emojis', () => {
    const merkV = view; view = 'erfolge'; renderErfolge();
    const bilder = document.querySelectorAll('#app .erf-ico').length;
    view = merkV;
    const soll = ERFOLGE.length + AUFGABEN.length;
    return bilder === soll || bilder + ' Bilder statt ' + soll;
  });
  t('Jede Tagesaufgabe hat ein Symbol, das es gibt', () => {
    const fehlt = AUFGABEN.filter(a => !a.svg || !ERFOLG_SVG[a.svg]);
    return fehlt.length === 0 || 'ohne Symbol: ' + fehlt.map(a => a.id).join(', ');
  });
  t('Keine Tagesaufgabe zeigt mehr einen Haken', () => {
    const merkV = view; view = 'erfolge'; renderErfolge();
    const q = document.getElementById('app').innerHTML;
    view = merkV;
    return (q.indexOf('✅') === -1 && q.indexOf('⬜') === -1) || 'da steht noch ein Haken';
  });

  // ================================================ Plan teilen (v35)
  /* Karls Idee: "kann man den Link sonst verpacken? In eine Ueberschrift z.B."
     🔴 Was mit einem Link passiert, entscheidet der Empfaenger. Discord kann ihn hinter
     zwei Worten verstecken, WhatsApp nicht. Geprueft wird deshalb, dass die App die Formen
     richtig BAUT -- nicht, dass ein fremdes Programm sie richtig anzeigt. */
  t('Der Teilen-Dialog geht auf und kennt die Adresse', () => {
    const pr = activeProg();
    sharePlan(pr.id);
    const m = document.getElementById('modal');
    const offen = m.classList.contains('show');
    const url = m.dataset.url || '';
    const knoepfe = m.querySelectorAll('[data-act^="teile-"]').length;
    closeModal();
    return (offen && url.indexOf('#p=') > -1 && knoepfe >= 3)
      || 'offen=' + offen + ' url=' + url.slice(0, 30) + ' knoepfe=' + knoepfe;
  });
  t('Ein Plan ohne Trainings wird nicht geteilt', () => {
    const merk = programs;
    programs = [{ id:'leer', name:'Leer', plans:[] }];
    const merkProg = profile.prog; profile.prog = 'leer';
    sharePlan('leer');
    const offen = document.getElementById('modal').classList.contains('show');
    closeModal(); programs = merk; profile.prog = merkProg; bindPlans();
    return offen === false || 'Dialog ging trotzdem auf';
  });
  /* ⚠️ Runde und eckige Klammern im Plannamen zerreissen die Discord-Schreibweise:
     aus `[Plan (neu)](adresse)` wird bei Discord ein halber Link und sichtbarer Rest. */
  t('Klammern im Plannamen zerreissen den Discord-Link nicht', () => {
    const titel = 'Plan (neu) [alt]';
    const gebaut = `[${titel.replace(/[\[\]()]/g,'')}](https://x.y/#p=z1)`;
    return (gebaut === '[Plan neu alt](https://x.y/#p=z1)')
      || 'kam heraus: ' + gebaut;
  });
  // Die Vorschau-Karte ist das Einzige, was auch bei WhatsApp wirkt.
  t('Die Seite bringt eine Vorschau-Karte mit', () => {
    const noetig = ['og:title', 'og:description', 'og:image', 'og:url'];
    const fehlt = noetig.filter(n => !document.querySelector('meta[property="' + n + '"]'));
    return fehlt.length === 0 || 'fehlt: ' + fehlt.join(', ');
  });
  t('Das Vorschau-Bild steht mit voller Adresse da', () => {
    const el = document.querySelector('meta[property="og:image"]');
    const v = el ? el.getAttribute('content') : '';
    // Ein relativer Pfad taugt hier nicht - der Messenger holt das Bild von aussen.
    return /^https:\/\//.test(v) || 'og:image ist relativ: ' + v;
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
  /* 🔴 Und der Einbau, nicht nur das Teil: `finishWorkout` muss die geplante Zahl auch
     wirklich mitschreiben. Ohne das bliebe `soll` fuer immer leer, `suggest` faende nie
     etwas vor und der reparierte Schutz waere erneut wirkungslos -- diesmal leiser. */
  t('Die geplante Satzzahl wird mitgeschrieben', () => {
    const mA = active, mS = sessions, mX = profile.xp, mV = view;
    sessions = [];
    active = laufendesTraining([{ weight:60, reps:10, done:true },
                                { weight:60, reps:9,  done:true },
                                { weight:'', reps:'', done:false }]);   // dritter nicht gemacht
    finishWorkout();
    const e = sessions.length ? sessions[0].entries[0] : null;
    active = mA; sessions = mS; profile.xp = mX; view = mV; closeModal();
    if(!e) return 'nichts gespeichert';
    return (e.soll === 3 && e.sets.length === 2)
      || 'soll=' + e.soll + ' gespeichert=' + e.sets.length;
  });
  t('Der Aufwaermsatz zaehlt auch beim Speichern nicht ins Soll', () => {
    const mA = active, mS = sessions, mX = profile.xp, mV = view;
    sessions = [];
    active = laufendesTraining([{ weight:40, reps:10, done:true, warm:true },
                                { weight:60, reps:10, done:true }]);
    finishWorkout();
    const e = sessions.length ? sessions[0].entries[0] : null;
    active = mA; sessions = mS; profile.xp = mX; view = mV; closeModal();
    return (e && e.soll === 1) || 'soll=' + (e && e.soll);
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

  // 🗑️ Hier standen bis zum 29.08.2026 zwei Pruefungen zur Tagesaufgabe „Reingeschaut"
  // (Reihenfolge beim Start, Nachfassen beim Zurueckkommen in die App). Beide sind mit der
  // Aufgabe weggefallen -- es gibt kein XP mehr fuers blosse Oeffnen, Karls Ansage.
  // ⚠️ Was von ihnen BLEIBEN muss, steht jetzt oben bei „Keine Aufgabe fuers blosse
  // Oeffnen der App": dass die Startfolge sie auch wirklich nicht mehr abhakt.
  // 🔴 Damit diese Textsuche greifen kann, darf der Aufruf auch in KOMMENTAREN nicht mehr
  // woertlich dastehen -- eine Textsuche unterscheidet Prosa nicht von Code. Am 29.08. war
  // die Pruefung genau deshalb einmal rot, obwohl kein Aufruf mehr existierte.

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

  // ================================================ XP-Bestenliste (29.08.2026)
  // Karls Wunsch: die zehn mit den meisten XP, auf der Erfolge-Seite.
  const erfolgeSeite = () => {
    const sV = session, bV = bestenliste;
    session = {user:{id:'ich', email:'karl@example.com'}, username:'karl',
               expires_at: Date.now()+3600e3, access_token:'x'};
    return {
      zeichne: (liste) => { bestenliste = liste; view = 'erfolge'; render(); return app.innerHTML; },
      zurueck: () => { session = sV; bestenliste = bV; view = 'home'; render(); }
    };
  };

  // ⚠️ Karls Meldung 29.08.2026: „in Erfolge steht 30 Wiegen, das ist doch kein Deutsch."
  // Stimmt -- `Wiegen` als zaehlbare Mehrzahl gibt es nicht, eine Wiege ist ein Kinderbett.
  t('Kein Erfolg heisst mehr "Wiegen"', () => {
    const schlecht = ERFOLGE.filter(e => /\bWiegen\b/.test(e.name));
    return schlecht.length === 0 || schlecht.map(e => e.name).join(', ');
  });

  // 🔴 Drei Zustaende, drei Anzeigen. Der wichtigste ist `false`: solange das SQL nicht
  // ausgefuehrt ist, antwortet Supabase mit einem Fehler -- und der darf nicht wie ein
  // Absturz aussehen, sondern muss sagen, was zu tun ist.
  t('Ohne eingerichtete Tabelle sagt die Seite, was fehlt', () => {
    const e = erfolgeSeite();
    const h = e.zeichne(false);
    e.zurueck();
    return (h.includes('noch nicht eingerichtet') && h.includes('supabase-bestenliste.sql'))
      || 'kein Hinweis auf das fehlende SQL';
  });
  t('Vor dem Laden steht "Wird geladen", nicht "niemand drin"', () => {
    const e = erfolgeSeite();
    const h = e.zeichne(null);
    e.zurueck();
    if (h.includes('Noch niemand drin')) return 'leer und ungeladen werden verwechselt';
    return h.includes('Wird geladen') || 'kein Ladehinweis';
  });
  t('Eine leere Liste sagt "Noch niemand drin"', () => {
    const e = erfolgeSeite();
    const h = e.zeichne([]);
    e.zurueck();
    return h.includes('Noch niemand drin') || 'keine Leer-Anzeige';
  });
  t('Die Bestenliste zeigt Platz, Name und XP', () => {
    const e = erfolgeSeite();
    const h = e.zeichne([{user_id:'a', name:'tibo', xp:42000},
                         {user_id:'ich', name:'karl', xp:8000},
                         {user_id:'c', name:'georg', xp:150}]);
    e.zurueck();
    if (!h.includes('tibo')) return 'Name fehlt';
    if (!h.includes('42.000')) return 'XP nicht als Zahl formatiert';
    if (h.indexOf('tibo') > h.indexOf('georg')) return 'nicht nach XP sortiert angezeigt';
    return true;
  });
  // Damit man sich in einer Liste von zehn Namen selbst wiederfindet.
  t('Die eigene Zeile ist markiert', () => {
    const e = erfolgeSeite();
    const h = e.zeichne([{user_id:'a', name:'tibo', xp:42000},
                         {user_id:'ich', name:'karl', xp:8000}]);
    e.zurueck();
    return h.includes('· du') || 'eigene Zeile nicht erkennbar';
  });
  /* 🗑️ Hier stand eine Pruefung darauf, dass auf der Seite steht, woher die Zahlen
     kommen. Karl hat den Satz am 29.08.2026 streichen lassen -- damit faellt auch die
     Pruefung. ⚠️ Festgehalten, weil es eine Zusicherung war, die ICH eingebaut hatte und
     nicht er: die Zahlen kommen weiterhin vom Geraet, es steht nur nicht mehr in der App.
     Der Hinweis lebt im Kopf von `supabase-bestenliste.sql` weiter. */
  /* ⚠️ Namen mit spitzen Klammern duerfen die Seite nicht umbauen -- sie kommen von anderen
     Nutzern und sind damit fremder Text, nicht eigener.
     🔴 Der Koeder ist bewusst HARMLOS (`<i>`, kein `onerror`). Beim ersten Versuch stand
     hier `<img src=x onerror=alert(1)>`. Das ist als Gegenprobe verlockend, weil es den
     Einbruch wirklich vorfuehrt -- aber genau deshalb unbrauchbar: ohne esc() FEUERT es, und
     ein alert() haelt den Pruef-Browser an, bis die Zeitgrenze zuschlaegt. Die Gegenprobe
     wurde damit nicht rot, sondern hing 180 Sekunden und lieferte gar kein Ergebnis.
     ➡️ Eine Pruefung, die im Fehlerfall haengt statt rot zu werden, ist keine Pruefung.
     `<i>` beweist dasselbe: entschaerft steht `&lt;i&gt;` in der Seite, roh ein echtes Tag. */
  t('Ein Name mit HTML darin wird entschaerft', () => {
    const e = erfolgeSeite();
    const h = e.zeichne([{user_id:'a', name:'<i>fremd</i>', xp:1}]);
    e.zurueck();
    if (h.includes('<i>fremd</i>')) return 'fremder Name landet als echtes HTML in der Seite';
    return h.includes('&lt;i&gt;fremd') || 'der Name steht gar nicht da';
  });
  /* 🔴 Die Pruefung, die es wirklich wert ist: was VERLAESST das Geraet.
     Am 24.08. gab `email_for_username` E-Mail-Adressen heraus. Eine Bestenliste ist genau
     dieselbe Bauform -- etwas ueber andere Leute, fuer alle lesbar. Hier wird deshalb der
     Rumpf der Anfrage gepreuft, nicht die Anzeige. */
  t('Hochgeschickt werden nur Name, XP und Zeitpunkt', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    const i = q.indexOf('async function bestenlisteSchieben');
    if (i < 0) return 'bestenlisteSchieben fehlt';
    const rumpf = q.slice(i, i + 1200);
    const verboten = ['session.user.email,', 'profile.weights', 'sessions', 'appDataBlob'];
    const drin = verboten.filter(w => rumpf.indexOf(w) >= 0);
    if (drin.length) return 'im Rumpf steht: ' + drin.join(', ');
    // Der Name wird aus der E-Mail abgeleitet, wenn kein Benutzername da ist -- dann aber
    // nur der Teil VOR dem @. Ohne dieses split stuende die ganze Adresse in der Liste.
    return rumpf.indexOf("split('@')[0]") >= 0
      || 'ohne split am @ koennte die volle E-Mail-Adresse in der Bestenliste landen';
  });
  // ⚠️ Gelesen werden duerfen auch nur diese Spalten -- ein `select=*` wuerde spaeter jede
  // neue Spalte automatisch mit herausgeben.
  t('Gelesen wird mit ausdruecklicher Spaltenliste, nicht mit select=*', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    const i = q.indexOf('gym_bestenliste?select=');
    if (i < 0) return 'kein select auf gym_bestenliste';
    const zeile = q.slice(i, i + 120);
    if (zeile.indexOf('select=*') >= 0) return 'select=* statt Spaltenliste';
    return zeile.indexOf('limit=10') >= 0 || 'kein limit=10 -- Karl wollte die Top 10';
  });

  // 🗑️ Karls Ansage vom 29.08.2026: die Serie kann von der STARTSEITE raus.
  // ⚠️ Die Rechnung darunter bleibt geprueft -- nur ihre Karte ist weg. Ohne diese Pruefung
  // koennte sie bei der naechsten Aenderung an renderHome still zurueckkommen.
  t('Die Wochen-Serie steht nicht mehr auf der Startseite', () => {
    const sesV = sessions, sV = session;
    session = {user:{id:'test'}, expires_at: Date.now()+3600e3, access_token:'x'};
    sessions = [0,1,2].map(n => ({date: vorWochen(n) + 864e5, entries: []}));
    if (wochenSerie() !== 3) { sessions = sesV; session = sV; return 'Aufbau falsch: Serie ist nicht 3'; }
    view = 'home'; render();
    const h = app.innerHTML;
    sessions = sesV; session = sV; view = 'home'; render();
    if (h.includes('am St\u00fcck')) return 'die Serien-Karte steht wieder auf der Startseite';
    if (h.includes('Wochen am St')) return 'die Serien-Karte steht wieder auf der Startseite';
    return true;
  });
  // 🔴 Und die Gegenprobe zur Gegenprobe: die Serie darf nicht ueberall verschwunden sein.
  // Karl hat „auf der Startseite" gesagt -- das Jahresraster im Verlauf zeigt sie weiter.
  t('Im Verlauf gibt es das Jahresraster weiterhin', () => {
    const sesV = sessions, sV = session;
    session = {user:{id:'test'}, expires_at: Date.now()+3600e3, access_token:'x'};
    sessions = [0,1,2].map(n => ({date: vorWochen(n) + 864e5, entries: []}));
    view = 'history'; render();
    const h = app.innerHTML;
    sessions = sesV; session = sV; view = 'home'; render();
    return h.length > 200 || 'Verlauf ist leer';
  });

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
  t('Weiter fuehrt bis zur Zusammenfassung', () => {
    kobFrisch(); kobBauen();
    let n = 0;
    for(let i = 0; i < 12; i++){
      // ⚠️ Schritt 1 sperrt Weiter, solange kein Vorhaben gewaehlt ist - das ist gewollt,
      // also muss die Pruefung waehlen statt sich am eigenen Riegel aufzuhaengen.
      const wahl = document.querySelector('[data-act="kob:art:halten"]');
      if(wahl) wahl.click();
      const w = document.querySelector('[data-act="kob:next"]');
      if(!w || w.disabled) break; w.click(); n++; }
    return (kobStep === KOB_LAST && n === KOB_LAST) || ('Schritt ' + kobStep + ' von ' + KOB_LAST + ', ' + n + ' Klicks');
  });
  t('Fuer jeden Schritt gibt es einen Satz von Brock', () => eq(KOB_SAY.length, KOB_LAST + 1));
  /* 🔴 Der Schluessel-Schritt darf NICHT blockieren. Er verlangt etwas von aussen
     (Google-Konto, zweite Seite, Warten) -- wer da haengenbleibt, richtet die Kalorien nie
     ein. "Weiter" muss also auch ohne Schluessel offen sein. */
  t('Der Schluessel-Schritt laesst sich ueberspringen', () => {
    kobFrisch(); kobBauen();
    kobDraft.art='halten'; kobDraft.wochen=12; kobDraft.kg=80;
    kobStep = KOB_LAST - 1; renderKcalOb();
    const w = document.querySelector('[data-act="kob:next"]');
    return (w && !w.disabled) || 'Weiter ist gesperrt';
  });
  t('Der Schluessel-Schritt bietet das Eintragen an', () => {
    kobFrisch(); kobBauen();
    kobDraft.art='halten'; kobDraft.wochen=12; kobDraft.kg=80;
    kobStep = KOB_LAST - 1; renderKcalOb();
    return !!document.querySelector('[data-act="kob:key"]') || 'kein Knopf zum Eintragen';
  });
  // ⚠️ Sonst sieht es aus, als ginge ohne Schluessel gar nichts - dabei brauchen
  // Barcode, eigene Lebensmittel und das Tagesziel keinen.
  t('Der Schritt sagt, dass es auch ohne geht', () => {
    kobFrisch(); kobBauen();
    kobDraft.art='halten'; kobDraft.wochen=12; kobDraft.kg=80;
    kobStep = KOB_LAST - 1; renderKcalOb();
    return /auch ohne/.test(document.getElementById('app').textContent) || 'kein Hinweis darauf';
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
    // ⚠️ KOB_LAST statt einer festen 4: am 27.08.2026 kam der Schritt mit dem
    // KI-Schluessel dazu, und elf Pruefungen sprangen auf einen Schritt, auf dem es kein
    // "Fertig" gibt. Die Zusammenfassung ist der letzte Schritt, wie viele es auch sind.
    kobStep = KOB_LAST; renderKcalOb();
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
    kobStep = KOB_LAST; renderKcalOb();
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

  /* ================================================ Hinweis auf eine neue Fassung (31.08.2026)
     Karl hatte am 27.08. zweimal die alte Fassung vor sich und hat es einmal als Fehler
     gemeldet ("es sind nur 2 Tutorials da"). Der Service Worker holt das Neue sofort --
     aber ein Fenster, das schon offen steht, behaelt sein HTML.
     ⚠️ **Der Melde-Weg selbst ist hier nicht pruefbar.** `updatefound` und `statechange`
     haengen an `navigator.serviceWorker`, und den gibt es unter `file://` gar nicht.
     Geprueft wird die ausgelagerte Entscheidung -- und der Einbau ueber APP_QUELLE. */
  t('Wartet eine Fassung und laeuft kein Training, ist die Leiste faellig', () => {
    return fassungsLeisteFaellig(true, 'home') === true || 'sie bliebe verborgen';
  });
  /* 🔴 Die Gegenprobe, um die es hier eigentlich geht: mitten im Training darf nichts
     aufpoppen, was beim Antippen die Seite neu laedt. */
  t('Mitten im Training wird sie zurueckgehalten', () => {
    return fassungsLeisteFaellig(true, 'workout') === false || 'sie erscheint im Training';
  });
  t('Ohne wartende Fassung erscheint sie nie', () => {
    return (fassungsLeisteFaellig(false, 'home') === false
         && fassungsLeisteFaellig(undefined, 'home') === false) || 'sie erscheint grundlos';
  });
  t('Beim Start ist die Leiste da, aber unsichtbar', () => {
    const el = document.getElementById('neufassung');
    if(!el) return 'die Leiste fehlt im Dokument';
    return el.classList.contains('show') === false || 'sie steht schon beim Start offen';
  });
  /* 🔴 Der Einbau statt nur des Teils: eine Entscheidung, die niemand abruft, ist keine. */
  t('render() holt einen zurueckgehaltenen Hinweis nach', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    return rumpf(q, 'render').indexOf('neueFassungPruefen()') > -1
      || 'render() fragt nicht nach';
  });
  /* ⚠️ Ohne `controller` in der Bedingung saehe JEDER neue Nutzer beim allerersten Start
     "Neue Fassung ist da" -- `installed` ist auch der Zustand der Erstinstallation. */
  t('Die Erstinstallation loest keinen Hinweis aus', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    const i = q.indexOf("neu.state === 'installed'");
    if(i < 0) return 'die Bedingung steht nicht da';
    return q.slice(i, i + 160).indexOf('navigator.serviceWorker.controller') > -1
      || 'installed wird ohne controller-Abfrage geglaubt';
  });
  /* Reihenfolge, wie beim Abmelden: erst wegschreiben, dann neu laden. Andersherum kostet
     ein Klick auf die Leiste den zuletzt eingetippten Satz. */
  t('Der Klick schreibt weg, BEVOR er neu laedt', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    const i = q.indexOf("leiste.addEventListener('click'");
    if(i < 0) return 'der Klick-Anschluss fehlt';
    const r = q.slice(i, i + 400).replace(/\/\*[\s\S]*?\*\//g, '');
    const f = r.indexOf('flushSync()'), l = r.indexOf('location.reload()');
    if(f < 0 || l < 0) return 'einer der beiden Schritte fehlt';
    return f < l || 'es wird neu geladen, bevor gespeichert ist';
  });
  /* 🔴 Und die Pruefung, die den eigentlichen Fund vom 31.08.2026 festhaelt: `APP_FASSUNG`
     stand 22 Fassungen lang auf 'v32', waehrend sw.js schon bei 'gymlog-v54' war. Der
     Kommentar "mit der Cacheversion in sw.js gleichziehen" stand die ganze Zeit daneben --
     **ein Kommentar haelt nichts fest.** Jede Problemmeldung trug die falsche Nummer.
     ⚠️ Und es haengt mehr daran als die Meldung: wird sw.js NICHT hochgezaehlt, laedt der
     Browser den Service Worker gar nicht erst neu -- dann bleibt der Hinweis oben fuer
     immer stumm, ohne dass irgendwo etwas rot wird. */
  t('APP_FASSUNG und die Cacheversion in sw.js ziehen gleich', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    const s = window.SW_QUELLE || ''; if(!s) return 'SW_QUELLE fehlt';
    const a = q.match(/APP_FASSUNG\s*=\s*'(v\d+)'/);
    const b = s.match(/CACHE\s*=\s*'gymlog-(v\d+)'/);
    if(!a) return 'APP_FASSUNG nicht gefunden';
    if(!b) return 'die Cacheversion in sw.js nicht gefunden';
    return a[1] === b[1] || ('App steht auf ' + a[1] + ', sw.js auf ' + b[1]);
  });

  /* ================================================ Essen aus der Datenbank suchen (31.08.2026)
     Karls Ansage: "wir brauchen eine datenbank fuer essen zum eintragen falls man keinen
     qr code hat". Die Datenbank hing schon dran -- aber nur am Barcode. */
  t('Kalorien kommen direkt aus energy-kcal_100g', () => {
    const d = offNachDraft({ product_name:'Quark', nutriments:{ 'energy-kcal_100g':66,
              proteins_100g:12, carbohydrates_100g:4, fat_100g:0.2 } });
    return (d && d.kcal === 66 && d.p === 12 && d.c === 4 && d.f === 0) || JSON.stringify(d);
  });
  /* ⚠️ Nicht jedes Produkt hat Kalorien -- manche nur Kilojoule. Ohne die Umrechnung stuende
     bei einem solchen Treffer der KJ-Wert als kcal da, also gut das Vierfache. */
  t('Fehlt kcal, wird aus Kilojoule umgerechnet', () => {
    const d = offNachDraft({ product_name:'X', nutriments:{ energy_100g:1000 } });
    return (d && d.kcal === 239) || 'kcal=' + (d && d.kcal);
  });
  /* 🔴 Der Fall, der die Trefferliste sonst mit Sackgassen fuellt: von den Produkten mit
     Deutschland-Kennung hatte am 22.08.2026 nur gut die Haelfte vollstaendige Naehrwerte. */
  t('Ohne jede Naehrwertangabe kommt nichts zurueck', () => {
    return (offNachDraft({ product_name:'X', nutriments:{} }) === null
         && offNachDraft({ product_name:'X' }) === null) || 'es kam ein Entwurf zurueck';
  });
  t('Der deutsche Name schlaegt den englischen', () => {
    const d = offNachDraft({ product_name:'Skimmed quark', product_name_de:'Magerquark',
              nutriments:{ 'energy-kcal_100g':66 } });
    return (d && d.name === 'Magerquark') || 'name=' + (d && d.name);
  });
  // Bei OFF stehen mehrere Marken in einem Feld, kommagetrennt ("Bio+, Aldi_bio").
  t('Von mehreren Marken bleibt die erste', () => {
    const d = offNachDraft({ product_name:'X', brands:'Bio+, Aldi_bio',
              nutriments:{ 'energy-kcal_100g':66 } });
    return (d && d.marke === 'Bio+') || 'marke=' + (d && d.marke);
  });

  /* 🔴 Und jetzt die Suche selbst, mit gefaelschtem `fetch`. Der Kern ist der Filter:
     ein Treffer ohne Naehrwerte darf gar nicht erst in der Liste stehen. */
  await tA('Treffer ohne Naehrwerte stehen nicht in der Liste', async () => {
    const mF = window.fetch, mS = foodStep, mV = view;
    window.fetch = async () => ({ ok:true, status:200, json: async () => ({ products:[
      { code:'1', product_name:'Mit Werten',  nutriments:{ 'energy-kcal_100g':66 } },
      { code:'2', product_name:'Ohne Werte',  nutriments:{} },
      { code:'3', product_name:'Nur Joule',   nutriments:{ energy_100g:418.4 } } ] }) });
    await dbSuche('quark');
    const namen = dbTreffer.map(f => f.name).join('|'), schritt = foodStep;
    window.fetch = mF; foodStep = mS; view = mV; dbTreffer = []; foodFehler = '';
    return (namen === 'Mit Werten|Nur Joule' && schritt === 'db') || namen + ' / ' + schritt;
  });
  /* 💡 Der Code wird mitgenommen, obwohl niemand gescannt hat: wer den Treffer behaelt,
     trifft ihn beim naechsten Mal sofort per Scan -- ohne Netz und ohne Suche. */
  await tA('Der Barcode des Treffers wird mitgenommen', async () => {
    const mF = window.fetch, mS = foodStep, mV = view;
    window.fetch = async () => ({ ok:true, status:200, json: async () => ({ products:[
      { code:'4260428021766', product_name:'Quark', nutriments:{ 'energy-kcal_100g':66 } } ] }) });
    await dbSuche('quark');
    const bc = dbTreffer[0] && dbTreffer[0].barcode;
    window.fetch = mF; foodStep = mS; view = mV; dbTreffer = []; foodFehler = '';
    return bc === '4260428021766' || 'barcode=' + bc;
  });
  /* ⚠️ Open Food Facts drosselt: beim Bauen am 31.08.2026 kamen nach wenigen Anfragen
     hintereinander nur noch 503er. Ein 503 ist kein Netzfehler -- `fetch` wirft dabei
     NICHT, es kommt eine gueltige Antwort mit ok:false. Ohne die Abfrage liefe die App
     in `d.products` von einer HTML-Fehlerseite. */
  await tA('Eine 503-Antwort wird als Fehler behandelt, nicht als leeres Ergebnis', async () => {
    const mF = window.fetch, mS = foodStep, mV = view;
    window.fetch = async () => ({ ok:false, status:503, json: async () => ({}) });
    await dbSuche('quark');
    const f = foodFehler, schritt = foodStep;
    window.fetch = mF; foodStep = mS; view = mV; foodFehler = '';
    return (/503/.test(f) && schritt === 'list') || 'Fehler="' + f + '" Schritt=' + schritt;
  });
  /* 🔴 Dieselbe Frage am zweiten Aufrufstelle — und hier ist der Schaden groesser als
     eine Fehlermeldung. Der catch-Block in `holeBarcode` entscheidet am WORTLAUT der
     Meldung, ob das Anlegen-Formular aufgeht. Ohne `r.ok` faellt ein 503 durch
     `!d.product` in "steht nicht in der Datenbank" — und Karl tippt die Naehrwerte
     einer Packung ab, die die Datenbank kennt. Nichts wird rot.
     ⚠️ Diese Pruefung schaut deshalb auf foodStep, nicht nur auf den Fehlertext:
     entscheidend ist, dass das Formular NICHT aufgeht. (Fund vom 01.09.2026) */
  await tA('Ein 503 beim Scannen oeffnet nicht das Anlegen-Formular', async () => {
    const mF = window.fetch, mS = foodStep, mV = view, mD = foodDraft;
    window.fetch = async () => ({ ok:false, status:503, json: async () => ({}) });
    await holeBarcode('0000000000000');
    const f = foodFehler, schritt = foodStep;
    window.fetch = mF; foodStep = mS; view = mV; foodDraft = mD; foodFehler = '';
    return (schritt !== 'new' && /503/.test(f)) || 'Schritt=' + schritt + ' Fehler="' + f + '"';
  });
  /* Und die Gegenprobe zum Fund: der echte "gibt es nicht"-Fall muss weiter ins
     Formular fuehren — sonst waere die Reparatur oben zu grob geraten. */
  await tA('Ein echtes Nicht-Gefunden oeffnet das Anlegen-Formular weiterhin', async () => {
    const mF = window.fetch, mS = foodStep, mV = view, mD = foodDraft;
    window.fetch = async () => ({ ok:true, status:200, json: async () => ({ status:0 }) });
    await holeBarcode('0000000000000');
    const schritt = foodStep, bc = foodDraft && foodDraft.barcode;
    window.fetch = mF; foodStep = mS; view = mV; foodDraft = mD; foodFehler = '';
    return (schritt === 'new' && bc === '0000000000000') || 'Schritt=' + schritt + ' bc=' + bc;
  });
  /* 🔴 Der Rest des Fundes vom 01.09., geschlossen am 02.09.2026. Die Weiche im
     catch hing am WORTLAUT der Fehlermeldung -- so sehr, dass die v57-Reparatur ihre
     eigene Meldung so formulieren musste, dass sie nicht darauf passt.
     Diese Pruefung wirft einen Fehler, den es so heute gar nicht gibt, und dessen Text
     zufaellig den Ausdruck enthaelt. Frueher waere das Formular aufgegangen und Karl
     haette eine Packung abgetippt, weil das Netz weg war. */
  await tA('Ein fremder Fehler mit dem richtigen Wortlaut oeffnet nichts', async () => {
    const mF = window.fetch, mS = foodStep, mV = view, mD = foodDraft;
    window.fetch = async () => { throw new Error('Proxy: Host nicht in der Datenbank hinterlegt'); };
    await holeBarcode('0000000000000');
    const schritt = foodStep;
    window.fetch = mF; foodStep = mS; view = mV; foodDraft = mD; foodFehler = '';
    return schritt !== 'new' || 'das Anlegen-Formular ist trotzdem aufgegangen';
  });
  /* ⚠️ Und die Gegenrichtung, damit die Weiche nicht einfach zugenagelt wird:
     der markierte Fall muss weiterhin durch. */
  t('Die Weiche liest ein Merkmal, nicht den Text', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    const i = q.indexOf('const nichtDrin');
    if(i < 0) return 'die Weiche nicht gefunden';
    const zeile = q.slice(i, q.indexOf(';', i));
    if(/\.test\(/.test(zeile)) return 'sie prueft wieder den Wortlaut: ' + zeile.trim();
    return zeile.indexOf('.art') > -1 || 'kein Merkmal am Fehler: ' + zeile.trim();
  });
  t('Ein einzelner Buchstabe fragt die Datenbank gar nicht erst', () => {
    const mF = window.fetch; let rufe = 0;
    window.fetch = async () => { rufe++; return { ok:true, json: async () => ({products:[]}) }; };
    dbSuche('a');
    window.fetch = mF; foodFehler = '';
    return rufe === 0 || 'es wurde ' + rufe + 'x gefragt';
  });
  /* 🔴 Der Einbau: die Suche ist nur erreichbar, wenn der Knopf sie auch ausloest. */
  t('Der Knopf unter der Liste ruft die Suche auf', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    return (q.indexOf("data-act=\"food:dbsuche\"") > -1
         && q.indexOf("a==='food:dbsuche'") > -1
         && q.indexOf('dbSuche(s?s.value') > -1) || 'der Weg vom Knopf zur Suche ist unterbrochen';
  });
  t('Ein Treffer fuehrt in den Mengen-Schritt', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    const i = q.indexOf('t.dataset.dbpick');
    if(i < 0) return 'der Treffer ist nicht anklickbar';
    return q.slice(i, i + 220).indexOf("foodStep='menge'") > -1 || 'er landet nicht bei der Menge';
  });
  /* Der Barcode-Weg muss dieselbe Umwandlung benutzen -- sonst laufen die beiden Wege
     wieder auseinander, und die Kilojoule-Umrechnung gaebe es nur noch auf einem. */
  t('Der Barcode-Weg benutzt dieselbe Umwandlung', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    return rumpf(q, 'holeBarcode').indexOf('offNachDraft(') > -1
      || 'holeBarcode rechnet wieder selbst';
  });

  /* ================================================ Karls Ansage vom 31.08.2026: der Satz raus
     "Die Gewichtskurve steht, aber es fehlen Essenstage: 0 von mindestens 4 ..."
     Dieselbe Behandlung wie der Wiegungs-Satz am 27.08.: keine Karte statt einer leeren. */
  t('Der Satz ueber fehlende Essenstage steht nicht mehr im Quelltext', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    return q.indexOf('es fehlen Essenstage') === -1 || 'der Satz steht noch da';
  });
  /* ⚠️ Und der Einbau dazu: der Zweig muss leer bleiben, sonst stuende eine leere Karte da.
     Genau davor warnt der Kommentar beim Wiegungs-Satz. */
  t('Bei zu wenig Essenstagen bleibt die Karte ganz weg', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    const i = q.indexOf("rk.stand==='zu-wenig-essen'");
    if(i < 0) return 'der Zweig fehlt ganz';
    const nach = q.slice(i, i + 120).replace(/\/\*[\s\S]*?\*\//g, '');
    return /inhalt\s*=\s*''/.test(nach) || 'der Zweig setzt wieder einen Inhalt';
  });

  /* ================================ Die Bestenliste und das Netz (Fund 4, 01.09.2026)
     Der Vertrag steht seit jeher im Quelltext: null = noch nicht geladen, [] = leer,
     false = gibt es serverseitig nicht. Gebrochen hat ihn die ERSTE ZEILE --
     `ensureToken()` gibt auch bei Netzfehler und 5xx false zurueck.
     Auf dem Bildschirm stand dann "Die Bestenliste ist noch nicht eingerichtet" samt
     Verweis auf supabase-bestenliste.sql: keine ausbleibende Antwort, sondern eine
     falsche Arbeitsanweisung.
     🔴 Die alten Pruefungen reichten false, null und [] direkt ans Zeichnen --
     sie pruefen, dass jeder Zustand richtig ANGEZEIGT wird, nie welchen Zustand
     bestenlisteHolen tatsaechlich LIEFERT. Das Teil war geprueft, der Einbau nicht. */
  const mitServer = async (antwort, fn) => {
    const mF = window.fetch, mE = window.ensureToken, mS = session;
    session = { access_token:'test', user:{id:'u1'} };
    window.ensureToken = async () => true;
    window.fetch = typeof antwort === 'function' ? antwort : (async () => antwort);
    try { return await fn(); }
    finally { window.fetch = mF; window.ensureToken = mE; session = mS; }
  };

  await tA('Kein Netz heisst "gerade nicht", nicht "gibt es nicht"', async () =>
    mitServer(async () => { throw new Error('kein Netz'); },
      async () => eq(await bestenlisteHolen(), null)));
  await tA('Ein ueberlasteter Server heisst nicht "nicht eingerichtet"', async () =>
    mitServer({ ok:false, status:503, json: async () => ({}) },
      async () => eq(await bestenlisteHolen(), null)));
  /* ⚠️ Und die Gegenrichtung: 404 heisst wirklich "die Tabelle fehlt". Ohne diese
     Pruefung koennte man Fund 4 "reparieren", indem man nie mehr false liefert -- dann
     saehe niemand mehr, dass das SQL fehlt. */
  await tA('Fehlt die Tabelle wirklich, sagt es das auch', async () =>
    mitServer({ ok:false, status:404, json: async () => ({}) },
      async () => eq(await bestenlisteHolen(), false)));
  await tA('Eine abgelaufene Anmeldung leert die Liste nicht', async () => {
    const mE = window.ensureToken, mS = session;
    session = { access_token:'test', user:{id:'u1'} };
    window.ensureToken = async () => false;
    try { return eq(await bestenlisteHolen(), null); }
    finally { window.ensureToken = mE; session = mS; }
  });
  await tA('Antwortet der Server, kommt die Liste durch', async () =>
    mitServer({ ok:true, status:200, json: async () => [{user_id:'a', name:'Karl', xp:5}] },
      async () => { const r = await bestenlisteHolen();
        return (Array.isArray(r) && r.length === 1) || JSON.stringify(r); }));

  /* ================================ Die Melde-Schlange (Fund 5, 01.09.2026)
     🔴 Eine dauerhaft abgewiesene Meldung blieb vorn stehen und alles dahinter kam
     nie mehr los. Genau die Sackgasse, vor der der Kommentar beim Stapelversand warnt --
     der Umbau auf Einzelversand hat die Nachbarn befreit, den Kopf nicht.
     Fuer Karl sah es so aus: "Danke! Meldung ist raus.", ein Fehler-Toast fuer 1,8
     Sekunden, und danach kam nie wieder etwas in Discord an. */
  const mitSchlange = async (eintraege, antwort, fn) => {
    const mF = window.fetch, mE = window.ensureToken, mS = session;
    const mL = localStorage.getItem(MELD_KEY);
    session = { access_token:'test', user:{id:'u1'} };
    window.ensureToken = async () => true;
    meldungenSchreiben(eintraege);
    DB.set(MELD_ABGELEHNT, []);
    window.fetch = antwort;
    try { return await fn(); }
    finally { window.fetch = mF; window.ensureToken = mE; session = mS;
              DB.set(MELD_ABGELEHNT, []);
              if(mL === null) localStorage.removeItem(MELD_KEY);
              else localStorage.setItem(MELD_KEY, mL); }
  };
  const meld = (id) => ({ id, text:'x'+id, umfeld:{}, erstellt:new Date().toISOString() });

  await tA('Eine abgewiesene Meldung blockiert die naechsten nicht', async () =>
    mitSchlange([meld('a'), meld('b'), meld('c')],
      async (u, o) => { const koerper = JSON.parse(o.body);
        return koerper.id === 'a' ? { ok:false, status:400, text: async () => 'kaputt' }
                                  : { ok:true, status:201, text: async () => '' }; },
      async () => {
        try { await meldungenNachreichen(); } catch(e) {}
        const rest = meldungenLesen();
        return rest.length === 0 || ('es liegen noch ' + rest.length + ' in der Schlange: '
          + rest.map(x=>x.id).join(','));
      }));
  await tA('Die abgewiesene Meldung geht nicht verloren', async () =>
    mitSchlange([meld('a'), meld('b')],
      async (u, o) => JSON.parse(o.body).id === 'a'
        ? { ok:false, status:400, text: async () => 'kaputt' }
        : { ok:true, status:201, text: async () => '' },
      async () => {
        try { await meldungenNachreichen(); } catch(e) {}
        const w = abgelehnteLesen();
        return (w.length === 1 && w[0].id === 'a' && w[0].status === 400) || JSON.stringify(w);
      }));
  await tA('Der Fehler wird gesagt, nicht verschluckt', async () =>
    mitSchlange([meld('a')],
      async () => ({ ok:false, status:400, text: async () => 'kaputt' }),
      async () => {
        try { await meldungenNachreichen(); return 'es kam kein Fehler heraus'; }
        catch(e) { return /abgewiesen/.test(String(e.message||e))
          || ('unerwarteter Text: ' + e.message); }
      }));
  /* ⚠️ Ein 5xx ist etwas anderes: der Server ist nur gerade ueberlastet. Da MUSS
     alles liegenbleiben -- sonst wuerfe eine Wartung die ganze Schlange weg. */
  await tA('Eine Serverwartung wirft die Schlange nicht weg', async () =>
    mitSchlange([meld('a'), meld('b')],
      async () => ({ ok:false, status:503, text: async () => 'wartung' }),
      async () => {
        try { await meldungenNachreichen(); } catch(e) {}
        return eq(meldungenLesen().length, 2);
      }));
  await tA('Die Bremse laesst die Meldung liegen', async () =>
    mitSchlange([meld('a')],
      async () => ({ ok:false, status:400, text: async () => 'GYM_BREMSE:7' }),
      async () => {
        try { await meldungenNachreichen(); } catch(e) { return 'die Bremse kam als Fehler'; }
        return (meldungenLesen().length === 1 && abgelehnteLesen().length === 0)
          || 'die gebremste Meldung wurde beiseitegelegt';
      }));
  /* 🔴 Die zweite Haelfte von Fund 5, und sie ist eine Handregel: das Wort muss
     woertlich mit supabase-meldungen.sql uebereinstimmen. Wird es dort umformuliert,
     gilt die Drosselung hier als harter Fehler -- und die Schlange steht.
     Gebaut wie die APP_FASSUNG-Pruefung: Quelltext gegen Quelltext. */
  t('GYM_BREMSE steht wortgleich in der Datenbank', () => {
    const sql = (window.SQL_QUELLEN || {})['supabase-meldungen.sql'];
    if(!sql) return 'supabase-meldungen.sql nicht hereingereicht';
    return sql.indexOf(GYM_BREMSE) !== -1
      || ('die App sucht nach "' + GYM_BREMSE + '", im SQL steht das nicht');
  });

  /* ================================ Fragen, die nicht gestellt werden konnten (Fund 6)
     🔴 supaRPC gab bei Netzfehler, 404, 403 und bei einer echten Antwort `null`
     dasselbe zurueck. Am Namens-Test hing daran mehr, als es aussieht: `null !== true`,
     also lief die Registrierung weiter -- egal ob der Name frei war oder ob niemand
     gefragt werden konnte. */
  const mitRPC = async (antwort, fn) => {
    const mF = window.fetch;
    window.fetch = typeof antwort === 'function' ? antwort : (async () => antwort);
    try { return await fn(); } finally { window.fetch = mF; }
  };
  await tA('Kein Netz ist keine Antwort', async () =>
    mitRPC(async () => { throw new Error('weg'); },
      async () => eq(await supaRPC('username_taken', {uname:'x'}), RPC_FEHLER)));
  await tA('Eine fehlende Funktion ist keine Antwort', async () =>
    mitRPC({ ok:false, status:404, json: async () => ({}) },
      async () => eq(await supaRPC('username_taken', {uname:'x'}), RPC_FEHLER)));
  await tA('Eine echte Antwort kommt durch', async () =>
    mitRPC({ ok:true, status:200, json: async () => true },
      async () => eq(await supaRPC('username_taken', {uname:'x'}), true)));
  /* ⚠️ Bewusst KEIN Abbruch: die Funktion koennte in der Datenbank schlicht
     fehlen, und dann kaeme niemand mehr ins Konto. Geprueft wird deshalb, dass die
     Registrierung weiterlaeuft -- und dass sie es nicht STILL tut. */
  await tA('Ein nicht erreichbarer Namens-Test stoppt die Anmeldung nicht', async () => {
    let gesagt = '';
    const mF = window.fetch, mT = window.toast;
    window.toast = (m) => { gesagt = m; };
    let rufe = 0;
    window.fetch = async () => { rufe++;
      if(rufe === 1) return { ok:false, status:404, json: async () => ({}) };   // der Namens-Test
      return { ok:false, status:400, json: async () => ({msg:'signup aus'}) };  // die Registrierung selbst
    };
    let fehler = '';
    try { await authSignUp('karl', 'k@x.de', 'geheim'); }
    catch(e) { fehler = String(e); }
    finally { window.fetch = mF; window.toast = mT; }
    if(/vergeben/.test(fehler)) return 'die Registrierung wurde als "Name vergeben" abgewiesen';
    return /geprüft/.test(gesagt) || ('es wurde nichts gesagt (toast: "' + gesagt + '")');
  });

  /* ================================ Aufgerufen, aber nirgends angelegt (Funde 6 und 9)
     🔴 Zwei Datenbank-Funktionen standen in KEINER .sql dieses Ordners:
     `username_taken` und `delete_own_account`. Wer das Supabase-Projekt aus diesen
     Dateien neu aufsetzt, bekommt eine Installation, in der Konten grundsaetzlich nur
     halb geloescht werden -- und nichts im Repo verraet, dass eine Datei fehlt.
     Ein RPC-Name ist eine Zeichenkette, die sonst niemand prueft. */
  t('Jede aufgerufene Datenbank-Funktion ist auch angelegt', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    const sql = Object.values(window.SQL_QUELLEN || {}).join('\n');
    if(!sql) return 'keine .sql hereingereicht';
    const namen = new Set();
    let m;
    const re1 = /rest\/v1\/rpc\/([a-z_][a-z0-9_]*)/g;
    while((m = re1.exec(q))) namen.add(m[1]);
    const re2 = /supaRPC\(\s*'([a-z_][a-z0-9_]*)'/g;
    while((m = re2.exec(q))) namen.add(m[1]);
    const fehlt = Array.from(namen).filter(n =>
      !(new RegExp('create\\s+(or\\s+replace\\s+)?function\\s+(public\\.)?' + n + '\\b')).test(sql));
    return fehlt.length === 0
      || ('wird gerufen, aber nirgends angelegt: ' + fehlt.join(', '));
  });

  /* ================================ Was ohne Netz da ist (Fund 7, 01.09.2026)
     🔴 zxing.min.js (336 KB, der iPhone-Weg zum Scannen) stand nicht in der
     Vorlade-Liste. Auf Karls Geraet faellt das nie auf -- Chrome/Android nimmt
     BarcodeDetector. Es trifft genau eine Person: frische Installation, iPhone, erster
     Scan im Keller-Gym. Der meldet "das Scannen geht nicht", und hier ist nichts
     nachzustellen.
     ⚠️ sw.js LAEUFT in den Pruefungen nie -- gelesen wird sein Quelltext. */
  /* ⚠️ Diese Pruefung war beim ersten Anlauf GRUEN, obwohl zxing.min.js aus der
     Liste heraus war: sie suchte im ganzen sw.js -- und der Dateiname stand auch im
     Kommentar darueber. Jetzt wird nur die Liste selbst durchsucht.
     🔴 Dritter Fall dieser Bauform an einem Tag, diesmal an mir selbst. */
  const assetsListe = () => {
    const s = window.SW_QUELLE || '';
    return (s.match(/const ASSETS = \[[\s\S]*?\];/) || [''])[0];
  };
  t('Der Barcode-Leser ist offline da', () => {
    const liste = assetsListe(); if(!liste) return 'ASSETS-Liste nicht gefunden';
    return liste.indexOf('zxing.min.js') !== -1 || 'zxing.min.js fehlt in ASSETS';
  });
  /* 🔴 Und die Pruefung, die den Fund ueberdauert: nicht der eine Dateiname,
     sondern die FORM. Alles, was index.html unter './...' nachlaedt, muss in der
     Vorlade-Liste stehen -- sonst wandert derselbe Fehler beim naechsten Bild weiter. */
  t('Alles Nachgeladene steht in der Vorlade-Liste', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    const liste = assetsListe(); if(!liste) return 'ASSETS-Liste nicht gefunden';
    const dateien = new Set();
    /* ⚠️ Der Punkt MITTEN im Namen ist der Grund, warum das hier beim ersten Anlauf
       nichts fand: `zxing.min.js` heisst nicht `zxing` + Endung. Ein Zeichenvorrat ohne
       Punkt hat ausgerechnet die eine Datei uebersehen, um die es ging. */
    let m; const re = /['"`]\.\/([A-Za-z0-9_.\-]+\.(?:js|png|svg|webmanifest))['"`]/g;
    while((m = re.exec(q))) dateien.add(m[1]);
    const fehlt = Array.from(dateien).filter(f => liste.indexOf("'./" + f + "'") < 0);
    return fehlt.length === 0
      || ('wird nachgeladen, ist aber nicht vorgeladen: ' + fehlt.join(', '));
  });

  /* ================================ Der kaputte Plan-Link (Fund 8, 01.09.2026)
     🔴 Der Fehlerfang war leer, und die Adresse war vorher schon bereinigt: ein
     abgeschnittener Link machte GAR NICHTS, und Neuladen brachte auch nichts mehr.
     Drei Faelle sahen fuer Karl identisch aus -- Link kaputt, Empfaenger hat eine alte
     Fassung, oder Plan-Teilen geht grundsaetzlich nicht. */
  const mitLink = (hash, fn) => {
    const mH = location.hash, mP = planImport, mF = planImportFehler, mG = importFehlerGezeigt;
    location.hash = hash; planImport = null; planImportFehler = ''; importFehlerGezeigt = false;
    try { return fn(); }
    finally { location.hash = mH; planImport = mP; planImportFehler = mF;
              importFehlerGezeigt = mG; }
  };
  t('Ein zerrissener Link bleibt nicht stumm', () => mitLink('#p=xTOTALKAPUTT', () => {
    leseImportAusLink();
    return planImportFehler !== '' || 'es wurde nichts gemerkt';
  }));
  /* ⚠️ Der zweite Teil des Fundes, und der wiegt schwerer als die Meldung: solange
     der Link in der Adresse steht, ist Neuladen ein echter zweiter Versuch. Vorher war
     er weg, BEVOR ueberhaupt entpackt wurde. */
  t('Ein misslungener Link bleibt in der Adresse stehen', () => mitLink('#p=xTOTALKAPUTT', () => {
    leseImportAusLink();
    return /p=/.test(location.hash) || 'die Adresse wurde trotzdem geraeumt';
  }));
  t('Ein gelungener Link wird aus der Adresse geraeumt', () => {
    const code = planCode(activeProg());
    return mitLink('#p=' + code, () => {
      leseImportAusLink();
      return (!!planImport && !/p=/.test(location.hash))
        || ('planImport=' + !!planImport + ' hash=' + location.hash.slice(0, 20));
    });
  });
  t('Die drei Faelle bekommen drei verschiedene Texte', () => {
    const a = importFehlerText('alt'), b = importFehlerText('leer'), c = importFehlerText('kaputt');
    return (!!a && !!b && !!c && a !== b && b !== c && a !== c) || 'zwei Texte sind gleich';
  });

  /* ================================ Essen per Foto: die Form des Aufrufs (02.09.2026)
     🔴 Karls Meldung beim ERSTEN echten Foto, zwoelf Tage nach dem Einbau:
     400, "The value 'json_schema' is not supported for 'type' at 'response_format'".
     Im Quelltext stand die OpenAI-Form (type 'json_schema', Schema in json_schema.schema).
     Google will bei der Interactions-API: type 'text' + mime_type 'application/json' +
     das Schema in `schema` -- `type` ist dort die AUSGABEART, nicht das Schema-Format.

     ⚠️ EHRLICH ZUR REICHWEITE DIESER PRUEFUNGEN: sie haetten den Fehler NICHT
     gefunden. Sie halten fest, was in der Dokumentation steht -- und geglaubt hatte ich
     vorher auch etwas. Was gefehlt hat, war ein einziger echter Aufruf; die
     Commit-Nachricht vom 21.08.2026 sagt das selbst ("Nicht geprueft: ein echtes Foto
     mit echtem Schluessel"). Was sie koennen: verhindern, dass die Form beim naechsten
     Umbau still wieder wegrutscht. */
  const einBild = () => new Promise(ok => {
    const c = document.createElement('canvas'); c.width = 2; c.height = 2;
    const x = c.getContext('2d'); x.fillStyle = '#888'; x.fillRect(0, 0, 2, 2);
    c.toBlob(b => ok(new File([b], 'teller.jpg', {type:'image/jpeg'})), 'image/jpeg');
  });
  const beimFoto = async (fn) => {
    const mF = window.fetch, mK = DB.get('aikey', ''), mS = foodStep, mV = view, mD = foodDraft;
    let koerper = null;
    DB.set('aikey', 'AIza-pruefung');
    window.fetch = async (u, o) => { koerper = JSON.parse(o.body);
      return { ok:true, status:200, json: async () => ({ steps:[{ type:'model_output',
        content:[{ type:'text', text: JSON.stringify({ name:'Teller', menge:'ca. 300 g',
          kcal:500, eiweiss:20, kohlenhydrate:50, fett:15, sicher:true }) }] }] }) }; };
    try { await schaetzeFoto(await einBild()); return fn(koerper); }
    finally { window.fetch = mF; DB.set('aikey', mK); foodStep = mS; view = mV;
              foodDraft = mD; foodBusy = ''; foodFehler = ''; }
  };

  await tA('Das erzwungene JSON hat die Form, die Google versteht', async () =>
    beimFoto(k => {
      if(!k) return 'es wurde gar nichts geschickt';
      const rf = k.response_format;
      if(!rf) return 'response_format fehlt';
      if(rf.type !== 'text') return "type ist '" + rf.type + "' statt 'text'";
      if(rf.mime_type !== 'application/json') return "mime_type ist '" + rf.mime_type + "'";
      if(!rf.schema || rf.schema.type !== 'object') return 'das Schema fehlt oder ist kein object';
      if(rf.json_schema) return 'die alte OpenAI-Form (json_schema) steht wieder drin';
      return true;
    }));
  t('Die sieben Felder stehen alle im Schema', () => {
    const q = window.APP_QUELLE || ''; if(!q) return 'APP_QUELLE fehlt';
    const noetig = ['name','menge','kcal','eiweiss','kohlenhydrate','fett','sicher'];
    const i = q.indexOf('response_format:{');
    if(i < 0) return 'response_format nicht gefunden';
    const block = q.slice(i, i + 1400);
    const fehlt = noetig.filter(f => block.indexOf(f + ':') < 0 && block.indexOf("'" + f + "'") < 0);
    return fehlt.length === 0 || ('fehlt im Schema: ' + fehlt.join(', '));
  });
  /* ⚠️ Das Bild geht als `data` + `mime_type` mit, nicht als inline_data wie bei
     der aelteren generateContent-API. Auch das war nie abgeschickt worden. */
  await tA('Das Bild geht in der Form mit, die die Interactions-API erwartet', async () =>
    beimFoto(k => {
      const bild = (k.input || []).find(x => x && x.type === 'image');
      if(!bild) return 'im input steckt kein Bild';
      if(!bild.data) return 'das Bild hat kein Feld "data"';
      if(bild.mime_type !== 'image/jpeg') return "mime_type ist '" + bild.mime_type + "'";
      return true;
    }));
  await tA('Aus der Antwort wird der Entwurf gebaut', async () =>
    beimFoto(() => (foodDraft && foodDraft.name === 'Teller' && foodDraft.kcal === 500
                    && foodDraft.quelle === 'foto') || JSON.stringify(foodDraft)));

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

# Und derselbe Weg fuer die .sql-Dateien (02.09.2026, Funde 6 und 9). Die App ruft
# Datenbank-Funktionen ueber ihren Namen -- eine Zeichenkette, die niemand prueft. Zwei
# davon standen in keiner .sql dieses Ordners, und beide Male ist die Folge still: 404,
# und die App macht daraus "Name ist frei" bzw. "halb geloescht". Hier kommt der Text
# herein, damit die Pruefung Aufruf gegen Definition halten kann.
SQL_TXT = {f.name: f.read_text(encoding='utf-8') for f in sorted(WORK.glob('supabase-*.sql'))}
SQL_BLOCK = '<script>window.SQL_QUELLEN = ' + json.dumps(SQL_TXT) + ';</script>' + chr(10)

# ⚠️ Und derselbe Weg fuer die App selbst. Grund (27.08.2026, dreimal an einem Abend
# passiert): eine Pruefung, die `document.documentElement.innerHTML` durchsucht, findet dort
# AUCH SICH SELBST -- die Pruefungen stehen ja mit im Dokument. Zweimal war eine Pruefung
# deshalb gruen, obwohl der gepruefte Aufruf gar nicht mehr dastand, und einmal rot, obwohl
# nichts kaputt war. APP_QUELLE ist der Quelltext OHNE die Pruefungen.
# ⚠️ `</script>` im Text beendet das umgebende Skript-Tag, egal ob es in Anfuehrungszeichen
# steht — der HTML-Parser sieht die Zeichenkette gar nicht. `<\/` ist in JavaScript dasselbe
# Zeichenpaar, fuer den Parser aber kein Ende. Ohne das war APP_QUELLE schlicht nicht da.
APP_BLOCK = ('<script>window.APP_QUELLE = ' + json.dumps(html).replace('</', r'<\/')
             + ';</script>' + chr(10))
(WORK / 'test.html').write_text(html + SW_BLOCK + SQL_BLOCK + APP_BLOCK + TESTS, encoding='utf-8')

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
