# -*- coding: utf-8 -*-
"""
datenschutz-pruefen.py - stimmt die Datenschutzerklaerung noch mit der App ueberein?

Gebaut am 09.09.2026. Karls Ansage: "KI Agenten fuer Datenschutz Erklaerung der
sie immer aktualliesiert ... er muss zu jeder neuen version laufen. er soll auch
pruefen ob das alles so legal ist."

WAS DIESE DATEI TUT UND WAS NICHT
Sie ist der mechanische Teil: sie sammelt die PRUEFBAREN Tatsachen und meldet,
wo die Erklaerung ihnen widerspricht. Ob eine Formulierung rechtlich traegt,
entscheidet sie NICHT - das ist die Aufgabe des Agenten (siehe README, Abschnitt
"Der Datenschutz-Waechter"). Beides zusammen ist der Waechter; dieses Skript ist
der Teil, der bei jedem Lauf in Sekunden durchlaeuft.

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
    if ungesicherte_aenderung_am_abschnitt() and stand != date.today():
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


def ungesicherte_aenderung_am_abschnitt():
    """Wurde renderPrivacy() geaendert, ohne dass es schon committet ist?

    🔴 DER GRUND, WARUM ES DIESE FUNKTION GIBT (Fund-Sucher, 09.09.2026):
    Die Pruefung lief urspruenglich NUR ueber `git log -L`. Das liest committete
    Historie - der Hook laeuft aber als PostToolUse, also IMMER vor dem Commit.
    Damit konnte die Pruefung genau die Aenderung, wegen der sie gestartet wurde,
    prinzipiell nicht sehen: Text aendern, Datum vergessen, committen, pushen -
    alles in einer Sitzung, und nichts wurde rot.

    Deshalb zuerst der Arbeitsbaum: `git diff` zeigt, was JETZT anders ist.
    """
    try:
        roh = subprocess.run(
            ["git", "-C", str(HIER), "diff", "--unified=0", "--", "index.html"],
            capture_output=True, text=True, timeout=60,
            # ⚠️ encoding MUSS gesetzt sein. Ohne das dekodiert Python die
            # Ausgabe auf Windows als cp1252, der Diff enthaelt aber UTF-8-
            # Umlaute -> UnicodeDecodeError im Lesethread, stdout wird None,
            # und die naechste Zeile stirbt an .splitlines(). Am 09.09.2026
            # genau so passiert, gemeldet vom eigenen Hook.
            encoding="utf-8", errors="replace",
        )
        if roh.returncode != 0:
            return None
        # Grob, aber ausreichend: steht im Diff eine Zeile aus dem Datenschutz-
        # Abschnitt? Die Marker sind Formulierungen, die nur dort vorkommen.
        marken = ("Datenschutz", "PRIVACY_", "Open Food Facts", "Bestenliste",
                  "DSGVO", "Art. 6", "Art. 13", "Aufsichtsbeh")
        for zeile in (roh.stdout or "").splitlines():
            if zeile.startswith(("+", "-")) and not zeile.startswith(("+++", "---")):
                if any(m in zeile for m in marken):
                    return True
        return False
    except (OSError, subprocess.SubprocessError):
        return None


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


def pruefe_pflichtangaben():
    """Steht das drin, was Art. 13 DSGVO verlangt?

    Kein Ersatz fuer eine rechtliche Pruefung - nur ein Netz gegen das
    versehentliche Loeschen ganzer Abschnitte beim Umbauen.
    """
    text = lies(INDEX)
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
