import os
from google.cloud import bigquery

_client = None

def get_bigquery_client() -> bigquery.Client:
    """Returns a singleton BigQuery client instance.
    Reads credentials from GOOGLE_APPLICATION_CREDENTIALS environment variable.
    """
    global _client
    if _client is None:
        _client = bigquery.Client()
    return _client
