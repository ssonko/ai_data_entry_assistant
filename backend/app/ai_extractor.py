import json
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def extract_data(file_content: str, user_prompt: str):

    try:
        response = await client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {
                    "role": "system",
                    "content": """
You extract and summarize key details from PDF text.

Return structured JSON.

Rules:
- Return valid JSON only.
- No markdown.
- No explanations outside JSON.
- If multiple records exist, return a JSON array.
- If a field is missing, return null.
- Do not invent data.
"""
                },
                {
                    "role": "user",
                    "content": f"""
{user_prompt}

DOCUMENT:
{file_content}
"""
                }
            ]
        )

        content = response.choices[0].message.content.strip()

        return json.loads(content)

    except Exception as e:
        print("Extraction error:", e)
        return None