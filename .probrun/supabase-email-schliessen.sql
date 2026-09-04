-- ============================================================================
--  Gym-Log · email_for_username entfernen                        24.08.2026
-- ============================================================================
--
--  Diese Funktion gab zu einem Benutzernamen die E-Mail-Adresse heraus. Sie war
--  fuer `anon` freigegeben und musste es sein -- gefragt wurde, BEVOR jemand
--  angemeldet ist. Wer einen Namen kannte oder erriet, bekam die Adresse dazu.
--
--  Am 24.08.2026 live nachgemessen, mit dem oeffentlichen Schluessel aus dem
--  Quelltext der App: HTTP 200, erreichbar ohne Anmeldung.
--
--  Angel-Log hat dieselbe Funktion am 18.08.2026 entfernt (v56). Ab Gym-Log v28
--  ruft die App sie nicht mehr -- Anmelden geht nur noch mit E-Mail.
--
--  ⚠️ `drop`, nicht bloss `revoke`: diese Datei wird mehrfach ausgefuehrt, und
--     ein stehengebliebener `grant` haette sie wieder geoeffnet.
--
--  ⚠️ Was hier NICHT zugemacht wird: `username_taken` bleibt oeffentlich und
--     muss es bleiben -- die Registrierung fragt damit, bevor jemand angemeldet
--     ist. Ob es einen Namen GIBT, ist also weiterhin abfragbar. Nur die E-Mail
--     dahinter nicht mehr.
--
--  Gefahrlos wiederholbar.
-- ============================================================================

drop function if exists public.email_for_username(text);

-- Gegenprobe: danach darf hier nichts mehr stehen.
select proname
  from pg_proc
 where proname = 'email_for_username';
