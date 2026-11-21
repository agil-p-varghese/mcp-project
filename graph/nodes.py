import json

from agents.planner import PLANNER_SYSTEM_PROMPT
from graph.state import BakeryState
from llm_client import llm, MODEL


def planner_node(state: BakeryState):

    # First execution: decompose the business question
    if not state["tasks"]:

        response = llm.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": PLANNER_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": state["business_question"]
                }
            ],
            max_tokens=1000
        )

        result = json.loads(response.choices[0].message.content)

        tasks = result["tasks"]

        # Add execution status to every task
        for task in tasks:
            task["status"] = "pending"

    else:
        tasks = state["tasks"]

    # Find the next pending task
    next_task = next(
        (task for task in tasks if task["status"] == "pending"),
        None
    )

    # No pending tasks means planning is complete
    if next_task is None:
        return {
            "tasks": tasks,
            "current_task": {}
        }

    # Mark the selected task as in progress
    next_task["status"] = "in_progress"

    return {
        "tasks": tasks,
        "current_task": next_task
    }