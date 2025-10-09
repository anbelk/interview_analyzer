import json
from openai import AsyncOpenAI

PROMPT_TEMPLATE = """
Ты получаешь транскрипт технического интервью программиста.

Твоя задача — вернуть строго валидный JSON без лишнего текста и комментариев.

Формат ответа:
{
  "company": "Название компании",
  "position": "Название должности",
  "vacancy_description": "Краткое описание",
  "questions": [
    {
      "text": "Формулировка вопроса",
      "topic": "Категория из списка",
      "answer": "Ответ кандидата"
    }
  ]
}

ДОПУСТИМЫЕ ТЕМАТИКИ (значение поля "topic"):
- "Математика"
- "ML-теория"
- "Data Science"
- "NLP"
- "CV"
- "Алгоритмы и структуры данных"
- "Программирование (языки и парадигмы)"
- "SQL"

ПРАВИЛА:
1. Используй только одну тему из списка выше.
2. Если вопрос охватывает несколько тем — выбери основную.
3. Если не удаётся однозначно определить тему — используй ближайшую по смыслу.
"""


client = AsyncOpenAI()

async def analyze_transcript(transcript: str):
    prompt = PROMPT_TEMPLATE + f"\nТранскрипт:\n{transcript}"
    resp = await client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    text = resp.choices[0].message.content.strip()
    return json.loads(text)
