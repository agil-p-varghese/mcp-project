
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

        
        # Conversation history
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": business_question
            }
        ]

        # Generic LLM tool-calling loop
        while True:

            response = llm.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=openai_tools,
                tool_choice="auto",
                max_tokens=500
            )

            message = response.choices[0].message

            print("\nLLM Response:")
            print(message)

            # Stop when the LLM has no more tool calls
            if not message.tool_calls:
                print("\nFinal LLM Answer:")
                print(message.content)
                break

            # Preserve the assistant's tool-call message
            messages.append(
                message.model_dump(exclude_none=True)
            )

            # Execute every tool selected by the LLM
            for tool_call in message.tool_calls:

                tool_name = tool_call.function.name

                arguments = json.loads(
                    tool_call.function.arguments
                )

                print("\nTool Selected:", tool_name)
                print("Arguments:", arguments)

                print("\nExecuting MCP Tool...")

                result = await mcp_client.call_tool(
                    tool_name,
                    arguments
                )

                # Extract structured result
                tool_result = result.structured_content

                print("\nMCP Tool Result:")
                print(tool_result)

                # Send the result back to the LLM
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result, default=str)
                    }
                )

if __name__ == "__main__":
    asyncio.run(main())
