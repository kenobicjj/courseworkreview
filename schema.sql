-- Table: criteria
CREATE TABLE criteria (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    text TEXT NOT NULL,
    file_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: submission
CREATE TABLE submission (
    id SERIAL PRIMARY KEY,
    folder_name TEXT NOT NULL,
    notebook_file TEXT,
    file_path TEXT,
    notebook_content JSONB,
    feedback TEXT,
    analyzed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: submission_file
CREATE TABLE submission_file (
    id SERIAL PRIMARY KEY,
    submission_id INTEGER NOT NULL REFERENCES submission(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: analysis_settings
CREATE TABLE analysis_settings (
    id SERIAL PRIMARY KEY,
    preamble TEXT,
    postamble TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trigger function to auto-update updated_at fields
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to relevant tables
CREATE TRIGGER trigger_set_submission_updated_at
BEFORE UPDATE ON submission
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trigger_set_analysis_settings_updated_at
BEFORE UPDATE ON analysis_settings
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
