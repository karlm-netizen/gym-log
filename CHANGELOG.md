# Änderungen

Neueste zuerst. Jede Zeile nennt den Commit, damit man zurückfindet.

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
