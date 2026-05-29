# Verification Methodology

To verify the accuracy of the BI and SQL assessment outcomes, we use a multi-tiered verification process.

## 1. Local EDA Validation
- Execute local Python scripts (e.g., `first_eda.py`) to audit raw counts, duplicates, and missing values from CSV source files.
- Compare local counts against BigQuery post-load queries to confirm 0 data loss during the ETL load.

## 2. SQL Integrity Asserts
Every query must be verified using the following check steps:
- **Deduplication Check**: Run queries with and without dynamic deduplication CTEs to measure the exact impact of duplicate PKs.
- **Chronology Check**: Ensure route durations are non-negative.
- **Timezone Verification**: Compare UTC vs local hours using timezone offset to confirm that local operations align with regional business hours (08:00 - 20:00).
- **Null Verification**: Count total null values in columns to verify proper parsing.
