-- ============================================================================
--  Gym-Log · XP-Bestenliste                                       29.08.2026
-- ============================================================================
--
--  Karls Wunsch: auf der Erfolge-Seite die zehn Leute mit den meisten XP.
--
--  Dafuer muessen XP und Name ANDERER Nutzer lesbar sein. Bisher liegt beides
--  ausschliesslich im eigenen Datenblock `gymlog_data.data` -- und der ist per
--  RLS auf den Eigentuemer beschraenkt. Genau so soll er auch bleiben.
--
--  ⚠️ DESHALB EINE EIGENE TABELLE UND KEINE SICHT AUF `gymlog_data`.
--     Eine Sicht darauf muesste die Zeilensperre umgehen (SECURITY DEFINER) und
--     haette damit Zugriff auf den GANZEN Block: Trainings, Gewichte, Mahlzeiten,
--     Meldungen. Ein Tippfehler in der Spaltenliste -- und alles davon steht in
--     der Bestenliste. Diese Tabelle hier kann gar nicht mehr hergeben als das,
--     was ausdruecklich hineingeschrieben wurde: Name, XP, Zeitpunkt.
--     Dieselbe Lehre wie bei `email_for_username` am 24.08.2026.
--
--  ⚠️ WAS DAMIT SICHTBAR WIRD: jeder angemeldete Nutzer sieht die Benutzernamen
--     und XP-Staende aller anderen. Das ist der Zweck einer Bestenliste, aber es
--     ist eine Aenderung -- vorher sah niemand irgendetwas vom anderen.
--     KEINE E-Mail-Adressen. Die stehen hier nirgends und duerfen es nie.
--
--  ⚠️ DIE ZAHL KOMMT VOM GERAET, NICHT VOM SERVER. XP wird in der App gerechnet
--     und hier hochgeschrieben. Wer will, kann seinen Browser-Speicher aendern
--     und eine beliebige Zahl eintragen. Das ist fuer eine Liste unter Freunden
--     in Ordnung, aber es ist keine Wertung, auf die man etwas geben koennte.
--     Serverseitig nachrechnen ginge nur, wenn der Server die Einheiten kennt --
--     dann muesste `gymlog_data` geoeffnet werden, und das ist der schlechtere
--     Tausch.
--
--  Gefahrlos wiederholbar.
-- ============================================================================

create table if not exists public.gym_bestenliste (
  user_id  uuid primary key references auth.users(id) on delete cascade,
  name     text        not null,
  xp       integer     not null default 0,
  stand    timestamptz not null default now()
);

-- Die Liste wird immer "die hoechsten zehn" gelesen -- ohne Index waere das bei
-- jedem Aufruf ein voller Durchlauf. Bei vier Leuten egal, bei vierhundert nicht.
create index if not exists gym_bestenliste_xp_idx
  on public.gym_bestenliste (xp desc);

alter table public.gym_bestenliste enable row level security;

-- ---------------------------------------------------------------------------
--  Lesen: jeder ANGEMELDETE Nutzer sieht die ganze Liste.
--  ⚠️ `to authenticated`, nicht `to public` -- sonst koennte jeder mit dem
--     oeffentlichen Schluessel aus dem Quelltext der App die Namen abrufen,
--     ohne ein Konto zu haben. Genau der Fehler von `email_for_username`.
-- ---------------------------------------------------------------------------
drop policy if exists "bestenliste lesen" on public.gym_bestenliste;
create policy "bestenliste lesen"
  on public.gym_bestenliste for select
  to authenticated
  using (true);

-- ---------------------------------------------------------------------------
--  Schreiben: ausschliesslich die eigene Zeile.
--  ⚠️ `with check` bei insert UND update. Ohne das `with check` beim update
--     duerfte man eine fremde Zeile zwar nicht auswaehlen, aber die eigene auf
--     eine fremde user_id umschreiben -- und damit deren Eintrag uebernehmen.
-- ---------------------------------------------------------------------------
drop policy if exists "eigene zeile anlegen" on public.gym_bestenliste;
create policy "eigene zeile anlegen"
  on public.gym_bestenliste for insert
  to authenticated
  with check (auth.uid() = user_id);

drop policy if exists "eigene zeile aendern" on public.gym_bestenliste;
create policy "eigene zeile aendern"
  on public.gym_bestenliste for update
  to authenticated
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- Loeschen braucht niemand. Ohne Regel ist es fuer alle gesperrt -- das ist
-- die richtige Voreinstellung, nicht eine Luecke.

-- ---------------------------------------------------------------------------
--  Gegenprobe: so muss es danach aussehen.
--  Erwartet: drei Regeln (select fuer authenticated, insert + update nur eigen),
--  rowsecurity = true.
-- ---------------------------------------------------------------------------
select relrowsecurity as rls_an
  from pg_class
 where oid = 'public.gym_bestenliste'::regclass;

select policyname, cmd, roles::text, qual, with_check
  from pg_policies
 where schemaname = 'public'
   and tablename  = 'gym_bestenliste'
 order by cmd, policyname;
