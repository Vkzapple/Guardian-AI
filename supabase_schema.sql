-- Jalankan di Supabase SQL Editor (Project -> SQL Editor -> New Query)

create table sessions (
    id bigint generated always as identity primary key,
    user_id text not null,
    "timestamp" timestamptz not null default now(),
    fatigue_score float8 not null,
    hr_zone int not null,
    hr_pct_of_max float8 not null,
    duration_in_high_zone_min float8 not null,
    goal text not null
);

-- Index biar query histori per user cepat (dipakai di GET /progress/{user_id})
create index idx_sessions_user_id_timestamp on sessions (user_id, "timestamp" desc);

-- (Opsional tapi disarankan) Row Level Security -- untuk prototype kita
-- disable dulu biar simpel, backend yang handle akses pakai service key.
alter table sessions enable row level security;

create policy "Allow all access via service role"
on sessions
for all
using (true)
with check (true);
