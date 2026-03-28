-- Migration: Add is_active column to resumes table
-- Purpose: Enable resume versioning - only active resume data shown to user

-- Add is_active column with default value and index
ALTER TABLE resumes 
ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL;

-- Create index for efficient filtering of active resumes
CREATE INDEX idx_resumes_is_active ON resumes(is_active);

-- Create compound index for efficient user-level active resume queries
CREATE INDEX idx_resumes_user_is_active ON resumes(user_id, is_active);
