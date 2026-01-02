# --- FILE: agents/extractor/extractor_agent.py (FINAL MODIFIED) ---

import aiohttp
import json
from typing import Dict, List, Any  # Added typing imports for clarity

from agents.extractor.extractor_prompt import EXTRACTOR_SYSTEM_PROMPT
from config import MODEL_NAME, LOCAL_API_URL


# --- Policy Merge Helper Function ---
# This merge logic is essential to select the correct extraction rules.
def merge_policy_for_extraction(policy: Dict[str, Any], example_name: str) -> List[str]:
    """
    Combines general extraction rules and client-specific extraction rules.
    Returns a single list of strings.
    """

    # 1. Start with General Extraction Rules
    general_rules = policy.get('general_rules', {}).get('extraction_rules', [])
    merged_rules = set(general_rules)

    # 2. Add Client-Specific Extraction Rules
    client_rules_dict = policy.get('client_specific_rules', {})
    if example_name in client_rules_dict:
        client_extraction_rules = client_rules_dict[example_name].get('extraction_rules', [])
        merged_rules.update(client_extraction_rules)

    return list(merged_rules)


# MODIFIED: Added 'example_name' argument
async def extract_from_chunk(input_chunk: str, policy: dict, example_name: str) -> str:
    """
    Extracts relevant facts from a text chunk, guided by the merged General and
    Client-Specific Extraction Rules.
    """

    # 1. MERGE THE EXTRACTION POLICY
    extraction_rules = merge_policy_for_extraction(policy, example_name)

    # 2. Format Rules for Prompt
    rules_str = "\n- ".join(extraction_rules) if extraction_rules else "No specific learned rules apply."

    # 3. Create a user prompt that includes the merged rules
    user_prompt = f"""
LEARNED EXTRACTION RULES TO FOLLOW (CRITICAL):
- {rules_str}
---
INPUT CHUNK TO PROCESS:
{input_chunk}
"""


    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": EXTRACTOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}  # MODIFIED: Using the new user_prompt
        ],
        # ... (rest of payload remains the same)
        "temperature": 0.0,
        "top_p": 0.9,
        "max_tokens": 1500,
        "stop": ["</s>"],
        "stream": False
    }
    # ... (rest of async call remains the same)
    async with aiohttp.ClientSession() as session:
        async with session.post(
                LOCAL_API_URL,
                json=payload,
                timeout=60
        ) as response:
            # ... (error handling and return logic)
            if response.status != 200:
                raise RuntimeError(await response.text())

            data = await response.json()
            content = data["choices"][0]["message"]["content"].strip()

    return content  # Returns the list of notes as a string