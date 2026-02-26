import json
from openai import OpenAI
from .config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

async def extract_data(file_content: str, user_prompt: str):

    response = client.chat.completions.create(
        model="gpt-5.nano",
        messages=[
            {"role": "system", "content": "Return structured JSON only."},
            {
                "role": "user",
                "content": f"""
                Extract the following:
                {user_prompt}

                Return valid JSON only.
                Document:
                {file_content}
                """
            }
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except:
        return None
