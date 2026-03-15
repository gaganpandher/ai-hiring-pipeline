-- Ensure proper charset and collation
ALTER DATABASE hiring_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Source schema and seed (Docker runs all files in /docker-entrypoint-initdb.d alphabetically)
-- Files are: 01_schema.sql, 02_seed.sql — rename accordingly if needed

-- Read-only analytics user for BI tools / PyCharm Database window
CREATE USER IF NOT EXISTS 'analytics_ro'@'%' IDENTIFIED BY 'analytics_readonly_pass';
GRANT SELECT ON hiring_db.* TO 'analytics_ro'@'%';
FLUSH PRIVILEGES;
