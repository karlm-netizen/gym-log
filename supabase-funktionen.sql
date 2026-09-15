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
--
--  ℹ️ 15.09.2026: `username_taken` hat eine Bremse bekommen (siehe Abschnitt 1).
--     Die Fassung davor war laut Messung vom 15.09. live -- `create or replace`
--     ersetzt sie; die zwei neuen Tabellen legt die Datei selbst an.
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

--  🟠 BREMSE (15.09.2026, Karls Ansage: „username kannst du bauen")
--     Bis hierher war die Funktion ungebremst: ein Skript konnte in einer Minute
--     tausende Namen durchprobieren. Jetzt: hoechstens 10 Fragen je Verbindung
--     pro Minute, danach antwortet sie mit HTTP 429 bis zur naechsten Minute.
--
--  ⚠️ WIE eine Verbindung erkannt wird, ist eine Datenschutz-Frage: es geht nur
--     ueber die IP-Adresse. Gespeichert wird sie NICHT im Klartext, sondern als
--     SHA-256 ueber (IP + geheimes Salz). ⚠️ Das Salz ist der ganze Punkt -- ohne
--     es waere der Hash ueber alle IPv4-Adressen in Minuten zurueckgerechnet.
--     Es liegt in einer Tabelle, an die niemand ausser dieser Funktion kommt.
--  ⚠️ Nach 10 Minuten wird jede Zeile geloescht (bei jedem Aufruf aufgeraeumt).
--     Steht so in der Datenschutzerklaerung (Abschnitt „Wenn du dich registrierst").
--
--  ⚠️ `raise ... using errcode = 'PT429'`: PostgREST macht aus PTxyz den HTTP-Status
--     xyz. Die App erkennt daran „zu viele Versuche" und sagt es, statt still
--     „konnte nicht pruefen" zu melden und trotzdem zu registrieren.
--  ⚠️ Das `raise` rollt den Zaehler dieses Aufrufs zurueck. Harmlos: er steht dann
--     auf 10, und jede weitere Frage in dieser Minute kommt wieder bei 11 an.

create table if not exists public.gym_namen_bremse (
  schluessel text        not null,
  minute     timestamptz not null,
  anzahl     int         not null default 0,
  primary key (schluessel, minute)
);
alter table public.gym_namen_bremse enable row level security;
revoke all on public.gym_namen_bremse from anon, authenticated;
-- KEINE policy: lesen und schreiben darf nur die Funktion (security definer).

create table if not exists public.gym_namen_bremse_salz (
  id   int  primary key default 1 check (id = 1),
  salz text not null default gen_random_uuid()::text
);
alter table public.gym_namen_bremse_salz enable row level security;
revoke all on public.gym_namen_bremse_salz from anon, authenticated;
insert into public.gym_namen_bremse_salz (id) values (1) on conflict (id) do nothing;

create or replace function public.username_taken(uname text)
returns boolean
language plpgsql
security definer
set search_path = public, auth
as $$
declare
  kopf  json := coalesce(nullif(current_setting('request.headers', true), '')::json, '{}'::json);
  ip    text := coalesce(nullif(kopf->>'cf-connecting-ip', ''),
                         nullif(trim(split_part(kopf->>'x-forwarded-for', ',', 1)), ''),
                         'unbekannt');
  salz  text;
  schl  text;
  n     int;
begin
  select s.salz into salz from public.gym_namen_bremse_salz s where s.id = 1;
  schl := encode(sha256(convert_to(ip || coalesce(salz, ''), 'UTF8')), 'hex');

  delete from public.gym_namen_bremse where minute < now() - interval '10 minutes';

  insert into public.gym_namen_bremse as b (schluessel, minute, anzahl)
       values (schl, date_trunc('minute', now()), 1)
  on conflict (schluessel, minute) do update set anzahl = b.anzahl + 1
    returning b.anzahl into n;

  if n > 10 then
    raise exception 'zu viele Anfragen' using errcode = 'PT429';
  end if;

  return exists (
    select 1 from auth.users
     where lower(raw_user_meta_data->>'username') = lower(trim(uname))
  );
end;
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
--  Gegenprobe Bremse: die zwei Tabellen sind fuer anon/authenticated zu.
--  Erwartet: zwei Zeilen, beide mit rowsecurity = true.
-- ---------------------------------------------------------------------------
select tablename, rowsecurity
  from pg_tables
 where schemaname = 'public'
   and tablename in ('gym_namen_bremse', 'gym_namen_bremse_salz');

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
