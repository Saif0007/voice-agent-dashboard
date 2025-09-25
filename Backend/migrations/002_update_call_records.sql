-- Migration: Add new fields to call_records table
-- Run this after the initial supabase_schema.sql has been executed

-- Add new columns to call_records table if they don't exist
DO $$
BEGIN
    -- Add access_token column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'call_records' AND column_name = 'access_token') THEN
        ALTER TABLE call_records ADD COLUMN access_token TEXT;
    END IF;

    -- Add call_type column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'call_records' AND column_name = 'call_type') THEN
        ALTER TABLE call_records ADD COLUMN call_type VARCHAR(50) DEFAULT 'phone_call';
    END IF;

    -- Add driver_name column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'call_records' AND column_name = 'driver_name') THEN
        ALTER TABLE call_records ADD COLUMN driver_name VARCHAR(255);
    END IF;

    -- Add load_number column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'call_records' AND column_name = 'load_number') THEN
        ALTER TABLE call_records ADD COLUMN load_number VARCHAR(255);
    END IF;

    -- Add phone_number column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'call_records' AND column_name = 'phone_number') THEN
        ALTER TABLE call_records ADD COLUMN phone_number VARCHAR(50);
    END IF;

    -- Add llm_id column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'call_records' AND column_name = 'llm_id') THEN
        ALTER TABLE call_records ADD COLUMN llm_id VARCHAR(255);
    END IF;
END $$;

-- Update the status column to include new status values (if needed)
-- This is safe to run multiple times
COMMENT ON COLUMN call_records.status IS 'Status values: active, completed, failed, initiated, registered';

-- Add indexes for the new columns for better performance
CREATE INDEX IF NOT EXISTS idx_call_records_call_type ON call_records(call_type);
CREATE INDEX IF NOT EXISTS idx_call_records_driver_name ON call_records(driver_name);
CREATE INDEX IF NOT EXISTS idx_call_records_load_number ON call_records(load_number);
CREATE INDEX IF NOT EXISTS idx_call_records_llm_id ON call_records(llm_id);

-- Update the view to include new fields
DROP VIEW IF EXISTS call_records_with_details;
CREATE OR REPLACE VIEW call_records_with_details AS
SELECT
    cr.*,
    cp.name as prompt_name,
    cp.content as prompt_content,
    ra.agent_name,
    ra.voice_id,
    rl.model as llm_model
FROM call_records cr
LEFT JOIN conversation_prompts cp ON cr.prompt_id = cp.id
LEFT JOIN retell_agents ra ON cr.agent_id = ra.agent_id
LEFT JOIN retell_llms rl ON cr.llm_id = rl.llm_id
ORDER BY cr.created_at DESC;

COMMIT;