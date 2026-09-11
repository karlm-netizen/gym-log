# Änderungen

Neueste zuerst. Jede Zeile nennt den Commit, damit man zurückfindet.

## 2026-09-11

### v0.083 — die Leiste sitzt tiefer, der Ladeschirm sagt Bescheid

Karls Meldung vom 11.09.2026 mit Bildschirmfoto: **„da sieht man ganz klar das die Leiste
viel höher ist als bei den anderen"** — und: **„mach es doch so das der Balken dann einfach
doppelt solange lädt und dort dann steht lade neue Version."**

#### 📐 Nachgemessen statt geraten

Das Foto (iPhone, 1179 × 2556 px = 393 × 852 pt) hat die Sache entschieden:

| | gemessen | angefordert |
|---|---|---|
| Leiste seitlich | **11,3 pt** | 10 pt ✅ |
| Leiste nach unten | **108 pt** | 44 pt ❌ |

Die Seitenränder stimmen **auf 1,3 pt genau** — dieselbe Regel, dieselbe Zeile. Nur der
Abstand nach unten ist zweieinhalbmal so groß wie angefordert.
➡️ Damit ist klar, wo es liegt: `env(safe-area-inset-bottom)` meldet auf dem Gerät viel mehr
als die 34 pt, mit denen hier gerechnet wurde. **Warum, ist von außen nicht zu sehen.**

#### 🧢 Deshalb ein Deckel statt einer Rechnung

Der Abstand nach unten ist jetzt **höchstens 26 px**, egal was `env()` meldet.
Die Lage der Leiste hängt damit nicht mehr an einer Zahl, die niemand nachprüfen kann.

⚠️ **`min()` steht in einer zweiten Zeile, mit einer einfachen Vorgabe davor** — genau wie
`color-mix` beim Hintergrund. Ein Browser, der `min()` nicht kennt, überspringt die Zeile;
ohne die Vorgabe stünde `bottom` auf `auto` und **die Leiste klebte plötzlich oben am
Bildschirm.** Dagegen steht eine eigene Prüfung, die im Quelltext nachsieht — im Regelwerk
ist die Vorgabe nicht mehr zu sehen, zwei gleiche Eigenschaften fallen dort zu einer zusammen.

#### 🧹 Und drei Maße, die auf derselben falschen Annahme standen

Innenabstand des Body, Pausenuhr und Offline-Band rechneten seit v0.081 alle mit
`env(safe-area-inset-bottom)`. **Beim Body wären das rund 184 px totes Feld unter jeder
Seite gewesen** — vermutlich der zweite Grund, warum das Profil so leer aussah.
➡️ Alle drei sind jetzt feste Zahlen: die Leiste steht höchstens 26 px über dem Rand und ist
rund 52 px hoch, ihre Oberkante liegt also nie höher als 78 px. 94 px räumen sie frei.
⚠️ Dazu eine Prüfung, die die Leiste **wirklich misst** und verlangt, dass der Inhalt
oberhalb endet.

#### 🔄 Der Ladeschirm sagt jetzt, warum er nochmal kommt

Seit v0.082 lädt die App auf dem Ladeschirm von selbst neu. **Ohne Hinweis sähe man denselben
Schirm zweimal und hielte es für einen Hänger.**

| | |
|---|---|
| 📝 | Statt „Wird geladen…" steht dort **„Lade neue Version…"** |
| ⏱️ | Der Balken läuft **doppelt so lange** (3600 statt 1800 ms) |
| 👆 | Auch beim Tippen auf die Leiste — wer tippt, soll genauso sehen, dass gearbeitet wird |

🔴 **Die Prüfung, die dabei wirklich zählt:** der Ladeschirm liegt über der ganzen App, und
es gibt eine harte Obergrenze (5000 ms), die ihn notfalls wegräumt. Liefe die Mindestzeit
darüber hinaus, **liefen zwei Uhren gegeneinander** — die Obergrenze nimmt den Schirm weg,
während die Mindestzeit ihn noch hält. Davor warnt der Kommentar seit dem 23.08.2026, und
die verdoppelte Zeit ist der erste Fall, der wirklich nah herankommt (3600 gegen 5000).

⚠️ Die Marke liegt im **Sitzungsspeicher** und wird **sofort beim Lesen gelöscht**: bricht
der Start ab, ist der nächste Versuch wieder ein ganz normaler Start.

#### 🧪 Am Prüfstand

**950 Prüfungen** (waren 943), alle grün, dazu die vier Datenschutz-Prüfungen.
**Zwei Gegenproben**, beide mit dem erwarteten Rot (**3** und **3**).

### v0.082 — ein Kasten im Profil, neue Fassung lädt von selbst

Karls zwei Meldungen vom 11.09.2026:
**„die 2 oberen Kästen bitte zusammenfügen brok ist dort doppelt zu sehen das mag ich nicht"**
und **„wenn die App eh einmal im lade screen ist und es eine neue Fassung gab kann sie dann
nicht einfach automatisch reingeladen werden"**.

#### 👤 Im Profil steht Brock nur noch einmal

Das Profil hatte oben einen eigenen Kasten mit Brock (72 px), Name und „Rang · Level" — und
**direkt darunter die Rang-Karte mit Brock (56 px), Rang und Level nochmal.** Dasselbe
Monster zweimal untereinander, dieselben zwei Angaben doppelt.

➡️ Der Name ist **in die Rang-Karte selbst** gewandert. Eine Karte, ein Brock.

⚠️ **Warum als Parameter und nicht als zweite Bauform:** diese Karte wird an **drei** Stellen
gezeichnet — Startseite, Rang-Leiter, Profil. Zwei Bauformen nebeneinander hießen Aura,
Funken und XP-Leiste doppelt zu pflegen, und beim nächsten Umbau fällt die eine mit und die
andere nicht. Ohne `name` bleibt alles exakt wie bisher; **dagegen steht eine eigene
Prüfung**, damit die Profil-Fassung nicht still auf der Startseite durchschlägt.

#### 🔄 Die neue Fassung lädt sich selbst, wo nichts verlorengehen kann

Karl hat recht, und der Grund stand schon im Code: **gefragt wird nur, weil ein Neuladen
wegreißt, was gerade eingetippt ist.** Auf dem Ladeschirm ist nichts eingetippt — die App ist
noch nicht mal gezeichnet.

| Lage | Was passiert |
|---|---|
| 🖼️ **Ladeschirm** | **lädt von selbst** |
| 🔑 **Anmeldeschirm** | **lädt von selbst** — wer kein Konto offen hat, hat nichts offen |
| ⌨️ **Irgendwo steht Getipptes** | fragt, wie bisher |
| 🏋️ **Laufendes Training** | fragt nie, lädt nie |
| 📱 **Angemeldet und drin** | fragt, wie bisher |

🔴 **Am Anmeldeschirm stehen zwei Felder — E-Mail und Passwort.** Wer die halbe Adresse
getippt hat und mittendrin ein Neuladen bekommt, tippt sie noch einmal und weiß nicht,
warum. Deshalb wird die **ganze Seite** auf Getipptes abgesucht, nicht nur das Anmeldefeld.
⚠️ Ein gesetzter Haken zählt dabei **nicht** als Text — sonst wäre das selbständige Laden
gesperrt, sobald irgendwo ein Schalter steht: eingebaut und wirkungslos.

#### 🚨 Die Bremse, die wichtiger ist als die Funktion selbst

Bliebe das Erkennen der neuen Fassung aus irgendeinem Grund hängen — ein Service Worker, der
sich bei jedem Start neu installiert —, **würde sich die App auf dem Ladeschirm endlos neu
laden.** Kein Absturz, keine Fehlermeldung, nur eine App, die ewig lädt und nicht mehr zu
benutzen ist.

➡️ Höchstens **ein** selbständiges Laden je Minute, im Sitzungsspeicher vermerkt.
⚠️ Wirft der Speicher (privater Modus), gilt **nicht erlaubt** — lieber einmal fragen als
eine Schleife riskieren.

#### 🧪 Am Prüfstand

**943 Prüfungen** (waren 931), alle grün, dazu die vier Datenschutz-Prüfungen.
**Drei Gegenproben**, alle mit dem erwarteten Rot:

1. Zweiter Kasten im Profil zurück, Endlos-Bremse entfernt → **3 rot**
2. Riegel gegen Getipptes und laufendes Training weg, Haken zählt mit → **3 rot**
3. Die Profil-Fassung der Karte schlägt überall durch → **1 rot**

### v0.081 — die Leiste schwebt, das Zahnrad ist raus

**Karls Ansage vom 11.09.2026:** *„Also Einstellungen können unten damit aus der Leiste raus
und der Leiste soll so rund und schweben sein und ein bisschen transparent."*

#### Was sich ändert

| | |
|---|---|
| 🔢 | **Vier Symbole statt fünf** — Trainieren, Kalorien, Erfolge, Profil |
| ⚙️ | **Das Zahnrad ist aus der Leiste raus.** Der Weg in die Einstellungen geht über das Profil (seit v0.080) |
| 🫧 | **Die Leiste schwebt:** runde Ecken, 10 px Abstand zum Rand, durchscheinend mit Milchglas dahinter |
| 👉 | Gewischt wird zwischen **vier** Reitern |
| 🖥️ | Auf dem PC bleibt es die angeklebte 232-px-Seitenleiste — **das Schweben wird dort vollständig zurückgenommen** |

#### 🔴 Zum zweiten Mal in zwei Tagen dieselbe Falle an derselben Leiste

**Die rote Zahl aus dem Postfach hing am Zahnrad.** Genau der Knopf ist heute aus der Leiste
gefallen. `navZahl()` steigt bei einem nicht gefundenen Knopf **still** aus — wäre der
Selektor stehengeblieben, wäre die Zahl **ersatzlos verschwunden**: eine Antwort, die es
gibt und die niemand sieht, und nirgends wird etwas rot.

➡️ Sie sitzt jetzt am **Profil-Knopf** — dort, wo der Weg ins Postfach anfängt. Die Prüfung
dazu **misst** die Zahl, statt im Quelltext zu lesen.

#### ⚠️ Drei weitere Sachen, die am Zahnrad hingen

1. **Sieben Ansichten haben ihre Markierung verloren.** Einstellungen, Verlauf, eine
   einzelne Einheit, Übungs-Verlauf, Admin, Datenschutz und Meldung markierten alle
   `settings`. Ohne neuen Ast in `setNav()` hätte die Leiste in diesen sieben Ansichten
   **komplett unmarkiert** dagestanden — kein Absturz, nur Orientierungslosigkeit.
   Sie markieren jetzt `profil`.
2. **Die Einstellungen hatten keinen Weg zurück.** Bis heute war es ein Reiter: antippen
   hin, antippen weg. Jetzt gibt es oben einen **Zurück-Pfeil ins Profil**.
3. **Der Rückwärts-Wisch.** `settings` steht nicht mehr in `REITER`; die Prüfung dafür
   ist auf `profil` umgezogen. (Aus den Einstellungen heraus wird jetzt gar nicht mehr
   animiert — richtig so, es ist kein Reiter mehr.)

#### 📐 Drei Maße hingen an der Höhe der Leiste

Sie schwebt 10 px höher als vorher, und der Geräte-Balken kommt darunter. Mitgezogen:
der **Innenabstand des Body**, die **Pausenuhr** und das **Offline-Band** — alle drei jetzt
mit `env(safe-area-inset-bottom)`.
🔴 **Die Pausenuhr stand mit ihren festen 56 px auf einem iPhone ohnehin schon im
Balkenbereich der Leiste.** Das ist mit repariert.

#### 🫧 Zwei Zeilen, die doppelt dastehen, und warum

`background` steht **zweimal** in der Regel: `color-mix` kennt nicht jeder Browser, und wer
es nicht kennt, überspringt die ganze Zeile. Ohne die deckende Vorgabe davor stünde die
Leiste dort **ohne Hintergrund** und der Inhalt liefe sichtbar dahinter durch.
**Lieber undurchsichtig als unlesbar.**

#### 🧪 Am Prüfstand

**931 Prüfungen** (waren 923), alle grün, dazu die vier Datenschutz-Prüfungen.
**Drei Gegenproben**, alle mit dem erwarteten Rot:

1. Den Zahl-Selektor am Zahnrad gelassen → **9 rot**
2. `setNav`-Ast weg, Zurück-Pfeil weg → **2 rot**
3. Schweben zurückgedreht, PC nimmt nichts zurück → **5 rot**

Vier Kommentare nachgezogen, die „fünf Reiter" sagten.

### v0.080 — Schritte-Erinnerung verschwindet, Einstellungen im Profil

Karls zwei Ansagen vom 11.09.2026:
**„Schritte gestern muss verschwinden sobald man sie eingetragen hat und man muss es genau
wie die anderen 2 Widgets auf der Startseite entfernen können."** und
**„Einstellungen müssen aufjedenfall bei Profil rein weil Einstellungen stehen nie allein."**

#### Was sich ändert

| | |
|---|---|
| 👟 | **„Schritte gestern" ist jetzt eine Erinnerung wie die anderen zwei** — steht da, solange gestern offen ist, und ist danach weg |
| 🔘 | **Dritter Schalter in den Einstellungen** — die Erinnerung lässt sich abstellen |
| 📍 | **Die Zahl hat einen festen Platz bekommen:** unten auf der Kalorien-Seite, unter der Gewichtskurve |
| ⚙️ | **Die Einstellungen sind vom Profil aus erreichbar** — samt der roten Zahl aus dem Postfach |

#### 🔴 Der Fund, der die Ansage sonst zur Falle gemacht hätte

Die Karte auf der Startseite war **der einzige Ort in der ganzen App**, an dem eine
Schrittzahl eingetragen *oder korrigiert* werden konnte. Hätte sie nach dem Eintragen nur
noch aufgehört zu erscheinen, wäre ein Zahlendreher **unumkehrbar** gewesen — 84.320 statt
8.432, und kein Weg zurück. `setzeSchritte()` überschreibt den Tag; die Korrektur *ist*
das erneute Eintragen, und genau das Feld dafür wäre verschwunden.

➡️ Deshalb hat die Zahl einen festen Platz auf der Kalorien-Seite bekommen. Dieselbe
Aufteilung wie bei den anderen zwei Erinnerungen: **die Startseite erinnert, die Sachseite
hält den Wert und lässt ihn ändern.**

#### ⚠️ Die zweite Stelle, an der eine naheliegende Fassung falsch gewesen wäre

`schritteAmTag()` gibt **0** zurück, wenn nichts dasteht — und ebenso, wenn eine **0**
dasteht. Mit `if(!schritteGestern())` wäre die Erinnerung für jemanden, der gestern
wirklich nicht gelaufen ist und das einträgt, **für immer stehengeblieben**: eine
Aufforderung, der man nachkommt, ohne dass sie je verschwindet.
➡️ Gefragt wird deshalb nach dem **Eintrag**, nicht nach der Zahl (`schritteGesternEingetragen()`).

#### 🚫 Einstellungen: verlinkt, nicht hineinkopiert

Abmelden, Alles zurücksetzen und Konto löschen stehen seit dem 27.08.2026 in genau der
Reihenfolge in den Einstellungen, die Karl angeordnet hat. **Drei gefährliche Knöpfe ein
zweites Mal aufzustellen wäre die schlechtere Art, dieser Ansage nachzukommen** — die
Prüfung von gestern („stehen NICHT im Profil") bleibt gültig und grün.
🔴 **Die rote Zahl steht mit im Profil.** Sie hängt sonst nur am Reiter unten; wer im Profil
steht und von dort in die Einstellungen geht, sähe ohne sie nicht, dass eine Antwort wartet.
Dieselbe Bauform wie gestern bei der Leiste.

#### 🧪 Am Prüfstand

**923 Prüfungen** (waren 912), alle grün, dazu die vier Datenschutz-Prüfungen.
**Drei Gegenproben gelaufen**, alle mit dem erwarteten Rot:

1. `schritteGesternEingetragen()` auf die Zahl statt den Eintrag umgestellt und die rote
   Zahl aus dem Profil genommen → **2 rot**
2. Die Schritt-Karte von der Kalorien-Seite genommen und das Zahnrad umgehängt → **8 rot**
3. Die Bedingung auf der Startseite auf `true` gesetzt → **3 rot**

#### ✂️ Zwei bestehende Prüfungen sind mitgezogen

- **„Beide Erinnerungen haben einen echten Schalter"** heißt jetzt **„Alle drei"** und
  erwartet drei statt zwei.
- **„Im Kalorien-Kasten steht keine Schritt-Zahl mehr"** ist **enger gefasst**, und das ist
  bewusst aufgeschrieben: sie hieß immer „im Kalorien-*Kasten*", hat aber die ganze Seite
  abgesucht. Geprüft wird jetzt der Teil **vor** der neuen Karte — Kopfzeile, Brock, Ring,
  Tagesziel, Mahlzeiten, Kurve. **Was sie schützt, schützt sie unverändert:** dass die Zahl
  nicht in die Rechnung zurückkommt. Daneben steht unverändert „Der Ring zeigt das
  Grundziel", und zwei neue Prüfungen verlangen, dass die neue Karte *gestern* zeigt und
  selbst sagt, dass sie nichts mitrechnet.
- **„Ein leeres Feld trägt nichts ein"** ist auf die Kalorien-Seite umgezogen — sie trug
  vorher ein und stand danach auf der Startseite vor einer Karte, die es nicht mehr gibt.
  **Sie ist beim ersten Lauf prompt umgefallen**, und zwar zu Recht.

#### 🧹 Datenschutzerklärung nachgezogen

Dort stand, die Schritte würden „auf der Startseite" eingetragen. Es sind jetzt zwei Orte.

### v0.079 — fünf Symbole, kein Text, Profil rechts

Karls Entscheidung vom 10.09.2026 im Wortlaut: die untere Leiste soll **„wie Instagram"**
aussehen, und dazu ein Profil. Seine Antwort auf die Rückfrage:
**„Fünf Symbole, kein Text, Profil rechts."**

#### Was sich ändert

| | |
|---|---|
| 🔤 | **Die Beschriftungen sind auf dem Handy weg.** Fünf Symbole, sonst nichts |
| 👤 | **Ein fünfter Reiter „Profil" ganz rechts** — Bild, Name, Rang, Level, drei Zahlen |
| 🔍 | Symbole etwas größer (25 statt 22 px), die Leiste etwas höher |
| 🏅 | **Die Rang-Leiter gehört jetzt zum Profil**, nicht mehr zu „Trainieren" |
| 👉 | Gewischt wird zwischen **fünf** Reitern statt vier |
| 🖥️ | **Auf dem PC bleibt alles beschriftet** — dort ist die Leiste eine 232 px breite Seitenleiste |

#### 🔴 Die Stelle, an der es still hätte schiefgehen können

Der Text ist weg — aber **die rote Zahl aus dem Postfach hängt IM Wort-Span.** Das war
eine bewusste Entscheidung vom 27.08.2026 (damit die Zahl auf dem PC an der Schrift klebt
statt in der Mitte eines 204 px breiten Knopfes zu schweben).

**Der naheliegende Weg wäre `display:none` gewesen** — und damit wäre die Zahl lautlos
mitverschwunden: eine Antwort im Postfach, die niemand sehen kann, und **nirgends wäre
etwas rot geworden.**

➡️ Stattdessen `font-size:0`: der Span bleibt stehen, schrumpft auf null und trägt die
Zahl weiter. Nebenbei behält jeder Knopf damit seinen Namen für eine Vorlesehilfe — ohne
das wären es fünf namenlose Bilder.
⚠️ **Und die PC-Fassung muss die Schriftgröße ausdrücklich zurücksetzen.** Ein
`nav button{font-size:14.5px}` hilft dort nicht: der Span hat seinen eigenen Wert.

#### 🧪 Am Prüfstand

**912 Prüfungen** (waren 898), alle grün, dazu die vier Datenschutz-Prüfungen.
Neu dabei und **beide gegengeprobt**:

- **„Die Zahl an der Leiste ist trotz fehlendem Text noch zu sehen"** — sie *misst* die
  Zahl (`getBoundingClientRect`), statt im Quelltext zu lesen. Mit `display:none` statt
  `font-size:0` wird sie rot.
  🔴 **Beim ersten Lauf ist sie selbst umgefallen, und das zu Recht:** im Prüfrahmen ist
  niemand angemeldet, und `body.gate` blendet die ganze Leiste aus. Gemessen wurden
  0 × 0 — egal wie richtig das CSS war. Jetzt nimmt die Prüfung die Klasse für die Dauer
  der Messung ab und setzt sie zurück, **und eine zweite Prüfung sichert genau das ab.**
- **„Auf dem PC bekommt die Beschriftung ihre Schrift zurück"** — liest die echte
  CSS-Regel aus `document.styleSheets`, weil sich die Fensterbreite im Prüfrahmen nicht
  umstellen lässt.
- **„Abmelden, Zurücksetzen und Löschen stehen NICHT im Profil"** — siehe unten.

#### 🚫 Was bewusst NICHT ins Profil gewandert ist

- **Der Konto-Kasten bleibt in den Einstellungen.** Abmelden, Alles zurücksetzen und Konto
  löschen stehen dort seit dem 27.08.2026 in genau der Reihenfolge, die Karl angeordnet
  hat. **Drei gefährliche Knöpfe still an einen zweiten Ort zu kopieren, wäre schlimmer
  als ein dünnes Profil** — dagegen steht jetzt eine Prüfung.
- **Der Verlauf wird von hier nicht verlinkt.** Sein Zurück-Pfeil sagt „Zurück zu
  Einstellungen" — von hier aus wäre das gelogen.
- **Die Wochen-Serie nicht.** Sie ist am 29.08.2026 auf Karls Ansage von der Startseite
  geflogen; sie im Profil wieder aufzumachen hieße, seine Entscheidung zurückzudrehen,
  nur an anderer Stelle.
- **`syncState` nicht.** Der Wert wird nur nachgezogen, solange man in den Einstellungen
  steht — im Profil stünde er fest und würde mit der Zeit falsch.

#### ❓ Eine Frage bleibt offen

Karls Stichwort war **„Profil einrichten"**. Gebaut ist jetzt die Ansicht — wer man ist
und wie weit man ist. **Ob „einrichten" auch heißt: Namen ändern, eigenes Bild**, ist
damit nicht beantwortet. Ein Namenswechsel rührt an die Username-Zuordnung in Supabase
und wird deshalb nicht nebenbei gebaut, sondern vorgelegt.

#### 🧹 Nebenbei: vier Kommentare, die nicht mehr stimmten

„Nur zwischen den **vier** Reitern der unteren Leiste" (zweimal), „welche **vier**
Reiter" im Prüfstand — und über `setNav` stand seit Längerem, die Rang-Ansicht habe
keinen eigenen Platz in der Leiste, weshalb dort „Trainieren" markiert bleibe.
**Das stimmt seit heute nicht mehr.** Alle vier nachgezogen.

## 2026-09-10

### v0.078 — zehn Punkte von Karls Liste, und die Schritte fliegen aus der Rechnung

Karl war den ganzen Tag nicht zu Hause und hat die Liste vom Handy geschickt.
**Nichts davon kam aus einem Agentenlauf** — alles sind Dinge, die er auf dem Schirm
gesehen hat.

#### 🔴 Der Fund, den er gesehen hat und achtzehn Tage lang niemand sonst

*„Neben der Flammen Streak bei Kalorien Startseite ist irgendein komisches Zeichen?"*

Neben der Serie stand das Zeichen **U+0082** — ein unsichtbares Steuerzeichen — und
dahinter eine glatte **2**. Es steht seit dem **23.08.2026** da, seit die Flamme gebaut
wurde, und **nichts ist davon je rot geworden.**

Entstanden ist es beim Schreiben durch ein Skript: gemeint war die CSS-Fluchtfolge fuer
den Punkt. In einem gewoehnlichen Python-Text sind Rueckstrich und die ersten drei
Ziffern aber eine **Oktalzahl** — 202 oktal ist genau U+0082 — und die letzte Ziffer
blieb als sichtbare 2 stehen.

⚠️ **Und derselbe Fehler ist beim Aufschreiben des Kommentars sofort wieder passiert.**
Die Erklaerung enthielt die Fluchtfolge als Beispiel und wurde auf dem Weg durch die
Shell erneut in das Steuerzeichen verwandelt. **Gefunden hat es die Pruefung, die genau
dafuer angelegt worden war, im ersten Lauf.**
➡️ Neue Pruefung: **kein unsichtbares Steuerzeichen irgendwo im Quelltext**, nicht nur
an dieser Stelle.

#### 🔴 Die Schritte sind aus jeder Rechnung raus

*„Schritte Feature nur als manuellen Feature reinnehmen, es soll ein Widget auf der
Startseite geben um die vom Vortag einzutragen — die sollen aber aus allen Rechnungen
rausgehalten werden."*

Das kehrt Karls eigene Entscheidung vom 22.08.2026 um. Weg sind:

- der Faktor **kg × 26** (`ERHALT_SITZEND`) — gerechnet wird wieder mit **× 30** fuer alle
- `kcalAusSchritten()`, die kcal je Schritt und das **bewegliche Tagesziel**
- der **Ein/Aus-Schalter** und der ganze Einstellungen-Block
- der **Kurzbefehl-Weg** aus der Adresszeile samt Anleitung und Adresse zum Kopieren

Neu: ein Feld **„Schritte gestern"** auf der Startseite. Der Vortag und nicht heute —
ein laufender Tag hat keine fertige Zahl, und weil das Eintragen den Tageswert
ueberschreibt, muesste man abends daran denken, es noch einmal zu tun.

⚠️ **Wer den Schalter anhatte, behaelt sein altes Grundziel.** Es wurde mit × 26
gerechnet, ist also tiefer, als es ohne Schritte sein muesste. **Es wird hier bewusst
nicht angefasst** — jemandem ueber Nacht die Tagesvorgabe zu aendern, ohne dass er es
merkt, waere schlimmer als eine Zahl, die er selbst neu vorschlagen lassen kann.

#### Was Karl sonst auf dem Schirm hatte

| | |
|---|---|
| 🔄 | **Der Ladebalken laedt jetzt wirklich von 0 auf 100 %.** Vorher lief ein 40-%-Streifen im Kreis — eine Bewegung, die nichts misst und beim haengenden Start genauso aussah wie beim normalen. Die Breite haengt an vier echten Wegmarken des Starts; die letzte Strecke laeuft ueber die restliche Mindestzeit voll |
| ⮕ | **Zwei Zurueckpfeile beim Essen-Eintragen — einer ist weg.** Nebenwirkung der Reparatur vom 04.09.: seit `h` dort von `=` auf `+=` umgestellt wurde, stand der Pfeil der Kopfzeile unter dem allgemeinen. Der Fehlerkasten sitzt jetzt unter der Kopfzeile statt darueber |
| 🗑️ | **„0 Einträge" neben „Ernährung" ist weg** — die Zahl sagte nichts, was die vier Mahlzeiten-Zeilen darunter nicht schon zeigen |
| 🗑️ | **Die Gewichts-Eintraege sind raus.** Der Kurvenverlauf reicht. ⚠️ **Damit gibt es keinen Weg mehr, einen einzelnen Wert zu loeschen** — ein Satz unter der Kurve sagt das jetzt: ein falscher Wert von heute wird ueberschrieben, wenn man sich heute noch einmal wiegt |
| ⚖️ | **Wiegen zaehlt einmal am Tag.** Die Erfolge zaehlten **Zeilen**, und der Kommentar daneben hielt das fuer dasselbe wie Tage, weil das Eintragen den Tag ueberschreibt. 🔴 **Das gilt nur fuer ein Geraet** — morgens am Handy, abends am PC, und der Abgleich legt zwei Zeilen fuer denselben Tag zusammen. Jetzt werden Tage gezaehlt |
| 🏆 | **Admin-XP stehen nicht mehr in der Bestenliste.** Es reicht nicht, das Hochschreiben zu lassen — die alte Zeile bliebe mit ihrem Stand fuer immer stehen. Sie wird **geloescht**, und das Ergebnis wird **gezaehlt**: kommt keine Zeile zurueck, sagt die Erfolge-Seite, dass die Loeschregel fehlt |
| 🔄 | **Zuruecksetzen zieht die Bestenliste mit.** Karls Fund: seine Freundin hat ihr Konto zurueckgesetzt, und ihre Admin-XP standen weiter in der Liste. Absichtlich ein Schreiben mit 0 und kein Loeschen — die `update`-Regel gibt es seit dem ersten Tag, die `delete`-Regel erst seit heute Mittag und **noch nicht eingespielt** |
| 🟥 | **„Problem melden" steht in Rot** — Warndreieck und Wort, nicht der ganze Kasten |

#### 🔴 Beim Bauen selbst fast ein Schaden angerichtet

Ein Schnitt sollte vier Klick-Behandler entfernen und haette **20 fremde mitgenommen**
(`kob:*`, `ob:*`, `addweight`, `kcalgoal`, `newplan` …). Die Bedingung dafuer war
**gruen**: sie pruefte, was im Schnitt drin sein *muss* — nicht, was **nicht** drin sein
darf. Aufgefallen ist es an einer Laengenangabe (−6870 statt −905 Zeichen) und daran,
dass das Skript vorher an etwas anderem abstuerzte.
➡️ Jeder Schnitt hat jetzt beide Bedingungen, und am Ende zaehlt das Skript nach, ob
alle Behandler noch da sind.

#### 🔴 Der Datenschutz-Durchgang — drei schwere Funde, zwei davon selbst verursacht

Die Datenschutzerklärung wurde bei diesem Umbau **nicht angefasst** — nachgemessen: von
42 geänderten Stellen berührt keine einzige den Abschnitt. Umgebaut wurden daneben
Löschweg, Schrittdaten und Bestenliste.

| | Fund |
|---|---|
| 🔴 | **Der Text versprach einen Widerruf, den es nicht mehr gibt.** *„Du kannst sie jederzeit einzeln löschen oder den Schalter wieder ausmachen"* — die Gewichtsliste ist auf Karls Ansage weg, der Schritte-Schalter beim Umbau. **Die App widersprach ihrem eigenen Rechtstext in derselben Datei:** unter der Kurve stand *„Eintragungen lassen sich nicht mehr löschen"*, 1.340 Zeilen weiter das Gegenteil |
| 🔴 | **Der Text nannte den iOS-Kurzbefehl als Quelle der Schrittzahl.** Den Weg gibt es seit v0.078 nicht mehr — und der Satz war in die ungünstige Richtung falsch: er ließ die Zahl wie etwas aussehen, das ein Automatismus einsammelt |
| 🔴 | *„nie deine E-Mail-Adresse"* — geht weiter raus, weil `supabase-meldungen.sql` nicht eingespielt ist. **Kein Code-Fehler, ein Handgriff** |
| 🟡 | „Zwei Dinge kann die App nicht erreichen" — es sind **drei**, die Bestenlisten-Zeile fehlte |
| 🟡 | Für Art.-9-Daten wurde gar keine Einwilligung mehr eingeholt, seit der Schalter weg ist |
| 🔵 | „die drei Fälle oben" sind **vier** — ausgerechnet die Textsuche fehlte |

✅ **Karls Entscheidung: nur der Text wird ehrlich gemacht**, kein Löschknopf zurück. Die
Erklärung sagt jetzt, wie es ist: einzelne Werte kann man nicht selbst löschen, der heutige
wird durch erneutes Eintragen überschrieben, ältere auf Zuruf, sonst Konto löschen.

#### 🔴 Warum keine der damals 898 Prüfungen das gefangen hat — und was jetzt dagegen steht

`ZUSAGEN` lief **nur in eine Richtung**: *Kennzeichen im Code → Wortfolge muss im Text
stehen.* Das fängt, wenn die App etwas Neues tut, das niemand aufgeschrieben hat. **Die
Gegenrichtung hat niemand gemessen** — der Text verspricht etwas, und das Stück Code dazu
ist verschwunden. Auch die Datums-Prüfung kann es bauartbedingt nicht sehen: sie fragt
*„ist der Stand älter als der Text?"*, nicht *„hat sich der Code bewegt, ohne dass der Text
mitging?"*

➡️ **Neu: `pruefe_eingeloest()` mit der Tabelle `VERSPRECHEN`.** Vier Regeln, jede eine
Wortfolge im Text plus das Kennzeichen im Code, das sie einlöst. **Drei davon hätten die
heutigen Funde gefangen.**
⚠️ Eine Regel schläft, solange ihre Wortfolge nicht im Text steht — das ist richtig, aber
wer eine Zusage *umformuliert* statt sie zu streichen, legt sie unbemerkt schlafen. Deshalb
**zählt der Lauf die schlafenden Regeln und nennt sie beim Namen.**

#### 🔴 Und beim Einbau genau dieser Prüfung derselbe Fehler noch einmal

Die neue Funktion hieß zuerst `pruefe_versprechen` — **und die gab es schon.** Python nimmt
die letzte Definition: die ältere war damit tot, samt ihrer Textsuche- und Tracking-Regel.
**Beide hätten nie wieder etwas geprüft und nie etwas gesagt.** Aufgefallen ist es nur
daran, dass eine Ausgabe doppelt erschien.

➡️ **`pruefe_ablauf_vollstaendig()`** liest jetzt den eigenen Quelltext und meldet, wenn
eine `pruefe_*`-Funktion definiert, aber in `main()` nicht gerufen wird — oder wenn ein Name
zweimal vergeben ist. **Sie nimmt sich selbst nicht aus.**

#### Zwei Funde aus dem eigenen Durchgang über v0.078

| | |
|---|---|
| 🔴 | **„Gestern" war nicht immer gestern.** `Date.now() - 864e5` mit der Begründung, an Umstelltagen sei das gleichwertig. **Nachgerechnet: falsch.** An einem 23-Stunden-Tag landet ein Eintrag um 00:30 auf **vorgestern**. Zweimal im Jahr, ein Zeitfenster von einer Stunde, und aufgefallen wäre es nie — die Zahl steht ja da. Jetzt wird im Kalender gerechnet |
| 🟡 | Der Ladebalken lief über **genau** die Restzeit und brach beim Verschwinden bei etwa 99 % ab. Jetzt ist er vorher voll |

#### Gegenproben

**Vier neue Schadensfälle** in `datenschutz-gegenprobe.py` (jetzt 23 statt 19): Versprechen
ohne Code (zweimal), eine Prüfung ohne Aufruf, ein Name zweimal definiert. ⚠️ Die zwei
letzten arbeiten auf einer Kopie des **Prüfskripts**, nicht von `index.html` — die
Ablauf-Prüfung liest ihren eigenen Quelltext.

#### Pruefstand

**899 Pruefungen** (waren 894), alle gruen, dazu die vier Datenschutz-Pruefungen.
⚠️ **Sechs Pruefungen wurden nicht geloescht, sondern umgedreht**: sie verlangten, dass
die Schritte mitrechnen und dass die Gewichts-Eintraege dastehen. Jetzt verlangen sie
das Gegenteil — dieselbe Stelle, andere Aussage. Geloescht waeren sie Stellen ohne Wache,
an denen die alte Rechnung stillschweigend zurueckkommen koennte.


### v0.077 — der Löschcode von heute Mittag tat nichts

**Der dritte Agentenlauf: 13 Funde, 5 schwer.** Von den 12 Funden des Laufs davor
waren 6 sauber behoben, 4 halb, 2 gar nicht.

#### 🔴 Der schwerste: eine Reparatur, die nie greifen konnte

Heute Mittag wurde auf Karls Entscheidung eingebaut, dass „Konto löschen" die eigene
Zeile in der Bestenliste mitlöscht. **Die Datenbank lässt das gar nicht zu.**
`supabase-bestenliste.sql` vergab drei Regeln — `select`, `insert`, `update`. Für
`delete` **keine**, und ohne Regel ist es unter RLS für alle gesperrt. Die Datei sagte
es sogar selbst: *„Löschen braucht niemand. Ohne Regel ist es für alle gesperrt."*

⚠️ **Und niemand hätte es gemerkt:** PostgREST antwortet auf so ein DELETE mit **204,
genau wie bei Erfolg** — null betroffene Zeilen sind kein Fehler. Der Code sah die
Antwort nicht einmal an. Der Kommentar daneben behauptete dabei das Gegenteil der Lage
(*„Gefahrlos: die Zeilensperre lässt ohnehin nur die eigene Zeile zu"*).

➡️ **Drei Dinge repariert, nicht eins:**
- Die **Löschregel** steht jetzt in `supabase-bestenliste.sql` (`auth.uid() = user_id`,
  öffnet nichts). ⚠️ **Muss im Dashboard eingespielt werden.**
- Der Code **zählt**, was wirklich gelöscht wurde (`Prefer: return=representation`).
  Eine eingespielte Datei ist kein Beweis.
- Der Bildschirm **sagt es**: neuer Ausgang `'dataonly-liste'` nennt den
  Bestenlisten-Eintrag ausdrücklich, statt „dein Fortschritt ist weg" zu behaupten.

#### 🔴 Drei der vier Zusagen-Regeln waren maskiert

`pruefe_zusagen` suchte Einzelwörter. Nachgemessen: **„IP-Adresse" steht 2× im
Abschnitt, „Google" 5×, „Bestenliste" 3×.** Wer den Google-IP-Satz löschte, bekam grün —
der Open-Food-Facts-Satz deckte ihn. Nur „Art. 9" (1×) war scharf.
➡️ Jetzt **Wortfolgen statt Wörter**, jede genau einmal im Text. Und die Gegenprobe
prüft diese Eindeutigkeit selbst, damit es beim nächsten Umformulieren auffällt.

#### 🔴 „Kontakt" konnte gar nicht mehr fehlschlagen

Die `const PRIVACY_`-Zeilen gehören zum „Abschnitt" — richtig für den Arbeitsbaum-Check,
Gift für die Pflichtangaben: `PRIVACY_CONTACT` steht dort immer.
**Nachgemessen: den ganzen Verantwortlich-Absatz gelöscht → keine Funde.**
➡️ Die Pflichtangaben lesen jetzt ohne die `const`-Zeilen. *Eine Prüfung, die nicht mehr
durchfallen kann, ist keine Prüfung.*

#### 🔴 Die Hook-Gegenprobe startete niemand

11 Proben, kein Hook, kein Skript, kein Prüfstand — **das Einzige, was den Hook
absichert**, rief nichts auf. Dieselbe Bauform wie „die Gegenprobe ist nirgends
verdrahtet" von gestern, einen Stock tiefer.
➡️ Sie läuft jetzt in `pruefungen.py` mit. Und sie testet endlich `main()` und
**`melde()`** — ausgerechnet die Funktion, die den Hook am 09.09. stumm machte, wurde
von keiner Probe je ausgeführt.

#### 🔴 Die Warnung „Python nicht gefunden" war unerreichbar

`settings.json` startet den Hook mit genau dem `python.exe`, dessen Fehlen sie melden
sollte. Fehlt es, läuft der Hook gar nicht erst an.
➡️ `PYTHON` fällt jetzt auf `sys.executable` zurück — damit läuft der Hook auch auf dem
Laptop, und die Warnung greift, wenn wirklich keines da ist.

#### 🟡 Und vier, die still danebenlagen

- **Der Diff war blind für alles, was `git add` gesehen hat.** `git diff` ohne `HEAD`
  vergleicht gegen den Index. Nachgemessen: Zeile geändert → Fund; dieselbe Zeile nach
  `git add` → **kein Fund**. Der übliche Ablauf hier ist `git add -A` und dann committen,
  also war der Check genau im entscheidenden Moment blind.
- **Klemmendes git war still** — jetzt ein eigener Fund.
- **Reine Löschungen zählten um eins daneben.** git schreibt `+<Zeile davor>,0`; wer
  genau die erste Zeile eines Bereichs löschte, rutschte durch. Das ist beim
  Konstanten-Block `PRIVACY_OWNER` — **die Zeile, an der die Pflichtangabe
  „Verantwortlicher" hängt.**
- **Übersprungen hieß „bestanden".** Die zwei Proben, die den Arbeitsbaum-Check
  festnageln, brauchen einen sauberen Stand — im Alltag läuft der Prüfstand aber gerade
  dann, wenn Änderungen offen sind. Sie sprangen fast immer ab, und der Lauf meldete
  trotzdem „bestanden". Jetzt steht es im Ergebnis.
- **Der Hook merkte sich den Stand, bevor die Meldung heraus war.** Stirbt `melde()` an
  der Ausgabe — genau das ist am 09.09. passiert —, wäre der Stand gemerkt und die
  Meldung weg. Jetzt wird erst gemeldet, dann quittiert.

**894 Prüfungen grün.** Gegenproben: 18 Fälle für die Datenschutz-Prüfung, 8 für den Hook.

### v0.076 — der Nachlauf des Fund-Suchers, und was er von gestern übrig ließ

**Der Agentenlauf nach v0.075 hat die Reparaturen selbst geprüft.** Ergebnis: **12 neue
Funde, 3 schwer** — und von den 19 Funden des Vortags waren **8 sauber behoben, 6 halb,
5 gar nicht.**

🔴 **Die Commit-Nachricht von `81e51ba` sagte „alle behoben". Das war falsch.**
Der Satz steht hier, weil er nicht stehen bleiben soll: eine Zusammenfassung, die mehr
behauptet als geprüft wurde, ist dieselbe Bauform wie ein Rechtstext, der mehr verspricht
als der Code tut.

#### 🔴 Der Arbeitsbaum-Check hat geraten statt gemessen

Er suchte in geänderten Zeilen nach acht Stichwörtern („Datenschutz", „Bestenliste", …).
**Beides nachgemessen, beides daneben:**
- **146 der 160 Zeilen** der Erklärung tragen keines dieser Wörter — darunter wörtlich
  die Sätze, um die es tags zuvor ging. Wer einen davon ändert und den Stand stehen lässt,
  bekam **keinen Fund**.
- **„Bestenliste" steht 13× in gewöhnlichem Code.** Von den letzten 14 Commits hätten drei
  den Check ausgelöst, **zwei davon zu Unrecht** — und weil die Prüfung seit v0.075 den
  Push blockiert, wäre der einzige Weg durch gewesen, `PRIVACY_STAND` auf heute zu setzen.
  **Damit wäre das Datum zum Build-Datum geworden und das Signal weg.**

➡️ Jetzt kommen die Zeilennummern aus den `@@`-Köpfen des Diffs und werden gegen den
echten Zeilenbereich der Erklärung gehalten. **Kein Stichwort mehr im Spiel.**

#### 🔴 Der Hook verbrauchte seinen Merker, bevor irgendetwas geprüft war

Der SHA-256 wurde geschrieben, **bevor** feststand, ob der Prüfer läuft. Stürzte er danach
ab, galt die Datei beim nächsten Mal als unverändert — **und wurde nie geprüft.** Ein
Merker, der die Prüfung ersetzt, statt sie auszulösen.
➡️ Der Hash wird jetzt erst **nach** einem Lauf gemerkt, der stattgefunden hat. Dazu:
alle geänderten Repos statt nur des ersten · `sw.js` zählt mit (der Prüfer liest sie) ·
ein nicht anlegbarer Merker-Ordner ist laut statt still.

#### 🔴 Von allem, was gestern in die Erklärung kam, prüfte kein Satz irgendetwas

Bestenliste, Art. 9, IP-Adresse, Push über Apple/Google, Grenzen des Löschens — **alle
ungesichert.** Sie hätten am nächsten Tag verschwinden können. *Genau die Geschichte, die
den Bestenlisten-Satz überhaupt in den Bericht gebracht hat: er stand elf Tage falsch da.*
➡️ Neu: `pruefe_zusagen()` — **was der Code tut, muss der Text sagen.** Vier Regeln, jede
mit einem Kennzeichen im Code.
➡️ Neu: `pruefe_handler()` — jedes `data-act` braucht seinen Zweig im Verteiler.
**Ein toter Knopf sieht aus wie ein Knopf.**

💡 **Und diese Regel hatte den Fehler sofort selbst:** das Kennzeichen `gewichtHinzu` war
geraten und gab es nie — die Art.-9-Regel prüfte nichts und sagte nichts. Nur die
Gegenprobe hat es gefunden. Jetzt meldet eine Regel, deren Kennzeichen ins Leere zeigt.

#### 🟡 Sechs weitere

**Die Erklärung widersprach sich selbst:** „Zwei Ausnahmen" stand vier Absätze über der
neu eingefügten dritten (Push). Jetzt drei, und dass man die dritte nicht selbst auslöst.
**Die Pflichtangaben-Prüfung las die ganze 549-KB-Datei** — Fundstellen außerhalb konnten
eine gelöschte Pflichtangabe maskieren (gemessen: „Speicherdauer" 6×, „Betroffenenrechte"
2×, **eine davon kam gestern durch die Reparatur eines anderen Fundes dazu**). Liest jetzt
nur den Abschnitt.
**Der Prüfstand blieb grün, wenn die Datenschutz-Skripte verschwinden** — jetzt rot.
**Vor der Anmeldung erschien die Navigationsleiste** — `gate` bleibt jetzt gesetzt.
**Der Export-Knopf stand ohne Konto da** und hätte eine leere Datei geladen.
**Der user_id-Rückfall an Discord** steht jetzt im Text.

#### ⚙️ Zwei Behauptungen ohne Mechanik

- `datenschutz-pruefen.py` verwies auf einen README-Abschnitt **„Der Datenschutz-Wächter",
  den es nie gab.** Das README hatte neun Zeilen und enthielt das Wort „Datenschutz" nicht.
  ➡️ Der Abschnitt steht jetzt da.
- Die Agentenrolle sagte **„Läuft nach jeder neuen APP_FASSUNG"** — im ganzen Vault gab es
  keine Stelle, die ihn startet. ➡️ Jetzt steht dort, was tatsächlich wann läuft.

#### 🧪 Die Gegenproben

**14 Fälle** für die Datenschutz-Prüfung (waren 4), **11** für den Hook (neu:
`werkzeuge/datenschutz-hook-gegenprobe.py`). Darunter die zwei, die den Arbeitsbaum-Check
festnageln: *eine Zeile ohne Stichwort im Abschnitt wird gesehen* — *eine Zeile mit
„Bestenliste" außerhalb löst nicht aus.*

**894 Prüfungen grün.**

## 2026-09-09

### v0.075 — die Datenschutzerklärung läuft ab jetzt mit

**Karls Ansage:** *„KI Agenten für Datenschutz Erklärung der sie immer aktualliesiert …
er muss zu jeder neuen version laufen. er soll auch prüfen ob das alles so legal ist."*

#### 🔴 Zwei Funde, beide sofort behoben

**1. Die Erklärung versprach etwas, das seit sechs Tagen nicht mehr stimmte.**
Beim Essen-Eintragen stand: *„Übertragen wird nur die Nummer, nichts über dich."*
Seit dem **03.09.** (v0.072, der neue Suchdienst) schickt die Textsuche aber **den
eingetippten Suchbegriff** an `search.openfoodfacts.org`. Wer „Protein Pudding Aldi"
tippt, schickt diesen Text an einen fremden Dienst.
➡️ **Die Suche steht jetzt als eigener Punkt in der Erklärung**, mit dem Hinweis, dass
Favoriten und Zuletzt *nicht* suchen — die stehen auf dem Gerät.

**2. `PRIVACY_STAND` stand auf dem 24. August**, obwohl der Text am 03.09. geändert
wurde. Unter einem geänderten Rechtstext stand ein altes Datum.
➡️ Jetzt der 9. September — und ab sofort schlägt die Prüfung an, sobald der Text
jünger ist als sein eigener Stand (`git log -L` auf `renderPrivacy`).

#### 🤖 Neu: `datenschutz-pruefen.py`

Läuft in Sekunden und prüft fünf Dinge: **unbekannte Ziele im Code** · **Stand vs.
letzte Textänderung** · **fehlende Pflichtangaben** (Art. 13 DSGVO) · **Versprechen,
die der Code widerlegt** · und was **nicht messbar** ist (Discord geht über eine
Supabase-Funktion hinaus, nicht aus dem Browser — das steht als Merkposten drin,
damit niemand denkt, es sei übersehen worden).

⚠️ **Kommentare werden vorher entfernt.** Ohne das schlug die Prüfung bei `wger.de` an —
der Host steht nur in einem Kommentar, der erklärt, woher die Übungsliste stammt; zur
Laufzeit geht dorthin nichts. **Eine Prüfung, die auf Kommentare anspringt, wird nach dem
dritten Fehlalarm nicht mehr gelesen.**

#### 🧪 `datenschutz-gegenprobe.py`

Baut Schadensfälle in eine Kopie ein — unbekannter Fremddienst · Textsuche ohne
Erwähnung · gelöschte Pflichtangabe · Zähldienst trotz „kein Tracking" — und verlangt,
dass jeder als **SCHWER** herauskommt. *(Vier zu diesem Zeitpunkt; in v0.076 sind es 14.)*
💡 **Ohne sie wüsste man nur, dass die Prüfung „OK" sagen kann** — nicht, dass sie
überhaupt in der Lage ist, „FEHLER" zu sagen.

#### ⚙️ Sie läuft von selbst

Ein `PostToolUse`-Hook im Vault (`werkzeuge/datenschutz-hook.py`) startet die Prüfung
nach einer Änderung an `index.html`. Gibt es Funde, kommen sie sofort zurück in die
Sitzung; gibt es keine, bleibt es still.

🔴 **Nachtrag 10.09.2026:** Der Satz stand hier zuerst als *„nach **jeder** Änderung"* —
**und war falsch, im selben Commit, der den Fund dazu enthielt.** Der Matcher
`Write|Edit` sah die Python-Patchskripte nicht, mit denen `index.html` hier fast immer
geändert wird. Behoben in v0.076: der Hook misst jetzt per SHA-256, **ob** sich etwas
geändert hat, statt zu fragen, **womit**. Seither stimmt der Satz.

🔴 **Der Hook hatte selbst genau den Fehler, den er finden soll.** Die erste Fassung gab
ihre Meldung mit `ensure_ascii=False` aus; ein Umlaut traf auf die cp1252-Konsole, der
`UnicodeEncodeError` landete im `except`, **und der Hook blieb still — obwohl der Prüfer
zwei Funde gemeldet hatte.** Gefunden nur durch die Gegenprobe, nie im Betrieb.

#### 🔎 Was die beiden Agentenläufe danach fanden

**Der Datenschutz-Wächter: 8 Funde. Der Fund-Sucher: 11.** Beide Berichte stehen im Vault
(`04-projects/gym-log-datenschutz-2026-09-09.md`, `…-funde-2026-09-09.md`).

##### 🔴 Die Bestenliste widersprach der Datenschutzerklärung

Im Text stand wörtlich: *„Andere Nutzer können deine Daten **nicht** sehen."*
Tatsächlich schiebt `bestenlisteSchieben()` bei **jedem** Abgleich Name und XP hoch, und
jeder Angemeldete liest die ganze Tabelle. **Das Wort „Bestenliste" kam in der Erklärung
kein einziges Mal vor.** Der falsche Satz ist vom 05.08., die Bestenliste vom 29.08. —
der Text wurde seitdem **zweimal angefasst**, ohne dass es auffiel.
➡️ **Karls Entscheidung: den Text richtigstellen, keinen Schalter.** Die Erklärung hat
jetzt einen eigenen Abschnitt „Die Bestenliste" — samt dem Hinweis, dass ohne Username
der vordere Teil der E-Mail-Adresse dort steht.

##### 🔴 An Discord ging die E-Mail-Adresse statt des Usernames

`supabase-meldungen.sql` las `u.email`, mit der Begründung *„Gym-Log hat KEINE
Benutzernamen"* — **die gibt es seit dem 28.07.2026**, und `username_taken()` liest sie
aus derselben Tabelle. Damit ging bei jeder Meldung eine direkt identifizierende Angabe
nach USA, obwohl die Erklärung „dein Username" versprach.
➡️ **Umgestellt.** Ohne Username stehen jetzt acht Zeichen der user_id statt einer Adresse.
⚠️ **Muss im Supabase-Dashboard neu eingespielt werden.**

##### 🔴 Vor der Anmeldung war die Erklärung nicht erreichbar

`render()` brach ohne Sitzung sofort ab. Man gab E-Mail, Username und Passwort ab,
**bevor man irgendetwas lesen konnte** — Art. 13 verlangt die Information zum Zeitpunkt
der Erhebung. ➡️ Die Anmeldemaske hat jetzt einen Hinweis samt Link, und
`view==='privacy'` ist vor dem Gate erreichbar.

##### 🔴 Und der Fund, der gegen die Arbeit von heute ging

**Der Fix am Suchweg war nur zur Hälfte richtig.** Die Ausweichsuche geht an
`world.openfoodfacts.org` — und für genau diesen Host stand drei Zeilen unter dem neuen
Absatz weiterhin *„Übertragen wird nur die Nummer"*.
💡 **Die eigene Prüfung wusste es sogar** — ihre Liste notiert den Host als „Barcode +
**Ausweichsuche**" —, konnte den Zweck aber nie vergleichen.

##### 🔴 Die Datums-Prüfung konnte die Änderung, wegen der sie läuft, nicht sehen

`git log -L` liest **committete** Historie; der Hook läuft als `PostToolUse`, also immer
**vor** dem Commit. Text ändern, Datum vergessen, committen, pushen — alles in einer
Sitzung, und nichts wurde rot.
➡️ Die Prüfung sieht jetzt **zuerst den Arbeitsbaum** (`git diff`) und erst danach die
Historie. Und wenn `renderPrivacy` umbenannt wird, meldet sie ihren **eigenen Ausfall**,
statt still `None` zurückzugeben.

##### 🔴 Der Hook sah genau die Änderungen nicht, die hier üblich sind

Der Matcher `Write|Edit` erfasst keine Python-Patchskripte — und so wird `index.html` in
diesem Projekt fast immer geändert. **Der CHANGELOG behauptete trotzdem „nach jeder
Änderung".**
➡️ Der Hook fragt nicht mehr, **womit** geändert wurde, sondern misst per SHA-256, **ob**
sich die Datei geändert hat. Das hält auch für `sed`, Editoren von Hand und alles, was
noch kommt.
➡️ Dazu: stürzt der Prüfer ab, **sagt der Hook das jetzt**. Vorher fiel ein Absturz still
unter den Tisch — und sah aus wie ein Prüfer ohne Funde.

##### 🟡 Fünf kleinere, alle behoben

**Art. 9** für Gesundheitsdaten (Gewicht, Schritte, Mahlzeiten) ergänzt · **die Grenzen
des Löschens** benannt (Discord-Nachricht, eigener Download) · **IP-Adresse** bei Suche
und Foto ehrlich genannt (*„nichts über dich"* war zu stark — eine IP ist personenbezogen,
EuGH *Breyer*) · **Push läuft über Apple bzw. Google** (USA), das stand nirgends ·
**der Export trägt jetzt Meldungen und Postfach mit**, damit „alles" auch alles heißt.

##### ⚙️ Und die Gegenprobe hängt jetzt an etwas

Sie war **nirgends verdrahtet** — das Einzige, was die zeichenketten-abhängigen Prüfungen
absichert, rief niemand auf. Jetzt laufen Prüfung **und** Gegenprobe am Ende von
`pruefungen.py` mit und gehen in dessen Rückgabewert ein: **wer hier rot ist, pusht nicht.**
Gegengeprüft — mit kaputter Erklärung wird der Prüfstand rot und nennt den Fund.
Die Gegenprobe selbst deckt jetzt **acht** Fälle ab statt vier; `pruefe_stand()` war
vorher die einzige Prüffunktion ganz ohne.

#### ⚖️ Was das Skript NICHT kann

Ob eine Formulierung rechtlich trägt, sieht kein `grep`. Dafür gibt es den Agenten
`datenschutz-waechter` (im Vault unter `.claude/agents/`): er prüft Rechtsgrundlagen,
Drittlandsübermittlung, Einwilligungen und ob der Text nach Art. 12 DSGVO verständlich
ist. **Er ändert die Erklärung nicht selbst** — er legt den Textvorschlag vor.

## 2026-09-06

### v0.074 — drei Checklisten aus Karls Reels, fünf davon gebaut

Karl hat drei Instagram-Reels transkribieren lassen und geschickt: eine UX-Checkliste
(Hick's Law), eine zu öffentlichen Endpunkten und Kosten, und fünf Anzeichen für eine
„hingevibte“ App. **Erst geprüft, dann gebaut** — der Bericht steht im Vault unter
`04-projects/gym-log-pruefung-checklisten-2026-09-06.md`.

⚠️ **Der wichtigste Befund war ein Nicht-Befund:** die Reels zielen auf Apps mit einem
Server, der Rechnungen bezahlt. **Gym-Log hat keinen.** Der KI-Schlüssel für die
Foto-Schätzung ist der eigene Google-Schlüssel im eigenen Browser, die Zeilensperre steht
überall, und die Meldungen haben seit dem 25.08. eine serverseitige Bremse. **Es gibt keine
Stelle, an der ein Fremder Kosten auf fremde Rechnung auslösen kann.**

#### 🎯 Ein Hauptknopf je Bildschirm (Hick's Law)

**Die Startseite konnte vier grüne `btn primary` gleichzeitig zeigen** — Fortsetzen, Starten,
Gewicht eintragen, Zu den Mahlzeiten — und alle sahen gleich wichtig aus. Genau der Fall aus
dem Reel: *„Entwurf speichern / Vorschau / Veröffentlichen“* nebeneinander.

- **`hauptKlasse()` vergibt Grün genau einmal.** Rangfolge: laufendes Training › heutiger
  Plan › wiegen › essen. Wer nicht Erster ist, wird zum ruhigen Zweitknopf.
- ⚠️ **Die Reihenfolge der Aufrufe im Quelltext IST die Rangfolge** — wer die Blöcke
  verschiebt, verschiebt auch, was grün ist. Steht als Warnung im Code.
- ✅ **`Verwerfen` bleibt aussen vor**: die gefährliche Handlung war schon vorher richtig
  leiser als die harmlose. Das war der einzige Platz, an dem die Regel bereits stimmte.

#### ✨ Vier Punkte aus „fünf Anzeichen für eine hingevibte App“

**1. Rückmeldung beim Tippen.** Vorher: **6 `:active`-Regeln auf 7.686 Zeilen.** Die meisten
Knöpfe und alle antippbaren Karten gaben beim Tippen gar nichts zurück. Jetzt ein
generischer Druckzustand für Knöpfe und Karten, mit Rücknahme bei „Bewegung reduzieren“.
⚠️ Bewusst weit oben im Stylesheet, damit die älteren, kräftigeren Regeln (`.mz-plus`,
`.food-plus`, `.zurueck`) ihre eigenen Werte behalten.

**2. Bildschirme öffnen leer.** 🔴 `let bestenliste = null` war eine reine
Arbeitsvariable — **nach jedem Kaltstart öffnete „Erfolge“ ohne Liste.** Jetzt wird die
letzte Liste im Gerät gemerkt und sofort gezeigt, die Auffrischung läuft dahinter.
⚠️ **Gemerkt wird nur eine echte Liste.** `false` heisst „die Tabelle fehlt“ und `null`
heisst „gerade nicht erreichbar“ — beides sind Aussagen über DIESEN Moment. Ein
gespeichertes `false` würde beim nächsten Start ein SQL anmahnen, das längst gelaufen ist.
🔴 **Und sie wird beim Abmelden geräumt** — sie enthält Namen anderer Leute und gehört
zum Konto, nicht zum Gerät. (Dieselbe Bauform wie die Push-Anmeldung, 30.08.2026.)

**3. Keine Ladeplatzhalter.** Jetzt Platzhalterzeilen in der Form des echten Inhalts, mit
leichtem Schimmern — **aber nur an den zwei Stellen, die wirklich aus dem Netz laden**
(Bestenliste, Essens-Suche). ⚠️ Bei der Foto-Schätzung bewusst nicht: dort kommt am Ende
ein einzelner Entwurf, drei Platzhalterzeilen wären ein Versprechen, das die App nicht hält.

**4. Kein Offline-Betrieb** — traf **nicht** zu, die App kann das längst. **Was fehlte: man
sah es nicht.** Jetzt ein ruhiger Streifen „Ohne Netz — Änderungen bleiben im Gerät“.
⚠️ Der Text behauptet bewusst **keinen Datenverlust**: `navigator.onLine` sagt nur „dieses
Gerät hat eine Verbindung“, und gespeichert ist ohnehin immer.

**5. Knöpfe warten auf den Server** — traf **nicht** zu. Die App ist lokal-zuerst; genau das,
was das Reel als Lösung vorschlägt, ist hier die Bauform.

#### 🤖 Der Fund-Sucher: fünf Funde, alle behoben — und zwei davon waren meine

⚠️ **Der Lauf ist an einem Sitzungslimit abgebrochen**, bevor ein Bericht kam. Er hatte
aber sieben Wegwerf-Proben im Prüfstand stehen lassen — **und die hatten schon gemessen.**
Die Proben sind entfernt, ihre Funde stehen hier.

**1. 🔴 Die Platzhalter kamen auch beim Barcode — und der endet in EINEM Entwurf.**
Ursache: die Unterscheidung Liste/Entwurf lief über den **Anzeigetext** (`/Datenbank/`).
Barcode und Textsuche melden aber beide *„Suche … in der Lebensmittel-Datenbank"*. Der
Barcode versprach damit drei Zeilen, die nie kamen.
➡️ Jetzt eine eigene Flagge `foodBusyListe`, die die aufrufende Stelle setzt.
💡 **Der Merkposten ist grösser als der Fehler:** eine Anzeige darf nicht davon abhängen,
was in einem anderen **Anzeigetext** steht. Der Text ist zum Lesen da, nicht zum Auswerten —
er ändert sich beim nächsten Umformulieren, und dann ist es still kaputt.

**2. 🔴 Das neue Offline-Band lag genau auf der Pausenuhr.** Nachgemessen: Band
372–406, Uhr 355–428. **Ausgerechnet während des Trainings**, wo die Uhr das Wichtigste auf
dem Schirm ist. ➡️ Das Band weicht der Uhr jetzt aus (`#timerbar.show ~ #offlineband`).

**3. 🟠 Das Räumen der Bestenliste sass im falschen Weg.** Es stand in
`kontoDatenRaeumen()` — der Fund-Sucher hat nachgezählt: **`clearSession()` wird siebenmal
gerufen, `kontoDatenRaeumen()` nur viermal.** Drei Wege löschten die Anmeldung ohne die
Liste, darunter das abgelaufene Token (*„Bitte neu anmelden"*). Meldet sich danach jemand
anderes an diesem Gerät an, sieht er bis zur ersten Auffrischung **die Liste des
Vorgängers.** ➡️ Umgezogen nach `clearSession()` — die eine Stelle, durch die alle Wege gehen.

**4. 🟡 Sagte der Server „die Tabelle gibt es nicht", blieb die gemerkte Liste liegen.**
Die App zeigte nach dem Auffrischen *„noch nicht eingerichtet"* und beim nächsten Kaltstart
wieder die alte Liste — **sie widersprach sich selbst, je nachdem wann man hinsah.**

**5. 🟡 `[data-go]` im Druckzustand war ein toter Selektor.** Diese App kennt kein
einziges `data-go`. Nachgezählt: vier Vorkommen im Quelltext, **alle vier waren die
Selektoren selbst.** Kostet nichts, tut nichts, fällt nie auf.

#### 🐛 Und ein Fund an meinen eigenen Prüfungen — dieselbe Bauform

Die neue Prüfung auf tote Selektoren lief über `document.styleSheets` und sprang mit
`if (r.cssRules) { …; continue; }` über **jede einzelne Regel** hinweg.
🔴 **Seit Chrome CSS-Verschachtelung kann, hat auch eine ganz normale Style-Regel ein
`cssRules`** — eine leere Liste, aber ein Objekt, und ein Objekt ist wahr.
**Die Prüfung meldete daraufhin „gar keine Attribut-Selektoren gefunden"** — also das
Harmlose —, obwohl sie in Wahrheit **nichts angesehen hatte.**
⚠️ Dazu sass im selben Sammler ein `catch`, das den Fehler geschluckt hätte. Beides
gerichtet: erst den Selektor lesen, dann nur bei echtem Inhalt absteigen — und ein Wurf
wird gemeldet statt verschwiegen.

#### 🤖 Der zweite Lauf: fünf weitere Funde, alle behoben

**1. 🟠 Abmelden während des Auffrischens schrieb die Liste des Vorgängers zurück.**
Genau die Lücke, die der Umzug nach `clearSession()` schliessen sollte — **auf dem
asynchronen Weg war sie weiter offen.** Zwischen den beiden `await` liegen zwei Netzrunden;
wer in der Zeit auf Abmelden tippt, räumt die Liste, und die danach eintreffende Antwort
schreibt sie seelenruhig wieder hinein. ➡️ Der Lauf merkt sich jetzt, **wer** ihn gestartet
hat, und prüft das nach dem Warten.

**2. 🟠 Der Druckzustand erreichte drei von vierzehn antippbaren Dingen** — und der
Kommentar daneben behauptete *„ALLE antippbaren Karten"*. 🔴 **Der Kommentar war falsch.**
Stumm blieben unter anderem **`.check`, der Satz-Haken — der meistgetippte Knopf im ganzen
Training**, dazu die Pausenuhr-Knöpfe, Chips, Icon-Knöpfe, Textlinks, Übungszeilen,
Themenkacheln und die Rangkarten. ➡️ Die Liste ist jetzt an der **Klick-Weiche**
ausgerichtet: wer dort steht, ist antippbar und gehört in die Regel.

**3. 🟡 Nach Ab- und Anmelden hing „Erfolge" bis zu 30 Sekunden im Platzhalter.**
Das Abmelden räumte die Liste, liess aber `bestenlisteZuletzt` stehen — die
30-Sekunden-Bremse griff weiter. **Und es sah exakt aus wie Laden**; der neue schimmernde
Platzhalter versprach sogar aktiv, dass gleich etwas kommt. ➡️ Eine Zeile.

**4. 🟡 Das Offline-Band lag bei laufender Uhr auf dem Toast** — dieselbe Kollision wie
mit der Pausenuhr, eine Ebene weiter. Nachgemessen: 11 px, und der Toast deckt mit z-index 60
die Oberkante zu. ➡️ 200 px statt 150 räumt beides.

**5. ⏭️ Offen und bewusst nicht gebaut: die gemerkte Bestenliste trägt kein Alter.**
Ohne Netz lässt die App den alten Stand stehen — richtig so. **Aber vorher stand dort
„Wird geladen …", jetzt stehen Zahlen.** Wer wochenlang offline ist, sieht seinen alten Rang,
als wäre er von eben. 🔴 **Das ist die Bauform in Reinform**, und die Reparatur
(`{ts, uid, rows}` statt nur `rows`) ändert, was im Gerät gespeichert wird — **deshalb liegt
sie als Entscheidung bei Karl**, nach der Regel vom 04.09.

#### 🐛 Zwei Funde an meinen eigenen Prüfungen — beide dieselbe Bauform

**a) Die Prüfung auf tote Selektoren sah gar nichts an.** Sie lief über
`document.styleSheets` und sprang mit `if (r.cssRules) { …; continue; }` über **jede
einzelne Regel** hinweg — seit Chrome CSS-Verschachtelung kann, hat auch eine ganz normale
Style-Regel ein `cssRules`: eine leere Liste, aber ein Objekt, und ein Objekt ist wahr.
**Gemeldet wurde „gar keine Attribut-Selektoren gefunden"**, also das Harmlose. Dazu ein
`catch`, das einen echten Wurf verschluckt hätte.

**b) Die erste Fassung der Druckzustand-Prüfung war genauso blind.** Sie suchte die
Selektornamen als **Text** im Quelltext — und fand sie im Nachbarblock (der
`prefers-reduced-motion`-Rücknahme) wieder. 🔴 **Die Gegenprobe hat es aufgedeckt:
Selektoren aus der Druck-Regel entfernt — alles blieb grün.**
➡️ Sie misst jetzt echt: sammelt aus dem Stylesheet alle Regeln mit `:active` **und** einem
wirklichen `transform`, legt für jedes der 17 antippbaren Dinge ein Probe-Element an und
fragt `matches()`. Was keine Regel trifft, fliegt auf.
💡 **Der Merkposten, der über diese App hinausgeht:** eine Prüfung, die Quelltext liest,
prüft, ob etwas **dasteht** — nicht, ob es **wirkt**. Bei CSS ist das fast immer zu wenig.

#### 🧪 Prüfungen 867 → 894

27 neue, **mit Gegenprobe an den Einbaustellen** — dreimal: für die fünf Neuerungen,
für die sechs Reparaturen aus dem ersten Lauf und für die fünf aus dem zweiten.
🔴 **Beim dritten Mal fielen zwei Prüfungen durch:** zwei Sabotagen blieben grün.
Genau daran ist Fund (b) oben aufgeflogen. Nach dem Umbau schlägt jede Sabotage an,
wiederhergestellt → 894 grün.
⚠️ **Eine bestehende Prüfung wurde umgeschrieben, nicht gelöscht:** der Ladehinweis der
Bestenliste war ein Satz und ist jetzt ein Platzhalter. **Die Absicht bleibt Wort für Wort
dieselbe** — „ungeladen“ darf nicht wie „leer“ aussehen.

#### 📋 Was bei Karl liegt (Supabase-Dashboard, nicht im Code)

- 🔴 **Es gibt keine Warnung bei ungewöhnlichem Verkehr.** Der Schaden ist ohne
  Rechnungskonto gedeckelt — aber „gedeckelt“ heisst: das Kontingent ist plötzlich weg und
  niemand weiss warum. *Settings → Billing*, zwei Minuten.
- 🟠 **`username_taken` ist öffentlich und ungebremst.** Muss offen bleiben (die
  Registrierung fragt damit), könnte aber eine Mengengrenze je IP bekommen.
- ❓ **Ist die E-Mail-Bestätigung an?** Aus = beliebig viele Konten. An = Supabase verschickt
  je Versuch eine Mail, und das Kontingent ist klein.

### v0.073 — Grabsteine: Gelöschtes bleibt gelöscht

#### 🪦 Der Datenverlust beim Abgleich, Schritt 1

Der Fund vom 03.09.2026: `vereinige()` liest eine Kennung, die auf einer Seite **fehlt**, als
*neu* — nicht als *gelöscht*. Wer eine Mahlzeit löschte und danach das andere Gerät aufmachte,
bekam sie zurück, mit demselben Zeitstempel. **Das sieht nicht nach Abgleich aus, das sieht
nach einem Gespenst aus.** Betroffen waren alle vier Listen mit Löschknopf: Einheiten,
Mahlzeiten, eigene Lebensmittel, Gewichte. Lag seit dem 27.08. — zehn Tage.

- **Beim Löschen wandert die Kennung nach `profile.geloescht`.** Der Abgleich nimmt nichts an,
  was dort steht — **und wirft aus dem eigenen Stand raus, was die andere Seite begraben hat.**
  ⚠️ Die zweite Richtung ist die wichtigere: ohne sie stünde das Gelöschte weiter in `basis`,
  `vereinige()` hielte die Kennung für bekannt, und der Filter liefe ins Leere.
- **Nach 90 Tagen räumt sich die Liste selbst auf** (`GRABSTEIN_TAGE`).
- 🟢 **Rein additiv** — kann nichts überschreiben, nur verhindern, dass etwas zurückkommt.
  Das schlimmste denkbare Ergebnis ist ein Grabstein zu viel, und den sieht man sofort.
- ⏭️ **Schritt 2 (Zeitstempel für Pläne und Einstellungen) ist bewusst nicht dabei** — der
  entscheidet neu, welcher Plan überlebt.

#### 🤖 Der Fund-Sucher: sieben Funde, und der erste traf die Prüfungen selbst

**1. 🔴 Alle 18 neuen Prüfungen blieben grün, wenn man die Grabsteine komplett abschaltete.**
Sie setzten `geloescht` von Hand und prüften nur den Abgleich — **dass beim Löschen überhaupt
ein Grabstein entsteht, war ungeprüft.** Der Agent hat es bewiesen: alle vier
`grabsteinSetzen`-Aufrufe entfernt → 860 ok, 0 fehlgeschlagen.
✅ **Sieben Prüfungen ergänzt, die echt klicken** statt den Zustand zu stellen — inklusive
„ein einzelner Klick begräbt noch nichts" (sonst wäre die Sicherheitsfrage wirkungslos) und
„der Grabstein überlebt das Speichern". Gegenprobe jetzt: **5 rot** statt 0.

**2. 🔴 Die XP-Begründung behauptete das Gegenteil dessen, was passiert.** Der Kommentar sagte,
ohne Abzug hätte dasselbe Löschen *nicht* je nach Gerät zwei Folgen. Doch — und zwar erst seit
es Grabsteine gibt: löscht das Handy eine Einheit, bevor der PC sie je gesehen hat, behält das
Handy die Punkte und der PC bekommt sie nie. ✅ **Kommentar an drei Stellen richtiggestellt,
Verhalten unverändert** — das ist eine Abwägung für Karl, keine Panne.

**3. 🟡 Der 90-Tage-Verfall stand als Tatsache da, ist aber eine Annahme.** Ein Gerät, das
länger als 90 Tage nicht offen war, hat den Eintrag noch. ✅ Als Restrisiko ausgeschrieben.

**4. 🟢 Tote Verzweigung in `ohneBegrabene`** (`Array.isArray(liste)?liste:[]` innerhalb eines
`if(!Array.isArray(liste))`) — las sich, als würde ein Nicht-Array durchgereicht. ✅ Behoben.

**Offen und Karl vorgelegt, weil es an Abgleich und Löschwegen rührt:** die XP-Abweichung ·
der Gewichts-Grabstein greift auf die Millisekunde, der Abgleich auf den Tag · „Alles
zurücksetzen" setzt keine Grabsteine · der Export trägt die Grabsteine jetzt mit.

**Prüfungen 842 → 867.**

## 2026-09-04

### v0.072 — Grün, die Mahlzeiten-Leiste, und sieben Funde des Fund-Suchers

#### 🎨 Nach Karls Entwurf nachgezogen

- **Grün** für Umschalter, Plus-Knöpfe und den großen Knopf unten — über `--ok`, nicht über
  `--accent`. ⚠️ `--accent` färbt die ganze App (Nav, XP-Balken, Links, jeden Hauptknopf);
  der Entwurf zeigt einen Bildschirm, keine neue Hausfarbe.
- **Die Mahlzeiten-Leiste** („Alle · Frühstück · …"). 🔴 Sie **filtert die Liste, sie wählt
  kein Ziel** — wohin das Essen geht, steht in der Überschrift und ändert sich nicht.
  Die Zuordnung kommt daraus, in welche Mahlzeit ein Lebensmittel bisher eingetragen wurde.

#### 🤖 Der Fund-Sucher: sieben Funde, alle grün durch 834 Prüfungen

**1. 🔴 Fehlermeldungen kamen im Listen-Schritt nie an.** `h =` statt `h +=` hat den roten
Kasten *„Hat nicht geklappt"* überschrieben, bevor er gezeichnet wurde. Betroffen: Barcode
ohne Netz · Datenbanksuche ohne Treffer · Netzfehler · **fehlgeschlagene Foto-Schätzung** ·
zu kurzer Suchtext.
⚠️ **Warum nichts rot wurde:** alle sechs Fehler-Prüfungen lasen die *Variable* `foodFehler`.
Keine sah nach, ob der Text auf dem Bildschirm ankommt.

**2. 🔴 Eigene Lebensmittel ließen sich nicht mehr löschen.** Die alte Zeile hatte ein ✕, die
neue Karte nicht — der Handler `data-delfood` wartete auf ein Element, das es nirgends mehr
gab. Zu `delfood` existierte **keine einzige Prüfung**.
✅ Das Kreuz ist zurück, **nur unter „Suchen"**: unter „Favoriten"/„Zuletzt" sieht man einen
Ausschnitt, und Löschen aus einem Ausschnitt löscht mehr, als man gerade sieht.

**3. 🔴 Ein fertiger Entwurf ging verloren, wenn man während der Wartezeit wegtippte.**
`holeBarcode()` behandelte seine zwei Erfolgsausgänge verschieden; der Foto-Weg fiel in die
Aufräumzeile. Beim Foto kostet jeder verlorene Versuch echtes Geld.
✅ Alle drei laufen jetzt durch `entwurfFertig()`. Wer weggegangen ist, wird **nicht
zurückgerissen** — der Entwurf bleibt liegen, ein Hinweis sagt Bescheid.

**4. + 7. 🔴 Die Zuordnung lief über den Namen.** Zwei Folgen, beide still:
- „Käse" (Gouda) und „käse" (Bergkäse) waren nicht unterscheidbar — eingetragen wurde der
  erste Treffer. **Die kcal sahen plausibel aus und stimmten nie.**
- Ein umbenanntes Lebensmittel riss die Verbindung zu allem, was vorher damit eingetragen
  wurde — und der Filter behauptete, man habe so etwas noch nie gegessen. **Das ist keine
  fehlende Auskunft, sondern eine falsche.**

✅ **`addMeal` schreibt jetzt die Kennung mit (`fid`).** Beide Wege gehen durch **eine**
Funktion `essenZuMahlzeit()` — was an zwei Orten stand, wird an einem repariert.
⚠️ **Alte Einträge haben kein `fid`**, ebenso alles aus Foto und Barcode ohne Merken.
Der Namensweg bleibt als Rückfallebene — er wird nur nicht mehr zuerst gefragt.

**5. 🔴 Eine Prüfung von heute Nachmittag prüfte nichts.** *„Der Suchtext überlebt den Wechsel
des Reiters"* hat **keinen Reiter gewechselt** — sie setzte die Variable und las das Feld aus.
Sie wäre grün geblieben, wenn genau das kaputtginge, was ihr Name behauptet.
✅ Jetzt wird geklickt: tippen → „Favoriten" → zurück → nachsehen.

**6. 🔴 Drei Kommentare behaupteten das Gegenteil des Codes** — darunter der Block *„Die
Mahlzeiten-Leiste ist bewusst nicht drin"*, **acht Zeilen über dem Code, der sie zeichnet.**
Dazu ein Satz über `data-pickfood`, der seit dem Umbau nicht mehr stimmte, und eine Zusage
über Bestandsdaten ohne `mz`-Feld, die von keiner Prüfung gedeckt war.

#### 🔬 Prüfungen 834 → 842, mit Gegenprobe

Acht neue, jede als Gegenprobe zu einem Fund. **Nachgewiesen:** alle vier Reparaturen
zurückgenommen → **5 Prüfungen rot**, danach wiederhergestellt → 842 grün.

⚠️ Nebenbei repariert: `foodBauen()` in den Prüfungen sicherte `foodFilter` nicht — eine
Prüfung hätte ihn an die nächste weitergereicht. Heute ging das gut, weil die Filter-Prüfung
die letzte war.


### v0.071 — „Essen eintragen" nach Karls Entwurf neu gebaut

Karl hat ein von GPT gezeichnetes Bild geschickt: *„so soll es gerne aussehen wenn man auf
essen eintragen geht"* — mit dem Hinweis, dass ein paar Sachen darin komisch dargestellt und
nicht wichtig sind.

**Übernommen:** Kopfzeile mit mittigem Titel und Barcode/Foto oben rechts · Drei-Wege-Umschalter
**Suchen / Favoriten / Zuletzt** · Suchfeld mit Lupe · Zeilen als Karten mit rundem Feld links,
kcal und Nährwerten (`7P 1K 6F`) rechts, rundem Plus · großer Knopf unten.

**„Zuletzt" ist neu** und ersetzt den „Nochmal"-Block, der am 03.09. weggefallen war.

#### 🔴 Drei Sachen aus dem Entwurf sind bewusst nicht drin

1. **Die Mahlzeiten-Leiste** („Alle · Frühstück · Mittagessen · …"). Seit dem 03.09. kommt man
   nur über einen Mahlzeiten-Knopf hierher, die Mahlzeit steht also fest, **bevor** hier etwas
   passiert — und seit heute steht sie in der Überschrift. Dieselben vier Namen als Filter
   daneben liest man als *„wohin geht das Essen"*: **zwei Quellen für dieselbe Angabe, die
   sich widersprechen können.** Genau der Fehler, den v0.070 behoben hat.
2. **Die Fotos der Lebensmittel.** Es gibt keine — weder in der App noch in der offenen
   Datenbank in brauchbarer Form. Statt eines erfundenen Bildes steht der **Anfangsbuchstabe**
   in einem Feld derselben Größe: die Zeile behält ihren Aufbau, ohne etwas zu behaupten.
3. **Die Überschrift „Beliebte Lebensmittel".** Beliebt bei wem? Die App kennt nur die eigene
   Liste; eine Beliebtheits-Reihenfolge wäre eine erfundene Zahl.

⚠️ **„Fertig" steht im Entwurf nicht und ist trotzdem geblieben** — er kam am 03.09. auf Karls
ausdrückliche Ansage. Ihn wegzunehmen, weil ein Entwurf ihn nicht zeigt, hieße eine Ansage
durch ein Bild zurückzunehmen.

#### 🔧 Was unter der Oberfläche dazu nötig war

- **`foodQ`** hält den Suchtext fest. Ohne die Variable wäre er nach einem Blick in die
  Favoriten weg — das Feld wird beim Reiter-Wechsel neu gebaut.
- **`food:new` und `food:dbsuche` lesen ihn jetzt aus `foodQ`** statt aus `#foodSearch`.
  🔴 Unter „Favoriten" und „Zuletzt" gibt es das Feld gar nicht, und `s?s.value:''` hätte dort
  **still einen leeren Namen weitergereicht.**
- **„Zuletzt" sucht über den Namen zurück in die Lebensmittel-Liste** und lässt weg, was es
  nicht mehr gibt. Mahlzeiten speichern einen Namen, keine Kennung — sonst stünde dort eine
  Zeile mit einem Plus, das ins Leere führt.

#### 🔬 Prüfungen 826 → 832, und eine umgeschrieben

Die neuen prüfen am gebauten Dokument: drei Umschalter-Felder mit genau einem aktiven ·
Titel und Barcode in der Kopfzeile · Favoriten zeigt nur Favoriten · **„Zuletzt" zeigt nichts,
was gelöscht wurde** · der Suchtext überlebt den Reiter-Wechsel · kein zweiter Mahlzeiten-Wähler.

🔴 **Eine bestehende Prüfung war kaputt, nicht der Code:** *„Der Knopf unter der Liste ruft die
Suche auf"* hielt den **Wortlaut** `dbSuche(s?s.value` fest. Durch die Umstellung auf `foodQ`
wurde sie rot, obwohl der Weg vom Knopf zur Suche vollständig war. **Eine Prüfung, die eine
Schreibweise festhält statt einer Verbindung, meldet jede Umbenennung als Fehler und keinen
einzigen echten.** Sie prüft jetzt den Zweig: ruft er `dbSuche` auf, und bekommt der Aufruf
überhaupt etwas mit?


### v0.070 — zwei Ansagen von Karl an der Ernährungs-Seite

**1. „der + button ist immernoch zu nah an der kcal leiste"**

🔴 **Nachgemessen statt geschätzt: es waren 0,0 px.** Der Ziel-Balken einer Mahlzeit stand
ohne jeden Abstand unter der Zeile mit dem Plus-Knopf — und der Knopf ist 44 px hoch und hat
einen Schlagschatten. Zwei Elemente, die sich berühren, liest das Auge als eines: der Balken
sah aus wie der Unterrand des Knopfes.

✅ **14 px dazwischen.** Der Balken bekommt einen eigenen Rahmen mit `margin-top`, nicht
`zielBalken()` selbst — die Funktion zeichnet auch die Eiweiß-Leiste weiter oben, und die
steht dort richtig.

**2. „wenn ich draufdrücke sollte oben stehm frühstück oder abenessen eintragen"**

Die Mahlzeit stand als Abzeichen **rechts neben** der Überschrift „Essen eintragen" — also an
der Stelle, an der auf allen anderen Seiten Zähler und Nebenangaben stehen. Sie ist aber keine
Nebenangabe: seit dem 03.09. kommt man nur noch über einen Mahlzeiten-Knopf hierher, und die
Mahlzeit ist **das Einzige, was diese Seite von den drei anderen unterscheidet.**

✅ **Jetzt steht sie in der Überschrift selbst:** „☕ Frühstück eintragen", „🥗 Abendessen
eintragen". Das Abzeichen daneben ist entfallen — zweimal dasselbe ist keine Betonung.

### 🔬 Drei neue Prüfungen, 823 → 826 — und diesmal mit Gegenprobe

⚠️ **Beide Änderungen werden am gebauten Dokument geprüft, nicht im Quelltext nachgelesen.**
Die erste **misst** den Abstand zwischen Knopf-Unterkante und Balken-Oberkante.

🔴 **Der Grund steht im Vault vom 03.09.:** eine Prüfung war grün, während die Gewichtskurve
ganz fehlte. **Ein Abstand, den niemand misst, ist genau die Sorte Fehler, die monatelang
unbemerkt bleibt** — es wird ja nichts rot.

✅ **Gegenprobe gemacht:** beide Änderungen zurückgenommen → **3 Prüfungen rot**, mit der
Meldung *„nur 0.0 px Luft zwischen Knopf und Balken"*. Danach wiederhergestellt, 826 grün.
**Die dritte Prüfung ist die Gegenprobe zur zweiten**: sie fällt, wenn das alte Abzeichen
neben der neuen Überschrift stehen bliebe.

## 2026-09-03

### v0.069 — der erste Agentenlauf seit dem 01.09., und er hat sich gelohnt

**Karls Frage am selben Abend:** *„wozu haben wir dann überhaupt den agenten?"* — berechtigt.
Er war seit dem 01.09. nicht mehr gelaufen. Angesetzt auf die rund 25 Änderungen dieses
Abends: **sechs Funde, drei schwer. Drei davon waren von diesem Abend, also von mir.**

#### 🔴 1. Der Favoriten-Stern kam nie auf das zweite Gerät

**`vereinige()` ist rein additiv über die Kennung** — was die Basis-Seite schon kennt, wird
komplett übersprungen. **Felder innerhalb eines Eintrags führt es nie zusammen**, und `fav`
ist genau so ein Feld. Der Stern wäre nur mitgewandert, wenn das ganze Lebensmittel neu ist:
also bei keinem, das je abgeglichen wurde.

🔴 **Der eigentliche Fund ist der Widerspruch im selben Dokument.** Am 02.09. stand die Grenze
sauber notiert (bei `letzteMenge`, `index.html:3347`). Am 03.09. schrieb ich 600 Zeilen weiter
das Gegenteil: *„wandert über `blobsZusammen` mit auf das zweite Gerät."* **Zwei Sätze, die
sich widersprechen, in einer Datei.**

✅ **Repariert über einen Zeitstempel `favAb`.** Ohne ihn ist es nicht lösbar: *„Stern gewinnt
immer"* wäre naheliegend und falsch — dann käme ein weggeklickter Favorit vom zweiten Gerät
ewig zurück. **Es gewinnt die jüngere Angabe, in beide Richtungen.**

#### 🔴 2. Beim Start gewinnt immer das lokale Gerät — und der Kommentar sagte, das könne nicht mehr sein

Im Quelltext stand: *„Diese Aufgabe gibt es seit dem 29.08. nicht mehr — der Auslöser ist
damit weg."* **Das war zu keinem Zeitpunkt richtig.** Es gibt zwei weitere Auslöser, die
beide `save()` rufen, bevor der erste Abgleich läuft:

- `comebackPruefen()` setzt bedingungslos `zuletztDa` (seit 27.08.)
- `aufgabeErledigen('auf')` beim ersten Öffnen (bis 29.08. und wieder ab 03.09.)

⚠️ **Damit ist `dirty` beim Start immer `true`**, und aus der dokumentierten Regel *„wer etwas
Ungesichertes hat, gibt vor"* ist in Wahrheit *„das zuletzt geöffnete Gerät gewinnt"* geworden.
Betroffen: Pläne, Einstellungen, `days`, `favs`, `skin`.

🔴 **Bewusst nicht nebenbei geändert.** Das zu reparieren heißt, an der Frage zu rühren,
welcher Stand bei Plänen gewinnt — mit Datenverlust als möglichem Preis. **Der falsche
Kommentar ist korrigiert, die Sache liegt Karl als Entscheidung vor.**

#### 🔴 3. Gelöschtes kommt zurück, sobald ein zweites Gerät mitspielt

`vereinige()` kennt keine Grabsteine: eine Kennung, die auf einer Seite fehlt, gilt als **neu**,
nicht als **gelöscht**. Betrifft Lebensmittel, Mahlzeiten, Einheiten und Gewichte — alle vier
haben einen Löschknopf. **Liegt seit dem 27.08. da**, wird durch Fund 2 verschärft.
🔴 **Ebenfalls nicht nebenbei geändert** — Grabsteine sind ein eigener Umbau. Liegt Karl vor.

#### 🟡 4. Meine eigene Prüfung von heute deckte einen von acht Pfeilen ab

*„Jeder Zurück-Pfeil sagt, wohin er führt"* zeichnete **eine** Ansicht und nahm den ersten
Treffer. **Der Name behauptete acht, geprüft wurde einer** — dieselbe Bauform wie „Brock steht
links vom Ring" wenige Stunden vorher. ✅ Geht jetzt über `APP_QUELLE` und prüft alle Aufrufe.

#### 🟡 5. Ein Kommentar erklärte gelöschten Code, den es wieder gibt

In `gewichtVerlaufHTML()` stand, `GW_FENSTER`, `gwFenster` und `weightImFenster()` seien „mit
der Kurve gegangen". **Alle drei sind da und in Betrieb** — die Kurve kam eine halbe Stunde
später zurück, der Satz blieb. **Er hätte bei der nächsten Durchsicht dazu geführt, drei
benutzte Bausteine als toten Code aufzuräumen.** Dieselbe Bauform wie `APP_FASSUNG` am 31.08.

#### 🟢 6. Die alte Tagesaufgabe verschluckte 10 XP

Ein Gerät, das den 03.09. übersprungen hat, trägt noch `ein:true`. `aufgabeXP` schlug im
neuen Katalog nach, fand nichts und zählte **0** — der Haken kam herüber, die Punkte nicht.
✅ `ALTE_AUFGABEN = { ein: 10 }`.

---

**823 Prüfungen (818 → 823), 0 rot.** Gegenprobe an beiden Enden gemacht: der Abgleich
ausgebaut → rot, der Zeitstempel an der **Aufrufstelle** ausgebaut → rot. *Eine Prüfung, die
nur die Funktion abdeckt und nicht ihren Einbau, ist die Hälfte wert.*

### v0.068 — die Kurve ist zurück, und bei den Bildern war wirklich etwas kaputt

🔴 **Ein Fehler von mir, den Karl gemeldet hat:** *„The Weight Progress Chart is missing."*

Seine Ansage von vorhin lautete *„die kurve für gewicht soll nicht im verlauf stehen, nur der
gewicht verlauf an sich, die eintragungen"* — **gemeint war verschieben, nicht wegwerfen.**
Ich hatte den Satz als „Kurve weg" gelesen und sie samt Zeitraum-Wahl und elf Prüfungen
gelöscht. **Der Unterschied im Satz ist ein einziges Wort:** „nicht im Verlauf" sagt, wo sie
nicht hingehört — nicht, dass es sie nicht geben soll.

✅ **Zurückgeholt** (aus `778f9ac`), und zwar dorthin, wo gewogen wird: **in den Körper-Tab**,
mit der Zeitraum-Wahl. **Im Verlauf stehen weiterhin nur die Eintragungen.** Kurve beim
Wiegen, Liste beim Nachschlagen.
⚠️ **818 Prüfungen waren grün, als die Kurve fehlte.** Gemerkt hat es Karl, nicht der
Prüfstand — es gab keine Prüfung dafür, dass die Kurve überhaupt irgendwo steht. Jetzt gibt
es eine.

#### 🖼️ Die Bilder — nachgemessen, nicht geschätzt

Karl: *„fix image aspect ratios and distortion."* Die neun Brock-Bilder:

```
brock-3   189 x 256   0,738  (hochkant)
brock-5   256 x 224   1,143  (quer)
```

🔴 **`monster()` setzte nur die Breite**, die Höhe kam aus `height:auto`. Bei 64 px Breite war
Brock **je nach Rang 56 bis 87 px hoch — 55 % Unterschied.** Die Karte sprang beim
Rangwechsel, und er wirkte mal groß, mal geduckt.
✅ **Feste Box `size × size` mit `object-fit:contain`**, dazu `width`/`height` als Attribute,
damit der Browser den Platz vor dem Laden freihält.
⚠️ **`contain`, nicht `cover`** — Karl hatte `cover` vorgeschlagen. `cover` füllt die Box und
**schneidet dafür ab**; bei einer Figur mit Kopf und Füßen wäre genau das der Schaden.

#### Und der Rest vom Abend

- ⬆️ **Kopfzeile über Brock** — Flamme, „Heute" und das Tagesziel stehen wieder oben,
  Brock darunter. *(Zweite Änderung an derselben Stelle an einem Abend; die jetzige ist die
  stimmigere: die Zeile trägt zwei Zahlen, die zum Ring gehören, nicht zu Brock.)*
- ➕ **Das Plus in den Mahlzeiten-Knöpfen ist ein SVG geworden.** Am CSS lag es nicht —
  `align-items:center` stand schon da. **Ein „+" ist eine Glyphe** und sitzt an der
  Schriftlinie, nicht mittig in ihrer Box. Zwei Striche als SVG haben diesen Bezug nicht.
- 📏 **Mehr Luft** in den Mahlzeiten-Blöcken (16 px statt 14, Einträge 11 statt 9).
- 🗑️ **Der 7-Tage-Schnitt hat keine eigene Karte mehr** (Karls Ansage). Die Rechnung dahinter
  bleibt — der Regelkreis weiter unten arbeitet damit.

---

### v0.067 — Karls XP-Werte, und eine Grenze, die nie ausgerechnet worden war

**Karls Ansage:** Gewicht **+10**, Mahlzeit **+10**, täglich reinschauen **+5**.
Deckel damit **25 → 40 XP.**

⚠️ **Das Reinschauen war seit dem 29.08. draußen** — auf Karls eigene Ansage damals:
*„man kann nicht jeden Tag XP kriegen für wenn man was gemacht hat, weil an manchen Tagen
machst du ja nichts."* Er hat es an diesem Abend zurückgeholt.
✅ **Die Prüfung von damals hat dabei getan, wofür sie da war:** der Umbau lief **rot**, statt
still durchzugehen. *Eine umgedrehte Entscheidung soll auffallen.*

🔴 **Der Einwand im Quelltext stand seit Wochen ohne Zahl da** — *„wüürde man die verbliebenen
größer machen, wäre Gigachad ohne Training erreichbar."* Nachgerechnet mit `xpForLevel(45)`:

| | | |
|---|---|---|
| **Level 45 (Gigachad)** | | **42.240 XP** |
| ohne Training, alte Regel | 10/Tag | 4.224 Tage = **11,6 Jahre** |
| ohne Training, neue Regel | 25/Tag | 1.690 Tage = **4,6 Jahre** |
| mit täglichem Training | 40/Tag | 1.056 Tage = **2,9 Jahre** |

➡️ **Die Sorge war überzogen.** Wer 4,6 Jahre lang jeden Tag die App aufmacht und wiegt, ohne
ein einziges Mal zu trainieren, ist kein Schlupfloch — das ist länger, als es diese App gibt.
Eine Einheit gibt weiterhin **260–380 XP**; Training bleibt der Hauptweg um ein Vielfaches.
💡 **Eine Grenze, die nie ausgerechnet wurde, war eine Vermutung, keine Grenze.**

- 🗑️ **Der Zähler „Noch X Aufgaben offen." ist weg** (Karls Ansage). Er stand unter einer
  Liste, in der jede Zeile ihren Stand schon selbst zeigt — und die Kopfzeile nennt
  „X von 40 XP". Dieselbe Auskunft ein drittes Mal, in Worten.

### v0.066 — die Suche hakte, und zehn Sachen an der Ernährung

**Karls Meldung, die alles andere überwog:** *„gerade hatte ich einen fehler als ich was
gesucht habe, als ich dann nochmal gesucht habe hat es sofort funktioniert … guck mal woran
das lag, das ist schlecht, davon können leute in zukunft genervt sein, sonst muss es länger
laden."*

🔴 **Nachgemessen, nicht geraten.** Fünf Anfragen an die alte Suche von Open Food Facts
(`cgi/search.pl`), von diesem Rechner aus:

```
Versuch 1: FEHLER 503 nach 348 ms      Versuch 4: HTTP 200 nach 698 ms
Versuch 2: FEHLER 503 nach  35 ms      Versuch 5: FEHLER 503 nach  56 ms
Versuch 3: FEHLER 503 nach  43 ms
```

**Vier von fünf abgelehnt.** Es ist keine Drosselung nach Anzahl — dann wären die späteren
dran gewesen, nicht die ersten. Die alte Perl-Suche lehnt unter Last zufällig ab, und ein
zweiter Versuch geht oft sofort durch. Genau Karls Erlebnis.

➡️ **Zwei Änderungen, in dieser Reihenfolge:**

1. **Der neue Suchdienst `search.openfoodfacts.org` ist jetzt der erste Weg.** Nachgemessen:
   **6 von 6 Anfragen durch, 240–400 ms.**
2. **Wer trotzdem scheitert, wird wiederholt** — erst der neue Weg noch einmal, dann die alte
   Suche als Ausweichweg. Karls Handel („sonst muss es länger laden") ist damit angenommen:
   im schlechten Fall bis zu ~1,5 s mehr, dafür keine Fehlermeldung, die beim zweiten Tippen
   von selbst verschwindet.

⚠️ **Die zwei Wege liefern verschiedene Formen** — der neue nennt die Trefferliste `hits` und
`brands` ein **Array**, die alte `products` und einen String. Ohne Weiche hätte `.split` mitten
in `.map()` geworfen und die **ganze Trefferliste wäre leer geblieben**: ein Fehlschlag, der wie
„nichts gefunden" aussieht. Dieselbe Bauform wie der Fund vom 01.09.

---

### Ernährung: der Weg zum Eintragen ist jetzt einer

- 🔴 **Eingetragen wird nur noch über die Mahlzeiten-Knöpfe** (Frühstück, Mittag, …). Der
  allgemeine Knopf „+ Essen eintragen" ist weg — auch der auf der Startseite, der führt jetzt
  zu den Mahlzeiten. **Damit steht die Zuordnung fest, bevor etwas eingetragen wird**; vorher
  wurde sie aus der Uhrzeit geraten.
- ⭐ **Favoriten statt „Nochmal".** Die Liste der zuletzt gegessenen Sachen ist raus, dafür hat
  jedes eigene Lebensmittel einen Stern. Favoriten stehen oben, unter einer eigenen Zeile.
  **Der Unterschied ist nicht die Anzeige, sondern wer entscheidet** — „Nochmal" riet aus dem
  Verlauf, ein Favorit steht, bis er weggeklickt wird.
- 🖐️ **Der Mahlzeiten-Knopf war 32×32 px** und ist jetzt **44×44** — Apples Mindestmaß für
  alles, was ein Daumen trifft. Er ist seit heute die einzige Tür, da zählt das doppelt.
  Dazu mehr Luft in den Blöcken und 14,5 px statt 14 px Schrift (Karl: *„die schrift dort und
  der button sehen so ein bisschen gequetscht aus"*).
- ⚪ **Die Mahlzeiten-Knöpfe sind weiß**, in beiden Themen — fest `#fff`, nicht die Kartenfarbe.
- 🧍 **Brock steht oben**, in eigener Karte über „Heute", mit seiner Sprechblase daneben.
  Der Ring rückt dafür in die Mitte seiner Karte.
- ✅ **Ein großer „Fertig"-Knopf unten** in der Essen-Ansicht, dazu ist „Eintragen" beim
  Mengenschritt größer geworden. Vorher führte nur das kleine „‹ Kalorien" oben links zurück.

### Erfolge, Verlauf, Navigation

- 📉 **Die Gewichtskurve ist raus.** Im Verlauf stehen nur noch die Eintragungen (Karls Ansage).
  Mit ihr sind `GW_FENSTER`, `gwFenster` und `weightImFenster()` gegangen — samt der elf
  Prüfungen für die Zeitraum-Wahl. **Prüfungen für gelöschten Code laufen entweder rot oder,
  schlimmer, grün gegen eine Attrappe.**
- 🏆 **Die Bestenliste steht ganz unten**, hinter dem Katalog. Nebenbei repariert: sie lädt aus
  dem Netz und war der einzige Block, der später nachwuchs — mittendrin schob er beim
  Eintreffen alles darunter nach unten, während man las.
- 🥇 **Neuer Erfolg: „Hundertmal gewogen"** (100 Eintragungen, 400 XP), mit eigenem Symbol.
  Weil `addWeight()` den heutigen Wert überschreibt statt einen zweiten anzulegen, sind
  100 Einträge auch 100 verschiedene Tage — nicht zu erschleichen.
- 📋 **Die Tagesaufgabe „Eingetragen" ist zwei Aufgaben geworden: „Mahlzeit" und „Gewicht".**
  🔴 **5 + 5 XP statt 10 + 10, und das ist eine Abwägung:** der Tagesdeckel liegt bei 25 XP,
  damit die Rangleiter nicht ohne Training erreichbar wird. Zwei Aufgaben à 10 hätten ihn auf
  35 gehoben. **Wer beides einträgt, bekommt genau die 10 XP von vorher** — nur in zwei
  Schritten sichtbar. Wer nur eines macht, bekommt 5 statt 10.
- ⬅️ **Alle acht Zurück-Links sind ein einheitlicher Pfeil geworden** — Icon statt Text,
  44×44 statt rund 20 px hoch. Das Ziel steht weiter im `aria-label`.

### Geprüft

**773 → 810 Prüfungen.** Neu darunter: der einzelne Fehlschlag, der wiederholt wird (Karls
Fall — die bisherige 503-Prüfung deckte nur den Dauerfehler ab), beide Antwortformen, die
Reihenfolge der Suchwege, Brocks Platz, die Knopfgrößen, die getrennten Tagesaufgaben und
der neue Erfolg in **beide** Richtungen (bei 99 zu, bei 100 auf).

🔴 **Gegenprobe gemacht, und sie hat einen eigenen Fund gebracht.** Testweise ausgebaut:
der Wiederholversuch, Brocks neuer Platz, die Bestenliste. Alle drei Prüfungen wurden rot —
aber beim ersten Anlauf blieb die Bestenlisten-Prüfung grün, **weil die Gegenprobe selbst
falsch war** (der Block landete noch weiter hinten statt vorn). Beinahe hätte ich eine
funktionierende Prüfung als Attrappe verworfen.
⚠️ **Und eine echte Attrappe kam dabei heraus:** die Prüfung *„Brock steht links vom Ring"*
prüfte nur, dass er im HTML **vor** dem Ring steht — nach dem Umzug nach oben blieb sie grün,
obwohl Brock gar nicht mehr neben dem Ring sitzt. **Der Name sagte etwas anderes als der
Inhalt.** Umbenannt und geschärft.

## 2026-09-02

### v0.065 — der Supabase-Test zielte auf die falsche Adresse

Karl, direkt nach v0.064: **wieder 401.** Der Authorization-Header allein hatte nicht
gereicht — Zeit, es nicht noch einmal zu vermuten, sondern direkt gegen Supabase zu
testen (curl, mit dem echten Schlüssel aus dem Quelltext):

```
/rest/v1/                               -> 401 "Secret API key required"
/rest/v1/gymlog_data?select=id&limit=1  -> 200 []
```

🔴 **Die nackte API-Wurzel ist im neuen Supabase-Schlüsselsystem extra abgeriegelt** — sie
verlangt einen `secret`-Schlüssel, unabhängig von jeder Kopfzeile. Der `publishable`-Schlüssel
der App (derselbe, der überall sonst funktioniert) darf sie gar nicht ansprechen. Eine echte
Tabelle geht damit tadellos.

**Der Test zielt jetzt auf `gymlog_data?select=id&limit=1`** — denselben Weg, den `cloudPull()`
längst geht, nur ohne Anmeldung. RLS lässt anonym ohnehin nichts zurück (`[]`), das ist hier
gewollt: es geht nur um „kommt eine Antwort", nicht um Daten.

**Eine neue Prüfung hält jetzt die Form fest** (806 → 807): das Ziel muss eine echte Tabelle
sein, nicht die blanke Wurzel — sonst wäre der nächste Umbau wieder nur eine Kopfzeile von
demselben Fehler entfernt gewesen.

### v0.064 — der Supabase-Test im Admin-Panel hatte selbst einen Fehler

Karls Meldung vom Handy, direkt nach dem ersten Ausprobieren von „Verbindung testen"
(v62): Open Food Facts grün, **Supabase „Antwort 401"**.

🔴 **Der Test schickte nur den `apikey`-Header, kein `Authorization`.** Jeder andere
Supabase-Aufruf in der App (`authHeaders()`) schickt beide — ohne `Authorization` weist
Supabase die Anfrage ab, bevor sie überhaupt bei den Daten ankommt. Jetzt ruft der Test
`authHeaders(false)` auf, denselben Weg wie der Rest der App.

⚠️ **Und meine eigene Prüfung dazu hätte das nicht gefangen** — sie prüfte nur, dass
irgendein Aufruf passiert, nie welche Header dabei sind. Neue Prüfung dazu (805 → 806),
die genau das nachmisst; Gegenprobe bestanden.

### v63 — Anfänger bekommen Ganzkörper vorgeschlagen, nicht Push/Pull/Legs

Karls Ansage: *„für anfänger im ersten halben jahr/ ersten monate zb sollte immer ein
ganzkörper training und nur 3 Trainingstage drinne haben"*. **Änderbar, nicht erzwungen** —
seine eigene Ergänzung dazu.

**Eine neue Frage, direkt nach „Bau ihn für mich":** *„Wie lange trainierst du schon?"* —
Anfänger (< 1 Jahr), Fortgeschritten (1–3 Jahre), Erfahren (> 3 Jahre). Die letzten beiden
sind meine Ergänzung, Karl hat die Auswahl bewusst offengelassen.

Wählst du **Anfänger**, werden 3 Tage und ein echter **Ganzkörper-Split (A/B im Wechsel)**
nur **vorausgewählt** — im nächsten Schritt kannst du weiterhin 2 bis 6 Tage wählen, die
Vorgabe ist kein Käfig.

🔴 **Kein Push/Pull/Legs unter neuem Namen** — zwei eigene Trainingstage mit je einer
Kniebeuge- oder Beinpressen-Variante, Bank- oder Schulterdrücken, einem Rücken-Zug und
Rumpf, bewusst machine-lastiger als die anderen Splits (Latzug statt Klimmzüge, Beinpresse
als Alternative zum Kreuzheben) — der erste Kontakt mit dem Gym soll nicht an einer Übung
scheitern, die Körperspannung voraussetzt, die noch niemand aufgebaut hat. Bei 3 gewählten
Tagen wechseln sich die zwei Tage von selbst als A/B/A ab.

**9 neue Prüfungen (796 → 805)**, inklusive einer, die genau das prüft, was heute mehrfach
schiefging: dass die **Zusammenfassung** vor dem Erstellen denselben Split zeigt wie das,
was tatsächlich gebaut wird — beide laufen jetzt über dieselbe Funktion (`splitFuer()`),
nicht über zwei eigene Rechnungen.

### v62 — Fehlerfang, letzte Menge, Verbindungstest, Gewicht in den Verlauf

Vier Punkte aus der Ideenliste vom Nachmittag — drei davon nach Karls direkter Ansage
(*„ja änder das"*, *„kann aber bitte mit ins admin panel"*, *„den verlauf des gewichtes
kann bitte rueber in die einstellungen unter verlauf"*), einer nach seinem *„ok was
können wir da machen"*.

**🚨 Ein globaler Fehlerfang.** Bis heute gab es in der ganzen App **keinen einzigen**
`window.onerror` oder `unhandledrejection` — jeder Fehler aus einem Klick-Handler verschwand
in einer Konsole, die niemand aufmacht. Jetzt zeigt eine dritte Leiste (grau, unter „Neue
Fassung" und „Speichern geht nicht") *„Etwas ist schiefgelaufen — tippen für Details"*, mit
dem Fehlertext und einem Knopf zum Schicken über denselben Melde-Weg wie *„Problem melden"*.
Zwei Filter, damit sie nicht zur Tapete wird: bekanntes Browser-Rauschen (ResizeObserver,
ein fremdes Skript ohne jede Zeile) zeigt nichts, und dieselbe Meldung erscheint höchstens
einmal je Sitzung.

**🥣 Die zuletzt benutzte Menge.** Wer ein Lebensmittel aus der eigenen Liste wählt, bekommt
jetzt vorgeschlagen, was zuletzt eingetragen wurde, statt immer 250 g Quark als 100 g
anzuzeigen. ⚠️ Ehrlich begrenzt: läuft über `vereinige()` beim Abgleich, das bei einer
bekannten Kennung die eigene Seite ganz behält — isst du am Handy und hast das Lebensmittel
schon auf dem PC, zieht die neuere Menge vom Handy nicht sofort nach.

**🩺 „Verbindung testen" — im Admin-Panel, nicht für alle.** Drei Knöpfe, jeder schickt einen
echten Aufruf an Open Food Facts, Supabase und Google (mit einem winzigen Testbild) und zeigt,
was zurückkam. Direkte Antwort auf den größten Fund des Tages: das Essens-Foto war zwölf Tage
kaputt, weil der Weg nach dem Bauen nie wirklich abgeschickt wurde.

**📉 Der Gewichts-Verlauf ist umgezogen.** Kurve, Zeitraum-Wahl und alle Einträge stehen jetzt
unter Einstellungen → Verlauf, zusammen mit der Trainings-Geschichte. Im Körper-Tab bleibt nur,
was man beim Wiegen braucht: das Eingabefeld und die drei Kennzahlen (Start / Aktuell / kg seit
Start).

---

**22 neue Prüfungen (774 → 796).** Eine alte Prüfung ist mit umgezogen und an die neue Seite
angepasst (`view='body'` → `view='history'`), eine zweite Gegenprobe ist dazugekommen, die
prüft, dass die Kurve im Körper-Tab **nicht mehr** steht.

🔴 **Drei Funde in der eigenen Prüfarbeit, alle drei über Gegenproben aufgefallen, keiner beim
Schreiben:**
- Beim Verschieben der Kurve gab es kurz **zwei** Aufrufstellen für dieselbe Anzeige — eine
  Gegenprobe blieb grün, weil sie nur die eine traf. Auf **eine** Aufrufstelle vereinheitlicht.
- Der Testhelfer für das Admin-Panel stellte den Zustand zurück, **bevor** die asynchrone
  Prüfung fertig war — ein `try/finally` ohne `await` auf die Promise. Repariert.
- Dieselbe Gegenprobe zeigte einen echten Fall: entfernt man die Klick-Wache für „Verbindung
  testen", **stürzt die Seite ab**, statt still falsch zu laufen — der Knopf hängt an derselben
  Klick-Weiche wie alles andere, und ohne seine eigene Abfangzeile fällt er durch bis zu einer
  Stelle, die ein Feld voraussetzt, das er nicht hat.
 — die Kurven zeigen jetzt die Zeit, nicht die Reihenfolge

**Beide Punkte abgeräumt, die noch bei mir lagen.**

#### Die Punkte sitzen nach ihrem zeitlichen Abstand

Bisher standen sie gleichmäßig nebeneinander — der Abstand war die **Reihenfolge**, nicht die
Zeit. Bei „1 Jahr" sah eine Pause von drei Monaten aus wie ein einzelner Tag, und zwei
Wiegungen an aufeinanderfolgenden Tagen genauso breit wie zwei mit einem halben Jahr dazwischen.

🔴 **Die Kurve hat damit einen Verlauf behauptet, den es nicht gab.** Ein steiler Anstieg
konnte in Wahrheit ein halbes Jahr gedauert haben. Das betraf **alle drei Kurven**
(Gewicht, Übungsgewicht, Volumen) und war so, seit es sie gibt.

✅ **Das mittlere Datum unten gilt jetzt immer.** Es stand vorher nur bei ungerader Punktzahl
da — nur dann lag ein Punkt wirklich auf der Mitte. Mit der Zeitachse ist die Mitte der Fläche
immer ein echter Zeitpunkt (die Mitte zwischen erstem und letztem Eintrag). **Sie gehört keinem
Punkt, und genau deshalb stimmt sie.**

⚠️ **Zwei Fälle fallen bewusst auf den alten Maßstab zurück:** wenn keine Zeitstempel dabei
sind, und wenn sie zurückspringen. Die Übungs-Kurve folgt der Reihenfolge in `sessions`, und
dass die nach Datum sortiert ist, ist nirgends zugesichert — bei einem Rücksprung liefe die
Linie im Zickzack. **Ein falscher Abstand ist besser als eine Linie, die zurückspringt.**

#### Der Fehlertext ist kein Schalter mehr

Beim Barcode-Scannen entschied der Fehlerfang am **Wortlaut** der Meldung
(`/nicht in der Datenbank|keine Nährwerte/`), ob das Anlegen-Formular aufgeht. Das hat zweimal
Schaden angerichtet: am 01.09. rutschte ein 503 in genau diesen Wortlaut (das war v57) — und
die Reparatur musste ihre eigene Meldung so formulieren, dass sie *nicht* darauf passt.

💡 **Eine Fehlermeldung, deren Text man nicht mehr frei ändern darf, ist kein Text mehr,
sondern ein Schalter mit Tarnkappe.** Jetzt hängt die Weiche an einem Merkmal am Fehler
selbst; der Text darf sagen, was er will.

---

**Sieben neue Prüfungen (766 → 773).** Eine alte ist **abgelöst** worden, nicht gelöscht: sie
hielt fest, dass es bei gerader Punktzahl **kein** mittleres Datum gibt. Das war unter dem
alten Maßstab richtig — mit der Zeitachse ist ihre Voraussetzung weggefallen, und an ihrer
Stelle steht jetzt, dass die Mitte den **Zeitpunkt** nennt und nicht einen Punkt.

🔴 **Und wieder eine meiner eigenen Prüfungen im ersten Anlauf falsch:** der Helfer, der die
Punkte aus der Kurve misst, griff den **Flächen**-Pfad statt der Linie — der hat zwei
zusätzliche Punkte, mit denen er unten zumacht. Fünf gemeldete Punkte, wo drei sind. **Rot aus
dem falschen Grund ist genauso wenig wert wie grün aus dem falschen Grund.**

### v60 — „Essen per Foto" hat noch nie funktioniert

Karls Meldung, mit Bildschirmfoto, beim **ersten echten Foto überhaupt**:

> Die KI antwortet nicht (400): The value 'json_schema' is not supported for 'type' at
> 'response_format'.

**Im Quelltext stand die Form eines anderen Anbieters.** `response_format: {type:'json_schema',
json_schema:{schema:…}}` ist die OpenAI-Schreibweise. Bei Googles Interactions-API ist `type`
die **Ausgabeart** (text, image, audio, number …), nicht das Schema-Format. Richtig ist:

```
response_format: { type:'text', mime_type:'application/json', schema:{ … } }
```

Sonst ist an dem Aufruf nichts falsch — Modell, Bildübergabe (`data` + `mime_type`) und das
Auslesen aus `steps[].type === 'model_output'` stimmen. **Es war die eine Zeile.**

🔴 **Der Merkposten ist größer als der Fehler.** Der Weg über Google ist am **21.08.2026**
eingebaut worden, und die Commit-Nachricht von damals sagt es selbst: *„Nicht geprueft: ein
echtes Foto mit echtem Schluessel."* **Zwölf Tage später hat es der erste Benutzer gefunden.**
Die Form war aus der Dokumentation geschrieben und nie abgeschickt worden.

⚠️ **Ehrlich zu den vier neuen Prüfungen (762 → 766): sie hätten das nicht gefunden.** Sie
halten fest, was in der Dokumentation steht — und daran hatte ich vorher auch geglaubt. Was
gefehlt hat, war ein einziger echter Aufruf. Was sie können: verhindern, dass die Form beim
nächsten Umbau still wieder wegrutscht.

💡 **Was gut funktioniert hat:** die Fehlermeldung. Sie hat den Text des Servers wörtlich
durchgereicht — deshalb stand auf dem Bildschirm genau die Zeile, mit der der Fehler in fünf
Minuten zu finden war, statt „Hat nicht geklappt".

### v59 — die acht übrigen Funde des Agentenlaufs sind zu

Am 01.09.2026 hat ein Agent die App nach **einer bestimmten Bauform** durchsucht: *etwas kann
monatelang falsch sein, ohne dass irgendwo etwas rot wird.* Neun Funde, einer (der 503 beim
Barcode) wurde noch am selben Abend als v57 repariert. **Hier sind die restlichen acht.**

Karls Ansage: *„ja mach die weg heute wird gym log gemacht"*.

**Nichts davon ist auf dem Bildschirm zu sehen — das ist der Punkt.** Jeder einzelne Fall war
ein Fehler, der wie ein normaler Zustand aussah.

---

**🔴 Das Kalorien-Tagesziel überlebte den Abgleich nicht.** `blobsZusammen` führte nur die drei
Listen (Mahlzeiten, Lebensmittel, Schritte) zusammen. **Ziel, Assistenten-Haken, Zielart,
Wochen, Startdatum, Startgewicht und Schrittmodus standen in keinem Zweig** — sie fielen unter
„das eigene Gerät gewinnt", und wenn die Gegenseite gar kein `kcal` hatte (ein Cloud-Stand von
vor dem 23.08.), wurde ein frisches Objekt ohne sie gebaut. **Für dich sah das aus wie ein
zurückgesetztes Handy:** der Einrichtungs-Assistent stand wieder da.
Die Regel ist bewusst eng — übernommen wird nur, was auf der eigenen Seite **fehlt**. Ein Ziel,
das schon steht, wird nicht überschrieben; sonst käme das alte Ziel vom zweiten Gerät zurück,
sobald es sich meldet. Der Assistenten-Haken ist die Ausnahme und geht ODER: einmal durch ist
durch.
*Der Fund davor war derselbe (27.08., Tagesaufgaben und Mahlzeiten) — repariert wurde damals,
was gemeldet war. Das Tagesziel stand nicht auf der Liste.*

**🔴 `DB.set` war der einzige Schreiber ohne Fehlerfang** — ausgerechnet der für Pläne,
Einheiten und Profil. `save()` schreibt fünf Schlüssel und ruft **danach** den Abgleich: warf
der zweite (Speicher voll, privater Modus), stand der erste, die drei danach fehlten, und in
die Cloud ging gar nichts. **Auf dem Bildschirm sah alles richtig aus** — der Wert stand ja in
der Variablen. Weg war er erst nach dem nächsten Neuladen.
Jetzt meldet `DB.set` zurück, ob es geklappt hat, `save()` läuft in jedem Fall durch, **der
Abgleich in die Cloud läuft weiter** (dann ist sie der einzige Ort, an dem der Satz noch
ankommt) — und oben erscheint eine **rote Leiste, die stehen bleibt**. Bewusst kein Toast: der
ist nach 1,8 Sekunden weg, und wer gerade eine Wiederholung eintippt, sieht ihn nicht.

**🟡 „Kein Empfang" wurde als „Die Bestenliste ist noch nicht eingerichtet" angezeigt** — samt
Verweis auf `supabase-bestenliste.sql`. Das ist keine ausbleibende Antwort, das ist eine
**falsche Arbeitsanweisung**: du setzt dich an SQL, das längst richtig ist. Ursache war die
erste Zeile — die Token-Prüfung gibt auch bei Netzfehler und bei jedem 5xx `false` zurück, und
`false` heißt hier „gibt es serverseitig nicht". Jetzt heißt `false` nur noch **404**, alles
andere ist „gerade nicht" und lässt den alten Stand stehen.

**🟡 Eine abgewiesene Meldung verstopfte die Warteschlange für immer.** Sie blieb vorn stehen,
und alles dahinter kam nie mehr los — bei einem wiederholbaren Fehler dauerhaft. Du sahst
„Danke! Meldung ist raus.", danach 1,8 Sekunden einen Fehler, und dann kam nie wieder etwas an.
Jetzt wird zwischen **4xx** (der Server nimmt sie nie an → beiseite legen, der Rest kommt
durch, und du bekommst es gesagt) und **5xx** (nur gerade überlastet → alles bleibt liegen)
unterschieden. Die beiseitegelegten Meldungen sind nicht weg, sie stehen im Gerät.
Dazu: das Wort `GYM_BREMSE` wird jetzt gegen `supabase-meldungen.sql` gehalten. Wird es dort je
umformuliert, gilt die Drosselung als harter Fehler — und die Schlange steht.

**🟡 Ein nicht erreichbarer Namens-Test hieß „Name ist frei".** Netzfehler, 404, 403 und eine
echte Antwort kamen alle als `null` zurück. Jetzt gibt es einen dritten Wert für **„konnte
nicht fragen"**, und die Registrierung sagt es. *Sie bricht bewusst nicht ab* — die Funktion
könnte in der Datenbank schlicht fehlen, und dann käme niemand mehr in ein Konto.

**🟡 Der Barcode-Leser war das Einzige, was nicht offline funktionierte.** `zxing.min.js`
(336 KB, der iPhone-Weg zum Scannen) und `icon.svg` standen nicht in der Vorlade-Liste. Auf
Karls Gerät fällt das nie auf — Chrome/Android nimmt einen eingebauten Weg. Es trifft genau
eine Person: frische Installation, iPhone, erster Scan im Keller-Gym.

**🟡 Ein kaputter Plan-Link machte gar nichts — und ließ sich nicht wiederholen.** Der
Fehlerfang war leer, und das `#p=…` wurde aus der Adresse geräumt, **bevor** entpackt wurde:
danach half auch Neuladen nicht mehr. Drei Fälle sahen identisch aus (Link abgeschnitten,
Empfänger hat eine alte Fassung, Teilen geht grundsätzlich nicht). Jetzt wird die Adresse erst
geräumt, wenn der Plan wirklich dasteht, und es erscheint ein Hinweis, der die drei Fälle
auseinanderhält.

**🟢 Zwei Datenbank-Funktionen standen in keiner `.sql` dieses Ordners** (`username_taken`,
`delete_own_account`). Wer das Supabase-Projekt aus diesen Dateien neu aufsetzt, bekommt eine
Installation, in der Konten grundsätzlich nur halb gelöscht werden. Neu:
**`supabase-funktionen.sql`**.
⚠️ Die Datei ist aus den Aufrufen in `index.html` geschrieben, **nicht aus der laufenden
Datenbank ausgelesen**. Vor dem Ausführen vergleichen — was live steht, gilt.

---

**33 neue Prüfungen (729 → 762)**, und drei davon prüfen nicht einen Fall, sondern die **Form**:

- Ein neues Feld in `profile.kcal`, das niemand in den Abgleich einträgt, wird rot.
- Eine Datenbank-Funktion, die gerufen, aber in keiner `.sql` angelegt wird, wird rot.
- Eine Datei, die `index.html` nachlädt und die nicht vorgeladen wird, wird rot.

**Jede Reparatur ist gegengeprüft** — ausgehängt und nachgesehen, ob die Prüfung rot wird und
dabei den *Schaden* nennt, nicht die fehlende Zeile.
🔴 **Dabei ist eine meiner eigenen Prüfungen durchgefallen:** die zum Barcode-Leser war grün,
obwohl die Datei aus der Liste heraus war — sie suchte im ganzen `sw.js`, und der Dateiname
stand auch im Kommentar darüber. Die zweite fand ihn nicht, weil `zxing.min.js` einen Punkt
mitten im Namen hat. **Beide repariert; ohne die Gegenprobe wären sie grün geblieben.**

## 2026-09-01

### v58 — die Gewichtskurve lässt sich jetzt auf einen Zeitraum stellen

Karls Ansage: „ich will das die kurve für das gewicht zeitlich einstellbar ist 1 woche
1 monat 1 jahr max“.

Über der Kurve stehen vier Knöpfe: **1 Woche · 1 Monat · 1 Jahr · Max**. Sie schneiden die
Kurve und die Spanne daneben zu. Voreingestellt ist **Max** — dasselbe Bild wie bisher, es
kommt also nichts weg, solange man nichts anfasst.

**Drei Entscheidungen, die man nicht sieht:**

⚠️ **Die Grenze zählt ab heute, nicht ab dem letzten Eintrag.** Wer sich drei Monate nicht
gewogen hat und „1 Woche“ drückt, sieht einen leeren Zeitraum — nicht die Woche von vor drei
Monaten unter der Überschrift „1 Woche“. Eine leere Woche ist eine Antwort; ein still
zurückgeschobenes Fenster wäre eine falsche.

⚠️ **Ein leerer Zeitraum ist kein toter Punkt.** Statt einer leeren Karte steht dort
„Kein Eintrag in diesem Zeitraum — eine Kurve braucht zwei“ **und der nächste Zeitraum, in
dem wirklich eine Kurve steht**, beim Namen genannt.

🔴 **„kg Differenz“ heißt jetzt „kg seit Start“.** Die drei Kästen oben zeigen weiterhin die
ganze Geschichte, die Kurve darunter nur noch den Zeitraum. Ohne das Wort „Start“ liest man
bei „1 Woche“ die Differenz eines halben Jahres als die der Woche — zwei Zahlen übereinander,
die sich widersprechen, und keine sagt, worauf sie sich bezieht. Die Liste „Einträge“ ganz
unten bleibt vollständig; dort will man auch alte Werte löschen können.

Der Zeitraum wird **bewusst nicht im Profil gespeichert**: das ist eine Blickrichtung, keine
Messung. Im Profil müsste er durch `blobsZusammen` und über zwei Geräte abgeglichen werden —
viel Maschinerie dafür, dass beim nächsten Öffnen ohnehin die volle Kurve das Richtige ist.

**Zwölf neue Prüfungen** (717 → 729). Sie prüfen den Filter allein **und** was in der Ansicht
ankommt — die Lehre vom selben Tag (v57) war eine, die nur an einer von zwei Stellen
eingebaut war.

✅ **Gegengeprüft, indem die Aufrufstelle ausgehängt wurde** (`weightImFenster` blieb dabei
unangetastet, damit die Probe den Einbau prüft und nicht die Funktion): vier Prüfungen werden
rot, die erste meldet genau den sichtbaren Schaden — `Max=7 Punkte, Woche=7`.

**Nicht angefasst, bewusst:** die Kurve setzt ihre Punkte weiterhin **gleichmäßig
nebeneinander**, nicht nach dem Abstand in der Zeit. Bei „1 Jahr“ sieht eine Pause von drei
Monaten deshalb genauso breit aus wie ein Tag. Das ist so, seit es die Kurve gibt, und gilt
für alle drei Kurven der App — es zu ändern ist eine eigene Sache und keine Zugabe zu dieser.


### 🔴 v57 — ein 503 beim Scannen schickte dich ins Abtippen

**Gefunden vom ersten Agentenlauf über die App** (9 Funde, dieser der schwerste).

`fetch` wirft bei einem 503 oder 429 **nicht**. Es kommt eine gültige Antwort, sie ist nur
leer. In `holeBarcode` fehlte die Abfrage `r.ok` — die leere Antwort rutschte durch
`!d.product` in die Meldung „Das Produkt steht nicht in der Datenbank.“

Und weil der `catch`-Block **am Wortlaut der Meldung** entscheidet, wie es weitergeht, ging
danach das Anlegen-Formular auf. **Ergebnis für den Benutzer: er tippt die vier Nährwerte
einer Packung ab, die die Datenbank längst kennt.** Kein Fehler zu sehen, nur unnötige
Arbeit — und Open Food Facts drosselt nach wenigen Anfragen hintereinander.

⚠️ **Die Lehre gab es schon.** Am 31.08. war genau dieses `r.ok` in `dbSuche` eingebaut
worden, nachdem beim Bauen echte 503er kamen. **Eingebaut wurde sie nur an der Stelle, an
der sie aufgefallen war** — dieselbe Datenbank, dieselbe Drosselung, zwei Aufrufstellen,
eine geprüft.

**Zwei neue Prüfungen** (715 → 717), und beide schauen auf `foodStep`, nicht nur auf den
Fehlertext:
- ein 503 beim Scannen darf das Anlegen-Formular **nicht** öffnen
- ein echtes „gibt es nicht“ muss es weiterhin öffnen, mit dem Barcode im Entwurf

✅ **Gegengeprüft, indem die Zeile wieder entfernt wurde:** die Prüfung wird rot und meldet
`Schritt=new` — also genau den Schaden, nicht nur eine fehlende Zeile.

## 2026-08-31

### 🔍 v56 — Essen suchen, wenn keine Packung da ist

**Karls Ansage:** *„wir brauchen eine datenbank für essen zum eintragen falls man keinen
qr code hat."*

**Die Datenbank hing längst dran — aber nur am Barcode.** Ohne Packung (loses Obst, Kantine,
Restaurant, oder schlicht: Verpackung schon weggeworfen) blieb genau ein Weg: alle vier
Nährwerte von Hand abtippen. **Das ist der Weg, den man einmal geht und danach nicht mehr.**

Jetzt steht unter der eigenen Liste ein Knopf: **🔍 „…" in der Datenbank suchen**. Antippen,
Treffer wählen, Menge angeben — derselbe Schluss-Schritt wie beim Barcode.

#### Drei Entscheidungen, die beim Bauen gemessen wurden

⚠️ **Gesucht wird auf Knopfdruck, nicht beim Tippen.** Open Food Facts drosselt spürbar —
beim Bauen kamen nach wenigen Anfragen hintereinander nur noch **503er**. Eine Suche bei jedem
Tastendruck wäre eine Reihe von Fehlschlägen statt einer Antwort. **Und im Keller-Gym ist
ohnehin kein Netz.**

🔴 **Treffer ohne Nährwerte werden gar nicht erst gezeigt.** Von den Produkten mit
Deutschland-Kennung hatte am 22.08. nur gut die Hälfte vollständige Werte. **Eine Liste, in der
jeder zweite Eintrag in eine Fehlermeldung führt, ist schlechter als eine kurze.**

💡 **Der Barcode wird mitgenommen, obwohl niemand gescannt hat.** Wer einen gefundenen Treffer
mit *„Auch in meine Liste aufnehmen"* behält, **trifft ihn beim nächsten Mal sofort per Scan** —
ohne Netz und ohne Suche.

#### 🔧 Die Umwandlung ist jetzt geteilt

`offNachDraft()` macht aus einem Open-Food-Facts-Produkt einen Entwurf — **beide Wege benutzen
sie**, Barcode wie Suche. Vorher stand die Rechnerei nur im Barcode-Weg.

⚠️ **Der Teil, der dabei am meisten wert ist: die Kilojoule-Umrechnung.** Nicht jedes Produkt
hat `energy-kcal_100g`, manche nur `energy_100g` in Kilojoule. **Ohne die Umrechnung stünde bei
einem solchen Treffer der kJ-Wert als kcal da — also gut das Vierfache.** Hätte die Suche ihre
eigene Rechnung bekommen, gäbe es diesen Schutz jetzt nur auf einem der beiden Wege.

#### 🗑️ Raus: der Satz über die fehlenden Essenstage

**Karls Ansage: „der satz raus".** Betroffen war:

> *„Die Gewichtskurve steht, aber es fehlen Essenstage: 0 von mindestens 4 in den letzten zwei
> Wochen."*

**Gleiche Behandlung wie beim Wiegungs-Satz vier Tage zuvor:** keine leere Karte, sondern gar
keine. 💡 **Beide sagten dasselbe — *du hast zu wenig eingetragen*.** Das weiß, wer einträgt,
ohne dass eine Karte es ihm vorrechnet; und wer es nicht tut, fängt deswegen nicht an.

#### ✅ Vierzehn neue Prüfungen — 701 → 715, alle acht Gegenproben rot

| Was kaputt gemacht wurde | Was rot wurde |
|---|---|
| Kilojoule-Umrechnung entfernt | *Fehlt kcal, wird aus Kilojoule umgerechnet* (+1 weitere) |
| Sackgassen-Filter entfernt | *Treffer ohne Nährwerte stehen nicht in der Liste* |
| 503-Abfrage entfernt | *Eine 503-Antwort wird als Fehler behandelt* |
| Mindestlänge entfernt | *Ein einzelner Buchstabe fragt gar nicht erst* |
| Barcode des Treffers weggelassen | *Der Barcode des Treffers wird mitgenommen* |
| `holeBarcode` rechnet wieder selbst | *Der Barcode-Weg benutzt dieselbe Umwandlung* |
| Karls Satz wieder eingebaut | *Der Satz steht nicht mehr im Quelltext* (+1 weitere) |
| Knopf-Aktion entfernt | *Der Knopf ruft die Suche auf* |

⚠️ **Eine 503-Antwort ist kein Netzfehler** — `fetch` wirft dabei **nicht**, es kommt eine
gültige Antwort mit `ok:false`. Ohne die Abfrage liefe die App in `d.products` einer
HTML-Fehlerseite und meldete „nichts gefunden", wo in Wahrheit gedrosselt wurde.

💡 **Gegen die echte Datenbank nachgemessen** (31.08., `haferflocken`): 24 Treffer, **alle 24
mit Nährwerten**, 0,7 s, deutsche Marken (Kölln, ja!, Crownfield).


### 🔔 v55 — die App sagt Bescheid, wenn eine neue Fassung bereitliegt

**Karls Ansage: „ok los".** Das war der Punkt, der seit dem 27.08. als *angeboten, nicht
gebaut* dastand.

**Das Problem war nie das Ausliefern, sondern das Ankommen.** Der Service Worker läuft auf
„Netz zuerst" und ruft `skipWaiting()` — neue Dateien sind sofort da. **Ein Fenster, das schon
offen steht, merkt davon nichts:** sein HTML ist geladen, und geladen bleibt geladen. Genau das
ist Karl am 27.08. zweimal passiert, einmal davon hat er es als Fehler gemeldet (*„es sind nur
2 Tutorials da"*) — **die App war nicht kaputt, sie war alt.**

Jetzt erscheint oben eine Leiste: *„Neue Fassung ist da — tippen zum Laden"*.

⚠️ **Sie lädt nicht von selbst neu.** Ein Neuladen reißt weg, was gerade eingetippt ist. Die
App übt dieselbe Vorsicht schon beim Sprung ins Postfach (*„läuft ein Training, bleibt sie
stehen"*). **Und mitten im Training erscheint sie gar nicht erst** — sie wird zurückgehalten
und kommt beim nächsten Bild danach.

💡 **Warum oben und nicht unten:** unten sitzen Reiterleiste und Pausenuhr — und die Uhr läuft
genau dann, wenn am wenigsten Platz für etwas Drittes ist.

⚠️ **Beim Zurückkommen wird nachgefragt**, höchstens alle fünf Minuten. Von selbst sieht der
Browser nur beim Navigieren nach — **eine PWA, die wochenlang im Hintergrund liegt, navigiert
nie.** Ohne diese Frage bliebe die Leiste bei genau dem Nutzer stumm, für den sie gebaut ist.

#### 🔴 Der Fund nebenbei: `APP_FASSUNG` stand auf `v32`

**22 Fassungen lang.** Die Zeile trägt seit jeher den Kommentar *„mit der Cacheversion in sw.js
gleichziehen"* — **und genau das ist seit v32 nicht passiert.** Jede Problemmeldung, die Karl
seit dem 27.08. geschickt hat, trug damit die falsche Nummer; wer ihr nachgegangen wäre, hätte
im falschen Stand gesucht.

💡 **Der Befund ist nicht die Zahl, sondern was sie festhielt:** ein Kommentar hält nichts fest.
Er stand die ganze Zeit daneben und hat 22 Mal nichts bewirkt. **Eine Prüfung tut es** — die
neue Prüfung *„APP_FASSUNG und die Cacheversion in sw.js ziehen gleich"* wird rot, sobald die
beiden auseinanderlaufen.

⚠️ **Und daran hängt mehr als die Meldenummer:** wird `sw.js` nicht hochgezählt, lädt der
Browser den Service Worker gar nicht erst neu — dann bliebe die neue Leiste **für immer stumm,
ohne dass irgendwo etwas rot wird.** Die Prüfung sichert also den Hinweis mit ab, nicht nur die
Nummer.

#### ✅ Acht neue Prüfungen — 693 → 701, alle fünf Gegenproben rot

⚠️ **Der Melde-Weg selbst ist nicht prüfbar:** `updatefound` und `statechange` hängen an
`navigator.serviceWorker`, und den gibt es unter `file://` gar nicht — der Prüfrahmen lädt aber
genau so. **Deshalb ist die Entscheidung ausgelagert** (`fassungsLeisteFaellig`), damit
wenigstens sie geprüft werden kann.

Geprüft wurde jede Prüfung gegen den kaputten Fall, nicht nur gegen den heilen:

| Was kaputt gemacht wurde | Was rot wurde |
|---|---|
| Trainings-Rücksicht entfernt | *Mitten im Training wird sie zurückgehalten* |
| Aufrufstelle in `render()` entfernt | *render() holt einen zurückgehaltenen Hinweis nach* |
| `sw.js` nicht hochgezählt | *APP_FASSUNG und die Cacheversion ziehen gleich* |
| `controller`-Abfrage entfernt | *Die Erstinstallation löst keinen Hinweis aus* |
| Reihenfolge am Klick vertauscht | *Der Klick schreibt weg, BEVOR er neu lädt* |

💡 **Zwei davon prüfen den Einbau, nicht das Teil.** Die Entscheidung allein wäre wertlos, wenn
`render()` sie nie abriefe — und die Gegenprobe entfernt deshalb die Aufrufstelle, nicht die
Funktion.

⚠️ **Was die Prüfungen nicht sagen können:** ob der Hinweis am Handy wirklich erscheint. Das
zeigt sich erst am **übernächsten** Deploy — beim nächsten ist die Leiste selbst das Neue, und
die alte Fassung im Fenster kennt sie noch nicht.

## 2026-08-30

### 🔍 v54 — die dritte Runde Durchsehen: Verlauf, Statistiken, Push-Anmeldung

**Keine Ansage von Karl.** Das ist der Posten, der seit v43 als *„noch nicht durchgesehen"*
dasteht. Drei Fehler, **keiner davon wäre durch Benutzen aufgefallen** — und alle drei geben
eine falsche Antwort auf eine Frage, die man der App wirklich stellt.

#### 1. 🏋️ Der Aufwärmsatz zählte im Übungs-Verlauf mit — überall sonst nicht

`exHistory()` ging über `e.sets`, während `volume()`, `doneSets()` und `prFor()` alle durch
`arbeit()` gehen. **Damit widersprachen sich zwei Seiten über dieselbe Einheit:** im Verlauf
stand *„4 Sätze"*, eine Ansicht tiefer *„5"*. Die Volumen-Kurve zeigte eine andere Zahl als
die Liste darüber.

🔴 **Der teuerste Teil war nicht die Anzahl, sondern das Gewicht.** Der Aufwärmsatz ist mit
70 % vorgeschlagen, aber eingetippt wird von Hand. Eine **100 statt 10** im Aufwärmfeld hob
*„Bestes kg"* und *„kg seit Start"* dauerhaft an — **ohne je als Rekord aufzutauchen**, denn
der Rekord-Weg hat die Aufwärmsätze schon immer ausgenommen. Der Fehler wäre also als
*„die Kurve stimmt nicht"* aufgefallen, nicht als das, was er ist.

#### 2. 📅 Ein Körpergewichts-Tag war im Jahresraster ein Ruhetag

Das Raster rechnete nur mit `volume()` — kg × Wdh. **Klimmzüge, Liegestütze, Dips, Plank,
Crunches: alle in der Bibliothek, alle mit Gewicht 0.** Also Volumen 0, also dieselbe Farbe
wie ein Tag, an dem gar nichts war. Und *„X Tage trainiert"* zählte sie ebenfalls nicht.

⚠️ **Das Raster beantwortet genau eine Frage** — *„bin ich drangeblieben?"* — und stand
deshalb bewusst ganz oben im Verlauf. **Ausgerechnet für den, der ohne Hanteln trainiert,
gab es die falsche Antwort.**

➡️ **Getrennt:** ob ein Tag zählt, entscheiden jetzt die Sätze. Wie dunkel er wird,
entscheidet weiter das Volumen. **Stufe 0 heißt ab jetzt ausschließlich „hier war nichts"** —
vorher hieß sie beides.
💡 Beiläufig mit raus: der Tooltip sagte *„1 Sätze"*. Derselbe Fehler wie *„Dreißig Wiegen"*
gestern, mit eigener Prüfung dagegen.

#### 3. 🔔 Die Push-Anmeldung überlebte das Abmelden — zweimal

Am 27.08. wurden drei Posten gefunden, die beim Abmelden liegenblieben (Postfach, offene
Meldungen, Gelesen-Liste). **Der vierte ist der, den `kontoDatenRaeumen()` gar nicht erreichen
kann:** die Push-Anmeldung liegt nicht im Browser-Speicher, sondern im Gerät **und** als Zeile
in `gym_push` — dort mit der Benutzer-id des Vorgängers.

| Folge | Was passiert |
|---|---|
| **Das Gerät brummte weiter** | Antwortet der Bot auf Karls Meldung, klingelt das Handy des Nächsten — und im Postfach steht nichts, denn das wurde beim Abmelden absichtlich geleert. |
| 🔴 **Der Nächste konnte Mitteilungen NIE einschalten** | `subscribe()` gibt bei gleichem Schlüssel **dieselbe `endpoint`** zurück. Das ist der Primärschlüssel von `gym_push` — das Anlegen wird damit ein *Ändern* an einer fremden Zeile, und das verbietet die Zeilensperre. |

⚠️ **Und die Fehlerbehandlung machte es schlimmer:** beim Fehlschlag löst die App die Anmeldung
im Gerät wieder auf — richtig so, sonst stünde der Schalter auf „an“ und es käme nie
etwas. Nur war das hier **die Anmeldung des
Vorgängers** — der war damit still abgemeldet, während seine Serverzeile stehenblieb.
Angezeigt wurde *„später nochmal"*, und später ging es genauso wenig.

✅ **Kein Text ist dabei je verlorengegangen:** der Push hat keine Nutzlast, der Satz steht
fest in `sw.js`. Es klingelte, es stand nur nichts drin.

🔧 Neu: `pushAbmelden()` ohne Toast, aufgerufen in `authSignOut()` **vor** `clearSession()`
(das DELETE braucht das Token) und in `deleteAccount()` vor dem Löschen der Daten — dort steht
*„alle Daten dauerhaft"*, dann darf auch nichts mehr klingeln.
⚠️ `on delete cascade` allein reicht nicht: es greift nur, wenn das Konto wirklich verschwindet.
Beim Ausgang `dataonly` bliebe die Zeile stehen.

#### 🐛 Ein Fund an den Prüfungen selbst

Die Reihenfolge-Prüfung (`pushAbmelden()` vor `clearSession()`) war zuerst **grün, obwohl sie
nichts prüfte**: über dem Aufruf steht ein Kommentar, in dem *„vor `clearSession()`"* als
Erklärung geschrieben steht. Die Suche fand den **Hinweis** statt des Aufrufs — und der Hinweis
steht immer vorne.
🔴 **Eine Prüfung, die sich am erklärenden Text festhält, ist grün, gerade wenn der Code falsch
ist.** Der Rumpf wird jetzt vor der Suche von Kommentaren befreit. Gegenprobe: den Aufruf hinter
`clearSession()` schieben → **1 rot**, mit der richtigen Begründung.

**Prüfungen 680 → 693.** Sechs Gegenproben, zusammen 10 rot — jede genau da, wo sie hingehört.

## 2026-08-29

### ✏️ v53 — zwei Textkorrekturen

**Karls Ansagen:**

1. ✅ **Der Hinweissatz unter der Bestenliste ist raus** (*„die Zahlen kommen von den Geräten,
   nicht vom Server …"*).
   ⚠️ **An der Sache ändert das nichts** — XP wird weiterhin auf dem Gerät gerechnet und
   hochgeschrieben. Es steht nur nicht mehr in der App. Der Hinweis lebt im Kopf von
   `supabase-bestenliste.sql` weiter, damit er nicht ganz verlorengeht.
   💡 Die Prüfung darauf ist mitgegangen — sie sicherte eine Zusicherung ab, die **ich**
   eingebaut hatte, nicht Karl.

2. ✅ **„Dreißig Wiegen" heißt jetzt „Dreißigmal gewogen".** Karl: *„das ist doch kein
   Deutsch."* Stimmt — **`Wiegen` als zählbare Mehrzahl gibt es nicht**, eine *Wiege* ist ein
   Kinderbett. Neue Prüfung: kein Erfolg darf mehr so heißen. Gegenprobe: alten Namen
   zurück → **1 rot**.

**Prüfungen 680** *(eine gestrichen, eine dazu).*

### 🏆 v52 — XP-Bestenliste auf der Erfolge-Seite

**Karls Wunsch:** *„Ich will ein XP-Leaderboard bei Erfolge drinnen. Soll die 10 User mit den
meisten XP anzeigen."*

Steht zwischen den Tagesaufgaben und dem Katalog — die Aufgaben sind *heute*, der Katalog ist
*insgesamt*, und die Liste vergleicht genau dieses Insgesamt. Platz, Name, XP; die eigene
Zeile ist markiert.

#### ⚠️ Das läuft erst, wenn Karl einmal SQL ausführt

XP und Namen anderer Nutzer standen bisher **nirgends** — der eigene Datenblock `gymlog_data`
ist per Zeilensperre auf den Eigentümer beschränkt und **bleibt es**. Es gibt deshalb eine
neue Tabelle: **`supabase-bestenliste.sql`**, einmal im Supabase-Dashboard ausführen.

💡 **Bis dahin stürzt nichts ab** — die Seite sagt, dass die Liste noch eingerichtet werden
muss. Drei Zustände, drei Anzeigen: *noch nicht geladen* · *geladen, aber leer* · *gibt es
serverseitig nicht*. **„Leer" und „ungeladen" zu verwechseln ist der klassische Fehler.**

#### 🔴 Warum eine eigene Tabelle und keine Sicht auf `gymlog_data`

Eine Sicht müsste die Zeilensperre umgehen und hätte damit Zugriff auf den **ganzen** Block:
Trainings, Gewichte, Mahlzeiten, Meldungen. **Ein Tippfehler in der Spaltenliste, und alles
davon steht in der Bestenliste.** Die neue Tabelle kann gar nicht mehr hergeben als das, was
ausdrücklich hineingeschrieben wurde: Name, XP, Zeitpunkt.
➡️ Dieselbe Lehre wie bei `email_for_username` am 24.08.

**Was sich damit ändert:** jeder angemeldete Nutzer sieht Namen und XP der anderen. Das ist der
Zweck — aber es ist eine Änderung, vorher sah niemand etwas vom anderen. **Keine
E-Mail-Adressen**, und der Name wird am `@` abgeschnitten, falls jemand keinen Benutzernamen
hat.

⚠️ **Die Zahlen kommen von den Geräten, nicht vom Server.** Wer will, kann seinen
Browser-Speicher ändern. Für eine Liste unter Freunden in Ordnung — es steht auch so auf der
Seite. Serverseitig nachrechnen ginge nur, wenn der Server die Einheiten kennt, und dafür
müsste `gymlog_data` geöffnet werden. **Der schlechtere Tausch.**

#### 🐛 Ein Fund an mir selbst: eine Prüfung, die hängt statt rot zu werden

Der Köder im Escaping-Test war zuerst `<img src=x onerror=alert(1)>`. Das führt den Einbruch
wirklich vor — **und genau deshalb war es unbrauchbar**: ohne `esc()` feuert es, und ein
`alert()` hält den Prüf-Browser an, bis die Zeitgrenze zuschlägt. **Die Gegenprobe wurde nicht
rot, sie hing 180 Sekunden und lieferte gar kein Ergebnis.**
➡️ **Eine Prüfung, die im Fehlerfall hängt statt rot zu werden, ist keine Prüfung.** Der Köder
ist jetzt ein harmloses `<i>` und beweist dasselbe.

**Prüfungen 671 → 680.** Gegenproben: das `split('@')` entfernen → **1 rot**; `esc()` entfernen
→ **1 rot**; `select=*` statt Spaltenliste → **1 rot**.

### 🗑️ v51 — die Wochen-Serie ist von der Startseite runter

**Karls Ansage:** *„1 Woche am Stück auf der Startseite kann raus."*

Die Karte mit der Zahl und den Kästchen daneben ist weg. **Der linke Block „Fortschritt"
besteht damit nur noch aus der Rang-Karte.**

⚠️ **Nur von der Startseite — sonst ändert sich nichts:**

| | |
|---|---|
| **Jahresraster im Verlauf** | bleibt — es *zeigt* dieselbe Sache, statt sie zu behaupten |
| **Erfolge „Vier am Stück" / „Acht Wochen"** | bleiben — die hängen an `besteWochenSerie()` |
| **Ess-Serie auf der Kalorien-Seite** | bleibt — andere Serie, andere Seite |

💡 **`wochenSerie()` selbst bleibt stehen**, obwohl sie damit **keinen Aufrufer mehr in der App
hat.** Sie ist getestet, sie meint etwas anderes als `besteWochenSerie()` (die laufende Serie
statt der längsten je), und diese Unterscheidung ist eine Falle, die schon zweimal gelöst
werden musste. 🔴 **Das steht so im Code** — wer sie wieder braucht, findet eine fertige
Funktion; wer aufräumt, weiß, dass nichts daran hängt.

**Prüfungen 669 → 671.** Zwei neue: dass die Karte **nicht** zurückkommt, und dass der Verlauf
**nicht** mit weggeräumt wurde. Gegenprobe: Karte wieder einbauen → **1 rot**.

### 🎚️ v50 — ein richtiger Kippschalter

**Karls Ansage:** *„ich will so einen richtigen Schalter für die beiden."*

**Aus den zwei Knöpfen sind zwei Kippschalter geworden** — grün und rechts, wenn an; grau und
links, wenn aus.

💡 **Warum das mehr ist als Optik:** ein Knopf mit *„Ausschalten"* sagt, was **passieren
würde**, nicht was **ist**. Man muss ihn lesen und dann gedanklich umdrehen. Ein Kippschalter
zeigt den Zustand selbst — den liest man, ohne zu lesen.

⚠️ **Ein leerer Knopf hat für eine Vorlesehilfe keinen Inhalt** — er wäre schlicht unsichtbar.
Der Schalter trägt deshalb `role="switch"`, `aria-checked` (der Zustand) und ein `aria-label`
(worum es geht). Wer Bewegung im System abgestellt hat, bekommt sie hier auch nicht.

#### ✅ Und diesmal ist das Ergebnis wirklich messbar

Beim Stretch in v47 musste der letzte Blick bei Karl bleiben — `getBoundingClientRect()` gibt
bei SVG-Formen die Geometrie **ohne** Strich heraus. **Hier sind es HTML-Elemente**, und da
liefert dieselbe Messung das volle Kästchen.

➡️ Die Prüfung misst deshalb, **wie weit der Knopf im An- und im Aus-Zustand vom linken Rand
sitzt**, und verlangt einen echten Versatz.
🔴 **Das fängt beide Richtungen der stillen Entkopplung:** CSS ohne Klasse *und* Klasse ohne
CSS. Beide Gegenproben ergaben denselben Befund — *Versatz nur 0,0 px*.

**Prüfungen 667 → 669.**

### ⚖️ v49 — zwei Erinnerungen auf der Startseite, beide abschaltbar

**Karls Ansagen:** *„Am besten morgens vor dem Essen. Zuletzt 103 kg am Fr., 28.08. — den Satz
bitte raus"*, *„den Reminder mit täglich wiegen soll man in den Einstellungen wegmachen
können"* und *„auf der Startseite soll auch ein Reminder sein für Essen eintragen, den man
auch einstellen kann."*

#### Der Satz ist raus

Er stand **jeden Tag** da und sagte **jeden Tag dasselbe**. Eine Erinnerung braucht keinen
Ratgeber — sie braucht ein Feld und einen Knopf.
ℹ️ **Auf der Kalorien-Seite bleibt der Hinweis stehen** — dort steht er einmal beim Eintragen,
nicht täglich auf der Startseite.

#### Zwei Erinnerungen, zwei Schalter

| | erscheint | verschwindet |
|---|---|---|
| **Heute wiegen** | solange für heute kein Gewicht drinsteht | nach dem Eintragen |
| **Essen eintragen** | solange für heute keine Mahlzeit drinsteht | nach der ersten Mahlzeit |

Beide lassen sich in den **Einstellungen** einzeln abschalten, ganz oben — es ist die einzige
Einstellung, die verändert, was man beim Öffnen als Erstes sieht.

⚠️ **Ohne Schalter wäre eine Erinnerung eine Aufforderung, die man nicht loswird.** Das ist der
Unterschied zwischen Erinnern und Nörgeln.

🔴 **Die Essens-Karte hat bewusst kein Eingabefeld wie die Wiege-Karte.** Ein Gewicht ist eine
Zahl, eine Mahlzeit braucht Name, Kalorien und Eiweiß — das ist eine Seite, kein Feld. Der Knopf
geht denselben Weg wie der auf der Kalorien-Seite.

#### 🔴 Die Stelle, an der es leise kaputtgegangen wäre: der Abgleich

Eine neue Einstellung im Profil fällt ohne eigenes Zutun unter *„alles andere kommt von
basis"* — also **vom eigenen Gerät**. Wer die Erinnerung am Handy ausschaltet, hätte sie am PC
weiter, und beim nächsten Schieben käme sie am Handy zurück. **Genau die Sorte Fehler, die am
27.08. Mahlzeiten und Tagesaufgaben verschluckt hat** (v45).

✅ **Die Schalter tragen deshalb einen Zeitstempel, und die spätere Entscheidung gewinnt.**
⚠️ **Nicht „Aus gewinnt"**, obwohl das naheliegt: dann käme man nie wieder an, solange ein
Gerät noch das alte Aus kennt.

**Prüfungen 658 → 667.** Gegenproben: den Schalter an der Karte ignorieren → **2 rot**; den
Abgleich die Schalter nicht mitnehmen lassen → **1 rot**.

### 🔴 v48 — kein XP mehr fürs bloße Öffnen der App

**Karls Ansage:** *„man kann nicht jeden Tag XP kriegen für wenn man was gemacht hat, weil an
manchen Tagen machst du ja nichts."*

**Er hat recht — und meine Antwort vom 26.08. war die schwächere.** Damals hatte ich genau
diesen Einwand selbst erhoben und ihn über die **Größenordnung** gelöst statt über ein Nein:
höchstens 30 XP am Tag, davon 5 fürs bloße Öffnen. Klein genug, um nicht zu tragen.

🔴 **Das war die falsche Stellschraube.** Eine kleine Belohnung für nichts bleibt eine
Belohnung für nichts — sie macht nur länger, bis es auffällt. **Wer die App 100 Tage lang nur
aufmacht, hatte 500 XP dafür, dass er nichts getan hat.**

✅ **„Reingeschaut" ist ersatzlos raus.** Es bleiben zwei Aufgaben, und **beide verlangen eine
Handlung**:

| | XP | |
|---|---:|---|
| ~~Reingeschaut~~ | ~~5~~ | ~~Die App heute geöffnet~~ — **entfallen** |
| **Eingetragen** | 10 | Gewicht oder eine Mahlzeit eingetragen |
| **Trainiert** | 15 | Eine Einheit abgeschlossen |

**Deckel 30 → 25 XP am Tag**, gegen 260–380 für eine Einheit.

⚠️ **Zurückgenommen wird nichts.** Wer die 5 XP an vergangenen Tagen bekommen hat, behält
sie — in dieser App wird kein Punktestand rückwirkend gekürzt (Regel vom 27.08.).
**Es gibt sie ab heute nur nicht mehr.**

💡 **Damit beantwortet sich auch die offene Frage vom 28.08.** (*„soll das Wiegen eine
Tagesaufgabe werden?"*): **nein, und es braucht auch keine** — Wiegen zählt bereits als
*Eingetragen*. Eine eigene Aufgabe dafür wäre genau die Aufblähung, gegen die Karls Ansage
sich richtet.

💡 **Ein Nebeneffekt, der ein Gewinn ist:** mit der Aufgabe fällt das Nachfassen beim
Zurückkommen in die App weg — und damit ein `render()` bei jedem Wechsel in die App, das
laufende Eingaben wegreißen konnte.

#### 🔴 Ein Fund beim Prüfen: eine Textsuche unterscheidet Prosa nicht von Code

Die neue Prüfung *„Keine Aufgabe fürs bloße Öffnen"* war zuerst **rot, obwohl kein Aufruf mehr
existierte** — sie fand `aufgabeErledigen('auf')` in drei **Kommentaren**, die die Geschichte
erklärten. Die Erwähnungen sind umgeschrieben.
⚠️ **Das ist kein Schönheitsfehler:** ein Aufruf, der nur noch in der Prosa steht, macht jede
Textsuche im Quelltext blind — in beide Richtungen.

**Prüfungen 659 → 658** *(zwei Prüfungen zu „Reingeschaut" sind mit dem Feature weggefallen,
eine neue kam dazu).* Gegenproben: die Aufgabe zurück in die Liste → **2 rot**; nur die
**Aufrufstelle** wieder scharf, Liste sauber → **1 rot**.

## 2026-08-28

### 🔴 v47 — der Verlauf war auf dem PC verzerrt, und die Startseite erinnert ans Wiegen

**Karls Meldungen:** *„der Gewichtsverlauf ist so komisch stretched auf dem PC"* und
*„Erinnerung auf der Startseite einmal am Tag Gewicht einzutragen."*

#### Der Stretch — und warum er nur auf dem PC auffällt

Die Kurve wird in einer Flaeche von 300 Einheiten gezeichnet und dann auf die Kartenbreite
gezogen. **Am Telefon ist das gut ein Zehntel mehr, in einem 1120-px-Fenster fast das
Dreifache** — gemessen 2,89.

🔴 **Gedehnt wurde dabei nicht nur die Lage der Punkte (das ist richtig so), sondern jede
Strichstärke.** Die Linie war an flachen Stellen dünn und an steilen dick, die Striche des
Rasters wurden zu Balken, und **die Punkte waren Ellipsen**.

✅ **Behoben mit `vector-effect="non-scaling-stroke"` an jedem Strich.**
⚠️ **Die Punkte mussten dafür aufhören, Kreise zu sein:** eine Füllung lässt sich von der
Dehnung nicht ausnehmen, ein Strich schon. Ein sehr kurzer Strich mit runder Kappe zeichnet
denselben Punkt — und hält seine Form in jeder Fensterbreite.

#### Die Erinnerung

Eine Karte auf der Startseite mit Eingabefeld und Knopf, **solange heute nichts eingetragen
ist**. Sie zeigt den letzten Wert mit Datum, damit man weiß, wogegen man sich misst.
🔴 **Nach dem Eintragen verschwindet sie.** Eine Erinnerung, die nach dem Erledigen stehen
bleibt, ist keine Erinnerung mehr.
💡 Feld und Knopf sind dieselben wie auf der Kalorien-Seite — kein zweiter Weg ins Datum.

#### ⚠️ Was hier NICHT geprüft werden kann

**Wie breit der gezeichnete Punkt am Ende ist.** `getBoundingClientRect()` liefert bei
SVG-Formen die Geometrie **ohne** Strich — ein Punkt aus reiner Kappe misst dort 0.
✅ **Statt einer Messung, die das Falsche misst**, wird jetzt die **Ursache** gemessen (die
Dehnung, über `getScreenCTM()`) und die **Gegenmaßnahme** geprüft (die Ausnahme an jedem
Strich, plus: gar keine gefüllte Form mehr in der Fläche).

#### 🐛 Nebenbei: eine Prüfung war zufällig rot

*„Ein Ausreisser am Ende kippt den Trend nicht mehr"* fiel bei einem von vier Läufen um, **ohne
dass sich am Code etwas geändert hatte**. Der älteste Messpunkt lag **genau auf der
Fenstergrenze** (21 Tage bei einem 21-Tage-Fenster); zwischen dem Bauen der Liste und dem
Rechnen vergehen Millisekunden, mal fiel er hinein, mal heraus. Fenster jetzt 22 Tage.

**Prüfungen 653 → 659.** Gegenproben: die Ausnahme entfernt → 1 rot (sieben Striche benannt),
die Erinnerung an der **Aufrufstelle** abgeschaltet → 2 rot.


### 📊 v46 — die Kurven haben jetzt eine Skala

**Karls Meldung:** *„beim Verlauf vom Gewicht meiner Gym-App stehen keine Parameter an der
Seite und unten."*

**Stimmt — und es galt für alle drei Kurven der App**, nicht nur für die eine: Körpergewicht,
Übungsgewicht und Volumen laufen durch dieselbe Funktion `lineChart()`. Sie zeichnete eine
nackte Linie. Man sah, **dass** es hoch oder runter ging, aber nicht von wo nach wo und über
welchen Zeitraum.

**Jetzt steht dort:**

| | |
|---|---|
| **Links** | höchster Wert (mit Einheit), Mitte, tiefster Wert — auf drei gestrichelten Linien |
| **Unten** | erstes und letztes Datum, bei ungerader Punktzahl auch das mittlere |

⚠️ **Warum die Zahlen als HTML neben dem SVG stehen und nicht darin:** die Kurve wird mit
`preserveAspectRatio="none"` auf die volle Kartenbreite gezogen. Text **im** SVG wäre auf
breiten Schirmen waagerecht mitgedehnt worden — auf dem PC deutlich verzerrt, auf dem Handy
kaum. Genau die Sorte Fehler, die am Prüfstand nicht auffällt.

🔴 **Ein mittleres Datum gibt es nur bei ungerader Punktzahl.** Bei vier Punkten säße der
mittlere Punkt bei 33 %, das Datum aber bei 50 % — es würde einen Zeitpunkt behaupten, den es
nicht gibt. Eine eigene Prüfung hält das fest.

💡 **Und bei lauter gleichen Werten steht links nur *eine* Zahl.** Dreimal derselbe Wert
untereinander täuschte eine Spanne vor, die es nicht gibt.

**Prüfungen 644 → 653.** Beide Gegenproben nachgezogen: die Aufrufstelle entschärft *(zwei
Prüfungen rot)* und die Beschriftung entfernt *(sieben rot)* — nicht nur die Funktion allein.

## 2026-08-27

### 🔴 v45 — der Abgleich hat die halbe App nicht mitgenommen

**Karls Meldung:** *„Habe eine Trainingseinheit auf meinem Handy eingetragen, habe auch den
Erfolg bekommen für den Tag — jedoch nicht auf dem PC, obwohl mir mein Training dort auch
angezeigt wird."*

🔴 **Genau so war es gebaut.** Zusammengeführt wurden **Einheiten und Gewichte**, alles andere
im Profil kam unverändert vom eigenen Gerät. Und das eigene Gerät gewinnt praktisch immer:
`aufgabeErledigen('auf')` hakt beim Start *Reingeschaut* ab, das ruft `save()` — damit steht
`dirty`, **bevor der erste Abgleich überhaupt läuft**. Der Zweig `dirty ? lokal : cloud` fiel
also immer auf die eigene Seite.

**Was dabei still verlorenging:**

| | |
|---|---|
| **Tagesaufgaben** | Karls Fall — der Haken kam nie an |
| **Ausgezahlte Erfolge** | 🔴 das zweite Gerät zahlt denselben Erfolg **nochmal** aus |
| **Mahlzeiten und eigene Lebensmittel** | echter Inhalt, weg sobald das andere Gerät schob |
| **Schritte** | dito |
| **Zuletzt hier gewesen** | das Wiederkommen wäre zu früh gekommen |

⚠️ **XP wird exakt nachgetragen, nicht geschätzt.** Für jeden Erfolg und jede Aufgabe, die neu
dazukommt, steht der Wert im Katalog — der wird addiert. Ein `Math.max` über beide Punktestände
wäre naheliegend und **falsch**: es zählt Einheiten doppelt, die beide Seiten schon kennen.

### 🔑 Die Admin-Konsole hat sich selbst zugesperrt

**Karl:** *„meine Admin-Konsole auf dem Handy ist außerdem weg."*

Die Geste war `devAdmin = !devAdmin` — **fünfmal auf Brock tippen hat also auch wieder
zugesperrt.** Der Hinweis dazu ist nach 1,8 Sekunden weg, das merkt man nicht.
➡️ Fünfmal tippen schließt jetzt nur noch **auf**. Zumachen geht über einen eigenen Knopf in
der Konsole. **Eine Geste, die aufschließt, darf nicht zufällig auch abschließen.**

### 🎞️ Der Seitenwechsel hängt jetzt am Finger

Beim Wischen folgt die Seite der Bewegung (45 % des Wegs), und beim Loslassen kommt die neue
aus der Richtung herein, in die gewischt wurde. Der Tipp auf die untere Leiste macht dasselbe —
sonst sähe dasselbe Ziel je nach Weg anders aus.
💡 **Am Rand wird es zäh** (18 % statt 45 %): die Seite gibt ein Stück nach und federt zurück.
Das sagt *„da kommt nichts mehr"*, ohne einen Satz dafür zu brauchen.
⚠️ Die Bewegung sitzt an `#app`, nicht am `body` — die untere Leiste und der Pausen-Timer
stehen **über** den Seiten, nicht auf einer.
⚠️ Alle Zuhörer sind `passive`, und `touchmove` entscheidet erst nach 12 px, ob es waagerecht
gemeint war. Ein Wisch, der das Scrollen bremst, wäre schlimmer als kein Wisch.

### Kleinigkeiten

- **Der goldene Kasten *„1 neu freigeschaltet"* ist raus** (Karls Ansage). Die NEU-Markierung
  am Erfolg selbst bleibt — gestrichen war der Kasten, nicht der Hinweis.
- **Alle drei Assistenten stehen jetzt in der Admin-Konsole**: Trainingsplan, Ernährung,
  Wiederkommen. Der Trainings-Assistent fehlte.

**Prüfungen: 623 → 644.** ✅ Sieben Gegenproben, jede beißt.
⚠️ Die Admin-Prüfung suchte zuerst im Quelltext nach `devAdmin=!devAdmin` — und fand es im
**Kommentar, der die alte Fassung erklärt**. Sie tippt jetzt fünfmal auf Brock und sieht nach.

### 📉 v44 — die drei offenen Funde aus dem Durchsehen

Karl hat zu allen dreien Ja gesagt.

#### 1. Der Gewichtstrend nimmt jetzt alle Messungen

Bis hierher rechnete er `(letzter − erster) / Tage`. **Alles dazwischen fiel weg** — bei drei
Wochen und acht Wiegungen sechs weggeworfene Messungen. Und ausgerechnet die beiden
empfindlichsten blieben stehen: ein schwerer Morgen am Anfang oder ein leichter am Ende kippte
das Ergebnis komplett.

⚠️ **Das war nicht egal.** Aus dieser Zahl leitet der Regelkreis eine kcal-Korrektur ab und
bietet sie als Knopf an.

➡️ Jetzt eine **Ausgleichsgerade** (kleinste Quadrate) über alle Punkte.

🔴 **Und die ehrliche Zahl dazu, weil meine erste Prüfung zu viel erwartet hatte:** eine
Ausgleichsgerade **dämpft** einen Ausreißer, sie löscht ihn nicht. Gemessen an sechs Wiegungen
mit einem Ausreißer am Ende: **−0,252 statt −0,333 kg/Woche** — gut ein Viertel weniger, nicht
die Hälfte. Wer den Ausreißer ganz loswerden will, braucht ein robustes Verfahren (Median der
Steigungen); das wäre eine eigene Entscheidung.

⚠️ **`von` und `bis` sind jetzt die Werte auf der Geraden**, nicht die gemessenen Randpunkte.
Das muss so sein, sonst passt die angezeigte Spanne nicht zur Rate daneben — und ein Satz,
dessen zwei Hälften sich widersprechen, ist schlimmer als eine ungenaue Zahl. Dafür steht eine
eigene Prüfung.
💡 Bei genau zwei Messungen kommt dasselbe heraus wie vorher: durch zwei Punkte geht nur eine
Gerade. Die alten Prüfungen blieben deshalb unverändert grün.

#### 2. Ein Fenster für beide Seiten

Vorher: **21 Tage Gewicht gegen 14 Tage Essen.** Der Regelkreis fragt aber genau eine Sache —
passt das, was in *diesem* Zeitraum gegessen wurde, zu dem, was die Waage im *selben* Zeitraum
gemacht hat. Zwei Fenster können das nicht beantworten.

➡️ Beide stehen jetzt auf `RK_FENSTER = 21`, als eine Konstante, damit sie nicht wieder
auseinanderlaufen.
💡 Nebeneffekt: Essenstage aus der dritten Woche zählen jetzt mit — wer unregelmäßig
mitschreibt, fällt seltener in *„zu wenig Essenstage"*.

#### 3. Das Schlüssel-Fenster kann nicht mehr stumm verschwinden

`showModal()` und `closeModal()` fassen dasselbe `#modal` an. Ein Aufruf von dort räumte den
Schlüssel-Dialog weg, und `fragKey()` gab **nie eine Antwort**. Wer das Foto über diesen Weg
geschickt hat, hätte **für immer** auf *„das Bild wird angesehen"* gestarrt.

➡️ Der Dialog hinterlegt jetzt, wie man ihn im Notfall abbricht; beide Wege lösen das vorher
aus — mit `false`, denn ohne Eingabe gibt es keinen Schlüssel.
⚠️ Die Prüfungen dazu laufen gegen eine Zeitgrenze. **Eine Prüfung darf nie das sein, was
hängenbleibt** — ohne den Wettlauf hätte ein Rückfall den ganzen Lauf blockiert statt ihn rot
zu machen.

**Prüfungen: 612 → 623.** ✅ Sechs Gegenproben, jede beißt.

### 🔍 v43 — zweite Runde Durchsehen: Trainings-Teil und Anmeldung

#### 🔴 5. Ein Schutz, der nie greifen konnte

In `suggest()` — der Funktion, die das Gewicht für heute vorschlägt — stand die richtige
Absicht: **mehr Gewicht erst, wenn beim letzten Mal jeder Satz gemacht wurde.** Wer vier Sätze
geplant und zwei geschafft hat, soll nicht auch noch hochgehen.

Geprüft wurde das mit `done.length === e.sets.length`. **In einer gespeicherten Einheit sind
aber ausschließlich gemachte Sätze** — `finishWorkout` legt nur ab, was abgehakt ist. Beide
Zahlen waren also immer gleich, `alle` war immer `true`.

➡️ **Zwei Fehler an einer Stelle:** der Zweig darunter (*„letztes Mal 2 von 4 Sätzen"*) konnte
**nie erscheinen** — toter Text. Und der Schutz hat **nie geschützt**: wer zwei von vier
Sätzen schaffte, bekam trotzdem mehr Gewicht vorgeschlagen, sobald diese zwei über dem Ziel
lagen.

✅ `finishWorkout` schreibt jetzt `soll` mit — die Zahl der Arbeitssätze, die dastanden.
⚠️ Ältere Einheiten haben kein `soll` und bleiben beim alten Verhalten. Lieber wie bisher als
eine geratene Sollzahl, die einen Vorschlag ausbremst, den es nie gab.
🔴 **Es gab sogar eine Prüfung dafür — und sie war grün.** Sie baute eine Einheit mit einem
nicht abgehakten Satz darin, also einen Zustand, den die App gar nicht erzeugen kann. Genau
das Muster, das heute schon dreimal dran war: **geprüft war das Teil, nicht sein Einbau.**

#### 🔴 6. Abmelden und Löschen ließen kontogebundene Daten liegen

Zurückgesetzt wurden Pläne, Einheiten, Profil und Einstellungen — **daneben blieb liegen:**

- **Das Postfach.** Nach dem Abmelden zählte `postfachUngelesen()` weiter; wer sich als
  Nächster anmeldet, sieht die rote Zahl und kurz die Meldungen des Vorgängers.
- 🔴 **Abgeschickte, aber noch nicht zugestellte Meldungen.** Die hängen an der Verbindung,
  nicht am Konto — **die nächste Anmeldung hätte sie mit ihrem Token rausgeschickt.** Eine
  Meldung von Karl käme unter dem Namen seines Bruders an. Der schärfste der drei.
- Die Liste der örtlich als gelesen markierten Antworten.

✅ Alle drei gehen jetzt beim Abmelden mit.
⚠️ **Der KI-Schlüssel bleibt beim Abmelden liegen, und das ist Absicht** — er gehört zum Gerät,
nicht zum Konto (steht so in den Einstellungen). Beim **Löschen** geht er mit: dort steht
*„alle Daten dauerhaft"*, und dann darf nichts übrigbleiben.

#### Was ich geprüft und in Ordnung gefunden habe

Barcode und Foto: Produktnamen aus der offenen Lebensmittel-Datenbank sind **überall maskiert**,
bevor sie ins Bild gehen — der einzige unmaskierte Fund landet in einem Toast, und der setzt
`textContent`. Auch die Namen aus einem geteilten Plan-Link sind sauber.

**Prüfungen: 600 → 612.** ✅ Acht Gegenproben, jede beißt.

### 🔍 v42 — erste Runde Durchsehen: vier Funde, zwei davon ernst

Karls Auftrag: *„kannst du nochmal die App komplett testen — aber ich meine nicht deine Tests,
sondern mal den Code überfliegen und gucken, ob du irgendwelche Fehler oder tote/unbegründete
Dinge findest."*

#### 🔴 1. Der Service Worker hat API-Antworten mitgecacht

`fetch` griff sich **jede** GET-Anfrage — also auch die an Supabase. Zwei Folgen, und die
zweite ist die schlimmere:

1. **Trainingsdaten und Problemmeldungen lagen im Cache.** `gymlog_data?select=data` ist eine
   GET-Anfrage; die Antwort mit dem kompletten Datenblock wurde abgelegt und blieb liegen —
   auch nach dem Abmelden, denn das räumt `localStorage` auf, nicht den Cache.
2. **Ohne Netz hat der Abgleich sich selbst angelogen.** `cloudPull()` unterscheidet
   ausdrücklich *„kein Netz"* von *„Konto ist leer"* — und zwar daran, ob die Anfrage
   durchgeht. Mit einer gecachten Antwort ging sie **immer** durch, mit einem alten Stand.
   Die App hat dann offline gegen eine veraltete Cloud zusammengeführt, statt den örtlichen
   Stand gelten zu lassen. **Genau diesen Fall beschreibt der Kommentar in `cloudSyncStart()`
   als den Datenverlust vom 24.08.2026.**

➡️ Der Service Worker fasst jetzt nur noch die eigene Seite an.

#### 🔴 2. `ensureToken` konnte die Anmeldung wegwerfen

Beim Start laufen `cloudSyncStart()` und `postfachAuffrischen()` nebeneinander los, beide
fragen nach einem gültigen Token. War er abgelaufen (App länger als eine Stunde zu), schickten
**beide denselben `refresh_token`**. Supabase gibt bei jedem Auffrischen einen neuen aus und
macht den alten ungültig — der zweite Aufruf bekam ein 400, und der 4xx-Zweig wirft die
Anmeldung weg.

⚠️ **Das Bild wäre gewesen: App nach ein paar Stunden aufgemacht und rausgeflogen** — ohne
Anlass und nicht jedes Mal, weil es am Rennen zweier Anfragen hängt. Ein Fehler, den man nicht
nachstellt, sondern nur liest.
➡️ Läuft schon eins, warten alle anderen auf dasselbe Versprechen. Der Riegel geht auch nach
einem Fehlschlag wieder auf — sonst wartet der nächste Aufruf ewig.

#### 🔴 3. Das Wiederkommen hat alles überschrieben (mein Fehler, eine Stunde alt)

Der v41-Block stand am **Ende** der Startfolge und setzte `view='comeback'` ohne Rücksicht —
über eine **offene Einheit**, über den Assistenten und über die Schritte aus dem
Kurzbefehl-Link. Alle drei haben einen konkreten Anlass; das Wiederkommen hat nur ein Datum.
➡️ Die Entscheidung steht jetzt als `startAnsicht()` da — als Funktion, damit sie prüfbar ist.

#### 4. Tote Funktion `setPlans`

Definiert, nie aufgerufen. Raus.

---

### 🛠️ Und ein Werkzeug, weil derselbe Prüf-Fehler heute dreimal kam

Eine Prüfung, die `document.documentElement.innerHTML` durchsucht, findet dort **auch sich
selbst** — die Prüfungen stehen ja mit im Dokument. Zweimal war eine deshalb grün, obwohl der
geprüfte Aufruf gar nicht mehr dastand, einmal rot, obwohl nichts kaputt war.

➡️ `window.APP_QUELLE` reicht den Quelltext der App **ohne die Prüfungen** herein.
⚠️ Dabei gleich in die nächste Falle getreten: `</script>` in einer Zeichenkette beendet das
umgebende Skript-Tag trotzdem — der HTML-Parser sieht die Anführungszeichen nicht. Maskiert
als `<\/`.

**Prüfungen: 590 → 600.** ✅ Sechs Gegenproben, jede beißt.

### 🎒 v41 — fünf Sachen von Karls Liste

#### 1. Die Tagesaufgaben haben Symbole statt Haken

*Reingeschaut* → Auge, *Eingetragen* → Stift, *Trainiert* → Hantel (dasselbe Bild wie beim
Erfolg *Fünfzig* — dieselbe Sache an zwei Stellen, kein Versehen).
⚠️ **Ohne Haken muss „erledigt" trotzdem lesbar bleiben.** Das trägt jetzt die Farbe: hell mit
grüner XP-Zahl gegen grau. Vorher nebeneinander angesehen.

#### 2. Der KI-Schlüssel steckt im Ernährungs-Assistenten

Sechs Schritte statt fünf. Er gehört dorthin und nicht in den Trainings-Assistenten — der
Schlüssel ist nur für *Essen per Foto* da.
🔴 **Überspringen hat die gleiche Größe wie Eintragen.** Ein Schritt, der etwas von außen
verlangt (Google-Konto, zweite Seite, Warten), darf den Assistenten nicht blockieren — sonst
bleibt jemand beim Einrichten hängen und die Kalorien stehen nie. Dafür steht eine eigene
Prüfung.
💡 Und es steht dabei, dass **alles andere ohne Schlüssel geht**: Barcode, eigene Lebensmittel,
Tagesziel. Sonst liest sich der Schritt wie eine Pflicht.

#### 3. Das Wiederkommen nach zwei Wochen

**Karls Nachsatz war die eigentliche Anforderung:** *„natürlich nicht direkt, wenn man die
Website das erste Mal öffnet."* Ein *„schön, dass du wieder da bist"* beim allerersten Öffnen
wäre peinlich.

➡️ Deshalb hängt es an einem Wert, der beim ersten Mal **fehlt** (`zuletztDa === null`), statt
an einer Rechnung mit einem Ersatzwert. **Kein Ersatzwert kann „noch nie" bedeuten.** Zweite
Sperre: wer nie trainiert und nie eingerichtet hat, bekommt es auch nicht — der war nicht weg,
der hat nie angefangen.
⚠️ **Erst fragen, dann stempeln.** Andersherum wäre die Antwort immer „nein" und das
Wiederkommen käme nie — ein Fehler, den keine Prüfung der beiden Hälften einzeln sieht.
Deshalb stehen beide in **einer** Funktion, und dafür gibt es eine eigene Prüfung.
💡 Inhaltlich wichtiger als das Lob: die Ansage, dass **nichts verfallen ist**. Level, Rang und
Erfolge bleiben; nur die Wochen-Serie fängt neu an. Sonst liest sich eine Pause wie eine Strafe.

#### 4. Beide Tutorials in der Admin-Konsole

Beide kommen im Betrieb nur unter Bedingungen hoch. Ohne diesen Weg müsste Karl zum Ansehen
die Bedingung fälschen, also Daten anfassen.
⚠️ **Das Abspielen rührt nichts an** — es zeichnet nur die Ansicht. Wer sich das Wiederkommen
ansieht, will es sehen, nicht seinen Zeitstempel verlieren und es danach echt bekommen.

#### 5. Wischen zwischen den Reitern

Nur zwischen den vier Reitern der unteren Leiste, und nur wenn man auf einem davon steht.
🔴 **Aus einer laufenden Einheit führt kein Wisch heraus** — dort wäre er ein Datenverlust.
Dasselbe gilt für Assistent, Wiederkommen und die Unteransichten.
⚠️ Drei Riegel: nicht aus einem Eingabefeld heraus, nicht aus etwas seitlich Scrollbarem
heraus, nicht bei offenem Fenster. Und `passive:true` — ein Wisch, der das normale Scrollen
bremst, wäre schlimmer als kein Wisch.

---

**Prüfungen: 570 → 590.** ✅ Acht Gegenproben, jede beißt.

⚠️ **Der neue Schritt im Assistenten hat zwölf bestehende Prüfungen umgeworfen** — sie sprangen
mit einer festen `kobStep = 4` auf die Zusammenfassung, die jetzt Schritt 5 ist. Sie stehen
jetzt auf `KOB_LAST`. **Eine Prüfung, die eine Schrittnummer hartkodiert, prüft die Nummer
mit** — und die war nie das Versprechen.

💡 Beim Ansehen der fertigen Ansichten fiel ein *„Wöchen-Serie"* auf. Dritter Tippfehler
heute, den nur das Hinsehen gefunden hat.

### 🔴 v40 — die untere Leiste ist zurückgebaut (mein Fehler)

**Karls Meldung:** *„Hab die App gerade mal auf dem Handy geöffnet — man kann die Leiste unten
nicht mehr sehen, und immer wenn ich schon ganz oben bin und dann noch weiter hochscrolle,
geht die Leiste hoch bis zur Mitte des Bildschirms."*

🔴 **Das war meine Korrektur aus v33, und sie war schlimmer als das Problem.** Anlass war ein
Verrutschen, das Karl **einmal** gesehen und selbst als einmalig beschrieben hatte. Daraus ist
ein Fehler geworden, der **bei jedem Scrollen** auftritt.

**Warum sie nicht funktionieren konnte:** `visualViewport.offsetTop` wandert beim Überziehen am
oberen Rand (Gummiband) mit, und `clientHeight` und `visualViewport.height` stehen auf Android
je nach Zustand der Adressleiste **in beiden Richtungen** auseinander. Die Rechnung hatte weder
ein verlässliches Vorzeichen noch einen ruhenden Nullpunkt — sie hat das Gummiband
mitgezeichnet.

➡️ **Ersatzlos raus.** `position:fixed; bottom:0` macht der Browser selbst richtig.

⚠️ **Die Regel daraus ist die eigentliche Lehre:** *gegen ein Verhalten, das man nicht
nachstellen kann, baut man keine Dauerkorrektur.* Die seltene Ausnahme ist billiger als eine
Korrektur, die immer läuft. Ich hatte in v33 sogar dazugeschrieben, dass ich es nicht
nachstellen konnte — und es trotzdem gebaut.

### ↕️ „Alles zurücksetzen" steht jetzt bei den anderen gefährlichen Knöpfen

Karls Ansage: zwischen **Abmelden** und **Konto löschen**. Sachlich gehört er auch dorthin — die
drei sind eine Leiter: abmelden (nichts weg), zurücksetzen (Daten weg, Konto bleibt), Konto
löschen (alles weg). Vorher stand er in der Ansicht-Karte zwischen Design und Pausen-Timer,
also zwischen lauter Harmlosem.

**Prüfungen: 567 → 570.** Die neue Leisten-Prüfung sah zuerst im Quelltext der Seite nach und
fand dort **ihren eigenen Text** wieder (die Prüfungen stehen mit im Dokument) — sie war rot,
obwohl nichts kaputt war. Jetzt prüft sie das Verhalten: die Leiste darf sich auch dann nicht
bewegen, wenn der sichtbare Bildschirm sich meldet.

### 🚚 v39 — die Volumen-Leiter stimmt jetzt auch physikalisch

**Karl:** *„Eine Tonne eine Mauer? Finde ich doof irgendwie."* und *„Zehn Tonnen ein Auto?
Erstens kann man das schwer erkennen, zweitens wiegt kein Auto zehn Tonnen."*

🔴 **Der zweite Einwand ist sachlich richtig — und er löst den ersten gleich mit.** Ein
Kleinwagen wiegt **ungefähr eine Tonne**. Das Auto war also nicht falsch, es stand nur **eine
Stufe zu hoch**. Damit wird die Mauer nicht ersetzt, sondern überflüssig.

| | vorher | jetzt |
|---|---|---|
| 1 t | 🧱 Mauer | 🚗 **Kleinwagen** — wiegt ungefähr eine Tonne |
| 10 t | 🚗 Auto | 🚚 **Lkw** — Sattelzug leer, Bus, Müllwagen liegen alle da |
| 100 t | 🐋 Wal | 🐋 Wal *(Blauwal ~150 t)* |
| 250 t | 🌋 Vulkan | 🌋 Vulkan |

Das Auto ist dabei **neu gezeichnet** — deutlichere Dachlinie und größere Räder, denn Karls
erster Einwand war *„kann man schwer erkennen"*, und der galt der Zeichnung, nicht der Stufe.

⚠️ **Beide mussten sich bei 24 px unterscheiden lassen** — das ist die echte Größe in der
Liste. Flach und rund gegen hoch und eckig; fünf Entwürfe nebeneinander angesehen, bevor einer
eingebaut wurde.

💡 **Was dabei auffällt, aber nicht angefasst ist:** der Vulkan auf 250 t ist jetzt der einzige
in der Reihe, der **kein Gewicht** ist, das man sich vorstellen kann. Ein Großraumflugzeug wäre
mit rund 280 t leer der passende Nachbar zum Wal. **Karls Entscheidung, nicht meine** — er hat
nach zwei Symbolen gefragt, nicht nach vieren.

**Prüfungen: 567** (unverändert — die bestehenden decken den Tausch ab: jeder Erfolg hat ein
Symbol, das es gibt, und keines wird zweimal vergeben).

### ✂️ v38 — Karls Textliste: zehn Erklärungen raus, vier kürzer

Karl hat eine Liste geschickt. Umgesetzt wie angegeben.

**Gestrichen:** *Waage und Essen im Abgleich* samt Hinweis auf zwei Wiegungen · Barcode/Foto ·
der Absatz unter den Tagesaufgaben · *„Diese drei geben keine XP"* · *„System folgt der
Hell/Dunkel-Einstellung"* · *„Das geht mit …"* samt *„Deine Trainingsdaten gehen nicht mit"* ·
der Nachsatz am Push-Stand · *„Deine Daten bleiben erhalten"*.

**Gekürzt:** Wiegen · Zurücksetzen · KI-Schlüssel · Konto löschen.

---

**Drei Stellen, an denen Streichen mehr war als Streichen:**

🔴 **1. Der Regelkreis wäre auf „undefined" gelaufen.** Der gestrichene Satz war der einzige
Inhalt des Zweigs *zu wenig Wiegungen* — fällt er ersatzlos weg, ist `inhalt` undefiniert und
im Bild steht das Wort. Jetzt erscheint in diesem Fall **gar keine Karte**; eine leere Karte
mit Überschrift wäre schlechter als keine. Ein getreuer Rückbau lässt **10 Prüfungen** fallen.

🔴 **2. Der Push-Stand wäre leer geblieben.** Gestrichen war die Erklärung, nicht der Zustand —
sonst stünde dort dauerhaft *„wird geprüft …"*. Es steht jetzt **An** bzw. **Aus** da, und
zwar in **beiden** Zweigen: „An" mit Nachsatz und „Aus" ohne wäre schief gewesen.

⚠️ **3. Was mit einer Meldung mitgeht, wird weiterhin mitgeschickt.** Nur der Hinweis auf der
Meldeseite ist weg. **Die vollständige Aufzählung steht unverändert auf der
Datenschutz-Seite** — Fassung, Browser-Kennung, Bildschirmgröße, online/offline, Anzahl der
Einheiten, letzter Abgleich. Dafür steht seit heute eine eigene Prüfung: aus einem gekürzten
Text darf keine verschwiegene Übertragung werden, und das ist etwas ganz anderes als ein
Textwunsch.

💡 Beim Aufräumen fiel ein toter `umfeldSammeln()`-Aufruf in `renderMeldung()` an — er hing nur
an der gestrichenen Anzeige. Beim Verschicken wird weiterhin frisch gesammelt.

**Prüfungen: 562 → 567.** ✅ Fünf Gegenproben. Geprüft wird dabei **nicht, dass Text fehlt** —
das wäre eine Prüfung, die jede spätere Verbesserung bestraft —, sondern das, was beim Streichen
kaputtgehen kann: kein „undefined", keine leere Karte, der Push-Zustand steht, der Aufgaben-Stand
steht, und die Meldedaten stehen im Datenschutz.

### 🔴 v37 — die rote Zahl ging nicht weg

**Karls Meldung:** *„die rote Zahl bei den Einstellungen geht nicht weg, wenn ich den Postkasten
öffne."*

🔴 **Dahinter lagen zwei Fehler übereinander — und der zweite hätte den ersten überlebt.**

#### 1. Das Öffnen hat nichts abgehakt

Gelesen wurde eine Antwort nur, wenn man auf die **einzelne Meldung tippte** (`data-meldread`).
Im Postfach steht die Antwort aber **vollständig da** — nichts ist zugeklappt. Wer sie gelesen
hat, hat sie gelesen; ein zusätzlicher Tipp auf etwas, das man schon sieht, ist keine Handlung,
sondern eine Hürde.

➡️ Abgehakt wird jetzt **beim Zeichnen der Seite**. Der tote Klick-Zweig ist raus.
💡 **Die Markierung bleibt trotzdem stehen, solange man da ist** — sonst verschwindet sie in dem
Moment, in dem man hinsieht, und man erfährt nie, *welche* Antwort neu war. Beim nächsten Besuch
ist sie weg. Gleiche Linie wie bei den frisch freigeschalteten Erfolgen aus v33.
⚠️ Eine Meldung **ohne** Antwort wird nicht abgehakt — dafür steht eine eigene Prüfung.

#### 2. Der Server hat die Marke wieder überschrieben

`postfachHolen()` legt die Zeilen vom Server über die örtliche Spiegelung. Bis *„gelesen"* beim
Server angekommen und verbucht war, kam von dort weiter `gelesen_am: null` zurück — **und die
rote Zahl war wieder da. Ohne Netz sogar dauerhaft.**

➡️ Das Gerät merkt sich jetzt, was es hier als gelesen betrachtet, und legt diese Marke über
jede Antwort vom Server. Die Kennung fliegt raus, sobald der Server es selbst so sieht oder die
Zeile aus den 30 Tagen fällt — **die Liste wächst also nicht mit.**

🔴 **Warum das der wichtigere von beiden ist:** Fehler 1 allein hätte man mit einem Tipp
umgehen können. Fehler 2 kam auch danach zurück, und zwar ohne erkennbaren Anlass — die Zahl
war weg und ein paar Sekunden später wieder da. Das sieht nicht nach einem Fehler aus, sondern
nach Spuk.

---

**Prüfungen: 552 → 562.**
✅ **Sieben Gegenproben:** Öffnen hakt nichts ab → 3 · Leiste nicht nachgezogen → 1 · Serverzeile
überschreibt → 1 · Marke nie vergessen → 1 · Markierung verschwindet sofort → 1 · Besuchsliste
nicht geleert → 1 · Meldungen ohne Antwort abgehakt → 1.

🔴 **Zwei davon haben beim ersten Anlauf wieder nicht gebissen — zum dritten Mal heute
dasselbe Muster.** Die Prüfung rief `gelesenLokalAnwenden()` direkt auf statt `postfachHolen()`,
und die Leisten-Prüfung sah nach einer Zahl, die vorher nie gezeichnet worden war. **Geprüft
war jeweils das Teil, nicht sein Einbau.** Beide sind jetzt echte Wege: der Abruf läuft mit
vorgetäuschtem Server durch, und die Zahl wird erst gezeichnet und dann gesucht.

### 🎨 v36 — die Erfolge haben jetzt gezeichnete Symbole

**Karls Ansage:** *„bei den Achievements SVG-Dateien benutzen."*

19 Symbole, gezeichnet im **selben Stil wie die Übungsbilder**: 48×48, Strich statt Fläche,
`.ma` für den dicken Akzentstrich. Damit sehen Erfolge und Übungen nach derselben App aus.

🔴 **Warum das mehr ist als Geschmack:** Emojis sehen auf jedem Gerät anders aus. Das
Bergsteiger-Emoji ist auf Android ein anderer Mensch als auf dem iPhone, und für 🗿 zeigen
manche Systeme gar nichts. Ein Katalog, dessen Bilder je nach Telefon wechseln, ist kein
Katalog.

⚠️ **Sie stehen im Quelltext und nicht als 19 eigene Dateien.** Die App ist eine einzige Datei,
damit sie offline läuft — 19 Nachladungen wären 19 Wege, an denen genau das scheitern kann.
*SVG* ist hier die Zeichenart, nicht der Dateiname.

**Drei Zustände, und sie hängen bewusst nicht nur an der Deckkraft:**

| Zustand | Aussehen |
|---|---|
| offen | Muted-Farbe, halb durchsichtig |
| geschafft | normale Schriftfarbe, Akzent im Detail |
| **frisch freigeschaltet** | **Gold — und es wackelt**, dieselbe Bewegung wie der Pokal an der Leiste |

💡 Die Bewegung ist dieselbe wie bei der goldenen Zahl, damit erkennbar zusammengehört, was
zusammengehört: die Zahl an der Leiste und das, was sie meint.

🔴 **Jedes Symbol ist angesehen worden, bevor es eingebaut wurde** — einmal in 60 px und einmal
in 24 px, denn 24 px ist die echte Größe in der Liste. **Drei Entwürfe sind dabei
durchgefallen:** ein Bizeps, der wie ein Rohr aussah (→ Hantel), ein Moai, der wie eine Tür
aussah (→ Krone), und ein Wal ohne Fontäne (→ mit). Danach noch ein Blick auf die ganze Seite —
dabei fiel ein *„vollstaendig"* ohne ä auf, das seit v33 dastand.

**Prüfungen: 546 → 552.** ✅ Vier Gegenproben: zwei Erfolge mit demselben Bild → 1 · Erfolg
ohne Bild → 1 · alle Zustände gleich → 1 · kein Ersatzbild → 1.

### 🔗 v35 — den Link verpacken, so weit es der Empfänger zulässt

**Karls Idee:** *„Kann man den Link sonst verpacken? In eine Überschrift z.B., hinter einfach
Gym-Log."*

🔴 **Die ehrliche Kurzfassung: das hängt am Empfänger, nicht an dieser App.** Was mit einem
Link passiert, entscheidet das Programm, in dem er landet. Deshalb drei Wege statt einem —
und bei einem davon ein ausdrückliches Nein.

**Discord — geht wirklich.** `[Mein Plan](adresse)` zeigt nur die zwei Worte, die Adresse ist
komplett unsichtbar. ⚠️ Runde und eckige Klammern im Plannamen zerreißen die Schreibweise und
werden deshalb entfernt — lieber ein Name ohne Klammern als ein Link, der nicht geht.

**E-Mail, Notizen, Word — geht auch.** Beim Kopieren liegt neben dem Text eine **HTML-Fassung**
in der Zwischenablage (`<a href="…">Mein Plan — Gym-Log</a>`). Eingefügt wird daraus ein
anklickbares Wort. ⚠️ Firefox kann kein `text/html` in die Zwischenablage schreiben; dort
landet die Adresse. Lieber schlichter als leer.

**WhatsApp — geht nicht, und ich tue nicht so.** Dort steht die Adresse als Text, immer. Der
Hinweis steht so auch im Dialog, statt dem Knopf einen Namen zu geben, der etwas verspricht.

➡️ **Was überall wirkt, ist die Vorschau-Karte.** Die Seite hatte bisher **keine einzige**
`og:`-Zeile — ein geteilter Link war überall nackter Text ohne Bild und ohne Titel. Jetzt holen
sich Messenger Symbol, Titel und eine Zeile Beschreibung. Die Nachricht sieht nach Gym-Log aus
statt nach hingeworfener Adresse.
⚠️ **Die Karte ist immer dieselbe, auch bei einem Plan-Link.** Der Teil nach der Raute (`#p=…`)
wird nie an den Server geschickt — ein Vorschau-Dienst sieht ihn gar nicht und könnte den
Plannamen nicht in den Titel schreiben.
⚠️ `og:image` steht mit **voller Adresse** da. Ein relativer Pfad taugt nicht, das Bild wird
von außen geholt. Dafür steht eine eigene Prüfung.

💡 **Der Teilen-Knopf tut nicht mehr direkt eine Sache, sondern öffnet einen Dialog** — der
Griff zum Teilen-Fenster des Handys steht aber als **erster** Knopf drin. Ein Knopf, der früher
eine Sache tat und jetzt vier anbietet, wäre sonst eine Verschlechterung für den häufigsten
Fall. Oben steht auch, wie lang der Link gerade ist.
⚠️ `navigator.share` braucht eine Nutzergeste — der Knopf **im** Dialog ist eine, deshalb geht
das auf, obwohl der Dialog dazwischensteht.

**Prüfungen: 541 → 546.** ✅ Vier Gegenproben: Karte raus → 1 · `og:image` relativ → 1 · leerer
Plan teilbar → 1 · Dialog ohne Adresse → 1.

### 🔴 v34 — beendete Trainings gingen verloren

**Karls Meldung:** *„Wenn ich auf Training beenden gehe, wird das Training einfach verworfen.
Liegt es daran, dass das Training nicht komplett abgeschlossen wurde? Aber das wäre nicht
richtig."*

**Er hat recht, und der Fehler war schwerer, als er klingt.** Bis hierher entschied **allein
der Haken**, ob ein Satz existiert:

```js
sets: e.sets.filter(s => s.done)          // alles ohne Haken: weg
if (entries.length === 0) { active = null; toast('Verworfen (nichts erledigt)'); }
```

Wer 80 kg und 8 Wiederholungen eintippte und den Haken nicht setzte, hatte für die App
**nichts getan**. Die ganze Einheit verschwand hinter einem Hinweis, der nach 1,8 Sekunden weg
war — **kein Rückweg, keine Nachfrage**, und der Text las sich wie eine Feststellung statt wie
ein Verlust.

➡️ **Ein Satz gilt jetzt als gemacht, wenn er abgehakt ist ODER wenn etwas drinsteht.**
Niemand tippt 80 kg ein, ohne sie gehoben zu haben. Der Haken bleibt, wofür er da ist — die
Pause starten, den Rekord im Moment feiern —, aber er entscheidet nicht mehr darüber, ob die
Arbeit stattgefunden hat.

⚠️ **Leere Sätze bleiben draußen.** Die Felder sind leer, solange niemand tippt (die Vorschläge
stehen als *Platzhalter*, nicht als Wert) — ein geplanter, aber nicht gemachter Satz trägt also
weiterhin nichts bei.
⚠️ **Nachgezogen wird dasselbe wie beim Abhaken von Hand:** fehlende Wiederholungen bekommen
die untere Zahl des Zielbereichs, und ein **Rekord wird auch hier vermerkt**. Sonst verlöre
Karl den Rekord-Bonus für genau die Sätze, die er getippt hat.
💡 **Und es wird gesagt, nicht stillschweigend gemacht:** *„3 Sätze waren nicht abgehakt —
mitgezählt, weil etwas drinstand."*

🔴 **Der Fall ohne jede Eingabe wird nicht mehr verworfen.** Früher war die Einheit dann weg.
Jetzt bleibt sie stehen und ein Fenster sagt, dass nichts da war; wegwerfen kann man sie über
*Abbrechen*. **Ein Fenster, das man wegtippen muss, ist an dieser Stelle billiger als eine
verlorene Einheit.**

### 🔗 Der Plan-Link, dritter Schritt — 1.050 → 198 Zeichen

**Karls Rückfrage** nach v33: *„Der Link sieht besser aus, aber immer noch sehr lang. Kann man
da noch was machen, oder bist du am Ende deiner Macht?"*

War ich nicht — und das ist der unangenehme Teil. **Was ich in v33 gemacht habe, waren die zwei
folgenlosen Schritte.** Dieser hier kostet etwas, und deshalb stand er nicht gleich dabei. Die
Abwägung hätte Karl gehört, nicht mir.

➡️ **Namen werden durch Nummern ersetzt.** Die Übungs-Bibliothek (672 Einträge, EXLIB + wger)
hat jede Übung schon — statt *„Schrägbankdrücken Kurzhantel"* (28 Zeichen) steht im Link eine
Zahl. Karls eigene Übungen kennt die Bibliothek nicht, die wandern weiter als Text mit.
➡️ **Vorgaben werden weggelassen.** 3 Sätze, Volumen hoch — der Normalfall steht nicht mehr da.

| | Zeichen |
|---|---|
| gestern (v2) | **1.050** |
| v33, heute Nachmittag | 391 |
| **v34, jetzt** | **198** — davon 43 die Adresse selbst |

*(Gemessen an einem Vier-Tage-Plan mit 23 Übungen. Beim kleinen Standardplan sind es 435 → 177
— der Gewinn wächst mit der Plangröße, also genau dort, wo die Beschwerde herkam.)*

🔴 **Der Preis, und er ist echt: eine Nummer ist nur so viel wert wie die Liste, auf die sie
zeigt.** Daraus folgt eine Regel, die wichtiger ist als das Feature selbst:

> **`EXLIB` und `EXLIB_WGER` sind ab jetzt anhängend. Nie umsortieren, nie etwas mittendrin
> einfügen, nie einen Eintrag löschen.**

Verschiebt sich ein Eintrag, zeigt jeder alte Link **still** auf die falsche Übung — und eine
falsche Nummer sieht aus wie eine richtige. **Eine Prüfung nagelt Länge und die beiden
Randeinträge fest** und fällt um, sobald jemand daran dreht. Fällt sie, ist nicht sie kaputt.

⚠️ **Kennt der Empfänger eine Nummer nicht** (ältere Fassung), fällt die Übung raus statt unter
falschem Namen im Plan zu landen — und er bekommt es gesagt: *„Eine Übung ist nicht dabei —
deine App kennt sie noch nicht."*
⚠️ **v1, v2 und v3 werden weiter gelesen.** Die v3-Links von heute Nachmittag stehen schon in
einem Chat.
📏 **Weiter geht es ohne Server nicht.** Der Plan steckt vollständig im Link; kürzer als seine
eigene Information wird er nicht.

---

**Prüfungen: 523 → 541.**
✅ **Acht Gegenproben, jede wirft genau das um, was der Rückbau kaputt macht:** Übernahme raus →
5 · leere Sätze mitzählen → 2 · Wiederholungen nicht nachziehen → 1 · Rekord ohne Haken weg →
2 · leere Einheit wieder still verwerfen → 1 · Bibliothek umsortieren → 1 · unbekannte Nummer
raten → 2 · eigene Übungen nicht mitschicken → 2.

### 🏅 v33 — zehn Meldungen von Karl, neun davon eingebaut

Karl hat nach einem Tag mit v32 eine Liste geschickt. Sie steht hier der Reihe nach, weil
mehrere Punkte denselben Kern haben: **etwas war richtig gebaut, aber an der falschen Stelle.**

#### 1. „Reingeschaut geht nicht direkt durch, wenn man die App startet"

🔴 **Es ging durch — eine Zeile zu spät.** Der Startblock zeichnete zuerst die Seite und hakte
die Tagesaufgabe danach ab. Neu gezeichnet hat danach niemand. Wer gleich nach dem Start auf
die Erfolgs-Seite ging, sah ein leeres Kästchen an einer Aufgabe, die längst erledigt war.

➡️ Abhaken steht jetzt **vor** dem ersten `render()`.

⚠️ **Die zweite Hälfte war der eigentliche Fund, und die hat Karl nicht gemeldet — sie wäre ihm
morgen früh aufgefallen.** Die App wird als PWA fast nie wirklich geschlossen; sie liegt im
Hintergrund und kommt am nächsten Tag wieder nach vorn. Der Startblock läuft dann **nie
erneut**, und die Tagesaufgabe wäre still offen geblieben. Beim Zurückkommen in die App wird
deshalb nachgefasst — und nur dann neu gezeichnet, wenn wirklich etwas dazukam, sonst risse
ein `render()` bei jedem Wechsel laufende Eingaben weg.

#### 2. „500 t sind zu viel" · 4. „13 Wochen ist zu viel, vor allem unfair bei Krankheit"

- **Halbe Million → Viertelmillion.** `v4` steht auf **250.000 kg** statt 500.000.
- **Ein Vierteljahr → Acht Wochen.** `d3` steht auf **8** statt 13.

🔴 **Bei den Wochen war die Zahl aber nur die halbe Antwort.** Karls zweiter Halbsatz — *„unfair
für Leute, die mal krank sind"* — wäre mit einer kleineren Zahl **nicht** behoben: eine Grippe
reißt eine Serie ab Woche 1 genauso ab wie ab Woche 12. Der Erfolg hätte dann Krankheit
bestraft, nicht fehlenden Willen.

➡️ Deshalb zählt `besteWochenSerieJoker()` daneben, und die **überbrückt eine ausgefallene
Woche**. Zwei Wochen am Stück reißen weiter ab — ohne diese Grenze wäre aus dem Erfolg
*„irgendwann mal acht Wochen trainiert"* geworden, und das misst gar nichts mehr.
⚠️ **Die Pausenwoche zählt nicht mit:** trainiert–Pause–trainiert steht bei 2, nicht bei 3.
Verziehen heißt verziehen, nicht geschenkt.
⚠️ **`besteWochenSerie()` bleibt daneben unverändert streng** — *Vier am Stück* ist kurz genug,
dass ein Joker ihn fast geschenkt hätte.

#### 3. „Ich will über meine Admin-Konsole alle Erfolge freischalten können"

Gebaut wie `devUnlockAll` bei den Designs: ein Schalter, der nur die Frage *„ist der offen?"*
umbiegt. **Gespeichert wird nichts** — aus geht der Schalter, und überall steht wieder der
echte Stand.

🔴 **Die wichtigste Zeile des ganzen Features ist eine Sperre**, und sie steht in
`erfolgeAuszahlen()`. Ohne sie hätte ein Klick auf *Alle Erfolge freischalten* **8.050 XP über
16 Erfolge** ins Profil geschrieben — und zurückgenommen wird hier nichts. Die Gegenprobe zeigt
genau diese Zahl, wenn man die Sperre entfernt.

#### 5. „Oben eine Anzeige, wie viele Erfolge man hat, bzw. ein Board"

Vorher stand dort ein graues *„12 von 22"* in Kleinschrift neben der Überschrift — eine
Fußnote, kein Stand. Jetzt: **Ring mit dem Anteil**, Prozentzahl, vollständige Gruppen und
**wie viel XP aus Erfolgen** verdient sind, gegen die mögliche Summe.

#### 6. „Auf dem PC ist die rote Zahl verschoben, die muss rechts über dem Wort sein"

🔴 **Und so war es auch.** Die Zahl hing am *Knopf* und stand auf `left:50%`. Auf dem Handy ist
das die Mitte über der Beschriftung — richtig. In der PC-Seitenleiste ist es die Mitte eines
204 px breiten Knopfes, also irgendwo hinter dem Wort im Leeren.

➡️ Die Beschriftungen sitzen jetzt in einem eigenen `<span class="navtxt">`, und die Zahl hängt
**an der Schrift statt an der Knopfbreite**.
💡 **Auf dem Handy ändert sich dabei nichts, und zwar mit Absicht:** dort ist der Span
`position:static`, die Zahl bezieht sich also weiter auf den Knopf und steht exakt wie vorher.
Erst die PC-Fassung schaltet ihn auf `relative`. Ein Umhängen im DOM je Bildschirmbreite wäre
die Alternative gewesen — ein Wort, das seinen eigenen Bezugsrahmen mitbringt, fällt bei
späteren Umbauten nicht auf die Nase.

#### 7. „Kann man was dagegen tun, dass der Plan-Link gefühlt ein A4-Blatt füllt"

**Gemessen an einem Vier-Tage-Plan mit 23 Übungen: 1.005 Zeichen.** In einer Chat-Blase ist das
eine Wand aus Buchstaben, und mancher Messenger bricht sie mittendrin um.

Zwei Schritte, zusammen **auf 398 Zeichen — 60 % kürzer**:

1. **v3 spart die Feldnamen.** Statt `{"n":…,"d":…,"w":…,"e":[…]}` steht dort
   `[name, tag, aufwärmen, übungen]`. Die Reihenfolge trägt die Bedeutung.
2. **Deflate.** Übungsnamen wiederholen sich zwischen den Trainings (*Bankdrücken* steht in
   Push **und** in Oberkörper) — genau davon lebt ein Packer. Das bringt mehr als Schritt 1.

⚠️ **v1 und v2 werden weiter gelesen.** Ein Link, den Karl gestern verschickt hat, darf morgen
nicht unbekannt sein. Fehlt `CompressionStream` (alter Browser), geht der alte lange Link raus.

🔴 **Und warum das Packen nicht im Klick passiert:** `CompressionStream` ist asynchron, und ein
`await` vor `navigator.share()` kostet auf iOS die Nutzergeste — dann geht das Teilen-Fenster
gar nicht mehr auf. Der Code wird deshalb **vorgewärmt, sobald die Plan-Liste gezeichnet
wird**, also lange bevor jemand auf Teilen drücken kann.

#### 8. „Die Leiste ganz unten war auf einmal in der Mitte"

⚠️ **Nicht nachgestellt** — es hängt am Browser, nicht an dieser App, und Karl hat es selbst
als einmalig beschrieben. Was dahintersteckt, ist aber bekannt: ein Handy hat **zwei**
Bildschirmgrößen. Die eine (Layout) rechnet die Seite, die andere (sichtbar) ist das, was
gerade zu sehen ist. `bottom:0` meint immer die erste. Laufen beide auseinander — typischerweise
kurz nachdem eine Tastatur zugegangen ist —, landet *„ganz unten"* mitten im Bild.

➡️ Eine Schleife misst den Unterschied und schiebt die Leiste um genau den Betrag zurück.
🔴 **Nur wenn er größer als 4 px ist.** Im Normalfall passiert damit gar nichts und der Browser
macht seine Arbeit weiter selbst — eine Dauerkorrektur hätte ein neues Zittern gegen ein
seltenes Verrutschen eingetauscht.

#### 9. „Bei Erfolge eine goldene Zahl, und das Zeichen wird Gold und bewegt sich"

Gebaut: **goldene Zahl am Pokal**, der Pokal färbt sich mit und wackelt alle 2,2 s kurz.

🔴 **Gold und nicht dieselbe rote Zahl, und das ist keine Geschmacksfrage.** Rot heißt in dieser
App *„da liegt etwas für dich"* — eine Antwort im Postfach, also ein offener Posten. Ein neuer
Erfolg ist das Gegenteil: eine Belohnung. Zwei verschiedene Sachen dürfen nicht gleich aussehen.
Dafür steht eine eigene Prüfung.

⚠️ **Beim ersten Start mit v33 leuchtet nichts auf**, obwohl die App noch nie wusste, was Karl
gesehen hat. Alles bereits Verdiente wird als *gesehen* eingetragen. Sonst hinge dort eine
goldene 12 für Erfolge, die er seit gestern kennt — und die Zahl wäre entwertet, bevor sie das
erste Mal etwas bedeutet.
⚠️ **Der Admin-Schalter zählt hier nicht mit**, sonst stünde nach einem Klick eine goldene 22
da und Karl sucht 22 Erfolge, die er nie freigeschaltet hat.
💡 Wer Bewegung im System abgestellt hat (`prefers-reduced-motion`), bekommt keine — das Gold
trägt die Botschaft auch allein.

#### 10. „Wie lange bleibt der KI-Schlüssel in der App und wie lange hält der?"

Keine Änderung, eine Antwort — sie steht in der Antwort an Karl und unten im Vault.

---

**Prüfungen: 495 → 523.**
✅ **Sieben Gegenproben, jede wirft genau das um, was der Rückbau kaputt macht:** Auszahl-Sperre
raus → 1 (und meldet die 8.050 XP) · d3 wieder streng → 1 · 500 t zurück → 1 · Zahl wieder am
Knopf → 1 · Reingeschaut wieder nach dem Zeichnen → 1 · goldene Zahl wie die rote → 2 ·
Vorwärmen abgeschaltet → 1.

🔴 **Zwei davon haben beim ersten Anlauf NICHT gebissen, und das war der wertvollste Teil des
Tages.** *d3 wieder streng zählen* ließ keine einzige Prüfung umfallen: alle Joker-Prüfungen
riefen `besteWochenSerieJoker()` direkt auf, und die Ziel-Prüfung sah nur die Zahl 8. Geprüft
war damit die Zählung — **aber nicht, dass der Erfolg sie benutzt**, also genau die Verbindung,
um die es Karl ging. Dasselbe beim Vorwärmen: geprüft war der Packer, nicht der Auslöser, und
ohne Auslöser hätte Karl beim ersten Teilen still wieder den langen Link bekommen.
➡️ **Beide Lücken sind mit einer eigenen Prüfung geschlossen.** Merksatz: eine Prüfung, die den
Baustein direkt aufruft, prüft den Baustein — nicht seinen Einbau.

## 2026-08-26

### 🎖️ v32 — Erfolge geben XP, Rang-Erfolge bewusst nicht

**Karls Frage:** *„Was meinst du, macht es Sinn, für Erfolge XP zu kriegen? Aber nicht für
Erfolge in Hinsicht auf Level."*

🔴 **Der zweite Halbsatz ist der eigentliche Fund, und er stimmt.** Ein Erfolg für *Level 25*,
der XP gibt, ist ein **Kreis**: die Belohnung fürs Leveln wären Level. Bei *Gigachad* wäre es
sogar folgenlos, weil darüber nichts mehr kommt.

Daraus die Regel, nach der jetzt alles gebaut ist — sie steht auch so im Quelltext, damit sie
beim nächsten Erfolg nicht vergessen wird:

> **Ein Erfolg gibt XP, wenn er nicht in XP gemessen wird.**

*Level 10*, *Level 25* und *Gigachad* stehen deshalb auf `xp:0` — **nicht vergessen, sondern
entschieden.** In der Ansicht steht der Grund unter der Gruppe, sonst sieht es nach einem
Fehler aus.

#### Warum das die Regel vom 22.08. nicht bricht

Dort steht: **kein XP fürs Essen**, weil es Level und Rang mit etwas aufbläht, das keine
Anstrengung ist. Der Unterschied:

- *„App geöffnet"* wäre eine **neue, freie XP-Quelle** — deshalb dort nur 5 XP mit Tagesdeckel.
- *„100 Einheiten"* ist **keine**. Die hundert Einheiten sind längst trainiert und haben längst
  XP gebracht. Der Erfolg ist ein **Bonus auf Arbeit, die schon geleistet ist**, kein zweiter
  Weg nach oben.

Deshalb dürfen diese dreistellig sein: 100 für die erste Stufe, bis 1.500 für *Hundert
Einheiten* und *Halbe Million*. **Zusammen 8.050 XP** von 42.240 bis Gigachad — **19 %**, und
für jeden einzelnen muss die Arbeit trotzdem gemacht werden.

#### Zwei Entscheidungen im Kleingedruckten

**1. Was ausgezahlt ist, wird gespeichert.** Das ist die einzige Stelle im ganzen Erfolgs-Teil,
an der etwas gespeichert wird — der Erfolg selbst bleibt gerechnet und damit immer ehrlich.
⚠️ Ohne diese Liste gäbe es bei **jedem App-Start** dieselben XP nochmal.

**2. Es wird nichts zurückgenommen.** Wer eine Einheit im Verlauf korrigiert und dabei unter
eine Schwelle rutscht, behält die XP. Gleiche Linie wie bei `sessRecalc`: **lieber ein alter
Wert stehen als ein geratener abgezogen.**

⚠️ **Rückwirkend beim ersten Start:** was längst erfüllt war, wird auf einen Schlag
gutgeschrieben. Das ist ein Sprung, kein Aufbau — aber die Arbeit dafür ist getan, und die
Alternative wäre, sie nie zu würdigen.

💡 **Ein neuer Erfolg bekommt ein eigenes Fenster, keinen Toast.** Ein Toast ist nach 1,8 s
weg — etwas, das man einmal im Leben freischaltet, soll man auch sehen.

**Prüfungen: 486 → 495.**
✅ **Dreimal gegengeprobt:** Gigachad auf 5.000 XP gesetzt → 2 Prüfungen fallen · Sperre gegen
doppelte Auszahlung raus → 1 · unerfüllte Erfolge auszahlen → 1 (und zeigt nebenbei die
Gesamtsumme: **8.050 XP über 16 Erfolge**).

### 🏆 v31 — XP zählt Anstrengung, Tagesaufgaben, und ein Erfolgs-Katalog

**Karls Ansage:** *„Wir brauchen ein System mit Aufgaben vielleicht, z. B. überhaupt die App
öffnen. Soll aber auch Gewicht belohnen, und ja, Anstrengung statt Kilos. Außerdem hätte ich
gerne einen Achievement-Katalog als 3ter Reiter unten zwischen Einstellungen und Kalorien."*

Der XP-Umbau stand seit dem **22.08.** als Karls eigener Punkt im Vault (*„wir müssen uns
unbedingt um xp kümmern"*) und war damals vertagt worden — *„mach erstmal das andere"*.

#### 1. Die Formel belohnt nicht mehr das Schwersein

**Vorher:** `Sätze×10 + 50 + (Volumen/1000)×20`, ohne Deckel.

| | Sätze | Volumen | XP |
|---|---|---|---|
| Anfänger, Oberkörper | 12 | 2.500 kg | **210** |
| Fortgeschritten, Beine | 18 | 20.000 kg | **630** |

🔴 **Faktor 3,0 — und daran war nichts Verdientes.** Kniebeugen bewegen nun mal mehr Kilo als
Curls. Ein ehrlich harter Oberkörpertag war weniger wert als ein lockerer Beintag, und wer
schon stark war, stieg dreimal so schnell auf. Bis Gigachad (Level 45, 42.240 XP): Anfänger
**15 Monate**, Fortgeschrittener **5**. Dranbleiben zählte in der Formel überhaupt nicht.

**Jetzt:** `Sätze×10 + 50 + Rekord-Sätze×25 + min(Volumen-XP, 100)`

Damit liegen dieselben zwei Einheiten bei **260** und **380** — Faktor **1,5**.

💡 **Die Kilos zählen weiter mit** (Karls ausdrückliche Ansage), aber gedeckelt bei 100 XP.
⚠️ **Der Deckel ist der eigentliche Eingriff, nicht der Rekord-Bonus.** Ohne ihn wächst der
Volumenanteil mit der Kraft unbegrenzt weiter und frisst alles andere auf.

⚠️ **Eine Falle beim Bauen: `sessRecalc()` rechnet XP neu, wenn man eine Einheit im Verlauf
korrigiert.** Ob ein Satz ein Rekord war, hängt aber an der **Historie zum Zeitpunkt des
Trainings** — aus den Sätzen allein ist das nicht herzuleiten. Die Anzahl wird deshalb an der
Einheit festgehalten (`s.pr`) und beim Nachrechnen durchgereicht. Sonst käme beim Bearbeiten
eine andere Zahl heraus als beim Beenden.

💡 Gezählt wird über eine Markierung **am Satz**, nicht beim Klicken — wer abhakt, abwählt und
erneut abhakt, bekäme sonst zweimal Rekord-XP.

#### 2. Tagesaufgaben — drei am Tag, zusammen 30 XP

*Reingeschaut* (5) · *Eingetragen* (10) · *Trainiert* (15).

🔴 **Hier steckt ein Einwand im Produkt statt in einer Rückfrage.** Im Vault steht seit dem
22.08. bewusst: **kein XP fürs Essen**, weil es Level und Rang mit etwas aufbläht, das keine
Anstrengung ist — Brocks Rang sagt dann nichts mehr über das Training aus. Eine Aufgabe
*„App geöffnet"* ist genau derselbe Fall.

➡️ **Gelöst über die Größenordnung, nicht über ein Nein:** höchstens **30 XP am Tag** gegen
**260–380** für eine Einheit. Wer nur die App öffnet, sammelt in einem Monat 150 XP — weniger
als eine einzige Einheit. **Aufgaben schieben an, sie tragen nicht.** Dafür steht eine eigene
Prüfung, die den Abstand festhält.

⚠️ Der Tageswechsel wird **beim Lesen** geprüft, nicht per Timer. Ein Timer um Mitternacht
liefe nur, solange die App offen ist — und nachts ist sie es nie.

#### 3. Erfolge — neuer Reiter zwischen Kalorien und Einstellungen

**18 Erfolge in fünf Gruppen:** Training, Volumen, Rekorde, Dranbleiben, Rang, Körper.

⚠️ **Alles wird gerechnet, nichts gespeichert.** Ein gespeicherter Erfolg geht beim Abmelden
verloren oder hängt nach einer korrigierten Einheit in der Luft — dann steht ein Haken an
etwas, das die Daten nicht mehr hergeben. Dieselbe Entscheidung wie beim Essens-Serienrekord.

💡 **Jeder Erfolg hat einen Zählerstand, auch die einmaligen.** *47 von 50* ist ein Grund
weiterzumachen, ein graues Feld nicht.

#### 🔴 Ein Fehler beim Bauen, gefunden von einer Prüfung

`wochenSerie()` **gab es schon** — sie zählt die Serie **bis heute** für die Flamme auf der
Startseite. Ich habe eine zweite gleichen Namens danebengestellt, und die bestehende hat sie
still überschrieben. Aufgefallen ist es nur, weil eine Prüfung eine konkrete Zahl erwartet hat.

➡️ Umbenannt in **`besteWochenSerie()`** — und das ist auch inhaltlich richtig: **für einen
Erfolg braucht es die längste Serie je, nicht die laufende.** Sonst verschwindet eine Trophäe
wieder, sobald die Serie reißt. **Geschafft bleibt geschafft.**
⚠️ Dazu benutzt sie jetzt `wochenStart()`, den Wochenbegriff der App (Montag 00:00). Meine
erste Fassung hatte eine eigene Wochenrechnung — die hätte an einer Stelle Montag und an einer
anderen Donnerstag gemeint.

**Prüfungen: 460 → 486.**
✅ **Fünfmal gegengeprobt**, jedes Mal fällt genau das um, was der Rückbau kaputt macht:
Volumen-Deckel raus → 2 · Rekord-Bonus raus → 2 · Namenskollision zurück → **kompletter
Abbruch** · Aufgaben-Sperre raus → 1 · Reiter ans Ende → 1.
⚠️ **Die erste Fassung der Reiter-Gegenprobe war falsch gebaut** (nur ein Attribut gesetzt
statt den Knopf zu verschieben) und sah deshalb wie eine schwache Prüfung aus. Richtig gebaut
fällt sie um. **Eine Gegenprobe, die nichts kaputt macht, beweist nichts.**

## 2026-08-25

### 🔴 v30 — die Antwort ist jetzt zu sehen, ohne dass man sie sucht

**Karls Frage:** *„Bau, dass man die Nachricht direkt sieht — oder zieht das Nachteile mit
sich?"* Es zieht genau **einen** nach sich, und der ist in dieser Fassung ausgeräumt (unten).

v29 hat dafür gesorgt, dass die App von einer Antwort **erfährt**. Sie zu **sehen** war
weiterhin Glückssache: die rote Zahl saß nur *in* den Einstellungen auf der Karte *Problem
melden* — also erst, nachdem man dort hingegangen war. Wer auf die Mitteilung tippte, landete
auf der Startseite, und dort deutete nichts auf eine Antwort hin.
🔴 **Eine Benachrichtigung, die man nur findet, wenn man ohnehin nachsieht, ist keine.**

**Zwei Wege, beide gebaut:**

#### Die rote Zahl steht an der unteren Leiste

Am **Zahnrad**, weil das Postfach dort drin liegt. ⚠️ **Nicht an „Trainieren"** — eine Zahl
an einer Stelle, hinter der nichts steckt, wäre schlimmer als keine. Ab zehn steht `9+` da.

#### Auf die Mitteilung tippen führt direkt ins Postfach

Zwei Fälle, weil das Handy zwei kennt: **war die App noch offen**, schickt der Service Worker
eine Nachricht ins bestehende Fenster; **war sie zu**, wird sie mit `#postfach` geöffnet.
⚠️ Die Raute wird sofort wieder aus der Adresszeile genommen — sonst landet jedes spätere
Neuladen erneut im Postfach.
⚠️ **Warum überhaupt eine Nachricht und kein einfaches `focus()`:** das offene Fenster weiß
nichts von der Mitteilung. `focus()` allein holt genau die Seite nach vorn, auf der nichts
steht — also den Zustand, den Karl gemeldet hat.

#### 🔴 Der eine Nachteil — und was dagegen steht

**Wer zwischen zwei Sätzen aufs Handy schaut, würde mitten aus seinem Training gerissen.**
Die Zeit läuft weiter, halb eingetippte Sätze stehen da, und der Weg zurück ist ein
Suchspiel. Das ist kein Randfall — es ist **die** Situation, in der die App benutzt wird.

➡️ **Deshalb springt sie nicht, solange ein Training läuft.** Dann bleibt es bei der roten
Zahl, und man geht hin, wenn man fertig ist. 💡 **Die Zahl muss in dem Fall trotzdem
erscheinen** — sonst wäre das Nicht-Springen ein stilles Verschlucken statt eines Aufschubs.
Dafür steht eine eigene Prüfung.

**Prüfungen: 451 → 460.**
✅ **Dreimal gegengeprobt**, jedes Mal fällt genau das um, was der Rückbau kaputt macht:
Wache gegen laufendes Training raus → 2 Prüfungen; Punkt an der Leiste raus → 3; `postMessage`
im Service Worker raus → 1.

⚠️ **Was dabei auffiel und hier stehen bleibt: `sw.js` läuft in den Prüfungen nie.** Ein
Service Worker hat eine eigene Umgebung, und headless registriert ihn nicht. Sein Quelltext
wird jetzt als Zeichenkette hereingereicht, damit der Weg von der Mitteilung ins Fenster
wenigstens **nachgelesen** werden kann. **Das ist Lesen, kein Ausführen** — wer glaubt, der
Service Worker sei damit geprüft, irrt sich.

### 🔔 v29 — die Antwort war da, die App zeigte sie nur nicht

**Karls Meldung:** *„benachrichtigt wurde ich auch, als ich dann aber auf die App gegangen
bin, war die Nachricht nicht da. Erst als ich die App einmal neugestartet habe."*

Der erste Fehler, den die **echte Benutzung** gefunden hat — der Push kam am 25.08. um 06:26
zum ersten Mal überhaupt auf einem Gerät an, und derselbe Handgriff legte den Fehler dahinter
frei. Auf dem Prüfstand wäre er nie aufgefallen: dort startet die App bei jedem Durchlauf neu,
und genau der Neustart hat ihn versteckt.

**Zwei Ursachen, beide behoben.**

#### 1. Verglichen wurde die Anzahl der Zeilen, nicht ihr Inhalt

Am Ende von `renderMeldung()` stand:

```js
postfachHolen().then(rows => { if(rows.length !== post.length) renderMeldung(); });
```

⚠️ **Eine Antwort legt keine Zeile an — sie füllt `antwort` in einer bestehenden.** Die Anzahl
blieb also gleich, die Bedingung war falsch, und neu gezeichnet wurde nie. Die Antwort **war
längst geholt und im Gerät gespeichert**; nur der Bildschirm zeigte weiter den alten Stand.
Deshalb stand sie nach einem Neustart da: dann wurde der Spiegel frisch gezeichnet.

Jetzt entscheidet `postfachGeaendert()` über einen Fingerabdruck aus `id`, `antwort` und
`gelesen_am`. 💡 **Der Meldetext geht bewusst nicht ein** — er liegt fest, sobald die Meldung
raus ist. Etwas zu beobachten, das sich nicht ändern kann, macht keine Prüfung besser.

⚠️ **Warum das eine eigene Funktion ist und nicht eine Zeile im Zeichnen:** hinge die Prüfung
an der Signatur statt an der Entscheidung, wäre sie **grün aus dem falschen Grund** — ein
Rückfall auf den Anzahl-Vergleich fiele niemandem auf. Genau dieser Fehler ist am 24.08. bei
der `@`-Prüfung aufgetreten.

#### 2. Nichts fragte den Server, außer man ging von Hand ins Postfach

`postfachHolen()` wurde an **zwei** Stellen gerufen: beim Zeichnen des Postfachs und nach dem
Abschicken einer Meldung. **Nicht beim Start, nicht beim Zurückkommen in die App.**

🔴 **Die Folge war größer als der sichtbare Fehler:** der Push weckte das Gerät, aber die App
fragte nirgends nach. Die rote Zahl an *Problem melden* blieb auf 0, weil sie nur den lokalen
Spiegel zählt. Wer auf die Mitteilung tippte, landete auf der Startseite — und dort deutete
**nichts** darauf hin, dass eine Antwort da war.

Jetzt wird beim Start und beim Zurückkommen nachgesehen, und nur bei einer echten Änderung neu
gezeichnet. ⚠️ **Eigene Bremse (5 s), nicht die 30 s vom Abgleich:** wer auf die Mitteilung
tippt, ist sofort in der App — dann muss die Antwort da sein, nicht eine halbe Minute später.

**Prüfungen: 445 → 451.**
✅ **Gegengeprobt:** setzt man den Anzahl-Vergleich wieder ein, fällt *„Eine Antwort löst ein
Neuzeichnen aus, obwohl die Anzahl gleich bleibt"* um. Ohne den Rückbau wäre nicht zu sehen
gewesen, ob die Prüfung den Fehler wirklich fängt.

## 2026-08-24

### 🔒 Angemeldet wird nur noch mit E-Mail

Der letzte offene Punkt aus dem Abgleich gegen [[angel-log]], das dieselbe Funktion am
**18.08.2026 entfernt hat** (v56).

Bis v27 ging Anmelden mit **E-Mail oder Benutzername**. Stand kein `@` in der Eingabe, holte
die App über die Datenbank-Funktion `email_for_username` erst die zugehörige Adresse. Diese
Funktion war für `anon` freigegeben und **musste** es sein — gefragt wird, bevor jemand
angemeldet ist.

🔴 **Die Folge: wer einen Benutzernamen kannte oder erriet, bekam die E-Mail dazu.**
Am 24.08. live nachgemessen, mit dem öffentlichen Schlüssel aus dem Quelltext der App —
also mit dem, was jeder Besucher der Seite ohnehin hat: **HTTP 200, erreichbar ohne
Anmeldung.**

⚖️ **Ehrlich zur Größenordnung:** an die Trainingsdaten kam dadurch nie jemand, dafür sorgt
RLS. Es ging allein um die Adresse. Der Grund fürs Zumachen bleibt trotzdem gut — **es ist
die einzige Sache an dieser App, die sich hinterher nicht reparieren lässt.** Herausgegebene
Adressen holt man nicht zurück, und man erfährt nicht einmal, dass es passiert ist.

- **Registrieren** bleibt unverändert: Benutzername + E-Mail + Passwort. Der Benutzername
  bleibt **Anzeigename**.
- **Anmelden** geht nur noch mit E-Mail. Das Feld ist jetzt ein echtes E-Mail-Feld
  (`type`, `inputmode`, `autocomplete`) — am Handy kommt damit die Tastatur mit `@`.
- Wer seinen Namen eintippt, bekommt einen **eigenen Satz** („Zum Anmelden brauchst du deine
  E-Mail-Adresse, nicht deinen Benutzernamen.") statt „Anmelden hat nicht geklappt" — sonst
  hielte er sein Passwort für falsch und probierte es immer wieder.

⚠️ **Was NICHT gewonnen ist:** `username_taken` bleibt öffentlich und **muss** es bleiben —
die Registrierung fragt damit. **Ob es einen Namen gibt, ist weiterhin abfragbar**, nur die
E-Mail dahinter nicht mehr.

#### 💡 Die Bequemlichkeit kommt an anderer Stelle zurück

Die zuletzt an **diesem Gerät** benutzte Adresse steht beim nächsten Anmelden im Feld.

- Eigener Speicherschlüssel, **nicht im Konto** — `clearSession()` räumt beim Abmelden das
  Konto weg, und genau danach soll sie ja noch dastehen. Sie überlebt das Abmelden und
  stirbt nur mit „Konto löschen".
- **Beim Registrieren bleibt das Feld leer.** Dort wäre es die Adresse eines anderen Kontos,
  und das fällt beim Tippen niemandem auf.
- Sie verlässt das Gerät nicht (reiner `localStorage`) und steht deshalb auch nicht in der
  Datenschutzerklärung bei den Wegen nach außen. Dafür gibt es zwei eigene Prüfungen.

🔴 **Ein Handgriff liegt bei Karl:** `supabase-email-schliessen.sql` einmal ausführen.
**Ein `git push` liefert die Datenbank nicht mit aus** — bis dahin ist die Funktion dort
weiter offen, auch wenn die App sie nicht mehr ruft. Es steht ein `drop function` in der
Datei, kein bloßes `revoke`: ein stehengebliebener `grant` hätte sie wieder geöffnet.

**Prüfungen: 435 → 445.**

✅ **Gegengeprobt: 9 der 10 neuen fallen gegen v27 um.** Die eine, die grün bleibt, ist der
Regressions-Wächter „`username_taken` wird weiter benutzt" — und der war zu Recht schon grün.
⚠️ **Dabei ist eine Prüfung aufgefallen, die grün war aus dem falschen Grund:** „wird auf `@`
geprüft" traf auch auf v27 zu — die prüft ebenfalls auf `@`, nur um danach **nachzuschlagen
statt abzubrechen**. Jetzt wird geprüft, dass auf die `@`-Prüfung ein `throw` folgt.


### 🔑 „Passwort vergessen" gibt es jetzt — und die Datenschutzerklärung kennt die ganze App

Beides aus Karls Ansage nach einem Abgleich gegen Angel-Log: *„check mal im allgemeinen die
app auf probleme die wir schon in der angel app hatten"*. Angel-Log ist sechs Wochen weiter
und hat diese Fehler schon bezahlt — hier ist der übernommene Teil.

#### 🔑 Der Weg zurück ins eigene Konto

Bis heute gab es **keinen**. Wer sein Passwort vergaß, war endgültig ausgesperrt — ohne Konto
ist die App nicht benutzbar, der Anmelde-Schirm liegt deckend über allem. Genau das ist Karl
am 18.08. bei [[angel-log]] selbst passiert, und seit dem 23.08. testet Bruno diese App.

Übernommen aus Angel-Log v57–v59, samt der dort teuer gelernten Feinheiten:

- **Eine Stunde Pause zwischen zwei Links** — 🔴 keine Sicherheitssperre, sie steht im
  `localStorage`. Der eingebaute Mailversand ist im Gratis-Tarif auf **2 Mails je Stunde**
  gedeckelt, und zwar **projektweit**. Ein Ungeduldiger, der dreimal drückt, verbraucht
  sonst beide Plätze der Stunde für alle anderen.
- **Der Schlüssel ist die Adresse, nicht das Gerät.** Wer beim ersten Versuch das falsche
  Konto erwischt, muss sofort das richtige probieren dürfen — geräteweit hätte die Bremse
  genau die richtige Handlung bestraft.
- **Gebremst wird vor dem Absenden, gesetzt erst nach dem Erfolg.** Eine Bremse danach hat
  den Platz schon verbraucht; und ein Vertipper darf niemanden aussperren, ohne dass
  überhaupt eine Mail unterwegs ist.
- **Das neue Passwort wird zweimal eingegeben.**
- **Der Token wird sofort aus der Adresszeile geräumt** — ein Zugangs-Token im Verlauf des
  Browsers ist genau das, was man nicht will, und beim Teilen der Adresse ginge er mit.
- **Der abgelaufene Link bekommt einen eigenen Satz** statt eines wortlosen Schirms.
- ⚠️ **Es wird nicht verraten, ob es die Adresse gibt** — weder durch die Meldung noch durch
  die Bremse. Sonst wäre das ein Nachschlagedienst „hat diese Adresse ein Konto?".
- 💡 **Wer das Passwort gesetzt hat, ist danach angemeldet.** Der Token aus der Mail *ist*
  eine gültige Sitzung — sonst wäre gleich der nächste Moment der, in dem man wieder scheitert.

🔴 **Ein Handgriff liegt bei Karl:** `https://karlm-netizen.github.io/gym-log/` muss in
Supabase unter **Authentication → URL Configuration → Redirect URLs** stehen. Fehlt sie,
schickt Supabase den Link stillschweigend woandershin — **und antwortet trotzdem mit 200**.
Von der App aus ist das nicht zu sehen.

#### 📜 Die Datenschutzerklärung stand auf dem 6. August

Seither sind **Schritte**, **Push** und der **Melde-Knopf** dazugekommen — keiner davon war
beschrieben. Und ein Satz stimmte dadurch nicht mehr: *„deine gespeicherten Daten verlassen
die EU nicht."*

- **Der Discord-Weg steht jetzt drin** — mit allem, was an einer Meldung mitgeht (Username,
  Fassung, Browser-Kennung, Bildschirm, online/offline, Anzahl der Einheiten, letzter
  Abgleich) und dem klaren Satz, dass sie damit die EU verlässt (Discord Inc., USA).
- **Schritte** stehen in der Datenliste, mit dem Hinweis, dass die Zahl aus dem Kurzbefehl
  kommt und die App keine Gesundheitsdaten selbst liest.
- **Die Push-Kennung** steht drin, samt „ohne Push wird nichts gespeichert".
- **Rechtsgrundlage** ergänzt: Gewicht, Schritte und Benachrichtigungen sind Einwilligung
  (Art. 6 Abs. 1 lit. a), zurücknehmbar über den jeweiligen Schalter.
- Aus „zwei Ausnahmen" sind **drei Fälle** geworden (Barcode, Foto, Meldung).
- **Stand: 24. August 2026.**

**Prüfungen: 415 → 435.**

✅ **Gegengeprobt:** die neuen Prüfungen gegen die Fassung von vorhin laufen lassen —
**19 der 20 fallen um.** Die eine, die grün bleibt, ist die Negativ-Prüfung („beim
Registrieren steht *kein* Vergessen-Link"), und die war vorher zu Recht grün.

⏭️ **Nicht mitgemacht:** `email_for_username` ist weiter offen. Angel-Log hat die Funktion am
18.08. entfernt, weil sie fremde E-Mail-Adressen herausgibt; live nachgemessen antwortet sie
bei Gym-Log ohne Anmeldung mit HTTP 200. Das braucht ein `drop function` in Supabase und
steht als eigener Punkt.


### 🔀 Der Abgleich führt jetzt zusammen, statt zu überschreiben

**Beim Beheben des Gewichts-Fehlers daneben gefunden** — und es war die größere Hälfte.

Der Abgleich schickte immer den **ganzen** Datenblock, und beim Start galt:
`if(dirty) schieben, sonst holen`. Ein Gerät mit einer **einzigen** ungesicherten Änderung
holte damit **nie** — es schob seinen Stand über den anderen. Zwei Geräte konnten sich so
gegenseitig Trainings und Gewichtseinträge löschen, ohne dass irgendwo etwas gemeldet wurde.

**Was jetzt passiert:** beim Start wird **immer erst geholt**, dann zusammengeführt, dann
bei Bedarf geschoben.

- **Trainings** werden über ihre Kennung vereinigt — was auf einem Gerät fehlt, kommt dazu.
- **Die Gewichtskurve** wird tageweise vereinigt. Steht für denselben Tag auf beiden Seiten
  ein Wert, gewinnt der spätere — dieselbe Regel, die `addWeight()` schon immer hatte.
- ⚠️ **XP kommt mit.** Der Punktestand steht gespeichert im Profil, er wird nicht aus den
  Einheiten gerechnet. Übernommene Einheiten bringen ihren Wert deshalb mit, sonst zeigte
  der Rang weniger an, als der Verlauf darunter hergibt.
- **Beim Zurückkommen in die App** wird nachgesehen, ob am anderen Gerät etwas dazukam
  (höchstens alle 30 s). Ohne das sähe ein PC, der den ganzen Tag offen steht, die
  Einheiten vom Handy nie.

💡 **Bewusst NICHT zusammengeführt: Pläne und Einstellungen.** Dort gilt weiter „wer zuletzt
sendet, gewinnt". Die ändert man bewusst an einem Gerät — und ein überschriebener Plan ist in
zwei Minuten neu getippt, drei verlorene Trainingseinheiten nicht.

**Prüfungen: 395 → 415.** Fassung **v26**.

✅ **Gegengeprobt:** stellt man das alte Überschreiben wieder her, fallen **neun** der neuen
Prüfungen um. Eine Prüfung, die auch ohne den Einbau grün ist, prüft nichts.


### ⚖️ Gewichtseinträge kamen nicht in der Cloud an

**Karls Meldung:** *„die eintragungen beim gewicht werden nicht gesyned"*.

Die Ursache lag **nicht im Eintragen** — `addWeight()` und `save()` sind seit dem 22.08.
geprüft und stimmen. Sie lag im Weg in die Cloud: gesendet wurde erst **2 Sekunden nach
der letzten Änderung** (`scheduleSync`), und es gab **keinen einzigen Handler**, der
vor dem Schließen noch schnell sichert.

💡 **Warum das ausgerechnet beim Gewicht auffällt und sonst nie:** Wiegen dauert fünf
Sekunden — Zahl eintippen, „Eingetragen", Handy weglegen. Die Seite friert ein, der Timer
feuert nie, der Eintrag bleibt auf dem Gerät liegen. Bei einem Training passiert genau
dasselbe, fällt aber nicht auf, weil man danach noch 45 Minuten in der App ist und der
nächste Handgriff die Sicherung nachholt.

**Eingebaut:**
- `flushSync()` — sendet sofort statt zu warten, sobald etwas Ungesichertes offen ist.
- Zwei Auslöser, weil kein Browser beide zuverlässig meldet: **`visibilitychange`**
  (Wegwischen, Bildschirm aus) und **`pagehide`** (echtes Schließen).
- `cloudPush(true)` setzt **`keepalive`** — damit sendet der Browser die Anfrage zu Ende,
  auch wenn die App schon zu ist. ⚠️ Nur bis **64 KB** Körper erlaubt, darüber wirft
  `fetch`; oberhalb wird deshalb normal gesendet statt gar nicht.
- Doppelt gesendet wird nichts: `flushSync` prüft `dirty` und löscht den wartenden Timer.

**Prüfungen: 387 → 395.** Fassung **v25**.

✅ **Gegengeprobt, nicht geglaubt:** mit entfernten Handlern fallen genau die drei neuen
Prüfungen um (`Wegschalten sendet sofort`, `Beim Wegschalten mit keepalive`,
`Schliessen sendet sofort`). Eine Prüfung, die auch ohne den Einbau grün ist, prüft nichts.

## 2026-08-23

### 🔔 Push nachgezogen — der Melde-Kreis war noch offen

⚠️ **Beim Testen aufgefallen:** das Bot-Protokoll meldete *„#1: keine Geräte angemeldet"*.
Der Grund war nicht die fehlende Anmeldung, sondern dass **Gym-Log überhaupt keinen
Push-Code hatte** — weder eine Anmeldung in der App noch einen `push`-Handler im Service
Worker. `gym_push.py` und die Tabelle waren gebaut, aber es gab niemanden, an den zu senden
gewesen wäre. „Alles wie bei Angel-Log" war damit noch nicht erfüllt.

Jetzt übernommen, samt der bei [[angel-log]] teuer gelernten Feinheiten:
- **Ohne Nutzlast** — der Meldetext ginge sonst durch die Server von Apple bzw. Google.
- **`showNotification` ist Pflicht:** wer ein Push-Ereignis empfängt und nichts anzeigt,
  wird nach ein paar Malen von der Zustellung ausgeschlossen.
- **Der Titel IST die Nachricht** — iOS setzt den App-Namen ohnehin darüber; ihn zu
  wiederholen ergab bei Angel-Log drei Zeilen, von denen zwei dasselbe sagten.
- **Bei einem Fehlschlag wird die Anmeldung im Gerät wieder aufgelöst** — sonst stünde der
  Schalter auf „an", während niemand weiß, wohin gesendet werden soll.
- Der Schalter unterscheidet **drei** Zustände: geht hier nicht / abgelehnt / an oder aus.

💡 **Derselbe VAPID-Schlüssel wie Angel-Log** — die Schlüssel gehören zum Absender, nicht
zum Supabase-Projekt. Es sendet derselbe Bot.

**Prüfungen: 383 → 387.** Fassung **v24**.

### 🐞 Problem melden — Formular, Postfach, Antworten aus Discord

**Karls Entscheidung vom 22.08.:** *„alles wie bei Angel-Log"*. Jetzt fertig.

**In der App:** „Problem melden" in den Einstellungen — Formular oben, eigenes Postfach
darunter. Antworten kommen mit roter Zahl am Eintrag zurück.

⚠️ **Die Meldung wird zuerst im Gerät abgelegt, dann verschickt.** Im Studio ist der Empfang
oft weg (Keller, Stahlbeton) — genau dort wird die App benutzt. „Abgeschickt" darf keine
Behauptung sein, die am Netz hängt.

⚠️ **Verschickt wird einzeln, nicht als Stapel.** Die Bremse (5 je 10 Minuten) wäre sonst
eine Falle: eine abgewiesene Zeile nimmt in PostgreSQL die ganze Anweisung mit — auch die
Meldungen daneben, die in Ordnung waren. Die lägen weiter im Gerät und würden **für immer**
zusammen abgewiesen. Bei [[angel-log]] am 12.08. genau deshalb umgebaut.

⚠️ **`lastSync` wurde nirgends geschrieben** — im Umfeld jeder Meldung hätte darum immer
„nie" gestanden. Wird jetzt bei jedem gelungenen Abgleich gesetzt.

**Im Bot:** `gym_antworten.py` und `gym_push.py`. `bot.py` bedient jetzt **beide Apps**.
⚠️ Sie schreiben in **denselben Kanal**, unterschieden werden sie allein an der ersten Zeile
(`🏋 Gym-Log — Meldung #7` gegen `🐞 Angel-Log — Meldung #7`) — die Nummernkreise
laufen unabhängig, es gibt beide Nummern. Im Nachhol-Lauf ist der Schlüssel deshalb
(App, Nummer) und nicht die Nummer allein.
⚠️ **Verschiedene Supabase-Projekte:** eigene `GYM_SUPABASE_*`-Variablen. Nur die
VAPID-Schlüssel werden geteilt — die gehören zum Absender, nicht zum Projekt.

⚠️ **Im SQL fehlte die Tabelle `gym_push`** — ohne sie hätte es Antworten nur beim nächsten
Öffnen gegeben. Als Abschnitt 4b nachgetragen; **muss noch ausgeführt werden.**

**Prüfungen: 375 → 383.** Fassung auf **v23**.

### 🏋️ Die Übungsliste wächst von 80 auf 672

**Karls Ansage:** *„wir müssen die Einheitenliste bearbeiten, da sie unvollständig ist — lass
uns mal eine Website suchen, die alle hat."*

**Gefunden: [wger.de](https://wger.de)** — offene Datenbank, freie API, kein Schlüssel nötig.
💡 **Nachgemessen statt geglaubt:** beworben werden „845+", davon tragen aber nur **628**
einen deutschen Namen — und das ist die Zahl, auf die es bei einer deutschen App ankommt.

⚠️ **Ergänzt, nicht ersetzt — der Befund, der die Richtung bestimmt hat.** Ein Abgleich zeigte:
von Karls 80 Übungen fehlen **14 bei wger**, darunter SZ-Curls, Scott-Curls, Bulgarian Split
Squat, Step-Ups und Ab-Wheel Rollout. Ein Austausch hätte sie verloren. Karls Liste steht
deshalb unverändert und **weiterhin zuerst**; die 592 neuen hängen dahinter.

⚠️ **Dubletten über normalisierte Namen abgefangen** (34 Stück): wgers „Bankdrücken LH" ist
Karls „Bankdrücken". Ohne das stünde dieselbe Übung zweimal in der Auswahl.

⚠️ **Icon und Wiederholungen kommen aus der wger-Kategorie, nicht aus dem Namen.**
`guessIcon()` würde bei über 500 unbekannten Namen raten, und jeder Fehlgriff ist ein falsches
Bild neben einer Übung — genau der Fehler vom 22.08. („Klimmzüge").

⚖️ **Lizenz CC-BY-SA**, die Namensnennung steht jetzt unten in der Übungsauswahl.

⚠️ **Ein Fehler beim Erzeugen, den der Prüfrahmen gefangen hat:** zwei Namen mit Apostroph
(„Butcher's Block Dehnung", „Devil's Press") waren nicht escaped und haben das **gesamte
Skript** lahmgelegt — die App startete nicht mehr. Ohne Prüfrahmen wäre das live gegangen.

**Prüfungen: 369 → 375.**

### 🍽️ Der Ernährungs-Teil bekommt vier Mahlzeiten

**Karls Vorlage** aus Discord — Frühstück / Mittagessen / Abendessen / Snacks, jede mit
eigenem Ziel und eigenem Plus-Knopf. Vorher war der Tag **eine flache Liste**.

💡 **Die Anteile stammen aus Karls Bild, nicht aus dem Lehrbuch:** dort stehen
1.113 / 1.484 / 927 / 185 kcal bei 3.709 kcal Tagesziel — also **30 / 40 / 25 / 5 %**.
Eine Prüfung rechnet genau diese vier Zahlen nach.

⚠️ **Bestandsdaten landen nicht im Sammeltopf.** Alte Einträge haben kein `mz`-Feld. Sie
pauschal auf „Snacks" zu werfen hätte jeden davon falsch einsortiert und die Blöcke von Tag
eins an unbrauchbar gemacht — stattdessen wird die Mahlzeit **aus der Uhrzeit erschlossen**,
die in jedem Eintrag steht.

⚠️ **Das Ziel hängt am Tagesziel des Tages**, nicht am Grundziel — im Schritt-Modus ist es
beweglich, und sonst zeigten die vier Blöcke zusammen etwas anderes an als der Ring darüber.

Der **jetzt fällige Block** ist mit einer Kante hervorgehoben, nicht mit einer Füllung: eine
gefüllte Zeile zwischen drei leeren sieht aus wie „ausgewählt", und ausgewählt ist hier nichts.

**Prüfungen: 360 → 369.**

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
