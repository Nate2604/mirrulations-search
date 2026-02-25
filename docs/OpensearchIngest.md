# How to Ingest Dummy Data into OpenSearch Database

This guide explains how to:
- Create and Activate a virtual environment
- Ingest dummy data
- Verify indexed data

Create/Activate Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

1. Run OpenSearch Locally

Follow `docs/OpensearchInstall.md` to start OpenSearch, then continue here.

2. Ingest Dummy Data

```bash
python db/ingest_docket.py
```

If successful, the script will print:
Ingested X records into OpenSearch.

3. Verify Indexed Data

```bash
curl -X GET "localhost:9200/docket-comments/_search?pretty"
```
If the ingest worked correctly, this command will return JSON containing the indexed documents.

Stop OpenSearch
```bash
brew services stop opensearch
```

If you used Docker instead:
```bash
docker stop opensearch
docker rm opensearch
```
