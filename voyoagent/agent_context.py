from voyo.utils.token import estimate_token_count


class Agent_Context():
    context_tokens: int

    usage_input_tokens: int
    usage_output_tokens: int
    usage_cache_input_tokens: int

    def __init__(self):
        self.context_tokens=0
        self.usage_input_tokens=0
        self.usage_output_tokens=0
        self.usage_cache_input_tokens=0
    
