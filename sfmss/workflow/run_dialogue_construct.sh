#!/bin/bash

FILE_PATH="sfmss/data/emr/emr_example_wp.json"   
PATIENT_PATH="sfmss/data/patient_simulate/patient_setting.json"
OUTPUT_DIR="results/sfmss_test_follow_up"
FAIL_ID_PATH=""
IGNORE_ID_PATH="" 
CONFIG_PATH="sfmss/config/agent_config.json"
PATIENT_PERSONALITY_PATH="sfmss/data/patient_simulate/bigfive_dataset.csv"
MAX_NUM=7

LOG_FILE="${OUTPUT_DIR}/output.log"

if [ ! -d "$OUTPUT_DIR" ]; then
  mkdir -p "$OUTPUT_DIR"
  echo "Created output directory: $OUTPUT_DIR"
fi

python sfmss/workflow/dialogue_construct.py\
  --file_path "$FILE_PATH" \
  --patient_path "$PATIENT_PATH" \
  --output_dir "$OUTPUT_DIR" \
  --fail_id_path "$FAIL_ID_PATH" \
  --ignore_id_path "$IGNORE_ID_PATH" \
  --config_path "$CONFIG_PATH" \
  --max_example $MAX_NUM \
  --patient_personality_path "$PATIENT_PERSONALITY_PATH" >> "$LOG_FILE" 2>&1
