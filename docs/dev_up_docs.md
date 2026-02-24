# How to Set up Developer Environment
Authors: Jeffery Eisenhardt, Cole Aydelotte, Collin Cabral-Castro.

# What this script does

dev_up.sh is a one-command development bootstrap script that automatically prepares and launches the application’s local runtime environment.

When executed, the script:

- Configures PYTHONPATH so the src/ module can be resolved
- Starts the application using Gunicorn with the project’s configuration

In short, it provisions the environment and launches the backend in one process.

# Why we need this

Setting up Python environments and starting services manually is repetitive and error-prone. Developers may forget steps, install packages globally, misconfigure paths, or start the server incorrectly.

This script exists to:
- Eliminate manual configuration mistakes
- Speed up onboarding and daily startup
- Provide a single, reliable command to run the app

By automating setup and execution, development becomes consistent, reproducible, and fast, allowing contributors to focus on building features rather than configuring tooling.

# Run the script
```bash
./dev_up.sh
```

You will see a message that says that Mirrulations Search has been started.

# How to turn off the project

To take down the project, you will have to run a different script, this would be dev_down.sh

## What does it do
Dev_down.sh removes the process that is running on port 80 using the PID file that is created by gunicorn.py.
It then will give you a message saying that Mirrulation Search is down
