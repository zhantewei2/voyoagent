"""Agent_Skill 技能注册与加载的单元测试。"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

#单元测试不访问真实网关，缺省时注入自洽占位值（真实环境变量优先）
os.environ.setdefault("OPENAI_MODEL", "test-model")
os.environ.setdefault("OPENAI_BASE_URL", "http://test.local/v1")
os.environ.setdefault("OPENAI_AUTH_TOKEN", "test-token")

import pytest

from voyoagent.agent import Voyo_Agent
from voyoagent.agent_skill import SKILL_FRAGMENT_ID
from voyoagent.constants import root_dir


@pytest.fixture
def agent():
    #只用到技能注册、提示词片段与工具表，不发起模型请求
    return Voyo_Agent(
        model="test-model",
        base_url="http://test.local/v1",
        api_key="test-token",
        system_prompt_path=str(root_dir / "prompts" / "system.md"),
        soul_prompt_path=str(root_dir / "prompts" / "soul.md"),
    )


def write_skill(skill_dir: Path, file_name: str = "SKILL.md", name: str = "", description: str = "", body: str = "正文内容") -> Path:
    #生成一个技能目录，返回其定义文件路径
    skill_dir.mkdir(parents=True, exist_ok=True)
    meta = [f"name: {name}", f"description: {description}"]
    frontmatter = "\n".join(line for line in meta if not line.endswith(": "))
    content = f"---\n{frontmatter}\n---\n{body}\n" if frontmatter else f"{body}\n"
    skill_file = skill_dir / file_name
    skill_file.write_text(content, encoding="utf-8")
    return skill_file


def skill_fragment(agent) -> str:
    #取提示词中的技能片段内容
    return dict(agent.agent_prompt.fragment_prompts).get(SKILL_FRAGMENT_ID, "")


#用例 1.1 识别大小写三种文件名
async def test_registry_skill_ignores_filename_case(agent, tmp_path):
    for i, file_name in enumerate(["SKILL.md", "skill.md", "SKILL.MD"]):
        write_skill(tmp_path / f"s{i}", file_name=file_name, name=f"skill-{i}", description="描述")

    registered = await agent.registry_skill(str(tmp_path))

    assert len(registered) == 3
    assert len(agent.skills) == 3
    assert {s["skill_dir"] for s in agent.skills} == {str(tmp_path / f"s{i}") for i in range(3)}


#用例 1.2 解析 name 与 description
async def test_registry_skill_parses_meta(agent, tmp_path):
    write_skill(tmp_path / "demo", name="demo-skill", description="演示技能")

    await agent.registry_skill(str(tmp_path / "demo"))

    assert agent.skills[0]["name"] == "demo-skill"
    assert agent.skills[0]["description"] == "演示技能"
    assert agent.skills[0]["readed"] is False


#用例 1.3 缺少 name 时回落目录名
async def test_registry_skill_fallback_name(agent, tmp_path):
    write_skill(tmp_path / "fallback-dir", description="只有描述")

    await agent.registry_skill(str(tmp_path / "fallback-dir"))

    assert agent.skills[0]["name"] == "fallback-dir"


#用例 1.4 一级子目录批量注册
async def test_registry_skill_scans_sub_dirs(agent, tmp_path):
    write_skill(tmp_path / "root" / "a", name="a-skill")
    write_skill(tmp_path / "root" / "b", name="b-skill")
    (tmp_path / "root" / "c").mkdir(parents=True)

    registered = await agent.registry_skill(str(tmp_path / "root"))

    assert len(registered) == 2
    assert {s["name"] for s in agent.skills} == {"a-skill", "b-skill"}


#用例 1.5 重复注册保留 readed 状态
async def test_registry_skill_keeps_readed(agent, tmp_path):
    write_skill(tmp_path / "demo", name="demo-skill")
    await agent.registry_skill(str(tmp_path / "demo"))
    agent.skills[0]["readed"] = True

    await agent.registry_skill(str(tmp_path / "demo"))

    assert len(agent.skills) == 1
    assert agent.skills[0]["readed"] is True


#用例 2.1 fragment 注入技能集合 JSON
async def test_skill_fragment_contains_skills(agent, tmp_path):
    write_skill(tmp_path / "demo", name="demo-skill", description="演示技能")

    await agent.registry_skill(str(tmp_path / "demo"))

    fragment = skill_fragment(agent)
    assert "demo-skill" in fragment
    assert "演示技能" in fragment
    assert '"readed": false' in fragment
    assert len([i for i, _ in agent.agent_prompt.fragment_prompts if i == SKILL_FRAGMENT_ID]) == 1


#用例 2.2 重复注册不产生重复 fragment
async def test_skill_fragment_not_duplicated(agent, tmp_path):
    write_skill(tmp_path / "demo", name="demo-skill")

    await agent.registry_skill(str(tmp_path / "demo"))
    await agent.registry_skill(str(tmp_path / "demo"))

    assert len([i for i, _ in agent.agent_prompt.fragment_prompts if i == SKILL_FRAGMENT_ID]) == 1


#用例 2.3 load_skill 工具已注册
async def test_load_skill_tool_registered(agent):
    names = {t["name"] for t in agent.tools}
    assert "load_skill" in names

    tool = next(t for t in agent.wire_tools if t["name"] == "load_skill")
    assert set(tool) == {"type", "name", "description", "parameters"}
    assert tool["parameters"]["required"] == ["dir"]


#用例 2.4 加载成功后 readed 置 True 且 fragment 刷新
async def test_load_skill_marks_readed(agent, tmp_path):
    write_skill(tmp_path / "demo", name="demo-skill", body="正文标记")
    await agent.registry_skill(str(tmp_path / "demo"))

    result = await agent._tool_load_skill({"dir": str(tmp_path / "demo")})

    assert "正文标记" in result
    assert agent.skills[0]["readed"] is True
    assert '"readed": true' in skill_fragment(agent)


#用例 2.5 未知技能返回提示而非异常
async def test_load_skill_unknown_dir(agent, tmp_path):
    result = await agent._tool_load_skill({"dir": str(tmp_path / "missing")})

    assert result.startswith("技能未注册")


#用例 2.6 初始化时按配置目录注册技能
async def test_skill_dirs_registered_on_init(tmp_path):
    write_skill(tmp_path / "demo", name="demo-skill")

    agent = Voyo_Agent(
        model="test-model",
        base_url="http://test.local/v1",
        api_key="test-token",
        system_prompt_path=str(root_dir / "prompts" / "system.md"),
        soul_prompt_path=str(root_dir / "prompts" / "soul.md"),
        skill_dirs=[str(tmp_path / "demo")],
    )
    await agent.init()

    assert [s["name"] for s in agent.skills] == ["demo-skill"]
    assert "demo-skill" in skill_fragment(agent)
