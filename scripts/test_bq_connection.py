import os
from dotenv import load_dotenv
from google.cloud import bigquery

def test_connection():
    try:
        # Load environment variables
        load_dotenv()
        
        project_id = os.getenv("GCP_PROJECT_ID")
        dataset_id = os.getenv("BQ_DATASET_ID")
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        print(f"[*] Project ID: {project_id}")
        print(f"[*] Dataset ID: {dataset_id}")
        print(f"[*] Credentials Path: {credentials_path}")
        
        if not project_id:
            print("[-] ERROR: GCP_PROJECT_ID is not set in the .env file")
            return
            
        # Initialize client (it will automatically use GOOGLE_APPLICATION_CREDENTIALS)
        print("[*] Initializing BigQuery Client...")
        client = bigquery.Client(project=project_id)
        
        # Test 1: Simple Query
        print("[*] Testing basic query execution (SELECT 1)...")
        query_job = client.query("SELECT 1 AS test_col")
        results = query_job.result()
        for row in results:
            print(f"[+] Data retrieved successfully: {row.test_col}")
            
        # Test 2: Try to list tables in the dataset (if dataset exists)
        print(f"[*] Checking Dataset '{dataset_id}'...")
        dataset_ref = f"{project_id}.{dataset_id}"
        tables = client.list_tables(dataset_ref)
        
        table_names = [table.table_id for table in tables]
        if table_names:
            print(f"[+] Success! Found {len(table_names)} tables in Dataset '{dataset_id}':")
            for t in table_names:
                print(f"    - {t}")
        else:
            print(f"[+] Connection successful, but Dataset '{dataset_id}' currently has no tables (you need to run the table creation scripts next).")
            
        print("\n[+] ALL CONNECTIONS ARE STABLE AND READY!")
        
    except Exception as e:
        print(f"\n[-] CONNECTION ERROR: {e}")

if __name__ == "__main__":
    test_connection()
