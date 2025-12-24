import json
from pathlib import Path

from agents.extractor_agent import extract_from_chunk
from agents.progressive_sitemap_agent import update_sitemap
from agents.verifier_agent import verify_sitemap
from agents.evaluator_agent import evaluate_sitemap
from agents.updation_agent import update_sitemap_from_evaluation

from utils.file_loader import read_file_text


CALL_FILE_KEYWORDS = ["call", "meeting", "discussion", "sync"]


def is_call_file(file_name: str) -> bool:
    name = file_name.lower()
    return any(k in name for k in CALL_FILE_KEYWORDS)


async def run_pipeline(input_folder: str):
    input_path = Path(input_folder)

    call_files = []
    reference_files = []

    # ----------------------------------
    # Step 1: Separate call files
    # ----------------------------------
    for file in input_path.glob("*"):
        if is_call_file(file.name):
            call_files.append(file)
        else:
            reference_files.append(file)

    if not call_files:
        raise RuntimeError("❌ No call-related files found.")

    print(f"\n📞 Call files detected: {[f.name for f in call_files]}")

    # ----------------------------------
    # Step 2: Extract facts ONLY from call files
    # ----------------------------------
    extracted_notes = []

    for file in call_files:
        raw_text = read_file_text(file)

        if not raw_text.strip():
            continue

        facts = await extract_from_chunk(raw_text)

        if facts and facts != "No sitemap-relevant information found.":
            extracted_notes.append(facts)

        print(f"✓ Extracted from {file.name}")

    for file in reference_files:
        raw_text = read_file_text(file)

        if not raw_text.strip():
            continue

        extracted_notes.append(raw_text)

    if not extracted_notes:
        raise RuntimeError("❌ No sitemap-relevant facts extracted from call files.")

    merged_facts = "\n".join(extracted_notes)

    print("\n📌 MERGED EXTRACTED FACTS:\n")
    print(merged_facts)

    # ----------------------------------
    # Step 3: Build sitemap from extracted facts
    # ----------------------------------
    sitemap = {
        "site": "Unknown",
        "pages": []
    }

    sitemap = await update_sitemap(sitemap, merged_facts)
    print("\n🧩 Initial Sitemap:\n", json.dumps(sitemap, indent=2))
    breakpoint()

    # ----------------------------------
    # Step 4: Verify structure
    # ----------------------------------
    sitemap = await verify_sitemap(sitemap)
    print("\n✅ Verified Sitemap:\n", json.dumps(sitemap, indent=2))

    # ----------------------------------
    # Step 5: Evaluate (using extracted facts only)
    # ----------------------------------
    evaluation = await evaluate_sitemap(sitemap, merged_facts)

    score = evaluation["score"]
    reasons = evaluation["reasons"]

    print(f"\n📊 CONTENT QUALITY SCORE: {score:.2f}")
    breakpoint()

    # ----------------------------------
    # Step 6: Improve sitemap using updation agent
    # ----------------------------------
    if score < 0.8 and reasons:
        print("\n🛠️ Improving sitemap based on evaluation feedback...")

        sitemap = await update_sitemap_from_evaluation(
            sitemap=sitemap,
            reasons=reasons,
            reference_text=merged_facts
        )

        print("\n✨ Sitemap improved successfully.")
        print(json.dumps(sitemap, indent=2))

        # ----------------------------------
        # Step 7: Re-evaluate after update
        # ----------------------------------
        evaluation = await evaluate_sitemap(sitemap, merged_facts)
        print(f"\n🔁 POST-UPDATE SCORE: {evaluation['score']:.2f}")

        reasons = evaluation["reasons"]

        if reasons:
            print("\n⚠️ Evaluation Issues:")
            for i, r in enumerate(reasons, 1):
                print(f"{i}. {r}")
        else:
            print("\n✅ Sitemap quality is excellent.")

    else:
        print("\n🎯 Sitemap accepted without automatic updates.")

    # ----------------------------------
    # Step 6: User-driven updates loop
    # ----------------------------------
    while True:
        user_feedback = input(
            "\nEnter changes (or type 'no change' / 'exit' / 'done'): "
        ).strip()

        if not user_feedback:
            continue

        if user_feedback.lower() in {"no change", "exit", "done"}:
            print("✅ Finalizing sitemap.")
            break

        sitemap = await update_sitemap_from_evaluation(sitemap, user_feedback)
        print("🔄 Sitemap updated.")

    return sitemap
