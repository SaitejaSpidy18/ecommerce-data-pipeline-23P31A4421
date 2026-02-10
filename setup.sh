#!/usr/bin/env bash
set -euo pipefail

echo "=== E-Commerce Data Pipeline - Environment Setup ==="

# 1. Check prerequisites
echo "[1/6] Checking prerequisites..."

command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not found. Please install Python 3.8+."; exit 1; }
command -v pip3 >/dev/null 2>&1 || { echo "pip3 is required but not found. Please install pip for Python 3."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not found. Please install Docker Desktop."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "docker-compose is required but not found. Please install Docker Compose."; exit 1; }

python3 --version
pip3 --version
docker --version
docker-compose --version

# 2. Create Python virtual environment
echo "[2/6] Creating Python virtual environment (./.venv)..."

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# Activate venv
# shellcheck disable=SC1091
source .venv/bin/activate

# 3. Install Python dependencies
echo "[3/6] Installing Python dependencies from requirements.txt..."

if [ ! -f "requirements.txt" ]; then
  echo "requirements.txt not found in project root. Please create it before running setup."
  exit 1
fi

pip install --upgrade pip
pip install -r requirements.txt

# 4. Prepare config and env files
echo "[4/6] Preparing config and environment files..."

if [ ! -d "config" ]; then
  mkdir -p config
fi

if [ ! -f "config/config.yaml" ]; then
  echo "config/config.yaml not found. Creating a template..."
  cat <<EOF > config/config.yaml
database:
  host: "\${DB_HOST:-localhost}"
  port: "\${DB_PORT:-5432}"
  name: "\${DB_NAME:-ecommercedb}"
  user: "\${DB_USER:-admin}"
  password: "\${DB_PASSWORD:-password}"

data_generation:
  num_customers: 1000
  num_products: 500
  num_transactions: 10000
  min_transaction_items: 15000
  max_transaction_items: 25000
  start_date: "2024-01-01"
  end_date: "2024-12-31"

pipeline:
  batch_size: 1000
  log_level: "INFO"
  max_retries: 3
  retry_backoff_seconds: 2

scheduler:
  enabled: false
  daily_run_time: "02:00"  # HH:MM 24-hr format

bi_tool:
  tool: "tableau"  # or "powerbi"
EOF
  echo "Created default config/config.yaml. Please review and adjust as needed."
fi

if [ ! -f ".env.example" ]; then
  echo ".env.example not found. Creating a template..."
  cat <<EOF > .env.example
# Database configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ecommercedb
DB_USER=admin
DB_PASSWORD=change_me

# Environment
APP_ENV=local
LOG_LEVEL=INFO
EOF
  echo "Created .env.example. Copy to .env and fill in real values."
fi

if [ ! -f ".env" ]; then
  echo ".env file not found. Creating from .env.example (edit credentials after this step)..."
  cp .env.example .env
fi

# 5. Start Docker services (PostgreSQL + pipeline)
echo "[5/6] Starting Docker services with docker-compose..."

if [ ! -f "docker/docker-compose.yml" ]; then
  echo "docker/docker-compose.yml not found. Please create Docker Compose config before running setup."
  exit 1
fi

docker-compose -f docker/docker-compose.yml up -d

echo "Waiting for PostgreSQL to become healthy..."
sleep 15

# 6. Initialize database schemas
echo "[6/6] Initializing database schemas..."

if command -v psql >/dev/null 2>&1; then
  DB_HOST="${DB_HOST:-localhost}"
  DB_PORT="${DB_PORT:-5432}"
  DB_NAME="${DB_NAME:-ecommercedb}"
  DB_USER="${DB_USER:-admin}"

  if [ -f "sql/ddl/create_staging_schema.sql" ]; then
    echo "Applying sql/ddl/create_staging_schema.sql..."
    PGPASSWORD="${DB_PASSWORD:-password}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "sql/ddl/create_staging_schema.sql"
  else
    echo "WARNING: sql/ddl/create_staging_schema.sql not found. Skipping staging schema creation."
  fi

  if [ -f "sql/ddl/create_production_schema.sql" ]; then
    echo "Applying sql/ddl/create_production_schema.sql..."
    PGPASSWORD="${DB_PASSWORD:-password}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "sql/ddl/create_production_schema.sql"
  else
    echo "WARNING: sql/ddl/create_production_schema.sql not found. Skipping production schema creation."
  fi

  if [ -f "sql/ddl/create_warehouse_schema.sql" ]; then
    echo "Applying sql/ddl/create_warehouse_schema.sql..."
    PGPASSWORD="${DB_PASSWORD:-password}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "sql/ddl/create_warehouse_schema.sql"
  else
    echo "WARNING: sql/ddl/create_warehouse_schema.sql not found. Skipping warehouse schema creation."
  fi
else
  echo "psql not found on host. Database schemas will be created by Postgres init scripts or separately."
fi

echo "=== Setup completed successfully. ==="
echo "Next steps:"
echo "1. Activate venv: source .venv/bin/activate"
echo "2. Run pipeline: python scripts/pipeline/orchestrator.py  (or your main entrypoint)"
