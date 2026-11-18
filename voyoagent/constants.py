from pathlib import Path

root_dir=Path(__file__).parent

class Constants:
    SKILL_DIRS=str(root_dir.joinpath("skills"))
    WORKSPACE_DIR=str(Path.cwd())
    MAX_TURNS=10000


