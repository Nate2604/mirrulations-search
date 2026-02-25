#!/bin/bash
set -euo pipefail

# Build the React frontend
(cd frontend && npm install && npm run build)

# Start the gunicorn server on port 80 using the configuration in conf/gunicorn.py
export PYTHONPATH="$PWD/src"
sudo OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES .venv/bin/gunicorn -c conf/gunicorn.py mirrsearch.app:app
echo "Mirrulations search has been started"
