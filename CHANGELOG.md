# Änderungen

Neueste zuerst. Jede Zeile nennt den Commit, damit man zurückfindet.

## 2026-08-23

### 🔧 Nachbesserung am selben Tag: schwarze Ränder und ein zu kurzer Ladescreen

**Karls Ansage:** *„selbes Problem wie bei der Angel-App, der Ladescreen ist zu kurz und man
[sieht] schwarze Ränder beim App Icon."*

**1. Die schwarzen Ränder.** Mein erster Zuschnitt hatte den schwarzen Grund der Bildmontage
mitgenommen — auf dem Homescreen wurde daraus ein dunkler Rahmen um das Icon.
⚠️ **Ein Versuch, das per Flächenfüllung zu lösen, ist gescheitert und wurde zurückgenommen:**
Brocks Hörner, die Hantel und der Schriftzug-Kasten hängen alle am selben dunklen Bereich wie
der Rahmen — die Füllung fraß sie mit. Jetzt wird stattdessen **der türkise Körper gemessen**
(x 48–504, y 417–891 im Original) und **hinter die dunkle Kontur gezoomt**. Ergebnis: randlos,
Motiv vollständig.

**2. Der Ladescreen.** Er hatte nur eine Obergrenze (5 s), aber **keine Mindestdauer** — die
Oberfläche steht nach wenigen Millisekunden, also war er weg, bevor man ihn gesehen hatte.
Jetzt **`SPLASH_MINDESTENS = 1800`**, gezählt **ab dem Öffnen der Seite**, nicht ab dem
Fertigwerden — sonst käme die Wartezeit oben drauf und ein langsames Gerät würde doppelt
bestraft. Genau die Lösung, die [[angel-log]] seit dem 08.08. hat.

⚠️ **Zwei bestehende Prüfungen wurden dadurch rot** — sie erwarteten, dass der Schirm sofort
weggeht. Genau dafür ist der Rahmen da. Sie bilden jetzt die neue Absicht ab, und eine
**Gegenprobe** ist dazugekommen: läuft die Mindestzeit noch, muss er stehen bleiben. Ohne die
würde ein späteres „sofort weg" niemandem auffallen.

**Prüfungen: 357 → 360.**

### 🖼️ App-Icon und Ladebildschirm nach Karls Entwurf

Karl hat den Entwurf am 23.08. in Discord abgelegt: Brock mit Hantel als Icon, dazu ein
Ladebildschirm mit Wortmarke, Untertitel und Ladebalken.

⚠️ **Ein Fehler, der dabei aufgefallen ist:** die Icons standen im Manifest auf
`"purpose": "any maskable"`. **Maskable beschneidet rund** — Karls „gym-log"-Schriftzug sitzt
aber unten am Rand und wäre auf Android abgeschnitten worden. Jetzt getrennt:
- `icon-192/512.png` — Karls Entwurf 1:1, `purpose: any`
- `icon-maskable-192/512.png` — Inhalt auf 80 %, drumherum der Türkiston aus dem Icon selbst
  (`#1bb9bc`, aus dem Bild gemessen statt geraten)

⚠️ **`icon.svg` ist raus** — es zeigte noch das alte Motiv. Solange es im `<link rel="icon">`
stand, hätte der Browser-Tab ein anderes Bild gezeigt als der Homescreen.

**Ladebildschirm** in Karls Reihenfolge: Wortmarke (`gym` weiß, `-log` grün) → „Dein Training.
Dein Fortschritt." → Brock im getragenen Rang → „Wird geladen…" → Balken. Die zwei Farben
stehen als HTML da, nicht als Bild — der Ladebildschirm ist genau dann sichtbar, wenn noch
nichts geladen ist.

`sw.js` auf **gymlog-v22**, sonst behalten die Handys die alten Symbole.

### 🔥 Die Flamme: eine Serie fürs Mitschreiben

**Karls Ansage:** *„Flammen beim kalorientracken streak"*.

💡 **Sie zählt Tage, die Trainings-Serie zählt Wochen — das ist Absicht.** Beim Training
gehören Ruhetage zum Plan, eine Tagesserie würde dort etwas bestrafen, das richtig ist. Beim
Essen gibt es keinen Ruhetag: jeder Tag ist mitgeschrieben oder nicht.

⚠️ **Der heutige Tag zählt nur mit, wenn schon etwas drinsteht** — sonst stünde die Serie
jeden Morgen auf 0, obwohl nichts versäumt ist. Dieselbe Falle wie bei der Wochenserie.

⚠️ **Bei 0 wird sie grau statt versteckt.** Eine Anzeige, die erst ab Tag 1 auftaucht, erklärt
sich nie — man sähe sie zum ersten Mal, wenn man sie schon hat.

Der Rekord wird **gerechnet, nicht gespeichert**: ein gespeicherter Wert wäre nach dem Löschen
eines Eintrags falsch und nie wieder richtigzustellen. Er steht nur daneben, wenn er größer als
die laufende Serie ist.

⚠️ **Fasst XP nicht an** — die Entscheidung vom 22.08. gilt: kein XP fürs Essen, sonst
entwertet es den Rang, der Training misst. Die Flamme ist eine Anzeige, keine Währung.

**Prüfungen: 346 → 357.** Elf neue, darunter der Morgen-Fall und die Unterscheidung
„gestern zuletzt" (Serie läuft) gegen „vorgestern zuletzt" (gerissen).

### 🗄️ Bug-Report, Teil 1: das Datenbank-Gerüst (`supabase-meldungen.sql`)

**Karls Entscheidung vom 22.08.2026:** *„alles wie bei Angel-Log“* — Formular, Postfach,
Antworten aus Discord zurück in die App, Push. **Gleicher Kanal wie Angel-Log, eigene
Überschrift** (`🏋 Gym-Log — Meldung #N` statt `🐞 Angel-Log — ...`), weil beide in
denselben Kanal schreiben.

⚠️ **Ein Unterschied zu Angel-Log, der auffiel:** Gym-Log hat **keine Profil-Tabelle und keine
Benutzernamen** — es gibt nur `gymlog_data`. Als Kennung des Melders bleibt deshalb die
**E-Mail aus `auth.users`**; die Zustell-Funktion ist nur dafür `security definer`.

**Mit übernommen, weil bei Angel-Log teuer gelernt:**
- **Bremse als Mengengrenze** (5 je 10 Min/Konto), nicht als 60-Sekunden-Abstand — sonst
  verschwindet ein Nachzügler-Stapel ohne Netz **für immer**.
- **`allowed_mentions.parse: []`** — in den Meldetext schreibt ein Fremder; ohne das pingt
  jeder mit `@everyone` den ganzen Server.
- **`Content-Type` ohne Zeichensatz** — sonst wirft pg_net, der Trigger fällt, und die Meldung
  landet nicht einmal in der Tabelle.
- **Gelesen-Vermerk als Funktion**, nicht als UPDATE-Policy — RLS kann Zeilen einschränken,
  aber keine einzelnen Spalten.

⚠️ **Noch nicht fertig:** App-Seite und die zwei Bot-Dateien (`gym_antworten.py`, `gym_push.py`)
fehlen. Und in `gym_konfig` müssen Webhook + Ping-ID von Hand eingetragen werden — ohne sie
kommt nichts an.

## 2026-08-22

### ✨ Schritte aus der Health-App — über Kurzbefehle

**Karls Ansage vom 22.08.2026:** *„soll mit der health app verbunden werden können um schritte
zutracken und die einrechnet."*

⚠️ **Gym-Log kann Apple Health nicht selbst lesen.** HealthKit ist Apps aus dem App Store
vorbehalten; Safari stellt keine Schnittstelle bereit, und einen Web-Standard für Schrittzähler
gibt es überhaupt nicht. Der Weg läuft deshalb über die **Kurzbefehle-App**: die darf Health
lesen und ruft Gym-Log mit `?schritte=8432` auf. Die vierschrittige Anleitung samt kopierbarer
Adresse steht direkt in den Einstellungen — nicht in einer Hilfe, die niemand aufmacht.

**Die Verrechnung — Karls Entscheidung:** Grundumsatz runter auf **Körpergewicht × 26**, dafür
zählt jeder Schritt.

⚠️ **Warum das nötig war:** der übliche Faktor **× 30 enthält Alltagsbewegung bereits**. Wer die
Schritte obendrauf rechnet, zählt dieselbe Bewegung zweimal und darf zu viel essen — bei 80 kg
und 10.000 Schritten rund 300 kcal zu Unrecht. Das Tagesziel wird dadurch an ruhigen Tagen
**kleiner als vorher**, an aktiven größer. Ein- und Ausschalten rechnet das Grundziel jedes Mal
neu; ohne das stünde das alte, zu hohe Ziel da *und* die Schritte kämen dazu.

- **kcal je Schritt:** Gehen kostet rund 0,5 kcal je kg und km, ein km sind rund 1250 Schritte
  → **0,0004 kcal je Schritt und kg**. Eine Faustregel, keine Physik — deshalb wird gerundet und
  nirgends mit Nachkommastellen ausgewiesen.
- ⚠️ **Ein Eintrag pro Tag, überschreiben statt addieren.** Der Kurzbefehl schickt den
  **Tagesstand**, nicht die Schritte seit dem letzten Mal. Wer hier addiert, hat nach drei
  Automatik-Läufen das Dreifache stehen.
- ⚠️ **Die Adresse wird nach dem Lesen bereinigt.** Sonst stünde die Zahl in der Adresszeile und
  jedes Neuladen — auch ein versehentliches am nächsten Tag — schriebe sie erneut ein.
- ⚠️ **Ohne eingetragenes Gewicht gibt es 0 kcal aus Schritten**, keine geratene Zahl. Die App
  würde sonst zum Mehressen einladen.
- ⚠️ **Ein Link bei ausgeschaltetem Modus schreibt nichts**, sondern sagt, wo man ihn anschaltet.
- **Der Wochenschnitt vergleicht mit dem Durchschnitt der Tagesziele**, nicht mit dem Grundziel —
  im Schritt-Modus hat jeder Tag ein eigenes.
- Die Adresse baut sich aus dem Standort statt fest verdrahtet zu sein: die App läuft auf GitHub
  Pages, kann aber auch woanders liegen.

**13 neue Prüfungen, 346 gesamt.** Dazu ein echter Durchlauf im Browser mit `?schritte=8432`,
`?schritte=8432&x=1`, `?schritte=abc` und `?schritte=999999` — Zahl übernommen, fremde Parameter
erhalten, Unsinn abgewiesen.

### ✨ Ladebildschirm mit Brock

**Karls Ansage vom 22.08.2026:** *„Ich brauche einen lade screen mit brock drauf."*

Brock in seinem **getragenen Rang** — der Schirm zeigt deinen Stand, nicht immer den
Anfänger-Brock. Dazu der Name und ein laufender Balken. Wer „Bewegung reduzieren" gesetzt hat,
bekommt einen ruhigen Schirm statt eines hüpfenden Monsters.

⚠️ **Die harte Zeitgrenze steht im Kopf der Datei, nicht in der Startroutine.** Der Schirm liegt
über der ganzen App — bliebe er stehen, wäre sie gesperrt, und zwar unbedienbar, nicht nur
hässlich. Der Wecker greift deshalb auch dann, wenn das Skript weiter unten gar nicht erst
durchläuft (Syntaxfehler, abgebrochener Download, kaputter Datenbestand). Genau das ist in
Angel-Log schon einmal passiert.

⚠️ **Weggenommen wird nach dem ersten `render()`, nicht nach dem Abgleich.** Der kann ohne Netz
ewig dauern, und die App ist vorher vollständig bedienbar.

💡 **Gegen den Farbblitz:** ein Abbild aus vier Farben und dem Bildnamen liegt im Gerät. Das
Kopf-Skript läuft, bevor es Paletten oder Ränge gibt — es kann sich nichts herleiten, nur
fertige Werte lesen. Ohne das säßen Träger einer hellen Palette eine Zehntelsekunde vor einem
dunkelgrauen Schirm. Ein kaputter Eintrag kostet nichts: dann sieht der Schirm nur schlichter aus.

**Neun Prüfungen** halten es fest — die wichtigste ist, dass der Schirm nach dem Start
tatsächlich wieder weg ist. **333 gesamt.**

### ✨ Ernährungs-Assistent beim ersten Öffnen

**Karls Ansage vom 22.08.2026:** *„Ich will das wenn man darauf klickt wird beim aller ersten
mal auch eine einstellung/tutorial gemacht. dh wielange will man drannbleiben und was ist das
ziel etc."*

Der Trainings-Teil führt seit jeher durch die Einrichtung, der Ernährungs-Teil fing als leerer
Ring an. Jetzt fünf Schritte: **Vorhaben → Gewicht → Zeitraum → Zusammenfassung.**

- **Der Zeitraum ist neu und kein Beiwerk.** 4, 8, 12, 16 Wochen oder ohne festes Ende. Daraus
  entstehen ein Zieldatum und eine Prognose (*„Wenn es so läuft, stehst du am 14.11. bei rund
  74,0 kg"*) — beides gab es vorher nicht.
- **In der Ansicht steht danach „Woche 3 von 12"** mit Balken. ⚠️ Nach Ablauf bleibt die
  Anzeige stehen, statt auf „Woche 15 von 12" weiterzulaufen.
- ⚠️ **Die Prognose kommt aus dem Vorhaben, nicht aus dem Verlauf** — sie ist die Ansage. Was
  tatsächlich passiert, sagt eine Karte weiter unten der Regelkreis. Zwei verschiedene Fragen,
  zwei getrennte Karten.
- **Das Gewicht aus dem Assistenten landet in der normalen Gewichtskurve**, nicht in einer
  zweiten Ablage daneben.
- ⚠️ **Bestandskonten werden nicht überfallen:** wer schon ein Tagesziel gesetzt hat, bekommt
  den Assistenten nicht nachträglich vorgesetzt. Für die gibt es **„Vorhaben ändern"**.
- **„Überspringen"** merkt sich das — sonst käme der Assistent beim nächsten Öffnen wieder und
  *„ich stell das selbst ein"* wäre eine Lüge.

### 💄 Brock steht jetzt links neben dem Kalorien-Ring

**Karls Ansage:** *„brock kann gerne links neben den kalorin kreis."*

Er saß in einer eigenen Karte darüber. Jetzt Figur und Ring nebeneinander, die Sprechblase
darunter. ⚠️ **Nicht** alle drei nebeneinander: Figur (72) + Ring (130) + Text wären auf einem
Telefon drei Spalten in ~340 px — der Text bräche dann nach jedem Wort um.

### 🐛 „Fr., 30.10.." — doppelter Punkt hinter dem Zieldatum

`fmtDate()` endet selbst auf einen Punkt. Der Satzpunkt dahinter ergab zwei.
💡 **Beim ersten Vorschaubild aufgefallen, nicht im Code-Lesen** — eine Prüfung hält es fest.

### ✅ 324 Prüfungen (vorher 305)

19 neue für den Assistenten. Zwei davon waren erst falsch und mussten korrigiert werden, nicht
die App: Schritt 1 sperrt „Weiter" absichtlich, solange kein Vorhaben gewählt ist — und ein
`type="number"`-Feld nimmt kein Komma an, der Wert wäre danach leer, ohne dass die App etwas
falsch macht.

Zwei bestehende Prüfungen mussten mitgezogen werden: die eine suchte die alte `.mascot`-Hülle,
die andere lief ohne `setup` und wurde jetzt zu Recht vom Assistenten abgefangen.

### ✨ Der Ernährungs-Teil weiß jetzt, was du wiegst

**Der rote Faden hinter allem Folgenden:** die App führt eine Gewichtskurve *und* ein
Essensprotokoll — und hat beide nie miteinander reden lassen. Der Kalorien-Teil kannte das
Körpergewicht nicht, obwohl es zwei Bildschirme weiter lag.

- **Brock kommentiert den Tag.** Er stand bisher nur auf der Startseite und redete
  ausschließlich über Training. Jetzt sieben Zustände: nichts eingetragen, kein Ziel gesetzt,
  gut unterwegs, Punktlandung, drüber, weit drüber, Ruhetag. Sprüche bleiben über den Tag
  stabil, wie beim Training.
- **Eiweiß bekommt ein echtes Ziel:** 1,8 g je kg Körpergewicht, mit Balken in derselben
  Bildsprache wie der Ring. ⚠️ **Ohne eingetragenes Gewicht steht dort ein Hinweis, keine
  geratene Zahl.**
- **An Trainingstagen 2,0 g statt 1,8 g.** `istTrainingstag()` fragt den Plan *und* ob heute
  schon trainiert wurde — ein spontanes Training zählt also mit.
- **Das Kalorienziel schlägt sich selbst vor.** Die Faustregel kg × 30 stand bisher als
  **Text im Eingabefenster**, den der Nutzer selbst anwenden sollte. Jetzt rechnet die App und
  bietet einen Knopf.
- **Wochenschnitt statt nur „heute".** Ein einzelner Tag sagt fast nichts.
  ⚠️ **Gerechnet wird nur über Tage MIT Eintrag.** Tage ohne Eintrag als 0 kcal zu zählen
  würde aus „nicht protokolliert" ein „nichts gegessen" machen — der häufigste Rechenfehler
  in solchen Apps.
- **„Nochmal"** — die sechs zuletzt gegessenen Sachen, jede nur einmal, direkt antippbar.
  💡 Essensprotokolle sterben nicht an Faulheit, sondern daran, dass man dasselbe Frühstück
  jeden Tag neu zusammensucht.

### ✨ Regelkreis: die Waage korrigiert das Kalorienziel

> *„In 14 Tagen 0,7 kg runter bei Ø 2.100 kcal. Für 0,5 kg pro Woche wären es eher 1.950."*

Beide Kurven lagen längst in der App. Es braucht keinen Server, keine KI, nur Arithmetik über
zwei vorhandene Reihen — **und kein bezahltes Abo kann es besser.**

Dazu neu: **abnehmen / halten / zunehmen** als ausdrückliche Angabe (`zielArt`). Danach richtet
sich der Zielversatz (−400 / 0 / +300 kcal) und die erwartete Änderung je Woche.

⚠️ **Der Regelkreis hält den Mund, wenn die Grundlage fehlt** — unter zwei Wiegungen, unter
sieben Tagen Spanne oder ohne gesetztes Ziel sagt er nichts, statt aus zwei Punkten einen Trend
zu erfinden. Das neue Ziel wird nie unter 1.200 kcal vorgeschlagen.

### ✨ Serie, Rekord-Meldung, Jahresraster

- **Wochenserie** — Wochen am Stück mit mindestens einem Training.
  ⚠️ Die **laufende** Woche zählt nur mit, wenn schon trainiert wurde; sonst würde die Serie
  jeden Montag um 0 Uhr scheinbar reißen.
- **Rekord sofort sichtbar:** ein neuer Bestwert meldet sich beim Abhaken des Satzes, nicht
  erst in der Auswertung.
- **Jahresraster** — 53×7 Felder über das Trainingsjahr.
  💡 Die Schwellen kommen aus **den eigenen Quantilen**, nicht aus festen Zahlen: ein
  Anfänger-Jahr und ein Fortgeschrittenen-Jahr sehen dadurch beide nach etwas aus.

### 🐛 Barcode: Sackgasse und verlorene Nummer

Stand ein Produkt nicht in Open Food Facts, kam eine Fehlermeldung — und sonst nichts.
Jetzt führt der Weg direkt ins Selbst-Anlegen, **und die gescannte Nummer wird mitgespeichert**
(`food:merken` und `food:newsave` haben sie vorher fallen lassen). Beim nächsten Scan findet
`eigenesZuBarcode()` die Packung in der **eigenen** Liste, ohne Netz.

💡 Zur Größenordnung: 422.265 Produkte mit Deutschland-Kennzeichnung, davon **246.807 mit
vollständigen Nährwerten**. Der Fall tritt also regelmäßig ein.

### ✅ 305 Prüfungen statt 160

Der Trainings-Teil wurde systematisch abgeklopft. **Zweimal lag die Prüfung falsch, nicht die
App** — beide Male habe ich die Prüfung korrigiert und den Grund hineingeschrieben:
`nextTrainingDay()` darf auf heute zeigen (wer nur montags trainiert …), und `planWarm(null)`
gibt richtigerweise die Profil-Einstellung zurück, nicht `false`.

⚠️ **Festgehaltene Lücke:** Einheiten von vor dem 06.08.2026 haben kein `xp`-Feld. Wird so
eine im Verlauf geändert, lässt `sessRecalc()` den Punktestand stehen. Eine Prüfung hält das
fest, damit es nicht als Fehler durchgeht, wenn es später jemandem auffällt.

### 🚫 Bewusst **nicht** gebaut: XP fürs Essen

Naheliegend — und es würde das System kaputtmachen. **XP misst zurzeit Training.** Wer
Protokollieren belohnt, bläht Level und Rang mit etwas auf, das keine Anstrengung ist, und
Brocks Rang hört auf, über das Training etwas auszusagen. Die Serie läuft deshalb **ohne XP**.

⚠️ Ebenfalls draußen geblieben: der **Schlüssel im Konto-Abgleich**. Halb gebaut, aber vier
Texte — darunter die Datenschutzerklärung — sagen weiter, er bleibe auf dem Gerät. Entweder
ganz oder gar nicht; steht offen.

### 🐛 Neues Konto: drei Trainings ohne Wochentag — „Ruhetag" für immer

`seedPlans()` legt für ein frisches Konto Push/Pull/Beine an — **ohne `day`**. Damit fand
`planForToday()` nie etwas, und die Startseite meldete **jeden einzelnen Tag**
*„Ruhetag · Noch keine Trainingstage festgelegt"*, obwohl drei fertige Trainings in der App
lagen.

Betroffen war, wer im Assistenten **„Selbst anlegen"** wählt — der Weg baut selbst keine Pläne
und lässt den Startbestand stehen. Wer den Assistenten durchklickt, bekommt seine Tage über
`buildPlans()` und hat den Fehler nie gesehen.

Jetzt **Mo / Mi / Fr**, der klassische 3er-Rhythmus. Im Editor jederzeit verschiebbar —
entscheidend ist, dass sie überhaupt einen Tag haben.

💡 **Gefunden beim systematischen Abklopfen des Trainings-Teils**, nicht durch eine Meldung.
Fünf neue Prüfungen halten es fest (160 gesamt).

### 🔧 Gym-Log hat einen Prüfrahmen — 154 Prüfungen, vorher null

`pruefungen.py`, gleicher Aufbau wie in angel-log: die echte `index.html` wird in Chrome
headless geladen, die Prüfungen unten angehängt, das Ergebnis aus dem DOM gelesen. Aufruf:
`python pruefungen.py`.

**Warum das nötig war:** Angel-Log hatte 700 Prüfungen, Gym-Log **null**. Die sechs Fehler vom
05.08.2026 sind ausnahmslos erst beim Benutzen aufgefallen. Die Prüfungen sind deshalb entlang
genau dieser Fehler gebaut — Pausen-Uhr, Gewichtsdatum, Übungsbild, Trainingstag — und nicht
entlang dessen, was sich leicht prüfen lässt.

⚠️ **Der erste Lauf hat sofort zwei echte Fehler gefunden.** Beide unten, beide behoben.

### 🐛 Klimmzüge und Überzüge bekamen das falsche Übungsbild

**Umlaut-Falle:** „Klimmzüge" enthält nicht die Zeichenfolge „klimmzug", „Überzüge" nicht
„überzug". `guessMove()` fiel deshalb durch bis zur neutralen Hantel.

💡 **Warum es nie auffiel:** bei den hinterlegten Übungen greift `EXMOVE` zuerst. Getroffen hat
es nur **selbst angelegte** Übungen mit diesen Namen. Jetzt `klimmz[uü]g` bzw. `überz[uü]g`.

### 🐛 Aufwärmgewicht konnte schwerer sein als der Arbeitssatz

Das Aufwärmgewicht sind 70 % des Arbeitsgewichts, **auf 2,5 kg gerundet** — und dieses Runden
geht auch nach oben. Bei **2 kg** Arbeitsgewicht kamen so **2,5 kg** Aufwärmgewicht heraus.

Betrifft leichte Übungen wie Seitheben, also genau die, die man mit 2–3 kg anfängt. Ergibt sich
kein Wert unter dem Arbeitsgewicht, bleibt das Feld jetzt leer, statt etwas Falsches
vorzuschlagen.

### 🔑 Schlüssel eintragen: echter Dialog statt `prompt()`

**Karls Ansage:** *„Wenn du auf schlüssel eintragen klickst muss es eine möglichkeit geben die
seite direkt aufzurufen und falls es nicht klappt ein hilfe button wo es erklärt wird."*

- **„Schlüssel-Seite öffnen"** als richtiger Knopf — vorher stand die Adresse nur als Text in
  einem `prompt()` und war nicht anklickbar.
- **Hilfe-Knopf**, der **vier** Ursachen der Reihe nach durchgeht: nicht angemeldet,
  Geburtsdatum am Google-Konto nicht hinterlegt (Google verlangt 18+ **und** die Bestätigung),
  mehrere Google-Konten gleichzeitig, VPN im falschen Land. Dazu der Hinweis, dass ein Schlüssel
  mit `AIza` anfängt und ein alter `sk-ant-…` nicht mehr funktioniert.
- ⚠️ **Die vierte Ursache kam nachträglich dazu** — bei Karl waren Anmeldung, Alter und Land
  alle in Ordnung, und Google wies ihn trotzdem ab. Die Hilfe hatte also nach einer Stunde schon
  eine bekannte Lücke; ein Schul- oder Arbeitskonto in derselben Sitzung ist die wahrscheinlichste
  verbleibende Erklärung.
- 💡 **Der Anlass war echt:** Google hat Karl am 22.08.2026 auf „Available regions" geworfen,
  obwohl Deutschland dort auf der Liste steht.
- ⚠️ `fragKey()` gibt jetzt ein **Promise** zurück. Beide Aufrufer sind mitgezogen — ohne
  `await` wäre das Foto sonst ohne Schlüssel losgeschickt worden.

## 2026-08-21

### Essen per Foto läuft jetzt über Google statt über Anthropic

**Karls Entscheidung.** Der Engpass war nie das Modell, sondern der Schlüssel: für Anthropic
braucht es ein Konto **mit Kreditkarte und Guthaben**. Für Google reicht ein **Google-Konto** —
die Gratis-Stufe verlangt kein Rechnungskonto (an der Quelle nachgesehen, nicht angenommen).
Damit ist die Foto-Schätzung für Freunde erreichbar, ohne dass jemand eine Kreditkarte hinterlegt.

- **Modell:** `gemini-3.7-flash` über die **Interactions-API**
  (`generativelanguage.googleapis.com/v1beta/interactions`), nicht das ältere `generateContent`.
- **Das erzwungene JSON-Format bleibt** — dieselben sieben Felder wie vorher, nur als
  `response_format`/`json_schema` statt als `output_config`. An der Anzeige ändert sich nichts.
- ⚠️ **Die Antwort wird anders ausgelesen.** Google liefert eine `steps`-Liste, in der **vor**
  der Antwort Denk-Schritte stehen können. Der Code sucht deshalb den Schritt `model_output`,
  statt `steps[0]` zu nehmen.
- **Ein alter `sk-ant-…`-Schlüssel wird erkannt** und beim ersten Foto gegen einen neuen
  getauscht — mit einem Satz, der sagt warum. Ohne das käme nur ein unverständliches 400.
- **Ein Fehler weniger geraten:** Google meldet einen falschen Schlüssel als **400**, nicht als
  401. Gemessen, nicht vermutet — die App fängt beides ab und sagt in beiden Fällen dasselbe.
- 🟢 **Der Aufruf aus dem Browser ist erlaubt.** Nachgemessen: die CORS-Vorabfrage antwortet mit
  `Access-Control-Allow-Origin` für genau diese Seite und lässt `x-goog-api-key` zu. Der
  Sonderheader, den Anthropic dafür verlangte, entfällt.

⚠️ **Die Datenschutz-Seite ist mitgeändert:** beim Foto steht jetzt **Google LLC, USA** statt
Anthropic. Dass die Bilder die EU verlassen, gilt unverändert — nur der Empfänger ist ein anderer.

🔴 **Was hier NICHT geprüft ist: ein echtes Foto mit einem echten Schlüssel.** Getestet wurde die
Form der Anfrage (Google beanstandet nur den Schlüssel, kein Feld) und dass die App fehlerfrei
lädt. Ob die Schätzung gut ist, zeigt erst der erste Teller.


### Der Barcode geht jetzt über die Kamera — auch auf dem iPhone

Beim Antippen von „Barcode" kam bisher auf dem iPhone ein Eingabefeld: *Nummer unter dem Barcode
eintippen*. Das war kein Fehler, sondern eine eingebaute Notlösung — **Safari kennt
`BarcodeDetector` nicht**, und die App hatte für diesen Fall nur das Tippen übrig. Aufgefallen
beim ersten echten Durchlauf des Kalorien-Teils.

Jetzt geht die Kamera auf, in drei Stufen:

1. **`BarcodeDetector`** (Chrome/Android) — unverändert, schnell, lädt nichts nach.
2. **ZXing im Browser** (`zxing.min.js`, 330 KB, liegt im Repo statt bei einem CDN) — für Safari
   und alles andere ohne `BarcodeDetector`. **Wird erst geladen, wenn wirklich gescannt wird**,
   nicht beim Start der App. Erkannt werden nur EAN-8/13 und UPC-A/E; das macht das Lesen schneller.
3. **Nummer eintippen** — nur noch, wenn gar keine Kamera da ist oder sie verweigert wird. Dazu
   steht im Scan-Fenster jetzt ein Knopf *„Nummer stattdessen eintippen"*, damit der Weg
   erreichbar bleibt, ohne dass erst etwas scheitern muss.

⚠️ **Die Bibliothek liegt bewusst im Repo, nicht bei einem CDN.** Die Datenschutz-Seite zählt jeden
Weg nach außen einzeln auf; ein CDN wäre ein neuer gewesen, für den niemand den Knopf gedrückt hat.
Was hinausgeht, bleibt unverändert: **nur die Barcode-Nummer, an Open Food Facts.**

- Cache-Version `gymlog-v15` → `gymlog-v16`.
- `zxing.min.js` steht **nicht** im Vorab-Cache: wer nie scannt, lädt es nie — und ein Barcode ohne
  Netz nützt ohnehin nichts, weil die Nährwerte nachgeschlagen werden müssen.

## 2026-08-06

### Kalorien zählen — der Anfang vom Ernährungs-Teil

Der Tab „Kalorien" (früher „Körper") hat jetzt einen Ernährungs-Teil. Das Gewicht steht unverändert
darunter.

- **Tagesziel und Ring.** Oben ein Ring mit „gegessen von Ziel", darunter Eiweiß, Kohlenhydrate und
  Fett des Tages. Über dem Ring setzt man das Ziel; ohne Ziel bleibt er leer.
- **Drei Wege, etwas einzutragen** — alle enden an derselben Stelle: Menge eintippen, fertig.
  1. **Eigene Lebensmittel.** Einmal Name und Nährwerte je 100 g eintragen, danach steht es in der
     Liste und ist mit zwei Tipps eingetragen.
  2. **Barcode.** Der Strichcode wird bei **Open Food Facts** nachgeschlagen (offene Datenbank,
     kostenlos, kennt deutsche Produkte gut). Wo der Browser Barcodes lesen kann, geht die Kamera
     auf — sonst tippt man die Ziffern ein (auf dem iPhone gibt es die Kamera-Erkennung nicht).
     Ein gefundenes Produkt lässt sich in die eigene Liste übernehmen.
  3. **Foto (KI).** Ein Bild vom Teller wird an Claude geschickt und geschätzt: Name, Portion,
     kcal und Makros. Das Ergebnis ist eine **Schätzung** und wird als solche gekennzeichnet, wenn
     das Bild schlecht zu erkennen war.
     Dafür läuft **Haiku** statt Opus (Karls Ansage) — ein Fünftel des Preises, **unter einem halben
     Cent pro Foto**. Die Unschärfe steckt hier im Bild, nicht im Denken.
     ⚠️ Dabei musste der `effort`-Regler raus: den gibt es erst ab Opus/Sonnet, bei Haiku wird der
     Aufruf damit abgelehnt. Eine Prüfung fängt den Aufruf jetzt ab und sieht nach, dass Modell,
     Format, Bild und Header stimmen — ohne echtes Geld auszugeben.
     ⚠️ **Dafür braucht es einen eigenen API-Schlüssel** (Einstellungen › Essen per Foto). Er liegt
     **nur auf dem Gerät** — nicht im Quelltext (das Repo ist öffentlich), nicht in der Cloud, nicht
     im heruntergeladenen Backup. Jedes Foto kostet ein paar Cent über das eigene Konto.
     Das Bild wird vor dem Senden verkleinert, sonst kostet ein Handyfoto ein Vielfaches.
- **Eingetragene Mahlzeiten speichern die ausgerechneten Werte**, nicht einen Verweis aufs
  Lebensmittel — ein später geändertes Lebensmittel schreibt die Vergangenheit damit nicht um.
- **Datenschutz-Seite ergänzt.** Die zwei neuen Wege nach außen stehen jetzt drin, samt der
  ehrlichen Einschränkung: ein Essens-Foto verlässt die EU. Zwei Sätze, die vorher pauschal
  „keine Weitergabe an Dritte" und „deine Daten verlassen die EU nicht" sagten, sind entsprechend
  präzisiert.
- ⚠️ **Nebenbei behoben, war schon vorher kaputt:** unter „Alle Trainingspläne" ragte die Knopfreihe
  (Auswählen · Bearbeiten · Löschen) bei 320 px **26 Pixel aus dem Bild**. Flex-Elemente schrumpfen
  von sich aus nicht unter ihre Textbreite; jetzt bricht der letzte Knopf notfalls um. Das gilt für
  alle Knopfreihen der App.

### Umbenennung, Satzzahl und Einheiten korrigieren

- **„Start" heißt jetzt „Trainieren", „Körper" heißt „Kalorien"** — mit passenden Zeichen in der
  Leiste: eine Hantel statt des Hauses, eine Flamme statt der Waage.
- **„Alle Trainingspläne" ist aus den Einstellungen raus.** Der Weg dorthin steht auf „Trainieren",
  wo die Trainingssachen hingehören; in den Einstellungen stand dieselbe Karte ein zweites Mal.
- **Drei Sätze statt vier bei viel Volumen** (Karls Ansage: „das reicht immer"). Damit ist die
  Voreinstellung überall 3. Die Volumen-Wahl ändert weiterhin den Wiederholungs-Bereich (6–10 bzw.
  8–12) und wie viele Übungen der Assistent pro Tag nimmt. **Bestehende Trainings behalten ihre
  gespeicherte Satzzahl** — geändert wird nur, womit neue Übungen anfangen.
- **Eine abgeschlossene Einheit lässt sich im Verlauf korrigieren.** Bisher gab es dort nur
  „Einheit löschen" — ein Tippfehler bei kg (100 statt 10) verzog Rekorde, Volumen und Kurven
  dauerhaft, und der einzige Ausweg war, die ganze Einheit wegzuwerfen. Jetzt oben rechts
  **„Bearbeiten"**: kg und Wdh ändern, einzelne Sätze löschen, Sätze nachlegen, ganze Übungen aus
  der Einheit werfen (zwei Tipps, wie beim Löschen sonst auch).
  - **Volumen, Rekorde, Kurven und XP rechnen sich neu.** Damit der Punktestand stimmen kann,
    merkt sich eine Einheit ab jetzt, wie viel XP es für sie gab. Einheiten von **vor** dem 06.08.
    haben das nicht — dort bleibt der Punktestand unangetastet, statt einen Wert zu raten.
  - Aufwärmsätze heißen in der Einheit jetzt **„Aufwärmen"** statt „Satz 1". Sie zählen nirgends
    mit, und die alte Beschriftung behauptete das Gegenteil.
  - ⚠️ Beim Verlassen eines Eingabefeldes wird **nicht** neu gezeichnet. Ein Neuzeichnen genau in
    dem Moment frisst den Klick, der es ausgelöst hat (mousedown auf ✕ → blur → neues DOM →
    mouseup ins Leere). Nachgetragen wird nur die Zahl in der Kopfzeile.

## 2026-08-05

### Mehrere Trainingspläne, PC-Version und Kleinigkeiten (nachts)

- **Es gibt jetzt mehrere Trainingspläne.** Bisher gab es *eine* Liste von Trainings. Ein
  Trainingsplan (z.B. „PPL 3er") enthält jetzt seine Trainings, und einer davon ist der aktuelle.
  „Alle Trainings" heißt entsprechend **„Alle Trainingspläne"** und listet die Pläne auf. Je Plan:
  **Auswählen** (macht ihn zum aktuellen), **Bearbeiten**, **Teilen**, **Löschen**. Darunter
  „Bauen lassen" (der Assistent) und „Leer anlegen".
  - Der Assistent **ersetzt nichts mehr**, sondern legt einen **neuen** Plan an und macht ihn zum
    aktuellen. Er fragt am Ende nach einem Namen.
  - **Bearbeiten wechselt den aktuellen Plan nicht.** In einem Plan, der nicht der aktuelle ist,
    gibt es kein „Starten" — sonst würde man versehentlich aus dem falschen Plan trainieren.
  - **Geteilte Pläne kommen als eigener Plan dazu**, nicht in einen bestehenden hinein. Der Link
    trägt jetzt auch den Namen des Plans.
  - **Bestehende Daten wandern automatisch** in einen Plan namens „Mein Plan" — beim Start und
    beim Laden alter Sicherungen und Cloud-Stände.
  - **„Trainingsplan einrichten" ist aus den Einstellungen verschwunden**; dort steht jetzt ein
    Verweis auf „Alle Trainingspläne", wo alles zum Thema Plan zusammenliegt.
- **PC-Version.** Ab 900 px Fensterbreite: die untere Leiste wird zur **Seitenleiste links**, der
  Inhalt wird breiter und liegt auf der Startseite in **zwei Spalten**, der Pausen-Timer sitzt
  rechts unten. Kein zweiter Quelltext — dieselbe App, nur andere Anordnung.
- **Die Laufzeit oben rechts ist deutlich größer** und in der Signalfarbe, mit festen Ziffernbreiten,
  damit sie beim Ticken nicht springt.
- ⚠️ **Der Pausen-Timer blieb nach dem Training stehen.** `stopRest()` hielt nur die Uhr an, die
  Restzeit blieb gesetzt — und damit die Leiste sichtbar. Beim Beenden, Abbrechen und Verwerfen
  wird sie jetzt richtig abgeräumt.
- **Die Gewichtsfrage ist ganz aus dem Assistenten raus.** Sechs Schritte statt sieben; Gewicht
  trägt man unter „Körper" ein.

### Vier neue Funktionen (spät abends)

- **Laufzeit der Einheit.** Sobald ein Training läuft, tickt oben rechts eine Uhr — auch auf der
  Startseite in der „Training läuft"-Karte. Am Ende wird die Dauer mitgespeichert und steht im
  Verlauf bei jeder Einheit sowie in ihrer Detailansicht. Einheiten von vor heute haben keine
  Dauer; dort steht dann nichts. Eigener Ticker statt Neuzeichnen im Sekundentakt — sonst würde
  beim Tippen der Fokus aus dem Eingabefeld springen.
- **Eigene Übung anlegen.** In der Übungs-Bibliothek ist der Suchtext zugleich der Name: steht
  nichts Passendes drin, legt die letzte Zeile die Übung genau so an. Als Bild kommt automatisch
  eine **neutrale Hantel**. Die galt vorher nicht — unbekannte Namen bekamen stillschweigend das
  Bizeps-Curl-Bild.
- **Aufwärmsatz.** Wählbar im Assistenten (Schritt 3, bei der Volumen-Frage) und pro Training im
  Editor. Bringt vor jeder Übung einen lockeren Satz mit rund **70 %** des Arbeitsgewichts, auf
  2,5 kg gerundet. Er ist mit **W** statt einer Nummer gekennzeichnet und **zählt nirgends mit**:
  nicht beim Volumen, nicht bei den Sätzen, nicht bei XP, nicht beim Rekord und vor allem nicht
  bei der Steigerung — sonst zöge der leichte Satz die Wiederholungs-Regel nach unten und es gäbe
  nie wieder mehr Gewicht.
  *(Kehrt die Entscheidung vom 30.07. um, mit der Aufwärmsätze abgelehnt wurden.)*
- **Trainingsplan teilen.** Rechts oben auf „Alle Trainings". Der ganze Plan steckt im Link —
  kein Server, kein Konto beim Empfänger nötig. Wer den Link öffnet, bekommt nach der Anmeldung
  ein Fenster mit der Liste und kann übernehmen oder ablehnen; **eigene Trainings bleiben stehen**.
  Ist ein Wochentag beim Empfänger schon belegt, kommt das Training ohne festen Tag rein statt gar
  nicht — die Ein-Training-pro-Tag-Regel bleibt damit heil. Geteilt wird nur der Plan: keine
  Einheiten, kein Fortschritt, kein Name.

### Karls Kleinigkeiten-Liste (abends)

- **Wiederholungen werden wieder selbst eingetippt.** Im laufenden Training steht neben dem Gewicht
  jetzt ein Wdh-Feld statt eines festen Ziel-Kästchens; der Zielbereich der Übung steht als Vorgabe
  darin. Bleibt es leer, zählt fürs Volumen weiterhin die untere Zahl des Bereichs.
  *(Kehrt die Entscheidung vom 30.07. um, mit der die Wdh-Eingabe entfernt wurde.)*
- **Neue Steigerungs-Regel.** Mehr Gewicht wird vorgeschlagen, sobald **jeder** Satz über der Grenze
  lag: **über 10 Wdh** bei wenig Volumen, **über 14 Wdh** bei viel. Vorher hing der Vorschlag nur
  daran, ob alle Sätze abgehakt waren. Der schwächste Satz entscheidet — ein einzelner guter Satz
  zieht das Gewicht nicht hoch.
- **Startseite: die drei Kacheln sind weg** (Einheiten · diese Woche · kg Vol.).
- **Startseite: ein laufendes Training steht nicht mehr ganz oben**, sondern direkt unter „Heute".
- **Einstellungen: „Trainingsplan einrichten" ist jetzt die erste Karte.**
- **Einstellungen: alles zum Konto steht zusammen.** Benutzername, Abmelden und Konto löschen sitzen
  in einem Kasten; vorher stand der Benutzer-Block allein an der Spitze.
- **„Verlauf & Rekorde" heißt nur noch „Verlauf".**
- **„+ Aus Bibliothek" ist nicht mehr weiß** — `primary` ist im dunklen Design fast weiß und stach
  als Klotz heraus. Sieht jetzt aus wie „+ Eigene" daneben.
- **Klassische Splits statt eigener Erfindungen.** Der 5-Tage-Fall war „Push, Pull, Beine plus zwei
  gemischte Tage" und damit der einzige, den es so nirgends gibt. Jetzt der klassische 5er-Split:
  Brust · Rücken · Schultern · Arme · Beine. Die übrigen waren schon etabliert (Upper/Lower,
  Push/Pull/Legs, Upper/Lower ×2, PPL ×2) und bleiben.

### Brock

- **Neun Rang-Brocks** aus Karls Blatt — je einer pro Rangstufe (`5e7ae23`). In der Rang-Leiter
  (gesperrte Stufen als graue Silhouette), auf der Rang-Karte und als sprechender Begleiter.
- **Auch im Einrichtungs-Assistenten** (`9c117ea`). Der Assistent ist **nicht** das Tutorial.
  Der alte `brock.png` bleibt nur noch auf dem Anmeldeschirm und im späteren Tutorial.

### Trainings & Plan

- **Belegte Wochentage sind gesperrt** (`a92de2f`) — steht an einem Tag schon ein Training, lässt er
  sich nicht ein zweites Mal vergeben.
- **Ziel (Wdh) je Übung** (`a92de2f`) — 6–10 oder 8–12 pro Übung statt nur global. Übungen ohne
  eigenes Ziel folgen weiter der globalen Wahl.
- **Plan anlegen: selbst oder automatisch** (`325c0df`) — zwei gleichrangige Wege, im Assistenten
  und auf der Trainings-Seite. Damit hat auch ein frisches Konto einen Ausweg aus der Einrichtung.
- **„+ Eigene" gab fest 3 Sätze**, der Assistent 4 — beides kommt jetzt aus derselben Stelle.

### Assistent

- **Nach dem Gewicht wird nur noch gefragt, wenn keins da ist** (`896c375`).
  ⚠️ Das war nicht nur lästig: das Feld war mit dem letzten Wert vorbelegt, und Einträge werden auf
  **heute** datiert — wer durchklickte, schrieb einen alten Wert als heutige Messung in die Kurve.
- **„Fokus auf Kraft / Muskelaufbau" ist raus** (`1fe70f3`) — 6–10 gegen 8–12 Wdh gibt diesen
  Unterschied nicht her.

### Datenschutz

- **Seite überarbeitet** (`a92de2f`). ⚠️ „Ohne Konto bleibt alles nur lokal" war seit der
  Login-Pflicht vom 31.07. falsch und ist raus. Ergänzt: Rechtsgrundlage (Art. 6),
  Auftragsverarbeitung (Art. 28), EU-Server ohne Drittlandtransfer, alle sechs Betroffenenrechte
  (Art. 15–21), Beschwerderecht (Art. 77), Stand-Datum.

### Behoben

- **Überlauf bei 320 px im Trainings-Editor** (`a92de2f`) — dem Namensfeld fehlte `min-width:0`,
  dadurch schob es den Lösch-Knopf aus dem Bild. Der Fehler bestand schon vorher.

---

## Davor

Für die Zeit vor dem 05.08.2026 gibt es keinen Changelog — die Historie steht in den Commits
(`git log`) und ausführlich in der Projektnotiz `04-projects/gym-log.md` im ki-os-Vault.
