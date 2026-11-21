
from langgraph.graph import StateGraph, START, END

from graph.state import BakeryState


def build_workflow():

    # Initialize graph with shared state
    builder = StateGraph(BakeryState)

    # Register agent nodes
    builder.add_node("planner", planner_node)
    builder.add_node("db_agent", db_node)
    builder.add_node("analyst", analyst_node)
    builder.add_node("report_agent", report_node)

    # Define workflow edges
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "db_agent")
    builder.add_edge("db_agent", "analyst")
    builder.add_edge("analyst", "planner")

    # Compile graph
    workflow = builder.compile()

    return workflow

#planner router
def planner_router(state: BakeryState):

    if not state["current_task"]:
        return "report_agent"

    return "db_agent"