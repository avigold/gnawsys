#!/usr/bin/env python3
"""
Generate distractor indices for each sentence in curated_sentences.json.

For each sentence, picks 3 other sentences from the same tag group as
distractors. If fewer than 3 same-tag sentences are available, fills
from randomised other sentences. Stores indices (not full text) so the
frontend can look up the actual text.
"""

import json
import random
from collections import defaultdict

INPUT_PATH = "/Users/avramscore/Projects/gnawsys/curated_sentences.json"

def main():
    # Read sentences
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        sentences = json.load(f)

    total = len(sentences)
    print(f"Loaded {total} sentences.")

    # Group indices by tag
    tag_groups = defaultdict(list)
    for idx, sentence in enumerate(sentences):
        tag_groups[sentence["tag"]].append(idx)

    print(f"Found {len(tag_groups)} unique tags.")

    # Build a list of all indices for fallback sampling
    all_indices = list(range(total))

    # Seed for reproducibility
    random.seed(42)

    for idx, sentence in enumerate(sentences):
        tag = sentence["tag"]
        # Same-tag candidates, excluding the sentence itself
        same_tag = [i for i in tag_groups[tag] if i != idx]

        if len(same_tag) >= 3:
            # Enough same-tag distractors available
            distractors = random.sample(same_tag, 3)
        else:
            # Use all available same-tag, then fill from the rest
            distractors = list(same_tag)
            # Candidates from other tags (exclude self and already-chosen)
            excluded = set(distractors) | {idx}
            remaining = [i for i in all_indices if i not in excluded]
            needed = 3 - len(distractors)
            distractors += random.sample(remaining, needed)

        sentence["distractors"] = distractors

    # Write back
    with open(INPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(sentences, f, ensure_ascii=False, indent=1)

    print(f"Done. Added distractors to all {total} sentences.")

    # Quick sanity check
    problems = 0
    for idx, s in enumerate(sentences):
        ds = s["distractors"]
        if idx in ds:
            problems += 1
            print(f"  ERROR: sentence {idx} appears in its own distractors")
        if len(ds) != len(set(ds)):
            problems += 1
            print(f"  ERROR: sentence {idx} has duplicate distractors")
        if len(ds) != 3:
            problems += 1
            print(f"  ERROR: sentence {idx} has {len(ds)} distractors (expected 3)")

    if problems == 0:
        print("Sanity check passed: no self-references, no duplicates, all have 3 distractors.")
    else:
        print(f"Sanity check found {problems} problem(s).")


if __name__ == "__main__":
    main()
