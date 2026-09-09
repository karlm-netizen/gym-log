# -*- coding: utf-8 -*-
"""
Gegenprobe zu datenschutz-pruefen.py - findet die Pruefung auch etwas?

Am 09.09.2026 meldete die Pruefung "keine Funde". Das ist die haeufigste Art,
wie eine Pruefung luegt: sie ist gruen, weil sie nichts SEHEN kann. Deshalb
werden hier vier Schadensfaelle in eine Kopie von index.html eingebaut; jeder
davon MUSS als SCHWER herauskommen.

Die echte index.html wird dabei nicht angefasst - gearbeitet wird auf einer
Kopie im Temp-Ordner, und die Modul-Konstante INDEX zeigt darauf.
"""
import importlib.util
import re
import shutil
import sys
import tempfile
from pathlib import Path

HIER = Path(__file__).resolve().parent
QUELLE = HIER / "datenschutz-pruefen.py"

spec = importlib.util.spec_from_file_location("dp", QUELLE)
dp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dp)

ECHTE = (HIER / "index.html").read_text(encoding="utf-8")
tmp = Path(tempfile.mkdtemp())
gescheitert = 0


def probe(name, umbau, pruefungen, erwartet_stichwort):
    """Einen Schadensfall einbauen und sehen, ob er auffaellt."""
    global gescheitert
    kopie = tmp / "index.html"
    kopie.write_text(umbau(ECHTE), encoding="utf-8")

    dp._funde.clear()
    dp.INDEX = kopie
    dp.SW = HIER / "sw.js"
    for f in pruefungen:
        f()

    schwer = [t for s, t, _ in dp._funde if s == "SCHWER"]
    getroffen = [t for t in schwer if erwartet_stichwort.lower() in t.lower()]
    if getroffen:
        print(f"[  OK  ] {name}")
        print(f"         -> {getroffen[0]}")
    else:
        print(f"[FEHLER] {name}")
        print(f"         Erwartet wurde ein Fund mit '{erwartet_stichwort}'.")
        print(f"         Gemeldet wurde: {schwer or 'nichts'}")
        gescheitert += 1


# --- 1. Ein neuer Fremddienst, den niemand erklaert hat ---
probe(
    "unbekanntes Ziel im Code wird gefunden",
    lambda t: t.replace("const SUCH_FELDER=",
                        "const SPION='https://tracker.example.com/sammeln';\nconst SUCH_FELDER=", 1),
    [dp.pruefe_ziele],
    "tracker.example.com",
)

# --- 2. Die Textsuche bleibt im Code, verschwindet aber aus der Erklaerung ---
def suche_aus_text_werfen(t):
    for wort in ("Suchfeld", "Suchbegriff", "was du suchst", "was du eintippst"):
        t = t.replace(wort, "XXX")
    return t

probe(
    "Textsuche im Code, aber nicht in der Erklaerung",
    suche_aus_text_werfen,
    [dp.pruefe_versprechen],
    "Textsuche",
)

# --- 3. Eine Pflichtangabe faellt beim Umbauen raus ---
probe(
    "geloeschte Pflichtangabe (Beschwerderecht) wird gefunden",
    lambda t: t.replace("Art. 77", "XXX").replace("Aufsichtsbehörde", "XXX"),
    [dp.pruefe_pflichtangaben],
    "Beschwerderecht",
)

# --- 4. Ein Zaehldienst neben dem Versprechen "kein Tracking" ---
probe(
    "Zaehldienst trotz 'kein Tracking' wird gefunden",
    lambda t: t.replace("const SUCH_FELDER=",
                        "const Z='https://plausible.io/js/script.js';\nconst SUCH_FELDER=", 1),
    [dp.pruefe_versprechen],
    "Tracking",
)

# --- 5. Der Stand ist alt, der Text wurde geaendert -> muss auffallen ---
# 🔴 Diese Probe fehlte bis zum 09.09.2026. Der Fund-Sucher hat es gemerkt:
# `pruefe_stand()` war die einzige Prueffunktion ohne Gegenprobe - ausgerechnet
# die, die den Fehler finden soll, der am haeufigsten passiert.
def stand_zurueckdrehen(t):
    import re as _re
    return _re.sub(r"PRIVACY_STAND\s*=\s*'[^']*'",
                   "PRIVACY_STAND='1. Januar 2020'", t, count=1)


probe(
    "alter PRIVACY_STAND bei geaendertem Text wird gefunden",
    stand_zurueckdrehen,
    [dp.pruefe_stand],
    "PRIVACY_STAND",
)

# --- 6. PRIVACY_STAND ganz weg -> muss auffallen ---
probe(
    "fehlender PRIVACY_STAND wird gefunden",
    lambda t: t.replace("const PRIVACY_STAND", "const PRIVACY_WEG", 1),
    [dp.pruefe_stand],
    "PRIVACY_STAND",
)

# --- 7. renderPrivacy umbenannt -> die Datums-Pruefung faellt aus und MUSS das sagen ---
# Vorher lief das still ins Leere: git rc=128, stderr ungelesen, Ergebnis None,
# Bericht "keine Funde". Eine ausgefallene Pruefung sah aus wie eine bestandene.
dp._funde.clear()
dp.INDEX = HIER / "index.html"
letzte, fehler = dp.letzte_aenderung_am_abschnitt()
if letzte is None and fehler is None:
    print("[ HINW ] Probe 7 uebersprungen: git liefert hier ohnehin nichts")
    print("         (kein Repo?) - die Probe braucht eine git-Historie.")
else:
    import subprocess as _sp
    roh = _sp.run(["git", "-C", str(HIER), "log", "-1", "--format=%ad", "--date=short",
                   "-L", "/function gibtEsNichtXyz/,/^}/:index.html"],
                  capture_output=True, text=True, encoding="utf-8",
                  errors="replace", timeout=60)
    if roh.returncode != 0 and "no match" in (roh.stderr or "").lower():
        print("[  OK  ] Probe 7: git meldet bei unbekanntem Funktionsnamen 'no match'")
        print("         -> genau daran erkennt die Pruefung ihren eigenen Ausfall")
    else:
        print("[FEHLER] Probe 7: git meldete kein 'no match' bei unbekannter Funktion")
        print("         rc:", roh.returncode, "stderr:", (roh.stderr or "")[:120])
        gescheitert += 1

# --- 8. Und die Gegenprobe zur Gegenprobe: die echte Datei muss sauber bleiben ---
dp._funde.clear()
dp.INDEX = HIER / "index.html"
dp.pruefe_ziele(); dp.pruefe_versprechen(); dp.pruefe_pflichtangaben()
echte_funde = [t for s, t, _ in dp._funde if s == "SCHWER"]
if echte_funde:
    print("[FEHLER] die echte index.html meldet Funde, obwohl sie sauber sein sollte:")
    for t in echte_funde:
        print("         -", t)
    gescheitert += 1
else:
    print("[  OK  ] die echte index.html bleibt ohne Fund")

shutil.rmtree(tmp, ignore_errors=True)
print()
print("Gegenprobe:", "bestanden" if not gescheitert else f"{gescheitert} Probe(n) gescheitert")
sys.exit(1 if gescheitert else 0)
