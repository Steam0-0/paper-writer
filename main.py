import argparse
import logging
import sys
from typing import Literal

from langgraph.graph import StateGraph, END

sys.path.insert(0, ".")

from config import graph_config
from state import PaperState, create_initial_state
from agents.planner import planner
from agents.writer import writer
from agents.reviewer import reviewer
from agents.orchestrator import should_continue, route_next_section, select_next_section
from utils.document import export_paper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def build_graph():
    builder = StateGraph(PaperState)

    builder.add_node("planner", planner)
    builder.add_node("select_section", select_next_section)
    builder.add_node("writer", writer)
    builder.add_node("reviewer", reviewer)

    builder.set_entry_point("planner")

    builder.add_edge("planner", "select_section")

    builder.add_conditional_edges(
        "select_section",
        route_next_section,
        {
            "writer": "writer",
            "end": END
        }
    )

    builder.add_edge("writer", "reviewer")

    builder.add_conditional_edges(
        "reviewer",
        should_continue,
        {
            "revise": "writer",
            "end": "select_section"
        }
    )

    return builder.compile(
        recursion_limit=graph_config.recursion_limit,
        debug=False
    )


def run_paper_writer(topic: str) -> PaperState:
    logger.info(f"Starting paper writer for topic: {topic}")

    graph = build_graph()
    initial_state = create_initial_state(topic)

    config = {"recursion_limit": graph_config.recursion_limit}
    result = graph.invoke(initial_state, config=config)

    logger.info("Paper writing completed")
    return result


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Academic Paper Writer")
    parser.add_argument("topic", nargs="?", default="基于贝叶斯的导弹装备性能评估",
                        help="Paper topic (default: 基于贝叶斯的导弹装备性能评估)")
    parser.add_argument("--output", "-o", help="Output filename")
    parser.add_argument("--format", "-f", choices=["docx", "md"],
                        help="Output format (default: from config)")

    args = parser.parse_args()

    try:
        result = run_paper_writer(args.topic)

        if result.get("error"):
            logger.error(f"Pipeline error: {result['error']}")
            print(f"\nError: {result['error']}")
            return 1

        filepath = export_paper(result, args.output)
        print(f"\n{'='*60}")
        print(f"Paper generated successfully!")
        print(f"Output: {filepath}")
        print(f"{'='*60}")

        print("\n--- Section Reviews ---")
        for section, review in result.get("reviews", {}).items():
            print(f"\n[{section}]")
            print(f"  Score: {review.score:.2f}/1.00")
            print(f"  Decision: {review.decision.value}")
            print(f"  Feedback: {review.feedback}")

        return 0

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"\nUnexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())