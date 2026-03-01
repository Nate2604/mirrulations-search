# db/setup_postgres.sh

Database setup script that creates and initializes the `mirrulations` PostgreSQL database. Works on **Mac (Homebrew)** and **Linux (systemd)**.

## What It Does

1. **Starts Postgres**:
   - Mac: `brew services start postgresql`
   - Linux: `systemctl start postgresql` (or postgresql-14/15/16/17)

2. **On Linux only** – configures auth so the app can connect:
   - Switches pg_hba localhost (127.0.0.1 and ::1) from `ident` to `md5`
   - Sets the `postgres` user password to `postgres`

3. **Drops** the `mirrulations` database if it exists.

4. **Creates** the `mirrulations` database.

5. **Applies the schema** from `db/schema-postgres.sql` (creates `dockets`, `documents`, `cfrparts` tables).

6. **Inserts seed data** – one sample document (CMS-2025-0242) for testing search.

## Platform Behavior

| Platform          | Postgres start                   | DB commands run as |
| ----------------- | -------------------------------- | ------------------ |
| Mac (brew)        | `brew services start postgresql` | Current user       |
| Linux (systemctl) | `systemctl start postgresql*`    | `sudo -u postgres` |

On Linux, `run_pg()` runs commands as the `postgres` system user because the default install only grants that user DB privileges. On Mac, Homebrew gives the current user a Postgres role.

## Usage

Run from the **project root**:

```bash
./db/setup_postgres.sh
```

Or from `db/`:

```bash
cd db
./setup_postgres.sh
```

The script resolves paths correctly from either location.

## When It Runs

- **prod_deploy.sh** / **prod_redeploy.sh** call it automatically when the `mirrulations` database doesn't exist.
- **dev_up.sh** calls it when `psql -lqt postgres` shows no `mirrulations` database.

## Important

⚠️ **Drops the database** – all existing data is removed. For production, the script should be updated to avoid dropping when the DB is already in use.

## Connect After Setup

```bash
psql mirrulations
# or with password (Linux):
PGPASSWORD=postgres psql -h localhost -U postgres mirrulations
```

## Related

- `db/schema-postgres.sql` – table definitions
- `prod_deploy.sh` – invokes this script when DB is missing
- `dev_up.sh` – invokes this script when DB is missing (dev)
