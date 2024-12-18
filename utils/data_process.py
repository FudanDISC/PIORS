import json
import pandas as pd
from tqdm import tqdm
import tiktoken

def read_data(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def read_data_jsonl(file_path):
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def write_data(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def jsonl_to_json(file_path, output_path):
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            data.append(json.loads(line))

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def json_len(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    print(len(data))


def calculate_tokens(text):
    try:
        tokenizer = tiktoken.encoding_for_model("gpt-4o")
        
        input_tokens = tokenizer.encode(text)
        input_token_count = len(input_tokens)
        
        return input_token_count
    except Exception as e:
        raise ValueError(str(e))
    
def combine_two_json(path1, path2, path):
    data1 = read_data(path1)
    data2 = read_data(path2)
    data = data1 + data2
    write_data(data, path)


def get_part_key(data, keys):
    new_data = []
    for item in data:
        new_item = {key:item[key] for key in keys}
        new_data.append(new_item)
    return new_data

def unique_data(data, column):
    ids = []
    new_data = []
    for item in data:
        if item[column] not in ids:
            new_data.append(item)
            ids.append(item[column])
    return new_data

def to_chinese(data:dict):
    key_map = {'notes':'注意事项','treatment_opinion':'诊疗意见','physical_examination':'体格检查','auxiliary_examination':'辅助检查','chief_complaint':'主诉','preliminary_diagnosis':'初步诊断','drug_allergy_history':'药物过敏史','present_illness_history':'现病史','past_history':'既往史','department':'科室','age':'年龄','gender':"性别"}
    data = {key_map[key]:data[key] for key in data.keys()}
    return data
    