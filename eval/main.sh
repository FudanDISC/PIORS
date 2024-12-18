#!/bin/bash

FILE_PATH="sfmss/data/emr/emr_example.json"  
PATIENT_PATH="sfmss/data/patient_simulate/patient_setting.json"
OUTPUT_DIR="results/eval_test"
FAIL_ID_PATH=""
IGNORE_ID_PATH=""
CONFIG_PATH="eval/config/eval_model_config.json"
PATIENT_PERSONALITY_PATH="sfmss/data/patient_simulate/bigfive_dataset.csv"
SFMSS_PIPELINE='false'
EVAL='true'
MAX_NUM=7
LOG_FILE="${OUTPUT_DIR}/output.log"

EVAL_DIR="results/eval_test" 
JUDGER_CONFIG_PATH="eval/config/judger_config.json"
EMR_PATH="sfmss/data/emr/emr_example.json"
EVAL_OUTPUT="${EVAL_DIR}/eval_result"
EVAL_LOG_FILE="${EVAL_OUTPUT}/output.log"

if [ ! -d "$OUTPUT_DIR" ]; then
  mkdir -p "$OUTPUT_DIR"
  echo "Created output directory: $OUTPUT_DIR"
fi

echo "Running dialogue generation.py..."
python sfmss/workflow/dialogue_construct.py \
  --file_path "$FILE_PATH" \
  --patient_path "$PATIENT_PATH" \
  --output_dir "$OUTPUT_DIR" \
  --fail_id_path "$FAIL_ID_PATH" \
  --ignore_id_path "$IGNORE_ID_PATH" \
  --config_path "$CONFIG_PATH" \
  --max_example $MAX_NUM \
  --sfmss_nurse_pipeline "$SFMSS_PIPELINE" \
  --eval "$EVAL" \
  --sample \
  --patient_personality_path "$PATIENT_PERSONALITY_PATH" >> "$LOG_FILE" 2>&1

if [ $? -ne 0 ]; then
  echo "Error: Dialogue generation failed. Check the log file: $LOG_FILE"
  exit 1
fi
echo "Completed dialogue generation successfully."

if [ ! -d "$EVAL_OUTPUT" ]; then
  mkdir -p "$EVAL_OUTPUT"
  echo "Created eval output directory: $EVAL_OUTPUT"
fi

echo "Starting automatic evalution..."
python eval/pipeline/auto_eval.py \
  --eval_dir "$EVAL_DIR" \
  --emr_path "$EMR_PATH" \
  --config_path "$JUDGER_CONFIG_PATH" >> "$EVAL_LOG_FILE" 2>&1

if [ $? -ne 0 ]; then
  echo "Error: Automatic evalution failed. Check the log file: $EVAL_LOG_FILE"
  exit 1
fi
echo "Completed automatic evalution successfully."

echo "All steps completed successfully. Results are in $OUTPUT_DIR and $EVAL_OUTPUT."
