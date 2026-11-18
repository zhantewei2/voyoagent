from pathlib import Path

import aiofiles

from voyoagent.utils.common_utils import load_file_content_async

SKILL_FILE_NAME = "skill.md"  # 文件名小写比较，等价 SKILL.md / skill.md / SKILL.MD

LOAD_SKILL_TOOL = {
    "type": "function",
    "name": "load_skill",
    "description": "加载指定技能的完整操作说明（该技能目录下的 SKILL.md）。当任务与某个可用技能相关时，先调用它获取指南再行动。",
    "parameters": {
        "type": "object",
        "properties": {
            "dir": {"type": "string", "description": "技能所在目录，取自可用技能列表的 skill_dir"},
            "name": {"type": "string", "description": "技能名称，可选，与 dir 二选一"},
        },
        "required": ["dir"],
    },
}


async def find_skill_file(skill_dir: Path) -> Path | None:
    #在技能目录内查找技能定义文件，文件名小写比较；不存在返回 None
    try:
        names = await aiofiles.os.listdir(skill_dir)
    except OSError:
        return None
    for name in names:
        if name.lower() == SKILL_FILE_NAME:
            path = skill_dir / name
            if await aiofiles.os.path.isfile(path):
                return path
    return None


async def read_skill_doc(skill_dir: Path) -> str:
    #读取技能目录下的技能定义文件全文，文件缺失时抛 FileNotFoundError
    skill_file = await find_skill_file(skill_dir)
    if skill_file is None:
        raise FileNotFoundError(f"技能目录 {skill_dir} 下没有 SKILL.md")
    return await load_file_content_async(str(skill_file))


def parse_skill_meta(content: str) -> dict:
    #解析 frontmatter 中的 key: value 字段，仅取 name 与 description
    meta: dict[str, str] = {}
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return meta
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, sep, value = line.partition(":")
        if not sep:
            continue
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return {k: v for k, v in meta.items() if k in ("name", "description")}
