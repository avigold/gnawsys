#!/usr/bin/env python3
"""Generate TTS audio for curated Hebrew sentences using OpenAI API.

Reads curated_sentences.json, generates an Opus audio file for each
sentence's Hebrew text, and saves them to audio/. Resumes automatically
by skipping files that already exist.
"""

import asyncio
import functools
import hashlib
import json
import os
import sys
import time

import httpx

# Unbuffered print
print = functools.partial(print, flush=True)

# ── Config ──────────────────────────────────────────────────────────
INPUT_FILE = "curated_sentences.json"
AUDIO_DIR = "audio"
MODEL = "tts-1"
VOICE = "nova"
FORMAT = "opus"
CONCURRENCY = 10


def sentence_id(hebrew: str) -> str:
    """Deterministic short ID from Hebrew text."""
    return hashlib.md5(hebrew.encode("utf-8")).hexdigest()[:12]


async def generate_one(client, api_key, hebrew, filepath, sem, stats):
    """Generate audio for one sentence."""
    async with sem:
        for attempt in range(3):
            try:
                resp = await client.post(
                    "https://api.openai.com/v1/audio/speech",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"model": MODEL, "voice": VOICE, "input": hebrew,
                          "response_format": FORMAT},
                    timeout=30.0,
                )
                if resp.status_code == 429:
                    wait = 30 * (attempt + 1)
                    print(f"  Rate limited, waiting {wait}s...")
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                stats["generated"] += 1
                return
            except Exception as e:
                if attempt == 2:
                    print(f"  Error: {e}")
                    stats["errors"] += 1
                else:
                    await asyncio.sleep(5)


async def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Set OPENAI_API_KEY environment variable.")
        sys.exit(1)

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        sentences = json.load(f)

    os.makedirs(AUDIO_DIR, exist_ok=True)
    existing = set(os.listdir(AUDIO_DIR))

    # Build task list, skipping already-generated files
    tasks_todo = []
    mapping = {}
    skipped = 0

    for i, s in enumerate(sentences):
        sid = sentence_id(s["hebrew"])
        mapping[sid] = i
        filename = f"{sid}.{FORMAT}"
        filepath = os.path.join(AUDIO_DIR, filename)
        if filename in existing:
            skipped += 1
        else:
            tasks_todo.append((s["hebrew"], filepath))

    total = len(sentences)
    print(f"Generating audio for {total} sentences ({skipped} already exist, {len(tasks_todo)} to generate)")
    print(f"Model: {MODEL} | Voice: {VOICE} | Format: {FORMAT} | Concurrency: {CONCURRENCY}")
    print()

    stats = {"generated": 0, "errors": 0}
    sem = asyncio.Semaphore(CONCURRENCY)
    start = time.time()

    # Process in chunks for progress reporting
    CHUNK = 100
    for chunk_start in range(0, len(tasks_todo), CHUNK):
        chunk = tasks_todo[chunk_start:chunk_start + CHUNK]
        async with httpx.AsyncClient() as client:
            aws = [generate_one(client, api_key, hebrew, fp, sem, stats)
                   for hebrew, fp in chunk]
            await asyncio.gather(*aws)

        done = skipped + stats["generated"] + stats["errors"]
        elapsed = time.time() - start
        rate = stats["generated"] / elapsed if elapsed > 0 and stats["generated"] > 0 else 0
        remaining = total - done
        eta = remaining / rate / 60 if rate > 0 else 0
        print(f"  {done}/{total} | generated: {stats['generated']} | "
              f"skipped: {skipped} | errors: {stats['errors']} | "
              f"ETA: {eta:.1f}m | elapsed: {elapsed / 60:.1f}m")

    # Write mapping file
    with open(os.path.join(AUDIO_DIR, "mapping.json"), "w", encoding="utf-8") as f:
        json.dump(mapping, f)

    # Add audio IDs to the curated sentences file
    for s in sentences:
        s["audio"] = sentence_id(s["hebrew"])

    with open(INPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(sentences, f, ensure_ascii=False, indent=1)

    elapsed = time.time() - start
    print()
    print(f"Done. {stats['generated']} generated, {skipped} skipped, {stats['errors']} errors")
    print(f"Time: {elapsed / 60:.1f} minutes")


if __name__ == "__main__":
    asyncio.run(main())
