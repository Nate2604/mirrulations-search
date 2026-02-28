#!/bin/bash

DB_NAME="mirrulations"

# Start Postgres (Mac/Homebrew vs Linux/systemctl)
if command -v brew &>/dev/null; then
    brew services start postgresql
    run_pg() { "$@"; }
elif command -v systemctl &>/dev/null; then
    for svc in postgresql postgresql-14 postgresql-15 postgresql-16 postgresql-17; do
        sudo systemctl start "$svc" 2>/dev/null && break
    done
    run_pg() { sudo -u postgres "$@"; }
    PGDATA=$(sudo -u postgres psql -t -A -c "SHOW data_directory" 2>/dev/null | tr -d '[:space:]')
    PGHBA="${PGDATA}/pg_hba.conf"
    if [[ -n "$PGHBA" && -f "$PGHBA" ]]; then
        if grep -q "127.0.0.1/32.*ident" "$PGHBA" 2>/dev/null; then
            sudo sed -i.bak '/127\.0\.0\.1\/32/s/ident$/md5/' "$PGHBA"
            grep -q "::1/128.*ident" "$PGHBA" 2>/dev/null && sudo sed -i.bak '/::1\/128/s/ident$/md5/' "$PGHBA" || true
            run_pg psql -c "ALTER USER postgres PASSWORD 'postgres';" 2>/dev/null || true
            for svc in postgresql postgresql-14 postgresql-15 postgresql-16 postgresql-17; do
                sudo systemctl reload "$svc" 2>/dev/null && break
            done
        fi
    fi
else
    run_pg() { "$@"; }
fi

# Paths: script lives in db/, schema is db/schema-postgres.sql
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"

#TODO: Change so database doesn't get dropped when prod ready.
# `run_pg` is a function that runs a command as the proper user on Linux, and as the current user on Mac.
echo "Dropping database if it exists..."
run_pg dropdb --if-exists $DB_NAME

echo "Creating database..."
run_pg createdb $DB_NAME

echo "Creating schema..."
run_pg psql -d $DB_NAME -f "$ROOT_DIR/db/schema-postgres.sql"

echo "Inserting seed data..."
run_pg psql $DB_NAME <<'EOF'

INSERT INTO documents (
    document_id,
    docket_id,
    document_api_link,
    agency_id,
    document_type,
    modify_date,
    posted_date,
    document_title,
    comment_start_date,
    comment_end_date
)
VALUES (
    'CMS-2025-0242-0001',
    'CMS-2025-0242',
    'https://api.regulations.gov/v4/documents/CMS-2025-0242-0001',
    'CMS',
    'Proposed Rule',
    '2025-02-12 11:20:00+00',
    '2025-02-10 10:15:00+00',
    'ESRD Treatment Choices Model Updates',
    '2025-03-01 00:00:00+00',
    '2025-05-01 00:00:00+00'
);

SELECT * FROM documents;

EOF

echo ""
echo "Database '$DB_NAME' is fully initialized."
echo "Connect with:"
echo "psql $DB_NAME"
