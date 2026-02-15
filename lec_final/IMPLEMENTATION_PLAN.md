# Final Project Implementation Plan

## Overview

This plan outlines the step-by-step implementation of the data platform for analyzing electronics sales by customer geography (state) and age. The project uses AWS services (S3, Glue, RDS PostgreSQL) orchestrated by Apache Airflow.

---

## 1. Data Pipeline Architecture

### Pipeline Dependency Diagram

```
┌─────────────────────┐     ┌──────────────────────┐
│   process_sales     │     │  process_customers   │
│   (scheduled daily) │     │   (scheduled daily)  │
└─────────┬───────────┘     └──────────┬───────────┘
          │                            │
          │    raw → bronze → silver   │
          │                            │
          └──────────┬─────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │ process_user_profiles │
          │    (manual trigger)   │
          └──────────┬────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │ enrich_user_profiles  │
          │    (manual trigger)   │
          └──────────┬────────────┘
                     │
                     ▼
              ┌────────────┐
              │   GOLD     │
              │ (RDS/DWH)  │
              └────────────┘
```

### Execution Order
1. `process_sales` - Daily scheduled (can run in parallel with process_customers)
2. `process_customers` - Daily scheduled (can run in parallel with process_sales)
3. `process_user_profiles` - Manual trigger (after sales & customers are loaded)
4. `enrich_user_profiles` - Manual trigger (after user_profiles is complete)

---

## 2. Infrastructure Components (Already Deployed)

| Component | Resource Name | Purpose |
|-----------|---------------|---------|
| **Data Lake S3** | `yurii-data-platform-data-lake-467137831070` | raw/bronze/silver/gold layers |
| **Airflow S3** | `yurii-data-platform-airflow-467137831070` | DAG storage |
| **Glue Database** | `yurii_data_platform_database` | Data Catalog |
| **Glue S3 Crawler** | `yurii-data-platform-s3-crawler` | Catalog S3 data |
| **RDS PostgreSQL** | `yurii-data-platform-warehouse...` | Gold layer (DWH) |
| **Airflow UI** | `http://yurii-data-platform-airflow-alb-...` | Orchestration |
| **Athena Workgroup** | `yurii-data-platform-workgroup` | Ad-hoc queries |

### S3 Bucket Structure
```
s3://yurii-data-platform-data-lake-467137831070/
├── raw/
│   ├── sales/2022-09-{1..30}/sales.csv
│   ├── customers/2022-08-{1..5}/*.csv
│   └── user_profiles/user_profiles.json
├── bronze/
│   ├── sales/          (partitioned by date)
│   └── customers/      (not partitioned)
├── silver/
│   ├── sales/          (partitioned by purchase_date)
│   ├── customers/      (not partitioned)
│   └── user_profiles/  (not partitioned)
└── gold/
    └── user_profiles_enriched/  (final enriched data)
```

---

## 3. Data Processing Steps

### 3.1 Pipeline: `process_sales`

| Attribute | Details |
|-----------|---------|
| **Schedule** | Daily (`@daily`) |
| **Input** | `s3://bucket/raw/sales/2022-09-{date}/sales.csv` |
| **Format** | CSV with header |
| **Partitioning** | By date (already partitioned in source) |

#### Source Schema (raw)
```
CustomerId, PurchaseDate, Product, Price
```

#### Bronze Layer
- **Transformation**: Read CSV as external table, all fields as STRING
- **Output**: `s3://bucket/bronze/sales/` (Parquet, partitioned by date)
- **Columns**: `CustomerId, PurchaseDate, Product, Price` (all STRING)

#### Silver Layer
- **Transformations**:
  - Rename columns: `CustomerId→client_id`, `PurchaseDate→purchase_date`, `Product→product_name`, `Price→price`
  - Clean price field (remove `$` symbol)
  - Cast types: `client_id` (INT), `purchase_date` (DATE), `price` (DECIMAL)
  - Data quality: Remove nulls, validate date format
- **Output**: `s3://bucket/silver/sales/` (Parquet, partitioned by `purchase_date`)
- **Columns**: `client_id (INT), purchase_date (DATE), product_name (STRING), price (DECIMAL)`

---

### 3.2 Pipeline: `process_customers`

| Attribute | Details |
|-----------|---------|
| **Schedule** | Daily (`@daily`) |
| **Input** | `s3://bucket/raw/customers/2022-08-{date}/*.csv` |
| **Format** | CSV with header |
| **Partitioning** | None (small dataset, full dump each day) |

**Note**: Each day's folder contains a full dump of all previous days' data. Use the latest folder (2022-08-5) for complete data.

#### Source Schema (raw)
```
Id, FirstName, LastName, Email, RegistrationDate, State
```

#### Bronze Layer
- **Transformation**: Read CSV as external table, all fields as STRING
- **Output**: `s3://bucket/bronze/customers/` (Parquet)
- **Columns**: `Id, FirstName, LastName, Email, RegistrationDate, State` (all STRING)

#### Silver Layer
- **Transformations**:
  - Rename columns: `Id→client_id`, `FirstName→first_name`, `LastName→last_name`, `Email→email`, `RegistrationDate→registration_date`, `State→state`
  - Cast types: `client_id` (INT), `registration_date` (DATE)
  - Deduplicate by `client_id` (keep latest record)
- **Output**: `s3://bucket/silver/customers/` (Parquet)
- **Columns**: `client_id (INT), first_name (STRING), last_name (STRING), email (STRING), registration_date (DATE), state (STRING)`

**Data Quality Issues** (to be fixed in enrichment):
- Missing `first_name` or `last_name` values
- Missing `state` values
- No age/birth_date information

---

### 3.3 Pipeline: `process_user_profiles`

| Attribute | Details |
|-----------|---------|
| **Schedule** | Manual trigger (no schedule) |
| **Input** | `s3://bucket/raw/user_profiles/user_profiles.json` |
| **Format** | JSONLine (one JSON object per line) |
| **Partitioning** | None |

#### Source Schema (raw)
```json
{"email": "...", "full_name": "...", "state": "...", "birth_date": "YYYY-MM-DD", "phone_number": "..."}
```

#### Silver Layer (direct from raw)
- **Transformations**:
  - Parse JSON fields
  - Cast `birth_date` to DATE type
  - Calculate `age` from `birth_date` (optional, can be done in enrichment)
- **Output**: `s3://bucket/silver/user_profiles/` (Parquet)
- **Columns**: `email (STRING), full_name (STRING), state (STRING), birth_date (DATE), phone_number (STRING)`

**Note**: This data has perfect quality and will be used to enrich customers data.

---

### 3.4 Pipeline: `enrich_user_profiles`

| Attribute | Details |
|-----------|---------|
| **Schedule** | Manual trigger (no schedule) |
| **Input** | `silver.customers` + `silver.user_profiles` |
| **Output** | `gold.user_profiles_enriched` (RDS PostgreSQL) |
| **Join Key** | `customers.email = user_profiles.email` |

#### Enrichment Logic (using SQL MERGE concept)
```sql
-- Pseudocode for enrichment
SELECT
    c.client_id,
    COALESCE(c.first_name, SPLIT(up.full_name, ' ')[0]) AS first_name,
    COALESCE(c.last_name, SPLIT(up.full_name, ' ')[1]) AS last_name,
    c.email,
    c.registration_date,
    COALESCE(c.state, up.state) AS state,
    up.birth_date,
    DATE_DIFF(CURRENT_DATE, up.birth_date, YEAR) AS age,
    up.phone_number
FROM silver.customers c
LEFT JOIN silver.user_profiles up ON c.email = up.email
```

#### Gold Layer Schema (RDS PostgreSQL)
```sql
CREATE TABLE gold.user_profiles_enriched (
    client_id INTEGER PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255) UNIQUE,
    registration_date DATE,
    state VARCHAR(50),
    birth_date DATE,
    age INTEGER,
    phone_number VARCHAR(50)
);
```

---

## 4. Implementation Tasks

### Phase 1: Initial Setup

- [ ] **Task 1.1**: Upload raw data to S3
  ```bash
  aws s3 cp --recursive data s3://yurii-data-platform-data-lake-467137831070/raw
  ```

- [ ] **Task 1.2**: Run Glue Crawler to catalog raw data
  ```bash
  aws glue start-crawler --name yurii-data-platform-s3-crawler
  ```

- [ ] **Task 1.3**: Verify tables in Glue Data Catalog
  - Check AWS Console: Glue → Data Catalog → Tables

### Phase 2: Create Glue ETL Jobs

- [ ] **Task 2.1**: Create `process_sales_raw_to_bronze` Glue job
  - Read from raw/sales (CSV)
  - Write to bronze/sales (Parquet, partitioned)

- [ ] **Task 2.2**: Create `process_sales_bronze_to_silver` Glue job
  - Read from bronze/sales
  - Apply transformations (rename, clean, cast)
  - Write to silver/sales (Parquet, partitioned)

- [ ] **Task 2.3**: Create `process_customers_raw_to_bronze` Glue job
  - Read from raw/customers (CSV)
  - Write to bronze/customers (Parquet)

- [ ] **Task 2.4**: Create `process_customers_bronze_to_silver` Glue job
  - Read from bronze/customers
  - Apply transformations (rename, deduplicate)
  - Write to silver/customers (Parquet)

- [ ] **Task 2.5**: Create `process_user_profiles_raw_to_silver` Glue job
  - Read from raw/user_profiles (JSONLine)
  - Write to silver/user_profiles (Parquet)

- [ ] **Task 2.6**: Create `enrich_user_profiles` Glue job
  - Read from silver/customers and silver/user_profiles
  - Join and enrich data
  - Write to RDS PostgreSQL gold.user_profiles_enriched

### Phase 3: Create Airflow DAGs

- [ ] **Task 3.1**: Create `process_sales_dag.py`
  - Schedule: `@daily`
  - Tasks: raw→bronze→silver

- [ ] **Task 3.2**: Create `process_customers_dag.py`
  - Schedule: `@daily`
  - Tasks: raw→bronze→silver

- [ ] **Task 3.3**: Create `process_user_profiles_dag.py`
  - Schedule: None (manual)
  - Tasks: raw→silver

- [ ] **Task 3.4**: Create `enrich_user_profiles_dag.py`
  - Schedule: None (manual)
  - Tasks: silver→gold (RDS)
  - Optional: Trigger from process_user_profiles on success

- [ ] **Task 3.5**: Upload DAGs to Airflow S3 bucket
  ```bash
  aws s3 cp dags/ s3://yurii-data-platform-airflow-467137831070/dags/ --recursive
  ```

### Phase 4: Create Gold Layer Table in RDS

- [ ] **Task 4.1**: Connect to RDS PostgreSQL
  ```bash
  psql -h <RDS_ENDPOINT> \
       -U <DB_USER> -d datawarehouse
  ```

- [ ] **Task 4.2**: Create gold schema and table
  ```sql
  CREATE SCHEMA IF NOT EXISTS gold;

  CREATE TABLE gold.user_profiles_enriched (
      client_id INTEGER PRIMARY KEY,
      first_name VARCHAR(100),
      last_name VARCHAR(100),
      email VARCHAR(255) UNIQUE,
      registration_date DATE,
      state VARCHAR(50),
      birth_date DATE,
      age INTEGER,
      phone_number VARCHAR(50)
  );
  ```

### Phase 5: Testing & Validation

- [ ] **Task 5.1**: Run process_sales DAG and verify data in silver layer
- [ ] **Task 5.2**: Run process_customers DAG and verify data in silver layer
- [ ] **Task 5.3**: Run process_user_profiles DAG and verify data in silver layer
- [ ] **Task 5.4**: Run enrich_user_profiles DAG and verify data in gold layer
- [ ] **Task 5.5**: Run final analytics query

---

## 5. Final Analytics Query

**Question (Ukrainian)**:
> В якому штаті було куплено найбільше телевізорів покупцями від 20 до 30 років за першу декаду вересня?

**Question (English)**:
> Which state had the most TV purchases by customers aged 20-30 in the first 10 days of September?

### SQL Query (for RDS PostgreSQL)
```sql
SELECT
    e.state,
    COUNT(*) AS tv_purchases
FROM gold.user_profiles_enriched e
JOIN silver.sales s ON e.client_id = s.client_id
WHERE
    s.product_name ILIKE '%TV%' OR s.product_name ILIKE '%телевізор%'
    AND e.age BETWEEN 20 AND 30
    AND s.purchase_date BETWEEN '2022-09-01' AND '2022-09-10'
GROUP BY e.state
ORDER BY tv_purchases DESC
LIMIT 1;
```

### Alternative Query (using Athena on S3)
```sql
SELECT
    up.state,
    COUNT(*) AS tv_purchases
FROM silver_sales s
JOIN silver_customers c ON s.client_id = c.client_id
JOIN silver_user_profiles up ON c.email = up.email
WHERE
    (s.product_name LIKE '%TV%' OR s.product_name LIKE '%Television%')
    AND DATE_DIFF('year', up.birth_date, CURRENT_DATE) BETWEEN 20 AND 30
    AND s.purchase_date BETWEEN DATE '2022-09-01' AND DATE '2022-09-10'
GROUP BY up.state
ORDER BY tv_purchases DESC
LIMIT 1;
```

---

## 6. Data Engineering Concepts Applied

| Concept | Where Applied |
|---------|---------------|
| **Data Cleansing** | Removing `$` from prices, handling nulls, deduplication |
| **Data Wrangling** | Column renaming, type casting, schema standardization |
| **Data Enrichment** | Joining customers with user_profiles to fill missing data |
| **MERGE Pattern** | Using COALESCE to prefer existing data, fill gaps from user_profiles |

---

## 7. Commit History Guidelines

Per project requirements, maintain meaningful commit history:

1. `feat: add infrastructure terraform configuration`
2. `feat: create process_sales glue jobs (raw→bronze→silver)`
3. `feat: create process_customers glue jobs`
4. `feat: create process_user_profiles glue job`
5. `feat: create enrich_user_profiles glue job with RDS integration`
6. `feat: add airflow DAGs for all pipelines`
7. `feat: add gold layer table schema`
8. `docs: add final analytics query and results`

**Important**: Do NOT submit with a single commit - this will result in 0 points!
