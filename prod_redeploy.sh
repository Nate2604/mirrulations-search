set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIRRSEARCH_SERVICE="mirrsearch.service"
MIRRSEARCH_SERVICE_PATH="/etc/systemd/system/${MIRRSEARCH_SERVICE}"

DOMAIN="dev.mirrulations.org"

cd "${PROJECT_ROOT}"

# Create .env if missing
if [[ ! -f .env ]]; then
    cat > .env <<'ENVEOF'
USE_POSTGRES=1
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mirrulations
DB_USER=postgres
DB_PASSWORD=
ENVEOF
    echo "Created .env with defaults (edit for RDS or custom credentials)"
fi

# Load .env for DB_HOST check
[[ -f .env ]] && source .env
DB_HOST="${DB_HOST:-localhost}"

# Install Postgres (AL2: amazon-linux-extras + yum; AL2023: dnf)
if ! command -v psql &>/dev/null || [[ "$DB_HOST" == "localhost" || "$DB_HOST" == "127.0.0.1" ]]; then
    if command -v amazon-linux-extras &>/dev/null; then
        sudo amazon-linux-extras enable postgresql14
        sudo yum install -y postgresql-server postgresql
    else
        sudo dnf install -y postgresql15 postgresql15-server
    fi
fi

# Local Postgres: ensure running, setup DB if needed
if [[ "$DB_HOST" == "localhost" || "$DB_HOST" == "127.0.0.1" ]]; then
    sudo postgresql-setup --initdb 2>/dev/null || sudo postgresql-setup initdb 2>/dev/null || true
    for svc in postgresql postgresql-14 postgresql-15 postgresql-16 postgresql-17; do
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