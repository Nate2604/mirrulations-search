# Continuous Deployment

Deployments to the EC2 instance are handled automatically by the **Deploy to EC2** workflow (`.github/workflows/deploy.yml`).

## Trigger

The workflow runs when the **Unit Tests** workflow completes successfully on `main`. It can also be triggered manually via `workflow_dispatch`.

## Checks

Before deploying, the workflow verifies that **Static Analysis** also passed for the same commit. This ensures both checks must succeed before any code reaches the server. Manual dispatches skip this check.

## Deploy Steps

1. SSHs into the EC2 instance using secrets (`EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY`)
2. Pulls the latest `main` branch (`git fetch` + `git reset --hard`)
3. Runs `./prod_redeploy.sh`, which:
   - Installs Node.js if missing
   - Creates a Python venv if missing, then installs pip dependencies
   - Builds the React frontend (`npm install && npm run build`)
   - Restarts the `mirrsearch` systemd service
