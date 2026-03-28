-- Migration: Add resume traceability to derived data
-- Purpose: Track which resume each parsed skill/experience/education came from
-- This enables cascade deletion of derived data when a resume is deleted

-- Migrate candidate_skills table
ALTER TABLE candidate_skills 
ADD COLUMN resume_id UUID NULL REFERENCES resumes(id) ON DELETE CASCADE;

ALTER TABLE candidate_skills 
ADD COLUMN is_derived_from_resume BOOLEAN NOT NULL DEFAULT false;

CREATE INDEX idx_candidate_skills_resume_id ON candidate_skills(resume_id);
CREATE INDEX idx_candidate_skills_is_derived ON candidate_skills(is_derived_from_resume);

-- Migrate experiences table
ALTER TABLE experiences 
ADD COLUMN resume_id UUID NULL REFERENCES resumes(id) ON DELETE CASCADE;

ALTER TABLE experiences 
ADD COLUMN is_derived_from_resume BOOLEAN NOT NULL DEFAULT false;

CREATE INDEX idx_experiences_resume_id ON experiences(resume_id);
CREATE INDEX idx_experiences_is_derived ON experiences(is_derived_from_resume);

-- Migrate educations table
ALTER TABLE educations 
ADD COLUMN resume_id UUID NULL REFERENCES resumes(id) ON DELETE CASCADE;

ALTER TABLE educations 
ADD COLUMN is_derived_from_resume BOOLEAN NOT NULL DEFAULT false;

CREATE INDEX idx_educations_resume_id ON educations(resume_id);
CREATE INDEX idx_educations_is_derived ON educations(is_derived_from_resume);

-- Track migration completion
COMMENT ON COLUMN candidate_skills.resume_id IS 'Foreign key to resume this skill was derived from';
COMMENT ON COLUMN candidate_skills.is_derived_from_resume IS 'True if this skill was auto-extracted from resume parsing';
COMMENT ON COLUMN experiences.resume_id IS 'Foreign key to resume this experience was derived from';
COMMENT ON COLUMN experiences.is_derived_from_resume IS 'True if this experience was auto-extracted from resume parsing';
COMMENT ON COLUMN educations.resume_id IS 'Foreign key to resume this education was derived from';
COMMENT ON COLUMN educations.is_derived_from_resume IS 'True if this education was auto-extracted from resume parsing';
