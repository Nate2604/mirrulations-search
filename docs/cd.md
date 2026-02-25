# Continuous Deployment

Deployments to the EC2 instance are handled automatically by the **Deploy to EC2** workflow (`.github/workflows/deploy.yml`).

## Trigger

The workflow runs when the **Unit Tests** workflow completes successfully on `main`. It can also be triggered manually via **Actions → Deploy to EC2 → Run workflow** (`workflow_dispatch`).

## Required Secrets

Configure these under **Settings → Secrets and variables → Actions** (and in the `development` environment if you use environment-specific secrets):

| Secret        | Description                               |
| ------------- | ----------------------------------------- |
| `EC2_HOST`    | The EC2 instance’s hostname or IP address |
| `EC2_USER`    | The SSH username                          |
| `EC2_SSH_KEY` | The private SSH key for that user         |

## What the Workflow Does

1. **Verify Static Analysis passed** (skipped on manual runs)  
   Uses the GitHub API to confirm the **Static Analysis** workflow also succeeded for the same commit. If it hasn’t or didn’t run, the job fails and no deploy happens.

2. **SSH into EC2 and redeploy**  
   Uses `appleboy/ssh-action` to connect to the server with the above secrets and run:
   - `cd /home/ec2-user/mirrulations-search`
   - `git fetch origin main` then `git reset --hard origin/main`
   - `./prod_redeploy.sh` — which installs Node if missing, installs pip deps, builds the frontend, and restarts the `mirrsearch` systemd service
