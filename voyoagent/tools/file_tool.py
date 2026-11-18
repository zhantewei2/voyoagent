import json
from pathlib import Path

import aiofiles
from voyo.utils.json import JSON
from voyoagent.constants import Constants
from voyoagent.utils.common_utils import (
    list_dir_async,
    load_file_rows_async,
    load_file_content_async,
    write_file_content_async,
)


def resolve_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(Constants.WORKSPACE_DIR) / p


READ_FILE_TOOL = {
    "type": "function",
    "name": "read_file",
    "description": "读取文本文件内容，每行格式为「行号\\t内容」。相对路径基于工作区目录解析。",
    "parameters": {
        "type": "object",
        "properties": {"path": {"type": "string", "description": "文件路径"}},
        "required": ["path"],
    },
}

WRITE_FILE_TOOL = {
    "type": "function",
    "name": "write_file",
    "description": "将文本写入文件，覆盖已有内容，父目录不存在时自动创建。仅用于新建文件或整体重写；修改已有文件请用 replace_file。相对路径基于工作区目录解析。",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "content": {"type": "string", "description": "写入的文本内容"},
        },
        "required": ["path", "content"],
    },
}

REPLACE_FILE_TOOL = {
    "type": "function",
    "name": "replace_file",
    "description": "精确替换文件中的片段，修改已有文件时优先使用本工具而不是 write_file。删除片段=new_string 传空串；插入内容=把锚点片段替换为「锚点+新内容」。old_string 需与文件原文逐字一致，注意不含 read_file 输出中每行首的行号前缀。相对路径基于工作区目录解析。",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "old_string": {"type": "string", "description": "待替换的原文片段，需含足够上下文保证在文件中唯一"},
            "new_string": {"type": "string", "description": "替换后的内容，删除片段时传空字符串"},
            "replace_all": {"type": "boolean", "description": "片段出现多处时是否全部替换，默认 false"},
        },
        "required": ["path", "old_string", "new_string"],
    },
}

LIST_DIR_TOOL = {
    "type": "function",
    "name": "list_dir",
    "description": "列出目录下的文件与子目录。相对路径基于工作区目录解析。",
    "parameters": {
        "type": "object",
        "properties": {"path": {"type": "string", "description": "目录路径"}},
        "required": ["path"],
    },
}


async def read_file(args: dict) -> str:
    try:
        path=args.get("path", "")
        return await load_file_rows_async(str(resolve_path(path)))
    except OSError as e:
        return f"读取失败: {e}"


async def write_file(args: dict) -> str:
    path = resolve_path(args.get("path", ""))
    try:
        await aiofiles.os.makedirs(path.parent, exist_ok=True)
        await write_file_content_async(str(path), args.get("content", ""))
        return f"已写入 {path}"
    except OSError as e:
        return f"写入失败: {e}"


def _match_lines(content: str, old: str) -> list[int]:
    #old_string 各处出现的行号（1 起始）
    lines, start = [], 0
    while (i := content.find(old, start)) >= 0:
        lines.append(content.count("\n", 0, i) + 1)
        start = i + len(old)
    return lines


async def replace_file(args: dict) -> str:
    old = args.get("old_string", "")
    if not old:
        return "替换失败: old_string 不能为空"
    path = resolve_path(args.get("path", ""))
    try:
        content = await load_file_content_async(str(path))
        n = content.count(old)
        if n == 0:
            return "替换失败: 未找到 old_string，请先用 read_file 查看原文再重试"
        replace_all = bool(args.get("replace_all", False))
        if n > 1 and not replace_all:
            return f"替换失败: old_string 匹配 {n} 处（行 {_match_lines(content, old)}），请扩充上下文使其唯一；确要全部替换请传 replace_all=true"
        new = content.replace(old, args.get("new_string", ""), -1 if replace_all else 1)
        await write_file_content_async(str(path), new)
        return f"已替换 {n if replace_all else 1} 处（行 {_match_lines(content, old)}）"
    except OSError as e:
        return f"替换失败: {e}"


async def list_dir(args: dict) -> str:
    path=args.get("path", "")
    r= await list_dir_async(path)
    return JSON.json(r)


READ_FILE_ENTRY = (READ_FILE_TOOL, read_file)
WRITE_FILE_ENTRY = (WRITE_FILE_TOOL, write_file)
REPLACE_FILE_ENTRY = (REPLACE_FILE_TOOL, replace_file)
LIST_DIR_ENTRY = (LIST_DIR_TOOL, list_dir)
