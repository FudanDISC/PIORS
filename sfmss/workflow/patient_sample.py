import sys
import os
sys.path.append(os.getcwd())
from sfmss.workflow.workflow import patient_info_sample
from utils.data_process import *
import argparse

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', type=str, required=True, help='Path to the EMR record JSON file.')
    parser.add_argument('--output_path', type=str, required=True, help='Path to output the EMR record with patient profile setting.')
    parser.add_argument('--patient_path', type=str, required=True, help='Path to the patient setting JSON file.')
    parser.add_argument('--patient_personality_path', type=str, required=True, help='Path to the patient personality data CSV file.')
    args = parser.parse_args()
    return args
   
if __name__ == '__main__':
    args = arg_parse()
    p_info = read_data(args.patient_path)
    patient_personality = pd.read_csv(args.patient_personality_path)
    emr = read_data(args.file_path)

    emr_with_p = []
    for item in emr:
        emr_with_p.append(patient_info_sample(item, p_info, patient_personality))
    
    write_data(emr_with_p, args.output_path)


