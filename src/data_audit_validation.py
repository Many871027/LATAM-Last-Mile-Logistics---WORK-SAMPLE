import os
import sys
import pandas as pd
import pydata_google_auth
from google.cloud import bigquery

def get_bq_client(project_id="meli-last-mile-sql-assessment"):
    try:
        credentials = pydata_google_auth.get_user_credentials(
            scopes=['https://www.googleapis.com/auth/cloud-platform'],
        )
        client = bigquery.Client(project=project_id, credentials=credentials)
        return client
    except Exception as e:
        print(f"Error connecting to BigQuery: {e}")
        sys.exit(1)

def run_audit():
    print("Connecting to BigQuery and running Unified Data Quality Audit...")
    client = get_bq_client()
    
    query = """
    SELECT 
      'shipments_new PK Duplication' as audit_check,
      COUNT(shipment_id) as total_records,
      COUNT(shipment_id) - COUNT(DISTINCT shipment_id) as error_count,
      ROUND((COUNT(shipment_id) - COUNT(DISTINCT shipment_id)) / COUNT(shipment_id) * 100, 2) as error_pct
    FROM `meli-last-mile-sql-assessment.LAstmile.shipments_new`

    UNION ALL

    SELECT
      'routes_new Chrono Violations' as audit_check,
      COUNT(*) as total_records,
      COUNTIF(actual_route_end_time < actual_route_start_time) as error_count,
      ROUND(COUNTIF(actual_route_end_time < actual_route_start_time) / COUNT(*) * 100, 2) as error_pct
    FROM `meli-last-mile-sql-assessment.LAstmile.routes_new`

    UNION ALL

    SELECT
      'shipment_events_new Hour Corruption' as audit_check,
      COUNT(*) as total_records,
      COUNTIF(event_hour_utc != EXTRACT(HOUR FROM event_timestamp)) as error_count,
      ROUND(COUNTIF(event_hour_utc != EXTRACT(HOUR FROM event_timestamp)) / COUNT(*) * 100, 2) as error_pct
    FROM `meli-last-mile-sql-assessment.LAstmile.shipment_events_new`
    WHERE event_timestamp IS NOT NULL

    UNION ALL

    SELECT
      'routes_new Missing Partners' as audit_check,
      COUNT(*) as total_records,
      COUNTIF(partner_id IS NULL) as error_count,
      ROUND(COUNTIF(partner_id IS NULL) / COUNT(*) * 100, 2) as error_pct
    FROM `meli-last-mile-sql-assessment.LAstmile.routes_new`

    UNION ALL

    SELECT
      'partners Deprecated Contracts' as audit_check,
      COUNT(*) as total_records,
      COUNTIF(active_flag = -1) as error_count,
      ROUND(COUNTIF(active_flag = -1) / COUNT(*) * 100, 2) as error_pct
    FROM `meli-last-mile-sql-assessment.LAstmile.partners`

    ORDER BY error_pct DESC;
    """
    
    df = client.query(query).to_dataframe()
    print("\\n--- UNIFIED DATA QUALITY AUDIT RESULTS ---")
    print(df.to_string(index=False))
    print("\\nAudit complete.")

if __name__ == "__main__":
    run_audit()
