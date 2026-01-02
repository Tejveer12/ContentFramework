# --- FILE: pipelines/inference_pipeline.py (FINAL UPDATE with Async Excel Call) ---

import asyncio
import json
from typing import Dict, Any, Tuple
from pathlib import Path

# --- Imports ---
from pipelines.shared_pipeline_steps import run_generation
from agents.evaluation.evaluator_agent import evaluate_sitemap
from agents.learning.policy_store import load_or_init_policy, save_policy
from agents.learning.policy_update_agent import update_policy_from_failures

# Assuming json_to_excel is imported from 'utils'
from utils.json_to_excel import json_to_excel


async def run_inference_with_self_correction(
        input_path: Path,
        example_name: str,
        target_score: float = 0.9,
        expected_sitemap: Dict[str, Any] = None,  # Required for evaluation
        enable_self_correction: bool = False  # <--- NEW FLAG for learning control
) -> Tuple[Dict[str, Any], bool]:
    """
    Runs the full generation pipeline using the current policy.
    If an expected sitemap is provided AND self-correction is enabled,
    it evaluates the score and triggers a policy update if the score is below the target.

    Returns: (final_generated_sitemap, policy_was_updated)
    """

    # 1. Load the latest trained policy
    policy = await load_or_init_policy()
    print(f"🧠 Loaded Policy for Client: {example_name}")

    # 2. GENERATE SITEMAP
    print(f"🚀 Starting generation for input path: {input_path.name}")
    generated_sitemap, merged_facts = await run_generation(
        input_path=input_path,
        policy=policy,
        example_name=example_name
    )

    policy_was_updated = False

    # Check if we have the necessary components for evaluation AND learning
    if expected_sitemap:
        print("\n--- EVALUATION AND POTENTIAL SELF-CORRECTION ---")

        # 3. EVALUATE (Against the EXPECTED Output)
        evaluation = await evaluate_sitemap(
            generated_sitemap=generated_sitemap,
            expected_sitemap=expected_sitemap,
            reference_text=merged_facts
        )

        score = evaluation["score"]
        reasons = evaluation["reasons"]

        print(f"📊 Evaluation Score: {score:.3f} / Failure Reasons: {len(reasons)}")

        # 4. CONDITIONAL POLICY UPDATE (Controlled by Flag and Score)
        if enable_self_correction:
            if score < target_score:
                print(f"    - ❌ Score {score:.3f} is below target {target_score}. Triggering policy learning...")
                #

                # The Learning Agent updates the general and/or client-specific rules
                new_policy = await update_policy_from_failures(
                    policy=policy,
                    evaluation_reasons=reasons,
                    generated_sitemap=generated_sitemap,
                    expected_sitemap=expected_sitemap,
                    example_name=example_name
                )

                # 5. Save the updated policy
                if new_policy != policy:
                    await save_policy(new_policy)
                    policy_was_updated = True
                    print("    - ✅ New Policy saved successfully.")
                else:
                    print("    - ⚠️ Policy agent returned original policy (no changes).")
            else:
                print("    - ✅ Score met target. No policy update needed.")
        else:
            print(f"    - ℹ️ Self-correction disabled (enable_self_correction=False). Policy update skipped.")

    elif expected_sitemap is None and enable_self_correction:
        print("⚠️ Warning: Cannot run self-correction. 'expected_sitemap' is missing.")

    print("\n--- INFERENCE COMPLETE ---")
    return generated_sitemap, policy_was_updated


# Example execution function (for testing/demonstration)
async def main_inference_run(client_input_dir: str, client_expected_output_path: str, enable_learning: bool = True):
    """
    Simulates a full inference run for a specific client and converts the final JSON output to Excel.
    """
    input_path = Path(client_input_dir)
    example_name = "Example-3-CERTIFIED IT PROS"

    # 1. Ensure the output directory exists
    output_dir = Path("data/output") / example_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Define the final output file path
    excel_output_path = output_dir / f"{example_name}_sitemap_output.xlsx"

    # Load gold standard for evaluation (optional, but needed for self-correction)
    try:
        with open(client_expected_output_path, 'r') as f:
            expected_sitemap = json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Warning: Expected sitemap not found at {client_expected_output_path}. Running blind inference.")
        expected_sitemap = None

    final_sitemap, was_updated = await run_inference_with_self_correction(
        input_path=input_path,
        example_name=example_name,
        expected_sitemap=expected_sitemap,
        enable_self_correction=enable_learning
    )

    print("\nFinal Generated Sitemap (Structure Only):")
    print(json.dumps(
        final_sitemap,
        indent=2))
    print(f"\nPolicy Updated: {was_updated}")

    # --- JSON to Excel Conversion (using asyncio.to_thread for synchronous I/O) ---
    print(f"\n📈 Converting JSON to Excel: {excel_output_path}")
    try:
        await asyncio.to_thread(json_to_excel, final_sitemap, str(excel_output_path))
    except Exception as e:
        print(f"❌ Error during Excel conversion: {e}")


# To run this:
if __name__ == "__main__":
    # Ensure you have 'openpyxl' installed: pip install openpyxl

    # Example 1: Run inference without learning (set enable_learning=False)
    # NOTE: Paths must exist in your file system
    asyncio.run(main_inference_run(
        client_input_dir="data/training/Example-3-CERTIFIED IT PROS/input",
        client_expected_output_path="data/training/Example-3-CERTIFIED IT PROS/output/AI Copy Certified IT Pros_ Content Framework.json",
        enable_learning=False
    ))