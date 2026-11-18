import os
import sys
from pathlib import Path

#保证从项目任意目录运行 pytest 时都能导入项目包
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

#单元测试不访问真实网关；voyoagent settings 需要三个键，缺省时注入占位值（真实环境变量优先）
os.environ.setdefault("OPENAI_MODEL", "test-model")
os.environ.setdefault("OPENAI_BASE_URL", "http://test.local/v1")
os.environ.setdefault("OPENAI_AUTH_TOKEN", "test-token")
