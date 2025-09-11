BEGIN;

ALTER TABLE IF EXISTS pons ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS photos ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS smmes ENABLE ROW LEVEL SECURITY;

CREATE POLICY pons_allow_authenticated ON pons
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY tasks_allow_authenticated ON tasks
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY photos_allow_authenticated ON photos
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY assets_allow_authenticated ON assets
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY smmes_allow_authenticated ON smmes
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

COMMIT;