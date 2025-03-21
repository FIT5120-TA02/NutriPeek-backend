# Database Migrations Guide

This guide explains how to run database migrations for both local and development environments.

## Prerequisites

- Python 3.9+
- PostgreSQL (local)
- Access to Supabase (development)
- Virtual environment activated

## Local Database Migrations

The local database migrations use Alembic with an async PostgreSQL driver (asyncpg).

### Setup Local Database

1. Make sure PostgreSQL is running locally
2. Create the database if it doesn't exist:

```bash
createdb onboarding_db_local
```

### Run Local Migrations

To apply migrations to your local database:

```bash
./scripts/apply_migrations.sh local
```

This script will:

1. Load environment variables from `env/local.env`
2. Set up the database connection
3. Run Alembic migrations

## Development Database Migrations (Supabase)

Due to potential network restrictions when connecting to Supabase from local machines, we provide two methods for applying migrations to the development database.

### Method 1: Using the Migration Script (Recommended)

If you have direct access to the Supabase database:

```bash
./scripts/apply_migrations.sh dev
```

### Method 2: Using SQL Script in Supabase SQL Editor

If Method 1 doesn't work due to network restrictions:

1. Log in to the Supabase dashboard
2. Navigate to the SQL Editor
3. Copy the contents of `scripts/supabase_migration.sql`
4. Paste and run the SQL in the Supabase SQL Editor

This SQL script:

- Creates all tables with proper snake_case naming
- Sets up appropriate indexes
- Establishes relationships between tables
- Updates the Alembic version tracking

## Creating New Migrations

When you make changes to the database models:

1. Update the model files in `src/app/models/`
2. Generate a new migration:

```bash
alembic revision --autogenerate -m "Description of changes"
```

3. Review the generated migration file in `migrations/versions/`
4. Apply the migration using one of the methods above

## Troubleshooting

### Connection Issues with Supabase

If you encounter connection issues with Supabase:

- Verify your DATABASE_URL in `env/dev.env`
- Check if your network allows connections to Supabase
- Try using Method 2 (SQL script) instead

### Migration Conflicts

If you encounter conflicts between migrations:

- Check the `alembic_version` table in your database
- Ensure you're running migrations in the correct order
- Consider resetting the database if in development

## Best Practices

- Always back up your database before running migrations
- Test migrations in a local environment before applying to development
- Keep migration descriptions clear and specific
- Review auto-generated migrations before applying them
