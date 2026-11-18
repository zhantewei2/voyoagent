# voyoagent 本地开发

voyoagent 使用文档见 [README.md](README.md)。本文件面向仓库开发者：仓库在 lib 之外还包含一个 Agent 管理平台（`server/` FastAPI + PostgreSQL，`frontend/` Vue3，模型 / Skill / MCP / Tool 资产管理与调试界面），以及 `tests_server/`、`tests_skill/`、`main.py` 示例；这些均不随 voyoagent 包发布。

## 环境准备

1. 复制 `.env.example` 为 `.env`（前端 dev 与后端都从这里取配置），填入真实值。必填项：`OPENAI_BASE_URL` / `OPENAI_MODEL` / `OPENAI_AUTH_TOKEN`、`ANTHROPIC_BASE_URL` / `ANTHROPIC_MODEL` / `ANTHROPIC_AUTH_TOKEN`、`DATABASE_URL`（PG 连接串，server 持久化）；可选 `PG_POOL_MIN_SIZE` / `PG_POOL_MAX_SIZE` / `LOG_DIR`（默认 logs）/ `SKILL_WORK_DIR`（默认 runtime/skills，技能物化目录）。

2. 建表：把 `server/sql/schema.sql` 在目标库执行一遍（开发库可删表重建）。

## 启动后端

```bash
uv run uvicorn server.app:app --host 127.0.0.1 --port 8000
```

## 启动前端

```bash
cd frontend
npm install        # 首次
npm run dev        # http://localhost:5173 ，/api 代理到 127.0.0.1:8000
```

前端依赖后端 8000 端口（见 `frontend/vite.config.ts` 代理）；后端端口改了要同步改代理目标。

## 测试

```bash
uv run pytest tests_server tests_skill   # 后端 + skill
cd frontend && npm run test              # 前端 vitest
cd frontend && npm run typecheck         # TS 类型检查
```

## 发布 voyoagent 包

包元数据在 `pyproject.toml`（hatchling），版本号在 `voyoagent/__init__.py` 的 `__version__`，发布产物只含 `voyoagent/` 包与 README。

推 tag 自动发布（GitHub Actions，`.github/workflows/publish.yml`）：

1. PyPI 上登记 Trusted Publisher（首次发布前一次性配置）：pypi.org → 账号 Settings → Publishing（项目已存在则在项目页 Settings → Publishing），填 GitHub owner / 仓库名、workflow 文件名 `publish.yml`、environment `pypi`。
2. 确认 `__version__` 已升到目标版本。
3. 推 tag 触发：

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

   workflow 会构建 wheel + sdist、校验 tag 与 `__version__` 一致，然后用 Trusted Publishing（OIDC）上传，GitHub 侧无需配置任何 token。

手动发布（备用）：

```bash
uv build     # 产出 dist/voyoagent-<ver>.tar.gz 与 .whl
uv publish   # 需 PyPI token（--token 或 UV_PUBLISH_TOKEN）
```

## 附：旧示例

`main.py` 是 deepagents 的最小 CLI 示例，与管理平台无关：`uv run main.py`（需 ANTHROPIC_* 环境变量，可用 `.\env.ps1` 载入 `.env`）。
