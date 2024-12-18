def one_chat(model_i, model_d, model_p, model_m, data_p):
    model_p.new(data_p)
    model_d.new(data_p)
    model_m.new(data_p)
    end, phase_p, response_p = model_p.one_turn()
    knowledge = [{'姓名':data_p['name']},{'年龄':data_p['age']},{'性别':data_p['gender']},{"辅助检查":data_p['auxiliary_examination']}]
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