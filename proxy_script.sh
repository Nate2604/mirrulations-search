#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

brew install postgresql@14 || true
brew services start postgresql@14

sleep 3

export PATH="$(brew --prefix postgresql@14)/bin:$PATH"
./db/setup_postgres.sh

cat > .env << ENVEOF
USE_POSTGRES=1
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mirrulations
DB_USER=$(whoami)
DB_PASSWORD=
ENVEOF

./dev_up.sh
