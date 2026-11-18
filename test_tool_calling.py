
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.getenv("HF_TOKEN")
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_readonly_sql",
            "description": "Execute a read-only SQL query against the BakeHouse database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "The SQL SELECT query to execute."
                    }
                },
                "required": ["sql"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="openai/gpt-oss-120b:cheapest",
    messages=[
    {
        "role": "system",
        "content": """
        You are an intelligent PostgreSQL database analyst for BakeHouse Analytics.

        Your job is to answer business questions using the available database tools.

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
    },
    {
        "role": "user",
        "content": "Which store generates the highest sales?"
    }
],
    tools=tools,
    tool_choice="auto"
)

message = response.choices[0].message

print("LLM Response:")
print(message)

if message.tool_calls:
    for tool_call in message.tool_calls:
        print("\nTool Selected:", tool_call.function.name)
        print("Arguments:", json.loads(tool_call.function.arguments))
else:
    print("\nThe model responded without requesting a tool call.")
