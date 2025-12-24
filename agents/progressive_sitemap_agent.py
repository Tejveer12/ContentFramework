import aiohttp
import json
from prompts.sitemap_system_prompt import SYSTEM_PROMPT
from config import MODEL_NAME, LOCAL_API_URL

async def update_sitemap(previous_sitemap: dict, new_input: str) -> dict:
    user_prompt = f"""
EXISTING SITEMAP (JSON):
{json.dumps(previous_sitemap, indent=2)}

NEW INPUT:
{new_input}

TASK:
- Update the existing sitemap using the new input
- Do NOT remove existing pages unless explicitly contradicted
- Add new pages, sections, collections, or products if mentioned
- Update Header/Footer placement if clarified
- Preserve wording wherever possible
- Output the FULL updated sitemap
- Output ONLY valid JSON
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "top_p": 0.8,
        "max_tokens": 3500,
        "stop": ["</s>", "```"],
        "stream": False
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            LOCAL_API_URL,
            json=payload,
            timeout=60
        ) as response:

            if response.status != 200:
                raise RuntimeError(await response.text())

            data = await response.json()
            content = data["choices"][0]["message"]["content"].strip()

    return content
