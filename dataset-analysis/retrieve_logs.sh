#!/usr/bin/env bash

ALIAS=lg12

SRC="ec2-user@${ALIAS}:/home/ec2-user"
DEST="$HOME/Datasets/serverless-study/data/${ALIAS}"

# Copy all log directories but nothing else (i.e., ignore other repo content)
rsync -amhvzP --stats --include='logs/**' --include='*/' --include='exp*.py' --exclude='*' "$SRC" "$DEST"
