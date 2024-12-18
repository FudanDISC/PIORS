from pydantic import BaseModel
from enum import Enum
from typing import List, Dict
class OneRecord(BaseModel):
    field: str
    record: str

class NewRecordResponse(BaseModel):
    new_record: list[OneRecord]
    
class NurseActionEnum(str, Enum):
    SYMPTOM_INQUIRY = "症状询问"
    HISTORY_INQUIRY = "病史询问"
    RECOMMEND_DEPARTMENT = "推荐科室"
    END_CONVERSATION = "结束对话"
    MEDICAL_REPLY = "医疗问题回复"
    OTHER_REPLY = "其他问题回复"
    QUICK_HELP = "提供快速帮助"

class NurseAction(BaseModel):
    action: NurseActionEnum

class PatientActionEnum(str, Enum):
    REQUEST = "需求提出"
    FEEDBACK = "信息反馈"
    QUESTION = "问题提出"
    END_CONVERSATION = "结束对话"
    IRRELEVANT_TOPIC = "提及无关话题"

class PatientAction(BaseModel):
    action: PatientActionEnum

class InfoActionEnum(str, Enum):
    SYMPTOM_INQUIRY = "症状询问"
    HISTORY_INQUIRY = "病史询问"
    
class InfoSuggestion(BaseModel):
    enough: bool
    suggestion: str
    action: InfoActionEnum

class OverallSuggestion(BaseModel):
    flag: bool
    suggestion: str
