set -e
git clone https://github.com/mirrulations/mirrulations-fetch.git
cd mirrulations-fetch
python3 -m venv .venv
source .venv/bin/activate
pip install .