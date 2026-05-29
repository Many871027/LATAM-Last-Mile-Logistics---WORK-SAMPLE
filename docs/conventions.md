# Coding & Query Conventions

To ensure readability and maintenance of the analytical pipeline, the following conventions are enforced:

## SQL Style Guidelines
- **Keywords**: Capitalize all SQL keywords (e.g., `SELECT`, `FROM`, `JOIN`, `WHERE`, `GROUP BY`, `ORDER BY`, `AND`, `OR`, `ON`, `AS`).
- **Nomenclature**:
  - Use lowercase snake_case for column aliases and table names.
  - Table aliases should be short but descriptive (e.g., `shipments_new` as `s`, `routes_new` as `r`).
- **Common Table Expressions (CTEs)**:
  - Prefer CTEs (`WITH ...`) over subqueries for complex logical blocks.
  - Name CTEs descriptively (e.g., `deduped_shipments`, `delivery_events`).
- **Safety Functions**:
  - Always use `SAFE_DIVIDE(numerator, denominator)` to prevent division by zero errors in metrics.
  - Avoid legacy SQL. All queries must run using `--use_legacy_sql=false` standard BigQuery SQL.

## Directory Structure Conventions
- **`DB/`**: Raw CSV data sources.
- **`Reports/`**: Markdown files with the analysis and answers for each individual question (Q1 through Q7).
- **`docs/`**: Project quality, architectural standards, and conventions.
- **`progress/`**: Session logs and checklist files.
