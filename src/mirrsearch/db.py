from dataclasses import dataclass
from typing import List, Dict, Any
import os
import json
import psycopg2

try:
    import boto3
except ImportError:
    boto3 = None

try:
    from dotenv import load_dotenv
except ImportError:
    LOAD_DOTENV = None
else:
    LOAD_DOTENV = load_dotenv


DUMMY_DATA = [
    {
        "docket_id": "CMS-2025-0242",
        "title": "ESRD Prospective Payment System Proposed Rule",
        "cfrPart": "42",
        "agency_id": "CMS",
        "document_type": "Proposed Rule",
    },
    {
        "docket_id": "CMS-2025-0242",
        "title": "End-Stage Renal Disease Treatment Standards Update",
        "cfrPart": "42",
        "agency_id": "CMS",
        "document_type": "Proposed Rule",
    },
    {
        "docket_id": "CMS-2025-0243",
        "title": "ESRD Quality Incentive Program for Renal Care",
        "cfrPart": "42",
        "agency_id": "CMS",
        "document_type": "Proposed Rule",
    },
    {
        "docket_id": "CMS-2025-0244",
        "title": "Renal Disease Management and Payment Reform",
        "cfrPart": "42",
        "agency_id": "CMS",
        "document_type": "Proposed Rule",
    },
]


@dataclass(frozen=True)
class DummyDBLayer:
    def search(self, query: str, filter_param: str = None) -> List[Dict[str, Any]]:
        q = (query or "").strip().lower()
        results = [
            item for item in DUMMY_DATA
            if q in item["docket_id"].lower()
            or q in item["title"].lower()
            or q in item["agency_id"].lower()
        ]
        if filter_param:
            results = [
                item for item in results
                if item["document_type"].lower() == filter_param.lower()
            ]
        return results


@dataclass(frozen=True)
class DBLayer:
    conn: Any = None

    def search(self, query: str, filter_param: str = None) -> List[Dict[str, Any]]:
        if self.conn is None:
            raise RuntimeError("No database connection available.")

        q = (query or "").strip()
        sql = """
            SELECT docket_id, document_title, agency_id, document_type
            FROM documents
            WHERE (docket_id ILIKE %s OR document_title ILIKE %s)
        """
        params = [f"%{q}%", f"%{q}%"] if q else ["%%", "%%"]
        if filter_param:
            sql += " AND document_type = %s"
            params.append(filter_param)

        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            return [
                {
                    "docket_id": row[0],
                    "title": row[1],
                    "cfrPart": None,
                    "agency_id": row[2],
                    "document_type": row[3],
                }
                for row in cur.fetchall()
            ]


def _get_secrets_from_aws() -> Dict[str, str]:
    if boto3 is None:
        raise ImportError("boto3 is required to use AWS Secrets Manager.")

    client = boto3.client(
        "secretsmanager",
        region_name="YOUR_REGION"
    )
    response = client.get_secret_value(
        SecretId="YOUR_SECRET_NAME"
    )
    return json.loads(response["SecretString"])


def get_postgres_connection() -> DBLayer:
    use_aws_secrets = os.getenv("USE_AWS_SECRETS", "").lower() in {"1", "true", "yes", "on"}

    if use_aws_secrets:
        creds = _get_secrets_from_aws()
        conn = psycopg2.connect(
            host=creds["host"],
            port=creds["port"],
            database=creds["db"],
            user=creds["username"],
            password=creds["password"]
        )
    else:
        if LOAD_DOTENV is not None:
            LOAD_DOTENV()
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )

    return DBLayer(conn)


def get_db():
    if LOAD_DOTENV is not None:
        LOAD_DOTENV()

    use_postgres = os.getenv("USE_POSTGRES", "").lower() in {"1", "true", "yes", "on"}

    if use_postgres:
        return get_postgres_connection()

    return DummyDBLayer()
