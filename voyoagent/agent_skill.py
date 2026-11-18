import logging
import os
from pathlib import Path
from typing import TypedDict

import aiofiles
from voyo.utils.json import JSON

from voyoagent.tools.file_tool import resolve_path
from voyoagent.tools.load_skill import LOAD_SKILL_TOOL, find_skill_file, parse_skill_meta, read_skill_doc
from voyoagent.utils.common_utils import load_file_content_async
from voyoagent.utils.exception import YoAgentCode, YoAgentException

logger = logging.getLogger(__name__)

SKILL_FRAGMENT_ID = "skills"


class SkillInfo(TypedDict):
    name: str
    description: str
    readed: bool
    skill_dir: str


async def scan_skill_dirs(root: Path) -> list[Path]:
    #定位根目录下的技能目录：自身命中则单技能，否则取一级子目录中命中的那些
    if not await aiofiles.os.path.isdir(root):
        raise YoAgentException(YoAgentCode.COMMON, f"技能目录不存在: {root}")
    if await find_skill_file(root) is not None:
        return [root]
    found: list[Path] = []
    for name in await aiofiles.os.listdir(root):
        sub = root / name
        if await aiofiles.os.path.isdir(sub) and await find_skill_file(sub) is not None:
            found.append(sub)
    return found


async def build_skill_info(skill_dir: Path) -> SkillInfo | None:
    #读取技能定义文件并解析元数据，name 缺失时回落为目录名
    skill_file = await find_skill_file(skill_dir)
    if skill_file is None:
        return None
    try:
        content = await load_file_content_async(str(skill_file))
    except OSError as e:
        logger.warning("技能定义文件读取失败: %s, %s", skill_file, e)
        return None
    meta = parse_skill_meta(content)
    return {
        "name": meta.get("name") or skill_dir.name,
        "description": meta.get("description", ""),
        "readed": False,
        "skill_dir": str(skill_dir),
    }


class Agent_Skill_Interface:
    #Agent_Skill 的对外接口，宿主 agent 只依赖这一层。
    #技能集合由 registry_skill 维护，加载状态由 load_skill 工具回写。

    def registry_tool(self, tool_entry):
        #宿主 agent 提供的注册入口：接收 (schema, handler) 二元组，写入 agent 工具表。
        raise NotImplementedError

    async def registry_skill(self, skill_dir: str | list[str]) -> list[SkillInfo]:
        #扫描技能目录并登记技能（name/description/skill_dir），返回本次登记的技能列表。
        raise NotImplementedError

    async def unregistry_skill(self, skill_dir: str | list[str]) -> list[SkillInfo]:
        #移除已登记的技能，返回被移除的技能列表。
        raise NotImplementedError

    def list_skill(self) -> list[dict]:
        #返回技能集合快照（同步、立即返回）。
        raise NotImplementedError


class Agent_Skill(Agent_Skill_Interface):
    skills: list[SkillInfo]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.skills = []
        self.registry_tool((LOAD_SKILL_TOOL, self._tool_load_skill))

    def registry_tool(self, tool_entry):
        #空实现仅声明接口；实际注册由 MRO 中更前的子类覆盖（如 Voyo_Agent 的工具注册表）
        pass

    async def registry_skill(self, skill_dir: str | list[str]) -> list[SkillInfo]:
        #扫描目录登记技能：目录自身含定义文件按单技能处理，否则逐个扫描其一级子目录
        dirs = skill_dir if isinstance(skill_dir, (list, tuple)) else [skill_dir]
        registered: list[SkillInfo] = []
        for one in dirs:
            for path in await scan_skill_dirs(resolve_path(one)):
                info = await build_skill_info(path)
                if info is not None:
                    self._upsert_skill(info)
                    registered.append(info)
        self._sync_skill_fragment()
        return registered

    async def unregistry_skill(self, skill_dir: str | list[str]) -> list[SkillInfo]:
        #移除已登记的技能，未登记的目录直接忽略
        dirs = skill_dir if isinstance(skill_dir, (list, tuple)) else [skill_dir]
        keys = {self._path_key(str(resolve_path(one))) for one in dirs}
        removed = [skill for skill in self.skills if self._path_key(skill["skill_dir"]) in keys]
        if removed:
            self.skills = [skill for skill in self.skills if self._path_key(skill["skill_dir"]) not in keys]
            self._sync_skill_fragment()
        return removed

    def list_skill(self) -> list[dict]:
        #技能集合快照
        return [dict(skill) for skill in self.skills]

    def _upsert_skill(self, info: SkillInfo):
        #同目录重复登记时保留既有 readed 状态
        key = self._path_key(info["skill_dir"])
        for i, skill in enumerate(self.skills):
            if self._path_key(skill["skill_dir"]) == key:
                info["readed"] = skill["readed"]
                self.skills[i] = info
                return
        self.skills.append(info)

    def _find_skill(self, skill_dir: str, name: str) -> SkillInfo | None:
        #按目录定位技能，目录未命中时回落到技能名
        if skill_dir:
            key = self._path_key(str(resolve_path(skill_dir)))
            for skill in self.skills:
                if self._path_key(skill["skill_dir"]) == key:
                    return skill
        if name:
            for skill in self.skills:
                if skill["name"] == name:
                    return skill
        return None

    @staticmethod
    def _path_key(path: str) -> str:
        #目录归一化键：小写化并统一分隔符，用于路径比较
        return os.path.normcase(str(Path(path).absolute()))

    def skill_fragment(self) -> str:
        #技能集合的提示词片段：JSON 集合 + 使用说明
        return (
            "可用技能集合（JSON 数组，readed 表示该技能是否已加载过）：\n"
            f"{JSON.json(self.skills)}\n"
            "当任务与某个技能相关时，先调用 load_skill 工具加载该技能的完整说明，再按其指引执行。"
        )

    def _sync_skill_fragment(self):
        #技能集合变化后刷新提示词片段，首次写入用追加、后续用替换
        agent_prompt = getattr(self, "agent_prompt", None)
        if agent_prompt is None:
            return
        content = self.skill_fragment()
        if not agent_prompt.replace_fragment_prompt(SKILL_FRAGMENT_ID, content):
            agent_prompt.append_fragment_prompt(SKILL_FRAGMENT_ID, content)

    async def _tool_load_skill(self, args: dict) -> str:
        #load_skill 工具：读取技能全文，成功后把技能标记为已加载
        skill_dir = args.get("dir", "")
        name = args.get("name", "")
        skill = self._find_skill(skill_dir, name)
        if skill is None:
            return f"技能未注册: {skill_dir or name}，可用技能: {self._available_skill_names()}"
        try:
            content = await read_skill_doc(Path(skill["skill_dir"]))
        except (OSError, FileNotFoundError) as e:
            return f"技能加载失败: {e}"
        skill["readed"] = True
        self._sync_skill_fragment()
        return content

    def _available_skill_names(self) -> str:
        #已登记技能的名称与目录，供模型纠错
        return ", ".join(f"{s['name']}({s['skill_dir']})" for s in self.skills) or "无"
