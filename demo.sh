#!/usr/bin/env bash
#
# demo.sh — one-command demo of the Meeting Follow-Through Agent
# =============================================================
# For judges / first-time users: this sets up an isolated virtual
# environment, installs dependencies, and runs the full end-to-end flow
# against the bundled sample transcripts.
#
# Prerequisites:
#   - Python 3.10+ available as `python3` (or set PYTHON=/path/to/python3.10+)
#   - AWS credentials with Amazon Bedrock access (Claude Sonnet 4 family)
#     provided via the environment or `aws configure`. Set AWS_REGION to a
#     region where Bedrock is enabled (e.g. us-east-1).
#
# Usage:
#   ./demo.sh
#   AWS_REGION=us-east-1 ./demo.sh
#   PYTHON=python3.12 ./demo.sh
#
set -euo pipefail

cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
VENV_DIR=".venv"

echo "==> Using interpreter: $($PYTHON --version 2>&1)"

# Enforce Python 3.10+ (Strands Agents SDK requirement).
if ! "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
  echo "ERROR: Python 3.10+ is required by the Strands Agents SDK." >&2
  echo "       Set PYTHON to a 3.10+ interpreter, e.g. PYTHON=python3.12 ./demo.sh" >&2
  exit 1
fi

# Create the virtual environment on first run.
if [ ! -d "$VENV_DIR" ]; then
  echo "==> Creating virtual environment in $VENV_DIR"
  "$PYTHON" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "==> Installing dependencies (strands-agents, python-dotenv)"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo "==> Region: ${AWS_REGION:-${AWS_DEFAULT_REGION:-<not set — using AWS default>}}"
echo "==> Running the Meeting Follow-Through Agent end-to-end..."
echo

python -u main.py "$@"
