### 异步代码

- 异步代码从第一行起就用异步实现：文件用 aiofiles，网络用 httpx 等异步库，延时用 `asyncio.sleep`。
- async 函数中禁止同步阻塞调用（文件/网络 IO、`time.sleep`、`subprocess.run`、CPU 密集计算），文件元数据操作（is_file、exists、iterdir、mkdir）也在其列。
- `asyncio.to_thread` 仅作兜底，只用于无法修改原逻辑的场景（第三方同步库、遗留代码）；禁止先写同步再用它转异步。
- 写完 async 函数后逐行自查是否有遗漏的阻塞调用。

### 图片视觉分析

需要对图片做视觉分析/检查时，必须安排一个临时 subagent（Agent 工具）去解析：把图片路径与检查/解析要求提给该 agent，由它返回检查或解析结果。
禁止在当前主 agent 内直接读图/做图片理解，防止图片内容把主上下文撑得过大。

### 模块边界

- `voyoagent/` 是外部框架模块，只作为黑盒依赖使用，不单独修改其内部实现。
- 新功能一律写在 `server/` 内，通过 voyoagent 的公开接口（`Yo_Agent`、`AgentManager` 无关的框架类）调用。

### server 分层

目录职责固定，不跨层调用：

```
server/
  app.py              # 装配：lifespan、路由注册、中间件
  config.py           # pydantic-settings 配置，读 .env
  db.py               # PG 连接池生命周期
  dependencies.py     # FastAPI Depends 注入
  controller/         # HTTP 层：解析入参、调用 service、返回响应
  service/            # 业务层：校验、编排、事务边界
  mapper/             # 数据层：只有 SQL，不写业务判断
  entity/             # 表实体：一表一实体
  models/             # 接口出入参
  middleware/         # 全局横切逻辑
```

调用方向固定：`controller -> service -> mapper -> entity`，反向禁止。
`mapper` 不得 import `service`；`controller` 不得直接写 SQL。

### 数据库（voyolib pg）

- 连接池：`from voyo.db.pg import ConnectionPool, set_default_pool`，在 `server/db.py` 的 `init_db()` 建池、`close_db()` 关闭，lifespan 中调用。
- mapper 写操作用 `@transaction()`（带括号调用），函数**最后一个参数必须名为 `conn`**，由 ContextVar 自动注入，禁止手动传 conn。
- 占位符用 `$1, $2, ...`（asyncpg 风格）。
- 主键统一用 `from voyo.utils import yo_unique` 的 `yo_unique.get_uid()`，实体中通过 `server/entity/base.py` 的 `new_id()` 生成，列类型 bigint。
- 建表脚本放 `server/sql/schema.sql`，一表一实体，实体与表字段一一对应。

### 接口响应

- 接口**不直接返回 dict/list**，统一用 voyolib 的 `Methods`：
  - `Methods.resp_result(data, code=200)` — 有数据返回
  - `Methods.resp_success()` — 无数据只回成功
- `resp_result` 走 voyolib 的 `YOJSONResponse`，由其处理 bigint 精度失真（超 2^53 转字符串）与 datetime 格式化，不要自己 `json.dumps`。
- 需要拼 JSON 字符串（如 SSE 帧）时用 `from voyo.utils.json import JSON` 的 `JSON.json(obj)`。

### 异常处理

- service / controller 中出错统一 `raise YoHttpException(code, msg)`，code 用 `from voyo.utils.exception import ExceptionType`（PARAM_ERROR/NOT_FOUND/SERVER_ERROR 等）。
- `server/middleware/exception.py` 的 `YoExceptionMiddleware` 捕获后统一转 `resp_result`，controller 不要自己 try/except 包业务异常。

### 日志

- 应用入口调用一次 `from voyo.utils import init_logger`（`init_db` 之后、lifespan 内）。
- 各模块用标准 `logging.getLogger(__name__)`，不自行配置 handler。

### 代码风格

- 注释只说「为什么」和约束，不复述代码；单条不超过 3 行。
- 类型注解齐全；公开函数写明返回类型。
- 同一函数内不混用同步与异步 IO。

### 敏感信息（禁止暴露）

- 代码、测试、脚本、配置、文档中禁止出现真实 api_key / token / 密码 / 数据库连接串，一律走环境变量（`.env`）或占位值（如 `test-token`）。
- `.env`、`.mcp.json`、`.claude/settings*.json` 不入库（.gitignore 已排除）；新增含凭证的文件同样不入库。
- 提交/发布前自查：grep 真实密钥格式（`sk-`、长 hex token、明文连接串），命中即删。

### 版本与发布

- 包版本唯一来源是 `voyoagent/__init__.py` 的 `__version__`（pyproject.toml 动态读取，不要在 pyproject.toml 里写静态 version）。
- 发版流程：先改 `__version__`，再打 `v{version}` 格式的 git tag（如 `v0.1.0`），tag 必须与 `__version__` 严格一致，push tag 触发 GitHub Actions 发布 PyPI。

### 界面视觉规范

- 颜色参差：标题/标签用深色 `var(--color-text)` 加粗，正文常规色，`--color-text-secondary` 只给辅助小字（hint、时间戳、注释性内容）；禁止大片灰平铺。
- 大小落差：页面标题 > 区块标题 > 标签 > 正文 > 辅助小字，字号至少拉开 3 档（用 `--font-size-*` 变量），避免 14px 一统到底。
- 密度节奏：表单/详情/modal/空态用间距分组（如表单标签 `padding-top: 20px` 与上文拉开），表格等密集区保持紧凑；不要全局一样密。
- 禁平铺陈述：用字重、颜色、间距做分组与层级，卡片内部分区要有主次，同级标签不得和内容同色同重。
- 色值一律走 `frontend/src/styles/vars.scss` 设计变量，SCSS 里不写死色值；新层级色先加变量再用。
