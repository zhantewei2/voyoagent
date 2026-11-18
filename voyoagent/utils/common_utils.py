import asyncio

import aiofiles
from aiofiles import os
from pathlib import Path
from typing import TypedDict
import sys
import platform


class ListDirItem(TypedDict):
    file_name: str
    is_dir: bool


def load_file_content(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


#启动阶段同步加载提示词文件（AgentPrompt.__init__ 为同步上下文）
def read_file(file_path: str) -> str:
    return load_file_content(file_path)

async def load_file_content_async(file_path: str) -> str:
    async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
        return await f.read()


async def load_file_rows_async(file_path:str)->str:
    async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
        lines=await f.readlines()
        lines=[f"{index}\t{line}" for index,line in enumerate(lines,1)]
        return "".join(lines)

def write_file_content(file_path: str,content:str)->str:
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


async def write_file_content_async(file_path: str, content: str)->str:
    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
        await f.write(content)


async def list_dir_async(dir_path: str) -> list[ListDirItem]:
    dir_path = Path(dir_path)
    if not await os.path.isdir(dir_path):
        return []

    file_names = await os.listdir(dir_path)
    items :list[ListDirItem]= []
    for name in file_names:
        is_dir = await os.path.isdir(dir_path / name)
        items.append({"file_name": name, "is_dir": is_dir})
    return items


def _decode_stream(data: bytes) -> str:
    for enc in ("utf-8", "gbk"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


async def run_command_async(command: str, cwd: str = None, timeout: int = 60) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_shell(
        command,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise
    return proc.returncode, _decode_stream(stdout), _decode_stream(stderr)



def os_family() -> str:
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    try:
        info = platform.freedesktop_os_release()
    except OSError:
        return "linux"
    if "rhel" in info.get("ID_LIKE", "") or info.get("ID") in {"centos", "rocky", "rhel"}:
        return "rhel"
    if "debian" in info.get("ID_LIKE", "") or info.get("ID") in {"debian", "ubuntu"}:
        return "debian"
    return "linux"