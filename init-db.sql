-- init-db.sql
-- Automatically executed on first PostgreSQL container startup
-- Creates separate databases for each microservice

-- ============================================================
-- Database for AUTH SERVICE (optional - currently uses SQLite)
-- ============================================================
CREATE USER auth_user WITH PASSWORD 'auth_pass';
CREATE DATABASE triduel_auth OWNER auth_user;
GRANT ALL PRIVILEGES ON DATABASE triduel_auth TO auth_user;

-- PostgreSQL 15+ requires additional grant for public schema
\c triduel_auth
GRANT ALL ON SCHEMA public TO auth_user;

-- ============================================================
-- Database for PLAYER SERVICE
-- ============================================================
\c postgres
CREATE USER player_user WITH PASSWORD 'player_pass';
CREATE DATABASE triduel_player OWNER player_user;
GRANT ALL PRIVILEGES ON DATABASE triduel_player TO player_user;

\c triduel_player
GRANT ALL ON SCHEMA public TO player_user;

-- ============================================================
-- Database for GAME SERVICE
-- ============================================================
\c postgres
CREATE USER game_user WITH PASSWORD 'game_pass';
CREATE DATABASE triduel_game OWNER game_user;
GRANT ALL PRIVILEGES ON DATABASE triduel_game TO game_user;

\c triduel_game
GRANT ALL ON SCHEMA public TO game_user;

