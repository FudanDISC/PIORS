import sys
import os
sys.path.append(os.getcwd())
import random
from utils.data_process import *
import pdb

def raw_one_chat(model_d,model_p,data_p):
    model_p.new(data_p)
    model_d.new(data_p)
    end, phase_p, response_p = model_p.one_turn()
    turn = 1
    save_chat = {'id':data_p["outpatient_number"],
                 'patient_setting':{"education":data_p['edu'],"personality":data_p['bigfive'],'personality_details':data_p['personality'],"finance":data_p['finance']},
                 'scene':model_p.scene,'p_disc':model_p.patient_disc,
                 'dialogue':[]}
    temp = [{"role":"patient","content":response_p}]
    temp[0]['phase'] = phase_p; temp[0]['turn'] = 1
    save_chat['dialogue'] += temp
    while not end and turn < 10:
        turn += 1
        response_d = model_d.one_turn(response_p)
        end, phase_p, response_p = model_p.one_turn(response_d)
        temp = [{"role":"doctor","content":response_d},{"role":"patient","content":response_p}]
        temp[1]['phase'] = phase_p
        temp[0]['turn'] = turn; temp[1]['turn'] = turn
        save_chat['dialogue'] += temp
    return save_chat


def one_chat(model_i, model_d, model_p, model_m, data_p):
    model_p.new(data_p)
    model_d.new(data_p)
    model_m.new(data_p)
    end, phase_p, response_p = model_p.one_turn()
    knowledge = [{'姓名':data_p['name']},{'年龄':data_p['age']},{'性别':data_p['gender']}]
    temp = [{"role":"patient","content":response_p}]
    knowledge += model_i.chat_process(temp, knowledge)
    suggestion = model_m.compare(knowledge)
    suggestion2 = None
    enough = suggestion.enough
    turn = 1
    save_chat = {'id':data_p["outpatient_number"],
                 'patient_setting':{"education":data_p['edu'],"personality":data_p['bigfive'],'personality_details':data_p['personality'],"finance":data_p['finance']},
                 'scene':model_p.scene,'p_disc':model_p.patient_disc,
                 'dialogue':[],'suggestion':[]}

    temp[0]['phase'] = phase_p; temp[0]['turn'] = 1
    save_chat['dialogue'] += temp
    if not suggestion.enough:
        save_chat['suggestion'].append({"monitor":"信息收集是否全面","content":suggestion.suggestion,"turn":1})
    while not end and turn < 10:
        turn += 1
        phase_d, response_d = model_d.one_turn(response_p, suggestion, suggestion2)
        end, phase_p, response_p = model_p.one_turn(response_d)
        temp = [{"role":"doctor","content":response_d},{"role":"patient","content":response_p}]
        knowledge += model_i.chat_process(temp, knowledge)
        if not end:
            if not enough:
                suggestion = model_m.compare(knowledge)
                enough = suggestion.enough
            flag, suggestion2 = model_m.monitor_chat(''.join(model_p.chat_text[-8:]))
            if not suggestion.enough:
                save_chat['suggestion'].append({"monitor":"信息收集是否全面","content":suggestion.suggestion,"turn":turn})
            if flag:
                save_chat['suggestion'].append({"monitor":"整体监督病人情绪和对话有效性","content":suggestion2,"turn":turn})

        temp[0]['phase'] = phase_d; temp[1]['phase'] = phase_p
        temp[0]['turn'] = turn; temp[1]['turn'] = turn
        save_chat['dialogue'] += temp
    return save_chat

def patient_info_sample(data, p_info, patient_personalities):
    edu = random.choices(p_info['education'], k=1, weights=[11.9, 24.4, 31.8, 13.6, 4.6, 7.6, 6.1])[0]
    finance = random.sample(p_info['finance'], 1)[0]

    BigFive = p_info['BigFive']
    sample_Bigfive = patient_personalities.sample(n=1).values.tolist()[0]
    personality = []
    data['bigfive'] = {}
    for (trait, result) in zip(BigFive.keys(), sample_Bigfive):
        if result != 'Neutral':
            personality += random.sample(BigFive[trait][result.capitalize()], 2)
        data['bigfive'][trait] = result

    data['edu'] = edu
    data['personality'] = personality
    data['finance'] = finance
    return data

def sample_personality(patients_data):
    random_row = patients_data.sample(n=1)
    print(random_row.values.tolist()[0])
