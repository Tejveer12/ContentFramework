# --- FILE: agents/sitemap/progressive_sitemap_agent.py (FINAL SIMPLIFIED PROMPT) ---

import aiohttp
import json
from typing import Dict, List, Any

from config import MODEL_NAME, LOCAL_API_URL
from agents.sitemap.sitemap_system_prompt import SYSTEM_PROMPT


# --- Policy Merge Helper Function ---
# This helper remains essential to create the single, flat list of rules.
def merge_policy_for_generation(policy: Dict[str, Any], client_name: str) -> Dict[str, Any]:
    """
    Combines general rules and client-specific rules into a single flat structure
    containing the final, active rules for the LLM.
    """

    # 1. Start with General Rules
    merged_policy = json.loads(json.dumps(policy.get('general_rules', {})))

    # 2. Check for and Apply Client-Specific Overrides/Additions
    client_rules_dict = policy.get('client_specific_rules', {})

    if client_name in client_rules_dict:
        client_rules = client_rules_dict[client_name]

        # Merge the lists of rules (using sets to handle duplicates)
        for rule_type in ["extraction_rules", "structure_rules", "content_rules"]:
            general_list = merged_policy.get(rule_type, [])
            client_list = client_rules.get(rule_type, [])

            merged_set = set(general_list)
            merged_set.update(client_list)
            merged_policy[rule_type] = list(merged_set)

    return merged_policy


async def generate_sitemap(new_input: str, policy: dict, client_name: str) -> str:
    """
    Generates the entire sitemap in a single shot based on facts, using
    the merged General and Client-Specific policies.
    """

    # 1. MERGE THE POLICY
    merged_policy = merge_policy_for_generation(policy, client_name)

    # 2. Extract MERGED Rules for Injection
    # We now pull the final, combined rule lists directly from merged_policy.
    merged_structure_rules = merged_policy.get("structure_rules", [])
    merged_content_rules = merged_policy.get("content_rules", [])

    structure_str = "\n- ".join(merged_structure_rules) or "No specific structure rules."
    content_str = "\n- ".join(merged_content_rules) or "No specific content rules."

    # 2. Construct the User Prompt with Rules
    user_prompt = f"""
LEARNED STRUCTURAL RULES TO STRICTLY FOLLOW:
- {structure_str}

LEARNED CONTENT RULES TO STRICTLY FOLLOW:
- {content_str}
---

NEW INPUT (Extracted Facts):
{new_input}

TASK:
- Update the existing sitemap using the new input, strictly adhering to the LEARNED RULES.
- Do NOT remove existing pages unless explicitly contradicted
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
        "stop": ["</s>"],
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