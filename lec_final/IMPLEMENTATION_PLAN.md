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

