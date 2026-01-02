# --- FILE: utils/dataset_loader.py (NEW) ---

import json
from pathlib import Path
from typing import List, Dict, Any

# Define the structure for a single training example
class TrainingExample:
    def __init__(self, name: str, input_path: Path, expected_sitemap: Dict[str, Any]):
        self.name = name
        self.input_path = input_path
        self.expected_sitemap = expected_sitemap

def load_training_dataset(base_path: str = "data/training") -> List[TrainingExample]:
    """
    Loads all training examples from the filesystem.
    """
    base_dir = Path(base_path)
    examples: List[TrainingExample] = []

    # Find all example folders (e.g., Example-1-BICKFORD USA)
    for example_dir in base_dir.iterdir():
        if example_dir.is_dir():
            # 1. Define input folder path
            input_folder = example_dir / "input"
            
            # 2. Find the expected output file (the 'golden' sitemap)
            # Assuming the golden file is the first JSON file in the 'output' folder
            output_folder = example_dir / "output"
            json_files = list(output_folder.glob("*.json"))
            
            if not json_files:
                print(f"⚠️ Warning: No expected JSON sitemap found for {example_dir.name}. Skipping.")
                continue

            # Load the expected sitemap (the ground truth)
            expected_sitemap_path = json_files[0]
            try:
                with open(expected_sitemap_path, 'r', encoding='utf-8') as f:
                    # Note: We use simple 'read' here for simplicity,
                    # but in a production setup, error handling is crucial
                    expected_sitemap = json.load(f)
            except json.JSONDecodeError:
                print(f"❌ Error decoding JSON for {example_dir.name}. Skipping.")
                continue

            examples.append(
                TrainingExample(
                    name=example_dir.name,
                    input_path=input_folder,
                    expected_sitemap=expected_sitemap
                )
            )

    return examples
