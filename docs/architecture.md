# E-Commerce Data Pipeline - Architecture Documentation

## Introduction

Hey! This document walks you through how our e-commerce data pipeline works under the hood. We've built a production-grade system that takes raw data, cleans it up, validates it, and makes it ready for business intelligence. Think of it as a three-stage factory: raw materials come in, we refine them, and out comes beautiful, actionable data.

## Quick Overview

Our pipeline is built on three main layers:

1. **Staging** - Where raw data lands (no questions asked)
2. **Production** - Where we clean and validate everything
3. **Warehouse** - Where the data gets transformed into a format that's perfect for analytics and dashboards

The whole thing runs automatically, checks data quality along the way, and generates reports so you know exactly what happened.

**What makes this cool:**
- Generates realistic test data on the fly
- Automatically catches data problems (bad emails, weird numbers, missing values)
- Organizes data into a star schema that dashboards love
- Runs on a schedule without you lifting a finger
- Everything's containerized, so it runs the same way everywhere
- Has solid test coverage (80%+ of the code is tested)

---

## How the Three Layers Work

### Layer 1: The Staging Layer
*"Just dump the raw stuff here"*

This is where all the raw data comes in, fresh from the source. We don't validate or clean anything here - we just want to land the data as fast as possible.

**What happens here:**
- Raw CSV files get loaded into tables
- We track when each load happened (timestamps)
- Data is stored with minimal constraints
- If you reload, we clear out the old data first (idempotent)
- We use batch loading to make it fast

**The tables:**
- `staging.customers` - Customer info
- `staging.products` - Product catalog
- `staging.transactions` - Sales transactions
- `staging.transaction_items` - Individual line items per transaction

### Layer 2: The Production Layer
*"Clean it up, follow the rules"*

This is where the real work happens. We take that raw data, clean it up, check it for problems, and make sure everything follows our business rules.

**What we do:**
- Normalize text (trim whitespace, fix spacing)
- Standardize emails (lowercase, validate format)
- Fix phone numbers (remove special characters)
- Check that prices are valid (positive, cost ≤ price)
- Make sure quantities make sense (positive numbers)
- Verify all references are correct (customer IDs exist, etc.)
- Structure everything in 3rd normal form (3NF) for consistency

**Quality checks we run:**
1. **Completeness** - Are required fields filled in? (no NULLs where they shouldn't be)
2. **Uniqueness** - Are there duplicate IDs? (each ID should be unique)
3. **Validity** - Is the data in the right format? (valid emails, positive prices)
4. **Consistency** - Does the data make sense together? (line_total = qty × price)
5. **Referential Integrity** - Do all the relationships check out? (all customer IDs actually exist)

We give everything a quality score out of 100, with weights:
- Completeness: 25%
- Uniqueness: 20%
- Validity: 20%
- Consistency: 20%
- Referential Integrity: 15%

### Layer 3: The Warehouse Layer
*"Organize it for analytics"*

This is where we reshape the data into a star schema - basically, dimensions around a central fact table. This structure is perfect for dashboards and analytical queries because it's denormalized just right.

**The dimensions (reference tables):**
- **dim_customers** - Who made the purchases (with history tracking)
- **dim_products** - What was sold (with history tracking)
- **dim_date** - When it happened (year, quarter, month, day of week, etc.)
- **dim_payment_method** - How they paid (Credit Card, UPI, etc.)
- **dim_transaction_status** - Was it successful? (Completed, Pending, Failed)

**The fact table:**
- **fact_sales** - The transactions themselves, with links to all the dimensions

**The aggregates (pre-calculated summaries):**
- **agg_daily_sales** - Revenue by day
- **agg_product_performance** - How each product is selling
- **agg_customer_metrics** - Customer spending patterns

We use something called "SCD Type 2" for customers and products. What that means is: we keep history. If a customer's email changes, we don't delete the old one - we mark it as old and add a new one. This way, reports from the past still make sense.

---

## The Data Journey

Here's what happens step by step:

Step 1: GENERATE DATA
Create realistic e-commerce data (customers, products, sales)
↓
Step 2: STAGE IT
Load raw data into staging tables
↓
Step 3: QUALITY CHECK
Run data quality validations
↓
Step 4: TRANSFORM
Clean, validate, and load to production
↓
Step 5: BUILD WAREHOUSE
Create dimensions and facts from production data
↓
Step 6: AGGREGATE
Create summary tables for dashboards
↓
Step 7: VISUALIZE
Build dashboards and run analytics queries


If anything fails along the way, the pipeline stops and tells you exactly what went wrong.

---

## Database Schemas Explained

### Staging Schema (Raw Landing Zone)
Think of this like a messy inbox:
- No constraints (anything goes)
- Just basic indexes for speed
- Load timestamps so you know when data arrived
- Tables get truncated on each reload

### Production Schema (Clean & Validated)
This is like a filing cabinet - everything's organized:
- 3rd Normal Form (3NF) - data is organized efficiently
- Every table has a primary key
- Foreign keys connect related tables
- Domain constraints (prices > 0, emails have @, etc.)
- Strategic indexes on columns you query a lot (dates, status, email)

### Warehouse Schema (Analytics-Ready)
This is designed for dashboards to be fast:
- Star schema (facts in the middle, dimensions around)
- Denormalized (some data repeated for speed)
- Surrogate keys (system-generated IDs)
- Aggregate tables for dashboard performance
- History tracking with effective dates

---

## Tech Stack

| What | How | Why |
|------|-----|-----|
| Data Generation | Python + Faker | Creates realistic test data |
| ETL | Python + psycopg2 | Orchestrates the pipeline |
| Database | PostgreSQL | Reliable, open-source, perfect for this |
| Scheduling | APScheduler | Runs the pipeline on a schedule |
| Quality Checks | Python + SQL | Catches data problems early |
| Analytics | SQL | Advanced queries and reporting |
| Dashboards | Tableau or Power BI | Pretty visualizations |
| Containers | Docker | Same environment everywhere |
| CI/CD | GitHub Actions | Auto-tests on every commit |
| Testing | pytest | Makes sure nothing breaks |
| Config | YAML | Easy to adjust without coding |
| Logging | Python logging | Tracks what happened when |

---

## Key Components

### The Orchestrator (`scripts/pipeline_orchestration.py`)
This is the conductor of the orchestra. It:
- Runs each phase in order
- Stops if something critical fails
- Logs everything
- Generates JSON reports
- Tells you how long it took

### The Scheduler (`scripts/scheduler.py`)
This keeps things running automatically:
- Uses cron expressions (runs at specific times)
- Executes the orchestrator on schedule
- Logs to a separate file
- Can be turned on/off in config

### The Monitor (`scripts/monitoring/pipeline_monitor.py`)
This is your health check:
- Counts rows in each table
- Checks if data is fresh
- Validates quality metrics
- Spots problems early
- Generates a system health report

### Data Quality Framework
Checks five dimensions of data quality:
1. **Completeness** - No missing values where they matter
2. **Uniqueness** - No duplicate IDs
3. **Validity** - Data is in the right format
4. **Consistency** - Related data makes sense together
5. **Referential Integrity** - All relationships are valid

---

## Design Decisions We Made

**Three-Tier Architecture**
Why? Separation of concerns. Staging is for speed, production is for correctness, warehouse is for analytics. Each has a different job.

**Idempotent Operations**
Why? So you can run the pipeline multiple times and get the same result. No duplicates, no weird side effects.

**SCD Type 2 for Dimensions**
Why? We wanted to keep history. If a customer moves cities, you want to know both the old and new address for reporting.

**Star Schema in Warehouse**
Why? Dashboards query a lot of rows really fast. The star schema is denormalized (which normally you'd avoid) but it's perfect for analytics.

**Config in YAML**
Why? Because changing code is scary. Config files let people tweak behavior without touching Python.

**Batch Processing**
Why? Loading a million rows one at a time is slow. Loading them in chunks is faster and uses less memory.

**Comprehensive Logging**
Why? When something breaks at 2 AM, you need to know what happened. Logging saves lives.

---

## Security & Speed

### Keeping Things Safe
- ✅ Database passwords go in `.env`, never in code
- ✅ Connections time out so nothing hangs forever
- ✅ All SQL is parameterized (no SQL injection)
- ✅ Data relationships are enforced by constraints
- ✅ Everything gets logged (audit trail)
- ✅ Connection pooling prevents exhaustion

### Making Things Fast
- **Indexes** on columns you search (foreign keys, dates, status)
- **Batch loading** instead of one row at a time
- **Connection pooling** so you don't create new connections constantly
- **Aggregate tables** pre-calculated for dashboards
- **Denormalized warehouse** so joins are simple
- **Surrogate keys** for fast joins
- Ready for **partitioning** if you need it (split by date, etc.)

### Scaling Up
If you need to handle more data:
- Run multiple workers in parallel
- Increase batch sizes
- Partition warehouse by date
- Archive old data to separate tables
- Create materialized views for complex aggregations

---

## Where Your Data Goes

---

## What We Monitor

We track:
- How many rows in each table
- When the last load happened (freshness)
- How long the pipeline took
- Quality scores over time
- Any broken relationships
- Percentage of NULL values
- Whether each phase succeeded

**Reports you get:**
- `pipeline_execution_report.json` - Did each phase work?
- `monitoring_report.json` - Performance metrics
- `quality_report.json` - Data quality scores
- `transformation_summary.json` - How many rows moved where
- `system_monitoring_report.json` - Overall health

---

## If Things Go Wrong

**Backup & Recovery:**
- Daily database backups
- Raw CSV exports
- All reports saved
- Code versioned in Git

**To recover:**
1. Restore the database from backup
2. Re-ingest raw data if needed
3. Re-transform staging → production
4. Re-load warehouse
5. Run quality checks to verify

---

## What's Next?

Future stuff we might add:
- Real-time streaming (Kafka)
- Big data processing (Spark)
- Incremental loads (CDC)
- Hide sensitive data (PII masking)
- Machine learning pipelines
- Deploy to multiple clouds
- Live dashboards
- Auto-detect weird data

---

## Terms You Might Hear

| Term | What It Means |
|------|---------------|
| **SCD Type 2** | Keep history - mark old records as old, add new ones |
| **Star Schema** | Facts in the middle, dimensions around (like a star) |
| **Conformed Dimension** | Same dimension used in multiple fact tables |
| **Surrogate Key** | System-generated ID (not from business) |
| **3NF** | Organized in a way that avoids data duplication |
| **Idempotent** | Run it once or 10 times, get the same result |
| **ACID** | Transactions are Atomic, Consistent, Isolated, Durable |
| **Slowly Changing** | Data that changes over time (like addresses) |
| **Batch Loading** | Load data in chunks, not one row at a time |

