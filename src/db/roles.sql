-- #############################################################################################
-- ###################### MUST BE EXECUTED BY SUPER USER #######################################
-- #############################################################################################

-- Admin with full control
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_admin') THEN
       CREATE ROLE app_admin WITH LOGIN PASSWORD 'admin_secure_pass' CREATEDB CREATEROLE;
   END IF;
END
$$;

-- Guest with read-only
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_guest') THEN
       CREATE ROLE app_guest WITH LOGIN PASSWORD 'guest_pass';
   END IF;
END
$$;

-- Database
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'tournament') THEN
       CREATE DATABASE tournament;
   END IF;
END
$$;

-- #############################################################################################
-- #############################################################################################
-- #############################################################################################