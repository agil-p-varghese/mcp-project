
from typing import Any
from datetime import datetime


def register_report_tools(mcp):

    @mcp.tool()
    def generate_report(
        business_question: str,
        query_results: dict[str, Any],
        summary_results: dict[str, Any]
    ) -> dict:
        """
        Generate a structured business report using SQL
        query results and their statistical summary.
        """

        rows = query_results.get("rows", [])
        findings = summary_results.get("key_findings", [])

        report = []

        report.append("# BakeHouse Analytics Report")
        report.append("")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        report.append("## 1. Business Objective")
        report.append(business_question)
        report.append("")

        report.append("## 2. Dataset Overview")
        report.append(f"- Records analyzed: {len(rows)}")
        report.append("")

        report.append("## 3. Key Findings")

        if not findings:
            report.append("No numerical findings available.")
        else:
            for finding in findings:
                report.append(f"### Metric: {finding['metric']}")
                report.append(f"- Total: {finding['total']}")
                report.append(f"- Average: {finding['average']}")
                report.append(f"- Maximum: {finding['maximum']}")
                report.append(f"- Minimum: {finding['minimum']}")
                report.append("")

        report.append("## 4. Query Results")

        if rows:
            report.append("```json")
            import json
            report.append(json.dumps(rows, indent=2))
            report.append("```")
        else:
            report.append("No records returned.")

        report.append("")
        report.append("## 5. Conclusion")

        if findings:
            report.append(
                "The analysis provides an overview of the "
                "selected business metrics and their performance."
            )
        else:
            report.append(
                "Insufficient numerical data was available "
                "to generate analytical conclusions."
            )

        return {
            "report_title": "BakeHouse Analytics Report",
            "generated_at": datetime.now().isoformat(),
            "report": "\n".join(report),
            "records_analyzed": len(rows)
        }

    return mcp
