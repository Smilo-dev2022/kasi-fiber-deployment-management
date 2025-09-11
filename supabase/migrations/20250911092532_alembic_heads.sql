INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Generating static SQL
INFO  [alembic.runtime.migration] Will assume transactional DDL.
BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

INFO  [alembic.runtime.migration] Running upgrade  -> 0001_init
-- Running upgrade  -> 0001_init

CREATE TABLE pons (
    id UUID NOT NULL, 
    status VARCHAR DEFAULT 'planned', 
    PRIMARY KEY (id)
);

CREATE TABLE photos (
    id UUID NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TABLE tasks (
    id UUID NOT NULL, 
    pon_id UUID, 
    step VARCHAR, 
    status VARCHAR, 
    started_at TIMESTAMP WITH TIME ZONE, 
    completed_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(pon_id) REFERENCES pons (id)
);

CREATE TABLE smmes (
    id UUID NOT NULL, 
    PRIMARY KEY (id)
);

INSERT INTO alembic_version (version_num) VALUES ('0001_init') RETURNING alembic_version.version_num;

INFO  [alembic.runtime.migration] Running upgrade 0001_init -> 0002_sla_timers
-- Running upgrade 0001_init -> 0002_sla_timers

ALTER TABLE tasks ADD COLUMN sla_minutes INTEGER;

ALTER TABLE tasks ADD COLUMN sla_due_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE tasks ADD COLUMN breached BOOLEAN DEFAULT false NOT NULL;

ALTER TABLE pons ADD COLUMN sla_breaches INTEGER DEFAULT '0' NOT NULL;

CREATE INDEX idx_tasks_sla_due_at ON tasks (sla_due_at);

CREATE INDEX idx_tasks_breached ON tasks (breached);

UPDATE alembic_version SET version_num='0002_sla_timers' WHERE alembic_version.version_num = '0001_init';

INFO  [alembic.runtime.migration] Running upgrade 0002_sla_timers -> 0003_photo_geo
-- Running upgrade 0002_sla_timers -> 0003_photo_geo

ALTER TABLE photos ADD COLUMN gps_lat NUMERIC(9, 6);

ALTER TABLE photos ADD COLUMN gps_lng NUMERIC(9, 6);

ALTER TABLE photos ADD COLUMN taken_ts TIMESTAMP WITH TIME ZONE;

ALTER TABLE photos ADD COLUMN exif_ok BOOLEAN DEFAULT false NOT NULL;

ALTER TABLE photos ADD COLUMN within_geofence BOOLEAN DEFAULT false NOT NULL;

ALTER TABLE pons ADD COLUMN center_lat NUMERIC(9, 6);

ALTER TABLE pons ADD COLUMN center_lng NUMERIC(9, 6);

ALTER TABLE pons ADD COLUMN geofence_radius_m INTEGER DEFAULT '200' NOT NULL;

CREATE INDEX idx_photos_taken_ts ON photos (taken_ts);

UPDATE alembic_version SET version_num='0003_photo_geo' WHERE alembic_version.version_num = '0002_sla_timers';

INFO  [alembic.runtime.migration] Running upgrade 0003_photo_geo -> 0004_assets_qr
-- Running upgrade 0003_photo_geo -> 0004_assets_qr

CREATE TABLE assets (
    id UUID NOT NULL, 
    type VARCHAR NOT NULL, 
    code VARCHAR NOT NULL, 
    sku VARCHAR, 
    status VARCHAR DEFAULT 'In Store' NOT NULL, 
    pon_id UUID, 
    issued_to UUID, 
    installed_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    UNIQUE (code), 
    FOREIGN KEY(pon_id) REFERENCES pons (id)
);

