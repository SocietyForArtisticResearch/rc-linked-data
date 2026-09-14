"""
Backfill screenshots/index.json for the back-catalogue of exposition screenshot
folders that predate the index.json format (they only have the old toc.json, or
nothing). Combines the real files on disk with page titles from a fresh
enriched.json dump. See readme.md for the target ScreenshotsToc schema.

Usage:
    python3 parsers/backfill_index_json.py <screenshots_root> <enriched_json> [--force]
"""

import argparse
import json
import logging
import os
import re

BASE_SCREENSHOT_RE = re.compile(r"^(\d+)\.png$")

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def load_enriched(enriched_json_path):
    with open(enriched_json_path) as f:
        entries = json.load(f)

    enriched_by_id = {}
    for entry in entries:
        expo_id = entry.get("id")
        if expo_id is None:
            continue

        title_by_page_and_file = {}
        title_by_page = {}
        toc = entry.get("toc") or {}
        for weave in toc.get("weaves") or []:
            page = weave.get("page")
            file_name = weave.get("file")
            page_title = weave.get("page_title")
            if page is None:
                continue
            if file_name is not None:
                title_by_page_and_file[(page, file_name)] = page_title
            title_by_page.setdefault(page, page_title)

        enriched_by_id[expo_id] = {
            "title_by_page_and_file": title_by_page_and_file,
            "title_by_page": title_by_page,
        }

    return enriched_by_id


def resolve_variant(page_dir, page_id, base_name, prefix):
    candidate_name = f"{prefix}{base_name}.jpg"
    if os.path.exists(os.path.join(page_dir, candidate_name)):
        return f"{page_id}/{candidate_name}"
    return f"{page_id}/{base_name}.png"


def build_screenshot_entries(expo_dir, expo_id, expo_enriched):
    title_by_page_and_file = expo_enriched.get("title_by_page_and_file", {}) if expo_enriched else {}
    title_by_page = expo_enriched.get("title_by_page", {}) if expo_enriched else {}

    entries = []
    for page_entry in sorted(os.scandir(expo_dir), key=lambda e: e.name):
        if not page_entry.is_dir() or not page_entry.name.isdigit():
            if page_entry.is_dir():
                logger.warning("Skipping non-integer page folder: %s/%s", expo_id, page_entry.name)
            continue

        page_id = int(page_entry.name)
        page_dir = page_entry.path

        base_files = sorted(
            m.group(1)
            for name in os.listdir(page_dir)
            if (m := BASE_SCREENSHOT_RE.match(name))
        )

        for base_name in base_files:
            file_name = f"{base_name}.png"
            page_title = title_by_page_and_file.get(
                (page_id, file_name), title_by_page.get(page_id)
            )
            entries.append({
                "weave_id": page_id,
                "page_title": page_title,
                "url": f"https://www.researchcatalogue.net/view/{expo_id}/{page_id}",
                "screenshots": {
                    "normal": f"{page_id}/{file_name}",
                    "compressed": resolve_variant(page_dir, page_id, base_name, "compressed_"),
                    "resized": resolve_variant(page_dir, page_id, base_name, "resized_"),
                },
            })

    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("screenshots_root", help="Root folder containing <expo-id>/<page-id>/ screenshot folders")
    parser.add_argument("enriched_json", help="Path to a fresh enriched.json dump")
    parser.add_argument("--force", action="store_true", help="Overwrite existing index.json files")
    args = parser.parse_args()

    logger.info("Loading enriched.json from %s", args.enriched_json)
    enriched_by_id = load_enriched(args.enriched_json)
    logger.info("Loaded %d enriched exposition entries", len(enriched_by_id))

    written = 0
    skipped_existing = 0
    skipped_empty = 0

    for expo_entry in sorted(os.scandir(args.screenshots_root), key=lambda e: e.name):
        if not expo_entry.is_dir() or not expo_entry.name.isdigit():
            continue

        expo_id = int(expo_entry.name)
        index_path = os.path.join(expo_entry.path, "index.json")

        if os.path.exists(index_path) and not args.force:
            skipped_existing += 1
            continue

        entries = build_screenshot_entries(expo_entry.path, expo_id, enriched_by_id.get(expo_id))
        if not entries:
            skipped_empty += 1
            continue

        index_dict = {
            "id": expo_id,
            "default_page_type": None,
            "screenshots": entries,
        }
        with open(index_path, "w") as index_file:
            json.dump(index_dict, index_file, indent=2)
        written += 1

    logger.info(
        "Done. Wrote %d index.json files, skipped %d with existing index.json, skipped %d with no screenshots.",
        written, skipped_existing, skipped_empty,
    )


if __name__ == "__main__":
    main()
