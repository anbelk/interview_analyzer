import json
from openai import AsyncOpenAI

PROMPT_TEMPLATE = """
Ты получаешь транскрипт технического интервью программиста.
Верни JSON:
{
    "company": "Название компании",
    "position": "Название должности",
    "vacancy_description": "Краткое описание",
    "questions": [
        {"text": "...", "topic": "...", "answer": "..."}
    ]
}
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
