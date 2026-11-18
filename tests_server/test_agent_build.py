#agent 装配字段 → 实例构建参数（mock mapper 与 Yo_Agent，不连真库）
from server.entity.agent_entity import AgentEntity
from server.entity.mcp_entity import McpEntity
from server.entity.model_entity import ModelEntity
from server.entity.skill_entity import SkillEntity
from server.service import agent_service
from server.service.agent_service import AgentManager


class FakeAgentPrompt:
    def __init__(self):
        self.soul_prompt = "默认 soul"


class FakeYoAgent:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.agent_prompt = FakeAgentPrompt()
        self.tools = []
        self.skill_dirs = []
        self.mcps = []
        self.inited = False

    def registry_tool(self, entry):
        self.tools.append(entry)

    async def registry_skill(self, dirs):
        self.skill_dirs.append(dirs)

    async def registry_mcp(self, name, command="", args=None, url=""):
        self.mcps.append((name, command, args, url))

    async def init(self):
        self.inited = True


async def test_build_agent_params(monkeypatch):
    agent = AgentEntity(id=1, name="a", soul_prompt="自定义 soul", model_id=2,
                        tool_names=["read_file"], skill_ids=[3], mcp_ids=[4])
    model = ModelEntity(id=2, name="m", model="model-x", base_url="http://b", api_key="k")
    skill = SkillEntity(id=3, name="s", content="c")
    mcp = McpEntity(id=4, name="echo", command="python", args=["x.py"], url="")

    async def fake_select_agent_detail(agent_id):
        return agent, model, [skill], [mcp]

    async def fake_materialize(self, one):
        return f"runtime/skills/{one.id}"

    monkeypatch.setattr(agent_service.agent_mapper, "select_agent_detail", fake_select_agent_detail)
    monkeypatch.setattr(AgentManager, "_materialize_skill", fake_materialize)
    monkeypatch.setattr(agent_service, "Yo_Agent", FakeYoAgent)

    instance = await AgentManager()._build(1)

    assert isinstance(instance, FakeYoAgent)
    assert instance.kwargs == {"model": "model-x", "base_url": "http://b", "api_key": "k",
                               "effort": "none", "auto_registry_tool": False}
    assert [entry[0]["name"] for entry in instance.tools] == ["read_file"]
    assert instance.agent_prompt.soul_prompt == "自定义 soul"
    assert instance.skill_dirs == [["runtime/skills/3"]]
    assert instance.mcps == [("echo", "python", ["x.py"], "")]
    assert instance.inited is True
