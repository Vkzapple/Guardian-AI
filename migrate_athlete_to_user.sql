-- Jalankan di Supabase SQL Editor
-- Migrasi: athletes -> users, athlete_id -> user_id (di semua tabel terkait)

alter table athletes rename to users;

alter table readings rename column athlete_id to user_id;
alter table alerts rename column athlete_id to user_id;

-- Rebuild index yang namanya masih menyebut athlete_id
drop index if exists readings_athlete_id_recorded_at_idx;
create index if not exists readings_user_id_recorded_at_idx
  on readings (user_id, recorded_at desc);

drop index if exists alerts_athlete_id_created_at_idx;
create index if not exists alerts_user_id_created_at_idx
  on alerts (user_id, created_at desc);

-- View latest_readings pakai athlete_id di "distinct on", perlu di-drop & rebuild
drop view if exists latest_readings;
create or replace view latest_readings as
select distinct on (user_id) *
from readings
order by user_id, recorded_at desc;
