import aiohttp

from prompts.extractor_prompt import EXTRACTOR_SYSTEM_PROMPT
from config import MODEL_NAME, LOCAL_API_URL

async def extract_from_chunk(input_chunk: str) -> dict:
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": EXTRACTOR_SYSTEM_PROMPT},
            {"role": "user", "content": input_chunk}
        ],
        "temperature": 0.0,
        "top_p": 0.9,
        "max_tokens": 1500,
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

