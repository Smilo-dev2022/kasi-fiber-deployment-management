## Supabase setup

### Prerequisites
- Supabase CLI installed (`npm i -g supabase` or see docs)
- Docker running (for local dev)

### Structure
- `supabase/config.toml` – local project config
- `supabase/migrations/` – versioned SQL
- `supabase/seed.sql` – minimal seed
- `supabase/functions/` – edge functions (none yet)

### Usage
1. Start local stack
```bash
supabase start
```
2. Reset and apply migrations
```bash
supabase db reset --no-backup --debug | cat
```
3. Seed
```bash
supabase db execute --file supabase/seed.sql | cat
```
4. Stop stack
```bash
supabase stop
```

### Env for client
Set `REACT_APP_SUPABASE_URL` and `REACT_APP_SUPABASE_ANON_KEY` to your local or hosted project values.

