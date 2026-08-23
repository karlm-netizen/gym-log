-- =====================================================================
--  Gym-Log — Fehlermeldungen aus der App ("Bug-Report")
--  Einmal im Supabase-SQL-Editor ausführen (Dashboard → SQL Editor → New query).
--
--  Karls Ansage vom 22.08.2026: „alles wie bei Angel-Log" — Formular, Postfach,
--  Antworten aus Discord zurück in die App, Push. Gleicher Kanal wie Angel-Log,
--  aber eigene Überschrift.
--
--  Der Block ist gefahrlos wiederholbar: alles ist "if not exists" bzw.
--  "create or replace". Zweimal ausführen richtet keinen Schaden an.
--
--  ⚠️ Zum Kopieren dieser Datei: als UTF-8 lesen. Wird sie als Windows-1252
--  gelesen (PowerShell-Standard), stehen die Umlaute schon beim Einfügen
--  verdorben in der Funktion — und die Discord-Nachricht gibt danach nur
--  wieder, was hier steht. Genau das ist bei Angel-Log passiert.
-- =====================================================================

-- ---------------------------------------------------------------------
--  1. Die Tabelle
--
--  id ist TEXT, nicht UUID — dieselbe Begründung wie bei Angel-Log: die App
--  erzeugt IDs per crypto.randomUUID(), hat aber einen Rückfall für alte
--  Safari-Versionen, der kein gültiges UUID-Format liefert.
--
--  ⚠️ Absichtlich KEIN Leserecht auf fremde Zeilen und keine Änderung/Löschung:
--  eine abgeschickte Meldung soll nicht nachträglich verschwinden können.
--  Karl liest sie im Dashboard (dort gilt RLS nicht), der Melder nur seine eigenen.
--
--  `umfeld` enthält, was eine Meldung erst brauchbar macht: Fassung, Gerät,
--  Bildschirm, Netz, Anzahl Einheiten, letzter Abgleich. Ohne das steht dort
--  „geht nicht" und niemand kann etwas damit anfangen.
-- ---------------------------------------------------------------------
create table if not exists public.gym_meldungen (
  id       text        primary key,
  user_id  uuid        not null default auth.uid()
                       references auth.users(id) on delete cascade,
  erstellt timestamptz not null default now(),
  text     text        not null,
  umfeld   jsonb
);

-- ⚠️ `create table if not exists` fasst eine BESTEHENDE Tabelle nicht an.
--    Neue Spalten müssen deshalb als `alter table` danebenstehen.
--
--  `nummer` ist die kurze Zahl, unter der eine Meldung in Discord steht. Die `id`
--  ist im Gerät erzeugt und zum Vorlesen viel zu lang; auf "#12" kann Karl
--  antworten, ohne etwas zu kopieren. Sie ist außerdem das Band, an dem der Bot
--  eine Antwort wieder ihrem Ticket zuordnet.
create sequence if not exists public.gym_meldungen_nr_seq;
alter table public.gym_meldungen
  add column if not exists nummer     bigint not null
                                      default nextval('public.gym_meldungen_nr_seq'),
  add column if not exists antwort    text,
  add column if not exists antwort_am timestamptz,
  add column if not exists gelesen_am timestamptz;

create index if not exists gym_meldungen_zeit_idx
  on public.gym_meldungen (erstellt desc);
-- Die App fragt bei jedem Abgleich "gibt es Antworten für mich?".
create index if not exists gym_meldungen_antwort_idx
  on public.gym_meldungen (user_id, antwort_am desc);

alter table public.gym_meldungen enable row level security;

drop policy if exists "eigene gym-meldungen lesen"   on public.gym_meldungen;
drop policy if exists "eigene gym-meldungen anlegen" on public.gym_meldungen;

create policy "eigene gym-meldungen lesen"   on public.gym_meldungen
  for select using (auth.uid() = user_id);
create policy "eigene gym-meldungen anlegen" on public.gym_meldungen
  for insert with check (auth.uid() = user_id);

-- ---------------------------------------------------------------------
--  2. Die Bremse: höchstens 5 Meldungen je 10 Minuten und Konto
--
--  ⚠️ Die Bremse muss HIER stehen und nicht nur in der App. Was die App sperrt,
--     sperrt nur die App: der Zugang zur Datenbank steht jedem offen, der den
--     öffentlichen Schlüssel aus dem Quelltext liest — und der steht dort
--     bauartbedingt. Eine Sperre im Browser ist eine Bitte, keine Grenze.
--
--  ⚠️ Bewusst eine Mengengrenze statt "60 Sekunden Abstand". Bei Angel-Log ist
--     aufgefallen: eine Meldung liegt erst im Gerät und geht mit dem nächsten
--     Abgleich hinaus. Wer ohne Netz zwei Meldungen schreibt, schickt beim
--     Wiederverbinden zwei auf einmal — eine Abstandsregel würde die zweite
--     abweisen, bei jedem weiteren Abgleich erneut, für immer.
--
--  ⚠️ Gezählt wird je Konto, nicht insgesamt — sonst bremsten sich zwei Melder
--     gegenseitig aus.
-- ---------------------------------------------------------------------
create or replace function public.gym_meldung_bremse()
returns trigger
language plpgsql
security definer            -- zählt auch Zeilen, die dem Melder nicht gehören
set search_path = public
as $$
declare
  wieviele int;
  frei     timestamptz;
  rest     int;
begin
  /* ⚠️ Gezählt wird über `erstellt`, und das ist zulässig, weil die App die
     Spalte NICHT mitschickt — sie fällt auf `default now()` zurück und ist damit
     der Eingangszeitpunkt auf dem Server, nicht eine Zahl vom Gerät. Eine Bremse,
     die auf einen vom Melder gelieferten Zeitstempel hört, bremst nur den Ehrlichen. */
  select count(*), min(erstellt)
    into wieviele, frei
    from public.gym_meldungen
   where user_id = new.user_id
     and erstellt > now() - interval '10 minutes';

  if wieviele >= 5 then
    rest := ceil(extract(epoch from (frei + interval '10 minutes' - now())));
    /* Die verbleibende Zahl gehört in die Meldung. Ohne sie steht in der App
       "zu schnell" und niemand weiß, ob er 2 oder 500 Sekunden warten soll. */
    raise exception 'GYM_BREMSE:%', greatest(rest, 1)
      using errcode = 'check_violation';
  end if;
  return new;
end $$;

drop trigger if exists gym_meldungen_bremse on public.gym_meldungen;
create trigger gym_meldungen_bremse
  before insert on public.gym_meldungen
  for each row execute function public.gym_meldung_bremse();

-- ---------------------------------------------------------------------
--  3. Eine Antwort als gelesen abhaken
--
--  ⚠️ Bewusst eine Funktion und keine UPDATE-Policy. Oben steht als Grundsatz:
--     eine abgeschickte Meldung soll sich nicht nachträglich ändern können. Eine
--     allgemeine UPDATE-Policy hätte genau das erlaubt — RLS kann Zeilen
--     einschränken, aber keine einzelnen Spalten. Diese Funktion fasst
--     ausschließlich `gelesen_am` an und nur an eigenen Zeilen.
-- ---------------------------------------------------------------------
create or replace function public.gym_meldung_gelesen(mid text)
returns void
language sql
security definer
set search_path = public
as $$
  update public.gym_meldungen
     set gelesen_am = now()
   where id = mid
     and user_id = auth.uid()
     and antwort is not null
     and gelesen_am is null;
$$;

revoke all on function public.gym_meldung_gelesen(text) from public;
grant execute on function public.gym_meldung_gelesen(text) to authenticated;

-- ---------------------------------------------------------------------
--  4. Meldungen zustellen statt nachsehen
--
--  Eine Meldung, von der niemand erfährt, ist so gut wie keine. Jede neue Zeile
--  geht deshalb als Nachricht an einen Discord-Webhook.
--
--  ⚠️ Die Webhook-Adresse steht NICHT in dieser Datei. Dieses Repo ist öffentlich;
--  wer die Adresse hat, kann in den Kanal schreiben. Sie liegt in einer eigenen
--  Tabelle, die per API für niemanden lesbar ist (RLS an, keine einzige Policy —
--  damit kommt nur das Dashboard bzw. die service_role dran).
--  Eingetragen wird sie einmal von Hand — siehe Block 5 ganz unten.
--
--  Ohne Eintrag passiert schlicht nichts — die App läuft unverändert weiter.
--
--  ⚠️ net.http_post() aus pg_net ist ASYNCHRON: es legt die Anfrage in eine
--  Warteschlange und kehrt sofort zurück. Das ist kein Detail, sondern der Grund,
--  warum es überhaupt in einem Trigger stehen darf. Würde der Versand auf Discord
--  warten, hinge das Abschicken einer Meldung an der Erreichbarkeit eines fremden
--  Servers — und ausgerechnet die Fehlermeldung wäre das Erste, was bei Störungen
--  nicht mehr durchkommt.
-- ---------------------------------------------------------------------
create extension if not exists pg_net;

create table if not exists public.gym_konfig (
  schluessel text primary key,
  wert       text not null
);
alter table public.gym_konfig enable row level security;
-- Absichtlich keine Policy. Kein Nutzer, auch kein angemeldeter, kommt hier ran.

create or replace function public.gym_meldung_zustellen()
returns trigger
language plpgsql
security definer                      -- der Melder darf gym_konfig nicht lesen
set search_path = public, net, extensions, auth
as $$
declare
  ziel     text;
  txt      text;
  abgleich text;
  melder   text;
  ping_id  text;
begin
  select wert into ziel from public.gym_konfig where schluessel = 'discord_webhook';
  if ziel is null or ziel = '' then return new; end if;

  /* ---- Wer hat gemeldet? ----
     ⚠️ Anders als Angel-Log hat Gym-Log KEINE Profil-Tabelle und keine
     Benutzernamen — es gibt nur `gymlog_data` (id + data). Als Kennung bleibt
     deshalb die E-Mail aus `auth.users`. Diese Funktion ist `security definer`,
     nur deshalb darf sie dort überhaupt lesen.
     ⚠️ `coalesce` auf 'unbekannt': fällt die Zeile weg, sähe es sonst aus, als
     sei der Melder vergessen worden. */
  select u.email into melder from auth.users u where u.id = new.user_id;
  melder := coalesce(melder, 'unbekannt');

  /* ---- Wen soll Discord anpingen? ----
     Die ID steht in `gym_konfig`, nicht hier im Quelltext: sie ändert sich, wenn
     Karl den Server wechselt, und dann soll niemand eine Funktion neu einspielen
     müssen. Steht dort nichts, wird nicht gepingt — und nicht etwa `<@>` geschrieben. */
  select wert into ping_id from public.gym_konfig where schluessel = 'discord_ping';
  if ping_id is not null and ping_id !~ '^\d+$' then ping_id := null; end if;

  -- Ein Zeitpunkt in ISO-Schreibweise ist zum Lesen nichts. 'nie' bleibt 'nie'.
  abgleich := coalesce(new.umfeld->>'letzterAbgleich', '?');
  if abgleich ~ '^\d{4}-\d{2}-\d{2}' then
    abgleich := to_char(abgleich::timestamptz at time zone 'Europe/Berlin',
                        'DD.MM. HH24:MI');
  end if;

  /* ⚠️ Bewusst OHNE Discord-Auszeichnung (**fett**, > Zitat, `Code`). Karls Ansage
     vom 10.08.2026 zu Angel-Log: „mach doch die komischen zeichen raus".
     ⚠️ Zeile 1 bleibt UNVERÄNDERT und beginnt genau mit "🏋 Gym-Log — Meldung #<zahl>".
     Der Bot liest die Nummer dort wieder heraus, wenn Karl mit Discords
     Antworten-Funktion antwortet — ohne sie gibt es kein Band zwischen Antwort und
     Ticket. Alles Neue gehört deshalb in Zeile 2, nicht davor und nicht dazwischen.
     ⚠️ Die Überschrift unterscheidet sich bewusst von Angel-Log ("🐞 Angel-Log"),
     weil beide Apps in DENSELBEN Kanal schreiben. */
  txt := '🏋 Gym-Log — Meldung #' || new.nummer || E'\n'
      || 'Von: ' || melder
      || coalesce('  <@' || ping_id || '>', '') || E'\n\n'
      || coalesce(new.text, '') || E'\n\n'
      || 'Fassung ' || coalesce(new.umfeld->>'fassung', '?')
      || ' · ' || coalesce(new.umfeld->>'netz', '?')
      || ' · ' || coalesce(new.umfeld->>'bildschirm', '?')
      || ' · ' || coalesce(new.umfeld->>'einheiten', '?') || ' Einheiten' || E'\n'
      || 'Letzter Abgleich: ' || abgleich || E'\n'
      || 'Gerät: ' || coalesce(new.umfeld->>'geraet', '?');

  perform net.http_post(
    url     := ziel,
    /* ⚠️ Genau `application/json`, ohne Zeichensatz dahinter. pg_net prüft den Kopf
       selbst und bricht bei allem anderen mit einer Ausnahme ab. Und weil diese
       Ausnahme in einem Trigger geworfen wird, fällt die ganze INSERT-Anweisung mit
       — die Meldung landet dann nicht einmal in der Tabelle. Bei Angel-Log am
       10.08.2026 genau so passiert. */
    headers := '{"Content-Type": "application/json"}'::jsonb,
    /* ⚠️ `allowed_mentions: {"parse": []}` ist kein Schönheitsflicken, sondern ein
       Loch, das ohne ihn offensteht. Ein Webhook löst Erwähnungen im Text
       standardmäßig auf. In diesen Text schreibt ein FREMDER — jeder, der die App
       hat. Wer "@everyone" ins Meldefeld tippt, pingt sonst Karls ganzen Server.
       ⚠️ `parse: []` und `users: [...]` schließen sich nicht aus, sie ergänzen sich:
       `parse` sagt, was aus dem TEXT aufgelöst werden darf (nichts), `users` ist die
       ausdrückliche Freigabe für genau diese eine ID. */
    body    := jsonb_build_object(
                 'content', left(txt, 1900),
                 'allowed_mentions', case
                   when ping_id is null then jsonb_build_object('parse', '[]'::jsonb)
                   else jsonb_build_object('parse', '[]'::jsonb,
                                           'users', jsonb_build_array(ping_id))
                 end)
  );
  return new;
end $$;

drop trigger if exists gym_meldungen_zustellen on public.gym_meldungen;
create trigger gym_meldungen_zustellen
  after insert on public.gym_meldungen
  for each row execute function public.gym_meldung_zustellen();

-- =====================================================================
--  5. ⚠️ NOCH ZU TUN — zwei Zeilen von Hand, sonst kommt nichts an
--
--  Die Webhook-Adresse ist DIESELBE wie bei Angel-Log (#bug-reports-angel-log)
--  — Karls Entscheidung vom 22.08.2026: gleicher Kanal, eigene Überschrift.
--
--  ⚠️ **Nachgemessen am 23.08.2026: die beiden Apps liegen in VERSCHIEDENEN
--     Supabase-Projekten.** gym-log ist `uvtxkdasgllnfkvtnkrq`, angel-log ist
--     `vxyvkyhbomdpdyqtbeza`. Ein `select ... from public.angel_konfig` geht hier
--     deshalb ins Leere — die Tabelle existiert in diesem Projekt gar nicht.
--
--  Zwei Wege an die Adresse:
--    a) Im Discord: Kanal #bug-reports-angel-log → Bearbeiten → Integrationen →
--       Webhooks → URL kopieren. (Der kuerzeste Weg.)
--    b) Im ANDEREN Supabase-Projekt (`vxyvkyhbomdpdyqtbeza`) im SQL-Editor:
--         select wert from public.angel_konfig where schluessel = 'discord_webhook';
--
--  Beide Zeilen hier einfügen und ausführen:
-- =====================================================================

-- insert into public.gym_konfig (schluessel, wert)
-- values ('discord_webhook', 'https://discord.com/api/webhooks/HIER_EINSETZEN')
-- on conflict (schluessel) do update set wert = excluded.wert;

-- insert into public.gym_konfig (schluessel, wert)
-- values ('discord_ping', '647688538816774154')
-- on conflict (schluessel) do update set wert = excluded.wert;
