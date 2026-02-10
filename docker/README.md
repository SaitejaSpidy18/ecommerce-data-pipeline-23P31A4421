# Docker Deployment Guide

## Overview

This guide explains how to run the e-commerce data pipeline using Docker and Docker Compose. Docker ensures that the pipeline runs the same way on your laptop, on your server, or in the cloud. No more "it works on my machine" problems.

## Prerequisites

Before you start, you need:

- Docker installed on your system
- Docker Compose installed
- At least 4GB of RAM available
- At least 10GB of disk space for the database and data files

Download Docker Desktop from docker.com. It includes both Docker and Docker Compose.

## Quick Start

The fastest way to get running is:

docker-compose -f docker/docker-compose.yml up -d

This command starts all the services in the background. The first run takes a few minutes as Docker downloads images and sets everything up.

Check if everything started correctly:

docker-compose -f docker/docker-compose.yml ps

You should see all services with status "Up".

## What Gets Started

When you run Docker Compose, it starts:

PostgreSQL Database
- Version 12
- Database name: ecommercedb
- User: admin
- Password: password
- Port: 5432 (on your machine)

Pipeline Application
- Python environment with all dependencies
- Ready to run the pipeline
- Mounted to your local scripts directory
- Port: 8000 (if API is added in future)

Volumes (Persistent Storage)
- postgres_data - Stores the database
- logs - Stores pipeline logs

## Running the Pipeline

Once services are started, run the pipeline:

docker-compose -f docker/docker-compose.yml exec pipeline python scripts/pipeline_orchestration.py

This command:
- Executes inside the running pipeline container
- Runs the full data pipeline
- Generates all reports
- Takes 2-5 minutes depending on data size

Watch the output. You will see each phase complete:
- Data Generation
- Data Ingestion
- Quality Checks
- Transformation
- Warehouse Load
- Analytics

## Stopping Services

When you are done:

docker-compose -f docker/docker-compose.yml down

This stops and removes all containers. Your database data is preserved in the postgres_data volume.

To stop without removing containers:

docker-compose -f docker/docker-compose.yml stop

To start them again:

docker-compose -f docker/docker-compose.yml start

## Viewing Logs

See what the pipeline is doing:

docker-compose -f docker/docker-compose.yml logs -f pipeline

The -f flag follows the logs in real-time. Press Ctrl+C to stop.

For database logs:

docker-compose -f docker/docker-compose.yml logs -f postgres

## Accessing the Database

Connect to PostgreSQL from your machine:

psql -h localhost -U admin -d ecommercedb

Password is "password". This works if you have psql installed locally.

Or use a GUI tool like pgAdmin, DBeaver, or DataGrip. Connect to:
- Host: localhost
- Port: 5432
- Username: admin
- Password: password
- Database: ecommercedb

## Viewing Reports

After the pipeline runs, check the generated reports:

On your machine
ls data/processed/

You should see:
- pipeline_execution_report.json
- quality_report.json
- transformation_summary.json
- monitoring_report.json
- ingestion_summary.json

View a report with:

cat data/processed/pipeline_execution_report.json

## Rebuilding Docker Images

If you change the Dockerfile or requirements.txt, rebuild the image:

docker-compose -f docker/docker-compose.yml build

Then start services again:

docker-compose -f docker/docker-compose.yml up -d

## Running Tests in Docker

Run the test suite inside the container:

docker-compose -f docker/docker-compose.yml exec pipeline pytest tests/ -v

View coverage report:

docker-compose -f docker/docker-compose.yml exec pipeline pytest tests/ --cov=scripts --cov-report=term-missing

## Environment Variables

The Docker Compose setup uses these environment variables. They are defined in docker-compose.yml:

DB_HOST=postgres (the service name, not localhost inside container)
DB_PORT=5432
DB_NAME=ecommercedb
DB_USER=admin
DB_PASSWORD=password
APP_ENV=docker
LOG_LEVEL=INFO

To override these, create a .env file in the root directory:

DB_HOST=postgres
DB_PORT=5432
DB_NAME=ecommercedb
DB_USER=admin
DB_PASSWORD=your_secure_password
APP_ENV=production
LOG_LEVEL=DEBUG

Docker Compose will load these variables automatically.

## Mounting Volumes

The setup mounts these directories:

Source on Your Machine maps to Container Path
./scripts maps to /app/scripts
./config maps to /app/config
./data maps to /app/data
./logs maps to /app/logs
./sql maps to /app/sql
./tests maps to /app/tests
postgres_data volume maps to /var/lib/postgresql/data

This means:
- Changes you make to scripts locally are reflected in the container immediately
- Logs and data generated in the container appear in your local folders
- Database data persists between container restarts

## Troubleshooting

Service fails to start:

Check logs:
docker-compose logs postgres

Common causes:
- Port 5432 already in use (change it in docker-compose.yml)
- Not enough disk space (clean up Docker: docker system prune)
- Corrupted database volume (remove and recreate: docker volume rm postgres_data)

Connection refused errors:

The pipeline container needs to wait for PostgreSQL to be ready. The compose file includes health checks and depends_on, so this should happen automatically. If it fails, wait a few seconds and try again:

docker-compose -f docker/docker-compose.yml exec pipeline python scripts/pipeline_orchestration.py

Out of memory errors:

Docker containers have memory limits. Increase Docker's memory allocation in Docker Desktop settings, or reduce batch sizes in config.yaml.

Database seems corrupted:

Stop services, remove the volume, and start fresh:

docker-compose -f docker/docker-compose.yml down
docker volume rm postgres_data
docker-compose -f docker/docker-compose.yml up -d

This destroys the database. Only do this if you can recreate the data.

## Performance Tips

Use host volumes instead of Docker volumes for better performance on macOS and Windows. The setup already does this.

Increase database cache in docker-compose.yml if you have plenty of RAM. Add this under postgres environment:

POSTGRES_INITDB_ARGS="-c shared_buffers=256MB -c effective_cache_size=1GB"

Use named volumes for database to avoid file system overhead. The setup already does this.

## Production Deployment

For production, modify docker-compose.yml:

1. Use a secure password, not "password"
2. Use a PostgreSQL image version that matches your production database
3. Add resource limits to prevent containers from consuming all resources
4. Use health checks to monitor services
5. Configure logging to send logs to a centralized system
6. Use environment-specific compose files like docker-compose.prod.yml

## Docker Networking

Services communicate by name within the Docker network. The pipeline connects to postgres using:
- hostname: postgres
- port: 5432

From your machine, you connect using:
- hostname: localhost
- port: 5432

The docker-compose.yml file creates a network that handles this mapping automatically.

## Cleanup

Remove all Docker resources for this project:

docker-compose -f docker/docker-compose.yml down -v

The -v flag removes all volumes, deleting the database. Use this to start fresh.

Remove just the containers but keep data:

docker-compose -f docker/docker-compose.yml down

Remove unused Docker resources across your system:

docker system prune -a

This frees up disk space. Use with caution.

## Next Steps

After getting comfortable with Docker:

1. Set up GitHub Actions to build and test in Docker automatically
2. Push images to Docker Hub for easier sharing
3. Deploy to Kubernetes for scaling to multiple machines
4. Use Docker Compose for development, Kubernetes for production

## Common Commands Reference

Start services in background:
docker-compose -f docker/docker-compose.yml up -d

Stop services:
docker-compose -f docker/docker-compose.yml down

View logs in real-time:
docker-compose -f docker/docker-compose.yml logs -f

Run pipeline:
docker-compose -f docker/docker-compose.yml exec pipeline python scripts/pipeline_orchestration.py

Run tests:
docker-compose -f docker/docker-compose.yml exec pipeline pytest tests/ -v

Connect to database:
docker-compose -f docker/docker-compose.yml exec postgres psql -U admin -d ecommercedb

Rebuild images:
docker-compose -f docker/docker-compose.yml build

Remove everything:
docker-compose -f docker/docker-compose.yml down -v

## Support

If you run into issues:

1. Check the Docker Compose logs
2. Verify Docker and Docker Compose are up to date
3. Ensure you have enough disk space and RAM
4. Try removing containers and starting fresh
5. Check the main README.md for additional help

