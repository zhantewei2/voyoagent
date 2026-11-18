from voyo.model import OpenAiResponsesMsg

from voyoagent.constants import root_dir
from voyoagent.utils.common_utils import read_file

class AgentPrompt:
    system_prompt:str
    soul_prompt: str
    fragment_prompts: list[tuple[id,str]]
    prompt: str

    def __init__(
            self,
            system_prompt_path:str,
            soul_prompt_path:str 
        ):
        self.prompt=""
        self.fragment_prompts=[]
        self.system_prompt=read_file( system_prompt_path)
        self.soul_prompt=read_file(soul_prompt_path)


    def get_unified_prompt(self)->str:
        return self.system_prompt + self.combine_fragment_prompts()+ "\n\n" + self.soul_prompt

    def get_unified_message(self)->list[OpenAiResponsesMsg]:
        return [
            {"role": "system", "content": self.get_unified_prompt()}
        ]

    def combine_fragment_prompts(self)->str:
        return "\n\n ### Here is our key information, please refer to it: \n\n" + "\n\n".join(fragment_prompt for id, fragment_prompt in self.fragment_prompts) + "\n\n" if self.fragment_prompts else ""
    
    def append_fragment_prompt(self, id:str,fragment_prompt:str):
        self.fragment_prompts.append((id,fragment_prompt))

    def replace_fragment_prompt(self, id:str,fragment_prompt:str)->bool:
        #按 id 替换已有 fragment，id 不存在时不做修改并返回 False
        for i,(old_id,_) in enumerate(self.fragment_prompts):
            if old_id==id:
                self.fragment_prompts[i]=(id,fragment_prompt)
                return True
        return False

    

