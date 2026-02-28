#!/bin/bash

DB_NAME="mirrulations"

# Start Postgres (Mac/Homebrew vs Linux/systemctl)
if command -v brew &>/dev/null; then
    brew services start postgresql
    run_pg() { "$@"; }
elif command -v systemctl &>/dev/null; then
    for svc in postgresql postgresql-15 postgresql-16 postgresql-17 postgresql15 postgresql16 postgresql17; do
        sudo systemctl start "$svc" 2>/dev/null && break
    done
    run_pg() { sudo -u postgres "$@"; }
else
    run_pg() { "$@"; }
fi

# Paths: script lives in db/, schema is db/schema-postgres.sql
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"

#TODO: Change so database doesn't get dropped when prod ready.

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
