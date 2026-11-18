from voyo.utils import VoyoException
from enum import IntEnum
class YoAgentException(VoyoException):
    def __init__(self, code, msg):
        super().__init__(code, msg)


class YoAgentCode(IntEnum):
    COMMON= 20001
    MCP_CONNECT_ERROR= 30001
    MCP_ERROR= 30000