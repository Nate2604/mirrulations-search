#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Install Postgres if missing (Mac/Homebrew)
if ! command -v psql &>/dev/null && command -v brew &>/dev/null; then
    echo "Installing PostgreSQL via Homebrew..."
    brew install postgresql
    brew services start postgresql
fi

# Setup Postgres DB if not already initialized
brew services start postgresql 2>/dev/null || true
if ! psql -lqt postgres 2>/dev/null | grep -qw mirrulations; then
    ./db/setup_postgres.sh
fi

# Build the React frontend
(cd frontend && npm install && npm run build)

# Load .env so Gunicorn (run via sudo) inherits USE_POSTGRES, DB_*, etc.
set -a
[[ -f .env ]] && source .env
set +a

# Stop existing Gunicorn if running (so we can start fresh)
if [[ -f gunicorn.pid ]]; then
    sudo kill -TERM "$(cat gunicorn.pid)" 2>/dev/null || true
    rm -f gunicorn.pid
fi

# Start the gunicorn server on port 80 using the configuration in conf/gunicorn.py
export PYTHONPATH="$PWD/src"
sudo -E OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES .venv/bin/gunicorn -c conf/gunicorn.py mirrsearch.app:app
echo "Mirrulations search has been started"
