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
--  ⚠️ NACHTRAG 29.08.2026: die erste Fassung hatte in jeder Policy eine Zeile
--     `to authenticated`. Karl hat damit einen Fehler bekommen. Das ist die
--     einzige Konstruktion in dieser Datei, die in `supabase-meldungen.sql`
--     nicht vorkommt -- also raus damit. Abgesichert wird jetzt ueber
--     `auth.uid() is not null`, was dasselbe leistet und in diesem Projekt
--     nachweislich funktioniert.
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
--
--  ⚠️ `auth.uid() is not null` und NICHT `to authenticated` -- obwohl beides
--     dasselbe absichert. Grund: `to authenticated` hat beim ersten Versuch am
--     29.08.2026 einen Fehler geworfen, und es ist die einzige Zeile in dieser
--     Datei, die in `supabase-meldungen.sql` (laeuft seit dem 23.08.) nicht
--     vorkommt. Hier steht deshalb nur, was in diesem Projekt nachweislich geht.
--
--  ⚠️ Die Absicherung selbst bleibt: eine Anfrage ohne Anmeldung bringt kein
--     `sub` im Token mit, `auth.uid()` ist dann NULL, und die Bedingung ist
--     nicht erfuellt -- es kommt keine Zeile zurueck. Ohne diese Bedingung
--     koennte jeder mit dem oeffentlichen Schluessel aus dem Quelltext der App
--     die Namen abrufen, ohne ein Konto zu haben. Genau der Fehler von
--     `email_for_username` am 24.08.2026.
-- ---------------------------------------------------------------------------
drop policy if exists "bestenliste lesen" on public.gym_bestenliste;
create policy "bestenliste lesen"
  on public.gym_bestenliste for select
  using (auth.uid() is not null);

-- ---------------------------------------------------------------------------
--  Schreiben: ausschliesslich die eigene Zeile.
--  ⚠️ `with check` bei insert UND update. Ohne das `with check` beim update
--     duerfte man eine fremde Zeile zwar nicht auswaehlen, aber die eigene auf
--     eine fremde user_id umschreiben -- und damit deren Eintrag uebernehmen.
-- ---------------------------------------------------------------------------
drop policy if exists "eigene zeile anlegen" on public.gym_bestenliste;
create policy "eigene zeile anlegen"
  on public.gym_bestenliste for insert
  with check (auth.uid() = user_id);

drop policy if exists "eigene zeile aendern" on public.gym_bestenliste;
create policy "eigene zeile aendern"
  on public.gym_bestenliste for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- ---------------------------------------------------------------------------
--  Die eigene Zeile loeschen duerfen -- neu am 10.09.2026.
--
--  🔴 WARUM DAS HIER JETZT STEHT: hier stand bis heute "Loeschen braucht
--  niemand. Ohne Regel ist es fuer alle gesperrt -- das ist die richtige
--  Voreinstellung, nicht eine Luecke."
--  Das stimmte, solange "Konto loeschen" sich auf `on delete cascade` verlassen
--  konnte. Genau das tut es aber im Fall `'dataonly'` NICHT: scheitert
--  `delete_own_account`, bleibt das Konto stehen -- und mit ihm die Zeile,
--  also Name und XP-Stand, sichtbar fuer jeden Angemeldeten.
--
--  ⚠️ Am 10.09.2026 wurde in `deleteAccount()` ein DELETE eingebaut, ohne dass
--  es diese Regel gab. PostgREST antwortet darauf mit **204 wie bei Erfolg**,
--  es sind null Zeilen betroffen, und niemand sieht hin. Der Kommentar im Code
--  behauptete dabei das Gegenteil der Lage ("die Zeilensperre laesst ohnehin
--  nur die eigene Zeile zu"). Gefunden vom Fund-Sucher am selben Tag.
--
--  💡 Die Regel oeffnet nichts: `auth.uid() = user_id` laesst genau die eigene
--  Zeile zu, so wie bei `update` daneben.
-- ---------------------------------------------------------------------------
drop policy if exists "eigene zeile loeschen" on public.gym_bestenliste;
create policy "eigene zeile loeschen"
  on public.gym_bestenliste for delete
  using (auth.uid() = user_id);

-- ---------------------------------------------------------------------------
--  Zwei Schalter: oeffentlich / bei Freunden -- neu am 13.09.2026 (gym-log v0.099).
--
--  Karls Ansage: "mach 2 schalter für freundesliste udn für die öffentliche".
--
--  🔴 DAS KANN NUR DIE DATENBANK. Wuerde die App bloss beim Lesen filtern, koennte
--  jeder Angemeldete mit dem oeffentlichen Schluessel die "nur Freunde"-Zeilen
--  trotzdem abrufen -- der Filter waere eine Bitte, keine Sperre.
--
--  Sichtbar ist eine Zeile jetzt nur noch, wenn
--    · sie oeffentlich ist, ODER
--    · es die eigene ist, ODER
--    · sie fuer Freunde freigegeben ist UND der Lesende mit ihr befreundet ist.
--  Sind beide Schalter aus, loescht die App die Zeile -- dann gibt es nichts zu lesen.
--
--  ⚠️ Die Unterabfrage auf `gym_freunde` braucht KEIN `security definer`: jeder
--  darf dort seine eigenen Freundschaften sehen ("eigene freunde sehen"), und
--  genau die fragt sie ab. Eine fremde Freundschaft sieht sie nicht, kann also
--  auch keine fremde Zeile freischalten.
--
--  💡 `default true` bei beiden: bestehende Zeilen bleiben wie bisher sichtbar,
--  und eine App-Fassung, die die Spalten noch nicht kennt, schreibt weiter
--  "oeffentlich". Das ist Karls Voreinstellung (an).
-- ---------------------------------------------------------------------------
alter table public.gym_bestenliste
  add column if not exists oeffentlich boolean not null default true;
alter table public.gym_bestenliste
  add column if not exists freunde     boolean not null default true;

drop policy if exists "bestenliste lesen" on public.gym_bestenliste;
create policy "bestenliste lesen"
  on public.gym_bestenliste for select
  using (
    auth.uid() is not null and (
      oeffentlich
      or auth.uid() = user_id
      or (freunde and exists (
            select 1 from public.gym_freunde f
             where (f.a = auth.uid() and f.b = gym_bestenliste.user_id)
                or (f.b = auth.uid() and f.a = gym_bestenliste.user_id)))
    )
  );

-- ---------------------------------------------------------------------------
--  Gegenprobe: so muss es danach aussehen.
--  Erwartet: VIER Regeln (select, insert, update, delete), rowsecurity = true.
--  Seit 13.09.2026: in `qual` der select-Regel steht `oeffentlich` und `gym_freunde`.
--  ⚠️ Bis zum 10.09.2026 waren es drei -- `delete` fehlte, siehe oben.
--  In der Spalte `roles` steht bei allen {public} -- das ist richtig so:
--  abgesichert wird ueber `qual` bzw. `with_check`, nicht ueber die Rolle. Wer
--  nicht angemeldet ist, hat kein `auth.uid()` und faellt an der Bedingung durch.
-- ---------------------------------------------------------------------------
select relrowsecurity as rls_an
  from pg_class
 where oid = 'public.gym_bestenliste'::regclass;

select policyname, cmd, roles::text, qual, with_check
  from pg_policies
 where schemaname = 'public'
   and tablename  = 'gym_bestenliste'
 order by cmd, policyname;
