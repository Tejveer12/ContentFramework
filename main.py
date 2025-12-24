import asyncio
import json
from pipeline import  run_pipeline

# ----------------------------------
# Entry point
# ----------------------------------
if __name__ == "__main__":
    final_sitemap = asyncio.run(
        run_pipeline("data/Share_content_data/Example-3-CERTIFIED IT PROS/input")
    )

    print("\n🏁 FINAL SITEMAP:\n")
    print(json.dumps(final_sitemap, indent=2))

    from utils.json_to_excel import json_to_excel

    json_to_excel(
        sitemap_json=final_sitemap,
        output_path="Certified_it.xlsx"
    )

    print("\n📤 Excel exported successfully ✅")
