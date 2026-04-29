#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT=${ENV:-local}
export ENV="${ENVIRONMENT}"

uvicorn app.main:app --host 0.0.0.0 --port 8000

