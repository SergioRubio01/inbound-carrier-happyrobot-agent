#!/usr/bin/env python3
"""
File: cli.py
Description: CLI tool for HappyRobot metrics fetching and PDF report generation
Author: HappyRobot Team
Created: 2024-08-21
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Flowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class MetricsCLI:
    """CLI tool for fetching and reporting HappyRobot metrics."""

    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

    async def fetch_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000,
    ) -> Dict[str, Any]:
        """Fetch metrics data from the API."""
        try:
            params: Dict[str, Any] = {"limit": limit}
            if start_date:
                params["start_date"] = start_date.isoformat()
            if end_date:
                params["end_date"] = end_date.isoformat()

            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                # Fetch individual call metrics
                response = await client.get(
                    f"{self.api_url}/api/v1/metrics/call",
                    headers=self.headers,
                    params=params,
                )

                if response.status_code in [404, 405]:
                    print(
                        "Warning: Phase 2 endpoints not yet implemented. Using fallback data."
                    )
                    return self._generate_fallback_data(start_date, end_date)

                response.raise_for_status()
                call_data = response.json()

                # Fetch summary statistics
                summary_response = await client.get(
                    f"{self.api_url}/api/v1/metrics/call/summary",
                    headers=self.headers,
                    params=params,
                )

                if summary_response.status_code in [404, 405]:
                    # Generate summary from call data
                    summary_data = self._calculate_summary_from_calls(call_data)
                else:
                    summary_response.raise_for_status()
                    summary_data = summary_response.json()

                return {
                    "call_metrics": call_data.get("metrics", []),
                    "summary": summary_data,
                    "total_count": call_data.get(
                        "total_count", len(call_data.get("metrics", []))
                    ),
                    "period": {
                        "start": start_date.isoformat() if start_date else None,
                        "end": end_date.isoformat() if end_date else None,
                    },
                }

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError("Authentication failed. Please check your API key.")
            elif e.response.status_code == 404:
                raise ValueError(
                    "API endpoint not found. Phase 2 might not be implemented yet."
                )
            else:
                raise ValueError(
                    f"API request failed: {e.response.status_code} - {e.response.text}"
                )
        except httpx.ConnectError:
            raise ValueError(
                f"Cannot connect to API at {self.api_url}. Please check the URL and ensure the service is running."
            )
        except Exception as e:
            raise ValueError(f"Unexpected error fetching metrics: {str(e)}")

    def _generate_fallback_data(
        self, start_date: Optional[datetime], end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Generate fallback data when Phase 2 endpoints are not available."""
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()

        # Generate sample data for demonstration
        sample_metrics = []
        for i in range(10):
            call_date = start_date + timedelta(days=i * 0.7)
            sample_metrics.append(
                {
                    "metrics_id": f"sample-{i:04d}-{call_date.strftime('%Y%m%d')}",
                    "transcript": f"Sample call transcript {i + 1}...",
                    "response": ["Success", "Rate too high", "Fallback error"][i % 3],
                    "response_reason": "Rate negotiation" if i % 3 == 1 else None,
                    "sentiment": ["Positive", "Neutral", "Negative"][i % 3],
                    "sentiment_reason": "Successful negotiation"
                    if i % 3 == 0
                    else "Price concerns"
                    if i % 3 == 1
                    else "Technical issues",
                    "created_at": call_date.isoformat(),
                }
            )

        return {
            "call_metrics": sample_metrics,
            "summary": {
                "total_calls": len(sample_metrics),
                "success_rate": 0.33,
                "response_distribution": {
                    "Success": 3,
                    "Rate too high": 4,
                    "Fallback error": 3,
                },
                "sentiment_distribution": {"Positive": 3, "Neutral": 4, "Negative": 3},
                "top_response_reasons": [{"reason": "Rate negotiation", "count": 4}],
                "top_sentiment_reasons": [{"reason": "Price concerns", "count": 4}],
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
            },
            "total_count": len(sample_metrics),
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        }

    def _calculate_summary_from_calls(
        self, call_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate summary statistics from individual call metrics."""
        metrics = call_data.get("metrics", [])

        if not metrics:
            return {
                "total_calls": 0,
                "success_rate": 0.0,
                "response_distribution": {},
                "sentiment_distribution": {},
                "top_response_reasons": [],
                "top_sentiment_reasons": [],
            }

        total_calls = len(metrics)
        successful_calls = sum(1 for m in metrics if m.get("response") == "Success")
        success_rate = successful_calls / total_calls if total_calls > 0 else 0.0

        # Response distribution
        response_dist: Dict[str, int] = {}
        for metric in metrics:
            response = metric.get("response", "Unknown")
            response_dist[response] = response_dist.get(response, 0) + 1

        # Sentiment distribution
        sentiment_dist: Dict[str, int] = {}
        for metric in metrics:
            sentiment = metric.get("sentiment")
            if sentiment:
                sentiment_dist[sentiment] = sentiment_dist.get(sentiment, 0) + 1

        # Top response reasons
        response_reasons: Dict[str, int] = {}
        for metric in metrics:
            if metric.get("response_reason"):
                reason = metric.get("response_reason")
                response_reasons[reason] = response_reasons.get(reason, 0) + 1

        top_response_reasons = [
            {"reason": reason, "count": count}
            for reason, count in sorted(
                response_reasons.items(), key=lambda x: x[1], reverse=True
            )
        ][:10]  # Top 10

        # Top sentiment reasons
        sentiment_reasons: Dict[str, int] = {}
        for metric in metrics:
            if metric.get("sentiment_reason"):
                reason = metric.get("sentiment_reason")
                sentiment_reasons[reason] = sentiment_reasons.get(reason, 0) + 1

        top_sentiment_reasons = [
            {"reason": reason, "count": count}
            for reason, count in sorted(
                sentiment_reasons.items(), key=lambda x: x[1], reverse=True
            )
        ][:10]  # Top 10

        return {
            "total_calls": total_calls,
            "success_rate": success_rate,
            "response_distribution": response_dist,
            "sentiment_distribution": sentiment_dist,
            "top_response_reasons": top_response_reasons,
            "top_sentiment_reasons": top_sentiment_reasons,
        }

    def generate_pdf_report(
        self, metrics_data: Dict[str, Any], output_file: str
    ) -> None:
        """Generate PDF report from metrics data."""
        try:
            doc = SimpleDocTemplate(output_file, pagesize=A4)
            story: List[Flowable] = []
            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Title"],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
            )

            heading_style = ParagraphStyle(
                "CustomHeading",
                parent=styles["Heading2"],
                fontSize=16,
                spaceAfter=12,
                spaceBefore=20,
            )

            # Title
            title = Paragraph("HappyRobot Metrics Report", title_style)
            story.append(title)

            # Report metadata
            period = metrics_data.get("period", {})
            start_date = period.get("start", "N/A")
            end_date = period.get("end", "N/A")
            generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

            metadata = f"""
            <para align="center">
            Report Period: {start_date[:10] if start_date != "N/A" else "N/A"} to {end_date[:10] if end_date != "N/A" else "N/A"}<br/>
            Generated: {generated_at}<br/>
            Total Records: {metrics_data.get("total_count", 0)}
            </para>
            """
            story.append(Paragraph(metadata, styles["Normal"]))
            story.append(Spacer(1, 20))

            # Summary statistics
            summary = metrics_data.get("summary", {})
            story.append(Paragraph("Summary Statistics", heading_style))

            summary_data = [
                ["Metric", "Value"],
                ["Total Calls", str(summary.get("total_calls", 0))],
                ["Success Rate", f"{summary.get('success_rate', 0):.2%}"],
            ]

            summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
            summary_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 14),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            story.append(summary_table)
            story.append(Spacer(1, 20))

            # Response distribution
            response_dist = summary.get("response_distribution", {})
            if response_dist:
                story.append(Paragraph("Response Distribution", heading_style))

                dist_data = [["Response", "Count", "Percentage"]]
                total_responses = sum(response_dist.values())

                for response, count in response_dist.items():
                    percentage = (
                        (count / total_responses * 100) if total_responses > 0 else 0
                    )
                    dist_data.append([response, str(count), f"{percentage:.1f}%"])

                dist_table = Table(
                    dist_data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch]
                )
                dist_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 14),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ]
                    )
                )
                story.append(dist_table)
                story.append(Spacer(1, 20))

            # Sentiment distribution
            sentiment_dist = summary.get("sentiment_distribution", {})
            if sentiment_dist:
                story.append(Paragraph("Sentiment Distribution", heading_style))

                sentiment_data = [["Sentiment", "Count", "Percentage"]]
                total_sentiments = sum(sentiment_dist.values())

                for sentiment, count in sentiment_dist.items():
                    percentage = (
                        (count / total_sentiments * 100) if total_sentiments > 0 else 0
                    )
                    sentiment_data.append([sentiment, str(count), f"{percentage:.1f}%"])

                sentiment_table = Table(
                    sentiment_data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch]
                )
                sentiment_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 14),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ]
                    )
                )
                story.append(sentiment_table)
                story.append(Spacer(1, 20))

            # Top response reasons
            response_reasons = summary.get("top_response_reasons", [])
            if response_reasons:
                story.append(Paragraph("Top Response Reasons", heading_style))

                # Create a style for wrapping text in reason cells
                reason_cell_style = ParagraphStyle(
                    "ReasonCellStyle",
                    parent=styles["Normal"],
                    fontSize=10,
                    leading=12,
                )

                reasons_data = [["Reason", "Count"]]
                for reason_info in response_reasons[:10]:  # Top 10
                    reason_text = reason_info.get("reason", "N/A")
                    reasons_data.append(
                        [
                            Paragraph(reason_text, reason_cell_style)
                            if len(reason_text) > 40
                            else reason_text,
                            str(reason_info.get("count", 0)),
                        ]
                    )

                reasons_table = Table(reasons_data, colWidths=[4 * inch, 1 * inch])
                reasons_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 14),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ]
                    )
                )
                story.append(reasons_table)
                story.append(Spacer(1, 20))

            # Top sentiment reasons
            sentiment_reasons = summary.get("top_sentiment_reasons", [])
            if sentiment_reasons:
                story.append(Paragraph("Top Sentiment Reasons", heading_style))

                # Create a style for wrapping text in sentiment reason cells
                sentiment_reason_cell_style = ParagraphStyle(
                    "SentimentReasonCellStyle",
                    parent=styles["Normal"],
                    fontSize=10,
                    leading=12,
                )

                sentiment_reasons_data = [["Reason", "Count"]]
                for reason_info in sentiment_reasons[:10]:  # Top 10
                    sentiment_reason_text = reason_info.get("reason", "N/A")
                    sentiment_reasons_data.append(
                        [
                            Paragraph(
                                sentiment_reason_text, sentiment_reason_cell_style
                            )
                            if len(sentiment_reason_text) > 40
                            else sentiment_reason_text,
                            str(reason_info.get("count", 0)),
                        ]
                    )

                sentiment_reasons_table = Table(
                    sentiment_reasons_data, colWidths=[4 * inch, 1 * inch]
                )
                sentiment_reasons_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 14),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ]
                    )
                )
                story.append(sentiment_reasons_table)
                story.append(Spacer(1, 20))

            # Detailed metrics table
            call_metrics = metrics_data.get("call_metrics", [])
            if call_metrics:
                story.append(PageBreak())
                story.append(Paragraph("Detailed Call Metrics", heading_style))

                # Limit to first 50 calls for PDF readability
                limited_metrics = call_metrics[:50]
                if len(call_metrics) > 50:
                    story.append(
                        Paragraph(
                            f"Showing first 50 of {len(call_metrics)} total calls",
                            styles["Normal"],
                        )
                    )
                    story.append(Spacer(1, 10))

                # Create a style for wrapping text in cells
                cell_style = ParagraphStyle(
                    "CellStyle",
                    parent=styles["Normal"],
                    fontSize=8,
                    leading=10,
                )

                metrics_data_table = [
                    ["Date", "Response", "Sentiment", "Response Reason"]
                ]

                for metric in limited_metrics:
                    created_at = metric.get("created_at", "N/A")
                    date_str = created_at[:10] if created_at != "N/A" else "N/A"

                    response = metric.get("response", "N/A")
                    sentiment = metric.get("sentiment", "N/A")
                    response_reason = (
                        metric.get("response_reason", "N/A")
                        if metric.get("response_reason")
                        else "N/A"
                    )

                    # Wrap long text in Paragraph objects for proper text wrapping
                    metrics_data_table.append(
                        [
                            date_str,
                            Paragraph(response, cell_style)
                            if len(response) > 20
                            else response,
                            Paragraph(sentiment, cell_style)
                            if len(sentiment) > 20
                            else sentiment,
                            Paragraph(response_reason, cell_style)
                            if len(response_reason) > 30
                            else response_reason,
                        ]
                    )

                detailed_table = Table(
                    metrics_data_table,
                    colWidths=[1.5 * inch, 1.2 * inch, 1.3 * inch, 2.5 * inch],
                )
                detailed_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 10),
                            ("FONTSIZE", (0, 1), (-1, -1), 8),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ]
                    )
                )
                story.append(detailed_table)

            # Build PDF
            doc.build(story)
            print(f"PDF report generated successfully: {output_file}")

        except Exception as e:
            raise ValueError(f"Error generating PDF report: {str(e)}")

    def output_json(self, metrics_data: Dict[str, Any], output_file: str) -> None:
        """Output metrics data as JSON."""
        try:
            with open(output_file, "w") as f:
                json.dump(metrics_data, f, indent=2, default=str)
            print(f"JSON output saved successfully: {output_file}")
        except Exception as e:
            raise ValueError(f"Error saving JSON output: {str(e)}")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="HappyRobot Metrics CLI - Generate reports from call metrics data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate PDF report for last 7 days
  python -m src.interfaces.cli --api-key YOUR_KEY

  # Generate report for specific date range
  python -m src.interfaces.cli --api-key YOUR_KEY --start-date 2024-01-01 --end-date 2024-01-31

  # Output as JSON instead of PDF
  python -m src.interfaces.cli --api-key YOUR_KEY --format json

  # Use with AWS deployment
  python -m src.interfaces.cli --api-url https://your-aws-api.com --api-key YOUR_KEY

  # Custom output file
  python -m src.interfaces.cli --api-key YOUR_KEY --output january_report.pdf
        """,
    )

    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)",
    )

    parser.add_argument("--api-key", required=True, help="API key for authentication")

    parser.add_argument(
        "--start-date",
        type=lambda s: datetime.fromisoformat(s),
        help="Start date in YYYY-MM-DD format (default: 7 days ago)",
    )

    parser.add_argument(
        "--end-date",
        type=lambda s: datetime.fromisoformat(s),
        help="End date in YYYY-MM-DD format (default: now)",
    )

    parser.add_argument(
        "--output",
        default="metrics_report.pdf",
        help="Output file name (default: metrics_report.pdf)",
    )

    parser.add_argument(
        "--format",
        choices=["pdf", "json"],
        default="pdf",
        help="Output format: pdf or json (default: pdf)",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum number of records to fetch (default: 1000)",
    )

    return parser.parse_args()


async def main():
    """Main CLI entry point."""
    try:
        args = parse_arguments()

        # Default date range: last 7 days if not specified
        if not args.start_date and not args.end_date:
            args.end_date = datetime.now()
            args.start_date = args.end_date - timedelta(days=7)
        elif args.start_date and not args.end_date:
            args.end_date = datetime.now()
        elif not args.start_date and args.end_date:
            args.start_date = args.end_date - timedelta(days=7)

        # Validate date range
        if args.start_date and args.end_date and args.start_date > args.end_date:
            print("Error: Start date cannot be after end date.", file=sys.stderr)
            sys.exit(1)

        # Initialize CLI
        cli = MetricsCLI(args.api_url, args.api_key)

        print(f"Fetching metrics from {args.api_url}")
        print(
            f"Date range: {args.start_date.strftime('%Y-%m-%d')} to {args.end_date.strftime('%Y-%m-%d')}"
        )

        # Fetch metrics
        metrics_data = await cli.fetch_metrics(
            args.start_date, args.end_date, args.limit
        )

        print(f"Retrieved {metrics_data.get('total_count', 0)} metrics records")

        # Generate output
        if args.format == "pdf":
            if not args.output.endswith(".pdf"):
                args.output += ".pdf"
            cli.generate_pdf_report(metrics_data, args.output)
        else:
            if not args.output.endswith(".json"):
                args.output += ".json"
            cli.output_json(metrics_data, args.output)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
