import json
import logging

from state import PaperState
from utils.llm import llm_client
from prompts import WRITER_SYSTEM_PROMPT, WRITER_USER_PROMPT

logger = logging.getLogger(__name__)


def writer(state: PaperState) -> PaperState:
    current_section = state.get("current_section", "")
    topic = state["topic"]

    logger.info(f"Running writer for section: {current_section}")

    outline_data = json.loads(state.get("outline", "{}"))
    chapters = outline_data.get("chapters", [])

    target_chapter = None
    for idx, ch in enumerate(chapters):
        if ch.get("chapter", "").lower() == current_section.lower():
            target_chapter = ch
            break

    if not target_chapter:
        logger.error(f"Chapter not found: {current_section}")
        return {**state, "error": f"Chapter not found: {current_section}"}

    user_prompt = WRITER_USER_PROMPT.format(
        section_num=chapters.index(target_chapter) + 1,
        chapter_title=target_chapter["chapter"],
        topic=topic,
        key_points="\n".join([f"- {p}" for p in target_chapter.get("key_points", [])]),
        purpose=target_chapter.get("purpose", "")
    )

    response = llm_client.generate(prompt=user_prompt, system_prompt=WRITER_SYSTEM_PROMPT)

    if not response.success:
        logger.error(f"Writer failed: {response.error}")
        return {**state, "error": f"Writer error: {response.error}"}

    sections = state.get("sections", {})
    sections[current_section] = response.content

    logger.info(f"Writer completed section: {current_section}")
    return {**state, "sections": sections}