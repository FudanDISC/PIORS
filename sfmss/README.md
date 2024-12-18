# SFMSS
[`main.sh`](main.sh) first samples the patient simulation settings, and then generate outpatient reception dialogues between patients and nurses. 


- [`run_patient_sample.sh`](workflow/run_patient_sample.sh) samples the Big Five personality traits and demographic characteristics from real-world distributions, and combines the patient simulation settings with medical records.

- [`run_dialogue_construct.sh`](workflow/run_dialogue_construct.sh) simualtes the outpatient reception dialogues based on the medical records **with patient simulation settings**, so you should run patient sampling first.

If you want to simulate dialogues without sample patient setting beforehand, you can add `--sample` flag in [run_dialogue_construct.sh](workflow/run_dialogue_construct.sh) is also a choice. However, running patient sampling first is recommended to ensure reproducibility.
```bash 
python sfmss/workflow/dialogue_construct.py \
  --file_path "$FILE_PATH" \
  --patient_path "$PATIENT_PATH" \
  --output_dir "$OUTPUT_DIR" \
  --fail_id_path "$FAIL_ID_PATH" \
  --ignore_id_path "$IGNORE_ID_PATH" \
  --config_path "$CONFIG_PATH" \
  --max_example $MAX_NUM \
  --sample \
  --patient_personality_path "$PATIENT_PERSONALITY_PATH" 
```

## Data 
If you want to use a custom dataset: 
- Make sure the dataset is a JSON file
- Update `FILE_PATH` in [main.sh](main.sh) or [run_dialogue_construct.sh](workflow/run_dialogue_construct.sh) to your dataset path.
- Confirm it has the following structure:
```json
{
        "auxiliary_examination": "Additional diagnostic tests or procedures that are used to support or confirm a diagnosis. ",
        "outpatient_number": "INT, The unique id of an outpatient medical record.",
        "chief_complaint": "The primary reason or main symptom for which a patient seeks medical care.",
        "physician_signature": " The official signature provided by the attending doctor who is responsible for the patient’s care. This field has been anonymized. ",
        "preliminary_diagnosis": "The initial assessment or hypothesis made by doctors.",
        "drug_allergy_history": "A patient’s previous allergic reactions to medications",
        "treatment_opinion": "The professional recommendations or suggestions provided by a doctor for the patient.",
        "present_illness_history": "A detailed account of the patient’s current symptoms and medical condition.",
        "physical_examination": "The systematic evaluation of a patient’s body by the doctor",
        "notes": "Specially notation given by doctors. ",
        "past_history": " A comprehensive summary of a patient’s previous health conditions, medical treatments, surgeries, hospitalizations, chronic illnesses, allergies, and medications. It may also include significant family medical history and lifestyle factors like smoking or alcohol use. ",
        "department": "The specific unit or division within the hospital where a patient is treated.",
        "age": "The age of the patient.",
        "name": "The anonymized name of the patient.",
        "gender": "The gender of the patient.",
        "patient_id": "The unique ID to identify the patient.",
        "visit_date": "The registration time of the patient’s current visit."
    }
```

## Other Medical Scenarios
The SFMSS framework is not limited to outpatient reception; it can also simulate other medical scenarios with minor modifications.

- For follow-up visits simulation, add `--followup` flag in [run_dialogue_construct.sh](workflow/run_dialogue_construct.sh).

```bash 
python sfmss/workflow/dialogue_construct.py\
  --file_path "$FILE_PATH" \
  --patient_path "$PATIENT_PATH" \
  --output_dir "$OUTPUT_DIR" \
  --fail_id_path "$FAIL_ID_PATH" \
  --ignore_id_path "$IGNORE_ID_PATH" \
  --config_path "$CONFIG_PATH" \
  --max_example $MAX_NUM \
  --followup \
  --patient_personality_path "$PATIENT_PERSONALITY_PATH" 
```

To align SFMSS with other medical scenarios, you can modify the following files as needed: [`system_prompt.py`](workflow/system_prompt.py), [`json_class.py`](workflow/json_class.py). Some corresponding modifications may need to be made in [`agents.py`](workflow/agents.py) and [`workflow.py`](workflow/workflow.py).