from pathlib import Path
from openpyxl import Workbook

def export_to_xlsx(json_data: dict, output_file: Path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Interview Analysis"

    ws.append(["Company", "Position", "Vacancy Description"])
    ws.append([json_data.get("company"), json_data.get("position"), json_data.get("vacancy_description")])
    ws.append([])

    ws.append(["Question", "Topic", "Answer"])
    for q in json_data.get("questions", []):
        ws.append([q.get("text"), q.get("topic"), q.get("answer")])

    wb.save(output_file)
