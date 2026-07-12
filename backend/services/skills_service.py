import json
import logging
from pathlib import Path

from backend.runtime_paths import runtime_file

logger = logging.getLogger(__name__)

SKILLS_FILE = runtime_file("data/skills.json")


def _ensure_dir():
    Path(SKILLS_FILE).parent.mkdir(parents=True, exist_ok=True)


def _load_skills() -> list[dict]:
    _ensure_dir()
    path = Path(SKILLS_FILE)
    if not path.exists():
        return _default_skills()
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return _default_skills()


def _save_skills(skills: list[dict]) -> None:
    _ensure_dir()
    with open(SKILLS_FILE, "w", encoding="utf-8") as f:
        json.dump(skills, f, ensure_ascii=False, indent=2)


def _default_skills() -> list[dict]:
    return [
        {
            "id": "technical_analysis",
            "name": "技术分析",
            "description": "在分析市场时加入技术指标分析（均线、MACD、RSI等）",
            "prompt": "在分析市场走势时，请结合技术分析指标（如移动平均线、MACD、RSI、布林带等）进行判断，并给出关键支撑位和阻力位。",
            "enabled": True,
        },
        {
            "id": "risk_warning",
            "name": "风险提示",
            "description": "每次回复末尾自动添加风险提示",
            "prompt": "在每次回复的末尾，请添加一段简短的风险提示，提醒投资者注意风险控制。",
            "enabled": True,
        },
        {
            "id": "macro_perspective",
            "name": "宏观视角",
            "description": "分析时加入宏观经济因素考量",
            "prompt": "在分析市场时，请结合宏观经济因素（如利率政策、通胀数据、就业数据、GDP增长等）进行综合分析。",
            "enabled": False,
        },
        {
            "id": "sentiment_analysis",
            "name": "情绪分析",
            "description": "关注市场情绪和资金流向",
            "prompt": "在分析时，请关注市场情绪指标（如VIX恐慌指数、资金流向、多空比等）以及社交媒体舆情。",
            "enabled": False,
        },
    ]


def list_skills() -> list[dict]:
    return _load_skills()


def add_skill(name: str, description: str, prompt: str) -> dict:
    skills = _load_skills()
    skill_id = name.lower().replace(" ", "_")
    for s in skills:
        if s["id"] == skill_id:
            return {"error": f"技能 '{name}' 已存在"}
    skill = {
        "id": skill_id,
        "name": name,
        "description": description,
        "prompt": prompt,
        "enabled": True,
    }
    skills.append(skill)
    _save_skills(skills)
    logger.info("添加技能: %s", name)
    return skill


def remove_skill(skill_id: str) -> dict:
    skills = _load_skills()
    new_skills = [s for s in skills if s["id"] != skill_id]
    if len(new_skills) == len(skills):
        return {"error": f"技能 '{skill_id}' 不存在"}
    _save_skills(new_skills)
    logger.info("移除技能: %s", skill_id)
    return {"ok": True, "removed": skill_id}


def toggle_skill(skill_id: str, enabled: bool) -> dict:
    skills = _load_skills()
    for s in skills:
        if s["id"] == skill_id:
            s["enabled"] = enabled
            _save_skills(skills)
            return {"ok": True, "id": skill_id, "enabled": enabled}
    return {"error": f"技能 '{skill_id}' 不存在"}


def get_active_prompts() -> str:
    """获取所有已启用技能的 prompt 片段，拼接到 system prompt。"""
    skills = _load_skills()
    active = [s for s in skills if s.get("enabled", False)]
    if not active:
        return ""
    lines = ["\n\n额外指令（来自已启用的技能）："]
    for s in active:
        lines.append(f"- [{s['name']}] {s['prompt']}")
    return "\n".join(lines)
