from openai import OpenAI
from pathlib import Path
import json

client = OpenAI()

PROMPT_TEMPLATE = """
Ты получаешь транскрипт технического интервью программиста.
Нужно извлечь из текста структурированные данные и вернуть результат строго в JSON формате:

{
  "company": "Название компании",
  "position": "Название должности",
  "vacancy_description": "Краткое описание",
  "questions": [
    {
      "text": "Формулировка вопроса",
      "topic": "Категория (Математика, ML-теория, Data Science, NLP, CV, Алгоритмы и структуры данных, Программирование, SQL)",
      "answer": "Ответ кандидата"
    }
  ]
}

Транскрипт:
{transcript}
"""

def analyze_transcript(file_path: Path) -> dict:
    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} not found")

    transcript = file_path.read_text(encoding="utf-8")

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "Ты помощник для анализа интервью."},
            {"role": "user", "content": PROMPT_TEMPLATE.format(transcript=transcript)}
        ],
        temperature=0.2,
    )

    raw_output = response.choices[0].message.content.strip()

    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        raise ValueError(f"LLM вернул некорректный JSON: {raw_output}")
