# prod_redeploy.sh

Production redeploy script for **code updates** on an existing EC2 instance. Skips certificate renewal and uses the existing venv.

## What It Does

1. **Creates `.env`** if missing (same defaults as prod_deploy).

2. **Installs/ensures PostgreSQL** and applies the same local Postgres setup as prod_deploy:
   - pg_hba fix (ident → md5 for localhost)
   - `postgres` password set to `postgres`
   - `.env` DB_PASSWORD fix if empty
   - Runs `db/setup_postgres.sh` only if the `mirrulations` database doesn't exist

3. **Installs Node.js** if missing.

4. **Creates venv** only if it doesn't exist; always runs `pip install -e .` and `pip install -r requirements.txt`.

5. **Builds the frontend** (`npm install` and `npm run build`).

6. **Stops mirrsearch**, copies the systemd service, and runs `prod_up.sh` to start it.

## What It Skips (vs prod_deploy)

- **Certbot** – does not run `certbot certonly` (assumes certificates already exist)
- **Certbot symlink** – does not update `/usr/bin/certbot`

## Usage

```bash
cd mirrulations-search
git pull
./prod_redeploy.sh
```

## When to Use

- Pushing code changes to production
- Updating dependencies (requirements.txt, package.json)
- Redeploying after schema or config changes

## Prerequisites

- Repository already cloned
- `.venv` and certs from a previous `prod_deploy.sh` run
- `DB_HOST=localhost` in `.env` for local Postgres

## Related

- `prod_deploy.sh` – full initial deploy
- `prod_up.sh` – restart service only
