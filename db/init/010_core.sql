-- Core reference tables
create table if not exists client (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_at timestamptz not null default now()
);

create table if not exists ward (
  id uuid primary key default gen_random_uuid(),
  client_id uuid not null references client(id) on delete cascade,
  name text not null,
  created_at timestamptz not null default now()
);

create table if not exists app_user (
  id uuid primary key default gen_random_uuid(),
  client_id uuid references client(id),
  email text unique,
  display_name text,
  created_at timestamptz not null default now()
);

-- PON with geofence
create table if not exists pon (
  id uuid primary key default gen_random_uuid(),
  client_id uuid not null references client(id) on delete cascade,
  ward_id uuid not null references ward(id) on delete cascade,
  name text not null,
  geofence geometry(polygon, 4326) not null,
  status text not null default 'planned',
  created_at timestamptz not null default now()
);
create index if not exists pon_gix on pon using gist (geofence);

-- Tasks
create table if not exists task (
  id uuid primary key default gen_random_uuid(),
  client_id uuid not null references client(id) on delete cascade,
  ward_id uuid not null references ward(id) on delete cascade,
  pon_id uuid references pon(id) on delete set null,
  type text not null,
  status text not null default 'pending',
  created_by uuid references app_user(id),
  created_at timestamptz not null default now()
);
create index if not exists task_ward_status_idx on task(ward_id, status);
create index if not exists task_pon_status_idx on task(pon_id, status);

-- Photos with EXIF/GPS
create table if not exists photo (
  id uuid primary key default gen_random_uuid(),
  task_id uuid references task(id) on delete set null,
  pon_id uuid references pon(id) on delete set null,
  s3_key text not null,
  exif_time timestamptz,
  gps geometry(point, 4326),
  tags text[] not null default '{}',
  ai_flags jsonb not null default '{}',
  validated boolean not null default false,
  validation_errors text[] not null default '{}',
  created_by uuid references app_user(id),
  created_at timestamptz not null default now()
);
create index if not exists photo_gix on photo using gist (gps);
create index if not exists photo_tags_gin on photo using gin (tags);

-- Assets and QR chain of custody
create table if not exists asset (
  id uuid primary key default gen_random_uuid(),
  type text not null check (type in ('pole','drum','bracket')),
  pon_id uuid references pon(id) on delete set null,
  ward_id uuid references ward(id) on delete set null,
  qrcode text unique not null,
  status text not null default 'in_stock',
  gps geometry(point, 4326),
  created_at timestamptz not null default now()
);

create table if not exists chain_of_custody (
  id uuid primary key default gen_random_uuid(),
  asset_id uuid not null references asset(id) on delete cascade,
  from_party text,
  to_party text,
  action text not null check (action in ('scan_in','scan_out','install','move')),
  by_user uuid references app_user(id),
  at timestamptz not null default now(),
  ward_id uuid references ward(id) on delete set null,
  pon_id uuid references pon(id) on delete set null
);
create index if not exists coc_asset_id_idx on chain_of_custody(asset_id);

-- SLA timers
create table if not exists sla_timer (
  id uuid primary key default gen_random_uuid(),
  task_id uuid references task(id) on delete cascade,
  step text not null,
  target_hours int not null,
  started_at timestamptz,
  stopped_at timestamptz,
  breach_at timestamptz generated always as (started_at + make_interval(hours => target_hours)) stored
);
create index if not exists sla_open_idx on sla_timer(task_id) where stopped_at is null;

-- seed helper for organizations and routing
-- orgs
-- insert into organizations (id, name, type) values
-- (gen_random_uuid(), 'Main Civil Co', 'Civil'),
-- (gen_random_uuid(), 'Tech Splice Co', 'Technical'),
-- (gen_random_uuid(), 'Maint Ops Co', 'Maintenance');

-- contracts
-- insert into contracts (id, org_id, scope, wards, sla_minutes_p1, sla_minutes_p2, sla_minutes_p3, sla_minutes_p4)
-- select gen_random_uuid(), id, 'Maintenance', array['48','49'], 120, 240, 1440, 4320 from organizations where name='Maint Ops Co';

-- assignments by ward
-- insert into assignments (id, org_id, scope, ward, priority)
-- select gen_random_uuid(), id, 'Civil', '48', 10 from organizations where name='Main Civil Co';
-- insert into assignments (id, org_id, scope, ward, priority)
-- select gen_random_uuid(), id, 'Technical', '48', 10 from organizations where name='Tech Splice Co';
