set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIRRSEARCH_SERVICE="mirrsearch.service"
MIRRSEARCH_SERVICE_PATH="/etc/systemd/system/${MIRRSEARCH_SERVICE}"

DOMAIN="dev.mirrulations.org"

cd "${PROJECT_ROOT}"

# Load .env for DB_HOST check
[[ -f .env ]] && source .env
DB_HOST="${DB_HOST:-localhost}"

# Install Postgres client (always needed)
if ! command -v psql &>/dev/null; then
    sudo yum install -y postgresql
fi

# Local Postgres: install server, ensure running, setup DB if needed
if [[ "$DB_HOST" == "localhost" || "$DB_HOST" == "127.0.0.1" ]]; then
    sudo yum install -y postgresql-server postgresql
    sudo postgresql-setup initdb 2>/dev/null || sudo /usr/bin/postgresql-setup --initdb 2>/dev/null || true
    for svc in postgresql postgresql-15 postgresql-16 postgresql-17 postgresql15 postgresql16 postgresql17; do
        sudo systemctl start "$svc" 2>/dev/null && break
    done
    if ! psql -lqt postgres 2>/dev/null | grep -qw mirrulations; then
        ./db/setup_postgres.sh
    fi
fi

if ! command -v node &>/dev/null; then
    curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
    sudo yum install -y nodejs
fi

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
./.venv/bin/pip install -e .
./.venv/bin/pip install -r requirements.txt

(cd frontend && npm install && npm run build)

sudo systemctl stop mirrsearch 2>/dev/null || true

sudo cp "${PROJECT_ROOT}/${MIRRSEARCH_SERVICE}" "${MIRRSEARCH_SERVICE_PATH}"
sudo systemctl daemon-reload
./prod_up.sh