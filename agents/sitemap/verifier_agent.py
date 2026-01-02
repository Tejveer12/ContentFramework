import aiohttp
import json
from agents.sitemap.sitemap_system_prompt import SYSTEM_PROMPT
from agents.sitemap.verifier_prompt import VERIFIER_SYSTEM_PROMPT
from config import MODEL_NAME, LOCAL_API_URL

async def verify_sitemap(sitemap):
    user_prompt = f"""
SITEMAP JSON TO VERIFY:
{json.dumps(sitemap, indent=2)}

TASK:
- Review and correct the sitemap
- Apply only structural and IA improvements
- Output the corrected FULL sitemap
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": VERIFIER_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.05,
        "top_p": 0.7,
        "max_tokens": 3500,
        "stop": ["</s>"],
        "stream": False
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(LOCAL_API_URL, json=payload, timeout=60) as resp:
            if resp.status != 200:
                raise RuntimeError(await resp.text())

            data = await resp.json()
            content = data["choices"][0]["message"]["content"].strip()

    try:
        return json.loads(content)
    except Exception:
        raise ValueError(f"Verifier returned invalid JSON:\n{content}")
