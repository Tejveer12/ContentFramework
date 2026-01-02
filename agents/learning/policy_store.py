# --- FILE: agents/learning/policy_store.py (NEW) ---
import json
from pathlib import Path
from typing import Dict, Any, List

# --- Configuration ---
POLICY_FILE = Path("learned_state/learned_policy.json")
METRICS_FILE = Path("learned_state/training_metrics.json")

DEFAULT_POLICY = {
    "general_rules": {
        "extraction_rules": [
            "Focus on navigation, product, and collection mentions.",
            "Ignore introductory pleasantries and general discussions."
        ],
        "structure_rules": [
            "All policies must be placed in the Footer under a 'Policies' main page.",
            "Home page must not contain sub pages."
        ],
        "content_rules": [
            "Do not invent new pages or sections; adhere strictly to extracted facts.",
            "Ensure all collection pages have a title and product grid section."
        ]
    },
    "client_specific_rules": {} # NEW: Empty dictionary to store client-specific policy updates
}


async def load_or_init_policy() -> Dict[str, List[str]]:
    """Loads the policy from file or initializes it to the default."""
    if POLICY_FILE.exists():
        print(f"Loading existing policy from: {POLICY_FILE}")
        try:
            with open(POLICY_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error reading {POLICY_FILE}. Initializing default policy.")
            return DEFAULT_POLICY
    
    print("No existing policy found. Initializing default policy.")
    POLICY_FILE.parent.mkdir(exist_ok=True)
    await save_policy(DEFAULT_POLICY)
    return DEFAULT_POLICY


async def save_policy(policy: Dict[str, List[str]]):
    """Saves the current learned policy to file."""
    try:
        POLICY_FILE.parent.mkdir(exist_ok=True)
        with open(POLICY_FILE, 'w') as f:
            json.dump(policy, f, indent=2)
    except Exception as e:
        print(f"Error saving policy file: {e}")


async def save_metrics(epoch: int, avg_score: float):
    """Saves training metrics, appending the results of the current epoch."""
    METRICS_FILE.parent.mkdir(exist_ok=True)
    
    # Load existing metrics
    metrics = []
    if METRICS_FILE.exists():
        try:
            with open(METRICS_FILE, 'r') as f:
                metrics = json.load(f)
        except json.JSONDecodeError:
            metrics = []
            
    # Append current epoch results
    metrics.append({"epoch": epoch, "avg_score": round(avg_score, 4)})
    
    # Save updated metrics
    try:
        with open(METRICS_FILE, 'w') as f:
            json.dump(metrics, f, indent=2)
    except Exception as e:
        print(f"Error saving metrics file: {e}")
