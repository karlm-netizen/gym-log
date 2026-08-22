# Änderungen

Neueste zuerst. Jede Zeile nennt den Commit, damit man zurückfindet.

## 2026-08-22

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
