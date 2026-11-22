
import asyncio
import os
import json
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from fastmcp import Client


load_dotenv()

# Hugging Face LLM connection
llm = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.getenv("HF_TOKEN")
)

MODEL = "openai/gpt-oss-120b:cheapest"


SYSTEM_PROMPT = """
You are an intelligent PostgreSQL database analyst for BakeHouse Analytics.

Your job is to answer business questions using the available MCP tools.

Rules:
1. Always call inspect_schema before generating SQL.
2. Use the schema returned by inspect_schema to identify valid tables and columns.
3. Generate PostgreSQL-compatible SQL only.
4. Never invent table names or column names.
5. Use execute_readonly_sql to execute database queries.
6. Execute only read-only SQL queries.
7. Use summarize_results to analyze query results.
8. Use generate_report to generate the final business report.
9. Never fabricate database results.
"""


def convert_mcp_tools_to_openai(mcp_tools):

    openai_tools = []

    for tool in mcp_tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.input_schema
            }
        })

    return openai_tools



async def main():

    # Import here to avoid circular imports:
    # graph.nodes imports llm and MODEL from this file.
    from graph.workflow import build_workflow

    async with Client(Path("main.py")) as mcp_client:

        print("Connected to BakeHouse MCP Server!")

        # Build the LangGraph workflow
        workflow = build_workflow(mcp_client)

        # Initial shared state
        initial_state = {
            "business_question": "Which is the store having highest sales?",
            "tasks": [],
            "current_task": {},
            "schema": {},
            "sql_queries": [],
            "query_results": [],
            "task_analyses": [],
            "observations": [],
            "final_resolution": "",
            "final_report": ""
        }

        print("\nStarting Bakery Analytics Workflow...")

        # Execute the complete multi-agent workflow
        final_state = await workflow.ainvoke(initial_state)

        print("\n========== FINAL REPORT ==========\n")
        print(final_state["final_report"])

        print("\n========== EXECUTION SUMMARY ==========\n")
        print("Tasks:", len(final_state["tasks"]))
        print("SQL queries executed:", len(final_state["sql_queries"]))
        print("Analyses completed:", len(final_state["task_analyses"]))


if __name__ == "__main__":
    asyncio.run(main())


