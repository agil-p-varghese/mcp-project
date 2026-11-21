
from typing import TypedDict, List, Dict, Any


class BakeryState(TypedDict):

    # Original user input
    business_question: str

    # Planner information
    tasks: List[Dict[str, Any]]
    current_task: Dict[str, Any]

    # Database execution information
    sql_queries: List[str]
    query_results: List[Dict[str, Any]]

    # Analyst information
    task_analyses: List[Dict[str, Any]]

    # Planner's consolidated findings
    observations: List[str]
    final_resolution: str

    # Report generation
    final_report: str
