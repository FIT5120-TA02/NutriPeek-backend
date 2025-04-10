# Database Migrations Guide

This guide explains how to apply database migrations in the NutriPeek project.

## Prerequisites

- Python 3.9+
- PostgreSQL (local)
- Access to Supabase (development)
- Virtual environment activated

## Standard Migration Workflow

### Step 1: Create or Update Models

First, create or update your SQLAlchemy models in the `src/app/models/` directory.

Ensure that:
- Models inherit from `Base` and relevant mixins (`UUIDMixin`, `TimestampMixin`)
- All relationships are properly defined
- The models are imported in `src/app/models/__init__.py`
- The models are imported in `src/app/core/db/base.py`

### Step 2: Generate Migration

Once your models are ready, generate a migration file:

```bash
# Activate virtual environment (if not already activated)
source venv/bin/activate

# Set Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Generate migration
alembic revision --autogenerate -m "Description of your changes"
```

This will create a new migration file in the `migrations/versions/` directory.

### Step 3: Review the Migration

Review the generated migration file to ensure it correctly captures your changes:

```bash
# Find the latest migration file
ls -la migrations/versions/
```

Open the latest file and check that:
- Tables are created/altered as expected
- Columns have the correct types and constraints
- Indexes and relationships are properly set up

### Step 4: Apply the Migration

Apply the migration to your database:

```bash
# For local database
export ENVIRONMENT=local
export ENV_FILE=./env/local.env
export $(grep -v '^#' $ENV_FILE | xargs)
alembic upgrade head

# For development database
export ENVIRONMENT=dev
export ENV_FILE=./env/dev.env
export $(grep -v '^#' $ENV_FILE | xargs)
alembic upgrade head
```

Alternatively, use the provided scripts:

```bash
# For local database
./scripts/shell/apply_migrations.sh local

# For development database
./scripts/shell/apply_migrations.sh dev
```

### Step 5: Verify the Migration

Verify that the migration was applied successfully:

```bash
# Check the current migration version
alembic current

# Check migration history
alembic history --verbose
```

You can also connect to the database and verify that the tables were created correctly.

## Common Migration Commands

### Check Current Version

```bash
alembic current
```

### Generate Migration Without Auto-Detection

```bash
alembic revision -m "Description of your changes"
```

### Apply Specific Migration

```bash
alembic upgrade <revision>
```

### Downgrade Migration

```bash
# Downgrade one revision
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision>

# Downgrade to base (before any migrations)
alembic downgrade base
```

### Generate SQL Script

```bash
# Generate SQL for the next migration
alembic upgrade head --sql > migration.sql
```

## Troubleshooting

### Auto-Generated Migrations Miss Changes

If the auto-generated migration doesn't include all your changes:

1. Make sure your models are imported in `src/app/core/db/base.py`
2. Check that your models are correctly inheriting from Base
3. Try clearing the Alembic version in your database and regenerating

### Connection Issues

If you're having trouble connecting to the database:

1. Check your connection string in the appropriate env file
2. Verify that the database exists and is accessible
3. Check for network issues, especially when connecting to Supabase

### Migration Conflicts

If you encounter conflicts between migrations:

1. Check the `alembic_version` table in your database
2. Ensure you're running migrations in the correct order
3. Consider starting with a fresh database if possible

## Best Practices

1. **Generate migrations for each logical change** - Don't combine unrelated model changes in a single migration
2. **Always review auto-generated migrations** - Alembic might not always capture all nuances of your changes
3. **Test migrations before applying to production** - Always run migrations in a test environment first
4. **Keep migrations small and focused** - This makes them easier to troubleshoot and roll back if needed
5. **Include meaningful descriptions** - Use clear, descriptive messages when generating migrations
6. **Version control your migrations** - Always commit migration files to your repository
7. **Document database changes** - Update README or documentation when making significant schema changes