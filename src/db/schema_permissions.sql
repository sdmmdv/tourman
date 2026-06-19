-- Allow app_admin to use and create in the project schema

GRANT USAGE ON SCHEMA public TO app_admin;
GRANT CREATE ON SCHEMA public TO app_admin;

GRANT USAGE ON SCHEMA public TO app_guest;
