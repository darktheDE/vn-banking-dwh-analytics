# src/utils/

Shared utility modules used across the ETL and ML layers.

## Module Index

| Module | Description |
|--------|-------------|
| `bigquery_client.py` | Singleton BigQuery client factory. Reads credentials from `GOOGLE_APPLICATION_CREDENTIALS` env variable. |
| `logger.py` | Configures the standard Python `logging` library with a consistent format for all batch jobs. |
| `config.py` | Loads and exposes all `.env` variables via `os.getenv()` with explicit type casting and validation. |

## Usage

```python
from src.utils.logger import get_logger
from src.utils.bigquery_client import get_bigquery_client
from src.utils.config import Config

logger = get_logger(__name__)
client = get_bigquery_client()
project_id = Config.GCP_PROJECT_ID
```

All scripts in `src/etl/` and `src/models/` must use `get_logger()` from this module instead of configuring logging independently.
