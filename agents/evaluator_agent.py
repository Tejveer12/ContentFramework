import aiohttp
import json

from config import MODEL_NAME, LOCAL_API_URL
from prompts.evaluator_prompt import EVALUATOR_SYSTEM_PROMPT


async def evaluate_sitemap(sitemap: dict, reference_text: str) -> dict:
    user_prompt = f"""
REFERENCE INPUT DOCUMENTS:
{reference_text}

CURRENT SITEMAP:
{json.dumps(sitemap, indent=2)}

TASK:
- Evaluate sitemap quality against the reference documents
- Identify gaps, missing sections, or unsupported content
- Do NOT modify the sitemap
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": EVALUATOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "top_p": 0.8,
        "max_tokens": 1200,
        "stop": ["</s>", "```"],
        "stream": False
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(LOCAL_API_URL, json=payload, timeout=60) as resp:
            if resp.status != 200:
                raise RuntimeError(await resp.text())

            data = await resp.json()
            content = data["choices"][0]["message"]["content"].strip()

    try:
        result = json.loads(content)
    except Exception:
        raise ValueError(f"Evaluator returned invalid JSON:\n{content}")

    # Hard validation
    if "score" not in result or "reasons" not in result:
        raise ValueError("Evaluator response must contain 'score' and 'reasons'")

    if not isinstance(result["score"], (int, float)):
        raise ValueError("Score must be a number")

    if not (0.0 <= result["score"] <= 1.0):
        raise ValueError("Score must be between 0 and 1")

    if not isinstance(result["reasons"], list):
        raise ValueError("Reasons must be a list")

    return result

