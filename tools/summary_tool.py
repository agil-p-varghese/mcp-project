
from typing import Any


def register_summary_tools(mcp):

    @mcp.tool()
    def summarize_results(
        business_question: str,
        results: dict[str, Any]
    ) -> dict:
        """
        Summarize SQL query results into business insights.

        Accepts structured SQL results and a business question.
        Identifies result size, numerical columns and key findings.
        """

        rows = results.get("rows", [])
        columns = results.get("columns", [])

        if not rows:
            return {
                "business_question": business_question,
                "summary": "The query returned no records.",
                "key_findings": []
            }

        findings = []

        # Identify numerical columns
        numeric_columns = []

        for column in columns:
            values = []

            for row in rows:
                value = row.get(column)

                if value is not None:
                    try:
                        values.append(float(value))
                    except (ValueError, TypeError):
                        pass

            if values:
                numeric_columns.append((column, values))

        # Generate basic statistics
        for column, values in numeric_columns:

            findings.append({
                "metric": column,
                "total": round(sum(values), 2),
                "average": round(sum(values) / len(values), 2),
                "maximum": round(max(values), 2),
                "minimum": round(min(values), 2)
            })

        return {
            "business_question": business_question,
            "total_records": len(rows),
            "key_findings": findings,
            "data": rows
        }

    return mcp
