-- =====================================================================
--  Gym-Log — Trainingsplan aus PDF: die Bremse (24.10.2026)
--
--  Karls Wahl: höchstens 3 Importe pro Person und Tag, dazu 50 für alle zusammen.
--  Gezählt wird in der Datenbank, damit niemand die Grenze im Browser umgehen kann.
--
--  Einrichten, in dieser Reihenfolge:
--   1. Diesen Block im SQL-Editor ausführen (Dashboard → SQL Editor → New query).
--      Am Ende stehen zwei Zähler; beide müssen 1 sein.
--   2. Edge Functions → „Deploy a new function" → „Via Editor", Name: plan-aus-pdf,
--      Inhalt: supabase/functions/plan-aus-pdf/index.ts aus diesem Repo, dann „Deploy".
--      In den Einstellungen der Funktion „Verify JWT" AUSschalten — die Funktion prüft die
--      Anmeldung selbst (/auth/v1/user), und mit den neuen Schlüsseln lehnt der Schalter
--      sonst gültige Anmeldungen ab.
--   3. Edge Functions → Secrets: ANTHROPIC_API_KEY = der Schlüssel aus console.anthropic.com.
--      Der Schlüssel gehört NUR dorthin, nie in die App und nie in dieses Repo.
--
--  Gefahrlos wiederholbar: alles ist "if not exists" bzw. "create or replace".
-- =====================================================================

-- ---------------------------------------------------------------------
--  1. Die Tabelle: nur WER und WANN, nie der Inhalt des PDFs.
--
--  ⚠️ RLS an und KEINE Policy: niemand liest oder schreibt hier direkt. Der einzige Weg
--  hinein ist die Funktion unten (security definer). Sonst könnte jeder seine eigenen
--  Zeilen löschen und die Bremse damit zurücksetzen.
-- ---------------------------------------------------------------------
create table if not exists public.pdf_importe (
  id       bigint      generated always as identity primary key,
  user_id  uuid        not null references auth.users(id) on delete cascade,
  erstellt timestamptz not null default now()
);
alter table public.pdf_importe enable row level security;
create index if not exists pdf_importe_wer_idx  on public.pdf_importe (user_id, erstellt);
create index if not exists pdf_importe_zeit_idx on public.pdf_importe (erstellt);

-- ---------------------------------------------------------------------
--  2. Die Bremse. Antwortet 'ok' (und zählt den Import), 'person', 'alle' oder 'anmelden'.
--
--  ⚠️ Die Sperre (advisory lock) macht aus zwei gleichzeitigen Anfragen eine Reihe.
--  Ohne sie zählen beide „2 von 3" und kommen beide durch.
--  ⚠️ Älter als 2 Tage wird bei jedem Aufruf gelöscht — so steht es in der
--  Datenschutzerklärung, und so lange braucht die Bremse die Zeilen höchstens.
-- ---------------------------------------------------------------------
create or replace function public.pdf_import_anmelden()
returns text
language plpgsql
security definer
set search_path = public
as $$
declare
  ich    uuid := auth.uid();
  n_ich  int;
  n_alle int;
begin
  if ich is null then return 'anmelden'; end if;
  perform pg_advisory_xact_lock(hashtext('pdf_importe'));
  delete from public.pdf_importe where erstellt < now() - interval '2 days';
  select count(*) into n_ich from public.pdf_importe
   where user_id = ich and erstellt > now() - interval '1 day';
  if n_ich >= 3 then return 'person'; end if;
  select count(*) into n_alle from public.pdf_importe
   where erstellt > now() - interval '1 day';
  if n_alle >= 50 then return 'alle'; end if;
  insert into public.pdf_importe (user_id) values (ich);
  return 'ok';
end
$$;

revoke all on function public.pdf_import_anmelden() from public, anon;
grant execute on function public.pdf_import_anmelden() to authenticated;

-- Sichtbare Zähler: „No rows" beweist nichts. Beide müssen 1 sein.
select
  (select count(*) from pg_tables where schemaname = 'public' and tablename = 'pdf_importe') as tabelle_da,
  (select count(*) from pg_proc where proname = 'pdf_import_anmelden')                       as bremse_da;
