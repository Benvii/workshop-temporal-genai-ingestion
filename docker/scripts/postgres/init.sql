CREATE EXTENSION IF NOT EXISTS vector;

-- Create the temporal database
CREATE DATABASE temporal;

-- Create the temporal user with the specified password
CREATE USER temporal WITH ENCRYPTED PASSWORD 'temporal';

-- Grant all privileges on the temporal database to the langfuse user
GRANT ALL PRIVILEGES ON DATABASE temporal TO temporal;

-- Connect to the temporal database
\c temporal

-- Grant usage and all privileges on the public schema to the langfuse user
GRANT ALL PRIVILEGES ON SCHEMA public TO temporal;

-- Alter default privileges for tables created in the public schema
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO temporal;

-- Create the langfuse database
CREATE DATABASE langfuse;

-- Create the langfuse user with the specified password
CREATE USER langfuse WITH ENCRYPTED PASSWORD 'langfuse';

-- Grant all privileges on the langfuse database to the langfuse user
GRANT ALL PRIVILEGES ON DATABASE langfuse TO langfuse;

-- Connect to the langfuse database
\c langfuse;

-- Grant usage and all privileges on the public schema to the langfuse user
GRANT ALL PRIVILEGES ON SCHEMA public TO langfuse;

-- Alter default privileges for tables created in the public schema
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO langfuse;

\! touch /var/lib/postgresql/data/db_init_completed