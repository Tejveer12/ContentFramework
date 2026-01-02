# --- FILE: train.py (NEW) ---

import asyncio
import os
from pathlib import Path
from pipelines.training_pipeline import train
from utils.dataset_loader import load_training_dataset
from config import TARGET_ACCURACY  # We assume this is set in your config.py

# --- Configuration ---
TRAINING_DATA_PATH = "data/training"


def ensure_learned_state_directory():
    """Ensures the directory for storing policy and metrics exists."""
    Path("learned_state").mkdir(exist_ok=True)


async def main():
    """
    Main function to load the dataset and start the training process.
    """
    ensure_learned_state_directory()

    # Load all 5 example sets (input + golden output)
    training_examples = load_training_dataset(TRAINING_DATA_PATH)

    if not training_examples:
        print(f"FATAL: No training examples found in {TRAINING_DATA_PATH}. Check your data structure.")
        return

    print(f"📚 Successfully loaded {len(training_examples)} training examples.")

    # Start the iterative training loop
    final_policy = await train(
        training_examples=training_examples,
        target_score=TARGET_ACCURACY
    )

    print("\n=============================================")
    print("✅ TRAINING COMPLETE.")
    print(f"Final Policy saved to learned_state/learned_policy.json")
    print(f"Metrics saved to learned_state/training_metrics.json")
    print("=============================================")

    # Display a snippet of the learned policy
    print("\n🧠 LEARNED POLICY SNIPPET:")
    print(f"Extraction Rules Learned: {len(final_policy.get('extraction_rules', []))}")
    print(f"Structure Rules Learned: {len(final_policy.get('structure_rules', []))}")


if __name__ == "__main__":
    # Ensure correct PATH is used if running from a script
    # This might be needed if you are running this from a different directory
    # os.chdir(Path(__file__).parent)

    try:
        asyncio.run(main())
    except RuntimeError as e:
        print(f"\n❌ A runtime error occurred during the pipeline execution: {e}")
        print("Please check the API service status and the agent logs.")