from voyoagent.log import logger
from voyoagent.agent_base import AgentEvent,AgentEventType
from voyo.utils.json import JSON

def write_log(event:AgentEventType):
    pass
    # logger.info(f"type: {event.type};")

def logger_event_handler(agent_event:AgentEvent):
    agent_event.subscribe(write_log)
