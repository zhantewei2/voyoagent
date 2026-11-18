"""最小 Skill 架构：不做目录扫描，load_skill(name) 按名读取 SKILL.md 全文返回给模型。

可用技能清单由调用方（system prompt）自行告知，模型判断相关后主动调用 load_skill。
"""

from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parents[1] / "skills"

LOAD_SKILL_TOOL = {
    "name": "load_skill",
    "description": "加载指定技能的完整操作说明（SKILL.md）。执行任务前若与某个可用技能相关，先调用它获取指南再行动。",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "技能名，对应 skills/ 下的目录名"},
        },
        "required": ["name"],
    },
}


def load_skill(name: str) -> str:
    path = (SKILLS_DIR / name / "SKILL.md").resolve()
    if path.parent.parent != SKILLS_DIR.resolve() or not path.is_file():
        return f"skill 不存在: {name}"
    return path.read_text(encoding="utf-8")
