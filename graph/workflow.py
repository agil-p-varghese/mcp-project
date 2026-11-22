from langgraph.graph import StateGraph, START, END

from graph.state import BakeryState
from graph.nodes import (
    planner_node,
    db_node,
    analyst_node,
    report_node
)


def planner_router(state: BakeryState):

    if not state["current_task"]:
        return "report_agent"

    return "db_agent"


def build_workflow(mcp_client):

    builder = StateGraph(BakeryState)

    # Register agent nodes
    builder.add_node("planner", planner_node)

    # Pass the MCP client to the DB Agent
    async def db_agent_wrapper(state: BakeryState):
        return await db_node(state, mcp_client)

    builder.add_node("db_agent", db_agent_wrapper)
    builder.add_node("analyst", analyst_node)
    builder.add_node("report_agent", report_node)

    # Define workflow connections
    builder.add_edge(START, "planner")

    builder.add_conditional_edges(
        "planner",
        planner_router,
        {
            "db_agent": "db_agent",
            "report_agent": "report_agent"
        }
    )

    builder.add_edge("db_agent", "analyst")
    builder.add_edge("analyst", "planner")

    builder.add_edge("report_agent", END)

    return builder.compile()