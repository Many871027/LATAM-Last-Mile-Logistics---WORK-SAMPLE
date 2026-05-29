import os
import sys
import pandas as pd
import numpy as np

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

def check_pk(df, pk_col, name):
    total = len(df)
    unique = df[pk_col].nunique()
    dups = total - unique
    if dups == 0:
        print_success(f"PK Integrity ({pk_col}): Solid. 0 duplicates.")
    else:
        print_warning(f"PK Integrity Violated in '{name}': {dups:,} duplicate keys ({dups/total*100:.2f}%)!")
        
def check_nulls(df, name):
    null_counts = df.isnull().sum()
    cols_with_nulls = null_counts[null_counts > 0]
    if cols_with_nulls.empty:
        print_success("Completeness Check: 0 NULL values across all columns.")
    else:
        print_warning(f"Completeness Check: Found NULL values in '{name}':")
        for col, cnt in cols_with_nulls.items():
            print(f"  - Column '{col}': {cnt:,} nulls ({cnt/len(df)*100:.2f}%)")

def main():
    db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DB")
    
    print_header("SENIOR OPERATIONS DATA AUDIT: SWEEPING ALL 9 LOGISTICS FILES")
    
    if not os.path.exists(db_dir):
        print_error(f"Directory {db_dir} does not exist.")
        sys.exit(1)
        
    # List files to verify
    csv_files = [
        "distribution_centers.csv",
        "partners.csv",
        "vehicle_types.csv",
        "routes.csv",
        "routes_new.csv",
        "shipments.csv",
        "shipments_new.csv",
        "shipment_events.csv",
        "shipment_events_new.csv"
    ]
    
    # Pre-load master dataframes for cross-reference validations
    masters = {}
    for f in csv_files:
        path = os.path.join(db_dir, f)
        if os.path.exists(path):
            try:
                masters[f] = pd.read_csv(path, low_memory=False)
            except Exception as e:
                print_error(f"Failed to pre-load {f}: {str(e)}")

    # 1. AUDIT: distribution_centers.csv
    print_header("1. AUDIT: distribution_centers.csv")
    if "distribution_centers.csv" in masters:
        df = masters["distribution_centers.csv"]
        print_info(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
        check_pk(df, "center_id", "distribution_centers")
        check_nulls(df, "distribution_centers")
        
        # Check active_flag values
        invalid_flags = df[~df['active_flag'].isin([0, 1])]
        if not invalid_flags.empty:
            print_error(f"Found {len(invalid_flags)} rows with invalid active_flag (expected 0 or 1):")
            print(invalid_flags[['center_id', 'active_flag']])
        else:
            print_success("Active flag values are valid (0 or 1).")
            
        # Check timezone offsets
        offsets = df['timezone_offset'].unique()
        print_info(f"Timezone offsets detected: {list(offsets)}")
        if any(abs(o) > 12 for o in offsets if pd.notna(o)):
            print_error("Anomaly: Timezone offset exceeds physical range (-12 to +12)!")
            
        # Check operational hours
        hour_errors = df[(df['operational_hours_start'] < 0) | (df['operational_hours_start'] > 23) |
                         (df['operational_hours_end'] < 0) | (df['operational_hours_end'] > 23)]
        if not hour_errors.empty:
            print_error(f"Found {len(hour_errors)} rows with invalid operational hours (outside 0-23):")
            print(hour_errors[['center_id', 'operational_hours_start', 'operational_hours_end']])
    else:
        print_error("distribution_centers.csv is missing!")

    # 2. AUDIT: partners.csv
    print_header("2. AUDIT: partners.csv")
    if "partners.csv" in masters:
        df = masters["partners.csv"]
        print_info(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
        check_pk(df, "partner_id", "partners")
        check_nulls(df, "partners")
        
        # Check for invalid active_flag (-1)
        invalid_flags = df[df['active_flag'] == -1]
        if not invalid_flags.empty:
            print_warning(f"Found {len(invalid_flags)} partners with active_flag = -1 (INVALID/DEPRECATED CONTRACTS):")
            print(invalid_flags[['partner_id', 'partner_name', 'active_flag']])
        else:
            print_success("No active_flag = -1 values found.")
            
        # Check for SLA bounds
        sla_anomalies = df[(df['sla_compliance_pct'] < 0) | (df['sla_compliance_pct'] > 100)]
        if not sla_anomalies.empty:
            print_error(f"Found {len(sla_anomalies)} partners with SLA compliance out of bounds (0-100%):")
            print(sla_anomalies[['partner_id', 'sla_compliance_pct']])
            
        # Check average delivery time bounds
        avg_time_errors = df[df['average_delivery_time_hours'] <= 0]
        if not avg_time_errors.empty:
            print_error(f"Found {len(avg_time_errors)} partners with average_delivery_time_hours <= 0:")
            print(avg_time_errors[['partner_id', 'average_delivery_time_hours']])
    else:
        print_error("partners.csv is missing!")

    # 3. AUDIT: vehicle_types.csv
    print_header("3. AUDIT: vehicle_types.csv")
    if "vehicle_types.csv" in masters:
        df = masters["vehicle_types.csv"]
        print_info(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
        check_pk(df, "vehicle_type_id", "vehicle_types")
        check_nulls(df, "vehicle_types")
        
        # Validate fuel type
        valid_fuels = ['FUEL', 'ELECTRIC', 'HUMAN']
        invalid_fuels = df[~df['fuel_type'].isin(valid_fuels)]
        if not invalid_fuels.empty:
            print_error(f"Found {len(invalid_fuels)} vehicle types with unexpected fuel_type:")
            print(invalid_fuels[['vehicle_type_id', 'fuel_type']])
        else:
            print_success(f"Fuel types are valid {valid_fuels}.")
            
        # Validate capacities
        cap_errors = df[df['max_capacity_units'] <= 0]
        if not cap_errors.empty:
            print_error(f"Found {len(cap_errors)} vehicles with capacity <= 0:")
            print(cap_errors[['vehicle_type_id', 'max_capacity_units']])
    else:
        print_error("vehicle_types.csv is missing!")

    # 4 & 5. AUDIT: routes.csv & routes_new.csv
    for r_file in ["routes.csv", "routes_new.csv"]:
        print_header(f"AUDIT: {r_file}")
        if r_file in masters:
            df = masters[r_file]
            print_info(f"Shape: {df.shape[0]:,} rows, {df.shape[1]} columns")
            check_pk(df, "route_id", r_file)
            check_nulls(df, r_file)
            
            # 4.1 Chronology Check (Start vs End time)
            # In routes.csv they are TIME strings, in routes_new they are TIMESTAMP strings.
            # We cast to datetime to perform subtraction safely.
            non_null_times = df[df['actual_route_start_time'].notnull() & df['actual_route_end_time'].notnull()]
            start_t = pd.to_datetime(non_null_times['actual_route_start_time'], errors='coerce')
            end_t = pd.to_datetime(non_null_times['actual_route_end_time'], errors='coerce')
            
            # Identify where end is before start
            chrono_errors = non_null_times[end_t < start_t]
            if not chrono_errors.empty:
                print_error(f"Chronology Anomaly: Found {len(chrono_errors)} routes where actual_route_end_time < actual_route_start_time!")
                print(chrono_errors[['route_id', 'actual_route_start_time', 'actual_route_end_time']].head(5))
            else:
                print_success("Chronology Check: 0 routes with actual_end before actual_start.")
                
            # 4.2 Overlapping routes check (Driver / Vehicle overlap)
            # Multiple routes on the same route_date operated by the same partner_id where times overlap
            print_info("Checking for route overlaps by partner/date (Driver Double-Allocation)...")
            overlap_df = df[df['partner_id'].notnull() & df['route_date'].notnull() & df['actual_route_start_time'].notnull() & df['actual_route_end_time'].notnull()]
            
            # Group by partner and date and search for overlap
            overlap_count = 0
            grouped = overlap_df.groupby(['partner_id', 'route_date'])
            for keys, group in grouped:
                if len(group) > 1:
                    # Sort by start time
                    group = group.copy()
                    group['start_dt'] = pd.to_datetime(group['actual_route_start_time'], errors='coerce')
                    group['end_dt'] = pd.to_datetime(group['actual_route_end_time'], errors='coerce')
                    group = group.dropna(subset=['start_dt', 'end_dt']).sort_values('start_dt')
                    
                    for i in range(len(group) - 1):
                        current_end = group.iloc[i]['end_dt']
                        next_start = group.iloc[i+1]['start_dt']
                        if current_end > next_start:
                            overlap_count += 1
                            if overlap_count <= 3:
                                print_warning(f"Overlap detected for partner {keys[0]} on {keys[1]}:")
                                print(f"  - Route A: {group.iloc[i]['route_id']} | End: {group.iloc[i]['actual_route_start_time']} - {group.iloc[i]['actual_route_end_time']}")
                                print(f"  - Route B: {group.iloc[i+1]['route_id']} | Start: {group.iloc[i+1]['actual_route_start_time']} - {group.iloc[i+1]['actual_route_end_time']}")
            if overlap_count > 0:
                print_error(f"Total overlapping routes (double allocations) detected: {overlap_count}")
            else:
                print_success("No overlapping routes detected.")
                
            # 4.3 Outlier Stop Counts
            stops_anomaly = df[df['actual_stops'] > df['estimated_stops'] * 1.5]
            if not stops_anomaly.empty:
                print_warning(f"Found {len(stops_anomaly)} routes where actual_stops exceeds estimated_stops by >50% (potential route inflation):")
                print(stops_anomaly[['route_id', 'estimated_stops', 'actual_stops']].head(5))
                
            # 4.4 Master key referential check
            if "partners.csv" in masters:
                valid_partners = set(masters["partners.csv"]["partner_id"])
                orphan_p = df[~df["partner_id"].isin(valid_partners) & df["partner_id"].notnull()]["partner_id"].unique()
                if len(orphan_p) > 0:
                    print_error(f"Referential Violation: Found {len(orphan_p)} orphan partner_ids in routes that do not exist in partners.csv!")
                    print(f"  Sample: {list(orphan_p)[:3]}")
                else:
                    print_success("Referential Integrity: All route partner_ids exist in partners.csv.")
                    
            if "vehicle_types.csv" in masters:
                valid_v = set(masters["vehicle_types.csv"]["vehicle_type_id"])
                orphan_v = df[~df["vehicle_type_id"].isin(valid_v) & df["vehicle_type_id"].notnull()]["vehicle_type_id"].unique()
                if len(orphan_v) > 0:
                    print_error(f"Referential Violation: Found {len(orphan_v)} orphan vehicle_type_ids in routes that do not exist in vehicle_types.csv!")
                else:
                    print_success("Referential Integrity: All route vehicle_type_ids exist in vehicle_types.csv.")
        else:
            print_error(f"{r_file} is missing!")

    # 6 & 7. AUDIT: shipments.csv & shipments_new.csv
    for s_file in ["shipments.csv", "shipments_new.csv"]:
        print_header(f"AUDIT: {s_file}")
        if s_file in masters:
            df = masters[s_file]
            print_info(f"Shape: {df.shape[0]:,} rows, {df.shape[1]} columns")
            check_pk(df, "shipment_id", s_file)
            check_nulls(df, s_file)
            
            # Check shipment_date format profiling
            if 'shipment_date' in df.columns:
                dates = df['shipment_date'].dropna()
                date_patterns = dates.astype(str).str.replace(r'\d', 'N', regex=True).value_counts()
                print_info(f"shipment_date formats in {s_file}:")
                for pat, count in date_patterns.items():
                    print(f"  - Pattern '{pat:<12}': {count:8,} rows ({count/len(dates)*100:6.2f}%)")
                    
            # Check status_change_timestamp format profiling
            if 'status_change_timestamp' in df.columns:
                ts = df['status_change_timestamp'].dropna()
                ts_patterns = ts.astype(str).str.replace(r'\d', 'N', regex=True).value_counts()
                print_info(f"status_change_timestamp formats in {s_file}:")
                for pat, count in ts_patterns.items():
                    print(f"  - Pattern '{pat:<20}': {count:8,} rows ({count/len(ts)*100:6.2f}%)")
                    
            # Check delivery attempt range
            if 'delivery_attempt_count' in df.columns:
                attempts = df['delivery_attempt_count']
                numeric_attempts = pd.to_numeric(attempts, errors='coerce')
                neg_attempts = (numeric_attempts < 0).sum()
                too_high = (numeric_attempts > 10).sum()
                if neg_attempts > 0:
                    print_error(f"Found {neg_attempts} rows with negative delivery_attempt_count!")
                if too_high > 0:
                    print_warning(f"Found {too_high} rows with excessive delivery_attempt_count (>10 attempts)!")
        else:
            print_error(f"{s_file} is missing!")

    # 8 & 9. AUDIT: shipment_events.csv & shipment_events_new.csv
    for se_file in ["shipment_events.csv", "shipment_events_new.csv"]:
        print_header(f"AUDIT: {se_file}")
        if se_file in masters:
            df = masters[se_file]
            print_info(f"Shape: {df.shape[0]:,} rows, {df.shape[1]} columns")
            check_pk(df, "event_id", se_file)
            check_nulls(df, se_file)
            
            # Validate event hours (0-23)
            hour_errors = df[(df['event_hour_utc'] < 0) | (df['event_hour_utc'] > 23)]
            if not hour_errors.empty:
                print_error(f"Found {len(hour_errors)} rows with invalid event_hour_utc (outside 0-23)!")
                print(hour_errors[['event_id', 'event_hour_utc']].head(5))
            else:
                print_success("All event_hour_utc values are within valid 0-23 range.")
                
            # Verify if event_hour_utc matches the hour in event_timestamp
            print_info("Checking event_hour_utc consistency with event_timestamp...")
            df_non_null = df[df['event_timestamp'].notnull() & df['event_hour_utc'].notnull()]
            parsed_hour = pd.to_datetime(df_non_null['event_timestamp'], errors='coerce').dt.hour
            mismatch = df_non_null[df_non_null['event_hour_utc'] != parsed_hour]
            
            if not mismatch.empty:
                print_error(f"Found {len(mismatch)} rows where event_hour_utc DOES NOT MATCH the hour in event_timestamp!")
                print(mismatch[['event_id', 'event_timestamp', 'event_hour_utc']].head(5))
            else:
                print_success("Verification Success: event_hour_utc is fully consistent with event_timestamp.")
                
            # Check for orphan shipments
            # Find if shipment_id in events exists in shipments
            if "shipments_new.csv" in masters:
                valid_shipments = set(masters["shipments_new.csv"]["shipment_id"])
                orphan_se = df[~df["shipment_id"].isin(valid_shipments) & df["shipment_id"].notnull()]["shipment_id"].unique()
                if len(orphan_se) > 0:
                    print_error(f"Referential Violation: Found {len(orphan_se)} unique shipment_ids in events that do not exist in shipments_new.csv!")
                    print(f"  Sample: {list(orphan_se)[:3]}")
                else:
                    print_success("Referential Integrity: All event shipment_ids exist in shipments_new.csv.")
        else:
            print_error(f"{se_file} is missing!")

    print_header("COMPREHENSIVE SWEEP ANALYSIS COMPLETE")

if __name__ == "__main__":
    main()
