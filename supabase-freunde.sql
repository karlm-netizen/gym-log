-- ============================================================================
--  Gym-Log · Freunde und die Bestenliste darunter               11.09.2026
-- ============================================================================
--
--  Karls Entscheidung vom 10.09.2026: "Leaderboard für Freunde", und zwar
--  **mit Code und Bestätigung** -- nicht über den Benutzernamen. Wer jemanden
--  hinzufügen will, gibt dessen Code ein; der andere muss annehmen.
--
--  ---------------------------------------------------------------------------
--  WARUM DREI TABELLEN UND ZWEI FUNKTIONEN, UND NICHT EINE TABELLE
--  ---------------------------------------------------------------------------
--
--  Der naheliegende Bau wäre eine Tabelle `gym_freunde_code` mit einer
--  Leseregel "jeder Angemeldete darf Codes lesen" -- dann könnte die App den
--  Code selbst nachschlagen. **Das wäre das Leck.**
--  PostgREST lässt jede Anfrage zu, die die Leseregel erfüllt, auch eine OHNE
--  Filter: `GET /gym_freunde_code?select=*` gäbe die komplette Liste zurück,
--  jeden Code jedes Nutzers. Ein Filter in der App ist keine Absicherung --
--  er steht in der App, und die App liegt offen im Quelltext.
--  ➡️ Deshalb: auf `gym_freunde_code` darf **jeder nur seine eigene Zeile**
--     lesen. Das Nachschlagen eines fremden Codes passiert ausschliesslich in
--     `freund_anfragen()`, einer Funktion mit `security definer` -- die sieht
--     die Tabelle, gibt aber nur ein Ergebnis heraus: ging / ging nicht.
--     Dieselbe Lehre wie bei `email_for_username` am 24.08.2026.
--
--  ---------------------------------------------------------------------------
--  ⚠️ IST EIN SECHSSTELLIGER CODE NICHT ZU KURZ ZUM RATEN?
--  ---------------------------------------------------------------------------
--
--  Er ist ratbar, ja: 31 Zeichen hoch 6 sind rund 887 Millionen -- viel, aber
--  nicht unknackbar, und eine Bremse gegen schnelles Durchprobieren hat diese
--  Datenbank nicht.
--  **Das ist trotzdem in Ordnung, und der Grund ist die Bestätigung.** Ein
--  erratener Code erzeugt nichts weiter als eine Anfrage, die der andere
--  wegtippen kann. Es gibt keinen Zustand, in dem ein Fremder durch Raten an
--  Daten kommt -- er kommt nur in eine Liste, die jemand ansieht.
--  🔴 **Deshalb gibt `freund_anfragen()` auch NICHT den Namen zurück, zu dem
--  der Code gehört.** Täte sie das, wäre Durchprobieren ein Weg, an Namen zu
--  kommen -- und dann wäre die Kürze des Codes sehr wohl ein Problem.
--  Der Name des Absenders wird beim Anfragen MITGESCHICKT, nicht nachgeschlagen:
--  es ist der eigene, da ist nichts zu verraten.
--
--  ---------------------------------------------------------------------------
--  WAS HIER NICHT DRINSTEHT
--  ---------------------------------------------------------------------------
--
--  Keine XP, keine Namen der Freunde, nichts über Training. Diese Tabellen
--  sagen nur, WER mit WEM verbunden ist. Die Zahlen für die Bestenliste holt
--  die App weiter aus `gym_bestenliste` (siehe supabase-bestenliste.sql) und
--  filtert sie auf die eigenen Freunde.
--  ⚠️ Wer Admin ist, steht seit dem 10.09.2026 gar nicht in `gym_bestenliste`
--  -- er taucht deshalb auch in der Freundesliste ohne Zahl auf. Das ist so
--  gewollt (Karls Ansage), aber es ist eine Folge, die man kennen muss.
--
--  ⚠️ Kein `to authenticated` in den Regeln. Abgesichert wird über
--  `auth.uid() is not null` -- genau wie in supabase-bestenliste.sql, wo die
--  andere Schreibweise am 29.08.2026 einen Fehler geworfen hat.
--
--  Gefahrlos wiederholbar.
-- ============================================================================


-- ===========================================================================
--  1. Der eigene Code
-- ===========================================================================

create table if not exists public.gym_freunde_code (
  user_id   uuid        primary key references auth.users(id) on delete cascade,
  code      text        not null unique,
  erstellt  timestamptz not null default now()
);

alter table public.gym_freunde_code enable row level security;

-- ---------------------------------------------------------------------------
--  🔴 NUR die eigene Zeile. Siehe die Begründung ganz oben -- eine großzügigere
--  Leseregel hier wäre gleichbedeutend damit, alle Codes zu veröffentlichen.
-- ---------------------------------------------------------------------------
drop policy if exists "eigenen code lesen" on public.gym_freunde_code;
create policy "eigenen code lesen"
  on public.gym_freunde_code for select
  using (auth.uid() = user_id);

-- Angelegt wird der Code von `freund_code_holen()`. Die Funktion läuft mit
-- `security definer` und braucht diese Regel nicht -- sie steht hier trotzdem,
-- damit ein Konto seinen Code notfalls auch von Hand bekommen kann.
drop policy if exists "eigenen code anlegen" on public.gym_freunde_code;
create policy "eigenen code anlegen"
  on public.gym_freunde_code for insert
  with check (auth.uid() = user_id);


-- ===========================================================================
--  2. Offene Anfragen
-- ===========================================================================

create table if not exists public.gym_freunde_anfragen (
  id        uuid        primary key default gen_random_uuid(),
  von       uuid        not null references auth.users(id) on delete cascade,
  an        uuid        not null references auth.users(id) on delete cascade,
  von_name  text        not null default '',
  erstellt  timestamptz not null default now(),
  unique (von, an)
);

create index if not exists gym_freunde_anfragen_an_idx
  on public.gym_freunde_anfragen (an);

alter table public.gym_freunde_anfragen enable row level security;

-- ---------------------------------------------------------------------------
--  Sehen darf eine Anfrage, wer sie geschickt hat oder wer gemeint ist.
--  ⚠️ Beide Richtungen mit Absicht: der Absender soll sehen, dass seine Anfrage
--  noch offen ist. Ohne das sähe eine verschickte Anfrage genauso aus wie eine,
--  die nie angekommen ist.
-- ---------------------------------------------------------------------------
drop policy if exists "eigene anfragen sehen" on public.gym_freunde_anfragen;
create policy "eigene anfragen sehen"
  on public.gym_freunde_anfragen for select
  using (auth.uid() = an or auth.uid() = von);

-- ---------------------------------------------------------------------------
--  Wegnehmen darf sie auch jeder von beiden: der Empfänger lehnt ab, der
--  Absender zieht zurück. Zwei Vorgänge, eine Regel.
--  🔴 Diese Regel MUSS es geben. Ohne sie wäre `delete` für alle gesperrt, das
--  Ablehnen liefe ins Leere -- und PostgREST meldete dabei **204 wie bei
--  Erfolg**. Genau der Fehler vom 10.09.2026 in der Bestenliste.
-- ---------------------------------------------------------------------------
drop policy if exists "eigene anfragen wegnehmen" on public.gym_freunde_anfragen;
create policy "eigene anfragen wegnehmen"
  on public.gym_freunde_anfragen for delete
  using (auth.uid() = an or auth.uid() = von);

-- ⚠️ KEINE insert-Regel. Anfragen entstehen ausschliesslich in
-- `freund_anfragen()` -- sonst könnte man sich Anfragen mit beliebigem
-- Absendernamen selbst ins Postfach legen.


-- ===========================================================================
--  3. Bestehende Freundschaften
-- ===========================================================================

-- ⚠️ EINE Zeile je Paar, nicht zwei. Die kleinere Kennung steht immer in `a`
-- (dafür der `check`). Zwei Zeilen je Paar wären der bequemere Bau -- und der
-- erste Ort, an dem eine halb gelöschte Freundschaft entsteht, die auf einer
-- Seite noch da ist und auf der anderen nicht.
create table if not exists public.gym_freunde (
  a     uuid        not null references auth.users(id) on delete cascade,
  b     uuid        not null references auth.users(id) on delete cascade,
  seit  timestamptz not null default now(),
  primary key (a, b),
  check (a < b)
);

create index if not exists gym_freunde_b_idx on public.gym_freunde (b);

alter table public.gym_freunde enable row level security;

drop policy if exists "eigene freunde sehen" on public.gym_freunde;
create policy "eigene freunde sehen"
  on public.gym_freunde for select
  using (auth.uid() = a or auth.uid() = b);

-- Beenden darf jeder von beiden.
drop policy if exists "freundschaft beenden" on public.gym_freunde;
create policy "freundschaft beenden"
  on public.gym_freunde for delete
  using (auth.uid() = a or auth.uid() = b);

-- ⚠️ Keine insert-Regel: Freundschaften entstehen nur über `freund_annehmen()`.


-- ===========================================================================
--  4. Den eigenen Code holen (und beim ersten Mal erzeugen)
-- ===========================================================================
--
--  ⚠️ Das Alphabet lässt 0/O/1/I/L weg. Der Code wird abgetippt oder vorgelesen
--  -- eine Null, die als O ankommt, ist ein Fehler, den niemand findet, weil
--  beide Seiten schwören, dasselbe zu haben.
--
--  ⚠️ Die Schleife versucht es bis zu zehnmal. Ein `unique` auf `code` fängt
--  die Kollision ab; ohne Wiederholung bekäme der unwahrscheinliche Fall einen
--  Fehler statt eines Codes. Bei 887 Millionen Möglichkeiten ist der zweite
--  Versuch praktisch nie nötig -- aber "praktisch nie" ist kein Zustand, den
--  man ungeprüft lässt.
-- ===========================================================================

create or replace function public.freund_code_holen()
returns text
language plpgsql
security definer
set search_path = public
as $$
declare
  v_uid     uuid := auth.uid();
  v_code    text;
  v_zeichen text := 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
  v_neu     text;
  i         int;
  n         int;
begin
  if v_uid is null then
    raise exception 'nicht angemeldet';
  end if;

  select code into v_code from public.gym_freunde_code where user_id = v_uid;
  if v_code is not null then
    return v_code;
  end if;

  for n in 1..10 loop
    v_neu := '';
    for i in 1..6 loop
      v_neu := v_neu || substr(v_zeichen, 1 + floor(random() * length(v_zeichen))::int, 1);
    end loop;
    begin
      insert into public.gym_freunde_code (user_id, code) values (v_uid, v_neu);
      return v_neu;
    exception when unique_violation then
      -- Zweimal dieselbe Kennung kann es nicht sein (user_id ist der Schlüssel),
      -- also war es der Code. Nochmal.
      continue;
    end;
  end loop;

  raise exception 'kein freier Code gefunden';
end;
$$;

revoke all on function public.freund_code_holen() from public;
grant execute on function public.freund_code_holen() to authenticated;


-- ===========================================================================
--  5. Eine Anfrage stellen
-- ===========================================================================
--
--  Rückgabe ist ein kurzes Wort, kein Satz -- die App schreibt den Text, damit
--  er sich ändern lässt, ohne die Datenbank anzufassen:
--    'ok'        Anfrage angelegt
--    'unbekannt' diesen Code gibt es nicht
--    'selbst'    das ist der eigene Code
--    'schon'     ihr seid bereits befreundet
--    'offen'     eine Anfrage liegt schon vor
--
--  🔴 'unbekannt' und 'selbst' sind absichtlich unterscheidbar, 'unbekannt' und
--  ein FALSCHER, aber existierender Code dagegen nicht -- beide führen zu 'ok'
--  bzw. 'unbekannt', ohne je einen Namen zu nennen. Wer durchprobiert, erfährt
--  nur, ob ein Code vergeben ist. Mehr gibt es hier nicht zu holen.
-- ===========================================================================

create or replace function public.freund_anfragen(p_code text, p_name text)
returns text
language plpgsql
security definer
set search_path = public
as $$
declare
  v_uid  uuid := auth.uid();
  v_ziel uuid;
  v_a    uuid;
  v_b    uuid;
begin
  if v_uid is null then
    raise exception 'nicht angemeldet';
  end if;

  -- Grosskleinschreibung egal, Striche und Leerzeichen raus: der Code wird
  -- abgetippt, und "k7-4xq2" ist derselbe wie "K74XQ2".
  p_code := upper(regexp_replace(coalesce(p_code, ''), '[^A-Za-z0-9]', '', 'g'));
  if p_code = '' then
    return 'unbekannt';
  end if;

  select user_id into v_ziel from public.gym_freunde_code where code = p_code;
  if v_ziel is null then
    return 'unbekannt';
  end if;
  if v_ziel = v_uid then
    return 'selbst';
  end if;

  v_a := least(v_uid, v_ziel);
  v_b := greatest(v_uid, v_ziel);
  if exists (select 1 from public.gym_freunde where a = v_a and b = v_b) then
    return 'schon';
  end if;

  -- ⚠️ Beide Richtungen prüfen. Liegt die Anfrage andersherum schon vor, wäre
  -- eine zweite kein Fehler, sondern zwei offene Anfragen zwischen denselben
  -- zwei Leuten -- und wer welche annimmt, entschiede der Zufall.
  if exists (select 1 from public.gym_freunde_anfragen
              where (von = v_uid and an = v_ziel) or (von = v_ziel and an = v_uid)) then
    return 'offen';
  end if;

  insert into public.gym_freunde_anfragen (von, an, von_name)
  values (v_uid, v_ziel, left(coalesce(p_name, ''), 40));

  return 'ok';
end;
$$;

revoke all on function public.freund_anfragen(text, text) from public;
grant execute on function public.freund_anfragen(text, text) to authenticated;


-- ===========================================================================
--  6. Eine Anfrage annehmen
-- ===========================================================================
--
--  🔴 Die Prüfung `an = auth.uid()` ist der ganze Punkt dieser Funktion. Sie
--  läuft mit `security definer`, sieht also alle Anfragen -- ohne diese Zeile
--  könnte jeder mit einer fremden Anfrage-Kennung eine Freundschaft stiften,
--  an der er selbst gar nicht beteiligt ist.
--
--  ⚠️ `on conflict do nothing` beim Einfügen: zweimal schnell hintereinander
--  auf "Annehmen" getippt darf keine Fehlermeldung geben. Die Anfrage wird
--  danach in jedem Fall weggeräumt.
-- ===========================================================================

create or replace function public.freund_annehmen(p_id uuid)
returns text
language plpgsql
security definer
set search_path = public
as $$
declare
  v_uid uuid := auth.uid();
  v_von uuid;
begin
  if v_uid is null then
    raise exception 'nicht angemeldet';
  end if;

  select von into v_von
    from public.gym_freunde_anfragen
   where id = p_id and an = v_uid;

  if v_von is null then
    return 'weg';          -- gibt es nicht (mehr), oder sie war nie an mich
  end if;

  insert into public.gym_freunde (a, b)
  values (least(v_uid, v_von), greatest(v_uid, v_von))
  on conflict do nothing;

  delete from public.gym_freunde_anfragen where id = p_id;
  return 'ok';
end;
$$;

revoke all on function public.freund_annehmen(uuid) from public;
grant execute on function public.freund_annehmen(uuid) to authenticated;


-- ===========================================================================
--  Gegenprobe: so muss es danach aussehen
-- ===========================================================================
--
--  Erwartet:
--    · drei Tabellen mit rls_an = true
--    · gym_freunde_code       2 Regeln (select, insert)
--    · gym_freunde_anfragen   2 Regeln (select, delete)  -- KEIN insert
--    · gym_freunde            2 Regeln (select, delete)  -- KEIN insert
--    · drei Funktionen, alle mit prosecdef = true
--
--  🔴 Fehlt bei `gym_freunde_anfragen` oder `gym_freunde` die delete-Regel,
--  läuft das Ablehnen bzw. das Beenden einer Freundschaft ins Leere -- und
--  PostgREST meldet dabei 204 wie bei Erfolg. Genau deshalb steht das hier.
-- ===========================================================================

select relname as tabelle, relrowsecurity as rls_an
  from pg_class
 where oid in ('public.gym_freunde_code'::regclass,
               'public.gym_freunde_anfragen'::regclass,
               'public.gym_freunde'::regclass);

select tablename, policyname, cmd, qual, with_check
  from pg_policies
 where schemaname = 'public'
   and tablename in ('gym_freunde_code', 'gym_freunde_anfragen', 'gym_freunde')
 order by tablename, cmd, policyname;

select proname, prosecdef as laeuft_als_eigentuemer
  from pg_proc
 where pronamespace = 'public'::regnamespace
   and proname in ('freund_code_holen', 'freund_anfragen', 'freund_annehmen')
 order by proname;
