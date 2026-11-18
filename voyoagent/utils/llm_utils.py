from typing import TypedDict
from voyo.model import OpenAiClient

class Extract_Llm_Stream(TypedDict):
    text: str
    thinking_text:str

def extract_openai_text(row_text:str)->Extract_Llm_Stream|None:
    
    row_data=OpenAiClient._parse_event(row_text)
    if not row_data:
        return
   
    choices= row_data.get("choices") or []
    if not choices:
        return
    delta= choices[0].get("delta",{})
    text=delta.get("content")
    thinking_text= delta.get("reasoning_content") or delta.get("reasoning")

    return {
        "text": text or "",
        "thinking_text": thinking_text or ""
    }