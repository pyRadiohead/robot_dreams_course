# AWS Services Guide for Data Engineers (Beginner-Friendly)

This guide explains each AWS service used in this data platform and why it's important for data engineering.

---

## 🗂️ Storage Services

### Amazon S3 (Simple Storage Service)
**What it is:** Cloud storage for files, like a massive hard drive in the cloud.

**Why we use it:**
- **Data Lake Storage**: Stores raw data files (CSV, JSON) and processed data
- **Cheap**: Pay only for what you store (~$0.023/GB/month)
- **Scalable**: Can store unlimited data
- **Durable**: 99.999999999% durability (won't lose your data)

**In our project:**
- `data-lake` bucket: Stores data in layers (raw → bronze → silver → gold)
- `airflow` bucket: Stores DAG files and Airflow configuration
- `athena-results` bucket: Stores query results from Athena

**Data Lake Layers:**
- **Raw**: Original data as-is (customers.csv, sales.csv)
- **Bronze**: Cleaned data with basic validation
- **Silver**: Transformed data, joined tables
- **Gold**: Business-ready aggregated data for analytics

---

### Amazon EFS (Elastic File System)
**What it is:** Shared file storage that multiple servers can access simultaneously.

**Why we use it:**
- Airflow needs shared storage so the webserver and scheduler can both access DAG files
- Unlike S3, EFS works like a regular folder that containers can mount

**In our project:**
- One EFS for DAG files
- One EFS for Airflow configuration files

---

## 🔍 Data Catalog & ETL

### AWS Glue
**What it is:** A serverless ETL (Extract, Transform, Load) service with a data catalog.

**Components we use:**

#### 1. Glue Data Catalog
- **What**: A metadata repository (database of databases)
- **Why**: Stores table schemas so you don't have to remember column names/types
- **Example**: After crawling, it knows `customers` table has columns: `customer_id`, `name`, `email`

#### 2. Glue Crawler
- **What**: Automatically scans your S3 data and creates table definitions
- **Why**: Saves you from manually defining schemas
- **How it works**:
  1. You point it at S3 folders
  2. It reads sample files
  3. It infers the schema (column names, data types)
  4. It creates tables in the Glue Catalog

**In our project:**
- S3 Crawler: Scans `raw/`, `bronze/`, `silver/`, `gold/` folders
- Redshift Crawler: Scans tables in Redshift

#### 3. Glue Connections
- **What**: Network connections to databases (like Redshift)
- **Why**: Allows Glue jobs to read/write to Redshift securely within the VPC

---

### Amazon Athena
**What it is:** SQL query engine that runs queries directly on S3 data.

**Why we use it:**
- **No servers**: Just write SQL, no infrastructure to manage
- **Pay per query**: Only pay for data scanned (~$5 per TB scanned)
- **Fast exploration**: Great for ad-hoc analysis before building full pipelines

**Example use case:**
```sql
SELECT customer_id, COUNT(*) as order_count
FROM "data_lake_db"."raw_sales"
WHERE date >= '2022-09-01'
GROUP BY customer_id;
```

**In our project:**
- Queries data cataloged by Glue
- Results stored in `athena-results` bucket

---

## 🗄️ Data Warehouse

### Amazon Redshift Serverless
**What it is:** A cloud data warehouse optimized for analytics queries.

**Why we use it instead of a regular database:**
- **Columnar storage**: Stores data by column (faster for analytics)
- **Massively parallel**: Runs queries across multiple nodes
- **Optimized for aggregations**: SUM, AVG, GROUP BY run very fast

**Serverless vs. Provisioned:**
- **Serverless**: Pay only when queries run (~$0.375/hour when active)
- **Provisioned**: Pay 24/7 even when idle (more expensive for learning)

**RPU (Redshift Processing Units):**
- Measure of compute capacity
- Minimum: 8 RPU (what we use)
- Auto-scales up during heavy queries, down when idle

**When to use Redshift:**
- Complex joins across large tables
- Aggregations over millions/billions of rows
- Business intelligence dashboards

**When to use Athena instead:**
- One-off exploratory queries
- Small datasets
- Don't want to load data into a warehouse

---

## 🔄 Orchestration

### Apache Airflow (on ECS)
**What it is:** A workflow orchestration tool that schedules and monitors data pipelines.

**Why we use it:**
- **DAGs (Directed Acyclic Graphs)**: Define pipelines as code
- **Scheduling**: Run jobs daily, hourly, or on custom schedules
- **Monitoring**: See which tasks succeeded/failed
- **Dependencies**: Task B runs only after Task A succeeds

**Example DAG:**
```
Extract from API → Load to S3 → Run Glue Crawler → Transform in Redshift
```

**Components:**
- **Webserver**: UI to view/trigger DAGs (accessible via browser)
- **Scheduler**: Monitors DAGs and triggers tasks on schedule
- **Executor**: Runs the actual tasks (we use LocalExecutor)
- **Metadata DB**: PostgreSQL database storing DAG run history

**Why on ECS instead of EC2:**
- No server management
- Auto-scaling
- Pay only for running containers

---

## ☁️ Compute Services

### Amazon ECS (Elastic Container Service) with Fargate
**What it is:** Runs Docker containers without managing servers.

**Why we use it:**
- **Serverless containers**: No EC2 instances to patch/maintain
- **Cost-effective**: Pay per second of container runtime
- **Scalable**: Can run 1 or 1000 containers

**Fargate vs. EC2 launch type:**
- **Fargate**: AWS manages the servers (easier, slightly more expensive)
- **EC2**: You manage the servers (cheaper, more work)

**In our project:**
- Runs Airflow webserver container
- Runs Airflow scheduler container
- Runs DAG sync task (copies DAGs from S3 to EFS every 5 minutes)

---

### Amazon RDS (Relational Database Service) - PostgreSQL
**What it is:** Managed PostgreSQL database.

**Why we use it:**
- Airflow needs a database to store metadata (DAG runs, task states, logs)
- RDS handles backups, patching, high availability

**db.t3.micro:**
- Smallest instance type
- Free-tier eligible (750 hours/month free for 12 months)
- 1 vCPU, 1 GB RAM (enough for Airflow metadata)

---

## 🌐 Networking Services

### Amazon VPC (Virtual Private Cloud)
**What it is:** Your own isolated network in AWS.

**Why we use it:**
- **Security**: Keep databases private (not accessible from internet)
- **Control**: Define which services can talk to each other

**Components:**

#### Subnets
- **Public subnets**: Have internet access (for ALB, NAT Gateway)
- **Private subnets**: No direct internet (for RDS, Redshift, EFS)

#### Internet Gateway (IGW)
- Allows public subnets to access the internet

#### NAT Gateway
- Allows private subnets to access internet (for downloading packages)
- **Cost warning**: ~$0.045/hour = ~$32/month (biggest always-on cost)

#### Route Tables
- Define where network traffic goes
- Public route: 0.0.0.0/0 → Internet Gateway
- Private route: 0.0.0.0/0 → NAT Gateway

---

### Application Load Balancer (ALB)
**What it is:** Distributes incoming web traffic across multiple containers.

**Why we use it:**
- Provides a single URL for Airflow UI
- Health checks: Restarts unhealthy containers
- Can scale to multiple webserver containers if needed

---

### Security Groups
**What they are:** Virtual firewalls controlling inbound/outbound traffic.

**In our project:**
- **Airflow SG**: Allows port 8080 (Airflow UI)
- **Database SG**: Allows port 5432 from Airflow containers only
- **Redshift SG**: Allows port 5439 from Glue and Airflow
- **ALB SG**: Allows port 80 from internet
- **EFS SG**: Allows port 2049 (NFS) from ECS tasks

---

## 📅 Automation Services

### Amazon EventBridge
**What it is:** Serverless event bus for scheduling tasks.

**Why we use it:**
- Triggers the DAG sync task every 5 minutes
- Alternative to cron jobs (no server needed)

**In our project:**
- Rule: `rate(5 minutes)`
- Target: ECS task (dag-sync)
- Action: Syncs S3 DAGs to EFS

---

## 📊 Monitoring

### Amazon CloudWatch Logs
**What it is:** Centralized logging service.

**Why we use it:**
- All container logs go here (Airflow webserver, scheduler, DAG sync)
- Searchable and filterable
- Retention: 7 days (to save costs)

**How to view logs:**
```bash
aws logs tail /aws/ecs/your-project-airflow-webserver --follow
```

---

## 🔐 Security & Access

### IAM (Identity and Access Management)
**What it is:** Controls who/what can access AWS resources.

**Roles we created:**

1. **Glue Service Role**: Allows Glue to read S3 and write to Glue Catalog
2. **Redshift Service Role**: Allows Redshift to read from S3
3. **Airflow Execution Role**: Allows ECS to pull container images and write logs
4. **Airflow Task Role**: Allows Airflow containers to access S3, Glue, Redshift
5. **DAG Sync Task Role**: Allows DAG sync to read S3 and write to EFS
6. **EventBridge Execution Role**: Allows EventBridge to trigger ECS tasks

**Principle of Least Privilege**: Each role has only the permissions it needs.

---

## 💰 Cost Breakdown

| Service | Configuration | Monthly Cost (Estimate) |
|---------|--------------|-------------------------|
| **NAT Gateway** | 1x + data transfer | ~$32 + data |
| **RDS PostgreSQL** | db.t3.micro, 20GB | Free tier / ~$15 |
| **ECS Fargate** | 2 tasks × 0.5 vCPU | ~$22 |
| **Redshift Serverless** | 8 RPU, 10 hrs/week | ~$15 |
| **ALB** | 1x | ~$16 |
| **EFS** | 1GB | ~$0.30 |
| **S3** | 10GB | ~$0.23 |
| **CloudWatch Logs** | 1GB | ~$0.50 |
| **Total** | | **~$100-120/month** |

**Cost-saving tips:**
- Run `terraform destroy` when not using (keeps code, deletes infrastructure)
- Use Athena instead of Redshift for small queries
- Reduce NAT Gateway usage (biggest cost)

---

## 🎯 Data Flow Summary

```
1. Upload CSV/JSON → S3 (raw/)
2. Glue Crawler → Scans S3 → Creates tables in Glue Catalog
3. Athena → Queries S3 data using Glue Catalog
4. Airflow DAG → Orchestrates:
   a. Glue Job → Transforms data → Writes to S3 (bronze/, silver/, gold/)
   b. COPY command → Loads data into Redshift
   c. Redshift SQL → Aggregates data
5. BI Tool (Tableau/PowerBI) → Connects to Redshift → Creates dashboards
```

---

## 📚 Learning Resources

- **AWS Free Tier**: https://aws.amazon.com/free/
- **Airflow Documentation**: https://airflow.apache.org/docs/
- **Glue Tutorial**: https://docs.aws.amazon.com/glue/latest/dg/tutorial-add-crawler.html
- **Redshift Best Practices**: https://docs.aws.amazon.com/redshift/latest/dg/best-practices.html

---

**Next Steps:**
1. Deploy the infrastructure (`terraform apply`)
2. Explore each service in the AWS Console
3. Run sample queries in Athena
4. Create your first Airflow DAG
5. Load data into Redshift and run analytics queries

