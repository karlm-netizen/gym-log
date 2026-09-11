# -*- coding: utf-8 -*-
"""
datenschutz-pruefen.py - stimmt die Datenschutzerklaerung noch mit der App ueberein?

Gebaut am 09.09.2026. Karls Ansage: "KI Agenten fuer Datenschutz Erklaerung der
sie immer aktualliesiert ... er muss zu jeder neuen version laufen. er soll auch
pruefen ob das alles so legal ist."

WAS DIESE DATEI TUT UND WAS NICHT
Sie ist der mechanische Teil: sie sammelt die PRUEFBAREN Tatsachen und meldet,
wo die Erklaerung ihnen widerspricht. Ob eine Formulierung rechtlich traegt,
entscheidet sie NICHT - das ist die Aufgabe des Agenten. Seine Rolle steht in
`ki-os-2/.claude/agents/datenschutz-waechter.md`, sein Ablauf im README dieses
Repos unter "Datenschutz". Beides zusammen ist der Waechter; dieses Skript ist
der Teil, der bei jedem Lauf in Sekunden durchlaeuft.
(Der Verweis zeigte bis zum 10.09.2026 auf einen README-Abschnitt, den es nie
gab - ein Wegweiser ins Leere ist schlimmer als keiner.)

WARUM ES SIE BRAUCHT - der Fund vom 09.09.2026
Die Erklaerung sagte beim Essen-Eintragen: "Uebertragen wird nur die Nummer,
nichts ueber dich." Seit dem 03.09. stimmte das nicht mehr: die Textsuche
schickt den eingetippten SUCHBEGRIFF an search.openfoodfacts.org. Sechs Tage
lang stand eine falsche Aussage in einem Rechtstext - und nichts wurde rot.
Genau die Bauform, die dieses Projekt seit dem 25.08. immer wieder trifft.

Aufruf:
    python datenschutz-pruefen.py           Bericht
    python datenschutz-pruefen.py --kurz    nur die Funde
"""

import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

HIER = Path(__file__).resolve().parent
INDEX = HIER / "index.html"
SW = HIER / "sw.js"

# ---------------------------------------------------------------------------
# Was die Erklaerung nennt. Jeder Eintrag ist ein VERSPRECHEN an den Nutzer -
# taucht im Code ein Ziel auf, das hier fehlt, geht etwas hinaus, das niemand
# erklaert hat.
#
# ⚠️ Diese Liste wird VON HAND gepflegt. Das ist Absicht: sie automatisch aus
# der Erklaerung zu lesen hiesse, den Text mit sich selbst zu vergleichen -
# dann waere jede Luecke im Text zugleich eine Luecke in der Pruefung.
ERKLAERTE_ZIELE = {
    "world.openfoodfacts.org":       "Barcode + Ausweichsuche (Open Food Facts, Frankreich)",
    "search.openfoodfacts.org":      "Textsuche (Open Food Facts, Frankreich)",
    "generativelanguage.googleapis.com": "Essens-Foto schaetzen (Google LLC, USA)",
    # 🔴 Supabase stand bis zum 09.09.2026 unter UNBEDENKLICH. Das war falsch:
    # es ist der GROESSTE Datenweg der App - dort liegen alle Trainings, Gewichte,
    # Mahlzeiten und die Bestenliste. Im Bericht stand er als "[unkritisch]".
    # Ein Werkzeug, das den Hauptdatenweg als unkritisch ausweist, gewoehnt einem
    # das Hinsehen ab. (Fund-Sucher, 09.09.2026)
    "uvtxkdasgllnfkvtnkrq.supabase.co": "die eigene Datenbank - ALLE Nutzerdaten "
                                        "(Auftragsverarbeitung, Art. 28 DSGVO)",
}

# Ziele, die im Text stehen duerfen, ohne dass zur Laufzeit etwas hingeht:
# Links, auf die der Nutzer selbst klickt, und die eigene Adresse.
# ⚠️ Was hier steht, wird NICHT weiter geprueft. Jeder Eintrag ist eine Behauptung
# ("dorthin geht zur Laufzeit nichts"), die niemand nachmisst - deshalb gehoert
# hier nur herein, was wirklich nur ein Link ist. Im Zweifel nach ERKLAERTE_ZIELE.
UNBEDENKLICH = {
    "karlm-netizen.github.io":  "die App selbst",
    "aistudio.google.com":      "Link zum Schluessel-Holen, oeffnet sich nur auf Klick",
    "myaccount.google.com":     "Link zu Googles eigenen Angaben, nur auf Klick",
    "wger.de":                  "Quelle der Uebungsliste, EINMALIG uebernommen - "
                                "zur Laufzeit geht nichts dorthin",
}

# Discord wird nicht vom Browser gerufen, sondern von der Supabase-Funktion.
# Steht in der Erklaerung und laesst sich hier nicht messen - deshalb als
# Merkposten, damit niemand denkt, die Pruefung haette ihn uebersehen.
NICHT_MESSBAR = [
    ("Discord (USA)", "Problemmeldungen gehen ueber eine Supabase-Funktion hinaus, "
                      "nicht aus dem Browser. In supabase-meldungen.sql nachsehen."),
]

_funde = []


def fund(schwere, text, *zeilen):
    _funde.append((schwere, text, zeilen))


def lies(pfad):
    return pfad.read_text(encoding="utf-8", errors="replace") if pfad.is_file() else ""


# ---------------------------------------------------------------------------
def kommentare_weg(quelltext):
    """Blockkommentare und HTML-Kommentare entfernen.

    Ohne das schlaegt die Pruefung bei wger.de an - der Host steht nur in einem
    Kommentar, der erklaert, WOHER die Uebungsliste stammt. Zur Laufzeit geht
    dorthin nichts. Eine Pruefung, die auf Kommentare anspringt, wird nach dem
    dritten Fehlalarm nicht mehr gelesen.
    """
    ohne = re.sub(r"/\*.*?\*/", " ", quelltext, flags=re.S)
    ohne = re.sub(r"<!--.*?-->", " ", ohne, flags=re.S)
    return ohne


def ziele_im_code(quelltext):
    """Alle Hosts, die im echten Code stehen (ohne Kommentare)."""
    return set(re.findall(r"https?://([a-zA-Z0-9.-]+)", kommentare_weg(quelltext)))


def pruefe_ziele():
    """Geht etwas hinaus, das die Erklaerung nicht nennt?"""
    quelltext = lies(INDEX) + "\n" + lies(SW)
    gefunden = ziele_im_code(quelltext)
    bekannt = set(ERKLAERTE_ZIELE) | set(UNBEDENKLICH)

    for host in sorted(gefunden - bekannt):
        fund("SCHWER", f"Unbekanntes Ziel im Code: {host}",
             "Es steht weder in der Datenschutzerklaerung noch in der Liste der",
             "unbedenklichen Links. Entweder gehoert es in die Erklaerung, oder",
             "es gehoert in UNBEDENKLICH - aber nicht stillschweigend in den Code.")

    # Umgekehrt: nennt die Erklaerung etwas, das es im Code nicht mehr gibt?
    for host in sorted(set(ERKLAERTE_ZIELE) - gefunden):
        fund("HINWEIS", f"Erklaert, aber im Code nicht mehr da: {host}",
             f"Die Erklaerung nennt es als \"{ERKLAERTE_ZIELE[host]}\".",
             "Eine Erklaerung, die mehr verspricht als passiert, ist kein Schaden -",
             "aber sie ist falsch, und beim naechsten Lesen glaubt sie jemand.")
    return gefunden


def pruefe_stand():
    """Ist PRIVACY_STAND juenger als die letzte Aenderung an der Erklaerung?

    Das ist die eigentliche Falle: der Text wird angefasst, das Datum darunter
    nicht. Dann steht "Stand: 24. August" unter einem Text vom 6. September.
    """
    quelltext = lies(INDEX)
    m = re.search(r"PRIVACY_STAND\s*=\s*['\"]([^'\"]+)['\"]", quelltext)
    if not m:
        fund("SCHWER", "PRIVACY_STAND nicht gefunden",
             "Ohne Datum weiss niemand, welchen Stand er gerade liest.")
        return None
    stand_text = m.group(1)

    monate = {"januar": 1, "februar": 2, "maerz": 3, "märz": 3, "april": 4, "mai": 5,
              "juni": 6, "juli": 7, "august": 8, "september": 9, "oktober": 10,
              "november": 11, "dezember": 12}
    m2 = re.match(r"(\d{1,2})\.\s*([A-Za-zÄÖÜäöü]+)\s*(\d{4})", stand_text)
    if not m2:
        fund("HINWEIS", f"PRIVACY_STAND ist '{stand_text}' - Datum nicht lesbar")
        return None
    tag, monat_wort, jahr = int(m2.group(1)), m2.group(2).lower(), int(m2.group(3))
    if monat_wort not in monate:
        fund("HINWEIS", f"PRIVACY_STAND: Monat '{monat_wort}' unbekannt")
        return None
    stand = date(jahr, monate[monat_wort], tag)

    # --- 1. Der Arbeitsbaum: gibt es JETZT ungesicherte Aenderungen am Text? ---
    # Das ist der Fall, den der Hook erwischen muss - er laeuft vor dem Commit.
    arbeitsbaum = ungesicherte_aenderung_am_abschnitt()
    if arbeitsbaum == "git-klemmt":
        fund("SCHWER", "Der Arbeitsbaum liess sich nicht pruefen (git antwortet nicht)",
             "Damit faellt genau die Pruefung aus, die VOR dem Commit greifen soll.",
             "Kein Repo? Kaputter Index? `git status` von Hand nachsehen.")
    elif arbeitsbaum == "abschnitt-weg":
        # ⚠️ Nicht als "geaendert" durchwinken: `"abschnitt-weg"` ist wahr, und ein
        # truthy Rueckgabewert haette hier still einen falschen Fund erzeugt.
        # Der Abschnitt ist NICHT auffindbar - das ist ein Defekt der Pruefung
        # selbst und muss als solcher dastehen.
        fund("SCHWER", "Die Erklaerung ist in index.html nicht auffindbar",
             "Gesucht wurde `function renderPrivacy` bis zur schliessenden Klammer.",
             "Solange das so ist, prueft nichts mehr, ob der Stand zum Text passt.")
    elif arbeitsbaum is True and stand != date.today():
        fund("SCHWER",
             f"Die Erklaerung ist gerade geaendert worden, PRIVACY_STAND steht "
             f"auf dem {stand:%d.%m.%Y}",
             "Die Aenderung ist noch nicht committet - genau der Zustand, in dem der",
             "Hook laeuft. Vor dem Commit das Datum mit hochziehen.")

    # --- 2. Die Historie: committete Aenderungen, deren Datum vergessen wurde ---
    letzte, git_fehler = letzte_aenderung_am_abschnitt()
    if git_fehler:
        # 🔴 Nicht schweigen. Frueher wurde daraus still None, und der Bericht
        # sagte "keine Funde" - eine Pruefung, die ausgefallen ist, sah aus wie
        # eine Pruefung, die nichts gefunden hat.
        fund("SCHWER", "Die Datums-Pruefung konnte nicht laufen",
             git_fehler,
             "Solange das so ist, faellt ein vergessener PRIVACY_STAND nicht mehr auf.",
             "Entweder den Namen in dieser Datei nachziehen (Suchmuster in",
             "letzte_aenderung_am_abschnitt) oder die Funktion zurueckbenennen.")
    elif letzte and letzte > stand:
        fund("SCHWER",
             f"Die Erklaerung wurde am {letzte:%d.%m.%Y} geaendert, "
             f"PRIVACY_STAND steht auf dem {stand:%d.%m.%Y}",
             "Unter einem geaenderten Text steht ein altes Datum. Wer wissen will,",
             "ob er die aktuelle Fassung liest, wird in die Irre gefuehrt.")
    return stand


def erklaerungs_zeilen():
    """Welche Zeilen von index.html gehoeren zur Datenschutzerklaerung?

    Gibt eine Liste von (von, bis) zurueck, 1-basiert und einschliesslich.
    Zwei Bereiche: die Funktion `renderPrivacy` und die PRIVACY_-Konstanten,
    die weit oben stehen (Verantwortlicher, Kontakt, Stand).

    Ist die Funktion nicht zu finden, gibt es None - der Aufrufer macht daraus
    einen lauten Fund, keine stille Null.
    """
    zeilen = lies(INDEX).splitlines()
    von = bis = None
    for i, z in enumerate(zeilen, start=1):
        if z.startswith("function renderPrivacy"):
            von = i
            continue
        if von and bis is None and z.rstrip() in ("}", " }"):
            bis = i
            break
    if von is None or bis is None:
        return None

    bereiche = [(von, bis)]
    konst = [i for i, z in enumerate(zeilen, start=1) if z.startswith("const PRIVACY_")]
    if konst:
        bereiche.append((min(konst), max(konst)))
    return bereiche


def ungesicherte_aenderung_am_abschnitt():
    """Wurde die Erklaerung geaendert, ohne dass es schon committet ist?

    🔴 WARUM ES DIESE FUNKTION GIBT (Fund-Sucher, 09.09.2026):
    Die Pruefung lief urspruenglich NUR ueber `git log -L`. Das liest committete
    Historie - der Hook laeuft aber als PostToolUse, also IMMER vor dem Commit.
    Damit konnte die Pruefung genau die Aenderung, wegen der sie gestartet wurde,
    prinzipiell nicht sehen.

    🔴 UND WARUM SIE AM 10.09.2026 NEU GESCHRIEBEN WURDE (Fund-Sucher, Nachlauf):
    Die erste Fassung suchte in den geaenderten ZEILEN nach acht Stichwoertern
    ("Datenschutz", "Bestenliste", "DSGVO" ...). Das ging in beide Richtungen
    daneben, beides nachgemessen:
      · 146 der 160 Zeilen von renderPrivacy tragen KEINES dieser Woerter -
        darunter woertlich die Saetze, um die es an dem Tag ging. Wer einen
        davon aendert und den Stand stehen laesst, bekam keinen Fund.
      · "Bestenliste" steht 13x in gewoehnlichem Code ausserhalb der Erklaerung.
        Von den letzten 14 Commits haetten drei den Check ausgeloest, zwei davon
        zu Unrecht - und weil die Pruefung seit dem 09.09. in `pruefungen.py`
        haengt, waere der einzige Weg durch gewesen, PRIVACY_STAND auf heute zu
        setzen. Damit waere das Datum zum Build-Datum geworden und das Signal weg.

    ➡️ Deshalb wird jetzt nicht mehr geraten, sondern gemessen: aus dem Diff
    kommen die Zeilennummern (@@-Koepfe), und die werden gegen den echten
    Zeilenbereich der Erklaerung gehalten. Kein Stichwort mehr im Spiel.
    """
    bereiche = erklaerungs_zeilen()
    if bereiche is None:
        return "abschnitt-weg"      # der Aufrufer meldet das laut

    try:
        roh = subprocess.run(
            # 🔴 `HEAD` MUSS dabeistehen (Fund-Sucher, 10.09.2026).
            # `git diff` allein vergleicht Arbeitsbaum gegen INDEX - alles,
            # was schon `git add` gesehen hat, steht in beiden gleich und
            # faellt aus dem Diff. Nachgemessen: Zeile in renderPrivacy
            # geaendert -> Fund; dieselbe Zeile nach `git add` -> KEIN Fund.
            # Der uebliche Ablauf hier ist `git add -A` und dann committen,
            # also war der Check genau im entscheidenden Moment blind.
            ["git", "-C", str(HIER), "diff", "HEAD", "--unified=0", "--", "index.html"],
            capture_output=True, text=True, timeout=60,
            # ⚠️ encoding MUSS gesetzt sein. Ohne das dekodiert Python die
            # Ausgabe auf Windows als cp1252, der Diff enthaelt aber UTF-8-
            # Umlaute -> UnicodeDecodeError im Lesethread, stdout wird None,
            # und die naechste Zeile stirbt an .splitlines(). Am 09.09.2026
            # genau so passiert, gemeldet vom eigenen Hook.
            encoding="utf-8", errors="replace",
        )
        if roh.returncode != 0:
            # 🔴 Nicht still None (Fund-Sucher, 10.09.2026). Klemmt git - kein
            # Repo, kaputter Index, fehlendes Programm -, kann der Arbeitsbaum
            # nicht geprueft werden. Das ist ein Ausfall der Pruefung und muss
            # als solcher dastehen, nicht als "nichts gefunden".
            return "git-klemmt"
    except (OSError, subprocess.SubprocessError):
        return "git-klemmt"

    # @@ -alt,n +neu,m @@  -- uns interessiert der NEUE Bereich.
    # Fehlt die Zahl nach dem Komma, ist es genau eine Zeile; ist sie 0, wurde
    # nur geloescht (dann liegt die Loeschstelle bei `start`).
    for kopf in re.findall(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", roh.stdout or "",
                           flags=re.M):
        start = int(kopf[0])
        anzahl = int(kopf[1]) if kopf[1] else 1
        # 🔴 Bei einer REINEN LOESCHUNG schreibt git `+<zeile davor>,0` - die
        # Zahl zeigt also auf die Zeile VOR der Loeschstelle (Fund-Sucher,
        # 10.09.2026). Wer genau die erste Zeile eines Bereichs loescht, landete
        # damit knapp davor und rutschte durch. Nachgemessen: `const
        # PRIVACY_OWNER` (Zeile 1547) geloescht -> `+1546,0` -> kein Fund.
        # ⚠️ Ausgerechnet an dieser Zeile haengt die Pflichtangabe
        # "Verantwortlicher". Deshalb bei `,0` einen Schritt nach vorn.
        if anzahl == 0:
            start += 1
        ende = start + max(anzahl, 1) - 1
        for von, bis in bereiche:
            if start <= bis and ende >= von:      # ueberschneiden sie sich?
                return True
    return False


def letzte_aenderung_am_abschnitt():
    """Wann wurde renderPrivacy() zuletzt COMMITTET? Aus der git-Historie.

    -L folgt der Funktion durch die Historie, auch wenn sie sich verschiebt.

    🔴 Zwei Faelle, in denen frueher still None herauskam und der Bericht dann
    "keine Funde" sagte (Fund-Sucher, 09.09.2026):
      - `renderPrivacy` umbenannt -> git endet mit rc=128 und "fatal: no match"
        auf stderr. stderr wurde nirgends gelesen.
      - kein Repo / kein git.
    Der erste Fall ist ein echter Defekt der Pruefung und muss laut sein; der
    zweite ist harmlos. Deshalb gibt es jetzt (datum, fehlermeldung) zurueck
    statt nur ein Datum.
    """
    try:
        roh = subprocess.run(
            ["git", "-C", str(HIER), "log", "-1", "--format=%ad", "--date=short",
             "-L", "/function renderPrivacy/,/^}/:index.html"],
            capture_output=True, text=True, timeout=60,
            encoding="utf-8", errors="replace",
        )
        if roh.returncode != 0:
            fehler = (roh.stderr or "").strip().splitlines()
            erste = fehler[0] if fehler else f"git endete mit {roh.returncode}"
            # "no match" heisst: die Funktion gibt es unter diesem Namen nicht mehr.
            if "no match" in erste.lower() or "kein treffer" in erste.lower():
                return None, ("git findet `renderPrivacy` nicht mehr in index.html: "
                              f"{erste}")
            return None, None          # kein Repo o. ae. - harmlos
        for zeile in (roh.stdout or "").splitlines():
            zeile = zeile.strip()
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", zeile):
                return datetime.strptime(zeile, "%Y-%m-%d").date(), None
    except (OSError, subprocess.SubprocessError, ValueError):
        return None, None
    return None, None


def pruefe_versprechen():
    """Saetze in der Erklaerung, die der Code widerlegt.

    Bewusst eine kurze, handgepflegte Liste statt einer schlauen Analyse: jeder
    Eintrag steht fuer einen Fehler, der schon einmal passiert ist. Eine
    Pruefung, die raet, findet nichts Verlaessliches.
    """
    quelltext = lies(INDEX)
    code = kommentare_weg(quelltext)

    # 09.09.2026: Die Erklaerung nannte nur Barcode und Foto - die Textsuche
    # schickt aber den eingetippten Begriff an Open Food Facts.
    #
    # ⚠️ Die erste Fassung dieser Regel war falsch gebaut: sie schlug an, sobald
    # irgendwo "nur die Nummer" stand. Nach dem Beheben stand der Satz weiter da
    # (beim Barcode, wo er stimmt) - und die Pruefung meldete den Fund erneut.
    # Eine Pruefung, die sich durch das Beheben nicht beruhigen laesst, wird nach
    # dem zweiten Mal weggeklickt. Deshalb wird jetzt das GEGENTEIL geprueft:
    # gibt es eine Textsuche im Code, muss die Erklaerung sie erwaehnen.
    sucht_mit_text = "search_terms=" in code or "/search?" in code
    if sucht_mit_text:
        erklaert = any(m in quelltext for m in
                       ("Suchfeld", "Suchbegriff", "was du suchst", "was du eintippst"))
        if not erklaert:
            fund("SCHWER",
                 "Die App hat eine Textsuche, die Erklaerung erwaehnt sie nicht",
                 "Was der Nutzer ins Suchfeld tippt, geht an Open Food Facts.",
                 "Das ist mehr als eine Barcode-Nummer und gehoert in den Text.")

    # Wer "kein Tracking" verspricht, darf keine Zaehldienste einbauen.
    zaehler = ["google-analytics", "googletagmanager", "plausible.io", "matomo",
               "sentry.io", "posthog", "hotjar"]
    drin = [z for z in zaehler if z in code]
    if drin and "kein Tracking" in quelltext:
        fund("SCHWER", f'Die Erklaerung sagt "kein Tracking", im Code steht: {", ".join(drin)}')


def erklaerungs_text(nur_anzeige=False):
    """Nur die Zeilen der Datenschutzerklaerung, nicht die ganze Datei.

    `nur_anzeige=True` laesst die `const PRIVACY_`-Zeilen weg.
    🔴 WARUM (Fund-Sucher, 10.09.2026): die Konstanten gehoeren zum "Abschnitt",
    damit eine Aenderung an ihnen den Arbeitsbaum-Check ausloest. Fuer die
    PFLICHTANGABEN sind sie aber Gift: `PRIVACY_CONTACT` steht dort immer, also
    konnte die Pflichtangabe "Kontakt" gar nicht mehr fehlschlagen.
    **Nachgemessen: den ganzen Verantwortlich-Absatz geloescht -> keine Funde.**
    Eine Pruefung, die nicht mehr durchfallen kann, ist keine Pruefung.

    🔴 WARUM (Fund-Sucher, Nachlauf 10.09.2026): `pruefe_pflichtangaben` las
    bis dahin `lies(INDEX)`, also alle 549 KB. Damit konnten Fundstellen
    AUSSERHALB der Erklaerung eine fehlende Pflichtangabe maskieren -
    nachgemessen: "Speicherdauer" 6x ausserhalb, "Betroffenenrechte" 2x.
    ⚠️ Und die Reparatur eines anderen Fundes hat das am 09.09. verschlimmert:
    der neue Kommentar bei `exportData` enthaelt "Art. 20 DSGVO" und maskiert
    seither die Betroffenenrechte mit. Wer den ganzen Abschnitt loescht, bekaeme
    trotzdem "keine Funde".
    """
    bereiche = erklaerungs_zeilen()
    if bereiche is None:
        return None
    zeilen = lies(INDEX).splitlines()
    heraus = []
    for von, bis in bereiche:
        for z in zeilen[von - 1:bis]:
            if nur_anzeige and z.startswith("const PRIVACY_"):
                continue
            heraus.append(z)
    return "\n".join(heraus)


# ---------------------------------------------------------------------------
# Was der Code TUT -> was der Text dazu SAGEN MUSS.
#
# 🔴 WARUM ES DIESE LISTE GIBT (Fund-Sucher, Nachlauf 10.09.2026): von allem,
# was am 09.09. in die Erklaerung geschrieben wurde - Bestenliste, Art. 9,
# IP-Adresse, Push ueber Apple/Google, Grenzen des Loeschens - pruefte
# **kein einziger Satz** irgendetwas. Sie haetten morgen wieder verschwinden
# koennen, und nichts waere rot geworden. Das ist exakt die Geschichte, die den
# Bestenlisten-Satz ueberhaupt in den Bericht gebracht hat: er stand elf Tage
# falsch da.
#
# Jede Regel ist: (Kennzeichen im Code, was im Text stehen muss, Begruendung).
# Das Kennzeichen wird OHNE Kommentare gesucht, der Text NUR im Abschnitt.
#
# 🔴 DIE PFLICHTWOERTER SIND WORTFOLGEN, KEINE EINZELWOERTER (10.09.2026).
# Die erste Fassung suchte "IP-Adresse", "Apple", "Google", "Bestenliste".
# Nachgemessen: "IP-Adresse" steht 2x im Abschnitt, "Google" 5x, "Bestenliste"
# 3x. Wer den Google-IP-Satz loescht, bekommt trotzdem gruen - der Satz bei
# Open Food Facts deckt ihn. **Drei der vier Regeln waren so maskiert**, nur
# "Art. 9" (1x) war scharf. Gefunden vom Fund-Sucher; die Gegenprobe hat es
# nicht gemerkt, weil sie das Wort UEBERALL ersetzte statt an einer Stelle.
# ⚠️ Eine Wortfolge, die nur an einer Stelle vorkommt, kann nicht maskiert
# werden. Beim Umformulieren muss sie hier nachgezogen werden - dann meldet
# sich die Regel, statt still gruen zu bleiben.
ZUSAGEN = [
    ("bestenlisteSchieben",
     ("bei jedem Abgleich in",),
     "Die App schiebt Name und XP in eine Tabelle, die alle Angemeldeten lesen. "
     "Steht das nicht im Text, sagt er das Gegenteil der Wahrheit - genau so war "
     "es vom 05.08. bis zum 09.09.2026."),
    ("gym_push",
     ("Adresse beim Mitteilungsdienst",),
     "Die Push-Kennung liegt beim Mitteilungsdienst des Browsers (Apple bzw. "
     "Google, USA). Als Drittlandsempfaenger muessen beide benannt sein."),
    ("generativelanguage.googleapis.com",
     ("IP-Adresse sieht Google",),
     "Jeder Aufruf traegt die IP mit, und eine IP ist personenbezogen "
     "(EuGH, Breyer, C-582/14). \"Nichts ueber dich\" waere zu stark."),
    ("suchAdresseNeu",
     ("IP-Adresse sieht der Dienst",),
     "Auch die Textsuche traegt die IP mit - der Satz beim Foto deckt sie nicht."),
    ("addWeight",
     ("Art. 9",),
     "Gewicht, Schritte und Mahlzeiten sind Gesundheitsdaten. Dafuer reicht "
     "Art. 6 nicht - es braucht die ausdrueckliche Einwilligung nach Art. 9 "
     "Abs. 2 lit. a."),
]


def pruefe_zusagen():
    """Tut der Code etwas, das der Text verschweigt?"""
    abschnitt = erklaerungs_text()
    if abschnitt is None:
        return                        # pruefe_stand meldet das schon laut
    code = kommentare_weg(lies(INDEX))

    for kennzeichen, pflicht, warum in ZUSAGEN:
        if kennzeichen not in code:
            # 🔴 NICHT still ueberspringen (gefunden am 10.09.2026 an dieser
            # Datei selbst: das Kennzeichen `gewichtHinzu` war geraten und gab es
            # nie - die Regel hat deshalb nie etwas geprueft und nie etwas gesagt.
            # Genau die Bauform, die dieses Werkzeug jagen soll.)
            # Entweder wurde die Funktion umbenannt, dann muss das Kennzeichen
            # nachgezogen werden, oder es gibt sie nicht mehr, dann gehoert die
            # Regel geloescht. Beides ist eine Entscheidung, keine Stille.
            fund("HINWEIS",
                 f"Die Zusagen-Regel `{kennzeichen}` findet ihr Kennzeichen nicht mehr",
                 "Sie prueft damit nichts. Umbenannt -> Kennzeichen nachziehen;",
                 "weggefallen -> Regel loeschen. Nicht stehen lassen.")
            continue
        fehlend = [w for w in pflicht if w not in abschnitt]
        if fehlend:
            fund("SCHWER",
                 f"Der Code hat `{kennzeichen}`, die Erklaerung sagt nichts von "
                 f"{', '.join(fehlend)}",
                 warum)


# ---------------------------------------------------------------------------
#  VERSPRECHEN - die Gegenrichtung zu ZUSAGEN (11.09.2026)
# ---------------------------------------------------------------------------
#  🔴 WARUM ES DAS GIBT. Am 11.09.2026 standen drei schwere Funde in der
#  Erklaerung, waehrend 898 Pruefungen und alle vier Datenschutz-Pruefungen
#  gruen waren:
#    · Der Text versprach, man koenne Gewicht und Schritte "jederzeit einzeln
#      loeschen" - beide Loeschwege waren in v0.078 abgebaut worden.
#    · Der Text nannte den "Kurzbefehl auf deinem iPhone" als Quelle der
#      Schrittzahl - den Weg gab es seit v0.078 nicht mehr.
#    · Der Text nannte einen "Schalter in den Einstellungen" - auch der war weg.
#
#  ZUSAGEN oben laeuft nur in EINE Richtung: Kennzeichen im Code -> Wortfolge
#  muss im Text stehen. Es faengt, wenn die App etwas Neues TUT, das niemand
#  aufgeschrieben hat. **Die andere Richtung hat niemand gemessen**: der Text
#  verspricht etwas, und das Stueck Code dazu ist verschwunden.
#
#  ⚠️ Die Datums-Pruefung kann es bauartbedingt nicht sehen. Sie fragt "ist der
#  Stand aelter als der Text?". Die gefaehrliche Frage ist "hat sich der CODE
#  bewegt, ohne dass der Text mitging?" - und fuer den Leser sieht ein Text mit
#  frischem Stand vollkommen in Ordnung aus.
#
#  ⚠️ EINE GRENZE, AUSDRUECKLICH: eine Regel schlaeft, solange ihre Wortfolge
#  nicht im Text steht. Das ist richtig so - was nicht versprochen wird, muss
#  auch nicht eingeloest werden. Aber wer eine Zusage UMFORMULIERT, statt sie zu
#  streichen, legt die Regel schlafen, ohne es zu merken. Deshalb zaehlt
#  `pruefe_eingeloest()` am Ende, wie viele Regeln scharf sind und wie viele
#  schlafen, und nennt die schlafenden beim Namen. **Eine Regel, die von selbst
#  einschlaeft, ist genau die Bauform, die dieses Werkzeug jagen soll.**
VERSPRECHEN = [
    ("Kurzbefehl",
     "?schritte=",
     "Der Text nennt den iOS-Kurzbefehl als Quelle der Schrittzahl. Ohne den "
     "Leser fuer `?schritte=` in der Adresszeile gibt es diesen Weg nicht - und "
     "der Leser haelt seine Zahl fuer etwas, das ein Automatismus einsammelt."),
    ("Schalter in den Einstellungen",
     "schritt:an",
     "Der Text nennt einen Schalter als Weg, die Einwilligung zurueckzunehmen. "
     "Gibt es den Schalter nicht, ist der Widerruf nach Art. 7 Abs. 3 nicht so "
     "einfach wie die Erteilung - er ist gar nicht da."),
    ("jederzeit einzeln\n        loeschen",
     'data-delweight="',
     "Der Text verspricht, einzelne Gewichtseintraege loeschen zu koennen. Dazu "
     "muss ein Element `data-delweight` ERZEUGEN - der blosse Zweig im "
     "Klick-Verteiler genuegt nicht, den erreicht ohne Knopf niemand."),
    ("jede Zeile hat ein",
     'data-delmeal="',
     "Der Text verspricht das Kreuz an jeder Mahlzeit. Verschwindet der Knopf, "
     "bleibt der einzige Loeschweg fuer Gesundheitsdaten ohne Ankuendigung weg."),
]


def pruefe_eingeloest():
    """Verspricht der Text etwas, das der Code nicht mehr kann?

    🔴 HIESS BEIM ERSTEN ANLAUF `pruefe_versprechen` - und es gibt diese
    Funktion weiter oben SCHON. Python nimmt die letzte Definition: meine haette
    die aeltere ueberschrieben und damit die Textsuche-Regel und die
    Tracking-Regel **still ausgeschaltet**. Beide waeren nie wieder gelaufen, und
    nichts waere rot geworden - dieselbe Bauform, gegen die diese Datei gebaut
    ist, eingefuehrt durch eine Pruefung gegen genau diese Bauform.
    ⚠️ Aufgefallen ist es nur daran, dass die Ausgabe doppelt erschien.
    Der Name ist deshalb jetzt ein anderer, und `pruefe_ablauf_vollstaendig()`
    unten zaehlt nach, dass beide im Ablauf stehen.
    """
    abschnitt = erklaerungs_text()
    if abschnitt is None:
        return                        # pruefe_stand meldet das schon laut
    quelltext = lies(INDEX)
    code = kommentare_weg(quelltext)

    # ⚠️ Die Wortfolge wird im TEXT gesucht, das Kennzeichen aber im GANZEN
    # Quelltext ohne Kommentare. Ein `data-delweight` darf ueberall stehen -
    # es kommt nur darauf an, dass es ueberhaupt erzeugt wird.
    schlafend = []
    for wortfolge, kennzeichen, warum in VERSPRECHEN:
        # Zeilenumbrueche im Text zaehlen nicht: die Erklaerung ist umbrochener
        # HTML-Quelltext, und wo genau umbrochen wird, ist Zufall der Formatierung.
        nadel = " ".join(wortfolge.split())
        heuhaufen = " ".join(abschnitt.split())
        if nadel not in heuhaufen:
            schlafend.append(nadel)
            continue
        if kennzeichen not in code:
            fund("SCHWER",
                 f"Die Erklaerung verspricht \"{nadel}\", aber `{kennzeichen}` "
                 f"gibt es im Code nicht mehr",
                 warum,
                 "Entweder den Weg wieder einbauen oder den Satz streichen -",
                 "ein Rechtstext, der mehr verspricht als der Code kann, ist der",
                 "schlechtere der beiden Fehler.")

    if schlafend:
        # Kein Fund, sondern Sicht: so faellt auf, wenn eine Regel durch eine
        # Umformulierung still eingeschlafen ist.
        print("   (VERSPRECHEN: %d von %d Regeln schlafen, weil ihre Wortfolge "
              "nicht im Text steht)" % (len(schlafend), len(VERSPRECHEN)))
        for s in schlafend:
            print("      schlaeft: \"%s\"" % s)


def pruefe_ablauf_vollstaendig():
    """Wird jede Pruefung, die es hier gibt, auch wirklich gerufen?

    🔴 WARUM (11.09.2026, an dieser Datei selbst passiert): eine neu
    hinzugefuegte Funktion hiess wie eine bestehende. Python nimmt die letzte
    Definition - die aeltere war damit weg, samt ihrer Textsuche- und
    Tracking-Regel. **Beide haetten nie wieder etwas geprueft und nie etwas
    gesagt.** Aufgefallen ist es nur daran, dass eine Ausgabe doppelt erschien;
    ohne diese Zufaelligkeit waere die Luecke geblieben.

    ⚠️ Zwei Faelle werden gemeldet, beide fuehren zu einer stillen Luecke:
      · eine `pruefe_*`-Funktion ist definiert, steht aber nicht in `main()`
      · ein Name ist zweimal definiert (die erste Fassung ist dann tot)

    💡 Diese Pruefung liest den eigenen Quelltext. Das ist Absicht: sie soll
    auch dann greifen, wenn jemand eine Funktion anlegt und den Aufruf vergisst -
    und genau dann kann sie nicht davon ausgehen, dass irgendjemand hinsieht.
    """
    eigener = lies(Path(__file__))
    if not eigener:
        fund("HINWEIS", "Die Ablauf-Pruefung kann den eigenen Quelltext nicht lesen",
             "Damit prueft sie nichts. Nicht stehen lassen.")
        return

    namen = re.findall(r"(?m)^def (pruefe_[a-zA-Z0-9_]*)\(", eigener)

    doppelt = sorted({x for x in namen if namen.count(x) > 1})
    for d in doppelt:
        fund("SCHWER", f"`{d}` ist in dieser Datei zweimal definiert",
             "Python nimmt die letzte - die erste Fassung ist toter Code und",
             "prueft nichts mehr, ohne dass irgendwo etwas rot wird.")

    m = re.search(r"(?ms)^def main\(\):(.*?)(?=^def |\Z)", eigener)
    if not m:
        fund("HINWEIS", "Die Ablauf-Pruefung findet `main()` nicht",
             "Umbenannt? Dann hier nachziehen.")
        return
    ablauf = m.group(1)

    # ⚠️ Sich selbst ausgenommen waere bequem und falsch: faellt DIESER Aufruf
    # weg, faellt mit ihm jede andere Meldung dieser Funktion. Sie steht deshalb
    # mit in der Liste - und meldet dann eben, dass sie selbst nicht laeuft.
    fehlend = [x for x in sorted(set(namen)) if (x + "(") not in ablauf]
    for f in fehlend:
        fund("SCHWER", f"`{f}` ist definiert, wird aber in `main()` nicht gerufen",
             "Eine Pruefung, die niemand startet, ist keine Pruefung -",
             "sie sieht nur so aus. Entweder aufrufen oder loeschen.")


def pruefe_handler():
    """Hat jedes `data-act` im HTML auch einen Zweig im Klick-Verteiler?

    🔴 WARUM (Fund-Sucher, Nachlauf 10.09.2026): die zwei neuen Knoepfe
    `zeigDatenschutz` und `zurueckZurAnmeldung` haengen an Zeichenketten, die an
    zwei getrennten Stellen stehen. Ein Tippfehler in einer davon faellt durch
    die ganze `else if`-Kette und tut **nichts** - der Link in der Anmeldemaske
    waere ein toter Knopf, und die Art.-13-Reparatur still wieder weg.
    ⚠️ Ein toter Knopf sieht aus wie ein Knopf.
    """
    quelltext = lies(INDEX)
    benutzt = set(re.findall(r'data-act="([a-zA-Z][a-zA-Z0-9_]*)"', quelltext))
    behandelt = set(re.findall(r"a\s*===\s*'([a-zA-Z][a-zA-Z0-9_]*)'", quelltext))
    behandelt |= set(re.findall(r'a\s*===\s*"([a-zA-Z][a-zA-Z0-9_]*)"', quelltext))
    for name in sorted(benutzt - behandelt):
        fund("SCHWER", f"Der Knopf `data-act=\"{name}\"` hat keinen Zweig im Verteiler",
             "Er tut beim Klicken nichts - und sieht dabei aus wie ein Knopf.")


def pruefe_pflichtangaben():
    """Steht das drin, was Art. 13 DSGVO verlangt?

    Kein Ersatz fuer eine rechtliche Pruefung - nur ein Netz gegen das
    versehentliche Loeschen ganzer Abschnitte beim Umbauen.

    ⚠️ Liest seit dem 10.09.2026 NUR den Abschnitt (siehe erklaerungs_text).
    """
    # ⚠️ `nur_anzeige=True`: die const-Zeilen zaehlen hier NICHT mit, sonst kann
    # "Kontakt" nie fehlschlagen (siehe erklaerungs_text).
    text = erklaerungs_text(nur_anzeige=True)
    if text is None:
        return                        # pruefe_stand meldet das schon laut
    pflicht = {
        "Verantwortlicher":      ["PRIVACY_OWNER", "Verantwortlich ist"],
        "Kontakt":               ["PRIVACY_CONTACT"],
        "Zwecke":                ["Wofuer sie benutzt werden", "Wofür sie benutzt werden"],
        "Rechtsgrundlage":       ["Art. 6 Abs. 1"],
        "Speicherdauer":         ["Wie lange"],
        "Betroffenenrechte":     ["Art. 15", "Art. 17", "Art. 20"],
        "Beschwerderecht":       ["Art. 77", "Aufsichtsbehoerde", "Aufsichtsbehörde"],
        "Drittlandsuebermittlung": ["USA"],
        "Auftragsverarbeitung":  ["Art. 28"],
    }
    for was, marken in pflicht.items():
        if not any(m in text for m in marken):
            fund("SCHWER", f"Pflichtangabe fehlt in der Erklaerung: {was}",
                 f"Gesucht wurde nach: {', '.join(marken)}")


def app_fassung():
    m = re.search(r"APP_FASSUNG\s*=\s*['\"]([^'\"]+)['\"]", lies(INDEX))
    return m.group(1) if m else "?"


def main():
    kurz = "--kurz" in sys.argv
    if not INDEX.is_file():
        print("index.html nicht gefunden:", INDEX)
        return 2

    if not kurz:
        print("=" * 70)
        print(f"  Datenschutz-Pruefung  ({app_fassung()})   "
              f"{datetime.now():%d.%m.%Y  %H:%M}")
        print("=" * 70)

    gefunden = pruefe_ziele()
    stand = pruefe_stand()
    pruefe_versprechen()
    pruefe_pflichtangaben()
    pruefe_zusagen()
    pruefe_eingeloest()
    pruefe_handler()
    pruefe_ablauf_vollstaendig()

    if not kurz:
        print("\n--- Wohin die App zur Laufzeit spricht ---")
        for host in sorted(gefunden):
            zweck = ERKLAERTE_ZIELE.get(host) or UNBEDENKLICH.get(host) or "?"
            zeichen = "erklaert " if host in ERKLAERTE_ZIELE else "unkritisch"
            print(f"  [{zeichen}] {host:<36} {zweck}")
        print("\n--- Von hier aus nicht messbar ---")
        for was, hinweis in NICHT_MESSBAR:
            print(f"  [ Hand  ] {was}")
            print(f"            {hinweis}")
        if stand:
            print(f"\n--- Stand der Erklaerung: {stand:%d.%m.%Y} ---")

    print("\n" + "=" * 70)
    schwer = [f for f in _funde if f[0] == "SCHWER"]
    hinweise = [f for f in _funde if f[0] != "SCHWER"]
    if not _funde:
        print("  Keine Funde - Erklaerung und Code passen zusammen.")
    else:
        print(f"  {len(schwer)} schwer, {len(hinweise)} Hinweis(e)")
        for schwere, text, zeilen in _funde:
            print(f"\n  [{schwere}] {text}")
            for z in zeilen:
                print(f"     {z}")
    print("=" * 70)

    if schwer:
        # ⚠️ Kein Emoji in der Ausgabe. Die Windows-Konsole laeuft auf cp1252 und
        # wirft dort UnicodeEncodeError - beim ersten Lauf am 09.09.2026 ist das
        # Skript genau hier abgestuerzt, NACHDEM es beide Funde korrekt gemeldet
        # hatte. Ein Pruefer, der an seiner eigenen Ausgabe stirbt, sieht aus wie
        # ein kaputter Pruefer.
        print("\n  -> Der rechtliche Teil gehoert dem Agenten, nicht diesem Skript.")
        print("     Was hier steht, sind Widersprueche zwischen Code und Text.")
    return 1 if schwer else 0


if __name__ == "__main__":
    sys.exit(main())
