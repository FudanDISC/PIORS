import sys
import os
sys.path.append(os.getcwd())
from openai import OpenAI
import json
import random
from sfmss.workflow.follow_up.system_prompt import *
from utils.data_process import *
from sfmss.workflow.json_class import *

class Nurse():
    def __init__(self, config) -> None:
        self.model_name = config['model_name']
        self.model = OpenAI(
            base_url=config['base_url'],
            api_key=config['api_key'],
        )
        self.messages = [] 
        self.chat_text = ["导诊人员：您好，有什么可以帮你的吗？\n"] 
        self.map_function = NURSE_PHASE
        self.turn = 0
        self.input_token = 0
        self.output_token = 0

    def new(self, data):
        self.department = data['department']
        emr = {}
        for key in ['chief_complaint', 'age', 'gender','department',
                 'present_illness_history','treatment_opinion',
                'preliminary_diagnosis','auxiliary_examination','notes']:
            emr[key] = data[key]
        self.first_record = emr

    def phase_judge(self):
        chat_text = ''.join(self.chat_text)
        try:
            response = self.model.beta.chat.completions.parse(
                model=self.model_name,
                response_format=NurseAction,
                messages = [{"role": "system","content": SYSTEM_PROMPT_J_D},
                            {"role": "user", "content": chat_text}]
            )
            response = response.choices[0].message.parsed
        except Exception as e:
            raise ValueError(str(e))
        
        self.input_token += calculate_tokens(chat_text + SYSTEM_PROMPT_J_D)
        self.output_token += calculate_tokens(str(response))
 
        response = response.action.value
        function = self.map_function[response]
        return response, function

    def chat(self, input, phase, function, suggestion, suggestion2=None):
        system_prompt = SYSTEM_PROMPT_D.format(first_record = self.first_record)
        input_prompt = f"<患者最新一次输入>：{input}\n<你当前应该采取的行动>：{phase}，{function}"
        if phase == '推荐科室' or  phase == '提供快速帮助' or  phase == '结束阶段':
            system_prompt = SYSTEM_PROMPT_D_2.format(department=self.department)
        else:
            if suggestion2:
                input_prompt = f"<患者最新一次输入>：{input}\n<你当前应该采取的行动>：{phase}，{function}\n<对导诊询问策略和语气的监督建议>：{suggestion2}。\n" 
            if suggestion:
                input_prompt += f"\n<对下一轮询问的监督建议>：{suggestion}" # 
        try:                 
            response = self.model.chat.completions.create(
                model=self.model_name,
                messages = [{"role": "system","content": system_prompt}] + self.messages +
                [{"role":"user","content":input_prompt}]
            )
            response = response.choices[0].message.content
        except Exception as e:
            raise ValueError(str(e))

        self.input_token += calculate_tokens(system_prompt + input_prompt)
        self.output_token += calculate_tokens(response)
        for message in self.messages:
            self.input_token += calculate_tokens(message['content'])
        return response
    
    def one_turn(self, input, suggestion=None, suggestion2=None):
        self.chat_text += [f"患者：{input}\n"]

        phase, function = self.phase_judge()
        if phase == '推荐科室' and suggestion.enough == False and self.turn<2:
            self.turn += 1
            phase = suggestion.action.value
            function = self.map_function[phase]
        response = self.chat(input, phase, function, suggestion.suggestion, suggestion2)
        self.messages.append({"role":"user", "content":input}) 

        self.messages.append({"role":"assistant", "content":response})
        self.chat_text += [f"导诊人员：{response}\n"]
        return phase, response


class Patient():
    def __init__(self, config) -> None:
        self.model_name = config['model_name']
        self.model = OpenAI(
            base_url=config['base_url'],
            api_key=config['api_key'],
        )
        self.messages = [] 
        self.chat_text = []  
        self.map_function = PATIENT_PHASE
        self.input_token = 0
        self.output_token = 0
        
    def new(self, data):
        for key in ['chief_complaint', 'name', 'age', 'gender', 'past_history',
                'drug_allergy_history', 'present_illness_history', 'edu', 'personality',"edu_d",'visit_date','finance','example','treatment_opinion',
                'preliminary_diagnosis','auxiliary_examination','notes']:
            setattr(self, key, data.get(key))
        self.patient_disc = self.patient_construct()
        self.scene_construct()
        self.profile = {"scene":self.scene, "patient_disc":self.patient_disc, "chief_complaint":self.chief_complaint, "present_illness_history":self.present_illness_history,"preliminary_diagnosis":self.preliminary_diagnosis, "treatment_opinion":self.treatment_opinion,"notes":self.notes, "auxiliary_examination":self.auxiliary_examination, "name":self.name, "gender":self.gender, "age":self.age}
    
    def patient_construct(self):
        input = f"性别：{self.gender}；年龄：{self.age}；受教育程度：{self.edu}；性格：{self.personality}；收入情况：{self.finance}"
        try:
            response = self.model.chat.completions.create(
                model=self.model_name,
                messages = [{"role": "system","content": SYSTEM_PROMPT_P_C},
                            {"role": "user", "content": input}]
            )
            response = response.choices[0].message.content
        except Exception as e:
            raise ValueError(str(e))
        
        self.input_token += calculate_tokens(SYSTEM_PROMPT_P_C+input)
        self.output_token += calculate_tokens(response)       
        return response

    def scene_construct(self):
        input_prompt = f"<受教育程度>：{self.edu}；<年龄>：{self.age}；<初诊主诉>：{self.chief_complaint}；<初步诊断>：{self.preliminary_diagnosis}；<诊疗意见>：{self.treatment_opinion}"
        try:
            response = self.model.chat.completions.create(
                model=self.model_name,
                messages = [{"role": "system","content": SYSTEM_PROMPT_S_C},
                            {"role": "user", "content": input_prompt}]
            )
            response = response.choices[0].message.content
        except Exception as e:
            raise ValueError(str(e))    
        self.scene = response
        self.input_token += calculate_tokens(SYSTEM_PROMPT_S_C+input_prompt)
        self.output_token += calculate_tokens(response)
        return response     

    def phase_judge(self):
        chat_text = ''.join(self.chat_text)
        input = f"<导诊对话>：{chat_text}\n\n<患者的初诊情况>：{self.chief_complaint}\n\n<患者的沟通风格>：{self.patient_disc}"
        try:
            response = self.model.beta.chat.completions.parse(
                model=self.model_name, 
                response_format=PatientAction,
                messages = [{"role": "system","content": SYSTEM_PROMPT_J_P},
                            {"role": "user", "content": input}]
            )
        except Exception as e:
            raise ValueError(str(e))    
        response = response.choices[0].message.parsed

        self.input_token += calculate_tokens(SYSTEM_PROMPT_J_P+input)
        self.output_token += calculate_tokens(str(response))

        response = response.action.value
        function = self.map_function[response]
        return response, function

    def chat(self, input, phase, function):
        system_prompt = SYSTEM_PROMPT_P.format(**self.profile)
        input_prompt = f'''<导诊人员的最新一次输入>：{input}\n<你应采取的行动>：{phase}，需要{function}\n\n<你的沟通风格>：{self.patient_disc}''' 
        try:
            response = self.model.chat.completions.create(
                model=self.model_name,
                messages = [{"role": "system","content": system_prompt}] + self.messages +
                [{"role":"user","content":input_prompt}]
            )
            response = response.choices[0].message.content
        except Exception as e:
            raise ValueError(str(e))
        
        self.input_token += calculate_tokens(system_prompt+input_prompt)
        self.output_token += calculate_tokens(response)
        for message in self.messages:
            self.input_token += calculate_tokens(message['content'])

        return response
    
    def one_turn(self, input="您好，有什么可以帮你的吗？"):
        self.chat_text += [f"导诊人员：{input}\n"]

        phase, function = self.phase_judge()
        if random.random()<0.1 and phase not in ['结束对话', '需求提出', '提及无关话题']:
            phase = '提及无关话题'
            function = self.map_function[phase]
        response = self.chat(input, phase, function)
        self.messages.append({"role":"user", "content":input}) 

        self.messages.append({"role":"assistant", "content":response})
        self.chat_text += [f"患者：{response}\n"]
        if phase == "结束对话":
            return True, phase, response
        return False, phase, response
    

class DialogueLLM():
    def __init__(self, config) -> None:
        self.model_name = config['model_name']
        self.model = OpenAI(
            base_url=config['base_url'],
            api_key= config['api_key'],
        )
        self.input_token = 0
        self.output_token = 0

    def chat_process(self, temp, knowlodge):
        input = f"已知信息：{str(knowlodge)}\n新对话：{str(temp)}"
        response = self.model.beta.chat.completions.parse(
            model=self.model_name,
            response_format=NewRecordResponse,
            messages=[{"role": "system",
                        "content": SYSTEM_PROMPT_DIALOGUE},
                        {"role": "user",
                        "content":input}]
        )
        response = response.choices[0].message.parsed.new_record
        self.input_token += calculate_tokens(SYSTEM_PROMPT_DIALOGUE + input)
        self.output_token += calculate_tokens(str(response))
        new_response = []
        for item in response:
            new_response.append({item.field:item.record})
        return new_response


class Supervisor():
    def __init__(self, config) -> None:
        self.model_name = config['model_name']
        self.model = OpenAI(
            base_url=config['base_url'],
            api_key=config['api_key'],
        )
        self.input_token = 0
        self.output_token = 0
    
    def new(self, data):
        emr = {}
        for key in ['chief_complaint', 'present_illness_history', 'treatment_opinion',
                'preliminary_diagnosis','notes']:
            emr[key] = data[key]
        self.real_info = emr
        self.preliminary_diagnosis = data['preliminary_diagnosis']

    def compare(self, knowledge):
        input = f"<导诊人员收集到的复诊信息>：{str(knowledge)}\n<患者的初诊信息>：{str(self.real_info)}"
        response = self.model.beta.chat.completions.parse(
            model=self.model_name,
            response_format=InfoSuggestion,
            messages = [{"role": "system","content": SYSTEM_PROMPT_M},
                        {"role": "user", "content": input}]
        )
        response = response.choices[0].message.parsed
        self.input_token += calculate_tokens(input+SYSTEM_PROMPT_M)
        self.output_token += calculate_tokens(str(response))
        return response
    
    def monitor_chat(self, chat_text):
        response = self.model.beta.chat.completions.parse(
            model=self.model_name,
            response_format=OverallSuggestion,
            messages = [{"role": "system","content": SYSTEM_PROMPT_M_B},
                        {"role": "user", "content": chat_text}]
        )
        response = response.choices[0].message.parsed

        self.input_token += calculate_tokens(chat_text+SYSTEM_PROMPT_M_B)
        self.output_token += calculate_tokens(str(response))
        return response.flag, response.suggestion
    