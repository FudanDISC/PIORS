import sys
import os
sys.path.append(os.getcwd())

import json
import jsonlines
from tqdm import tqdm
from sfmss.workflow.agents import *
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
from threading import Lock
from utils.data_process import *
import argparse
import numpy as np
import re

def arg_parse():
    parser = argparse.ArgumentParser(description="Process file paths for a medical dialogue evaluation.")
    parser.add_argument('--eval_dir', type=str, required=True, help='Evaluation data folder')
    parser.add_argument('--config_path', type=str, required=True, help='Path to the configuration JSON file')
    parser.add_argument('--emr_path', required=True, help='Path to the corresponding EMRs.')
    args = parser.parse_args()
    return args

def stat_eval(dialogue):
    turn = (len(dialogue)+1)/2
    avg_turn_p = 0
    avg_turn_d = 0
    for chat in dialogue[::2]:
        avg_turn_p += len(chat['content'])
    for chat in dialogue[1:][::2]:
        avg_turn_d += len(chat['content'])
    avg_turn_d = avg_turn_d/(turn-1)
    avg_turn_p = avg_turn_p/turn
    return turn, avg_turn_p, avg_turn_d

def get_department(dialogue, model_j):
    input_token = output_token = 0
    chat_text = ''
    for item in dialogue:
        chat_text += f"<{item['role']}>:{item['content']}\n"
    system_prompt = '''你要根据用户给出的一段医患分诊导诊的对话，提取出导诊人员给患者最终推荐的科室。注意返回JSON，格式为:{"department":}。
如果没有完成导诊，则返回空。
注意“全科医学科”和“全科医学科(保健科)”是两个科室。'''
    try:
        response = model_j.chat.completions.create(
                model='gpt-4o',
                response_format={ "type": "json_object" },
                messages = [{"role": "system","content": system_prompt},
                            {"role": "user", "content": chat_text}]
            )
    except Exception as e:
        raise ValueError(str(e))
    try:
        response = json.loads(response.choices[0].message.content)
        input_token = calculate_tokens(system_prompt+chat_text)
        output_token = calculate_tokens(str(response))
        response = response['department']
        response = re.sub(r'（', '(', response) 
        response = re.sub(r'）', ')', response) 
    except Exception as e:
        raise ValueError(str(e))
    
    return response, input_token, output_token

def get_llm_overall_score(dialogue, message, model_j):
    input_token = output_token = 0
    chat_text = ''
    for item in dialogue:
        chat_text += f"{item['role']}:{item['content']}\n"
    message_text = f"主诉：{message['chief_complaint']}\n现病史:{message['present_illness_history']}\n既往史：{message['past_history']}"
    input_prompt = f'''你是一个具有专业医疗背景、公正且严格的评估者。你需要对一段发生在患者和导诊人员之间的导诊对话进行打分。你将被提供该患者的真实情况及其应当被分诊的科室。你应当基于导诊人员对患者信息的收集能力、对应患者实际情况和可能诊断的问询和导诊逻辑、导诊判断的准确性等方面对导诊人员表现做出从医疗专业性角度出发的评估，并给出一个1-5分的打分。
你关注的重点应当是上述提及的相关内容，不要让对话长度、患者或导诊人员的语言风格等影响你的打分和判断。你的打分应该足够严格以确保一定的区分度，不要轻易给出满分。
请使用JSON格式返回，格式为{{"score":得分}}

###<患者信息>###
{message_text}
###<应被分配科室>###
{message['department']}

###<医患分诊对话>###
{chat_text}'''
    try:
        response = model_j.chat.completions.create(
                model='gpt-4o',
                response_format={ "type": "json_object" },
                messages = [
                            {"role": "user", "content": input_prompt}] 
            )
    except Exception as e:
        raise ValueError(str(e))
    try:
        response = json.loads(response.choices[0].message.content)
        input_token = calculate_tokens(input_prompt)
        output_token = calculate_tokens(str(response))
        response = response['score']
    except Exception as e:
        print(str(e))
        raise ValueError(str(e))
    return response, input_token, output_token

def get_llm_info_score(dialogue, message, model_j):
    input_token = output_token = 0
    chat_text = ''
    for item in dialogue:
        chat_text += f"{item['role']}:{item['content']}\n"
    message_text = f"主诉：{message['chief_complaint']}\n现病史:{message['present_illness_history']}\n既往史：{message['past_history']}"
    input_prompt = f'''你是一个具有专业医疗背景、公正且严格的评估者。你需要阅读一段发生在患者和导诊人员之间的导诊对话，并对其中导诊人员的诊前信息收集能力给出一个1-5的打分，主要关注主诉和现病史的信息收集。你将被提供该患者的真实情况及其应当被分诊的科室。
不要让对话长度、患者或导诊人员的语言风格等影响你的打分和判断。你的打分应该足够严格以确保一定的区分度，不要轻易给出满分。
请使用JSON格式返回，格式为{{"score":得分}}、

###<患者信息>###
{message_text}
###<应被分配科室>###
{message['department']}

###<医患分诊对话>###
{chat_text}'''
    try:
        response = model_j.chat.completions.create(
                model='gpt-4o',
                response_format={ "type": "json_object" },
                messages = [
                            {"role": "user", "content": input_prompt}] 
            )
    except Exception as e:
        raise ValueError(str(e))
    try:
        response = json.loads(response.choices[0].message.content)
        input_token = calculate_tokens(input_prompt)
        output_token = calculate_tokens(str(response))
        # print(response['analysis'])
        response = response['score']
    except Exception as e:
        print(str(e))
        raise ValueError(str(e))
    return response, input_token, output_token

def do_submit(item, message, model):
    id = item['id']
    turn, avg_turn_p, avg_turn_d = stat_eval(item['dialogue'])
    input_token = 0
    output_token = 0
    score = 0
    score_info = 0
    department = ''
    try:
        score, input_token_1, output_token_1 = get_llm_overall_score(item['dialogue'], message, model)
        score_info, input_token_3, output_token_3 = get_llm_info_score(item['dialogue'], message, model)
        department, input_token_4, output_token_4 = get_department(item['dialogue'], model)
        eval_item = {"id":id,"error":False,"turn_num":turn,"avg_turn_p":avg_turn_p, "avg_turn_d":avg_turn_d,"department":department,"score":score, "i_score":score_info}  # 
        input_token =  input_token_1 + input_token_3 + input_token_4
        output_token =  output_token_1 + output_token_3 + output_token_4
    except ValueError as e:
        eval_item = {"id":id,"error":True,"turn_num":turn,"avg_turn_p":avg_turn_p, "avg_turn_d":avg_turn_d,"message":str(e)}
        print("id",id,"fail!,message",str(e))
    return eval_item, input_token, output_token

write_lock = Lock()

def do_parse(eval_item, output_file, output_fail_file, pbar):
    if not eval_item['error']:
        dict_success = eval_item
        with write_lock:
            with jsonlines.open(output_file, 'a') as f_success:
                f_success.write(dict_success)
        pbar.update(1)
    else:
        dict_failure = eval_item
        with write_lock:
            with jsonlines.open(output_fail_file, 'a') as f_failure:
                f_failure.write(dict_failure)
        pbar.update(1)


def acc(eval_data, emr):
    acc = 0
    num = 0
    for i, item in enumerate(eval_data):
        num += 1
        id = item['id']
        department_pred = item['department']
        department_real = emr.loc[emr['outpatient_number'] == id, 'department'].values[0]
        eval_data[i]['acc'] = 0
        eval_data[i]['real_departmrnt'] = department_real

        if department_pred == department_real:
            acc += 1
            eval_data[i]['acc'] = 1
            
    print('科室分诊acc：',acc/num)
    return eval_data


if __name__ == '__main__':
    args = arg_parse()
    dialogue_path = os.path.join(args.eval_dir, "output.json")
    emr_path = args.emr_path
    eval_output = os.path.join(args.eval_dir, "eval_result")
    output_path = os.path.join(eval_output, "eval.jsonl")
    output_path_2 = os.path.join(eval_output, "eval.json")
    output_fail_path = os.path.join(eval_output, "eval_fail.jsonl")
        
    config = read_data(args.config_path)
    dialogue_c = read_data(dialogue_path)
    emr = read_data(emr_path)
    emr = pd.DataFrame(emr)
    model = OpenAI(
            base_url=config['base_url'],
            api_key=config['api_key'],
        )
    
    eval_result = []
    max_workers_submit = 40
    max_workers_parse = 10
    success = 0
    input_tokens = []
    output_tokens = []

    with ThreadPoolExecutor(max_workers=max_workers_submit) as submit_executor, ThreadPoolExecutor(max_workers=max_workers_parse) as parse_executor:

        submit_futures = {}
        for item in dialogue_c:
            id = item['id']
            emr_message = emr.loc[emr['outpatient_number'] == id].to_dict('records')[0]
            future = submit_executor.submit(do_submit, item, emr_message, model)
            submit_futures[future] = item

        total_tasks = len(submit_futures)
        pbar = tqdm(total=total_tasks, desc="Progress", leave=False)

        parse_futures = []
        for future in concurrent.futures.as_completed(submit_futures):
            text_info = submit_futures[future]
            try:
                response, input_token, output_token = future.result()
                parse_futures.append(parse_executor.submit(do_parse, response, output_path, output_fail_path, pbar))
                if not response['error']:
                    eval_result.append(response)
                    input_tokens.append(input_token)
                    output_tokens.append(output_token)
                    success += 1
            except Exception as e:
                print(f"Error processing task {response['id']}: {e}")

        for future in concurrent.futures.as_completed(parse_futures):
            try:
                result = future.result()
            except Exception as e:
                print(f"Error processing parse task: {e}")
    
    print("\n--------------success result-------------------")
    print("success items:",success)
    print("avg_input_tokens:", np.mean(input_tokens))
    print("avg_output_tokens:",np.mean(output_tokens))
    print("\n----------------fail result---------------------")
    print("fail items:",len(dialogue_c)-success)

    print("\n---------------eval result----------------------")
    eval_result = acc(eval_result, emr)
    write_data(eval_result, output_path_2)

    eval_result = pd.DataFrame(eval_result)
    print("avg_turn:",eval_result['turn_num'].mean())
    print("avg_single_turn_len_doctor:",eval_result['avg_turn_p'].mean())
    print("avg_single_turn_len_patient:",eval_result['avg_turn_d'].mean())
    print("avg_overall_score:",eval_result['score'].mean())
    print("avg_info_score:",eval_result['i_score'].mean())

    
    







