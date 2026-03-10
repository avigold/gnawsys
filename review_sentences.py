#!/usr/bin/env python3
"""Generate and review 10,000 Hebrew sentences using Claude API.

Generates sentences with generator.py, sends batches to Claude for
review, keeps only those that pass all checks, and saves the curated
pool to curated_sentences.json.

Checkpoints progress every 10 batches so the job can be resumed.
"""

import asyncio
import functools
import json
import os
import re
import sys
import time

# Unbuffered print
print = functools.partial(print, flush=True)

import anthropic
from generator import generate

# ── Config ──────────────────────────────────────────────────────────
TARGET = 10_000
BATCH_SIZE = 50          # sentences per API call
CONCURRENCY = 1          # sequential to respect rate limits
DELAY = 8.0              # seconds between batches (30K tok/min ≈ 3.5K per 7s)
MODEL = "claude-sonnet-4-20250514"
CHECKPOINT_FILE = "curated_sentences_checkpoint.json"
OUTPUT_FILE = "curated_sentences.json"

SYSTEM_PROMPT = """\
You are an expert Hebrew language reviewer for a language-learning app. \
You will receive batches of Hebrew learning sentences. Each has four fields: \
hebrew (Hebrew text), transliteration (romanised pronunciation), english \
(English translation), and tag (grammar category).

For each sentence, evaluate:
1. SEMANTIC – Does the sentence make sense? Would a Hebrew speaker say this?
2. GRAMMAR – Is the Hebrew grammatically correct (conjugation, gender/number \
agreement, prepositions, correct use of את)?
3. TRANSLITERATION – Does the transliteration accurately represent the Hebrew?
4. TRANSLATION – Does the English accurately convey the Hebrew meaning?

Respond with a JSON array. Each element:
- "id": the sentence index (0-based)
- "pass": true if ALL four criteria are met, false otherwise
- "reason": if false, a brief explanation. Omit if true.

Output ONLY the JSON array, no other text."""


# ── Helpers ─────────────────────────────────────────────────────────

def load_checkpoint():
    """Load previously saved good sentences and seen set."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        seen = {s["hebrew"] for s in data}
        print(f"Resumed from checkpoint: {len(data)} sentences")
        return data, seen
    return [], set()


def save_checkpoint(good):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(good, f, ensure_ascii=False, indent=1)


def generate_unique(n, seen):
    """Generate n unique sentences not in seen set."""
    batch = []
    attempts = 0
    while len(batch) < n and attempts < n * 5:
        s = generate()
        attempts += 1
        if s and s["hebrew"] not in seen:
            seen.add(s["hebrew"])
            batch.append(s)
    return batch


def parse_response(text, batch):
    """Parse Claude's JSON response and return list of passing sentences."""
    # Strip markdown fences if present
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    results = json.loads(text)
    passing_ids = {r["id"] for r in results if r.get("pass") is True}
    failed = [r for r in results if not r.get("pass")]

    return [batch[i] for i in passing_ids if i < len(batch)], failed


# ── Main loop ───────────────────────────────────────────────────────

async def review_batch(client, batch, sem):
    """Send one batch to Claude for review. Returns (passing, failed)."""
    payload = [
        {"id": i, "hebrew": s["hebrew"], "transliteration": s["transliteration"],
         "english": s["english"], "tag": s["tag"]}
        for i, s in enumerate(batch)
    ]
    async with sem:
        try:
            resp = await client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
            )
            text = resp.content[0].text
            return parse_response(text, batch)
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"  Parse error: {e}")
            return [], []
        except anthropic.APIError as e:
            print(f"  API error: {e}")
            return [], []


async def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY environment variable.")
        sys.exit(1)

    client = anthropic.AsyncAnthropic(api_key=api_key, max_retries=5)
    good, seen = load_checkpoint()
    total_reviewed = 0
    total_passed = 0
    start = time.time()

    print(f"Target: {TARGET} sentences | Model: {MODEL}")
    print(f"Batch size: {BATCH_SIZE} | Concurrency: {CONCURRENCY}")
    print()

    batch_count = 0

    while len(good) < TARGET:
        # Generate enough to fill CONCURRENCY batches, plus buffer for dedup
        needed = TARGET - len(good)
        gen_count = min(needed + 200, CONCURRENCY * BATCH_SIZE + 100)
        raw = generate_unique(gen_count, seen)

        if not raw:
            print("WARNING: generator unable to produce unique sentences. Stopping.")
            break

        # Split into sub-batches
        sub_batches = [raw[i:i + BATCH_SIZE] for i in range(0, len(raw), BATCH_SIZE)]

        # Review concurrently
        sem = asyncio.Semaphore(CONCURRENCY)
        tasks = [review_batch(client, sb, sem) for sb in sub_batches]
        results = await asyncio.gather(*tasks)

        round_passed = 0
        round_reviewed = 0
        round_failures = []
        for passing, failed in results:
            round_reviewed += BATCH_SIZE
            round_passed += len(passing)
            good.extend(passing)
            round_failures.extend(failed)

        total_reviewed += round_reviewed
        total_passed += round_passed
        batch_count += len(sub_batches)

        elapsed = time.time() - start
        rate = len(good) / elapsed if elapsed > 0 else 0
        eta = (TARGET - len(good)) / rate if rate > 0 else 0
        pass_rate = total_passed / total_reviewed * 100 if total_reviewed else 0

        print(f"  {len(good):,}/{TARGET:,} good | "
              f"pass rate: {pass_rate:.0f}% | "
              f"ETA: {eta / 60:.1f}m | "
              f"elapsed: {elapsed / 60:.1f}m")

        # Show a few failure reasons for insight
        if round_failures:
            for f in round_failures[:3]:
                print(f"    ✗ [{f.get('id')}] {f.get('reason', '?')}")

        # Checkpoint every 10 batches
        if batch_count % 10 == 0:
            save_checkpoint(good)

        # Pace requests to stay within rate limits
        await asyncio.sleep(DELAY)

        # Trim to target
        if len(good) >= TARGET:
            good = good[:TARGET]
            break

    save_checkpoint(good)

    # Write final output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(good[:TARGET], f, ensure_ascii=False, indent=1)

    elapsed = time.time() - start
    pass_rate = total_passed / total_reviewed * 100 if total_reviewed else 0
    print()
    print(f"Done. {len(good[:TARGET]):,} curated sentences saved to {OUTPUT_FILE}")
    print(f"Total reviewed: {total_reviewed:,} | Pass rate: {pass_rate:.0f}%")
    print(f"Time: {elapsed / 60:.1f} minutes")


if __name__ == "__main__":
    asyncio.run(main())
