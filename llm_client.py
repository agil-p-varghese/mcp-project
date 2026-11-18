
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

    async with Client(Path("main.py")) as mcp_client:

        print("Connected to BakeHouse MCP Server!")

        # Discover MCP tools
        mcp_tools = await mcp_client.list_tools()

        # Convert tools for the LLM
        openai_tools = convert_mcp_tools_to_openai(mcp_tools)

        # Business question
        business_question = "Which store generates the highest sales?"

        # Send question to Hugging Face LLM
        response = llm.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": business_question
                }
            ],
            tools=openai_tools,
            tool_choice="auto",
            max_tokens=500
        )

        message = response.choices[0].message

        print("\nLLM Response:")
        print(message)

        
        if message.tool_calls:

            for tool_call in message.tool_calls:

                tool_name = tool_call.function.name

                arguments = json.loads(
                    tool_call.function.arguments
                )

                print("\nTool Selected:", tool_name)
                print("Arguments:", arguments)

                # For this test, execute only inspect_schema
                if tool_name == "inspect_schema":

                    print("\nExecuting MCP Tool...")

                    result = await mcp_client.call_tool(
                        tool_name,
                        arguments
                    )

                    # Extract structured schema
                    schema = result.structured_content

                    print("\nSchema retrieved successfully!")

                    # Send schema back to the LLM
                    messages = [
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT
                        },
                        {
                            "role": "user",
                            "content": business_question
                        },
                        {
                            "role": "assistant",
                            "tool_calls": [
                                {
                                    "id": tool_call.id,
                                    "type": "function",
                                    "function": {
                                        "name": tool_name,
                                        "arguments": json.dumps(arguments)
                                    }
                                }
                            ]
                        },
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(schema)
                        }
                    ]

                    # Ask the LLM to continue
                    next_response = llm.chat.completions.create(
                        model=MODEL,
                        messages=messages,
                        tools=openai_tools,
                        tool_choice="auto",
                        max_tokens=500
                    )

                    print("\nLLM Response After Schema Inspection:")
                    print(next_response.choices[0].message)

                    #adding logic for execute read_only sql tool
                    next_message = next_response.choices[0].message

                    if next_message.tool_calls:

                        for next_tool_call in next_message.tool_calls:

                            tool_name = next_tool_call.function.name

                            arguments = json.loads(
                                next_tool_call.function.arguments
                            )

                            print("\nNext Tool Selected:", tool_name)
                            print("Arguments:", arguments)

                            if tool_name == "execute_readonly_sql":

                                print("\nExecuting SQL through MCP...")

                                query_result = await mcp_client.call_tool(
                                    tool_name,
                                    arguments
                                )

                                print("\nDatabase Query Result:")
                                print("======================")
                                print(query_result)

                                ###

                                # Extract structured query results
                                query_data = query_result.structured_content

                                # Add SQL execution result to conversation
                                messages.extend([
                                    {
                                        "role": "assistant",
                                        "tool_calls": [
                                            {
                                                "id": next_tool_call.id,
                                                "type": "function",
                                                "function": {
                                                    "name": tool_name,
                                                    "arguments": json.dumps(arguments)
                                                }
                                            }
                                        ]
                                    },
                                    {
                                        "role": "tool",
                                        "tool_call_id": next_tool_call.id,
                                        "content": json.dumps(query_data)
                                    }
                                ])

                                # Ask LLM for the next action
                                summary_response = llm.chat.completions.create(
                                    model=MODEL,
                                    messages=messages,
                                    tools=openai_tools,
                                    tool_choice="auto",
                                    max_tokens=500
                                )

                                print("\nLLM Response After SQL Execution:")
                                print(summary_response.choices[0].message)
                                #
                                #logic for summarize tool.py
                                #
                                summary_message = summary_response.choices[0].message

                                if summary_message.tool_calls:

                                    for summary_tool_call in summary_message.tool_calls:

                                        summary_tool_name = summary_tool_call.function.name

                                        summary_arguments = json.loads(
                                            summary_tool_call.function.arguments
                                        )

                                        print("\nNext Tool Selected:", summary_tool_name)
                                        print("Arguments:", summary_arguments)

                                        if summary_tool_name == "summarize_results":

                                            print("\nExecuting Summary Tool...")

                                            summary_result = await mcp_client.call_tool(
                                                summary_tool_name,
                                                summary_arguments
                                            )

                                            print("\nSummary Result:")
                                            print("================")
                                            print(summary_result.structured_content)
                                        else:
                                            print("Tool execution skipped for this test.")

            else:
                print("\nLLM responded without selecting a tool.")



if __name__ == "__main__":
    asyncio.run(main())
