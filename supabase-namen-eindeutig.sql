-- ============================================================================
--  Gym-Log · Kein Benutzername zweimal                              15.09.2026
-- ============================================================================
--
--  Karl: „hast du auch eine sperre für gleiche namen es darf keine gleichen geben"
--
--  🔴 BIS HIERHER GAB ES NUR DIE FRAGE VORHER, KEINE SPERRE.
--     Die App ruft vor dem Registrieren `username_taken()`. Das hielt drei Wege
--     nicht auf:
--       1. Die Frage schlaegt fehl (Netz, Stoerung, seit heute auch die Bremse)
--          -> die App registriert mit einem Hinweis trotzdem.
--       2. Zwei Registrierungen mit demselben Namen im selben Moment -- beide
--          fragen, beide hoeren „frei".
--       3. Wer die Schnittstelle direkt ruft (PUT /auth/v1/user mit
--          data.username), fragt gar nicht erst -- auch NACH der Registrierung.
--
--  ➡️ Die Sperre sitzt deshalb dort, wo jeder Weg vorbei muss: an `auth.users`
--     selbst, als Trigger vor jedem Anlegen und jeder Namensaenderung.
--
--  ⚠️ Gleich heisst: ohne Gross/Klein und ohne Leerzeichen am Rand -- dieselbe
--     Regel wie in `username_taken()`. „Karl" und „ karl " sind derselbe Name.
--  ⚠️ `pg_advisory_xact_lock` je Name: zwei gleichzeitige Registrierungen mit
--     demselben Namen laufen nacheinander, und die zweite sieht die erste.
--     Ohne die Sperre saehen beide noch keinen Treffer (Fall 2 oben).
--  ⚠️ Eine Aenderung, die den eigenen Namen NICHT anfasst, laeuft immer durch --
--     sonst koennte ein Konto, das heute schon doppelt ist, sich nie wieder
--     aendern (Supabase schreibt die Zeile auch beim Anmelden).
--  ⚠️ Kein Name (leer) wird nicht geprueft: Konten ohne Username gibt es, und
--     die sind untereinander nicht „gleich".
--
--  Die Fehlermeldung, die Supabase beim Registrieren daraus macht, ist nur
--  „Database error saving new user". Die App fragt in dem Fall noch einmal
--  `username_taken()` und sagt dann „Username ist schon vergeben".
--
--  Gefahrlos wiederholbar. Aendert keine bestehenden Konten.
-- ============================================================================

create or replace function public.gym_name_eindeutig()
returns trigger
language plpgsql
security definer
set search_path = public, auth
as $$
declare
  neu text := lower(trim(coalesce(new.raw_user_meta_data->>'username', '')));
begin
  if neu = '' then
    return new;
  end if;
  if tg_op = 'UPDATE'
     and neu = lower(trim(coalesce(old.raw_user_meta_data->>'username', ''))) then
    return new;
  end if;

  perform pg_advisory_xact_lock(hashtext('gym-name:' || neu));

  if exists (
    select 1 from auth.users u
     where u.id <> new.id
       and lower(trim(coalesce(u.raw_user_meta_data->>'username', ''))) = neu
  ) then
    raise exception 'Benutzername vergeben' using errcode = '23505';
  end if;

  return new;
end;
$$;

revoke all on function public.gym_name_eindeutig() from public, anon, authenticated;

drop trigger if exists gym_name_eindeutig on auth.users;
create trigger gym_name_eindeutig
  before insert or update of raw_user_meta_data on auth.users
  for each row execute function public.gym_name_eindeutig();


-- ---------------------------------------------------------------------------
--  Gegenprobe: gibt es HEUTE schon doppelte Namen?
--  Erwartet: „No rows returned". Kommt eine Zeile, sind das Konten von vorher --
--  die Sperre fasst sie nicht an, verhindert aber jedes weitere.
-- ---------------------------------------------------------------------------
select lower(trim(raw_user_meta_data->>'username')) as name, count(*) as konten
  from auth.users
 where coalesce(trim(raw_user_meta_data->>'username'), '') <> ''
 group by 1
having count(*) > 1;
