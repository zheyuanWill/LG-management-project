-- Ship Repair Module V2 Migration
-- Replaces old complex tables with simplified 4-model architecture

-- Create enum types for new module
DO $$ BEGIN CREATE TYPE projectstatus AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE taskstatus AS ENUM ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE taskcategory AS ENUM ('ENGINE', 'ELECTRICAL', 'HULL', 'PAINTING', 'PIPING', 'DECK', 'SAFETY', 'CLASS_SURVEY', 'OTHER'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE issuetype AS ENUM ('QUALITY', 'SCHEDULE', 'SAFETY', 'SUPPLY', 'OTHER'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE issueseverity AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE issuestatus AS ENUM ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Create new tables
CREATE TABLE IF NOT EXISTS sr_projects (
    id SERIAL PRIMARY KEY,
    project_name VARCHAR(200) NOT NULL,
    vessel_name VARCHAR(200) NOT NULL,
    ship_owner VARCHAR(200),
    shipyard VARCHAR(200),
    dock_in_date DATE,
    dock_out_date DATE,
    repair_specification TEXT,
    status projectstatus DEFAULT 'NOT_STARTED',
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS sr_tasks (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES sr_projects(id) ON DELETE CASCADE,
    task_name VARCHAR(500) NOT NULL,
    description TEXT,
    category taskcategory DEFAULT 'OTHER',
    status taskstatus DEFAULT 'PENDING',
    planned_start DATE,
    planned_end DATE,
    actual_start DATE,
    actual_end DATE,
    ai_generated BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS sr_daily_logs (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES sr_projects(id) ON DELETE CASCADE,
    log_date DATE NOT NULL,
    reporter_id INTEGER NOT NULL REFERENCES users(id),
    work_done TEXT,
    discoveries TEXT,
    tomorrow_plan TEXT,
    notes TEXT,
    ai_processed BOOLEAN DEFAULT FALSE,
    ai_processed_at TIMESTAMPTZ,
    ai_summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS sr_daily_log_attachments (
    id SERIAL PRIMARY KEY,
    daily_log_id INTEGER NOT NULL REFERENCES sr_daily_logs(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(200) NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS sr_issues (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES sr_projects(id) ON DELETE CASCADE,
    task_id INTEGER REFERENCES sr_tasks(id),
    daily_log_id INTEGER REFERENCES sr_daily_logs(id),
    issue_type issuetype DEFAULT 'OTHER',
    title VARCHAR(500) NOT NULL,
    description TEXT,
    severity issueseverity DEFAULT 'MEDIUM',
    status issuestatus DEFAULT 'OPEN',
    ai_generated BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT,
    resolved_at TIMESTAMPTZ,
    resolved_by INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Drop old tables (cascade to clean up FKs)
DROP TABLE IF EXISTS supplier_feedbacks CASCADE;
DROP TABLE IF EXISTS spare_part_risks CASCADE;
DROP TABLE IF EXISTS ncrs CASCADE;
DROP TABLE IF EXISTS anomalies CASCADE;
DROP TABLE IF EXISTS photo_evidences CASCADE;
DROP TABLE IF EXISTS daily_reports CASCADE;
DROP TABLE IF EXISTS plan_version_comparisons CASCADE;
DROP TABLE IF EXISTS repair_tasks CASCADE;
DROP TABLE IF EXISTS repair_plans CASCADE;
DROP TABLE IF EXISTS shipyard_quotes CASCADE;
DROP TABLE IF EXISTS shipyard_inquiries CASCADE;
DROP TABLE IF EXISTS customer_visits CASCADE;
DROP TABLE IF EXISTS ship_background_checks CASCADE;
