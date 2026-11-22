import json
from agents.analyst import ANALYST_SYSTEM_PROMPT
from agents.report_agent import REPORT_SYSTEM_PROMPT
from agents.db_agent import DB_AGENT_SYSTEM_PROMPT
from agents.planner import PLANNER_SYSTEM_PROMPT
from graph.state import BakeryState
from llm_client import llm, MODEL
from langsmith import traceable

#mcp helper for tracing
def create_mcp_tool_callers(mcp_client):

    @traceable(name="inspect_schema", run_type="tool")
    async def inspect_schema():

        result = await mcp_client.call_tool(
            "inspect_schema", {}
        )

        return result.structured_content

    @traceable(name="execute_readonly_sql", run_type="tool")
    async def execute_readonly_sql(sql: str):

        result = await mcp_client.call_tool(
            "execute_readonly_sql",
            {"sql": sql}
        )

        return result.structured_content

    return {
        "inspect_schema": inspect_schema,
        "execute_readonly_sql": execute_readonly_sql
    }


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

#db node

async def db_node(state: BakeryState, mcp_tools):

    # 1. Inspect schema if it hasn't been loaded yet
    schema = await mcp_tools["inspect_schema"]()

    if not schema:
        schema = await mcp_tools["inspect_schema"]()


    # 2. Get the current task
    task = state["current_task"]

    # 3. Ask the LLM to generate SQL
    response = llm.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": DB_AGENT_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": f"""
                Database schema:
                {json.dumps(schema, indent=2)}

                Business question:
                {task['business_question']}

                Generate one PostgreSQL SELECT query.
                Return only the SQL query, without markdown.
                """
            }
        ],
        max_tokens=500
    )

    sql = response.choices[0].message.content.strip()

    # Remove markdown fences if the model returns them
    sql = sql.replace("```sql", "").replace("```", "").strip()

    # 4. Execute SQL through MCP
    result = await mcp_tools["execute_readonly_sql"](sql)

    # 5. Return updated shared state
    return {
        "schema": schema,
        "sql_queries": state.get("sql_queries", []) + [sql],
        "query_results": state.get("query_results", []) + [
            {
                "task_id": task["task_id"],
                "business_question": task["business_question"],
                "sql": sql,
                "result": result
            }
        ]
    }

#analyst node

def analyst_node(state: BakeryState):

    # Get the latest database result
    query_data = state["query_results"][-1]

    task = state["current_task"]

    response = llm.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": ANALYST_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": f"""
                Business question:
                {task['business_question']}

                SQL query:
                {query_data['sql']}

                Database result:
                {json.dumps(query_data['result'], indent=2)}

                Analyze these results and provide business findings.
                """
            }
        ],
        max_tokens=700
    )

    analysis = response.choices[0].message.content

    # Mark the current task as completed
    tasks = state["tasks"]

    for item in tasks:
        if item["task_id"] == task["task_id"]:
            item["status"] = "completed"
            break

    return {
        "tasks": tasks,
        "task_analyses": state.get("task_analyses", []) + [
            {
                "task_id": task["task_id"],
                "business_question": task["business_question"],
                "analysis": analysis
            }
        ],
        "observations": state.get("observations", []) + [analysis]
    }

#report_agent node

def report_node(state: BakeryState):

    response = llm.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": REPORT_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": f"""
                Original business question:
                {state['business_question']}

                Completed task analyses:
                {json.dumps(state['task_analyses'], indent=2)}

                Consolidated observations:
                {json.dumps(state['observations'], indent=2)}

                Generate the final business report.
                """
            }
        ],
        max_tokens=1500
    )

    final_report = response.choices[0].message.content

    return {
        "final_report": final_report
    }