-- Create a simple test table and permissive RLS policies for anon
create table if not exists public.test_ping (
    id uuid default gen_random_uuid() primary key,
    created_at timestamptz default now() not null,
    note text
);

alter table public.test_ping enable row level security;

-- Allow anon to select and insert (tighten later as needed)
do $$
begin
    if not exists (
        select 1 from pg_policies where schemaname = 'public' and tablename = 'test_ping' and policyname = 'anon_can_select'
    ) then
        create policy anon_can_select on public.test_ping for select to anon using (true);
    end if;
    if not exists (
        select 1 from pg_policies where schemaname = 'public' and tablename = 'test_ping' and policyname = 'anon_can_insert'
    ) then
        create policy anon_can_insert on public.test_ping for insert to anon with check (true);
    end if;
end $$;

grant usage on schema public to anon, authenticated;
grant select, insert on table public.test_ping to anon, authenticated;
