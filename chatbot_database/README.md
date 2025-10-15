# Chatbot Database (Postgres) - Local Development

A minimal Postgres service for local development using Docker Compose.

## Prerequisites
- Docker and Docker Compose installed

## Setup
1) Copy the example env file and adjust as needed:
   cp .env.example .env

2) Start the database container:
   docker compose up -d

This will start a Postgres 16 container listening on localhost:5432 with data persisted to a named volume `pgdata`.

## Connection Details
The backend can connect using a SQLAlchemy-compatible DATABASE_URL (psycopg2 driver):

postgresql+psycopg2://chat_user:chat_pass@localhost:5432/chat_db

Update the credentials and database name if you changed them in `.env`.

## Useful Commands
- Stop containers: 
  docker compose down

- Stop and remove persistent volume (destructive):
  docker compose down -v

- Tail logs:
  docker compose logs -f postgres

- psql connection example:
  psql "postgresql://chat_user:chat_pass@localhost:5432/chat_db"

## Notes
- Intended for local development only. Do not use the example credentials in production.
- Data is persisted via a named Docker volume `pgdata`.
