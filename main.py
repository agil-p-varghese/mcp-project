
from tools.schema_tool import mcp
from tools.summary_tool import register_summary_tools
from tools.report_tool import register_report_tools

register_summary_tools(mcp)
register_report_tools(mcp)


if __name__ == "__main__":
    mcp.run()
