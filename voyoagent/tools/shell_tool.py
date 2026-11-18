import asyncio
from pathlib import Path

from voyo.utils.json import JSON
from voyoagent.constants import Constants
from voyoagent.tools.file_tool import resolve_path
from voyoagent.utils.common_utils import run_command_async

RUN_SHELL_TOOL = {
    "type": "function",
    "name": "run_shell",
    "description": "在 shell 中执行命令，返回退出码、stdout 与 stderr。相对工作目录基于工作区目录解析。",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "要执行的 shell 命令"},
            "cwd": {"type": "string", "description": "执行命令的工作目录，缺省为工作区目录"},
            "timeout": {"type": "integer", "description": "超时秒数，默认 60"},
        },
        "required": ["command"],
    },
}


async def run_shell(args: dict) -> str:
    command = args.get("command", "")
    if not command:
        return "命令为空"
    cwd = resolve_path(args.get("cwd", "."))
    timeout = args.get("timeout", 60)
    try:
        code, stdout, stderr = await run_command_async(command, cwd=str(cwd), timeout=timeout)
    except asyncio.TimeoutError:
        return f"执行超时（>{timeout}s）: {command}"
    except OSError as e:
        return f"执行失败: {e}"
    return JSON.json({"returncode": code, "stdout": stdout, "stderr": stderr})


RUN_SHELL_ENTRY = (RUN_SHELL_TOOL, run_shell)
