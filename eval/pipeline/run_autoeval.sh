#!/bin/bash

EVAL_DIR="results/eval_test" 
CONFIG_PATH="eval/config/judger_config.json"
EMR_PATH="sfmss/data/emr/emr_example.json"

EVAL_OUTPUT="${EVAL_DIR}/eval_result"
LOG_FILE="${EVAL_DIR}/eval_result/output.log"

if [ ! -d "$EVAL_OUTPUT" ]; then
  mkdir -p "$EVAL_OUTPUT"
  echo "Created eval output directory: $EVAL_OUTPUT"
fi

python eval/pipeline/auto_eval.py \
  --eval_dir "$EVAL_DIR" \
  --emr_path "$EMR_PATH" \
  --config_path "$CONFIG_PATH" >> "$LOG_FILE" 2>&1