#!/usr/bin/env bash

# Shell script using rsync to copy a dataset from a remote load generator (lg).
# Supported configuration via environment variables:
# * SB_DATA_SOURCE: a prefix to distinguish data from different load generators (default lg12)
# * SB_DATA_DIR: optionally override the data path directly (default data/lg12/raw)


# Source: https://stackoverflow.com/a/246128
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

DATA_SOURCE="${SB_DATA_SOURCE:-lg12}"
DEFAULT_DATA_DIR="${SCRIPT_DIR}/../data/${DATA_SOURCE}/raw"

SRC="ec2-user@${DATA_SOURCE}:/home/ec2-user/"
DEST="${SB_DATA_DIR:-"$DEFAULT_DATA_DIR"}"

# Copy all sb log directories but nothing else (i.e., ignore other repo content or logs)
# Optionally preview using: --dry-run
rsync -amhvzP --stats --exclude='sb-env' --exclude='.vscode-server' --exclude='.serverless' --exclude='.git' --exclude='node_modules' --include='logs/*/*' --include='*/' --exclude='*' "$SRC" "$DEST"
