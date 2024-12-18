FILE_PATH="sfmss/data/emr/emr_example.json"
OUTPUT_PATH="sfmss/data/emr/emr_example_wp.json"
PATIENT_PATH="sfmss/data/patient_simulate/patient_setting.json"
PATIENT_PERSONALITY_PATH="sfmss/data/patient_simulate/bigfive_dataset.csv"

python sfmss/workflow/patient_sample.py \
    --file_path "$FILE_PATH" \
    --output_path "$OUTPUT_PATH" \
    --patient_path "$PATIENT_PATH" \
    --patient_personality_path "$PATIENT_PERSONALITY_PATH"
