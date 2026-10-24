from datetime import date, timedelta
from html import escape
from io import BytesIO
from typing import Mapping

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm as millimeter
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

WeeklyPlan = Mapping[str, Mapping[str, str]]


def _meal_text(value: str) -> str:
    if not value or value == "--- None ---":
        return "Not planned"
    return value


def build_weekly_plan_pdf(week_start: date, days: WeeklyPlan) -> bytes:
    buffer = BytesIO()
    page_size = (90 * millimeter, 300 * millimeter)
    document = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        rightMargin=7 * millimeter,
        leftMargin=7 * millimeter,
        topMargin=8 * millimeter,
        bottomMargin=8 * millimeter,
        title=f"Weekly Meal Plan - {week_start.isoformat()}",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PlanTitle",
        parent=styles["Title"],
        fontSize=15,
        leading=18,
        alignment=1,
        spaceAfter=3 * millimeter,
    )
    subtitle_style = ParagraphStyle(
        "PlanSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        alignment=1,
        textColor=colors.HexColor("#555555"),
        spaceAfter=5 * millimeter,
    )
    day_style = ParagraphStyle(
        "DayHeading",
        parent=styles["Heading2"],
        fontSize=11,
        leading=14,
        spaceAfter=0,
    )
    meal_style = ParagraphStyle(
        "Meal",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        wordWrap="CJK",
    )
    label_style = ParagraphStyle(
        "MealLabel",
        parent=meal_style,
        fontName="Helvetica-Bold",
    )

    story = [
        Paragraph("Weekly Meal Plan", title_style),
        Paragraph(
            f"{week_start.strftime('%b %d')} - "
            f"{(week_start + timedelta(days=6)).strftime('%b %d, %Y')}",
            subtitle_style,
        ),
    ]

    for day_name, details in days.items():
        day_date = date.fromisoformat(details["Date"])
        day_heading = Paragraph(
            f"{escape(day_name)} &nbsp; {day_date.strftime('%a, %b %d')}",
            day_style,
        )
        meals = Table(
            [
                [
                    Paragraph("Lunch", label_style),
                    Paragraph(escape(_meal_text(details.get("Lunch", ""))), meal_style),
                ],
                [
                    Paragraph("Dinner", label_style),
                    Paragraph(escape(_meal_text(details.get("Dinner", ""))), meal_style),
                ],
            ],
            colWidths=[38, document.width - 38],
        )
        meals.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#D9DEE7")),
            ])
        )
        story.append(KeepTogether([day_heading, meals, Spacer(1, 3 * millimeter)]))

    document.build(story)
    return buffer.getvalue()


def build_weekly_plan_html(week_start: date, days: WeeklyPlan) -> str:
    end_date = week_start + timedelta(days=6)
    day_cards = []
    for day_name, details in days.items():
        day_date = date.fromisoformat(details["Date"])
        lunch = escape(_meal_text(details.get("Lunch", "")))
        dinner = escape(_meal_text(details.get("Dinner", "")))
        day_cards.append(
            f"""
            <section class="day">
              <h2>{escape(day_name)} <span>{day_date.strftime('%a, %b %d')}</span></h2>
              <p><strong>Lunch</strong><span>{lunch}</span></p>
              <p><strong>Dinner</strong><span>{dinner}</span></p>
            </section>
            """
        )

    return f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          body {{
            color: #202938;
            font-family: Arial, sans-serif;
            margin: 16px auto;
            max-width: 560px;
            padding: 0 12px;
          }}
          h1 {{ font-size: 1.35rem; margin-bottom: 4px; }}
          .week {{ color: #5a6472; margin: 0 0 16px; }}
          .day {{
            border: 1px solid #d9dee7;
            border-radius: 8px;
            margin: 10px 0;
            padding: 10px 12px;
            break-inside: avoid;
          }}
          h2 {{ font-size: 1rem; margin: 0 0 8px; }}
          h2 span {{ color: #5a6472; font-size: .9rem; font-weight: normal; }}
          p {{ display: grid; grid-template-columns: 54px 1fr; gap: 8px; margin: 6px 0; }}
          button {{ font: inherit; padding: 10px 14px; }}
          @page {{ size: 90mm auto; margin: 5mm; }}
          @media print {{
            body {{ margin: 0; max-width: none; padding: 0; }}
            button {{ display: none; }}
            .day {{ border: 0; border-bottom: 1px solid #d9dee7; border-radius: 0; }}
          }}
        </style>
      </head>
      <body>
        <button onclick="window.print()">Print weekly plan</button>
        <h1>Weekly Meal Plan</h1>
        <p class="week">{week_start.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}</p>
        {''.join(day_cards)}
      </body>
    </html>
    """
