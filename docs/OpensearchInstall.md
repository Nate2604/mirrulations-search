# OpenSearch Installation and Launch Guide (macOS with Homebrew)

This short guide shows how to install and run OpenSearch using Homebrew
on macOS and how to verify it's running. The commands below are unchanged
— they're simply organized for clarity.

## Create a Python virtual environment

Before working with the project, you may want to create and activate a
Python virtual environment (optional):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Install and run OpenSearch

Install OpenSearch via Homebrew:

```bash
brew install opensearch
```

Start the OpenSearch service:

```bash
brew services start opensearch
```

Verify OpenSearch is running(Should return json output if working correctly):

```bash
curl -X GET "http://localhost:9200/"
```

Stop the OpenSearch service when finished:

```bash
brew services stop opensearch
```
