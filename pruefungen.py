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
import subprocess, re, pathlib, shutil, sys, os

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
(function(){
  const out = [];
  let ok = 0, bad = 0;
  const t = (name, fn) => {
    try { const r = fn(); if (r === true) { ok++; out.push('OK   ' + name); }
          else { bad++; out.push('FAIL ' + name + '  -> ' + r); } }
    catch (e) { bad++; out.push('ERR  ' + name + '  -> ' + e.message); }
  };
  const eq = (a, b) => a === b ? true : (JSON.stringify(a) + ' != ' + JSON.stringify(b));

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
(WORK / 'test.html').write_text(html + TESTS, encoding='utf-8')

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
