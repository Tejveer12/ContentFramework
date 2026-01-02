import aiohttp
import json
from updation_prompt import UPDATION_SYSTEM_PROMPT, USER_UPDATION_SYSTEM_PROMPT
from config import MODEL_NAME, LOCAL_API_URL


async def update_sitemap_from_evaluation(
    sitemap: dict,
    reasons: list[str],
    reference_text: str
) -> dict:

    user_prompt = f"""
REFERENCE INPUT CONTENT:
{reference_text}

EVALUATION ISSUES TO FIX:
{json.dumps(reasons, indent=2)}

CURRENT SITEMAP:
{json.dumps(sitemap, indent=2)}

TASK:
- Fix the sitemap based on the evaluation issues
- Improve relevance and completeness
- Ensure strong alignment with reference content
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": UPDATION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.15,
        "top_p": 0.85,
        "max_tokens": 3500,
        "stop": ["</s>", "```"],
        "stream": False
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            LOCAL_API_URL,
            json=payload,
            timeout=60
        ) as resp:

            if resp.status != 200:
                raise RuntimeError(await resp.text())

            data = await resp.json()
            content = data["choices"][0]["message"]["content"].strip()

    try:
        updated = json.loads(content)
    except Exception:
        raise ValueError(f"Updation agent returned invalid JSON:\n{content}")

    return updated

async def update_sitemap_from_user(
    sitemap: dict,
    user_feedback: str
) -> dict:

    user_prompt = f"""
USER FEEDBACK:
{user_feedback}

CURRENT SITEMAP:
{json.dumps(sitemap, indent=2)}

TASK:
- Apply the user-requested changes to the sitemap
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": USER_UPDATION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "top_p": 0.85,
        "max_tokens": 3000,
        "stop": ["</s>"],
        "stream": False
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            LOCAL_API_URL,
            json=payload,
            timeout=60
        ) as resp:

            if resp.status != 200:
                raise RuntimeError(await resp.text())

            data = await resp.json()
            content = data["choices"][0]["message"]["content"].strip()

    try:
        updated = json.loads(content)
    except Exception:
        raise ValueError(f"User updation agent returned invalid JSON:\n{content}")

    return updated