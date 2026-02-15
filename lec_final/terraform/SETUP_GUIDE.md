# Terraform Infrastructure Setup Guide

## Prerequisites

1. **AWS CLI** configured with your IAM user credentials:
   ```bash
   aws configure
   # Enter: Access Key ID, Secret Access Key, Region: us-east-1, Output: json
   ```

2. **Terraform** >= 1.5.0 installed:
   ```bash
   # macOS
   brew install terraform
   # Linux
   sudo apt-get install -y terraform
   # Or download from https://developer.hashicorp.com/terraform/downloads
   ```

3. Verify setup:
   ```bash
   aws sts get-caller-identity
   terraform --version
   ```

## Cost Estimates & Free-Tier Notes

| Service | Configuration | Estimated Cost |
|---------|--------------|----------------|
| NAT Gateway | 1x (required for private subnets) | ~$0.045/hr + data |
| RDS PostgreSQL | db.t3.micro, 20GB | Free-tier eligible (750 hrs/mo) |
| ECS Fargate | 2 tasks × 0.5 vCPU, 1GB | ~$0.03/hr per task |
| Redshift Serverless | 8 RPU (min) | ~$0.375/hr **only when active** |
| ALB | 1x Application LB | ~$0.0225/hr |
| EFS | 2 file systems | ~$0.30/GB/mo (minimal usage) |
| S3 | 3 buckets | Negligible for small data |
| Elastic IP | 1x (for NAT) | Free when attached |

**⚠️ IMPORTANT**: Redshift Serverless charges only when queries run. The NAT Gateway
is the biggest always-on cost (~$1.08/day). **Tear down when not in use!**

**Estimated total**: ~$2-4/day when Airflow is running, much less when idle.

## Step 1: (Optional) Set Up Remote State Backend

For a learning project, local state is fine. Skip this step if you prefer simplicity.

```bash
# Create S3 bucket for Terraform state
aws s3 mb s3://YOUR_PROJECT_NAME-terraform-state --region us-east-1

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

Then uncomment the `backend "s3"` block in `main.tf` and update the bucket name.

## Step 2: Configure Variables

```bash
cd lec_final/terraform

# Copy the example and edit with your values
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars - CHANGE THE PASSWORDS!
# Redshift password must have: uppercase, lowercase, number (e.g., MyPass123!)
```

## Step 3: Initialize and Deploy

```bash
# Initialize Terraform (downloads providers)
terraform init

# Preview what will be created
terraform plan

# Deploy (type 'yes' when prompted) — takes 10-20 minutes
terraform apply
```

**Note**: RDS creation takes ~5-10 minutes. Redshift namespace takes ~3-5 minutes.

## Step 4: Upload Data to S3

After deployment, get the Data Lake bucket name from outputs:

```bash
# Get the bucket name
export DATA_LAKE_BUCKET=$(terraform output -raw data_lake_bucket_name)
echo "Data Lake Bucket: $DATA_LAKE_BUCKET"

# Upload all data files to the raw/ prefix
aws s3 cp --recursive ../data s3://$DATA_LAKE_BUCKET/raw
```

Verify the upload:
```bash
aws s3 ls s3://$DATA_LAKE_BUCKET/raw/ --recursive | head -20
```

## Step 5: Run the Glue Crawler

```bash
# Get the crawler name
export CRAWLER_NAME=$(terraform output -raw glue_crawler_name)

# Start the crawler
aws glue start-crawler --name $CRAWLER_NAME

# Check crawler status (wait ~5 minutes)
aws glue get-crawler --name $CRAWLER_NAME --query 'Crawler.State'
```

After the crawler completes, verify tables were created:
```bash
export GLUE_DB=$(terraform output -raw glue_database_name)
aws glue get-tables --database-name $GLUE_DB --query 'TableList[].Name'
```

You should see tables for `customers`, `sales`, and `user_profiles` under the `raw` prefix.

## Step 6: Upload DAGs to Airflow

```bash
export AIRFLOW_BUCKET=$(terraform output -raw airflow_bucket_name)

# Upload your DAG files
aws s3 cp your_dag_file.py s3://$AIRFLOW_BUCKET/dags/

# DAGs sync to EFS every 5 minutes via the scheduled ECS task
```

## Step 7: Access Airflow Web UI

```bash
echo "Airflow URL: $(terraform output -raw airflow_web_ui)"
```

Open the URL in your browser. Login with the credentials from `terraform.tfvars`.

## Step 8: Connect to Redshift

Access Redshift via the AWS Console:
1. Go to [Redshift Serverless](https://us-east-1.console.aws.amazon.com/redshiftv2/home?region=us-east-1#serverless-dashboard)
2. Click on your workgroup
3. Click "Query data" to open the query editor
4. Connect using the admin credentials from `terraform.tfvars`

