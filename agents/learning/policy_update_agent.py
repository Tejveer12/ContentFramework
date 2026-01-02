# # --- FILE: agents/learning/policy_update_agent.py (CRITICALLY MODIFIED) ---
#
# import aiohttp
# import json
# from typing import Dict, List, Any
#
# # --- Imports ---
# from config import MODEL_NAME, LOCAL_API_URL
# # Assuming policy_prompt.py and policy_store.py have been updated as planned
# from agents.learning.policy_prompt import POLICY_UPDATE_SYSTEM_PROMPT
# from agents.learning.policy_store import DEFAULT_POLICY
#
#
# def merge_rule_lists(existing_list: List[str], new_list: List[str]) -> List[str]:
#     """Merges two lists, ensuring no duplicates (using sets)."""
#     if not isinstance(existing_list, list) or not isinstance(new_list, list):
#         # Handle cases where the lists might be None or incorrectly formatted
#         return list(set(existing_list or []) | set(new_list or []))
#
#     merged = set(existing_list)
#     merged.update(new_list)
#     return list(merged)
#
#
# def merge_policy_updates(
#         policy: Dict[str, Any],
#         update: Dict[str, Any],
#         example_name: str
# ) -> Dict[str, Any]:
#     """Applies the partial update JSON from the LLM to the full policy structure."""
#
#     # Use a deep copy to ensure immutability is maintained
#     # Note: JSON round-trip is used here for a safe deep copy, assuming policy is JSON-serializable.
#     new_policy = json.loads(json.dumps(policy))
#
#     # --- 1. Merge General Rules ---
#     general_update = update.get("general_rules_update", {})
#     if general_update:
#         for rule_type, new_rules in general_update.items():
#             if rule_type in new_policy["general_rules"]:
#                 new_policy["general_rules"][rule_type] = merge_rule_lists(
#                     new_policy["general_rules"][rule_type], new_rules
#                 )
#
#     # --- 2. Merge Client-Specific Rules ---
#     client_update = update.get("client_rules_update", {})
#     if client_update:
#         # Ensure the client's entry exists in the master policy
#         if example_name not in new_policy["client_specific_rules"]:
#             # Initialize the client's rule structure if it's new
#             new_policy["client_specific_rules"][example_name] = {
#                 "extraction_rules": [],
#                 "structure_rules": [],
#                 "content_rules": []
#             }
#
#         # Merge the specific rules for this client
#         client_target = new_policy["client_specific_rules"][example_name]
#         for rule_type, new_rules in client_update.items():
#             if rule_type in client_target:
#                 client_target[rule_type] = merge_rule_lists(
#                     client_target[rule_type], new_rules
#                 )
#
#     return new_policy
#
#
# async def update_policy_from_failures(
#         policy: Dict[str, List[str]],
#         evaluation_reasons: List[str],
#         generated_sitemap: Dict[str, Any],
#         expected_sitemap: Dict[str, Any],
#         example_name: str  # <--- CRITICAL NEW INPUT
# ) -> Dict[str, List[str]]:
#     """
#     Analyzes evaluation failures and current sitemaps to induce a new,
#     improved set of policy rules, partitioning them by client.
#     """
#
#     # --- Prompt Construction ---
#     current_general_rules_str = json.dumps(policy.get("general_rules", {}), indent=2)
#     reasons_str = "\n- ".join(evaluation_reasons)
#
#     user_prompt = f"""
# CURRENT GENERAL POLICY (RULES TO BE REFINED):
# {current_general_rules_str}
#
# CLIENT CONTEXT: The current example being analyzed is **{example_name}**.
#
# EVALUATION FAILURES (The system must learn to fix these):
# - {reasons_str}
#
# GENERATED SITEMAP (The wrong output):
# {json.dumps(generated_sitemap, indent=2)}
#
# EXPECTED SITEMAP (The correct output - the gold standard):
# {json.dumps(expected_sitemap, indent=2)}
# """
#
#     payload = {
#         "model": MODEL_NAME,
#         "messages": [
#             {"role": "system", "content": POLICY_UPDATE_SYSTEM_PROMPT},
#             {"role": "user", "content": user_prompt}
#         ],
#         "temperature": 0.1,  # Keep low for deterministic rule induction
#         "top_p": 0.8,
#         "max_tokens": 1500,
#         "stop": ["</s>", "```"],
#         "stream": False
#     }
#
#     # --- LLM Call to Induce Policy (Returns Partial JSON Update) ---
#     async with aiohttp.ClientSession() as session:
#         async with session.post(LOCAL_API_URL, json=payload, timeout=90) as resp:
#             if resp.status != 200:
#                 raise RuntimeError(f"Policy Agent API Error: {await resp.text()}")
#
#             data = await resp.json()
#             content = data["choices"][0]["message"]["content"].strip()
#
#     try:
#         # LLM returns partial policy update (e.g., {"client_rules_update": {...}})
#         partial_update = json.loads(content)
#
#         # --- MERGE STEP (CRITICAL) ---
#         new_policy = merge_policy_updates(policy, partial_update, example_name)
#
#         print(f"✨ Policy successfully updated (General and/or Client: {example_name}).")
#         return new_policy
#
#     except Exception as e:
#         print(f"Policy Agent returned invalid JSON or error during merge: {e}. Raw content was:\n{content[:500]}...")
#         # Return the original policy to prevent regression
#         return policy


# --- FILE: agents/learning/policy_update_agent.py (SIMPLIFIED REPLACEMENT LOGIC) ---

import aiohttp
import json
from typing import Dict, List, Any

# --- Imports ---
from config import MODEL_NAME, LOCAL_API_URL
from agents.learning.policy_prompt import POLICY_UPDATE_SYSTEM_PROMPT
from agents.learning.policy_store import DEFAULT_POLICY


# The merge_rule_lists and merge_policy_updates helpers are REMOVED entirely,
# as the LLM now handles the merge.


async def update_policy_from_failures(
        policy: Dict[str, Any],  # Changed type hint to Any for robustness
        evaluation_reasons: List[str],
        generated_sitemap: Dict[str, Any],
        expected_sitemap: Dict[str, Any],
        example_name: str
) -> Dict[str, Any]:
    """
    Analyzes evaluation failures, gives the LLM context (current policies),
    and accepts the full, merged updated policy structure from the LLM.
    """

    # --- 1. Extract Current Policy Context for the LLM ---

    # Current General Rules (pass entire object)
    current_general_rules = policy.get("general_rules", {})
    current_general_rules_str = json.dumps(current_general_rules, indent=2)

    # Current Client-Specific Rules (pass ONLY the current client's object)
    current_client_rules = policy.get("client_specific_rules", {}).get(
        example_name,
        {"extraction_rules": [], "structure_rules": [], "content_rules": []}  # Initialize if client is new
    )
    current_client_rules_str = json.dumps(current_client_rules, indent=2)

    reasons_str = "\n- ".join(evaluation_reasons)

    # --- 2. Prompt Construction (Provide all context for LLM to merge) ---
    user_prompt = f"""
CURRENT GENERAL POLICY (RULES TO BE REFINED):
{current_general_rules_str}

CURRENT CLIENT ({example_name}) SPECIFIC POLICY (RULES TO BE REFINED):
{current_client_rules_str}

EVALUATION FAILURES (The system must learn to fix these):
- {reasons_str}

GENERATED SITEMAP (The wrong output):
{json.dumps(generated_sitemap, indent=2)}

EXPECTED SITEMAP (The correct output - the gold standard):
{json.dumps(expected_sitemap, indent=2)}
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": POLICY_UPDATE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "top_p": 0.8,
        "max_tokens": 3000,  # Increased max tokens since the LLM returns the *full* policy
        "stop": ["</s>", "```"],
        "stream": False
    }

    # --- 3. LLM Call to Induce Policy (Returns FULL Updated JSON) ---
    async with aiohttp.ClientSession() as session:
        async with session.post(LOCAL_API_URL, json=payload, timeout=90) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Policy Agent API Error: {await resp.text()}")

            data = await resp.json()
            content = data["choices"][0]["message"]["content"].strip()

    try:
        # LLM returns the ENTIRE updated policy structure
        full_updated_policy_parts = json.loads(content)

        # --- 4. REPLACEMENT LOGIC (CRITICAL) ---
        new_policy = json.loads(json.dumps(policy))  # Deep copy original

        # a) Replace General Rules
        new_policy["general_rules"] = full_updated_policy_parts["general_rules"]

        # b) Replace Client-Specific Rules for the current example
        if "client_specific_rules" not in new_policy:
            new_policy["client_specific_rules"] = {}

        new_policy["client_specific_rules"][example_name] = full_updated_policy_parts["client_specific_rules"]

        print(f"✨ Policy successfully updated by LLM (General and/or Client: {example_name}).")

        return new_policy

    except Exception as e:
        print(
            f"Policy Agent returned invalid JSON or error during replacement: {e}. Raw content was:\n{content[:500]}...")
        # Return the original policy to prevent regression
        return policy