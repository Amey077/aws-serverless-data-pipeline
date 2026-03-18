# AWS Serverless Data Pipeline

An event-driven, serverless ETL pipeline that fetches a 2-million-row sales CSV (zipped) from an HTTPS endpoint, uncompresses it, converts to partitioned Parquet, archives the original, and exposes the data for querying via Amazon Athena.

---

## Architecture

```
[HTTPS URL]
     │
     ▼
┌──────────────────┐
│  retrieve        │  Downloads ZIP → uploads to raw_data/
└────────┬─────────┘
         │ S3 event (raw_data/*.zip)
         ├───────────────────────────────────────┐
         ▼                                       ▼
┌──────────────────┐                   ┌──────────────────┐
│  uncompress      │                   │  archive         │
│  Lambda          │                   │  Lambda          │
└────────┬─────────┘                   └──────────────────┘
Extracts CSV → processed_data/         Copies ZIP → Archive/
                                       Deletes from raw_data/
         │ S3 event (processed_data/*.csv)
         ▼
┌──────────────────┐
│  transform       │  Reads CSV with PyArrow
│  Lambda          │  Writes Parquet partitioned by Country
└────────┬─────────┘
         │
         ▼
  transformed_data/country=<X>/<country>.parquet
         │
         ▼
  AWS Glue Catalog ──► Amazon Athena
```

### S3 Prefix Layout

| Prefix | Content |
|--------|---------|
| `raw_data/{date}/2m_sales_records.zip` | Downloaded ZIP (temporary) |
| `processed_data/{date}/*.csv` | Extracted CSV |
| `Archive/{date}/2m_sales_records.zip` | Archived ZIP |
| `transformed_data/country=<X>/<X>.parquet` | Hive-partitioned Parquet |
| `lambda/` | Lambda deployment ZIPs |
| `athena-results/` | Athena query output |

---

## Lambda Functions

| Function | Trigger | What it does |
|----------|---------|-------------|
| `retrieve-data` | Manual / scheduled | Downloads ZIP from HTTPS, uploads to `raw_data/` |
| `uncompress-data` | S3 event on `raw_data/` | Extracts ZIP, uploads CSV to `processed_data/` |
| `archive-data` | S3 event on `raw_data/` | Copies ZIP to `Archive/`, deletes from `raw_data/` |
| `transform-data` | S3 event on `processed_data/` | Reads CSV via PyArrow, writes Parquet partitioned by `Country` |

---

## Infrastructure (CloudFormation)

Two stacks deployed in order:

| Stack | Template | Contains |
|-------|----------|---------|
| `aws-serverless-data-pipeline-s3` | `template.json` | S3 bucket, Glue database |
| `aws-serverless-data-pipeline-lambda` | `template_2.json` | IAM role, 4 Lambda functions, Lambda permissions, Glue table |

---

## CI/CD (GitHub Actions)

Pushes to `main` automatically:
1. Deploy `template.json` (S3 + Glue DB)
2. Package all 4 Lambda ZIPs (installs `requests` for retrieve, `pyarrow` for transform using `manylinux2014_x86_64` platform)
3. Upload ZIPs to S3
4. Deploy `template_2.json` (Lambdas + IAM + Glue table)
5. Update Lambda function code from S3

AWS credentials via OIDC: `arn:aws:iam::302432775392:role/GitHubActionsDeploymentRole`

---

## How to Trigger the Pipeline

Once deployed, invoke `retrieve-data` manually:

**AWS Console:** Lambda → `retrieve-data` → Test (any test event body)

**AWS CLI:**
```bash
aws lambda invoke --function-name retrieve-data /tmp/out.json --region us-east-1
cat /tmp/out.json
```

The chain then fires automatically via S3 events:
- `retrieve` uploads ZIP → S3 triggers `uncompress` + `archive` in parallel
- `uncompress` uploads CSV → S3 triggers `transform`

---

## Querying with Athena

1. Open **Athena Console** → select the `aws_data_pipeline_db` database
2. Run once after first pipeline execution to register partitions:
   ```sql
   MSCK REPAIR TABLE aws_data_pipeline_db.aws_data_table;
   ```
---

## Project Structure

```
aws-serverless-data-pipeline/
├── .github/
│   └── workflows/
│       ├── deploy.yml          # GitHub Actions CI/CD - deploy on push to main
│       └── delete.yml          # GitHub Actions - teardown/cleanup
├── cloudformation/
│   ├── template.json           # Stack 1: S3 bucket + Glue database
│   └── template_2.json         # Stack 2: Lambdas + IAM + Glue table
├── lambda/
│   ├── retrieve/
│   │   └── retrieve.py         # Downloads ZIP from HTTPS
│   ├── uncompress/
│   │   └── uncompress.py       # Extracts ZIP → CSV
│   ├── archive/
│   │   └── archive.py          # Copies ZIP to Archive/, deletes original
│   └── transform/
│       └── transform.py        # CSV → Parquet partitioned by Country
├── tests/
│   ├── test_archive.py         # Unit tests for archive Lambda
│   └── test_retrieve.py        # Unit tests for retrieve Lambda
└── README.md
```

---

## What I would have done if I had more time

| Area | Improvement |
|------|------------|
| **S3 notifications** | Add S3 event triggers into CloudFormation (`NotificationConfiguration`) instead of manually |
| **Streaming download** | `retrieve` currently loads the full ZIP into memory — use chunked streaming to avoid memory error on large files |
| **Column normalisation** | `transform` uses raw CSV column names with spaces; normalise to lowercase underscores for cleaner Athena queries |
| **Error handling** | Dead letter queues (SQS/SNS) on each Lambda for failed event notifications |
| **Step Functions** | Replace S3 event chaining with an explicit state machine for visibility and retries |
| **Observability** | CloudWatch Alarms + SNS alerts on Lambda errors |
| **Data quality** | Row count / null rate validation step before writing Parquet |
| **Glue Crawler** | Automate partition discovery instead of manual `MSCK REPAIR TABLE` |
| **Unit tests** | Mock `boto3` / `requests` with `moto` and `responses` for local testing |
| **Scheduled runs** | EventBridge rule to run the pipeline on a schedule |