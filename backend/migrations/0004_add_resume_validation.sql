-- Add validation and authenticity tracking columns to resumes table
ALTER TABLE resumes 
ADD COLUMN IF NOT EXISTS validation_status VARCHAR(50) DEFAULT 'PENDING',  -- PENDING, PASSED, FAILED, SUSPICIOUS
ADD COLUMN IF NOT EXISTS validation_warnings JSONB DEFAULT NULL,  -- JSON array of validation warnings
ADD COLUMN IF NOT EXISTS is_ai_generated BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS ai_suspicion_reasons JSONB DEFAULT NULL,  -- JSON array of AI detection reasons
ADD COLUMN IF NOT EXISTS authenticity_score NUMERIC(3,2) DEFAULT 1.0;  -- 0.0 to 1.0, where 1.0 is most authentic
