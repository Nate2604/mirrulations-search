from mirrsearch.db import get_db, get_opensearch_connection

INDEX_NAME = "docket-comments"
DOCKET_ID = "CMS-2025-0240"


def create_index_if_not_exists(client):
    if not client.indices.exists(index=INDEX_NAME):
        client.indices.create(index=INDEX_NAME)


def ingest_one_docket(docket_id: str):
    db = get_db()
    client = get_opensearch_connection()

    create_index_if_not_exists(client)

    # Search dummy DB for docket
    records = db.search(docket_id)

    for i, record in enumerate(records):
        doc_id = f"{docket_id}-{i}"

        client.index(
            index=INDEX_NAME,
            id=doc_id,
            body=record
        )

    print(f"Ingested {len(records)} records into OpenSearch.")


if __name__ == "__main__":
    ingest_one_docket(DOCKET_ID)
