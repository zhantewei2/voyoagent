-- server 层建表脚本：每张表一个 entity，主键统一用 voyolib unique_id（bigint）
-- model_id/skill_ids/mcp_ids 为逻辑引用（不加 FK），被引用校验由 service 完成

CREATE TABLE IF NOT EXISTS t_model (
    id          BIGINT PRIMARY KEY,
    name        VARCHAR(128) NOT NULL UNIQUE,
    model       VARCHAR(128) NOT NULL,
    base_url    VARCHAR(512) NOT NULL,
    api_key     VARCHAR(256) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS t_skill (
    id          BIGINT PRIMARY KEY,
    name        VARCHAR(128) NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS t_mcp (
    id          BIGINT PRIMARY KEY,
    name        VARCHAR(128) NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    command     VARCHAR(256) NOT NULL DEFAULT '',
    args        TEXT[] NOT NULL DEFAULT '{}',
    url         VARCHAR(512) NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS t_agent (
    id          BIGINT PRIMARY KEY,
    name        VARCHAR(128) NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    soul_prompt TEXT NOT NULL DEFAULT '',
    model_id    BIGINT NOT NULL,
    tool_names  TEXT[] NOT NULL DEFAULT '{}',
    skill_ids   BIGINT[] NOT NULL DEFAULT '{}',
    mcp_ids     BIGINT[] NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS t_chat (
    id          BIGINT PRIMARY KEY,
    agent_id    BIGINT NOT NULL,
    title       VARCHAR(256) NOT NULL DEFAULT '',
    history     TEXT NOT NULL DEFAULT '[]',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
