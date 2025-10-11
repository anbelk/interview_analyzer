from pathlib import Path
from io import BytesIO
from openpyxl import Workbook

def generate_xlsx_from_analysis(analysis: dict) -> BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = "Interview Analysis"

    ws.append(["Company", "Position", "Vacancy Description"])
    ws.append([
        analysis.get("company", ""),
        analysis.get("position", ""),
        analysis.get("vacancy_description", "")
    ])
    ws.append([])

    ws.append(["Question", "Topic", "Answer"])
    for q in analysis.get("questions", []):
        ws.append([q.get("text"), q.get("topic"), q.get("answer")])

    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio

def save_report(analysis: dict, report_path: Path):
    with open(report_path, "wb") as f:
        f.write(generate_xlsx_from_analysis(analysis).getbuffer())
    return report_path
