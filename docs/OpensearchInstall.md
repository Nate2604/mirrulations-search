# OpenSearch Installation and Launch Guide

This doc shows two ways to run OpenSearch locally:
- Docker (recommended)
- Homebrew (macOS)

Pick one; you do not need both.

## Option A: Docker (recommended)

Start OpenSearch in Docker:

```bash
docker run -d --name opensearch \
  -p 9200:9200 -p 9600:9600 \
  -e "discovery.type=single-node" \
  -e "plugins.security.disabled=true" \
  opensearchproject/opensearch:2.11.0
```

Verify OpenSearch is running (should return JSON output):

```bash
curl -X GET "http://localhost:9200/"
```

Stop and remove the container when finished:

```bash
docker stop opensearch
docker rm opensearch
```

## Option B: Homebrew (macOS)

Install and run OpenSearch:

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
