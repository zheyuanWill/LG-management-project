-- Migration: Simplify ship repair MVP
-- Run this inside the postgres container: docker exec -i lgm-postgres psql -U postgres -d lg_management < migrate_mvp_simplify.sql

-- ========================================
-- 1. RepairPlan changes
-- ========================================

-- Add new fields
ALTER TABLE repair_plans ADD COLUMN IF NOT EXISTS plan_name VARCHAR(500);
ALTER TABLE repair_plans ADD COLUMN IF NOT EXISTS vessel_name VARCHAR(200);
ALTER TABLE repair_plans ADD COLUMN IF NOT EXISTS progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100);

-- Create new status enum type
DO $$ BEGIN
    CREATE TYPE repairplanstatus AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Add status column
ALTER TABLE repair_plans ADD COLUMN IF NOT EXISTS status repairplanstatus DEFAULT 'NOT_STARTED';

-- Drop the unique constraint on order_id + version (MVP doesn't need version tracking)
ALTER TABLE repair_plans DROP CONSTRAINT IF EXISTS uq_repair_plan_order_version;

-- Make version nullable (we'll phase it out but keep the column for now)
ALTER TABLE repair_plans ALTER COLUMN version DROP NOT NULL;

-- ========================================
-- 2. DailyReport changes
-- ========================================

-- Rename completed_tasks to today_work
ALTER TABLE daily_reports RENAME COLUMN completed_tasks TO today_work;

-- Add tomorrow_plan field
ALTER TABLE daily_reports ADD COLUMN IF NOT EXISTS tomorrow_plan TEXT;

-- Add linked_ncr_id
ALTER TABLE daily_reports ADD COLUMN IF NOT EXISTS linked_ncr_id INTEGER REFERENCES ncrs(id);

-- Drop columns we don't need in MVP
ALTER TABLE daily_reports DROP COLUMN IF EXISTS unfinished_tasks;
ALTER TABLE daily_reports DROP COLUMN IF EXISTS unfinished_reason;
ALTER TABLE daily_reports DROP COLUMN IF EXISTS affects_quality;
ALTER TABLE daily_reports DROP COLUMN IF EXISTS affects_safety;
ALTER TABLE daily_reports DROP COLUMN IF EXISTS requires_gm_decision;
ALTER TABLE daily_reports DROP COLUMN IF EXISTS gm_decision_items;
ALTER TABLE daily_reports DROP COLUMN IF EXISTS one_line_summary;
ALTER TABLE daily_reports DROP COLUMN IF EXISTS linked_spare_part_risk_id;

-- ========================================
-- 3. NCR changes
-- ========================================

-- Create priority enum
DO $$ BEGIN
    CREATE TYPE ncrpriority AS ENUM ('URGENT', 'HIGH', 'MEDIUM', 'LOW');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Add new fields
ALTER TABLE ncrs ADD COLUMN IF NOT EXISTS priority ncrpriority DEFAULT 'MEDIUM';
ALTER TABLE ncrs ADD COLUMN IF NOT EXISTS responsible_person VARCHAR(200);
ALTER TABLE ncrs ADD COLUMN IF NOT EXISTS rectification_deadline DATE;

-- Simplify status enum (keep existing values but we'll only use 3 in the app)
-- The existing NCRStatus enum has PENDING, IN_PROGRESS, PENDING_REVIEW, CLOSED, OVERDUE, CANCELLED
-- We'll just use PENDING, IN_PROGRESS, CLOSED in the app logic

-- ========================================
-- 4. Data migration for existing records
-- ========================================

-- Set plan_name from notes or default value for existing plans
UPDATE repair_plans SET plan_name = COALESCE(SUBSTRING(notes FROM 1 FOR 100), '修船计划') WHERE plan_name IS NULL;

-- Set progress to 0 for all existing plans
UPDATE repair_plans SET progress = 0 WHERE progress IS NULL;

-- Set status based on ai_disassembled and human_confirmed
UPDATE repair_plans SET status = 
    CASE 
        WHEN human_confirmed THEN 'IN_PROGRESS'
        ELSE 'NOT_STARTED'
    END
WHERE status IS NULL;

-- Set tomorrow_plan to empty string for existing daily reports
UPDATE daily_reports SET tomorrow_plan = '' WHERE tomorrow_plan IS NULL;

-- Set priority to MEDIUM for existing NCRs
UPDATE ncrs SET priority = 'MEDIUM' WHERE priority IS NULL;

-- ========================================
-- Done!
-- ========================================
