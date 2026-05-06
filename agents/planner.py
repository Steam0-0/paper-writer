import json
import logging

from state import PaperState
from utils.llm import llm_client
from prompts import PLANNER_SYSTEM_PROMPT, PLANNER_USER_PROMPT

logger = logging.getLogger(__name__)


def parse_outline(response_content: str) -> dict:
    """解析LLM返回的大纲JSON"""
    try:
        if "```json" in response_content:
            start = response_content.find("```json") + 7
            end = response_content.find("```", start)
            json_str = response_content[start:end].strip()
        elif "```" in response_content:
            start = response_content.find("```") + 3
            end = response_content.find("```", start)
            json_str = response_content[start:end].strip()
        else:
            json_str = response_content.strip()

        while json_str.startswith("json"):
            json_str = json_str[4:].strip()

        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse outline JSON: {e}")
        return {"chapters": []}


def planner(state: PaperState) -> PaperState:
    """生成论文大纲"""
    logger.info(f"Running planner for topic: {state['topic']}")

    user_prompt = PLANNER_USER_PROMPT.format(topic=state["topic"])
    response = llm_client.generate(prompt=user_prompt, system_prompt=PLANNER_SYSTEM_PROMPT)

    if not response.success:
        logger.error(f"Planner failed: {response.error}")
        return {**state, "error": f"Planner error: {response.error}"}

    outline_data = parse_outline(response.content)
    logger.info(f"Planner generated {len(outline_data.get('chapters', []))} chapters")

    return {**state, "outline": json.dumps(outline_data, ensure_ascii=False, indent=2)}