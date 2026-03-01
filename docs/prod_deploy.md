# prod_deploy.sh

Full production deployment script for a **fresh** Amazon Linux EC2 instance. Use this for initial setup.

## What It Does

1. **Creates `.env`** if missing, with defaults for local Postgres (`USE_POSTGRES=1`, `DB_HOST=localhost`, `DB_NAME=mirrulations`, `DB_USER=postgres`, `DB_PASSWORD=postgres`).

2. **Installs PostgreSQL** (Amazon Linux 2: `amazon-linux-extras` + yum; Amazon Linux 2023: dnf).

3. **Configures local Postgres** when `DB_HOST` is localhost:
   - Initializes Postgres if needed
   - Starts the Postgres service
   - Fixes pg_hba: switches localhost auth from `ident` to `md5` so the app (running as root) can connect
   - Sets the `postgres` user password to `postgres`
   - Ensures `.env` has `DB_PASSWORD=postgres` if it was empty
   - Runs `db/setup_postgres.sh` if the `mirrulations` database doesn't exist

4. **Installs Node.js** (via NodeSource) if missing.

5. **Creates Python venv** and installs dependencies if `.venv` doesn't exist.

6. **Builds the frontend** (`npm install` and `npm run build`).

7. **Links certbot** to `/usr/bin/certbot`.

8. **Stops mirrsearch** if running.

9. **Obtains Let's Encrypt certificate** for `dev.mirrulations.org` (standalone mode; requires port 80 free).

10. **Copies the systemd service** and runs `prod_up.sh` to start mirrsearch.

## Prerequisites

- Amazon Linux 2 or 2023 EC2 instance
- Security group allows inbound 80 and 443
- `dev.mirrulations.org` DNS points to this instance's public IP
- Port 80 not in use (certbot standalone needs it temporarily)

## Usage

```bash
cd mirrulations-search
chmod +x prod_deploy.sh
./prod_deploy.sh
```

## When to Use

- First deployment on a new server
- After cloning the repo on fresh EC2

## Related

- `prod_redeploy.sh` – for code updates (skips certbot, venv creation)
- `prod_up.sh` – restarts the systemd service only
