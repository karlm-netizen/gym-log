# -*- coding: utf-8 -*-
"""
Der Arbeitsbaum-Check: greift er in den drei Fällen, die am 10.09.2026 danebengingen?

Die Proben 8/9 in `datenschutz-gegenprobe.py` prüfen dasselbe Werkzeug, springen
aber ab, wenn der Arbeitsbaum nicht sauber ist. Diese Datei deckt die drei Fälle
ab, die der Fund-Sucher einzeln nachgemessen hat:

  · eine Änderung, die bereits `git add` gesehen hat  (war blind)
  · eine gelöschte ERSTE Zeile eines Bereichs         (Zählfehler um eins)
  · klemmendes git                                     (war still)

⚠️ Sie fasst die echte `index.html` an und stellt sie mit Hash-Kontrolle wieder
her. Ohne sauberen Arbeitsbaum steigt sie aus — dann steht das im Ergebnis.

    python datenschutz-arbeitsbaum-probe.py
"""
import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path

REPO = Path(r"C:\Users\karlm\OneDrive\Desktop\gym-log")
INDEX = REPO / "index.html"

spec = importlib.util.spec_from_file_location("dp", REPO / "datenschutz-pruefen.py")
dp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dp)

orig = INDEX.read_bytes()
h = hashlib.sha256(orig).hexdigest()
text = orig.decode("utf-8")
zeilen = text.splitlines(keepends=True)
fehler = 0


def sag(ok, name, extra=""):
    global fehler
    print(f"[{'  OK  ' if ok else 'FEHLER'}] {name}")
    if extra:
        print(f"         {extra}")
    if not ok:
        fehler += 1


def git(*args):
    return subprocess.run(["git", "-C", str(REPO)] + list(args),
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=60)


# Nur auf sauberem Stand messbar
if git("diff", "--quiet", "HEAD", "--", "index.html").returncode != 0:
    # ⚠️ Kein stilles Exit 0: uebersprungen ist nicht bestanden (dieselbe Lehre
    # wie bei den Proben 8/9 der Gegenprobe, 10.09.2026).
    print("[ UEBER ] Arbeitsbaum ist nicht sauber - diese Probe braucht einen")
    print("          committeten Stand. Erst committen, dann nochmal.")
    print()
    print("Arbeitsbaum-Probe: UEBERSPRUNGEN (nichts geprueft)")
    sys.exit(0)

bereiche = dp.erklaerungs_zeilen()
print("Bereiche:", bereiche)
print()

try:
    # --- Neu 8a: sieht der Check eine VORGEMERKTE Aenderung? ---
    ziel = bereiche[0][0] + 20            # irgendwo mitten in renderPrivacy
    neu = list(zeilen)
    neu[ziel - 1] = zeilen[ziel - 1].rstrip("\r\n") + " \n"
    INDEX.write_bytes("".join(neu).encode("utf-8"))
    vor_add = dp.ungesicherte_aenderung_am_abschnitt()
    git("add", "index.html")
    nach_add = dp.ungesicherte_aenderung_am_abschnitt()
    git("reset", "-q", "HEAD", "--", "index.html")
    sag(vor_add is True and nach_add is True,
        "Neu 8a: vorgemerkte Aenderung wird gesehen",
        f"vor `git add`: {vor_add} · nach `git add`: {nach_add} (frueher: False)")
    INDEX.write_bytes(orig)

    # --- Neu 9: geloeschte ERSTE Zeile eines Bereichs ---
    kvon = bereiche[1][0]                 # erste const PRIVACY_-Zeile
    neu = [z for i, z in enumerate(zeilen, start=1) if i != kvon]
    INDEX.write_bytes("".join(neu).encode("utf-8"))
    ergebnis = dp.ungesicherte_aenderung_am_abschnitt()
    sag(ergebnis is True,
        f"Neu 9: geloeschte erste Bereichszeile ({kvon}) wird gesehen",
        f"Ergebnis: {ergebnis} (frueher: False - Zaehlfehler um eins)")
    INDEX.write_bytes(orig)

    # --- Neu 8b: klemmendes git ist laut ---
    dp.HIER = Path(r"C:\gibt-es-nicht-xyz")
    ergebnis = dp.ungesicherte_aenderung_am_abschnitt()
    dp.HIER = REPO
    sag(ergebnis == "git-klemmt",
        "Neu 8b: klemmendes git meldet sich",
        f"Ergebnis: {ergebnis!r} (frueher: None - still)")

finally:
    INDEX.write_bytes(orig)
    git("reset", "-q", "HEAD", "--", "index.html")
    ok = hashlib.sha256(INDEX.read_bytes()).hexdigest() == h
    sag(ok, "index.html unveraendert wiederhergestellt")

print()
print("Nachmessung:", "bestanden" if not fehler else f"{fehler} Fehler")
sys.exit(1 if fehler else 0)
