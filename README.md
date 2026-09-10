# Gym-Log

Persönliche Trainings-App (PWA) — Trainings mit Übungs-Bibliothek, Live-Logging,
Pausen-Timer, Verlauf & Rekorde, plus Level-/Rang-System mit freischaltbaren Designs.

Läuft offline, Daten liegen lokal im Browser. Auf dem Handy über „Zum Home-Bildschirm
hinzufügen" als App installierbar.

**Live:** https://karlm-netizen.github.io/gym-log/

## Datenschutz

Die Datenschutzerklärung steht in `index.html` (Funktion `renderPrivacy`). Sie soll
nie hinter dem Code herhinken — deshalb hängen zwei Dinge daran:

| | |
|---|---|
| `datenschutz-pruefen.py` | **mechanisch:** unbekannte Ziele im Code · Stand vs. letzte Textänderung · Pflichtangaben (Art. 13) · Zusagen, die der Code widerlegt · tote Knöpfe |
| `datenschutz-gegenprobe.py` | **13 eingebaute Schadensfälle** — jeder muss als SCHWER herauskommen |

Beide laufen am Ende von `pruefungen.py` mit und gehen in dessen Rückgabewert ein:
**wer dort rot ist, pusht nicht.** Fehlt eine der Dateien, wird der Prüfstand rot —
nicht grün mit einer Zeile Hinweis.

### Der Datenschutz-Wächter

Was `grep` nicht sieht — ob eine Rechtsgrundlage trägt, ob eine Einwilligung
wirklich eingeholt wird, ob der Text nach Art. 12 verständlich ist — prüft ein
Agent. Seine Rolle steht in `ki-os-2/.claude/agents/datenschutz-waechter.md`.

**Er läuft nicht von selbst.** Gestartet wird er zusammen mit dem Fund-Sucher nach
einem größeren Umbau (Regel in `ki-os-2/CLAUDE.md`). Er ändert die Erklärung nie
selbst, sondern legt den Textvorschlag vor.

⚠️ **Vor jedem Push mit geändertem Datenschutztext:** `PRIVACY_STAND` mit hochziehen.
Die Prüfung schlägt sonst an — sie vergleicht das Datum mit dem Arbeitsbaum *und*
der git-Historie.
