-- Olive Baby Tracker - Database Schema

CREATE TABLE IF NOT EXISTS users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS babies (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    created_by  UUID NOT NULL REFERENCES users(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS baby_access (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    baby_id     UUID NOT NULL REFERENCES babies(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role        TEXT NOT NULL DEFAULT 'caregiver',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(baby_id, user_id)
);

CREATE TABLE IF NOT EXISTS magic_links (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       TEXT NOT NULL,
    token       TEXT UNIQUE NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    used        BOOLEAN NOT NULL DEFAULT false,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token       TEXT UNIQUE NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);

CREATE TABLE IF NOT EXISTS invites (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    baby_id     UUID NOT NULL REFERENCES babies(id) ON DELETE CASCADE,
    invited_by  UUID NOT NULL REFERENCES users(id),
    email       TEXT NOT NULL,
    token       TEXT UNIQUE NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    accepted    BOOLEAN NOT NULL DEFAULT false,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS feedings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    baby_id     UUID NOT NULL REFERENCES babies(id) ON DELETE CASCADE,
    logged_by   UUID REFERENCES users(id),
    occurred_at TIMESTAMPTZ NOT NULL,
    milk_type   TEXT NOT NULL,
    amount_oz   REAL NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_feedings_baby_date ON feedings(baby_id, occurred_at);

CREATE TABLE IF NOT EXISTS poops (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    baby_id     UUID NOT NULL REFERENCES babies(id) ON DELETE CASCADE,
    logged_by   UUID REFERENCES users(id),
    occurred_at TIMESTAMPTZ NOT NULL,
    poop_type   TEXT NOT NULL,
    notes       TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_poops_baby_date ON poops(baby_id, occurred_at);

CREATE TABLE IF NOT EXISTS sleeps (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    baby_id     UUID NOT NULL REFERENCES babies(id) ON DELETE CASCADE,
    logged_by   UUID REFERENCES users(id),
    start_time  TIMESTAMPTZ NOT NULL,
    end_time    TIMESTAMPTZ NOT NULL,
    duration_hrs REAL NOT NULL,
    notes       TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_sleeps_baby_date ON sleeps(baby_id, start_time);

CREATE TABLE IF NOT EXISTS weights (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    baby_id     UUID NOT NULL REFERENCES babies(id) ON DELETE CASCADE,
    logged_by   UUID REFERENCES users(id),
    occurred_at TIMESTAMPTZ NOT NULL,
    pounds      INTEGER NOT NULL,
    ounces      REAL NOT NULL,
    total_lbs   REAL NOT NULL,
    input_mode  TEXT NOT NULL DEFAULT 'lbs_oz',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_weights_baby_date ON weights(baby_id, occurred_at);
