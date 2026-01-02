# --- FILE: pipelines/shared_pipeline_steps.py (UPDATED for Client Policy Merge) ---

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

# --- Reused Imports (Must be updated to accept policy) ---
from agents.extractor.extractor_agent import extract_from_chunk
from agents.sitemap.sitemap_agent import generate_sitemap
from agents.sitemap.verifier_agent import verify_sitemap

# --- Reused Utility Imports ---
from utils.file_loader import read_file_text

CALL_FILE_KEYWORDS = ["call", "meeting", "discussion", "sync"]


def is_call_file(file_name: str) -> bool:
    """Checks if a file is a transcription or meeting notes."""
    name = file_name.lower()
    return any(k in name for k in CALL_FILE_KEYWORDS)


async def run_generation(
        input_path: Path,
        policy: Dict[str, Any],  # Policy is now Dict[str, Any] due to nested structure
        example_name: str  # <--- CRITICAL NEW INPUT for client-specific policy
) -> Tuple[Dict[str, Any], str]:
    """
    Runs the full generation pipeline (Extract -> Build -> Verify)
    using the provided policy and client context.

    Returns: (generated_sitemap, merged_facts)
    """

    # ----------------------------------
    # Step 1: Prepare Input Files
    # ----------------------------------
    call_files = []
    reference_files = []

    # Separate input files based on keyword detection
    for file in input_path.glob("*"):
        if is_call_file(file.name):
            call_files.append(file)
        else:
            reference_files.append(file)

    if not call_files:
        raise RuntimeError(f"❌ No call-related files found in {input_path}")

    print(f"    - Processing {len(call_files)} call files and {len(reference_files)} reference files.")

    # ----------------------------------
    # Step 2: Extract facts using Policy
    # ----------------------------------
    extracted_notes = []

    # Extract facts concurrently from all call files
    extraction_tasks = []

    # NOTE: The Extractor Agent requires the MERGED policy (General + Client-Specific).
    # This merge logic should be extracted into a utility or performed here before extraction.
    # We will assume a merge utility function exists or the full policy is passed and the extractor handles it.

    for file in call_files:
        raw_text = read_file_text(file)
        if raw_text.strip():
            # PASS THE FULL POLICY TO THE EXTRACTOR AGENT
            task = extract_from_chunk(raw_text, policy=policy, example_name=example_name)
            extraction_tasks.append(task)

    # Use asyncio.gather for parallel extraction
    facts_from_calls = await asyncio.gather(*extraction_tasks)

    for facts in facts_from_calls:
        if facts and facts != "No sitemap-relevant information found.":
            extracted_notes.append(facts)

    # Add reference files (e.g., SOWs, Handover docs) raw text directly
    for file in reference_files:
        raw_text = read_file_text(file)
        if raw_text.strip():
            extracted_notes.append(raw_text)

    if not extracted_notes:
        raise RuntimeError("❌ No sitemap-relevant facts extracted.")

    merged_facts = "\n".join(extracted_notes)

    # PASS THE POLICY AND EXAMPLE_NAME TO THE SITEMAP AGENT (CRITICAL)
    sitemap_json = await generate_sitemap(
        new_input=merged_facts,
        policy=policy,
        client_name=example_name  # <--- CRITICAL: Passes client name for merge logic
    )

    # # Parse the resulting sitemap
    # try:
    #     sitemap = json.loads(sitemap_json_str)
    # except json.JSONDecodeError as e:
    #     # This error should be rare due to Pydantic guidance in update_sitemap
    #     raise ValueError(f"Sitemap agent returned invalid JSON: {e}")

    # ----------------------------------
    # Step 4: Verify structure
    # ----------------------------------
    # The Verifier Agent needs the reference facts to check for hallucination.
    sitemap = await verify_sitemap(sitemap_json)

    # Parse the resulting sitemap
    # try:
    #     sitemap = json.loads(sitemap)
    # except json.JSONDecodeError as e:
    #     # This error should be rare due to Pydantic guidance in update_sitemap
    #     raise ValueError(f"Sitemap agent returned invalid JSON: {e}")
    #
    print("    - ✅ Generation cycle complete.")

    # NOTE: run_generation is expected to return the DICTIONARY and the facts.
    return sitemap, merged_facts