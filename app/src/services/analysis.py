import json
from openai import AsyncOpenAI
from src.config import VLLM_API_BASE, VLLM_MODEL_NAME

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

client = AsyncOpenAI(
    base_url=VLLM_API_BASE,
    api_key="not-needed"
)

async def analyze_transcript(transcript: str):
    prompt = PROMPT_TEMPLATE + f"\nТранскрипт:\n{transcript}"
    
    messages = [
        {"role": "system", "content": "Вы — эксперт-аналитик. Ваша задача — вернуть корректный JSON-объект."},
        {"role": "user", "content": prompt}
    ]

    resp = await client.chat.completions.create(
        model=VLLM_MODEL_NAME,
        messages=messages,
        temperature=0.1,
        max_tokens=4096
    )
    text = resp.choices[0].message.content.strip()

    if text.startswith("```json"):
        text = text[7:-3].strip()

    return json.loads(text)