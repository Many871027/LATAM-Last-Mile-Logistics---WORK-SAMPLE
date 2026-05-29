import os
import sys
import pandas as pd
from google.cloud import bigquery
import pydata_google_auth

# Enable ANSI colors in Windows terminal
if os.name == 'nt':
    os.system('color')

# ANSI Color Codes
C_BLUE = "\033[94m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91;1m"
C_CYAN = "\033[96;1m"
C_BOLD = "\033[1m"
C_RESET = "\033[0m"

def print_header(title):
    print(f"\n{C_CYAN}{'='*80}{C_RESET}")
    print(f"{C_CYAN}{C_BOLD}   {title}{C_RESET}")
    print(f"{C_CYAN}{'='*80}{C_RESET}")

def print_section(title):
    print(f"\n{C_BOLD}{C_BLUE}>>> {title}{C_RESET}")

def print_success(msg):
    print(f"{C_GREEN}[OK] {msg}{C_RESET}")

def print_info(msg):
    print(f"{C_BLUE}[i] {msg}{C_RESET}")

def print_warning(msg):
    print(f"{C_YELLOW}[!] {msg}{C_RESET}")

def print_error(msg):
    print(f"{C_RED}[ERR] {msg}{C_RESET}")

# 1. Define Explicit Schemas (Senior Ingestion Protocol)
SCHEMAS = {
    "distribution_centers": [
        bigquery.SchemaField("center_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("center_name", "STRING"),
        bigquery.SchemaField("country", "STRING"),
        bigquery.SchemaField("region", "STRING"),
        bigquery.SchemaField("center_type", "STRING"),
        bigquery.SchemaField("active_flag", "INTEGER"),
        bigquery.SchemaField("operational_hours_start", "INTEGER"),
        bigquery.SchemaField("operational_hours_end", "INTEGER"),
        bigquery.SchemaField("max_daily_capacity_units", "INTEGER"),
        bigquery.SchemaField("established_date", "DATE"),
        bigquery.SchemaField("timezone_offset", "INTEGER"),
    ],
    "partners": [
        bigquery.SchemaField("partner_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("partner_name", "STRING"),
        bigquery.SchemaField("partner_type", "STRING"),
        bigquery.SchemaField("country", "STRING"),
        bigquery.SchemaField("active_flag", "INTEGER"),
        bigquery.SchemaField("contract_start_date", "DATE"),
        bigquery.SchemaField("contract_end_date", "DATE"),
        bigquery.SchemaField("average_delivery_time_hours", "FLOAT"),
        bigquery.SchemaField("sla_compliance_pct", "FLOAT"),
    ],
    "vehicle_types": [
        bigquery.SchemaField("vehicle_type_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("vehicle_type_name", "STRING"),
        bigquery.SchemaField("max_capacity_units", "INTEGER"),
        bigquery.SchemaField("fuel_type", "STRING"),
        bigquery.SchemaField("active_flag", "INTEGER"),
    ],
    "routes": [
        bigquery.SchemaField("route_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("partner_id", "STRING"),
        bigquery.SchemaField("vehicle_type_id", "STRING"),
        bigquery.SchemaField("center_id", "STRING"),
        bigquery.SchemaField("route_date", "DATE"),
        bigquery.SchemaField("route_type", "STRING"),
        bigquery.SchemaField("route_status", "STRING"),
        bigquery.SchemaField("planned_route_start_time", "TIME"),
        bigquery.SchemaField("planned_route_end_time", "TIME"),
        bigquery.SchemaField("actual_route_start_time", "TIME"),
        bigquery.SchemaField("actual_route_end_time", "TIME"),
        bigquery.SchemaField("route_distance_km", "FLOAT"),
        bigquery.SchemaField("estimated_stops", "INTEGER"),
        bigquery.SchemaField("actual_stops", "INTEGER"),
    ],
    "routes_new": [
        bigquery.SchemaField("route_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("partner_id", "STRING"),
        bigquery.SchemaField("vehicle_type_id", "STRING"),
        bigquery.SchemaField("center_id", "STRING"),
        bigquery.SchemaField("route_date", "DATE"),
        bigquery.SchemaField("route_type", "STRING"),
        bigquery.SchemaField("route_status", "STRING"),
        bigquery.SchemaField("planned_route_start_time", "TIMESTAMP"),
        bigquery.SchemaField("planned_route_end_time", "TIMESTAMP"),
        bigquery.SchemaField("actual_route_start_time", "TIMESTAMP"),
        bigquery.SchemaField("actual_route_end_time", "TIMESTAMP"),
        bigquery.SchemaField("route_distance_km", "FLOAT"),
        bigquery.SchemaField("estimated_stops", "INTEGER"),
        bigquery.SchemaField("actual_stops", "INTEGER"),
    ],
    "shipments": [
        bigquery.SchemaField("shipment_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("route_id", "STRING"),
        bigquery.SchemaField("partner_id", "STRING"),
        bigquery.SchemaField("shipment_date", "DATE"),
        bigquery.SchemaField("shipment_status", "STRING"),
        bigquery.SchemaField("status_change_timestamp", "TIMESTAMP"),
        bigquery.SchemaField("delivery_attempt_count", "INTEGER"),
        bigquery.SchemaField("last_status_detail", "STRING"),
    ],
    "shipments_new": [
        bigquery.SchemaField("shipment_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("route_id", "STRING"),
        bigquery.SchemaField("last_status_detail", "STRING"),
        bigquery.SchemaField("delivery_attempt_count", "INTEGER"),
        bigquery.SchemaField("status_change_timestamp", "TIMESTAMP"),
    ],
    "shipment_events": [
        bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("shipment_id", "STRING"),
        bigquery.SchemaField("center_id", "STRING"),
        bigquery.SchemaField("event_type", "STRING"),
        bigquery.SchemaField("event_timestamp", "TIMESTAMP"),
        bigquery.SchemaField("event_hour_utc", "INTEGER"),
    ],
    "shipment_events_new": [
        bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("shipment_id", "STRING"),
        bigquery.SchemaField("route_id", "STRING"),
        bigquery.SchemaField("event_type", "STRING"),
        bigquery.SchemaField("event_timestamp", "TIMESTAMP"),
        bigquery.SchemaField("event_hour_utc", "INTEGER"),
    ]
}

def robust_to_datetime(series):
    sample = series.dropna().iloc[0] if not series.dropna().empty else None
    if sample and isinstance(sample, str):
        if '/' in sample:
            return pd.to_datetime(series, dayfirst=True, errors='coerce')
        else:
            return pd.to_datetime(series, dayfirst=False, errors='coerce')
    return pd.to_datetime(series, errors='coerce')

def clean_time(val):
    if pd.isna(val):
        return None
    val_str = str(val).strip()
    if len(val_str.split(':')) == 2:
        return val_str + ":00"
    return val_str

def main():
    print_header("SENIOR ETL PIPELINE: CLEANING & INGESTING LATAM LAST MILE DATA")
    
    db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DB")
    project_id = "meli-last-mile-sql-assessment"
    dataset_id = "LAstmile"
    
    # 2. Authentication
    print_section("Authenticating and Connecting to BigQuery")
    try:
        credentials = pydata_google_auth.get_user_credentials(
            scopes=['https://www.googleapis.com/auth/cloud-platform'],
        )
        client = bigquery.Client(project=project_id, credentials=credentials)
        print_success("Connected to BigQuery successfully.")
    except Exception as e:
        print_error(f"Authentication failed: {str(e)}")
        sys.exit(1)
        
    # Iterate through all 9 tables in the schema list
    for table_name, schema in SCHEMAS.items():
        print_header(f"PROCESSING TABLE: {table_name}")
        csv_file = os.path.join(db_dir, f"{table_name}.csv")
        
        if not os.path.exists(csv_file):
            print_error(f"Source file {csv_file} does not exist. Skipping.")
            continue
            
        print_info(f"Loading {csv_file} in memory...")
        try:
            df = pd.read_csv(csv_file, low_memory=False)
            print_info(f"Loaded {len(df):,} rows.")
        except Exception as e:
            print_error(f"Failed to read CSV: {str(e)}")
            continue
            
        # 3. Clean columns based on target types
        print_info("Cleaning column formats to match BQ strict constraints...")
        
        # Analyze schema fields to clean date/time formats
        for field in schema:
            col = field.name
            if col not in df.columns:
                # If column is missing and it's required, raise error
                if field.mode == "REQUIRED":
                    print_error(f"Required column '{col}' is missing in CSV!")
                    sys.exit(1)
                else:
                    df[col] = None
                    continue
            
            # 3.1. Clean Dates
            if field.field_type == "DATE":
                df[col] = robust_to_datetime(df[col]).dt.strftime('%Y-%m-%d')
                
            # 3.2. Clean Timestamps
            elif field.field_type == "TIMESTAMP":
                # Convert to datetime and format as standard ISO timestamp
                df[col] = robust_to_datetime(df[col]).dt.strftime('%Y-%m-%d %H:%M:%S')
                
            # 3.3. Clean Times
            elif field.field_type == "TIME":
                df[col] = df[col].apply(clean_time)
                
            # 3.4. Clean Integers
            elif field.field_type == "INTEGER":
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # If the column has NaNs but is INTEGER, we replace it with None (which is fine for NULLABLE fields)
                # BQ client handles Float/Int conversion with None as Null
                
            # 3.5. Clean Floats
            elif field.field_type == "FLOAT":
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # 4. Upload using strict BigQuery load configuration
        # Align columns with the BigQuery schema mapping
        schema_cols = [field.name for field in schema]
        df = df[schema_cols]
        
        temp_cleaned_csv = os.path.join(db_dir, f"{table_name}_cleaned_temp.csv")
        print_info(f"Writing cleaned data to temporary file: {temp_cleaned_csv}...")
        
        # Save as standard UTF-8 CSV with no index and standard date formatting
        df.to_csv(temp_cleaned_csv, index=False, date_format='%Y-%m-%d %H:%M:%S')
        
        table_ref = client.dataset(dataset_id).table(table_name)
        
        # Senior Loading Configuration: Strict, Idempotent
        job_config = bigquery.LoadJobConfig(
            schema=schema,
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,
            # WRITE_TRUNCATE guarantees idempotency (wipes table and reloads to avoid duplicates if rerun)
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            # max_bad_records=0 ensures that any parsing error fails the upload immediately (zero tolerance for dirty data)
            max_bad_records=0,
            # We explicitly define the CSV parsing parameters
            allow_quoted_newlines=True,
            field_delimiter=","
        )
        
        print_info(f"Executing BigQuery load job for '{table_name}' with 0 bad records tolerance (Strict Ingestion)...")
        try:
            with open(temp_cleaned_csv, "rb") as source_file:
                load_job = client.load_table_from_file(
                    source_file,
                    table_ref,
                    job_config=job_config
                )
            
            # Wait for job to complete
            load_job.result()
            print_success(f"Ingested {load_job.output_rows:,} rows successfully into `{project_id}.{dataset_id}.{table_name}`.")
            
        except Exception as e:
            print_error(f"Strict load job FAILED for '{table_name}': {str(e)}")
            # Keep the temp file for debugging
            continue
            
        # Clean up temp file
        if os.path.exists(temp_cleaned_csv):
            os.remove(temp_cleaned_csv)
            
    print_header("ETL PIPELINE EXECUTION COMPLETE. DATA WAREHOUSE INTEGRITY RESTORED.")

if __name__ == "__main__":
    main()
