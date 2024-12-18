# Automatic Evluation

The evluation pipeline includes two parts: dialogue simulation and quality evaluation. 
- [`main.sh`](main.sh) runs the whole pipeline
- [`run_dialogue_simulation.sh`](pipeline/run_dialogue_simulation.sh) performs only the dialogue simulation
- [`run_autoeval.sh`](pipeline/run_autoeval.sh) performs only the quality evaluation.

To evaluate different models, modify `Nurse` in [eval_model_config](config/eval_model_config.json). To use your custom dataset, update `FILE_PATH` and `EMR_PATH` in [main.sh](main.sh). The required data format can be found in [SFMSS Data](../sfmss/README.md#Data).

When comparing the performance of different models, we strongly recommend removing `--sample` in [main.sh](main.sh) and running patient sampling first. This ensures the same patient simulation settings, making the results comparable. (Remember to update the `FILE_PATH` to the new path containing records with patient settings.)
```bash
bash sfmss/workflow/run_patient_sample.sh
bash main.sh
```

The Folder [`result`](eval/result) contains all evaluation results presented in the paper, including both automatic and human evaluation results.

