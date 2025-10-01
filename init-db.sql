-- Create the database user
CREATE USER ipo_user WITH PASSWORD 'ipo_password';

-- Grant necessary permissions
ALTER USER ipo_user CREATEDB;

-- Create the database
CREATE DATABASE ipo_reminder;

-- Grant all privileges to the user
GRANT ALL PRIVILEGES ON DATABASE ipo_reminder TO ipo_user;

-- Connect to the database
\c ipo_reminder

-- Create necessary extensions if needed
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
