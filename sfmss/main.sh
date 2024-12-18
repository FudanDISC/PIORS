#!/bin/bash

FILE_PATH="sfmss/data/emr/emr_example.json"
OUTPUT_PATH="sfmss/data/emr/emr_example_wp.json"
PATIENT_PATH="sfmss/data/patient_simulate/patient_setting.json"
PATIENT_PERSONALITY_PATH="sfmss/data/patient_simulate/bigfive_dataset.csv"
CONFIG_PATH="sfmss/config/agent_config.json"
OUTPUT_DIR="results/sfmss_test"
FAIL_ID_PATH=""
IGNORE_ID_PATH=""
MAX_NUM=7

LOG_FILE="${OUTPUT_DIR}/output.log"

echo "Sampling patient setting from real-world distribution....."
python sfmss/workflow/patient_sample.py \
    --file_path "$FILE_PATH" \
    --output_path "$OUTPUT_PATH" \
    --patient_path "$PATIENT_PATH" \
    --patient_personality_path "$PATIENT_PERSONALITY_PATH"

if [ $? -ne 0 ]; then
    echo "Error: Failed to execute patient sampling."
    exit 1
fi
echo "Patient sampling completed successfully."

FILE_PATH="$OUTPUT_PATH"

if [ ! -d "$OUTPUT_DIR" ]; then
    mkdir -p "$OUTPUT_DIR"
    echo "Created output directory: $OUTPUT_DIR"
fi

echo "Running dialogue simulation.py..."
python sfmss/workflow/dialogue_construct.py \
    --file_path "$FILE_PATH" \
    --patient_path "$PATIENT_PATH" \
    --output_dir "$OUTPUT_DIR" \
    --fail_id_path "$FAIL_ID_PATH" \
    --ignore_id_path "$IGNORE_ID_PATH" \
    --config_path "$CONFIG_PATH" \
    --max_example $MAX_NUM \
    --patient_personality_path "$PATIENT_PERSONALITY_PATH" >> "$LOG_FILE" 2>&1

if [ $? -ne 0 ]; then
    echo "Error: Dialogue simualtion failed to execute. Check the log file: $LOG_FILE"
    exit 1
fi

echo "Dialogue simulation completed successfully. Results are in $OUTPUT_DIR."
