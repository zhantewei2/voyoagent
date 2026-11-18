"""最小可运行的 Deep Agent 示例：stdin/stdout 交互 + 内置规划/虚拟文件系统。"""

import os
import sys
import threading
from typing import Any

if hasattr(sys.stdout, "reconfigure"):  # Windows GBK 控制台兼容
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")

from deepagents import create_deep_agent
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import InMemorySaver

THREAD_ID = "main"


def get_weather(city: str) -> str:
    """查询指定城市当前天气。"""
    return f"{city}：晴，26°C，微风"


def web_search(query: str) -> str:
    """联网搜索，返回与 query 相关的摘要信息。"""
    return f"「{query}」的搜索摘要：这是示例数据，可替换为真实搜索 API。"


def build_model() -> ChatAnthropic:
    """Anthropic 兼容端点，显式关闭思考。凭证来自 env.ps1 载入的 .env。"""
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    if not token:
        raise SystemExit("缺少 ANTHROPIC_AUTH_TOKEN：先在 PowerShell 里执行 .\\env.ps1")
    return ChatAnthropic(
        model=os.environ.get("ANTHROPIC_MODEL", "mimo-v2.6-pro"),
        api_key=token,
        default_headers={"Authorization": f"Bearer {token}"},
        max_tokens=8192,
        thinking={"type": "disabled"},
    )


def build_agent():
    return create_deep_agent(
        model=build_model(),
        tools=[get_weather, web_search],
        system_prompt=(
            "你是一个高效的研究助手。可用工具：ls、read_file、write_file、edit_file、"
            "delete、glob、grep、execute、task、get_weather、web_search。"
            "直接给出结论，不要展示推理过程、解题步骤或操作铺垫。"
        ),
        checkpointer=InMemorySaver(),
    )


def render_blocks(content: Any):
    """把消息 content 规范成 dict 块序列。"""
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return [b if isinstance(b, dict) else {"type": "text", "text": str(b)} for b in content or []]


def _brief(value: Any, limit: int = 120) -> str:
    text = " ".join(str(value).split())
    return text if len(text) <= limit else text[:limit] + "…"


class Spinner:
    """静默等待期在当前行转圈；首个输出到达时调用 stop() 擦除。"""

    FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def __init__(self, label: str = "等待模型响应…"):
        self._label = label
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        i = 0
        while not self._stop.wait(0.12):
            print(f"\r  {self.FRAMES[i % len(self.FRAMES)]} {self._label}", end="", flush=True)
            i += 1

    def start(self) -> "Spinner":
        self._thread.start()
        return self

    def stop(self) -> None:
        if self._stop.is_set():
            return
        self._stop.set()
        self._thread.join(timeout=0.4)
        print("\r" + " " * 40 + "\r", end="", flush=True)


_spinner: Spinner | None = None


def _wake() -> None:
    """首个可见输出到达，停掉等待指示。"""
    global _spinner
    if _spinner is not None:
        _spinner.stop()
        _spinner = None


def report_tool_call(name: str) -> None:
    _wake()
    print(f"\n  [->] {name}", flush=True)


def report_tool_result(content: Any) -> None:
    _wake()
    print(f"  [<-] {_brief(content)}", flush=True)


def report_thinking(block: dict) -> None:
    """思考块若仍到达，明确标出，避免混进正文被误认为已关闭。"""
    _wake()
    print(f"\n  [thinking] {_brief(block.get('thinking', ''))}", flush=True)


def run_turn(agent, text: str) -> None:
    global _spinner
    _spinner = Spinner().start()
    try:
        events = agent.stream(
            {"messages": [{"role": "user", "content": text}]},
            config={"configurable": {"thread_id": THREAD_ID}},
            stream_mode="messages",
        )
        seen_tools: set[str] = set()
        for msg, _meta in events:
            if getattr(msg, "type", "") == "tool":
                report_tool_result(msg.content)
                continue
            for block in render_blocks(msg.content):
                btype = block.get("type")
                if btype == "text":
                    if not block.get("text"):
                        continue
                    _wake()
                    print(block["text"], end="", flush=True)
                elif btype in {"thinking", "redacted_thinking"}:
                    report_thinking(block)
                elif btype in {"tool_use", "tool_call"}:
                    key = block.get("id") or block.get("name") or ""
                    if key in seen_tools:
                        continue
                    seen_tools.add(key)
                    report_tool_call(block.get("name", "?"))
    finally:
        _wake()
        print(flush=True)


def chat_loop(agent) -> None:
    model = os.environ.get("ANTHROPIC_MODEL", "mimo-v2.6-pro")
    print(f"就绪 model={model} thinking=disabled；输入消息开始；exit / quit 或 Ctrl+C 退出。")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line.lower() in {"exit", "quit"}:
            break
        if not line:
            continue
        run_turn(agent, line)


if __name__ == "__main__":
    chat_loop(build_agent())
