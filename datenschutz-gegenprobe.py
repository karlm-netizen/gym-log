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

# --- 8+9. Der Arbeitsbaum-Check: sieht er den Abschnitt, und NUR den? ---
# 🔴 Diese beiden Proben fehlten bis zum 10.09.2026 (Fund-Sucher, Nachlauf).
# Die erste Fassung des Checks suchte acht Stichwoerter in geaenderten Zeilen und
# ging in BEIDE Richtungen daneben: 146 der 160 Zeilen der Erklaerung trugen kein
# Stichwort, und "Bestenliste" steht 13x in gewoehnlichem Code. Ohne Gegenprobe
# war beides nicht zu sehen.
#
# ⚠️ Diese Proben aendern die ECHTE index.html kurz und stellen sie danach wieder
# her - anders geht es nicht, denn `git diff` misst den Arbeitsbaum, nicht eine
# Kopie im Temp-Ordner. Hash-Kontrolle danach.
import hashlib as _h
import subprocess as _sp2

_echte = HIER / "index.html"
_orig = _echte.read_bytes()
_hash = _h.sha256(_orig).hexdigest()

_sauber = _sp2.run(["git", "-C", str(HIER), "diff", "--quiet", "--", "index.html"],
                   capture_output=True).returncode == 0
if not _sauber:
    print("[ HINW ] Proben 8+9 uebersprungen: index.html ist gerade nicht committet")
    print("         (der Check misst den Arbeitsbaum - er braucht einen sauberen Start)")
else:
    dp.INDEX = _echte
    _text = _orig.decode("utf-8")
    _zeilen = _text.splitlines(keepends=True)
    _bereiche = dp.erklaerungs_zeilen()
    try:
        # --- Probe 8: eine Zeile IM Abschnitt, die KEIN Stichwort traegt ---
        # Genau der Fall, den die alte Fassung nicht sah.
        _von, _bis = _bereiche[0]
        _ziel = None
        _marker = ("Datenschutz", "PRIVACY_", "Open Food Facts", "Bestenliste",
                   "DSGVO", "Art. 6", "Art. 13", "Aufsichtsbeh")
        for _i in range(_von, _bis):
            _z = _zeilen[_i - 1]
            if len(_z.strip()) > 40 and not any(_m in _z for _m in _marker):
                _ziel = _i
                break
        if _ziel is None:
            print("[ HINW ] Probe 8: keine markenlose Zeile im Abschnitt gefunden")
        else:
            _neu = list(_zeilen)
            _neu[_ziel - 1] = _z.rstrip("\r\n") + " \n"   # ein Leerzeichen mehr
            _echte.write_bytes("".join(_neu).encode("utf-8"))
            if dp.ungesicherte_aenderung_am_abschnitt() is True:
                print(f"[  OK  ] Probe 8: Aenderung an Zeile {_ziel} (ohne Stichwort) wird gesehen")
            else:
                print(f"[FEHLER] Probe 8: Aenderung an Zeile {_ziel} im Abschnitt blieb unbemerkt")
                gescheitert += 1
            _echte.write_bytes(_orig)

        # --- Probe 9: eine Zeile MIT "Bestenliste" AUSSERHALB des Abschnitts ---
        # Genau der Fehlalarm, der den Pruefstand taeglich rot gemacht haette.
        _aussen = None
        for _i, _z2 in enumerate(_zeilen, start=1):
            if "Bestenliste" in _z2 and not any(v <= _i <= b for v, b in _bereiche):
                _aussen = _i
                break
        if _aussen is None:
            print("[ HINW ] Probe 9: kein 'Bestenliste' ausserhalb des Abschnitts gefunden")
        else:
            _neu = list(_zeilen)
            _neu[_aussen - 1] = _zeilen[_aussen - 1].rstrip("\r\n") + " \n"
            _echte.write_bytes("".join(_neu).encode("utf-8"))
            if dp.ungesicherte_aenderung_am_abschnitt() is False:
                print(f"[  OK  ] Probe 9: Aenderung an Zeile {_aussen} ('Bestenliste' im Code) loest NICHT aus")
            else:
                print(f"[FEHLER] Probe 9: Fehlalarm bei Zeile {_aussen} ausserhalb der Erklaerung")
                gescheitert += 1
    finally:
        _echte.write_bytes(_orig)
        if _h.sha256(_echte.read_bytes()).hexdigest() != _hash:
            print("[FEHLER] index.html NICHT sauber wiederhergestellt!")
            gescheitert += 1

# --- 10. Eine Zusage faellt aus dem Text, der Code tut es weiter ---
# 🔴 Neu am 10.09.2026. Von allem, was am 09.09. in die Erklaerung geschrieben
# wurde, prueste vorher kein einziger Satz irgendetwas - sie haetten am naechsten
# Tag verschwinden koennen, ohne dass etwas rot wird.
probe(
    "Bestenliste faellt aus dem Text, Code schiebt weiter",
    lambda t: t.replace("Die Bestenliste", "XXX").replace("Bestenliste</b>", "XXX</b>")
               .replace("die Bestenliste", "XXX").replace("Bestenliste", "XXX"),
    [dp.pruefe_zusagen],
    "bestenlisteSchieben",
)

probe(
    "Art. 9 faellt aus dem Text, Gewicht wird weiter erfasst",
    lambda t: t.replace("Art. 9", "XXX"),
    [dp.pruefe_zusagen],
    "Art. 9",
)

probe(
    "IP-Adresse faellt aus dem Text, das Foto geht weiter zu Google",
    lambda t: t.replace("IP-Adresse", "XXX"),
    [dp.pruefe_zusagen],
    "IP-Adresse",
)

# --- 11. Ein Knopf ohne Handler ---
# Ein toter Knopf sieht aus wie ein Knopf.
probe(
    "data-act ohne Zweig im Verteiler wird gefunden",
    lambda t: t.replace('data-act="zeigDatenschutz"', 'data-act="zeigDatenschutzz"', 1),
    [dp.pruefe_handler],
    "zeigDatenschutzz",
)

# --- 12. Pflichtangabe NUR ausserhalb der Erklaerung -> gilt als fehlend ---
# 🔴 Der Kern von Fund 3 (alt) und Neu 8: die Pruefung las die ganze 549-KB-Datei,
# also konnten Fundstellen ausserhalb eine geloeschte Pflichtangabe maskieren.
# Gemessen: "Speicherdauer" 6x ausserhalb, "Betroffenenrechte" 2x - eine davon
# kam am 09.09. durch die Reparatur eines anderen Fundes dazu.
def rechte_nur_aussen(t):
    """Art.-15/17/20-Nennungen im Abschnitt loeschen, aussen stehen lassen."""
    bereiche = dp.erklaerungs_zeilen()
    zeilen = t.splitlines(keepends=True)
    for von, bis in bereiche:
        for i in range(von - 1, min(bis, len(zeilen))):
            for wort in ("Art. 15", "Art. 16", "Art. 17", "Art. 18", "Art. 20", "Art. 21"):
                zeilen[i] = zeilen[i].replace(wort, "XXX")
    return "".join(zeilen)


probe(
    "Betroffenenrechte nur noch ausserhalb -> gilt als fehlend",
    rechte_nur_aussen,
    [dp.pruefe_pflichtangaben],
    "Betroffenenrechte",
)

# --- 13. Die Erklaerung ganz weg -> muss laut sein, nicht still ---
probe(
    "umbenannte renderPrivacy wird als Defekt gemeldet",
    lambda t: t.replace("function renderPrivacy(", "function renderDatenschutzSeite(", 1),
    [dp.pruefe_stand],
    "nicht auffindbar",
)

# --- 14. Und die Gegenprobe zur Gegenprobe: die echte Datei muss sauber bleiben ---
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
