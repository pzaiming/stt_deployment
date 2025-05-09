-- =============================================================================
-- DROP EXISTING TABLES
-- =============================================================================
-- This section ensures that any existing tables named 'user_data' and 'keywords'
-- are removed before creating new ones. This helps in avoiding conflicts or
-- duplication when running the script multiple times.
-- =============================================================================
-- DROP TABLE IF EXISTS user_data;
-- DROP TABLE IF EXISTS keywords;
-- =============================================================================
-- CREATE TABLES
-- =============================================================================
-- This section creates two tables: 'user_data' and 'keywords' in the 'public'
-- schema. The 'user_data' table stores information related to user interactions,
-- while the 'keywords' table holds keywords associated with different services
-- and users.
-- =============================================================================
-- Create user_data table
CREATE TABLE IF NOT EXISTS public.user_data (
    circuit TEXT,
    audio_file_path TEXT,
    file_name TEXT,
    duration TEXT,
    stt_transcript TEXT,
    gt_transcript TEXT,
    operator_remark TEXT,
    start_time TIMESTAMP,
    start_year INT,
    start_month INT,
    start_day INT,
    start_hour INT,
    start_minute INT,
    start_second INT,
    last_modified TIMESTAMP,
    created TIMESTAMP,
    src TEXT,
    dst TEXT,
    bookmark TEXT,
    mplan TEXT,
    created_by TEXT,
    stereo BOOLEAN DEFAULT FALSE,
    PRIMARY KEY(circuit, start_time, file_name, created_by)
);

-- Create keywords table
CREATE TABLE IF NOT EXISTS public.keywords (
    keyword TEXT,
    priority_ INT,
    service_ TEXT,
    created_by TEXT,
    PRIMARY KEY(keyword, priority_, service_, created_by)
);

-- =============================================================================
-- CREATE USERS AND SCHEMAS
-- =============================================================================
-- This section creates user roles ('user1' and 'user2') with login capabilities
-- and assigns them to their respective schemas. It also sets up privileges to
-- ensure that each user has appropriate access to their own schema while
-- restricting access from the PUBLIC.
-- =============================================================================
-- Sample users
DO $$ BEGIN -- Create roles for normal users
IF NOT EXISTS (
    SELECT
    FROM
        pg_catalog.pg_roles
    WHERE
        rolname = 'user1'
) THEN CREATE ROLE user1 WITH LOGIN PASSWORD 'userpassword';

END IF;

IF NOT EXISTS (
    SELECT
    FROM
        pg_catalog.pg_roles
    WHERE
        rolname = 'user2'
) THEN CREATE ROLE user2 WITH LOGIN PASSWORD 'userpassword';

END IF;

END $$;

-- Create schemas for each user and set ownership
CREATE SCHEMA IF NOT EXISTS user1 AUTHORIZATION user1;
CREATE SCHEMA IF NOT EXISTS user2 AUTHORIZATION user2;

-- Grant necessary privileges on schemas
GRANT ALL ON SCHEMA user1 TO user1;
GRANT ALL ON SCHEMA user2 TO user2;

-- Revoke all privileges on user schemas from PUBLIC
REVOKE ALL ON SCHEMA user1
FROM
    PUBLIC;

REVOKE ALL ON SCHEMA user2
FROM
    PUBLIC;

-- Set default search_path for each user
ALTER ROLE user1
SET
    search_path = user1,
    public;

ALTER ROLE user2
SET
    search_path = user2,
    public;

-- =============================================================================
-- CREATE PRIVATE TABLES
-- =============================================================================
-- This section creates private tables for 'user1' and 'user2' within their
-- respective schemas. These tables are intended to store user-specific private
-- data that should not be accessible to other users.
-- =============================================================================
SET
    ROLE user1;

-- Create user1_private_table in user1 schema
CREATE TABLE IF NOT EXISTS user1.user1_private_table (
    private_id SERIAL PRIMARY KEY,
    private_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

RESET ROLE;

SET
    ROLE user2;

-- Create user2_private_table in user2 schema
CREATE TABLE IF NOT EXISTS user2.user2_private_table (
    private_id SERIAL PRIMARY KEY,
    private_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

RESET ROLE;

-- =============================================================================
-- INSERT SAMPLE DATA
-- =============================================================================
-- This section inserts sample data into the 'user_data' and 'keywords' tables.
-- The 'ON CONFLICT DO NOTHING' clause ensures that duplicate entries based on
-- the primary key are ignored, preventing insertion errors.
-- =============================================================================
-- Sample data for user_data table
INSERT INTO
    public.user_data (
        circuit,
        audio_file_path,
        file_name,
        duration,
        stt_transcript,
        gt_transcript,
        operator_remark,
        start_time,
        start_year,
        start_month,
        start_day,
        start_hour,
        start_minute,
        start_second,
        last_modified,
        created,
        src,
        dst,
        bookmark,
        mplan,
        created_by,
        stereo
    )
VALUES
    (
        'circuit_1',
        '/audio/next.wav',
        'next.wav',
        '00:03:20',
        'B 0.00 1.27 This is a sample STT transcript. urgent.
        B 1.28 2.45 This is another line',
        'B 0.00 1.27 This is a sample GT transcript. urgent.
        B 1.28 2.45 This is another line',
        'Sample operator remark',
        '2017-01-05 17:52:30',
        2017,
        1,
        5,
        17,
        52,
        30,
        '2017-01-05 17:55:00',
        '2017-01-05 17:55:00',
        'SRC1',
        'DST1',
        'True',
        'True',
        'user1',
        FALSE
    ),
    (
        'circuit_2',
        '/audio/path/back.wav',
        'back.wav',
        '00:02:45',
        'L 0.00 1.27 This is a sample STT transcript. urgent.
        R 0.50 2.45 This is another line',
        'L 0.00 1.27 This is a sample GT transcript. urgent.
        R 0.50 2.45 This is another line',
        'Another operator remark',
        '2018-02-10 14:22:15',
        2018,
        2,
        10,
        14,
        22,
        15,
        '2018-02-10 14:30:00',
        '2018-02-10 14:30:00',
        'SRC2',
        'DST2',
        'False',
        'False',
        'user2',
        TRUE
    ) ON CONFLICT (circuit, start_time, file_name, created_by) DO NOTHING;

-- Sample data for keywords table
INSERT INTO
    public.keywords (keyword, priority_, service_, created_by)
VALUES
    ('urgent', 1, 'service_a', 'user1'),
    ('routine', 2, 'service_b', 'user1'),
    ('emergency', 1, 'service_c', 'user2'),
    ('urgent', 1, 'service_a', 'user2'),
    ('routine', 2, 'service_b', 'user2') ON CONFLICT (keyword, priority_, service_, created_by) DO NOTHING;

SET
    ROLE user1;

-- Sample data for user1_private_table
INSERT INTO
    user1.user1_private_table (private_data)
VALUES
    ('User1 Private Data 1'),
    ('User1 Private Data 2') ON CONFLICT DO NOTHING;

RESET ROLE;

SET
    ROLE user2;

-- Sample data for user2_private_table
INSERT INTO
    user2.user2_private_table (private_data)
VALUES
    ('User2 Private Data 1'),
    ('User2 Private Data 2') ON CONFLICT DO NOTHING;

RESET ROLE;

-- =============================================================================
-- GRANT PRIVILEGES ON PUBLIC SCHEMA
-- =============================================================================
-- This section manages access to the 'public' schema by revoking creation
-- privileges from PUBLIC, granting usage and select permissions, and setting
-- default privileges for future tables.
-- =============================================================================
-- Grant USAGE and SELECT on public schema
REVOKE CREATE ON SCHEMA public
FROM
    PUBLIC;

GRANT USAGE ON SCHEMA public TO PUBLIC;

GRANT
SELECT
    ON ALL TABLES IN SCHEMA public TO PUBLIC;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT
SELECT
    ON TABLES TO PUBLIC;

-- =============================================================================
-- GRANT DATA MANIPULATION PRIVILEGES TO USERS
-- =============================================================================
-- Grants INSERT, UPDATE, and DELETE permissions on the 'user_data' and
-- 'keywords' tables to specified users ('user1', 'user2', 'user3'). This
-- allows these users to modify data within these tables as needed.
-- =============================================================================
-- Grant INSERT, UPDATE, DELETE on public tables to normal users
GRANT
INSERT
,
UPDATE
,
    DELETE ON TABLE public.user_data TO user1,
    user2;

GRANT
INSERT
,
UPDATE
,
    DELETE ON TABLE public.keywords TO user1,
    user2;

-- =============================================================================
-- ENABLE ROW LEVEL SECURITY (RLS) AND CREATE POLICIES
-- =============================================================================
-- This section enables Row Level Security on the 'user_data' and 'keywords'
-- tables and defines policies to control access based on the 'created_by'
-- field. Only the user who created a row can SELECT, INSERT, UPDATE, or DELETE
-- it.
-- =============================================================================
-- Enable RLS on user_data table
ALTER TABLE
    public.user_data ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for user_data
DROP POLICY IF EXISTS select_user_data_policy ON public.user_data;

CREATE POLICY select_user_data_policy ON public.user_data FOR
SELECT
    USING (lower(created_by) = lower(current_user));

DROP POLICY IF EXISTS insert_user_data_policy ON public.user_data;

CREATE POLICY insert_user_data_policy ON public.user_data FOR
INSERT
    WITH CHECK (lower(created_by) = lower(current_user));

DROP POLICY IF EXISTS update_user_data_policy ON public.user_data;

CREATE POLICY update_user_data_policy ON public.user_data FOR
UPDATE
    USING (lower(created_by) = lower(current_user));

DROP POLICY IF EXISTS delete_user_data_policy ON public.user_data;

CREATE POLICY delete_user_data_policy ON public.user_data FOR DELETE USING (lower(created_by) = lower(current_user));

-- Enable RLS on keywords table
ALTER TABLE
    public.keywords ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for keywords
DROP POLICY IF EXISTS select_keywords_policy ON public.keywords;

CREATE POLICY select_keywords_policy ON public.keywords FOR
SELECT
    USING (lower(created_by) = lower(current_user));

DROP POLICY IF EXISTS insert_keywords_policy ON public.keywords;

CREATE POLICY insert_keywords_policy ON public.keywords FOR
INSERT
    WITH CHECK (lower(created_by) = lower(current_user));

DROP POLICY IF EXISTS update_keywords_policy ON public.keywords;

CREATE POLICY update_keywords_policy ON public.keywords FOR
UPDATE
    USING (lower(created_by) = lower(current_user));

DROP POLICY IF EXISTS delete_keywords_policy ON public.keywords;

CREATE POLICY delete_keywords_policy ON public.keywords FOR DELETE USING (lower(created_by) = lower(current_user));

-- =============================================================================
-- FINAL GRANT STATEMENTS AND COMMIT
-- =============================================================================
-- These final statements ensure that all users have the necessary usage and
-- select permissions on the 'public' schema and its tables. The COMMIT
-- statement finalizes all the changes made in this script.
-- =============================================================================
-- Grant USAGE on public schema to PUBLIC
GRANT USAGE ON SCHEMA public TO PUBLIC;

-- Grant SELECT on all existing tables in public schema to PUBLIC
GRANT
SELECT
    ON ALL TABLES IN SCHEMA public TO PUBLIC;

-- Set default privileges for future tables in public schema
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT
SELECT
    ON TABLES TO PUBLIC;

-- Finalize all changes
COMMIT;