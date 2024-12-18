import sys
import os
sys.path.append(os.getcwd())

import jsonlines
from tqdm import tqdm
# from sfmss.workflow.agents import *
# from sfmss.workflow.workflow import *
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
from threading import Lock
from utils.data_process import *
import argparse
import numpy as np

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', type=str, required=True, help='Path to the EMR record JSON file.')
    parser.add_argument('--patient_path', type=str, required=True, help='Path to the patient setting JSON file.')
    parser.add_argument('--output_dir', type=str, required=True, help='Path to the output folder.')
    parser.add_argument('--fail_id_path', type=str, required=False, help='Path to the fail ids JSONL file to reconstruct.', default='')
    parser.add_argument('--ignore_id_path', type=str, required=False, help='Path to ids to ignore not to construct.', default='')
    parser.add_argument('--config_path', type=str, required=True, help='Path to the configuration API JSON file.')
    parser.add_argument('--patient_personality_path', type=str, required=True, help='Path to the patient personality data CSV file.')
    parser.add_argument('--max_example', type=int, required=False, help='Max number of dialogue to construct.')
    parser.add_argument('--sfmss_nurse_pipeline', type=str, required=False, help='Run dialogue simulation with/without SFMSS Nurse pipeline.', default='true')
    parser.add_argument('--eval', type=str, required=False, help='If true, run the automatic evaluation dialogue generation pipeline without department.', default='false')
    parser.add_argument('--followup', action='store_true', help='If set, run the follow-up version of workflow and agents.')
    parser.add_argument('--sample', action='store_true', help='If set, run the dialogue simulation with patient setting sampling in the process.')
    args = parser.parse_args()
    return args

args = arg_parse()
if args.followup:
    from sfmss.workflow.follow_up.agents import *
    from sfmss.workflow.follow_up.workflow import *
    print("Follow-up visit modules imported.")
else:
    from sfmss.workflow.agents import *
    from sfmss.workflow.workflow import *
    print("First visit modules imported.")
    
def do_submit(emr_data, p_info, p_data, config, sample=True, pipeline='true', eval='false'):
    if sample:
        patient = patient_info_sample(emr_data, p_info, p_data)
    else:
        patient = emr_data
    if pipeline == 'true':
        model_d = Nurse(config['Nurse'])
    elif eval == 'true':
        model_d = Nurse_Raw(config['Nurse'])
    else:
        model_d = Nurse_Raw(config['Nurse'], department_given=True)
    model_p = Patient(config['Patient'])
    model_i = DialogueLLM(config['Supervisor-info'])
    model_m = Supervisor(config['Supervisor'])
    try:
        if pipeline == 'true':
            response = one_chat(model_i, model_d, model_p, model_m, patient)
        else:
            response = raw_one_chat(model_d, model_p, patient)
        response['error'] = False
        input_token_mini = model_i.input_token 
        output_token_mini = model_i.output_token
        input_token = model_p.input_token + model_m.input_token + model_d.input_token
        output_token = model_p.output_token  + model_m.output_token+ model_d.input_token
    except Exception as e:
        response = {"id":emr_data['outpatient_number'],"error":True,"message":str(e)}
        input_token_mini = model_i.input_token 
        output_token_mini = model_i.output_token
        input_token = model_p.input_token + model_m.input_token + model_d.input_token
        output_token = model_p.output_token + model_m.output_token + model_d.input_token
    return response, input_token, output_token, input_token_mini, output_token_mini


write_lock = Lock()

def do_parse(response, output_file, failure_file, pbar):
    if not response['error']:
        dict_success = response
        with write_lock:
            with jsonlines.open(output_file, 'a') as f_success:
                f_success.write(dict_success)
        pbar.update(1)
    else:
        dict_failure = response
        with write_lock:
            with jsonlines.open(failure_file, 'a') as f_failure:
                f_failure.write(dict_failure)
        pbar.update(1)
        print("id: " + str(response["id"]) + ", Fail")


if __name__ == '__main__':

    if args.eval == 'true':
        assert args.sfmss_nurse_pipeline == 'false'
    
    data = read_data(args.file_path)
    p_info = read_data(args.patient_path)
    p_data = pd.read_csv(args.patient_personality_path)
    config = read_data(args.config_path)

    output_dir = args.output_dir
    output_path = os.path.join(output_dir, "output.jsonl")
    fail_path = os.path.join(output_dir, "fail_output.jsonl")
    output_path_json = os.path.join(output_dir, "output.json")
    random.seed(1234)
    random.shuffle(data)
    data = data[:args.max_example]
    print('Num of dialogue to generate:',len(data))
    if args.fail_id_path:
        fail_id = read_data_jsonl(args.fail_id_path)
        fail_id = pd.DataFrame(get_part_key(fail_id, ['id']))['id'].to_list()
        data = [item for item in data if item['outpatient_number'] in fail_id]
        print(len(data))
    
    if args.ignore_id_path:
        ignore_id = read_data_jsonl(args.ignore_id_path)
        ignore_id = pd.DataFrame(get_part_key(ignore_id, ['id']))['id'].to_list()
        data = [item for item in data if item['outpatient_number'] not in ignore_id]
        print(len(data))
       
    max_workers_submit = 40
    max_workers_parse = 10
    input_tokens = []
    output_tokens = []
    input_tokens_mini = []
    output_tokens_mini = []
    fail_input_tokens = []
    fail_output_tokens = []
    fail_input_tokens_mini = []
    fail_output_tokens_mini = []
    success = 0
    with ThreadPoolExecutor(max_workers=max_workers_submit) as submit_executor, ThreadPoolExecutor(max_workers=max_workers_parse) as parse_executor:
        submit_futures = {submit_executor.submit(do_submit, item, p_info, p_data, config, args.sample, args.sfmss_nurse_pipeline, args.eval): item for item in data }

        total_tasks = len(submit_futures)
        pbar = tqdm(total=total_tasks, desc="Progress", leave=False)

        parse_futures = []
        for future in concurrent.futures.as_completed(submit_futures):
            text_info = submit_futures[future]
            try:
                response, input_token, output_token, input_token_mini, output_token_mini = future.result()
                parse_futures.append(parse_executor.submit(do_parse, response, output_path, fail_path, pbar))
                if not response['error']:
                    success += 1
                    input_tokens_mini.append(input_token_mini)
                    output_tokens_mini.append(output_token_mini)
                    input_tokens.append(input_token)
                    output_tokens.append(output_token)
                else:
                    fail_input_tokens_mini.append(input_token_mini)
                    fail_output_tokens_mini.append(output_token_mini)
                    fail_input_tokens.append(input_token)
                    fail_output_tokens.append(output_token)

            except Exception as e:
                print(f"Error processing task {response['id']}: {e}")

        for future in concurrent.futures.as_completed(parse_futures):
            try:
                result = future.result()
            except Exception as e:
                print(f"Error processing parse task: {e}")

    print("\n----------------success results-----------------------")
    print("success items:",success)
    print(f"avg_input_token:{np.mean(input_tokens)}")
    print(f"avg_output_token:{np.mean(output_tokens)}")
    print(f"avg_input_token_mini:{np.mean(input_tokens_mini)}")
    print(f"avg_output_token_mini:{np.mean(output_tokens_mini)}")

    print("\n-------------------fail results------------------------")
    print("fail items:",len(data) - success)
    print(f"avg_input_token:{np.mean(fail_input_tokens)}")
    print(f"avg_output_token:{np.mean(fail_output_tokens)}")
    print(f"avg_input_token_mini:{np.mean(fail_input_tokens_mini)}")
    print(f"avg_output_token_mini:{np.mean(fail_output_tokens_mini)}")


    jsonl_to_json(output_path, output_path_json)
    
    

