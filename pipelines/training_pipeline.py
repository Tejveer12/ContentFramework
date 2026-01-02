# --- FILE: pipelines/training_pipeline.py (UPDATED) ---

import asyncio
import json
from typing import List, Dict, Any
from pathlib import Path

# --- New Imports ---
from agents.learning.policy_store import load_or_init_policy, save_policy, save_metrics
from agents.learning.policy_update_agent import update_policy_from_failures
from utils.dataset_loader import load_training_dataset, TrainingExample
# --- Reused/Modified Agent Imports ---
from pipelines.shared_pipeline_steps import run_generation
from agents.evaluation.evaluator_agent import evaluate_sitemap


async def train(training_examples: List[TrainingExample], target_score: float = 0.9):
    """
    The example-driven, self-improving training loop.
    """
    policy = await load_or_init_policy()

    # The policy now has a two-tiered structure, print only the general rules for clarity
    general_rules_display = policy.get("general_rules", {})
    print(f"🚀 Starting agent training loop with target score: {target_score}")
    print(f"🧠 Initial Policy (General Rules): {general_rules_display}")

    for epoch in range(1, 11):  # Limiting to 10 epochs for safety/speed
        print(f"\n======== EPOCH {epoch} ========")
        scores = []
        needs_retraining = False

        # 1. Iterate over all training examples
        for example in training_examples:
            print(f"  > Running Example: {example.name}")

            # --- GENERATE (Using the CURRENT Policy) ---
            # run_generation is assumed to return the final sitemap as a JSON string
            generated_sitemap_json, merged_facts = await run_generation(
                input_path=example.input_path,
                policy=policy,
                example_name=example.name  # CRITICAL: Pass client name for policy merging
            )

            print(generated_sitemap_json)

            # CRITICAL FIX: Decode the JSON string into a dictionary
            # try:
            #     generated_sitemap_dict = json.loads(generated_sitemap_json_str)
            # except json.JSONDecodeError as e:
            #     print(f"    - ❌ JSON Decode Error during generation for {example.name}: {e}")
            #     print("    - Skipping evaluation and returning original policy.")
            #     continue  # Skip this iteration if the output is unusable

            # print(generated_sitemap_json_str) # Removed print of entire large JSON string
            print(f"    - Generation cycle complete. Facts: {len(merged_facts.splitlines())} lines.")

            # --- EVALUATE (Against the GOLDEN Output) ---
            evaluation = await evaluate_sitemap(
                generated_sitemap=generated_sitemap_json,  # Pass Dict
                expected_sitemap=example.expected_sitemap,
                reference_text=merged_facts
            )

            # print("REASONS: ", evaluation["reasons"]) # Removed print of reasons for cleaner log
            score = evaluation["score"]
            scores.append(score)

            print(f"    - Score: {score:.2f} / Reasons: {len(evaluation['reasons'])}")

            # --- LEARN AND UPDATE POLICY (Retrain based on input failure) ---
            if score < target_score:
                print(f"    - ❌ Score too low. Learning from failure...")

                # The Learning Agent updates the rules in the policy
                policy = await update_policy_from_failures(
                    policy=policy,
                    evaluation_reasons=evaluation["reasons"],
                    generated_sitemap=generated_sitemap_json,  # Pass Dict
                    expected_sitemap=example.expected_sitemap,
                    example_name=example.name  # CRITICAL: Pass client name for client-specific learning
                )
                needs_retraining = True

        # 2. Check Epoch Results
        avg_score = sum(scores) / len(scores) if scores else 0
        print(f"\n📊 EPOCH {epoch} COMPLETE. Average Score: {avg_score:.3f}")

        # 3. Save State
        await save_policy(policy)
        await save_metrics(epoch, avg_score)

        # 4. Check Stopping Condition
        if avg_score >= target_score:
            print(f"\n🏆 Training successful! Target score of {target_score} achieved.")
            break

        if epoch == 10 and avg_score < target_score:
            print(f"\n⚠️ Max epochs reached. Final score: {avg_score:.3f}")
            break

        if not needs_retraining and avg_score < target_score:
            print(f"\n🛑 No policy updates were made this epoch and target not met. Halting training.")
            break

    return policy