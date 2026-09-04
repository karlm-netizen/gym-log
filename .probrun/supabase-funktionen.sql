-- ============================================================================
--  Gym-Log · Die zwei Funktionen, die die App ruft                 02.09.2026
-- ============================================================================
--
--  🔴 WARUM ES DIESE DATEI GIBT (Funde 6 und 9 vom 01.09.2026)
--
--  Die App ruft zwei Datenbank-Funktionen auf, die in KEINER .sql dieses
--  Ordners angelegt wurden:
--
--      username_taken(uname)     index.html · Registrierung
--      delete_own_account()      index.html · Konto loeschen
--
--  Wer das Supabase-Projekt aus den Dateien dieses Ordners neu aufsetzt,
--  bekommt eine Installation, in der beide fehlen -- und nichts im Repo
--  verraet das. Die Folgen sind still:
--
--    · `username_taken` fehlt  -> 404 auf jede Anfrage. Die App hat das bis
--      zum 02.09.2026 wie "Name ist frei" behandelt. Zwei Konten mit
--      demselben Namen fallen erst in der Bestenliste auf.
--    · `delete_own_account` fehlt -> 404. Konten werden grundsaetzlich nur
--      halb geloescht: die Daten sind weg, die Anmeldung bleibt. Immerhin
--      sagt die App das ehrlich ("dataonly").
--
--  ⚠️ WICHTIG, BEVOR DAS HIER JEMAND AUSFUEHRT
--
--     Diese Datei ist aus den AUFRUFEN in index.html geschrieben, nicht aus
--     der laufenden Datenbank ausgelesen. Was in Karls Supabase-Projekt
--     tatsaechlich steht, ist von hier aus nicht zu sehen -- moeglich ist
--     beides: die Funktionen sind laengst da (dann aendert `create or replace`
--     sie auf diese Fassung), oder sie fehlen (dann legt es sie an).
--
--     ➡️ Vor dem Ausfuehren einmal nachsehen, was da ist:
--
--         select proname, pg_get_functiondef(oid)
--           from pg_proc
--          where proname in ('username_taken','delete_own_account');
--
--     Kommt dort etwas anderes heraus als unten steht, ist die laufende
--     Fassung die richtige -- dann gehoert SIE hier hinein, nicht umgekehrt.
--
--  Gefahrlos wiederholbar.
-- ============================================================================


-- ---------------------------------------------------------------------------
--  1. Ist dieser Benutzername schon vergeben?
-- ---------------------------------------------------------------------------
--  ⚠️ MUSS fuer `anon` freigegeben sein: gefragt wird waehrend der
--     Registrierung, also bevor jemand angemeldet ist.
--
--  ⚠️ Damit ist abfragbar, OB es einen Namen gibt. Das ist der bewusst in Kauf
--     genommene Rest aus dem 24.08.2026 -- und genau die Grenze: die E-Mail
--     dahinter gibt diese Funktion nicht heraus, und `email_for_username`
--     wurde deshalb geloescht (siehe supabase-email-schliessen.sql).
--
--  ⚠️ SECURITY DEFINER, weil `auth.users` fuer `anon` nicht lesbar ist. Die
--     Funktion gibt nur `true`/`false` zurueck -- sie kann nichts anderes
--     hergeben, egal wer sie ruft.

create or replace function public.username_taken(uname text)
returns boolean
language sql
security definer
set search_path = public, auth
as $$
  select exists (
    select 1 from auth.users
     where lower(raw_user_meta_data->>'username') = lower(trim(uname))
  );
$$;

revoke all on function public.username_taken(text) from public;
grant execute on function public.username_taken(text) to anon, authenticated;


-- ---------------------------------------------------------------------------
--  2. Das eigene Konto loeschen
-- ---------------------------------------------------------------------------
--  ⚠️ Loescht IMMER nur `auth.uid()` -- den Aufrufer selbst. Es gibt keinen
--     Parameter, also auch nichts, was man auf eine fremde Kennung setzen
--     koennte. Das ist die ganze Absicherung, und sie reicht genau deshalb.
--
--  ⚠️ Nicht fuer `anon`. Ohne Anmeldung ist `auth.uid()` null, und dann
--     loescht das `delete` nichts -- aber gar nicht erst freigeben ist
--     ehrlicher als sich auf ein null zu verlassen.
--
--  ℹ️ Die App loescht VORHER schon `gymlog_data` und meldet `gym_push` ab.
--     Was hier faellt, ist die Anmeldung selbst; was per `on delete cascade`
--     daranhaengt, geht mit.

create or replace function public.delete_own_account()
returns void
language sql
security definer
set search_path = public, auth
as $$
  delete from auth.users where id = auth.uid();
$$;

revoke all on function public.delete_own_account() from public;
grant execute on function public.delete_own_account() to authenticated;


-- ---------------------------------------------------------------------------
--  Gegenprobe: beide muessen danach dastehen.
-- ---------------------------------------------------------------------------
select proname,
       pg_get_userbyid(proowner)                        as eigentuemer,
       prosecdef                                        as security_definer
  from pg_proc
 where pronamespace = 'public'::regnamespace
   and proname in ('username_taken', 'delete_own_account')
 order by proname;
